"""Offline kernel-boundary tests. No native enumeration or runtime marker access."""
import ctypes as C
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, call, patch

import recovery_context as context
from recovery_verifier import context_snapshot


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.actual_uid = os.geteuid()
        self.kernel = Mock()
        self.kernel.boot.return_value = '12345678-1234-1234-1234-123456789abc'
        self.kernel.session.return_value = (42, 16)
        self.kernel.pids.return_value = (101, 102)
        self.rows = {pid: (pid, 1, 501, 501, 501, 123, pid) for pid in (101, 102)}
        self.paths = {101: '/usr/bin/python3', 102: '/Applications/Editor'}
        self.kernel.process.side_effect = lambda pid: self.rows[pid]
        self.kernel.path.side_effect = lambda pid: self.paths[pid]
        for item in (patch.object(context, '_Kernel', return_value=self.kernel),
                     patch.object(context.os, 'getuid', return_value=501),
                     patch.object(context.os, 'geteuid', return_value=501),
                     patch.object(context.os, 'getpid', return_value=101)):
            item.start()
            self.addCleanup(item.stop)

    def test_empty_inventory_matches_verifier(self):
        result = context.capture_context()
        context_snapshot(result)
        self.assertEqual(result['session'], '42')
        self.assertGreater(result['checked_ns'], 0)
        self.assertEqual(self.kernel.pids.call_count, 3)

    def test_explicit_clock_supplies_transaction_timestamp(self):
        self.assertEqual(context.capture_context(clock=lambda: 987654321)['checked_ns'], 987654321)

    def test_workers_in_any_build_path_block(self):
        for name in ('StopSpikeWorker', 'MacControlExecutor'):
            with self.subTest(name=name):
                self.paths[102] = '/arbitrary/old-build/' + name
                result = context.capture_context()
                self.assertEqual(result['executors'][0]['pid'], 102)
                self.assertEqual(result['executors'][0]['start'], '123-102')
                with self.assertRaises(ValueError):
                    context_snapshot(result)

    def test_unreadable_process_or_path_never_means_absent(self):
        for operation in ('process', 'path', 'pids', 'boot', 'session'):
            with self.subTest(operation=operation):
                method = getattr(self.kernel, operation)
                previous = method.side_effect
                method.side_effect = OSError('unavailable')
                with self.assertRaises(ValueError):
                    context.capture_context()
                method.side_effect = previous

    def test_invalid_enumeration(self):
        for pids in ((), (102,), (101, 101), (101, 0), (101, -1), (101, True)):
            with self.subTest(pids=pids):
                self.kernel.pids.return_value = pids
                with self.assertRaises(ValueError):
                    context.capture_context()

    def test_inventory_failure_cause_and_boundary_are_distinguished_without_retry(self):
        cases = (
            ('inventoryInitialQuery', (OSError('query'),), 1),
            ('inventoryInitialMalformed', ((101, 101),), 1),
            ('inventoryInitialMalformed', ((102,),), 1),
            ('inventoryAfterFirstScanQuery', ((101, 102), OSError('query')), 2),
            ('inventoryAfterFirstScanMalformed', ((101, 102), (101, 101)), 2),
            ('inventoryAfterFirstScanChanged', ((101, 102), (101,)), 2),
            ('inventoryAfterSecondScanQuery',
             ((101, 102), (101, 102), OSError('query')), 3),
            ('inventoryAfterSecondScanMalformed',
             ((101, 102), (101, 102), (101, 101)), 3),
            ('inventoryAfterSecondScanChanged',
             ((101, 102), (101, 102), (101, 102, 103)), 3),
        )
        for expected, samples, calls in cases:
            self.kernel.pids.reset_mock(side_effect=True)
            self.kernel.pids.side_effect = samples
            with self.subTest(expected=expected), self.assertRaises(ValueError) as caught:
                context.capture_context()
            self.assertEqual(caught.exception.stage, expected)
            self.assertEqual(self.kernel.pids.call_count, calls)

    def test_failure_stage_does_not_expose_process_details(self):
        self.kernel.path.side_effect = OSError('private/path/and/process')
        with self.assertRaises(ValueError) as caught:
            context.capture_context()
        self.assertEqual(caught.exception.stage, 'processPath')
        self.assertNotIn('private', str(caught.exception))

    def test_process_identity_cause_and_scan_are_distinguished_without_retry(self):
        first_scan = (self.rows[101], self.rows[101], self.rows[102], self.rows[102])
        cases = (
            ('processIdentityFirstScanRead', (OSError('private process'),), 1),
            ('processIdentityFirstScanMalformed', ((101, 1),), 1),
            ('processIdentitySecondScanRead',
             first_scan + (ValueError('private process'),), 5),
            ('processIdentitySecondScanMalformed', first_scan + ((101, 1),), 5),
        )
        for expected, samples, calls in cases:
            self.kernel.process.reset_mock(side_effect=True)
            self.kernel.process.side_effect = samples
            with self.subTest(expected=expected), self.assertRaises(ValueError) as caught:
                context.capture_context()
            self.assertEqual(caught.exception.stage, expected)
            self.assertEqual(self.kernel.process.call_count, calls)
            self.assertNotIn('private', str(caught.exception))

    def test_native_read_categories_keep_scan_position_and_stop_without_retry(self):
        rows = (self.rows[101], self.rows[101], self.rows[102], self.rows[102])
        for kind in context.PROCESS_IDENTITY_FAILURE_KINDS:
            for before, boundary in (((), 'processIdentityFirstScanRead'),
                                     (rows[:1], 'processRecheckRead'),
                                     (rows, 'processIdentitySecondScanRead')):
                self.kernel.process.reset_mock(side_effect=True)
                self.kernel.process.side_effect = (*before, context.ProcessIdentityFailure(kind))
                with self.subTest(kind=kind, boundary=boundary), \
                        self.assertRaises(context.ContextFailure) as caught:
                    context.capture_context()
                self.assertEqual(caught.exception.stage, boundary + kind)
                self.assertEqual(self.kernel.process.call_count, len(before) + 1)

    def test_first_read_missing_noncaller_is_accepted_only_when_both_inventories_confirm_absence(self):
        self.rows[103] = (103, 1, 501, 501, 501, 123, 103)
        self.paths[103] = '/Applications/Editor'
        self.kernel.pids.side_effect = ((101, 102, 103), (101, 103), (101, 103))
        reads = {}

        def process(pid):
            reads[pid] = reads.get(pid, 0) + 1
            if pid == 102 and reads[pid] == 1:
                raise context.ProcessIdentityFailure('Missing')
            return self.rows[pid]

        self.kernel.process.side_effect = process
        result = context.capture_context()

        self.assertEqual(result['executors'], [])
        self.assertEqual(self.kernel.process.call_args_list,
                         [call(101), call(101), call(102), call(103), call(103),
                          call(101), call(101), call(103), call(103)])
        self.assertEqual(self.kernel.path.call_args_list,
                         [call(101), call(103), call(101), call(103)])

    def test_multiple_first_read_missing_noncallers_are_omitted_from_both_later_scans(self):
        for pid in (103, 104):
            self.rows[pid] = (pid, 1, 501, 501, 501, 123, pid)
            self.paths[pid] = '/Applications/Editor'
        self.kernel.pids.side_effect = ((101, 102, 103, 104), (101, 103), (101, 103))
        reads = {}

        def process(pid):
            reads[pid] = reads.get(pid, 0) + 1
            if pid in (102, 104) and reads[pid] == 1:
                raise context.ProcessIdentityFailure('Missing')
            return self.rows[pid]

        self.kernel.process.side_effect = process
        context.capture_context()

        self.assertEqual(self.kernel.process.call_args_list[:6],
                         [call(101), call(101), call(102), call(103), call(103), call(104)])
        self.assertNotIn(call(102), self.kernel.path.call_args_list)
        self.assertNotIn(call(104), self.kernel.path.call_args_list)

    def test_first_read_missing_must_be_absent_from_middle_inventory(self):
        self.kernel.pids.side_effect = ((101, 102), (101, 102))
        self.kernel.process.side_effect = (
            self.rows[101], self.rows[101], context.ProcessIdentityFailure('Missing'))

        with self.assertRaises(context.ContextFailure) as caught:
            context.capture_context()

        self.assertEqual(caught.exception.stage, 'inventoryAfterFirstScanChanged')
        self.assertEqual(self.kernel.pids.call_count, 2)

    def test_first_read_missing_cannot_reappear_or_be_replaced_after_second_scan(self):
        self.rows[103] = (103, 1, 501, 501, 501, 123, 103)
        self.paths[103] = '/Applications/Editor'
        for final in ((101, 102, 103), (101, 103, 104)):
            self.kernel.pids.reset_mock(side_effect=True)
            self.kernel.process.reset_mock(side_effect=True)
            self.kernel.path.reset_mock(side_effect=True)
            self.kernel.pids.side_effect = ((101, 102, 103), (101, 103), final)
            self.kernel.path.side_effect = lambda pid: self.paths[pid]
            reads = {}

            def process(pid):
                reads[pid] = reads.get(pid, 0) + 1
                if pid == 102 and reads[pid] == 1:
                    raise context.ProcessIdentityFailure('Missing')
                return self.rows[pid]

            self.kernel.process.side_effect = process
            with self.subTest(final=final), self.assertRaises(context.ContextFailure) as caught:
                context.capture_context()
            self.assertEqual(caught.exception.stage, 'inventoryAfterSecondScanChanged')
            self.assertEqual(self.kernel.pids.call_count, 3)

    def test_nonmissing_first_read_failure_of_noncaller_remains_fail_closed(self):
        for kind in context.PROCESS_IDENTITY_FAILURE_KINDS - {'Missing'}:
            self.kernel.process.reset_mock(side_effect=True)
            self.kernel.process.side_effect = (
                self.rows[101], self.rows[101], context.ProcessIdentityFailure(kind))
            with self.subTest(kind=kind), self.assertRaises(context.ContextFailure) as caught:
                context.capture_context()
            self.assertEqual(caught.exception.stage, 'processIdentityFirstScanRead' + kind)
            self.assertEqual(self.kernel.process.call_count, 3)

    def test_missing_caller_recheck_and_second_scan_remain_fail_closed(self):
        cases = (
            ('processIdentityFirstScanReadMissing',
             (context.ProcessIdentityFailure('Missing'),), 1),
            ('processRecheckReadMissing',
             (self.rows[101], context.ProcessIdentityFailure('Missing')), 2),
            ('processIdentitySecondScanReadMissing',
             (self.rows[101], self.rows[101], self.rows[102], self.rows[102],
              context.ProcessIdentityFailure('Missing')), 5),
        )
        for expected, samples, calls in cases:
            self.kernel.process.reset_mock(side_effect=True)
            self.kernel.process.side_effect = samples
            with self.subTest(expected=expected), self.assertRaises(context.ContextFailure) as caught:
                context.capture_context()
            self.assertEqual(caught.exception.stage, expected)
            self.assertEqual(self.kernel.process.call_count, calls)

    def test_missing_pid_does_not_hide_survivor_drift_or_known_candidate(self):
        self.rows[103] = (103, 1, 501, 501, 501, 123, 103)
        self.paths[102] = '/tmp/StopSpikeWorker'
        self.paths[103] = '/Applications/Editor'
        cases = (((101, 102, 103), (101,), 102),
                 ((101, 102), (101,), None))
        for initial, middle, missing in cases:
            self.kernel.pids.reset_mock(side_effect=True)
            self.kernel.process.reset_mock(side_effect=True)
            self.kernel.path.reset_mock(side_effect=True)
            self.kernel.pids.side_effect = (initial, middle)
            self.kernel.path.side_effect = lambda pid: self.paths[pid]
            reads = {}

            def process(pid):
                reads[pid] = reads.get(pid, 0) + 1
                if pid == missing and reads[pid] == 1:
                    raise context.ProcessIdentityFailure('Missing')
                return self.rows[pid]

            self.kernel.process.side_effect = process
            with self.subTest(initial=initial, middle=middle, missing=missing), \
                    self.assertRaises(context.ContextFailure) as caught:
                context.capture_context()
            self.assertEqual(caught.exception.stage, 'inventoryAfterFirstScanChanged')

    def test_known_candidate_missing_on_second_scan_remains_fail_closed(self):
        self.paths[102] = '/tmp/StopSpikeWorker'
        self.kernel.pids.side_effect = ((101, 102), (101, 102))
        self.kernel.process.side_effect = (
            self.rows[101], self.rows[101], self.rows[102], self.rows[102],
            self.rows[101], self.rows[101], context.ProcessIdentityFailure('Missing'))

        with self.assertRaises(context.ContextFailure) as caught:
            context.capture_context()

        self.assertEqual(caught.exception.stage, 'processIdentitySecondScanReadMissing')
        self.assertEqual(self.kernel.path.call_args_list,
                         [call(101), call(102), call(101)])

    def test_initial_omission_exposed_when_middle_inventory_adds_candidate(self):
        self.paths[102] = '/tmp/StopSpikeWorker'
        self.kernel.pids.side_effect = ((101,), (101, 102))

        with self.assertRaises(context.ContextFailure) as caught:
            context.capture_context()

        self.assertEqual(caught.exception.stage, 'inventoryAfterFirstScanChanged')
        self.assertNotIn(call(102), self.kernel.process.call_args_list)
        self.assertNotIn(call(102), self.kernel.path.call_args_list)

    def test_pid_reuse_uid_parent_and_path_drift(self):
        original = self.rows[102]
        for index in range(1, 7):
            calls = 0
            def row(pid):
                nonlocal calls
                if pid == 102:
                    calls += 1
                    if calls > 1:
                        changed = list(original)
                        changed[index] += 1
                        return tuple(changed)
                return self.rows[pid]
            self.kernel.process.side_effect = row
            with self.subTest(index=index), self.assertRaises(ValueError):
                context.capture_context()
        self.kernel.process.side_effect = lambda pid: self.rows[pid]
        self.kernel.path.side_effect = ['/usr/bin/python3', '/Applications/Editor',
                                      '/usr/bin/python3', '/tmp/StopSpikeWorker']
        with self.assertRaises(ValueError):
            context.capture_context()

    def test_bad_row(self):
        original = self.rows[102]
        for index, value in ((0, 103), (2, 502), (5, 0), (6, 1000000)):
            changed = list(original)
            changed[index] = value
            self.rows[102] = tuple(changed)
            with self.subTest(index=index), self.assertRaises(ValueError):
                context.capture_context()

    def test_incarnation_changes_between_complete_scans(self):
        calls = 0
        def row(pid):
            nonlocal calls
            if pid == 102:
                calls += 1
                if calls > 2:
                    return (*self.rows[pid][:-1], 999)
            return self.rows[pid]
        self.kernel.process.side_effect = row
        with self.assertRaises(ValueError):
            context.capture_context()

    def test_malformed_paths_and_caller_drift(self):
        for path in ('relative', '/tmp/../worker', '/tmp/worker\x00', None):
            self.paths[102] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                context.capture_context()
        self.paths[102] = '/Applications/Editor'
        for operation, values in (('getuid', [501, 502]), ('geteuid', [501, 502]),
                                  ('getpid', [101, 999])):
            with patch.object(context.os, operation, side_effect=values):
                with self.assertRaises(ValueError):
                    context.capture_context()

    def test_context_drift(self):
        for operation, samples in (
                ('boot', [self.kernel.boot.return_value, '22345678-1234-1234-1234-123456789abc']),
                ('session', [(42, 16), (43, 16)])):
            method = getattr(self.kernel, operation)
            method.side_effect = samples
            with self.assertRaises(ValueError):
                context.capture_context()
            method.side_effect = None

    def test_invalid_session_and_privileged_caller(self):
        for session in ((0, 16), (42, 17), (42, 0), (42, 0x1010)):
            self.kernel.session.return_value = session
            with self.assertRaises(ValueError):
                context.capture_context()
        self.kernel.session.return_value = (42, 16)
        with patch.object(context.os, 'geteuid', return_value=0):
            with self.assertRaises(ValueError):
                context.capture_context()

    def test_locked_adapter_uses_probe_and_preserves_files(self):
        # Real snapshot/adapter/probe, mocked Darwin calls. This establishes the
        # caller integration, not native inventory or verified boot freshness.
        import recovery_record as model
        from recovery_evidence import check_recovery
        from test_recovery_record import identity
        for pid, row in self.rows.items():
            self.rows[pid] = (*row[:2], self.actual_uid, self.actual_uid,
                              self.actual_uid, *row[5:])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            marker, run = root / 'marker', root / 'run'
            recovery = run / 'recovery'
            for path in (marker, run, recovery):
                path.mkdir(mode=0o700)
            record = model.new_record(identity())
            record['identity']['boot'] = 'different-boot'
            files = {marker / 'lock': b'unresolved:' + record['identity']['run'].encode(),
                     recovery / 'record.lock': b'',
                     recovery / 'record.json': model.encode(record)}
            for path, data in files.items():
                path.write_bytes(data)
                path.chmod(0o600)
            with patch.object(context.os, 'geteuid', return_value=self.actual_uid), \
                    patch.object(context.os, 'getuid', return_value=self.actual_uid):
                verdict = check_recovery(marker, run, context.capture_context)
                self.assertNotEqual(verdict.result, 'blocked')
                self.assertFalse(verdict.restart_eligible)
                self.paths[102] = '/tmp/StopSpikeWorker'
                self.assertEqual(check_recovery(marker, run, context.capture_context).result,
                                 'blocked')
                self.kernel.pids.side_effect = OSError('incomplete')
                self.assertEqual(check_recovery(marker, run, context.capture_context).result,
                                 'blocked')
            self.assertEqual({path: path.read_bytes() for path in files}, files)


class EnumerationTests(unittest.TestCase):
    def setUp(self):
        self.kernel = object.__new__(context._Kernel)
        self.kernel.lib = Mock()

    def test_bytes_not_pid_count(self):
        def fill(kind, uid, buffer, capacity):
            self.assertEqual((kind, uid), (4, 501))
            buffer[0], buffer[1] = 101, 102
            return 2 * C.sizeof(C.c_int)
        self.kernel.lib.proc_listpids.side_effect = fill
        self.assertEqual(self.kernel.pids(501), (101, 102))

    def test_error_partial_and_full_buffer_reject(self):
        capacity = context.MAX_PIDS * C.sizeof(C.c_int)
        for count in (-1, 0, 3, capacity, capacity + 4):
            self.kernel.lib.proc_listpids.return_value = count
            with self.subTest(count=count), self.assertRaises(ValueError):
                self.kernel.pids(501)

    def test_native_query_and_returned_inventory_failures_are_distinct(self):
        self.kernel.lib.proc_listpids.side_effect = OSError('native query detail')
        with self.assertRaises(ValueError) as caught:
            self.kernel.pids(501)
        self.assertEqual(caught.exception.kind, 'Query')
        self.assertNotIn('native query detail', str(caught.exception))

        self.kernel.lib.proc_listpids.side_effect = None
        self.kernel.lib.proc_listpids.return_value = 3
        with self.assertRaises(ValueError) as caught:
            self.kernel.pids(501)
        self.assertEqual(caught.exception.kind, 'Malformed')

    def test_duplicate_zero_and_negative_entries_reject(self):
        for entries in ((101, 101), (101, 0), (101, -1)):
            def fill(kind, uid, buffer, capacity):
                buffer[0], buffer[1] = entries
                return 8
            self.kernel.lib.proc_listpids.side_effect = fill
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                self.kernel.pids(501)


if __name__ == '__main__':
    unittest.main()
