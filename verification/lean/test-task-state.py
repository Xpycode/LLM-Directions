#!/usr/bin/env python3
"""Disposable record contract checks, not a production migrator or host-behavior proof."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).parent

def progress(record):
    selected = record.get('selected')
    if not selected or selected not in record['plans']:
        raise ValueError('selection required')
    tasks = record['plans'][selected]
    for task in tasks:
        if task['status'] == 'complete' and (not task.get('evidence') or task.get('gate')):
            raise ValueError('completion lacks evidence or retains gate')
    return sum(t['status'] == 'complete' for t in tasks), len(tasks)

def reconcile(root, record, interrupt=False):
    """Rehearse the documented ordered writes on disposable records only."""
    original = root / 'original.json'
    backup = root / 'original.backup.json'
    if not backup.exists():
        backup.write_bytes(original.read_bytes())
    elif backup.read_bytes() != original.read_bytes():
        raise ValueError('original backup mismatch')
    count = progress(record)
    canonical = root / record['selected']
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(json.dumps(record, sort_keys=True))
    if interrupt:
        return
    for link in [record['current_handoff'], *record['historical_handoffs']]:
        assert (root / link.split('#')[0]).exists(), link
    state = {'plan': record['selected'], 'progress': count, 'handoff': record['current_handoff']}
    (root / 'PROJECT_STATE.json').write_text(json.dumps(state, sort_keys=True))
    (root / 'TASKS.md').write_text(f"Active plan: {record['selected']}\nBacklog: retained\n")

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lean-state-')
        self.root = Path(self.temp.name)
        self.record = json.loads((HERE / 'policy-examples.json').read_text())
        (self.root / 'original.json').write_text(json.dumps(self.record))
        (self.root / 'TASKS.md').write_text('legacy mirrors and backlog\n')
        for path in ['sessions/old.md', 'sessions/new.md', 'proof.md']:
            p = self.root / path; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('original evidence\n')

    def tearDown(self):
        self.temp.cleanup()

    def test_selected_identity_and_mirrors(self):
        self.assertEqual(progress(self.record), (1, 2))
        self.record['selected'] = 'plans/B.md'
        self.assertEqual(progress(self.record), (0, 1))

    def test_missing_ambiguous_selection(self):
        self.record['selected'] = None
        with self.assertRaises(ValueError): progress(self.record)

    def test_gate_cannot_be_complete(self):
        self.record['plans']['plans/A.md'][1]['status'] = 'complete'
        with self.assertRaises(ValueError): progress(self.record)

    def test_no_plan_standalone_remains_tracker(self):
        self.record['plans'] = {}; self.record['selected'] = None
        before = (self.root / 'TASKS.md').read_bytes()
        with self.assertRaises(ValueError): progress(self.record)
        self.assertEqual((self.root / 'TASKS.md').read_bytes(), before)

    def test_interrupt_resume_idempotent_history(self):
        original = (self.root / 'original.json').read_bytes()
        old_log = (self.root / 'sessions/old.md').read_bytes()
        reconcile(self.root, self.record, interrupt=True)
        self.assertIn('legacy', (self.root / 'TASKS.md').read_text())
        self.assertFalse((self.root / 'PROJECT_STATE.json').exists())
        reconcile(self.root, self.record)
        before = {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        reconcile(self.root, self.record)
        self.assertEqual(before, {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        self.assertEqual((self.root / 'original.backup.json').read_bytes(), original)
        self.assertEqual((self.root / 'sessions/old.md').read_bytes(), old_log)
        self.assertEqual(json.loads((self.root / 'PROJECT_STATE.json').read_text())['handoff'], 'sessions/new.md#resume')

    def test_backup_mismatch_stops(self):
        (self.root / 'original.backup.json').write_text('different evidence')
        with self.assertRaises(ValueError): reconcile(self.root, self.record)

    def test_docs_layout(self):
        docs=self.root/'docs'; docs.mkdir()
        for p in list(self.root.iterdir()):
            if p != docs: p.rename(docs/p.name)
        reconcile(docs,self.record)
        self.assertEqual(json.loads((docs/'PROJECT_STATE.json').read_text())['progress'],[1,2])

    def test_archival_updates_links_before_retirement(self):
        reconcile(self.root,self.record)
        plan=self.root/'plans/A.md'; retained=plan.read_bytes()
        archive=self.root/'archive/A.md'; archive.parent.mkdir(); archive.write_bytes(retained)
        # Archive keeps data and explicit evidence target; move/retire only after link validation.
        evidence=self.root/'archive/evidence.md'; evidence.write_bytes((self.root/'proof.md').read_bytes())
        (self.root/'TASKS.md').write_text('Completed: archive/A.md; evidence: archive/evidence.md\n')
        self.assertTrue(archive.exists() and evidence.exists())
        self.assertEqual(hashlib.sha256(retained).digest(),hashlib.sha256(archive.read_bytes()).digest())
        plan.unlink()
        self.assertTrue(archive.exists() and evidence.exists())

if __name__ == '__main__':
    unittest.main()
