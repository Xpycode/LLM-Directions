"""Explicit legacy activation and one-shot admission; no CLI or desktop input.

All namespaces, pins, provenance and native observation dependencies are selected
by a trusted caller. Returned acknowledgements must be independently retained.
Neither a surviving receipt nor its self-computed digest authenticates completion.
Every mutation borrows an existing MarkerLock and preserves all evidence names.
"""
from dataclasses import dataclass
import json
import os
import re
import uuid

import recovery_bootstrap as bootstrap
import recovery_seal as seals
from recovery_snapshot import fingerprint, require
from recovery_storage import flush_file, flush_directory

INTENT = "activation.intent"
STAGED = "activation.receipt.tmp"
RECEIPT = "activation.receipt.json"
CONSUMED = "activation.consumed"
ARTIFACTS = (INTENT, STAGED, RECEIPT)
FENCES = (*bootstrap.ARTIFACTS, *ARTIFACTS, CONSUMED)
MAX_ACK = 131072


def _id(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{32}", value) is not None,
            "invalidActivationIdentity")


def _equal(actual, expected, reason="activationContinuityLost"):
    require(bootstrap.encode(actual) == bootstrap.encode(expected), reason)


def _snapshot(owner, sealed, names, *, marker=b"clean", marker_stamp=None):
    """Only declared added names may vary from the original completion seal."""
    root = bootstrap._root(owner)
    before = bootstrap._stamps(owner)
    require(owner.directory == sealed["directory"], "activationNamespaceMismatch")
    # APFS directory link counts also change when regular entries are added.
    # Exact full stamps apply between mutations; identity/privacy remain stable.
    _equal(before[0][:4], sealed["stamps"][0][:4])
    _equal(before[1], sealed["stamps"][1] if marker_stamp is None else marker_stamp)
    require(owner.read_marker(139) == marker, "activationMarkerChanged")
    seals._names(root, ("lock", *bootstrap.ARTIFACTS, *names))
    for index, name in enumerate(bootstrap.ARTIFACTS):
        _equal(seals._read_artifact(root, name, 1 if index == 0 else 2),
               sealed["artifacts"][name])
    added = {name: seals._read_artifact(root, name,
               2 if name in (STAGED, RECEIPT) and RECEIPT in names else 1) for name in names}
    if RECEIPT in names:
        _equal(added[STAGED], added[RECEIPT], "invalidActivationTopology")
    distinct = [tuple(sealed["stamps"][1][0]),
                tuple(sealed["artifacts"][bootstrap.ARTIFACTS[0]]["stamp"][0]),
                tuple(sealed["artifacts"][bootstrap.ARTIFACTS[2]]["stamp"][0])]
    distinct.extend(tuple(row["stamp"][0]) for name, row in added.items() if name != RECEIPT)
    require(len(set(distinct)) == len(distinct), "invalidActivationTopology")
    seals._names(root, ("lock", *bootstrap.ARTIFACTS, *names))
    _equal(bootstrap._stamps(owner), before)
    require(owner.read_marker(139) == marker, "activationMarkerChanged")
    return dict(root_stamp=before[0], marker_stamp=before[1], artifacts=added)


def _check(owner, sealed, snapshot, *, marker=b"clean"):
    _equal(_snapshot(owner, sealed, tuple(snapshot["artifacts"]), marker=marker,
                     marker_stamp=snapshot["marker_stamp"]), snapshot)


def _context(owner, sealed, snapshot, initialized, observe, clock):
    started = clock()
    _check(owner, sealed, snapshot)
    first = bootstrap._sample(observe())
    _check(owner, sealed, snapshot)
    second = bootstrap._sample(observe())
    samples = bootstrap._pair([first, second])
    require((first["boot"], first["session"]) ==
            (initialized[-1]["boot"], initialized[-1]["session"]), "activationContextChanged")
    require(initialized[-1]["checked_ns"] <= first["checked_ns"], "staleContext")
    ended = clock()
    require(type(started) is int and type(ended) is int and
            0 < started <= first["checked_ns"] <= second["checked_ns"] <= ended and
            ended - started <= bootstrap.WINDOW_NS, "staleContext")
    _check(owner, sealed, snapshot)
    return samples


def _chain(snapshot, sealed, seal):
    rows = snapshot["artifacts"]
    intent_raw = seals._unhex(rows[INTENT]["hex"], MAX_ACK)
    intent = seals._canonical(intent_raw, MAX_ACK)
    seals._keys(intent, "schema activation_id seal_sha256 completion_id directory root_before marker_stamp samples")
    _id(intent["activation_id"])
    samples = bootstrap._pair(intent["samples"])
    expected = dict(schema="legacyActivationIntent/v1", activation_id=intent["activation_id"],
                    seal_sha256=seal.trusted_sha256, completion_id=sealed["transaction_id"],
                    directory=sealed["directory"], root_before=sealed["stamps"][0],
                    marker_stamp=sealed["stamps"][1], samples=samples)
    _equal(intent, expected, "activationIntentMismatch")
    receipt = seals._canonical(seals._unhex(rows[RECEIPT]["hex"], MAX_ACK), MAX_ACK)
    seals._keys(receipt, "schema activation_id seal_sha256 intent_sha256 intent_stamp root_before")
    seals._stamp(receipt["root_before"])
    _equal(receipt["root_before"][:4], sealed["stamps"][0][:4])
    expected = dict(schema="legacyActivationReceipt/v1", activation_id=intent["activation_id"],
                    seal_sha256=seal.trusted_sha256, intent_sha256=bootstrap.digest(intent_raw),
                    intent_stamp=rows[INTENT]["stamp"], root_before=receipt["root_before"])
    _equal(receipt, expected, "activationReceiptMismatch")
    _equal(rows[STAGED], rows[RECEIPT], "invalidActivationTopology")
    return intent["activation_id"], samples


@dataclass(frozen=True)
class TrustedActivation:
    raw: bytes
    trusted_sha256: str
    provenance: str


@dataclass(frozen=True)
class TrustedTransition:
    raw: bytes
    trusted_sha256: str
    provenance: str


def _data(value, kind):
    require(type(value) is kind, "untrustedActivationEvidence")
    bootstrap._pin(value.raw, value.trusted_sha256, MAX_ACK)
    bootstrap._provenance(value.provenance)
    data = seals._canonical(value.raw, MAX_ACK)
    seals._keys(data, "schema activation_id seal_sha256 provenance directory snapshot samples")
    require(data["schema"] == ("legacyActivation/v1" if kind is TrustedActivation else
                               "legacyActivationTransition/v1"), "invalidActivationSchema")
    _id(data["activation_id"])
    require(data["provenance"] == value.provenance and type(data["directory"]) is str,
            "activationProvenanceMismatch")
    require(type(data["seal_sha256"]) is str and
            re.fullmatch(r"[0-9a-f]{64}", data["seal_sha256"]) is not None,
            "invalidActivationSealDigest")
    bootstrap._pair(data["samples"])
    snapshot = data["snapshot"]
    seals._keys(snapshot, "root_stamp marker_stamp artifacts")
    seals._stamp(snapshot["root_stamp"])
    seals._stamp(snapshot["marker_stamp"])
    seals._keys(snapshot["artifacts"], " ".join(ARTIFACTS))
    for entry in snapshot["artifacts"].values():
        seals._keys(entry, "hex sha256 stamp")
        raw = seals._unhex(entry["hex"], MAX_ACK)
        bootstrap._pin(raw, entry["sha256"], MAX_ACK)
        seals._stamp(entry["stamp"])
    return data


def load_activation(raw, *, trusted_sha256, provenance):
    value = TrustedActivation(raw, trusted_sha256, provenance)
    _data(value, TrustedActivation)
    return value


def load_transition(raw, *, trusted_sha256, provenance):
    value = TrustedTransition(raw, trusted_sha256, provenance)
    _data(value, TrustedTransition)
    return value


def _record(kind, activation_id, seal, sealed, snapshot, samples, provenance):
    raw = bootstrap.encode(dict(schema="legacyActivation/v1" if kind is TrustedActivation else
                                "legacyActivationTransition/v1", activation_id=activation_id,
                                seal_sha256=seal.trusted_sha256, provenance=provenance,
                                directory=sealed["directory"], snapshot=snapshot, samples=samples))
    value = kind(raw, bootstrap.digest(raw), provenance)
    _data(value, kind)
    return value


def _validate(owner, value, kind, seal, baseline, history, history_pin, observe, clock):
    data = _data(value, kind)
    sealed = seals._seal_data(seal)
    initialized = seals._audit(sealed, baseline, history, history_pin)
    require(data["seal_sha256"] == seal.trusted_sha256 and
            data["directory"] == sealed["directory"], "activationSealMismatch")
    snapshot = data["snapshot"]
    _equal(snapshot["marker_stamp"], sealed["stamps"][1], "activationMarkerChanged")
    _check(owner, sealed, snapshot)
    activation_id, prior = _chain(snapshot, sealed, seal)
    require(data["activation_id"] == activation_id, "activationIdentityMismatch")
    for pair in (prior, data["samples"]):
        require((pair[-1]["boot"], pair[-1]["session"]) ==
                (initialized[-1]["boot"], initialized[-1]["session"]) and
                initialized[-1]["checked_ns"] <= pair[0]["checked_ns"], "activationContextChanged")
    require(prior[-1]["checked_ns"] <= data["samples"][0]["checked_ns"], "staleContext")
    samples = _context(owner, sealed, snapshot, data["samples"], observe, clock)
    return data, sealed, samples


def activate(owner, seal, baseline, *, history, trusted_history_sha256, observe, clock,
             provenance, checkpoint_sink=None, boundary=lambda stage: None):
    """Durably publish activation, never launch or change the clean marker.

    Optional trusted checkpoint_sink independently retains post-publication
    transition evidence. It must preserve bytes/pin/provenance, never merely hash
    a later receipt. Failure or absence means crash reconciliation has no witness.
    Returned completion acknowledgement likewise needs independent retention.
    """
    bootstrap._provenance(provenance)
    require(checkpoint_sink is None or callable(checkpoint_sink), "invalidCheckpointSink")
    candidate = seals.preflight(owner, seal, baseline, history=history,
        trusted_history_sha256=trusted_history_sha256, observe=observe, clock=clock)
    sealed = seals._seal_data(seal)
    snapshot = _snapshot(owner, sealed, ())
    _equal(snapshot["root_stamp"], sealed["stamps"][0])
    activation_id = uuid.uuid4().hex
    intent = bootstrap.encode(dict(schema="legacyActivationIntent/v1", activation_id=activation_id,
        seal_sha256=seal.trusted_sha256, completion_id=sealed["transaction_id"],
        directory=owner.directory, root_before=snapshot["root_stamp"],
        marker_stamp=snapshot["marker_stamp"], samples=candidate["current_samples"]))
    root = bootstrap._root(owner)
    boundary("activationVerified")
    _check(owner, sealed, snapshot)
    stamp, root_stamp = bootstrap._write_new(root, INTENT, intent, boundary, "intent")
    flush_directory(root)
    boundary("intentDirectoryFlushed")
    snapshot = _snapshot(owner, sealed, (INTENT,))
    _equal(snapshot["root_stamp"], json.loads(bootstrap.encode(root_stamp)))
    _equal(snapshot["artifacts"][INTENT]["stamp"], json.loads(bootstrap.encode(stamp)))
    require(snapshot["artifacts"][INTENT]["hex"] == intent.hex(), "activationIntentMismatch")
    receipt = bootstrap.encode(dict(schema="legacyActivationReceipt/v1", activation_id=activation_id,
        seal_sha256=seal.trusted_sha256, intent_sha256=bootstrap.digest(intent),
        intent_stamp=snapshot["artifacts"][INTENT]["stamp"], root_before=snapshot["root_stamp"]))
    _check(owner, sealed, snapshot)
    stamp, root_stamp = bootstrap._write_new(root, STAGED, receipt, boundary, "receipt")
    staged = _snapshot(owner, sealed, (INTENT, STAGED))
    _equal(staged["root_stamp"], json.loads(bootstrap.encode(root_stamp)))
    _equal(staged["artifacts"][INTENT], snapshot["artifacts"][INTENT])
    _equal(staged["artifacts"][STAGED]["stamp"], json.loads(bootstrap.encode(stamp)))
    require(staged["artifacts"][STAGED]["hex"] == receipt.hex(), "activationReceiptMismatch")
    os.link(STAGED, RECEIPT, src_dir_fd=root, dst_dir_fd=root, follow_symlinks=False)
    snapshot = _snapshot(owner, sealed, ARTIFACTS)
    # Only our link-count/ctime and root metadata changed at publication.
    published_stamp = snapshot["artifacts"][STAGED]["stamp"]
    require(published_stamp[:4] == staged["artifacts"][STAGED]["stamp"][:4] and
            published_stamp[5:7] == staged["artifacts"][STAGED]["stamp"][5:7] and
            snapshot["artifacts"][STAGED]["hex"] == receipt.hex(), "activationPublicationChanged")
    _equal(snapshot["artifacts"][INTENT], staged["artifacts"][INTENT])
    _chain(snapshot, sealed, seal)
    boundary("receiptPublished")
    _check(owner, sealed, snapshot)
    samples = _context(owner, sealed, snapshot, candidate["current_samples"], observe, clock)
    transition = _record(TrustedTransition, activation_id, seal, sealed, snapshot, samples, provenance)
    if checkpoint_sink is not None:
        checkpoint_sink(transition)
    boundary("transitionRetained")
    _check(owner, sealed, snapshot)
    flush_directory(root)
    boundary("activationDirectoryFlushed")
    samples = _context(owner, sealed, snapshot, samples, observe, clock)
    acknowledgement = _record(TrustedActivation, activation_id, seal, sealed, snapshot, samples, provenance)
    boundary("activationAcknowledged")
    _check(owner, sealed, snapshot)
    return acknowledgement


def reconcile(owner, transition, seal, baseline, *, history, trusted_history_sha256,
              observe, clock, provenance, boundary=lambda stage: None):
    """Explicitly establish NEW durability from a separately acquired checkpoint.

    No witness means rejection. Complete-looking files cannot synthesize one.
    This never asserts the previous writer reached its flush or changes names.
    """
    bootstrap._provenance(provenance)
    data, sealed, samples = _validate(owner, transition, TrustedTransition, seal, baseline,
                                     history, trusted_history_sha256, observe, clock)
    root = bootstrap._root(owner)
    for name in (INTENT, STAGED):
        fd = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
        try:
            _equal(json.loads(bootstrap.encode(fingerprint(os.fstat(fd)))),
                   data["snapshot"]["artifacts"][name]["stamp"])
            flush_file(fd)
        finally:
            os.close(fd)
        boundary("reconcileIntentFlushed" if name == INTENT else "reconcileReceiptFlushed")
        _check(owner, sealed, data["snapshot"])
    flush_directory(root)
    boundary("reconcileDirectoryFlushed")
    samples = _context(owner, sealed, data["snapshot"], samples, observe, clock)
    result = _record(TrustedActivation, data["activation_id"], seal, sealed,
                     data["snapshot"], samples, provenance)
    _check(owner, sealed, data["snapshot"])
    return result


@dataclass(frozen=True)
class ActivationRequest:
    acknowledgement: TrustedActivation
    seal: seals.TrustedSeal
    baseline: bootstrap.TrustedBaseline
    history: bytes
    trusted_history_sha256: str
    observe: object
    clock: object
    boundary: object = lambda stage: None


def consume(owner, request, run_id):
    """The actual launch gate calls this before it returns marker ownership.

    This reserves one identified run, not a foreground grant. All caller-side
    window, target, ledger and input checks still apply. The consumption fence is
    permanent, including if admission crashes or later cleanup restores clean.
    """
    require(type(request) is ActivationRequest, "untrustedActivationRequest")
    _id(run_id)
    require(callable(request.observe) and callable(request.clock) and callable(request.boundary),
            "invalidActivationRequest")
    data, sealed, samples = _validate(owner, request.acknowledgement, TrustedActivation,
        request.seal, request.baseline, request.history, request.trusted_history_sha256,
        request.observe, request.clock)
    root = bootstrap._root(owner)
    request.boundary("consumptionVerified")
    _check(owner, sealed, data["snapshot"])
    raw = bootstrap.encode(dict(schema="legacyActivationConsumption/v1", run_id=run_id,
        activation_id=data["activation_id"], activation_sha256=request.acknowledgement.trusted_sha256,
        seal_sha256=request.seal.trusted_sha256, samples=samples))
    stamp, root_stamp = bootstrap._write_new(root, CONSUMED, raw, request.boundary, "consumption")
    flush_directory(root)
    request.boundary("consumptionDirectoryFlushed")
    snapshot = _snapshot(owner, sealed, (*ARTIFACTS, CONSUMED))
    _equal(snapshot["root_stamp"], json.loads(bootstrap.encode(root_stamp)))
    for name in ARTIFACTS:
        _equal(snapshot["artifacts"][name], data["snapshot"]["artifacts"][name])
    _equal(snapshot["artifacts"][CONSUMED]["stamp"], json.loads(bootstrap.encode(stamp)))
    require(snapshot["artifacts"][CONSUMED]["hex"] == raw.hex(), "consumptionChanged")
    samples = _context(owner, sealed, snapshot, samples, request.observe, request.clock)
    unresolved = b"unresolved:" + run_id.encode("ascii")
    owner.write_marker(unresolved)
    marker_stamp = bootstrap._stamps(owner)[1]
    request.boundary("admissionMarkerWritten")
    flush_file(owner._fd)
    request.boundary("admissionMarkerFlushed")
    ended = request.clock()
    require(type(ended) is int and samples[-1]["checked_ns"] <= ended <=
            samples[0]["checked_ns"] + bootstrap.WINDOW_NS, "staleContext")
    snapshot["marker_stamp"] = marker_stamp
    _check(owner, sealed, snapshot, marker=unresolved)
