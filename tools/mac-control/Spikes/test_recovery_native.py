"""Native-shaped wire tests over Python peers; no native app, input or marker."""
import time
import unittest
from unittest.mock import patch

import test_recovery_evidence as fixtures
from recovery_admission import Admission
from recovery_evidence import OwnedEvidence
from recovery_native import NativeFrames
from recovery_storage import RecordWriter
from test_recovery_record import identity


EMIT = r'''
def emit(event, **fields):
    row = dict(source=role, event=event, ns=str(time.monotonic_ns()), **fields)
    if event == 'posted':
        row['down'] = row.pop('kind') == 'down'
        row.pop('sequence')
    elif event == 'checkpoint':
        row['run'] = run
        row['heldKeysEmpty'] = row.pop('held') == []
    elif event == 'receipt':
        row['event'] = 'keyDown' if row.pop('kind') == 'down' else 'keyUp'
        row.pop('sequence')
        row['sourcePID'] = row.pop('origin_pid')
        if row['event'] == 'keyDown':
            row.update(count=(row['tag'] - 1000 + 1) // 2, matchesSamplePrefix=True)
    elif event == 'observationComplete':
        row.update(pid=os.getpid(), isActive=True, frontmostPID=os.getpid())
    print(json.dumps(row), flush=True)
'''
NATIVE_PEER = fixtures.PEER.replace(
    "def emit(event, **fields):\n    print(json.dumps(dict(event=event, run=run, ns=time.monotonic_ns(), **fields)), flush=True)",
    EMIT).replace("    sys.exit(7 if fault == 'target-failure' else 0)",
                 "    sys.stdin.read()\n    sys.exit(7 if fault == 'target-failure' else 0)")


class NativeWireTests(unittest.TestCase):
    setUp = fixtures.RecoveryEvidenceTests.setUp
    tearDown = fixtures.RecoveryEvidenceTests.tearDown
    write = fixtures.RecoveryEvidenceTests.write
    until = fixtures.RecoveryEvidenceTests.until
    probe = fixtures.RecoveryEvidenceTests.probe
    result = fixtures.RecoveryEvidenceTests.result

    def start(self, fault='none'):
        def observer(identity, children):
            # Synthetic peers use this clock in place of mach_continuous_time.
            return OwnedEvidence(identity, children, time.monotonic_ns, native_tag_base=1000)
        with patch.object(fixtures, 'PEER', NATIVE_PEER), \
                patch.object(fixtures, 'OwnedEvidence', side_effect=observer):
            fixtures.RecoveryEvidenceTests.start(self, fault)

    def finish(self):
        self.until(lambda: len(self.observer.rows['posts']) == 4
                   and len(self.observer.rows['receipts']) >= 4
                   and len(self.observer.rows['checkpoints']) == 2)
        self.observer.bind_durable_record(self.raw)
        self.children['worker'].stdin.write(b'finish\n')
        self.children['worker'].stdin.flush()
        self.until(lambda: 'worker' in self.observer.exits and 'worker' in self.observer.streams)
        end = max(self.observer.exits['worker']['ns'], self.observer.streams['worker']['eof_ns'])
        self.until(lambda: time.monotonic_ns() >= end + 5_000_000)
        with patch('recovery_verifier.OBSERVATION_NS', 5_000_000):
            self.observer.request_observation()
        self.until(lambda: 'acknowledged_ns' in self.observer.fence)
        self.assertIsNone(self.children['target'].poll())
        self.observer.finish_target()
        self.until(lambda: len(self.observer.exits) == len(self.observer.streams) == 2)

    def test_native_wire_fence_eof_and_wait(self):
        self.start()
        self.finish()
        verdict = self.result()
        self.assertEqual(verdict.result, 'sameBootCandidate', verdict)
        self.assertFalse(verdict.restart_eligible)
        self.assertFalse(verdict.native_recovery_verified)

    def test_duplicate_and_wrong_semantics_never_bind(self):
        for fault in ('duplicate-receipt', 'wrong-kind', 'wrong-origin'):
            with self.subTest(fault=fault):
                case = NativeWireTests()
                case.setUp()
                try:
                    case.start(fault)
                    with self.assertRaises(ValueError):
                        case.finish()
                    self.assertEqual(case.result().result, 'blocked')
                finally:
                    case.tearDown()

    def test_after_fence_input_and_failed_exit_block(self):
        for fault in ('after-fence', 'target-failure'):
            with self.subTest(fault=fault):
                case = NativeWireTests()
                case.setUp()
                try:
                    case.start(fault)
                    case.finish()
                    self.assertEqual(case.result().result, 'blocked')
                finally:
                    case.tearDown()

    def test_early_target_close_rejected(self):
        self.start()
        with self.assertRaises(ValueError):
            self.observer.finish_target()

    def test_receipt_after_actual_worker_exit_cannot_bind(self):
        self.start('delayed-receipt')
        self.children['worker'].wait(timeout=2)
        self.until(lambda: len(self.observer.rows['receipts']) == 4
                   and len(self.observer.rows['checkpoints']) == 2)
        with self.assertRaises(ValueError):
            self.observer.bind_durable_record(self.raw)
        self.assertEqual(self.result().result, 'blocked')

    def test_diagnostics_are_bounded_and_future_time_rejects(self):
        self.start()
        import json
        heartbeat = dict(source='worker', event='heartbeat', ns=str(time.monotonic_ns()))
        with patch('recovery_evidence.MAX_ROWS', 1):
            self.observer._frame('worker', json.dumps(heartbeat).encode())
            with self.assertRaises(ValueError):
                self.observer._frame('worker', json.dumps(heartbeat).encode())
        heartbeat['ns'] = str((1 << 64) - 1)
        with self.assertRaises(ValueError):
            self.observer._frame('worker', json.dumps(heartbeat).encode())

    def test_real_writer_ack_delivered_through_admission(self):
        self.start()
        self.until(lambda: len(self.observer.rows['receipts']) == 4
                   and len(self.observer.rows['checkpoints']) == 2)
        directory = self.root / 'independent-writer'
        directory.mkdir(mode=0o700)
        writer = RecordWriter(directory)
        try:
            admission = Admission(writer, self.identity, time.monotonic_ns())
            def acknowledged():
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    self.observer.pump(0.01)
                    data = admission.poll(time.monotonic_ns())
                    if data is not None:
                        return data
                self.fail('writer acknowledgement timeout')
            acknowledged()
            # Storage/admission replay using collected events. This checks the
            # ack transport, not native dispatch ordering or live admission.
            from supervisor import Evidence
            evidence = Evidence()
            for tag in (1001, 1003):
                admission.reserve(tag, time.monotonic_ns())
                acknowledged()
                for seq in (tag - 1000, tag - 999):
                    admission.consume(seq, seq + 1000)
                evidence.reserve_pair(tag)
                posts = [r for r in self.observer.rows['posts'] if r['tag'] <= tag + 1]
                receipts = [r for r in self.observer.rows['receipts'] if r['tag'] <= tag + 1]
                evidence.posted = {r['tag'] for r in posts}
                evidence.received = {r['tag']: r['ns'] for r in receipts}
                evidence.verified_origin = {r['tag'] for r in receipts
                                            if r['origin_pid'] == self.identity['worker']['pid']}
                evidence.down_counts[tag] = 1
                evidence.valid_text.add(tag)
                evidence.received_kind = {r['tag']: r['kind'] for r in receipts}
                evidence.posted_kind = {r['tag']: r['kind'] for r in posts}
                admission.resolve(tag - 999, evidence, time.monotonic_ns())
                data = acknowledged()
            self.assertEqual(data, self.raw)
            self.assertIsNone(admission.poll(time.monotonic_ns()))
            self.observer.bind_durable_record(data)
            self.assertIsNotNone(self.observer.digest)
        finally:
            writer.close()
            self.assertTrue(writer.finished.wait(2))


class NativeFrameTests(unittest.TestCase):
    def setUp(self):
        self.adapter = NativeFrames(identity(), 1000)

    def test_kind_comes_from_wire_not_sequence(self):
        row = dict(source='worker', event='posted', ns='12', tag=1001, down=False)
        result = self.adapter.normalize('worker', row)
        self.assertEqual((result['sequence'], result['kind']), (1, 'up'))

    def test_forged_source_unknown_event_and_malformed_time(self):
        row = dict(source='worker', event='posted', ns='12', tag=1001, down=True)
        for change in (dict(source='target'), dict(event='workerExited'), dict(ns=12),
                       dict(ns='012'), dict(ns='-1'), dict(ns='１２'), dict(down=1),
                       dict(tag=1000), dict(tag=1257), dict(extra=True)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.adapter.normalize('worker', dict(row, **change))

    def test_checkpoint_must_report_current_run_and_empty_held_state(self):
        row = dict(source='worker', event='checkpoint', ns='12', tag=1002, sequence=2,
                   run=identity()['run'], heldKeysEmpty=True)
        self.assertEqual(self.adapter.normalize('worker', row)['held'], [])
        for change in (dict(run='wrong'), dict(sequence=4), dict(heldKeysEmpty=False)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.adapter.normalize('worker', dict(row, **change))

    def test_native_clock_must_be_explicit(self):
        with self.assertRaises(ValueError):
            OwnedEvidence(identity(), {'worker': None, 'target': None}, native_tag_base=1000)

    def test_matching_prefix_requires_actual_text_progress(self):
        row = dict(source='target', event='keyDown', ns='12', tag=1001,
                   sourcePID=identity()['worker']['pid'], count=0, matchesSamplePrefix=True)
        with self.assertRaises(ValueError):
            self.adapter.normalize('target', row)
        self.adapter.normalize('target', dict(row, count=1))
        with self.assertRaises(ValueError):
            self.adapter.normalize('target', dict(row, tag=1003, count=1))


if __name__ == '__main__':
    unittest.main()
