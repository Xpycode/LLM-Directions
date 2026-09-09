"""Completion evidence and read-only activation candidates, in explicit namespaces.

Only initialize_sealed can acquire completion evidence: it performs initialization
itself under uninterrupted ownership. There is no retrospective sealing, default
runtime, activation, marker repair, input or retry API. External pins/provenance
are trusted caller inputs, not authentication inferred from an arbitrary file.
"""
from dataclasses import dataclass
import json
import os
import re
import stat
import uuid

import recovery_bootstrap as bootstrap
from recovery_snapshot import _Snapshot, fingerprint, identity, require, SnapshotError
from recovery_storage import flush_directory

MAX_AUDIT = 2 * (bootstrap.MAX_BASELINE + bootstrap.MAX_HISTORY) + 65536
MAX_SEAL = 6 * MAX_AUDIT + 65536
SEAL_NAMES = ("seal.tmp", "seal.json")


def _canonical(raw, limit):
    require(type(raw) is bytes and 0 < len(raw) <= limit, "invalidEvidenceSize")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicateEvidenceKey")
            result[key] = value
        return result
    try:
        data = json.loads(raw, object_pairs_hook=unique)
        require(type(data) is dict and bootstrap.encode(data) == raw, "noncanonicalEvidence")
        return data
    except (TypeError, RecursionError, OverflowError) as error:
        raise SnapshotError("invalidEvidence") from error


def _keys(data, names):
    require(type(data) is dict and set(data) == set(names.split()), "invalidEvidenceFields")


def _stamp(value):
    require(type(value) is list and len(value) == 8 and
            type(value[0]) is list and len(value[0]) == 2 and
            all(type(n) is int and n >= 0 for n in value[0] + value[1:]),
            "invalidFingerprint")
    return value


def _unhex(value, limit):
    require(type(value) is str and 0 < len(value) <= 2 * limit and
            len(value) % 2 == 0 and re.fullmatch(r"[0-9a-f]+", value) is not None,
            "invalidEvidenceHex")
    return bytes.fromhex(value)


def _names(root, expected):
    names = set()
    with os.scandir(root) as entries:
        for index, entry in enumerate(entries):
            require(index < len(expected) and entry.name in expected, "unexpectedNamespaceEntry")
            names.add(entry.name)
    require(names == set(expected), "incompleteNamespace")


def _read_artifact(root, name, links):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
                stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == links and
                0 < info.st_size <= MAX_AUDIT, "unsafeAuditFile")
        raw = os.pread(fd, info.st_size + 1, 0)
        stamp = fingerprint(info)
        require(len(raw) == info.st_size and fingerprint(os.fstat(fd)) == stamp and
                fingerprint(os.stat(name, dir_fd=root, follow_symlinks=False)) == stamp,
                "interveningStateChange")
        return dict(hex=raw.hex(), sha256=bootstrap.digest(raw),
                    stamp=json.loads(bootstrap.encode(stamp)))
    finally:
        os.close(fd)


def _capture(owner):
    root = bootstrap._root(owner)
    stamps = bootstrap._stamps(owner)
    _names(root, ("lock", *bootstrap.ARTIFACTS))
    require(owner.read_marker(139) == b"clean", "notInitializedClean")
    artifacts = {name: _read_artifact(root, name, 1 if index == 0 else 2)
                 for index, name in enumerate(bootstrap.ARTIFACTS)}
    pending, staged, committed = (artifacts[name] for name in bootstrap.ARTIFACTS)
    require(staged == committed and
            len({tuple(stamps[1][0]), tuple(pending["stamp"][0]),
                 tuple(committed["stamp"][0])}) == 3, "invalidAuditTopology")
    _names(root, ("lock", *bootstrap.ARTIFACTS))
    require(bootstrap._stamps(owner) == stamps and owner.read_marker(139) == b"clean",
            "interveningStateChange")
    return dict(directory=owner.directory, stamps=stamps, artifacts=artifacts)


def _audit(snapshot, baseline, history, history_pin):
    directory, old_stamps, old_samples = bootstrap._baseline_data(baseline)
    bootstrap._pin(history, history_pin, bootstrap.MAX_HISTORY)
    artifacts = snapshot["artifacts"]
    pending_raw = _unhex(artifacts[bootstrap.ARTIFACTS[0]]["hex"], MAX_AUDIT)
    committed_raw = _unhex(artifacts[bootstrap.ARTIFACTS[2]]["hex"], MAX_AUDIT)
    pending = _canonical(pending_raw, MAX_AUDIT)
    committed = _canonical(committed_raw, MAX_AUDIT)
    samples = bootstrap._pair(committed.get("current_samples"))
    require(directory == snapshot["directory"] and
            snapshot["stamps"][0][0] == old_stamps[0][0] and
            snapshot["stamps"][1][0] == old_stamps[1][0], "baselineNamespaceMismatch")
    require(samples[0]["boot"] != old_samples[0]["boot"], "sameBoot")
    expected = dict(schema="legacyBootstrap/v2", result="initializedFenced",
                    launch_eligible=False, native_recovery_verified=False,
                    historical_outcome="failedOrUnknownNonRetryable",
                    baseline_hex=baseline.raw.hex(), baseline_sha256=baseline.trusted_sha256,
                    baseline_provenance=baseline.provenance,
                    history_hex=history.hex(), history_sha256=history_pin,
                    old_marker_hex=b"unresolved".hex(), old_stamps=old_stamps,
                    current_samples=samples, initialized_marker_stamp=snapshot["stamps"][1])
    # Byte equality preserves scalar types (False must not compare equal to 0).
    require(bootstrap.encode(expected) == committed_raw, "auditMismatch")
    del expected["initialized_marker_stamp"]
    expected["result"] = "pending"
    require(bootstrap.encode(expected) == pending_raw, "auditMismatch")
    return samples


@dataclass(frozen=True)
class TrustedSeal:
    raw: bytes
    trusted_sha256: str
    provenance: str


def _seal_data(seal):
    require(type(seal) is TrustedSeal, "untrustedCompletionSeal")
    bootstrap._pin(seal.raw, seal.trusted_sha256, MAX_SEAL)
    bootstrap._provenance(seal.provenance)
    data = _canonical(seal.raw, MAX_SEAL)
    _keys(data, "schema transaction_id provenance directory stamps artifacts")
    require(data["schema"] == "legacyCompletion/v1" and
            type(data["transaction_id"]) is str and
            re.fullmatch(r"[0-9a-f]{32}", data["transaction_id"]) is not None and
            int(data["transaction_id"], 16) != 0, "invalidCompletionSeal")
    bootstrap._provenance(data["provenance"])
    require(data["provenance"] == seal.provenance, "completionProvenanceMismatch")
    require(type(data["directory"]) is str and data["directory"].startswith("/") and
            os.path.normpath(data["directory"]) == data["directory"] and
            type(data["stamps"]) is list and len(data["stamps"]) == 2,
            "invalidCompletionSeal")
    for stamp in data["stamps"]:
        _stamp(stamp)
    _keys(data["artifacts"], " ".join(bootstrap.ARTIFACTS))
    for entry in data["artifacts"].values():
        _keys(entry, "hex sha256 stamp")
        raw = _unhex(entry["hex"], MAX_AUDIT)
        bootstrap._pin(raw, entry["sha256"], MAX_AUDIT)
        _stamp(entry["stamp"])
    return data


def load_seal(raw, *, trusted_sha256, provenance):
    """External pin must come from independent acquisition, not the loaded file."""
    result = TrustedSeal(raw, trusted_sha256, provenance)
    _seal_data(result)
    return result


def _match(owner, data):
    actual = _capture(owner)
    expected = {name: data[name] for name in ("directory", "stamps", "artifacts")}
    require(bootstrap.encode(actual) == bootstrap.encode(expected), "completionContinuityLost")


def preflight(owner, seal, baseline, *, history, trusted_history_sha256, observe, clock):
    """Read-only candidate while borrowing a held owner; never opens report paths.

    observe/clock are explicit trusted bounded native dependencies in a live caller.
    Output does not outlive ownership as authority and cannot enable the launcher.
    """
    data = _seal_data(seal)
    initialized = _audit(data, baseline, history, trusted_history_sha256)
    started = clock()
    _match(owner, data)
    first = bootstrap._sample(observe())
    _match(owner, data)
    second = bootstrap._sample(observe())
    samples = bootstrap._pair([first, second])
    require((first["boot"], first["session"]) ==
            (initialized[0]["boot"], initialized[0]["session"]), "initializationContextChanged")
    require(initialized[-1]["checked_ns"] <= first["checked_ns"], "staleContext")
    _match(owner, data)
    ended = clock()
    require(type(started) is int and type(ended) is int and
            0 < started <= first["checked_ns"] <= second["checked_ns"] <= ended and
            ended - started <= bootstrap.WINDOW_NS, "staleContext")
    # The injected clock is also an observation boundary. Recheck exact bytes
    # after the last callback, not merely the lock inode's continued existence.
    _match(owner, data)
    return dict(result="activationCandidate", launch_eligible=False,
                native_recovery_verified=False, transaction_id=data["transaction_id"],
                seal_sha256=seal.trusted_sha256, current_samples=samples)


def _external_recheck(tree, root, stamp):
    for parent, name, fd in tree._edges:
        require(identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) ==
                identity(os.fstat(fd)), "sealNamespaceChanged")
    tree._private_directory(root)
    require(fingerprint(os.fstat(root)) == stamp, "sealNamespaceChanged")


def initialize_sealed(owner, baseline, *, seal_directory, provenance, observe, clock,
                      history, trusted_history_sha256, boundary=lambda stage: None):
    """Initialize and retain a seal outside the marker namespace before returning.

    The returned pin is acquired here, after actual initialization/flushes. A caller
    must retain it independently for later load_seal. A surviving seal.json after a
    failed/crashed call is NOT permission to manufacture a pin from that file.
    No API accepts an old initializer result for retrospective sealing.
    """
    bootstrap._provenance(provenance)
    bootstrap._root(owner)
    seal_directory = os.fspath(seal_directory)
    common = os.path.commonpath([owner.directory, seal_directory])
    require(common not in (owner.directory, seal_directory), "sealNamespaceNotSeparate")
    tree = _Snapshot()
    try:
        root = tree._trusted_directory(seal_directory)
        _names(root, ())
        external_stamp = fingerprint(os.fstat(root))
        audit = bootstrap.initialize_fenced(owner, baseline, observe=observe, clock=clock,
            history=history, trusted_history_sha256=trusted_history_sha256, boundary=boundary)
        # There is no caller callback or ownership gap between initializer return
        # and this snapshot. Later loading cannot reproduce this acquisition.
        snapshot = _capture(owner)
        require(snapshot["artifacts"][bootstrap.ARTIFACTS[2]]["hex"] ==
                bootstrap.encode(audit).hex(), "auditMismatch")
        _audit(snapshot, baseline, history, trusted_history_sha256)
        raw = bootstrap.encode(dict(snapshot, schema="legacyCompletion/v1",
                                    transaction_id=uuid.uuid4().hex, provenance=provenance))
        seal = load_seal(raw, trusted_sha256=bootstrap.digest(raw), provenance=provenance)
        _external_recheck(tree, root, external_stamp)
        stamp, external_stamp = bootstrap._write_new(root, SEAL_NAMES[0], raw, boundary, "seal")
        _external_recheck(tree, root, external_stamp)
        _match(owner, snapshot)
        os.link(SEAL_NAMES[0], SEAL_NAMES[1], src_dir_fd=root, dst_dir_fd=root,
                follow_symlinks=False)
        stamp = fingerprint(os.stat(SEAL_NAMES[0], dir_fd=root, follow_symlinks=False))
        external_stamp = fingerprint(os.fstat(root))
        boundary("sealPublished")
        flush_directory(root)
        boundary("sealDirectoryFlushed")
        for name in SEAL_NAMES:
            bootstrap._check_file(root, name, raw, stamp)
        require(stamp[4] == 2, "invalidSealTopology")
        _names(root, SEAL_NAMES)
        _external_recheck(tree, root, external_stamp)
        _match(owner, snapshot)
        return seal
    finally:
        tree._close()
