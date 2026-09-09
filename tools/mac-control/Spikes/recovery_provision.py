"""One-time evidence slots with an independent, explicitly trusted local anchor.

The anchor directory is installer/caller configuration, NEVER a path selected
from evidence or discovered at restart. It is the root of trust under the existing
cooperating same-UID model; its original writer is trusted. No default paths,
installation, native marker access, launch, overwrite, repair or automatic retry.
Both roots must already exist privately in a persistent deployment location.
"""
import os
import stat
import uuid

import recovery_bootstrap as bootstrap
import recovery_seal as seals
from recovery_caller import WitnessSlot
from recovery_snapshot import _Snapshot, fingerprint, identity, require
from recovery_storage import flush_file, flush_directory

ROLES = ("baseline", "seal", "transition", "activation", "reconciliation")
NAMES = ("anchor.fence", "anchor.tmp", "anchor.json")
FENCE = b"independent-witness-provisioning/v1\n"
MAX_ANCHOR = 16384


def _separate(first, second):
    common = os.path.commonpath([first, second])
    require(common not in (first, second), "anchorNamespacesNotSeparate")


def _roots(tree, evidence, anchor):
    evidence, anchor = os.fspath(evidence), os.fspath(anchor)
    _separate(evidence, anchor)
    root = tree._trusted_directory(evidence)
    config = tree._trusted_directory(anchor)
    require(identity(os.fstat(root)) != identity(os.fstat(config)), "anchorNamespacesNotSeparate")
    return evidence, anchor, root, config


def _stable(tree, stamps):
    for fd, stamp in stamps.items():
        seals._external_recheck(tree, fd, stamp)


def _id(value):
    require(type(value) is list and len(value) == 2 and
            all(type(n) is int and n >= 0 for n in value), "invalidAnchorIdentity")
    return tuple(value)


def _manifest(raw, evidence, anchor, root, config):
    data = seals._canonical(raw, MAX_ANCHOR)
    seals._keys(data, "schema transaction_id evidence_directory anchor_directory evidence_identity anchor_identity slots")
    require(data["schema"] == "witnessProvision/v1" and data["evidence_directory"] == evidence and
            data["anchor_directory"] == anchor, "anchorConfigurationMismatch")
    require(type(data["transaction_id"]) is str and len(data["transaction_id"]) == 32 and
            uuid.UUID(hex=data["transaction_id"]).hex == data["transaction_id"] and
            int(data["transaction_id"], 16) != 0, "invalidAnchorTransaction")
    require(_id(data["evidence_identity"]) == identity(os.fstat(root)) and
            _id(data["anchor_identity"]) == identity(os.fstat(config)), "anchorDirectoryChanged")
    seals._keys(data["slots"], " ".join(ROLES))
    ids = [_id(data["slots"][role]) for role in ROLES]
    require(len(set(ids + [identity(os.fstat(root)), identity(os.fstat(config))])) == len(ROLES) + 2,
            "invalidAnchorTopology")
    return data


def _slots(tree, root, data, *, empty=False):
    seals._names(root, ROLES)
    result = {}
    for role in ROLES:
        fd = tree._open(role, os.O_RDONLY | os.O_DIRECTORY, root)
        tree._private_directory(fd)
        require(identity(os.fstat(fd)) == _id(data["slots"][role]), "witnessDirectoryChanged")
        if empty:
            seals._names(fd, ())
        result[fd] = fingerprint(os.fstat(fd))
    return result


def _files(root, raw, stamp, fence_stamp):
    seals._names(root, NAMES)
    require(stamp[4] == 2 and fence_stamp[4] == 1 and stamp[0] != fence_stamp[0],
            "invalidAnchorTopology")
    bootstrap._check_file(root, NAMES[0], FENCE, fence_stamp)
    for name in NAMES[1:]:
        bootstrap._check_file(root, name, raw, stamp)


def _result(evidence, data):
    return {role: WitnessSlot(os.path.join(evidence, role), _id(data["slots"][role])) for role in ROLES}


def provision(evidence_directory, *, trusted_anchor_directory, boundary=lambda stage: None):
    """Create fixed slots and retain their original identities independently.

    Both explicitly selected roots must be private and empty. Parent directory
    flushes retain their existing names. A permanent fence precedes slot creation;
    incomplete attempts cannot be retried. Returned slots grant no input rights.
    """
    tree = _Snapshot()
    try:
        evidence, anchor, root, config = _roots(tree, evidence_directory, trusted_anchor_directory)
        seals._names(root, ())
        seals._names(config, ())
        stamps = {fd: fingerprint(os.fstat(fd)) for fd in (root, config)}
        # These parents were securely opened during the no-symlink path walks.
        for parent, _, fd in tree._edges:
            if fd in (root, config):
                flush_directory(parent)
        _stable(tree, stamps)
        fence_stamp, stamps[config] = bootstrap._write_new(config, NAMES[0], FENCE, boundary, "fence")
        flush_directory(config)
        boundary("fenceDirectoryFlushed")
        _stable(tree, stamps)
        bootstrap._check_file(config, NAMES[0], FENCE, fence_stamp)
        slots = {}
        for role in ROLES:
            _stable(tree, stamps)
            seals._names(root, tuple(slots))
            os.mkdir(role, mode=0o700, dir_fd=root)
            fd = tree._open(role, os.O_RDONLY | os.O_DIRECTORY, root)
            tree._private_directory(fd)
            slots[role] = identity(os.fstat(fd))
            stamps[root], stamps[fd] = fingerprint(os.fstat(root)), fingerprint(os.fstat(fd))
            boundary("slotCreated:" + role)
            flush_directory(fd)
            _stable(tree, stamps)
            seals._names(fd, ())
        flush_directory(root)
        boundary("slotsDirectoryFlushed")
        _stable(tree, stamps)
        raw = bootstrap.encode(dict(schema="witnessProvision/v1", transaction_id=uuid.uuid4().hex,
            evidence_directory=evidence, anchor_directory=anchor, evidence_identity=identity(os.fstat(root)),
            anchor_identity=identity(os.fstat(config)), slots=slots))
        data = _manifest(raw, evidence, anchor, root, config)
        seals._names(config, (NAMES[0],))
        bootstrap._check_file(config, NAMES[0], FENCE, fence_stamp)
        stamp, stamps[config] = bootstrap._write_new(config, NAMES[1], raw, boundary, "manifest")
        _stable(tree, stamps)
        os.link(NAMES[1], NAMES[2], src_dir_fd=config, dst_dir_fd=config, follow_symlinks=False)
        published = fingerprint(os.stat(NAMES[1], dir_fd=config, follow_symlinks=False))
        require(published[:4] == stamp[:4] and published[5:7] == stamp[5:7], "anchorPublicationChanged")
        stamps[config] = fingerprint(os.fstat(config))
        boundary("anchorPublished")
        _files(config, raw, published, fence_stamp)
        _stable(tree, stamps)
        flush_directory(config)
        boundary("anchorDirectoryFlushed")
        _files(config, raw, published, fence_stamp)
        _stable(tree, stamps)
        _slots(tree, root, data, empty=True)
        _stable(tree, stamps)
        return _result(evidence, data)
    finally:
        tree._close()


def load(evidence_directory, *, trusted_anchor_directory):
    """Reload only from explicit trusted configuration and reestablish durability.

    The published original manifest pins slot identities before any witness was
    collected. Do not synthesize those identities from surviving evidence. This
    accepts complete publication after interruption, but never repairs a partial
    transaction or asserts the original provision call finished. Witness contents
    remain separately validated by recovery_retention.load.
    """
    tree = _Snapshot()
    try:
        evidence, anchor, root, config = _roots(tree, evidence_directory, trusted_anchor_directory)
        stamps = {fd: fingerprint(os.fstat(fd)) for fd in (root, config)}
        seals._names(config, NAMES)
        files = []
        for name, links, limit in ((NAMES[0], 1, len(FENCE)), (NAMES[2], 2, MAX_ANCHOR)):
            fd = tree._open(name, os.O_RDWR, config)
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
                    stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == links and
                    0 < info.st_size <= limit, "unsafeAnchorFile")
            stamp = fingerprint(info)
            raw = os.pread(fd, info.st_size + 1, 0)
            require(len(raw) == info.st_size and fingerprint(os.fstat(fd)) == stamp, "anchorChanged")
            files.append((fd, raw, stamp))
        require(files[0][1] == FENCE, "invalidAnchorFence")
        raw, stamp, fence_stamp = files[1][1], files[1][2], files[0][2]
        data = _manifest(raw, evidence, anchor, root, config)
        stamps.update(_slots(tree, root, data))
        _files(config, raw, stamp, fence_stamp)
        _stable(tree, stamps)
        for fd, _, _ in files:
            flush_file(fd)
        # Child directories before the root that names them, then publication.
        for fd in stamps:
            if fd not in (root, config):
                flush_directory(fd)
        flush_directory(root)
        flush_directory(config)
        for parent, _, fd in tree._edges:
            if fd in (root, config):
                flush_directory(parent)
        _files(config, raw, stamp, fence_stamp)
        _stable(tree, stamps)
        return _result(evidence, data)
    finally:
        tree._close()
