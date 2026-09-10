"""Explicit diagnostic CLI; never initializes, activates, clears or launches.

Storage commands mutate only caller-selected disposable roots using existing
provisioning. Inspection borrows the existing marker lock read-only. Caller pins
and location-review text are trusted operator inputs, not machine attestations.
Reports are observations only and cannot be supplied as activation authority.
"""
import argparse
import json
import os
import stat
import sys

import recovery_acquire as acquire
import recovery_bootstrap as bootstrap
import recovery_provision as provision
from recovery_probe import capture_bounded_context
from recovery_snapshot import MarkerLock, _Snapshot, fingerprint, require
from runtime_root import trusted_runtime_root


def _read(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= limit,
                'missingOrOversizeEvidence')
        raw = os.pread(fd, limit + 1, 0)
        require(len(raw) == before.st_size and fingerprint(os.fstat(fd)) == fingerprint(before),
                'evidenceChanged')
        return raw
    finally:
        os.close(fd)


def _inspect_trusted(marker_directory, baseline, *, observe, clock):
    """Observe one authenticated baseline while holding its original marker."""
    directory, stamps, old_samples = bootstrap._baseline_data(baseline)
    require(marker_directory == directory, 'baselineNamespaceMismatch')
    owner = MarkerLock.acquire(marker_directory, create=False)
    try:
        current_stamps, samples, _ = bootstrap._observe_locked(owner, observe, clock, stamps)
        require(samples[0]['boot'] != old_samples[0]['boot'], 'sameBoot')
        return directory, current_stamps, samples
    finally:
        owner.close()


def _observation_report(result, directory, fingerprints, samples, baseline, history_sha256):
    # Reports remain non-authorizing even if every read-only check passes.
    return dict(result=result, marker_directory=directory,
        marker_unchanged=True, marker_class='legacyUnresolved', fingerprints=fingerprints,
        samples=samples, baseline_sha256=baseline.trusted_sha256,
        history_sha256=history_sha256, provenance=baseline.provenance,
        historical_outcome='failedOrUnknownNonRetryable')


def inspect_legacy(args, *, observe, clock):
    # Authenticate original bytes BEFORE touching the runtime namespace.
    baseline = bootstrap.load_baseline(_read(args.baseline, bootstrap.MAX_BASELINE),
        trusted_sha256=args.baseline_sha256, provenance=args.provenance)
    bootstrap._pin(_read(args.history, bootstrap.MAX_HISTORY), args.history_sha256,
                   bootstrap.MAX_HISTORY)
    directory, fingerprints, samples = _inspect_trusted(
        args.marker_directory, baseline, observe=observe, clock=clock)
    return _observation_report('legacyPreflightObserved', directory, fingerprints, samples,
                               baseline, args.history_sha256)


def _acquired_namespaces(args):
    paths = [args.marker_directory, args.evidence_directory,
             args.anchor_directory, args.archive_directory]
    for index, first in enumerate(paths):
        for second in paths[index + 1:]:
            provision._separate(first, second)


def inspect_acquired(args, *, observe, clock):
    # Establish the complete explicit topology before loading/flushing retained
    # witnesses. load_acquired returns the already authenticated baseline and
    # acquisition provenance; no temporary export or caller-created pin exists.
    _acquired_namespaces(args)
    baseline, metadata = acquire.load_acquired(args)
    directory, fingerprints, samples = _inspect_trusted(
        args.marker_directory, baseline, observe=observe, clock=clock)
    report = _observation_report('acquiredPreflightObserved', directory, fingerprints, samples,
                                 baseline, metadata['history_sha256'])
    report['acquisition'] = metadata
    return report


def storage(args):
    bootstrap._provenance(args.location_review)
    operation = provision.provision if args.operation == 'storage-provision' else provision.load
    slots = operation(args.evidence_directory, trusted_anchor_directory=args.anchor_directory)
    # Diagnostic post-operation metadata only, never new trust pins. Reuse the
    # no-symlink walker and compare each slot to the identities just validated.
    tree = _Snapshot()
    try:
        roots = {}
        for role, path in (('evidence', args.evidence_directory), ('anchor', args.anchor_directory)):
            fd = tree._trusted_directory(path)
            roots[role] = fingerprint(os.fstat(fd))
        for slot in slots.values():
            fd = tree._trusted_directory(slot.directory)
            require(fingerprint(os.fstat(fd))[0] == slot.trusted_identity, 'witnessDirectoryChanged')
        provision._stable(tree, dict(tree._directories))
    finally:
        tree._close()
    return dict(result='disposableStorageProvisioned' if args.operation == 'storage-provision'
                else 'disposableStorageReloaded',
        evidence_directory=args.evidence_directory, anchor_directory=args.anchor_directory,
        location_review=args.location_review, location_policy_verified=False,
        validated_root_mode='0700', validated_owner_uid=os.geteuid(),
        root_fingerprints=roots,
        flush_calls_completed=True, power_loss_verified=False,
        slots={name: dict(directory=slot.directory, identity=slot.trusted_identity)
               for name, slot in slots.items()})


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest='operation', required=True)
    for name in ('storage-provision', 'storage-reload'):
        command = commands.add_parser(name, help='Disposable storage only; reload also flushes files')
        command.add_argument('--evidence-directory', required=True,
                             help='Explicit canonical private root; already exists, empty for provision')
        command.add_argument('--anchor-directory', required=True,
                             help='Independent configured private root; never discovered from evidence')
        command.add_argument('--location-review', required=True,
                             help='Operator record of location/sync review, or explicit fixture-only limitation')
    command = commands.add_parser('inspect-legacy', help='Read-only observation; never a recovery grant')
    for name in ('marker-directory', 'baseline', 'baseline-sha256', 'history', 'history-sha256', 'provenance'):
        command.add_argument('--' + name, required=True)
    command = commands.add_parser('inspect-acquired',
                                  help='Read-only observation of retained acquisition')
    for name in ('marker-directory', 'evidence-directory', 'anchor-directory',
                 'archive-directory', 'inventory-library', 'inventory-sha256'):
        command.add_argument('--' + name, required=True)
    return result


def main(argv=None, *, observe=None, clock=None):
    args = parser().parse_args(argv)
    report = dict(schema='recoveryPreflight/v1', operation=args.operation,
                  launch_eligible=False, native_recovery_verified=False, platform=sys.platform)
    if args.operation == 'inspect-acquired':
        report['inventory_sha256'] = args.inventory_sha256
    try:
        if args.operation in ('inspect-legacy', 'inspect-acquired'):
            inventory_library = None
            if args.operation == 'inspect-acquired':
                inventory_library = acquire.inventory_configuration(
                    args.inventory_library, args.inventory_sha256)
                require(observe is None, 'ambiguousInventoryObserver')
            if observe is None or clock is None:
                trusted_runtime_root(args.marker_directory)
            if clock is None:
                from supervisor import mac_clock
                clock = mac_clock()
            if observe is None:
                if inventory_library is None:
                    observe = lambda: capture_bounded_context(clock=clock)
                else:
                    observe = lambda: capture_bounded_context(
                        clock=clock, inventory_library=inventory_library)
            operation = inspect_legacy if args.operation == 'inspect-legacy' else inspect_acquired
            report.update(operation(args, observe=observe, clock=clock))
        else:
            report.update(storage(args))
        code = 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            OverflowError, RecursionError) as error:
        # Avoid echoing evidence bytes or OS error filenames. Named validation
        # failures are short contract reasons; malformed input is generic.
        reason = str(error) if isinstance(error, ValueError) else type(error).__name__
        if not reason or len(reason) > 100 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ' for c in reason):
            reason = type(error).__name__
        report.update(result='unresolved', reason=reason)
        code = 1
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
