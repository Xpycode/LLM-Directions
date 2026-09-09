"""Offline legacy initialization preparation; no CLI, runtime path or input API.

The trusted caller selects the namespace, owns MarkerLock throughout, supplies
independently acquired bounded native context, and authenticates retained bytes
against a digest pinned OUTSIDE those bytes. Computing a digest of an arbitrary
report and passing it back here does not establish trust. Provenance describes
that external acquisition; this module cannot authenticate the caller.

Success is initializedFenced, NOT launch eligibility. bootstrap.pending is a
permanent fence, including after success. All launchers must reject any bootstrap
artifact before interpreting marker bytes. Activation requires a separately
reviewed procedure; there is deliberately no resume, cleanup, retry or dispatch.
Advisory ownership covers conforming launchers, not hostile same-UID writers.
"""
from dataclasses import dataclass
import hashlib
import json
import os
import re
import uuid

from recovery_snapshot import MarkerLock, fingerprint, require
from recovery_storage import flush_directory, flush_file
from recovery_verifier import context_snapshot

ARTIFACTS = ("bootstrap.pending", "bootstrap.committed.tmp", "bootstrap.committed.json")
MAX_BASELINE = 65536
MAX_HISTORY = 1048576
WINDOW_NS = 2_000_000_000


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _pin(raw, trusted_sha256, limit):
    require(type(raw) is bytes and 0 < len(raw) <= limit, "missingOrOversizeEvidence")
    require(type(trusted_sha256) is str and
            re.fullmatch(r"[0-9a-f]{64}", trusted_sha256) is not None and
            digest(raw) == trusted_sha256, "untrustedEvidence")


def _provenance(value):
    require(type(value) is str and 0 < len(value.strip()) <= 4096,
            "missingExternalProvenance")


def _sample(value):
    # Round-trip owns the observer's dictionary; later mutations cannot alter it.
    value = json.loads(encode(value))
    context_snapshot(value)
    parsed = uuid.UUID(value["boot"])
    require(str(parsed) == value["boot"] and parsed.int != 0, "unknownBoot")
    return value


def _pair(samples):
    require(type(samples) is list and len(samples) == 2, "missingContextSamples")
    first, second = map(_sample, samples)
    require((first["boot"], first["session"]) == (second["boot"], second["session"]),
            "contextDrift")
    require(first["checked_ns"] <= second["checked_ns"] <=
            first["checked_ns"] + WINDOW_NS, "staleContext")
    return [first, second]


def _root(owner):
    require(type(owner) is MarkerLock, "untrustedMarkerLock")
    owner.recheck()
    return owner._tree._directories[0][0]


def _stamps(owner):
    root = _root(owner)
    return json.loads(encode([fingerprint(os.fstat(root)), fingerprint(os.fstat(owner._fd))]))


def _no_artifacts(owner):
    root = _root(owner)
    for name in ARTIFACTS:
        try:
            os.stat(name, dir_fd=root, follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise ValueError("bootstrapAlreadyAttempted")


def _observe_locked(owner, observe, clock, expected=None):
    _no_artifacts(owner)
    stamp = _stamps(owner)
    if expected is not None:
        require(stamp == expected, "baselineContinuityLost")
    start = clock()
    first = _sample(observe())
    marker = owner.read_marker(139)
    second = _sample(observe())
    end = clock()
    samples = _pair([first, second])
    require(type(start) is int and type(end) is int and
            0 < start <= first["checked_ns"] <= second["checked_ns"] <= end
            and end - start <= WINDOW_NS, "staleContext")
    require(_stamps(owner) == stamp and owner.read_marker(139) == marker,
            "interveningStateChange")
    require(marker == b"unresolved", "notLegacyUnresolved")
    return stamp, samples, start


def capture_baseline(owner, *, observe, clock, provenance):
    """Read-only present observation; does not claim the crash's boot identity.

    Retain these bytes externally and separately pin their digest before a future
    load. The observer must acquire fresh native evidence on each invocation.
    """
    _provenance(provenance)
    stamps, samples, _ = _observe_locked(owner, observe, clock)
    return encode({"schema": "legacyBaseline/v1", "directory": owner.directory,
                   "stamps": stamps, "samples": samples, "marker": "unresolved",
                   "provenance": provenance})


@dataclass(frozen=True)
class TrustedBaseline:
    raw: bytes
    trusted_sha256: str
    provenance: str


def _baseline_data(baseline):
    require(type(baseline) is TrustedBaseline, "untrustedBaseline")
    _pin(baseline.raw, baseline.trusted_sha256, MAX_BASELINE)
    _provenance(baseline.provenance)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicateEvidenceKey")
            result[key] = value
        return result
    data = json.loads(baseline.raw, object_pairs_hook=unique)
    if data.get("schema") == "legacyBaseline/v1":
        require(set(data) == {"schema", "directory", "stamps", "samples", "marker", "provenance"}
                and data["marker"] == "unresolved", "invalidBaseline")
        directory, stamps, samples = data["directory"], data["stamps"], data["samples"]
        _provenance(data["provenance"])
    else:
        # Existing retained prospective report is accepted only when its entire
        # original bytes have an independent external pin. Never rewrite it.
        locked, metadata = data["lockedBaseline"], data["metadataVerification"]
        require(locked["result"] == "legacyBaselineObserved" and
                locked["markerClass"] == "legacyUnresolved" and
                locked["markerBytes"] == 10 and locked["markerSHA256"] == digest(b"unresolved")
                and locked["markerUnchanged"] is True and
                metadata["result"] == "legacyBaselineMetadataVerified" and
                metadata["markerAndDirectoryUnchanged"] is True,
                "invalidBaseline")
        directory = locked["markerDirectory"]
        stamps = [metadata["rootFingerprint"], metadata["markerFingerprint"]]
        samples = metadata["contextSamples"]
        earlier = _pair(locked["contextSamples"])
        require((earlier[0]["boot"], earlier[0]["session"]) ==
                (samples[0]["boot"], samples[0]["session"]), "contextDrift")
    require(type(directory) is str and type(stamps) is list and len(stamps) == 2,
            "invalidBaseline")
    for stamp in stamps:
        require(type(stamp) is list and len(stamp) == 8 and
                type(stamp[0]) is list and len(stamp[0]) == 2 and
                all(type(n) is int and n >= 0 for n in stamp[0] + stamp[1:]),
                "invalidFingerprint")
    return directory, stamps, _pair(samples)


def load_baseline(raw, *, trusted_sha256, provenance):
    """Load retained bytes only against caller's separately authenticated pin.

    A pin stored inside the report or computed from it at load time is explicitly
    outside this contract. No default pin, report path, or runtime discovery exists.
    """
    result = TrustedBaseline(raw, trusted_sha256, provenance)
    _baseline_data(result)
    return result


def _write_new(root, name, raw, boundary, prefix):
    fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=root)
    try:
        root_stamp = fingerprint(os.fstat(root))
        stamp = fingerprint(os.fstat(fd))
        boundary(prefix + "Created")
        _check_file(root, name, b"", stamp)
        require(fingerprint(os.fstat(root)) == root_stamp, "interveningStateChange")
        offset = 0
        while offset < len(raw):
            count = os.write(fd, raw[offset:])
            require(count > 0, "partialEvidenceWrite")
            offset += count
        stamp = fingerprint(os.fstat(fd))
        boundary(prefix + "Written")
        _check_file(root, name, raw, stamp)
        flush_file(fd)
        boundary(prefix + "Flushed")
        _check_file(root, name, raw, stamp)
        require(fingerprint(os.fstat(root)) == root_stamp, "interveningStateChange")
        return stamp, root_stamp
    finally:
        os.close(fd)


def _check_file(root, name, raw, stamp):
    fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=root)
    try:
        require(fingerprint(os.fstat(fd)) == stamp and
                os.pread(fd, len(raw) + 1, 0) == raw and
                fingerprint(os.fstat(fd)) == stamp, "interveningStateChange")
    finally:
        os.close(fd)


def initialize_fenced(owner, baseline, *, observe, clock, history,
                      trusted_history_sha256, boundary=lambda stage: None):
    """One explicit offline mutation of a caller-selected isolated fixture.

    Retain pending/full original evidence before changing the SAME locked inode.
    Write+flush the clean marker, then atomically publish the flushed committed
    audit via exclusive hard-link creation. Pending is never removed, so errors,
    crashes and success all block ordinary startup. No historical run is invented.
    boundary is only a fault-injection hook, never an authorization callback.
    """
    directory, stamps, old_samples = _baseline_data(baseline)
    _pin(history, trusted_history_sha256, MAX_HISTORY)
    require(directory == owner.directory, "baselineNamespaceMismatch")
    _, samples, started = _observe_locked(owner, observe, clock, stamps)
    require(samples[0]["boot"] != old_samples[0]["boot"], "sameBoot")
    boundary("verified")
    require(_stamps(owner) == stamps and owner.read_marker(139) == b"unresolved",
            "interveningStateChange")
    root = _root(owner)
    audit = {"schema": "legacyBootstrap/v2", "result": "initializedFenced",
             "launch_eligible": False, "native_recovery_verified": False,
             "historical_outcome": "failedOrUnknownNonRetryable",
             "baseline_hex": baseline.raw.hex(), "baseline_sha256": baseline.trusted_sha256,
             "baseline_provenance": baseline.provenance,
             "history_hex": history.hex(), "history_sha256": trusted_history_sha256,
             "old_marker_hex": b"unresolved".hex(), "old_stamps": stamps,
             "current_samples": samples}
    # No marker mutation until the permanent fence and full evidence are durable.
    pending = encode(dict(audit, result="pending"))
    pending_stamp, expected_root = _write_new(root, ARTIFACTS[0], pending, boundary, "pending")
    flush_directory(root)
    boundary("pendingDirectoryFlushed")
    _check_file(root, ARTIFACTS[0], pending, pending_stamp)
    owner.recheck()
    require(fingerprint(os.fstat(root)) == expected_root and
            _stamps(owner)[1] == stamps[1] and owner.read_marker(139) == b"unresolved",
            "interveningStateChange")
    now = clock()
    require(type(now) is int and samples[-1]["checked_ns"] <= now <= started + WINDOW_NS,
            "staleContext")
    owner.write_marker(b"clean")
    flush_file(owner._fd)
    initialized_marker_stamp = _stamps(owner)[1]
    boundary("markerFlushed")
    _check_file(root, ARTIFACTS[0], pending, pending_stamp)
    owner.recheck()
    require(owner.read_marker(139) == b"clean" and
            _stamps(owner)[1] == initialized_marker_stamp and
            fingerprint(os.fstat(root)) == expected_root, "interveningStateChange")
    # Pending predates initialization and cannot contain this observation.
    # Bind the actual post-write fingerprint, not just the reusable word clean.
    # This is a prerequisite for activation continuity, not a completion seal.
    audit["initialized_marker_stamp"] = initialized_marker_stamp
    committed = encode(audit)
    committed_stamp, _ = _write_new(root, ARTIFACTS[1], committed, boundary, "committed")
    _check_file(root, ARTIFACTS[0], pending, pending_stamp)
    _check_file(root, ARTIFACTS[1], committed, committed_stamp)
    # link is atomic and fails if destination exists; never replace any evidence.
    os.link(ARTIFACTS[1], ARTIFACTS[2], src_dir_fd=root, dst_dir_fd=root,
            follow_symlinks=False)
    # Link creation changes link count/ctime of our committed inode.
    committed_stamp = fingerprint(os.stat(ARTIFACTS[1], dir_fd=root, follow_symlinks=False))
    expected_root = fingerprint(os.fstat(root))
    boundary("committedPublished")
    flush_directory(root)
    boundary("committedDirectoryFlushed")
    _check_file(root, ARTIFACTS[0], pending, pending_stamp)
    _check_file(root, ARTIFACTS[1], committed, committed_stamp)
    _check_file(root, ARTIFACTS[2], committed, committed_stamp)
    require(fingerprint(os.fstat(root)) == expected_root, "interveningStateChange")
    owner.recheck()
    require(owner.read_marker(139) == b"clean" and
            _stamps(owner)[1] == initialized_marker_stamp, "interveningStateChange")
    # Keep staging evidence too: there is no cleanup/activation edge in this API.
    return audit
