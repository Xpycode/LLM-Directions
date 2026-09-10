"""Prospective baseline acquisition; no initialization, activation or launch.

Explicit fresh private roots only. Archive bytes are acquired NOW, not evidence
authenticated at the old crash. Their digest is bound inside a newly observed,
independently retained baseline. Failed attempts preserve every artifact.
"""
import argparse
import json
import os
import stat
import uuid

import recovery_bootstrap as bootstrap
import recovery_provision as provision
import recovery_retention as retention
import recovery_seal as seals
from recovery_probe import ProbeFailure, capture_bounded_context
from recovery_snapshot import MarkerLock, _Snapshot, fingerprint, require
from recovery_storage import flush_directory


def namespaces(args):
    paths = [args.evidence_directory, args.anchor_directory, args.archive_directory]
    if args.operation == 'capture':
        paths.append(args.marker_directory)
    for i, first in enumerate(paths):
        for second in paths[i + 1:]:
            provision._separate(first, second)


def read_history_source(path):
    require(type(path) is str and path.startswith('/') and not path.startswith('//') and
            os.path.normpath(path) == path, 'invalidHistoryPath')
    tree = _Snapshot()
    try:
        fd = tree._open('/', os.O_RDONLY | os.O_DIRECTORY)
        components = path.split('/')[1:]
        for part in components[:-1]:
            fd = tree._open(part, os.O_RDONLY | os.O_DIRECTORY, fd)
        fd = tree._open(components[-1], os.O_RDONLY, fd)
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= bootstrap.MAX_HISTORY,
                'invalidHistorySource')
        raw = os.pread(fd, bootstrap.MAX_HISTORY + 1, 0)
        require(len(raw) == info.st_size and fingerprint(os.fstat(fd)) == fingerprint(info),
                'historySourceChanged')
        for parent, name, opened in tree._edges:
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            require((named.st_dev, named.st_ino) == (os.fstat(opened).st_dev, os.fstat(opened).st_ino),
                    'historySourceChanged')
        return raw
    finally:
        tree._close()


def load_acquired(args):
    namespaces(args)
    slots = provision.load(args.evidence_directory, trusted_anchor_directory=args.anchor_directory)
    slot = slots['baseline']
    baseline = retention.load(slot.directory, kind='baseline', trusted_directory_identity=slot.trusted_identity)
    data = json.loads(baseline.raw)
    require(data.get('schema') == 'legacyBaseline/v1' and
            data['provenance'] == baseline.provenance, 'acquisitionProvenanceMismatch')
    metadata = seals._canonical(baseline.provenance.encode(), 4096)
    seals._keys(metadata, 'schema acquisition_id history_sha256 history_bytes classification historical_outcome operator_record')
    require(metadata['schema'] == 'prospectiveAcquisition/v1' and
            metadata['classification'] == 'historicalCopyAcquiredNow' and
            metadata['historical_outcome'] == 'failedOrUnknownNonRetryable' and
            type(metadata['acquisition_id']) is str and
            uuid.UUID(hex=metadata['acquisition_id']).hex == metadata['acquisition_id'] and
            int(metadata['acquisition_id'], 16) != 0 and
            type(metadata['history_bytes']) is int and 0 < metadata['history_bytes'] <= bootstrap.MAX_HISTORY,
            'invalidAcquisitionProvenance')
    bootstrap._provenance(metadata['operator_record'])
    tree = _Snapshot()
    try:
        root = tree._trusted_directory(args.archive_directory)
        stamp = fingerprint(os.fstat(root))
        seals._names(root, ('history.json',))
        history = tree._file(root, 'history.json', bootstrap.MAX_HISTORY)
        bootstrap._pin(history, metadata['history_sha256'], bootstrap.MAX_HISTORY)
        require(len(history) == metadata['history_bytes'], 'historyLengthMismatch')
        seals._external_recheck(tree, root, stamp)
        bootstrap._check_file(root, 'history.json', history, tree._files[-1][3])
        return baseline, metadata
    finally:
        tree._close()


def capture(args, *, observe, clock):
    # The caller report identifies which of the four observations failed without
    # altering the helper wire contract or attributing new detail to old reports.
    observation = 0
    original_observe = observe
    def observe():
        nonlocal observation
        observation += 1
        try:
            return original_observe()
        except ProbeFailure as error:
            error.acquisition_observation = observation
            raise

    namespaces(args)
    bootstrap._provenance(args.operator_record)
    history = read_history_source(args.history_source)
    metadata = dict(schema='prospectiveAcquisition/v1', acquisition_id=uuid.uuid4().hex,
        history_sha256=bootstrap.digest(history), history_bytes=len(history),
        classification='historicalCopyAcquiredNow', historical_outcome='failedOrUnknownNonRetryable',
        operator_record=args.operator_record)
    provenance = bootstrap.encode(metadata).decode()
    bootstrap._provenance(provenance)
    tree = _Snapshot()
    owner = None
    try:
        archive = tree._trusted_directory(args.archive_directory)
        seals._names(archive, ())
        # All roots are explicit caller configuration established before capture.
        # Provision rejects reused/partial roots; it never repairs an attempt.
        slots = provision.provision(args.evidence_directory, trusted_anchor_directory=args.anchor_directory)
        owner = MarkerLock.acquire(args.marker_directory, create=False)
        stamps = bootstrap._stamps(owner)
        archive_stamp, directory_stamp = bootstrap._write_new(archive, 'history.json', history,
                                                             lambda stage: None, 'history')
        flush_directory(archive)
        for parent, _, fd in tree._edges:
            if fd == archive:
                flush_directory(parent)
        seals._external_recheck(tree, archive, directory_stamp)
        bootstrap._check_file(archive, 'history.json', history, archive_stamp)
        raw = bootstrap.capture_baseline(owner, observe=observe, clock=clock, provenance=provenance)
        require(bootstrap._stamps(owner) == stamps, 'interveningStateChange')
        # This digest is taken directly by the NEW original acquisition writer.
        baseline = bootstrap.load_baseline(raw, trusted_sha256=bootstrap.digest(raw), provenance=provenance)
        slots['baseline'].retain(baseline)
        _, final_samples, _ = bootstrap._observe_locked(owner, observe, clock, stamps)
        first = json.loads(raw)['samples'][0]
        require((first['boot'], first['session']) ==
                (final_samples[0]['boot'], final_samples[0]['session']), 'contextDrift')
        seals._external_recheck(tree, archive, directory_stamp)
        bootstrap._check_file(archive, 'history.json', history, archive_stamp)
        return baseline, metadata
    finally:
        if owner is not None:
            owner.close()
        tree._close()


def main(argv=None, *, observe=None, clock=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    for operation in ('capture', 'reload'):
        command = commands.add_parser(operation)
        for field in ('evidence-directory', 'anchor-directory', 'archive-directory'):
            command.add_argument('--' + field, required=True)
        if operation == 'capture':
            for field in ('marker-directory', 'history-source', 'operator-record'):
                command.add_argument('--' + field, required=True)
    args = parser.parse_args(argv)
    report = dict(schema='prospectiveAcquisitionReport/v1', operation=args.operation,
                  launch_eligible=False, native_recovery_verified=False)
    try:
        if args.operation == 'capture':
            if clock is None:
                from supervisor import mac_clock
                clock = mac_clock()
            if observe is None:
                observe = lambda: capture_bounded_context(clock=clock)
            baseline, metadata = capture(args, observe=observe, clock=clock)
        else:
            baseline, metadata = load_acquired(args)
        report.update(result='prospectiveBaselineRetained' if args.operation == 'capture' else 'acquiredEvidenceReloaded',
            baseline_sha256=baseline.trusted_sha256, acquisition=metadata,
            marker_unchanged=True if args.operation == 'capture' else None)
        code = 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, RecursionError) as error:
        report.update(result='unresolved', reason=type(error).__name__)
        if isinstance(error, ProbeFailure):
            report['failure_stage'] = error.stage
            observation = getattr(error, 'acquisition_observation', None)
            if type(observation) is int and 1 <= observation <= 4:
                report['failure_observation'] = observation
                report['failure_phase'] = 'baseline' if observation <= 2 else 'final'
        code = 1
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
