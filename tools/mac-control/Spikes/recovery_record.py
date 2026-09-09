"""Offline spike recovery model. No runtime paths, process operations or disk writer.

Inputs are evidence already verified by a future trusted adapter, not arbitrary
reports. A candidate is never permission to clear a marker, replay or signal a PID.
WriteGate models acknowledgements only; recovery_admission connects storage and
OS identity setup for the supervisor's worker-crash case. Reconciliation is separate.
"""
import copy
import json
import re

MAX_EVENTS = 256
MAX_BYTES = 65536


def require(condition):
    if not condition:
        raise ValueError("invalid or unresolved recovery evidence")


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected.split()))


def number(value, minimum=0):
    require(type(value) is int and minimum <= value <= 2**63 - 1)


def token(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) is not None)


def check_identity(value):
    keys(value, "boot session run worker target")
    for field in ("boot", "session", "run"):
        token(value[field])
    for role in ("worker", "target"):
        process = value[role]
        keys(process, "pid start code")
        number(process["pid"], 1)
        token(process["start"])
        require(type(process["code"]) is str and
                re.fullmatch(r"[a-f0-9]{64}", process["code"]) is not None)
    require(value["worker"]["pid"] != value["target"]["pid"])


def validate(record):
    keys(record, "version identity revision state sequence checkpoint events")
    require(type(record["version"]) is int and record["version"] == 1)
    check_identity(record["identity"])
    for field in ("revision", "sequence", "checkpoint"):
        number(record[field])
    events = record["events"]
    require(type(events) is list and len(events) <= MAX_EVENTS)
    require(record["sequence"] == len(events))
    require(record["checkpoint"] <= len(events) and record["checkpoint"] % 2 == 0)
    require(record["revision"] >= len(events))
    tags = set()
    for sequence, event in enumerate(events, 1):
        keys(event, "sequence tag kind")
        number(event["sequence"], 1)
        number(event["tag"], 1)
        require(event["sequence"] == sequence and event["tag"] not in tags)
        require(event["kind"] == ("down" if sequence % 2 else "up"))
        tags.add(event["tag"])
    state = record["state"]
    require(state in ("prepared", "uncertain", "resolved"))
    if state == "prepared":
        require(not events and record["revision"] == 0)
    elif state == "uncertain":
        require(len(events) > record["checkpoint"])
    else:
        require(bool(events) and record["checkpoint"] == len(events))
        require(record["revision"] > len(events))
    return record


def encode(record):
    data = json.dumps(validate(record), sort_keys=True, separators=(",", ":")).encode()
    require(len(data) <= MAX_BYTES)
    return data


def parse(data):
    require(type(data) is bytes and 0 < len(data) <= MAX_BYTES)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result)
            result[key] = value
        return result

    try:
        return validate(json.loads(data, object_pairs_hook=unique))
    except (UnicodeError, RecursionError, TypeError, KeyError) as error:
        raise ValueError("invalid recovery record") from error


def new_record(identity):
    return validate(dict(version=1, identity=copy.deepcopy(identity), revision=0,
                         state="prepared", sequence=0, checkpoint=0, events=[]))


def admit(record, event):
    result = copy.deepcopy(validate(record))
    result["events"].append(copy.deepcopy(event))
    result.update(revision=result["revision"] + 1, sequence=result["sequence"] + 1,
                  state="uncertain")
    return validate(result)


def reserve_pair(record, down_tag):
    """Durably reserve normal down and its possible emergency cleanup up together."""
    require(record["state"] in ("prepared", "resolved"))
    sequence = record["sequence"]
    result = admit(record, dict(sequence=sequence + 1, tag=down_tag, kind="down"))
    return admit(result, dict(sequence=sequence + 2, tag=down_tag + 1, kind="up"))


def checkpoint(record, proof):
    validate(record)
    keys(proof, "identity sequence tag held receipts")
    check_identity(proof["identity"])
    number(proof["sequence"], 1)
    number(proof["tag"], 1)
    require(record["state"] == "uncertain" and record["sequence"] % 2 == 0)
    require(proof["identity"] == record["identity"] and proof["held"] == [])
    require(proof["sequence"] == record["sequence"] and
            proof["tag"] == record["events"][-1]["tag"])
    # Exact cumulative receipts: no missing, duplicated, reordered or extra event.
    # Validate types too: Python equality alone accepts True as integer 1.
    receipt_record = dict(record, events=proof["receipts"])
    validate(receipt_record)
    require(proof["receipts"] == record["events"])
    result = copy.deepcopy(record)
    result.update(revision=result["revision"] + 1, state="resolved",
                  checkpoint=result["sequence"])
    return validate(result)


def recovery_candidate(record, proof):
    """Pure evidence predicate, deliberately not named clean/restart eligible."""
    try:
        validate(record)
        keys(proof, "identity worker_exited target_exited observation_complete sequence tag")
        check_identity(proof["identity"])
        number(proof["sequence"], 1)
        number(proof["tag"], 1)
        return (record["state"] == "resolved" and
                proof["identity"] == record["identity"] and
                proof["sequence"] == record["sequence"] and
                proof["tag"] == record["events"][-1]["tag"] and
                all(proof[field] is True for field in
                    ("worker_exited", "target_exited", "observation_complete")))
    except (ValueError, TypeError, KeyError):
        return False


class WriteGate:
    """Single pending revision; stop/write failure permanently closes this instance.

    The adapter must acknowledge exact bytes only after durable completion under
    the live lock. Nothing here authenticates that adapter or performs a flush.
    A loaded record never restores an old dispatch permit.
    """

    def __init__(self, record):
        self._record = parse(encode(record))
        self._pending = None
        self._closed = False
        self.dispatch_ready = False

    @property
    def record(self):
        return copy.deepcopy(self._record)

    def stage(self, record):
        try:
            require(not self._closed and self._pending is None and not self.dispatch_ready)
            validate(record)
            require(record["identity"] == self._record["identity"])
            # Append one event, reserve one complete pair, or resolve the boundary.
            if record["state"] == "uncertain":
                if record["sequence"] == self._record["sequence"] + 2:
                    expected = reserve_pair(self._record, record["events"][-2]["tag"])
                else:
                    expected = admit(self._record, record["events"][-1])
            else:
                expected = checkpoint(self._record, dict(
                    identity=record["identity"], sequence=record["sequence"],
                    tag=record["events"][-1]["tag"], held=[], receipts=record["events"]))
            require(record == expected)
            self.dispatch_ready = False
            self._pending = encode(record)
            return self._pending
        except (ValueError, TypeError, KeyError, IndexError):
            self.stop()
            raise ValueError("write transition rejected") from None

    def acknowledge(self, data):
        if self._closed or self._pending is None or data != self._pending:
            self.stop()
            raise ValueError("stale or failed durable acknowledgement")
        self._record = parse(data)
        self._pending = None
        self.dispatch_ready = self._record["state"] == "uncertain"

    def consume_dispatch(self):
        require(self.dispatch_ready and not self._closed)
        self.dispatch_ready = False

    def stop(self):
        if self._pending is not None:
            pending = parse(self._pending)
            if pending["state"] == "uncertain":
                # A failed/late write may have reached disk. Keep the conservative
                # attempted boundary, never fall back to an earlier resolved one.
                self._record = pending
        self._closed = True
        self.dispatch_ready = False
        self._pending = None

    def write_failed(self):
        self.stop()
