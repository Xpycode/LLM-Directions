"""Explicit independent witness slots for the trusted native caller.

A slot is a pre-provisioned private directory OUTSIDE the runtime/seal namespace.
Its identity must be authenticated by the caller before acquisition, never read
from a report or obtained by statting an arbitrary surviving directory on reload.
Only this trusted writer may populate it. Same-UID malicious writers and inode
reuse after deletion are outside this cooperating-caller trust model.

No provisioning, discovery, CLI, marker access, launch, repair or deletion occurs.
Load establishes durability anew for a witness already acquired by the original
caller; it does not assert that the previous retention call completed.
"""
import os
import stat

import recovery_activation as activation
import recovery_bootstrap as bootstrap
import recovery_seal as seals
from recovery_snapshot import _Snapshot, fingerprint, identity, require
from recovery_storage import flush_file, flush_directory

NAMES = ("witness.tmp", "witness.json")
KINDS = {
    "baseline": (bootstrap.TrustedBaseline, bootstrap.load_baseline, bootstrap.MAX_BASELINE),
    "seal": (seals.TrustedSeal, seals.load_seal, seals.MAX_SEAL),
    "transition": (activation.TrustedTransition, activation.load_transition, activation.MAX_ACK),
    "activation": (activation.TrustedActivation, activation.load_activation, activation.MAX_ACK),
}
MAX_WITNESS = 2 * seals.MAX_SEAL + 4096


def _root(tree, directory, pin):
    require(type(pin) is tuple and len(pin) == 2 and
            all(type(n) is int and n >= 0 for n in pin), "untrustedWitnessDirectory")
    root = tree._trusted_directory(directory)
    require(identity(os.fstat(root)) == pin, "witnessDirectoryChanged")
    return root


def check_empty(directory, *, trusted_directory_identity):
    """Preflight a previously provisioned slot without creating anything."""
    tree = _Snapshot()
    try:
        root = _root(tree, directory, trusted_directory_identity)
        stamp = fingerprint(os.fstat(root))
        seals._names(root, ())
        seals._external_recheck(tree, root, stamp)
    finally:
        tree._close()


def _encode(value):
    matches = [kind for kind, row in KINDS.items() if type(value) is row[0]]
    require(len(matches) == 1, "untrustedWitness")
    kind = matches[0]
    KINDS[kind][1](value.raw, trusted_sha256=value.trusted_sha256, provenance=value.provenance)
    raw = bootstrap.encode(dict(schema="independentWitness/v1", kind=kind,
        raw_hex=value.raw.hex(), trusted_sha256=value.trusted_sha256, provenance=value.provenance))
    require(len(raw) <= MAX_WITNESS, "witnessTooLarge")
    return raw


def _decode(raw, kind):
    require(type(kind) is str and kind in KINDS, "invalidWitnessKind")
    data = seals._canonical(raw, MAX_WITNESS)
    seals._keys(data, "schema kind raw_hex trusted_sha256 provenance")
    require(data["schema"] == "independentWitness/v1" and data["kind"] == kind,
            "witnessKindMismatch")
    return KINDS[kind][1](seals._unhex(data["raw_hex"], KINDS[kind][2]),
        trusted_sha256=data["trusted_sha256"], provenance=data["provenance"])


def _check(tree, root, root_stamp, raw, stamp):
    seals._external_recheck(tree, root, root_stamp)
    seals._names(root, NAMES)
    require(stamp[4] == 2, "invalidWitnessTopology")
    for name in NAMES:
        bootstrap._check_file(root, name, raw, stamp)
    seals._external_recheck(tree, root, root_stamp)


def retain(directory, value, *, trusted_directory_identity, boundary=lambda stage: None):
    """Retain exact acquired bytes/pin/provenance once; failure leaves all names.

    Call directly from the transition sink or after the original seal/activation
    function returns. Never construct value from surviving runtime receipts.
    The caller must provision/flush the slot and independently retain its identity
    beforehand. This function never creates that trust anchor retrospectively.
    """
    raw = _encode(value)
    tree = _Snapshot()
    try:
        root = _root(tree, directory, trusted_directory_identity)
        seals._names(root, ())
        stamp, root_stamp = bootstrap._write_new(root, NAMES[0], raw, boundary, "witness")
        seals._external_recheck(tree, root, root_stamp)
        os.link(NAMES[0], NAMES[1], src_dir_fd=root, dst_dir_fd=root, follow_symlinks=False)
        published = fingerprint(os.stat(NAMES[0], dir_fd=root, follow_symlinks=False))
        require(published[:4] == stamp[:4] and published[5:7] == stamp[5:7],
                "witnessPublicationChanged")
        root_stamp = fingerprint(os.fstat(root))
        boundary("witnessPublished")
        _check(tree, root, root_stamp, raw, published)
        flush_directory(root)
        boundary("witnessDirectoryFlushed")
        _check(tree, root, root_stamp, raw, published)
    finally:
        tree._close()


def load(directory, *, kind, trusted_directory_identity):
    """Explicit trusted-slot reload, with a new file and directory flush.

    The stored hash is trusted ONLY through the previously authenticated slot and
    exclusive original writer. It is not authentication of arbitrary JSON.
    Complete publication can survive interrupted retention: its payload was
    acquired before retention started. A transition remains a transition and
    must pass explicit activation.reconcile; it cannot become completion here.
    """
    tree = _Snapshot()
    try:
        root = _root(tree, directory, trusted_directory_identity)
        seals._names(root, NAMES)
        root_stamp = fingerprint(os.fstat(root))
        fd = tree._open(NAMES[1], os.O_RDWR, root)
        info = os.fstat(fd)
        # _regular requires one link; these are intentionally two names/one inode.
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
                stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 2 and
                0 < info.st_size <= MAX_WITNESS, "unsafeWitnessFile")
        stamp = fingerprint(info)
        raw = os.pread(fd, info.st_size + 1, 0)
        require(len(raw) == info.st_size and fingerprint(os.fstat(fd)) == stamp,
                "witnessChanged")
        value = _decode(raw, kind)
        _check(tree, root, root_stamp, raw, stamp)
        flush_file(fd)
        flush_directory(root)
        require(fingerprint(os.fstat(fd)) == stamp, "witnessChanged")
        _check(tree, root, root_stamp, raw, stamp)
        return value
    finally:
        tree._close()
