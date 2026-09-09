"""Read-only, offline reconciliation evidence checker for the isolated spike.

The caller supplies immutable snapshots from a future trusted adapter: marker and
latest record read under both runtime/storage locks, OS boot/session and complete
executor inventory, and independent owned-process/stream observations. Dictionaries
do not authenticate those claims. Never feed a user report into a runtime decision.
This module performs no I/O, process lookup, signalling, marker clearing or replay.
Candidates describe consistent evidence, NOT native recovery or restart authority.
"""
from dataclasses import dataclass
import hashlib

import recovery_record as model

OBSERVATION_NS = 2_000_000_000


@dataclass(frozen=True)
class Verdict:
    result: str
    reason: str
    restart_eligible: bool = False
    native_recovery_verified: bool = False


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def timestamp(value, end):
    model.number(value, 1)
    check(value <= end, "futureEvidence")
    return value


def context_snapshot(context):
    model.keys(context, "boot session checked_ns inventory_complete executors")
    model.token(context["boot"])
    model.token(context["session"])
    model.number(context["checked_ns"], 1)
    check(context["inventory_complete"] is True and
          type(context["executors"]) is list and context["executors"] == [],
          "executorInventoryUnresolved")


def event_rows(rows, record, end, receipts=False):
    check(type(rows) is list and len(rows) == len(record["events"]),
          "eventMultiplicityMismatch")
    times = []
    for row, expected in zip(rows, record["events"]):
        fields = "sequence tag kind ns origin_pid" if receipts else "sequence tag kind ns"
        model.keys(row, fields)
        model.number(row["sequence"], 1)
        model.number(row["tag"], 1)
        check({key: row[key] for key in ("sequence", "tag", "kind")} == expected,
              "eventBoundaryMismatch")
        if receipts:
            model.number(row["origin_pid"], 1)
            check(row["origin_pid"] == record["identity"]["worker"]["pid"],
                  "receiptOriginMismatch")
        times.append(timestamp(row["ns"], end))
    check(times == sorted(times), "eventOrderMismatch")
    return times


def completed_boundary(record, evidence, end):
    """Validate actual cumulative event/checkpoint rows, including pre-exit binding."""
    model.validate(record)
    check(record["state"] == "resolved", "unresolvedBoundary")
    posts = event_rows(evidence["posts"], record, end)
    receipts = event_rows(evidence["receipts"], record, end, receipts=True)
    # Native post acknowledgements are emitted AFTER CGEvent.post returns;
    # target receipt can precede that acknowledgement on another process.
    checkpoints = evidence["checkpoints"]
    check(type(checkpoints) is list and len(checkpoints) == len(posts) // 2,
          "missingOrDuplicateCheckpoint")
    checkpoint_times = []
    for index, row in enumerate(checkpoints, 1):
        model.keys(row, "run sequence tag held ns")
        model.number(row["sequence"], 1)
        model.number(row["tag"], 1)
        model.token(row["run"])
        sequence = index * 2
        check(row["run"] == record["identity"]["run"] and row["sequence"] == sequence
              and row["tag"] == record["events"][sequence - 1]["tag"]
              and type(row["held"]) is list and row["held"] == [],
              "checkpointMismatch")
        ns = timestamp(row["ns"], end)
        check(posts[sequence - 1] <= ns, "checkpointBeforePostReturn")
        if sequence < len(posts):
            check(max(ns, receipts[sequence - 1]) <=
                  min(posts[sequence], receipts[sequence]),
                  "nextPairBeforeResolution")
        checkpoint_times.append(ns)
    return posts, receipts, checkpoint_times


def same_boot(record, raw, evidence, context):
    model.keys(evidence, "identity record_sha256 posts receipts checkpoints exits streams fence end_ns")
    model.check_identity(evidence["identity"])
    check(evidence["identity"] == record["identity"], "evidenceIdentityMismatch")
    check(evidence["record_sha256"] == hashlib.sha256(raw).hexdigest(),
          "recordSnapshotMismatch")
    end = timestamp(evidence["end_ns"], context["checked_ns"])
    posts, receipts, checkpoint_times = completed_boundary(record, evidence, end)

    exits, streams = evidence["exits"], evidence["streams"]
    model.keys(exits, "worker target")
    model.keys(streams, "worker target")
    exit_times, eof_times = {}, {}
    for role in ("worker", "target"):
        row = exits[role]
        model.keys(row, "identity status ns method")
        # Owned wait observations bind PID/start/code, not a PID absence lookup.
        check(row["identity"] == record["identity"][role], "exitIdentityMismatch")
        model.check_identity(dict(record["identity"], **{role: row["identity"]}))
        check(row["method"] == "ownedWait" and type(row["status"]) is int
              and -127 <= row["status"] <= 255, "exitUnverified")
        if role == "target":
            check(row["status"] == 0, "targetExitFailed")
        exit_times[role] = timestamp(row["ns"], end)
        stream = streams[role]
        model.keys(stream, "eof_ns complete")
        check(stream["complete"] is True, "incompleteStream")
        eof_times[role] = timestamp(stream["eof_ns"], end)

    check(max(posts[-1], checkpoint_times[-1]) <=
          min(exit_times["worker"], eof_times["worker"]), "workerBoundaryAfterClosure")
    fence = evidence["fence"]
    model.keys(fence, "run target requested_ns acknowledged_ns")
    check(fence["run"] == record["identity"]["run"] and
          fence["target"] == record["identity"]["target"], "fenceIdentityMismatch")
    model.check_identity(dict(record["identity"], target=fence["target"]))
    requested = timestamp(fence["requested_ns"], end)
    acknowledged = timestamp(fence["acknowledged_ns"], end)
    check(requested >= max(exit_times["worker"], eof_times["worker"])
          + OBSERVATION_NS, "shortObservation")
    check(requested <= acknowledged <=
          min(exit_times["target"], eof_times["target"]), "fenceOrderMismatch")
    # This bounded experiment kills only after all receipts/checkpoints resolve.
    # A receipt after verified worker exit is pending-delivery evidence, not a pass.
    check(receipts[-1] <= exit_times["worker"], "lateReceipt")


def verify(marker, raw_record, context, evidence=None):
    """Check supplied evidence only; all outcomes leave marker/admission untouched.

    New-boot candidates require a valid run-bound old record and independently
    obtained different current boot plus a complete empty executor inventory.
    Legacy/missing records stay blocked even on that path: separate bootstrap
    verification is outside this checker. Same-boot evidence uses normalized
    integer monotonic nanoseconds from independent owned streams; adapters must
    preserve every post/receipt/checkpoint, including duplicates and late rows.
    """
    try:
        record = model.parse(raw_record)
        check(type(marker) is bytes and
              marker == b"unresolved:" + record["identity"]["run"].encode("ascii"),
              "markerRunMismatch")
        context_snapshot(context)
        if context["boot"] != record["identity"]["boot"]:
            check(evidence is None, "mixedBootEvidence")
            return Verdict("newBootCandidate", "differentBootAndEmptyInventory")
        check(context["session"] == record["identity"]["session"], "sessionMismatch")
        same_boot(record, raw_record, evidence, context)
        return Verdict("sameBootCandidate", "boundCheckpointExitAndObservation")
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as error:
        # Reasons are controlled strings, never report contents or process paths.
        known = str(error)
        reasons = {"futureEvidence", "executorInventoryUnresolved", "eventMultiplicityMismatch",
                   "eventBoundaryMismatch", "receiptOriginMismatch", "eventOrderMismatch",
                   "evidenceIdentityMismatch", "recordSnapshotMismatch", "unresolvedBoundary",
                   "missingOrDuplicateCheckpoint", "checkpointMismatch", "checkpointBeforePostReturn",
                   "nextPairBeforeResolution", "exitIdentityMismatch", "exitUnverified",
                   "targetExitFailed", "incompleteStream", "workerBoundaryAfterClosure",
                   "fenceIdentityMismatch", "shortObservation", "fenceOrderMismatch", "lateReceipt",
                   "markerRunMismatch", "mixedBootEvidence", "sessionMismatch"}
        return Verdict("blocked", known if known in reasons else "invalidOrMissingEvidence")
