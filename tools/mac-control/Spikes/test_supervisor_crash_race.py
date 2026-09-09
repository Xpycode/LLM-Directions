"""Asynchronous kill cannot reopen storage after final recovery binding."""
import unittest

import recovery_record as model
import test_focus_supervisor as fixture
from test_recovery_admission import FakeWriter
from test_worker_crash import CrashTransport


class CrashRaceTests(unittest.TestCase):
    def test_delayed_final_ack_and_asynchronous_kill_freeze_final_boundary(self):
        rig = CrashTransport()

        class DelayedAck(FakeWriter):
            delay = 15

            def poll(self):
                if self.pending:
                    record = model.parse(self.pending)
                    if record['sequence'] == 12 and record['state'] == 'resolved' and self.delay:
                        self.delay -= 1
                        return None
                return super().poll()

        rig.record_writer = DelayedAck()
        original_popen, original_select = rig.popen, rig.select

        def popen(*args, **kwargs):
            peer = original_popen(*args, **kwargs)
            if peer.name == 'worker':
                # kill returns before wait status becomes observable.
                peer.kill = lambda: setattr(peer, 'killed', True)
            return peer

        def select(timeout):
            worker = rig.peers.get('worker')
            if worker and worker.killed:
                worker.returncode = -9
            return original_select(timeout)

        rig.popen, rig.select = popen, select
        _, code, trace, marker = fixture.FocusSupervisorTests().run_transport(
            rig=rig, focus_loss=False, worker_crash=True)
        injection = next(i for i, row in enumerate(trace) if row['event'] == 'workerCrashInjected')
        self.assertFalse(any(row['event'] == 'recordPending' for row in trace[injection:]))
        self.assertIsNone(rig.record_writer.pending)
        self.assertEqual(rig.record_writer.saved[-1]['state'], 'resolved')
        self.assertEqual(rig.record_writer.saved[-1]['sequence'], 12)
        self.assertEqual(len([row for _, row in rig.commands if row['op'] == 'event']), 12)
        self.assertTrue(any(row['event'] == 'recoveryEvidenceCollected' for row in trace))
        self.assertEqual(code, 2)
        self.assertEqual(marker, b'unresolved')


if __name__ == '__main__':
    unittest.main()
