#!/usr/bin/env python3
"""Static status contracts plus disposable reference-routing fixtures.

The routing model below is a fixture, not a command interpreter or real agent run.
No fetch, detector, Git mutation, network, app or host request is performed.
"""
from pathlib import Path
import re
import shutil
import tempfile
import unittest

MASTER = Path(__file__).resolve().parents[2]
CORE = MASTER / 'commands/status.md'


def resolve_master(command_source):
    """Model only the documented repository-source fallback, including symlinks."""
    root = command_source.resolve().parent.parent
    if not (root / 'commands/status.md').is_file() or not (root / 'reference/status').is_dir():
        raise ValueError('Directions master unavailable')
    return root


def fixture_reads(master, argument, known_concurrency=False, mutation=False):
    """Rehearse mode selection from the source table; no procedure is executed."""
    core = (master / 'commands/status.md').read_text()
    mode = 'status'
    for line in core.splitlines():
        if not line.startswith('|'):
            continue
        cells = line.split('|')
        if argument and argument in re.findall(r'"([^"]+)"', cells[1]):
            mode = re.search(r'\*\*(\w+)\*\*', cells[2]).group(1)
            break
    references = []
    if mode == 'arrive':
        references.append('reference/status/arrive.md')
    if mode == 'arrive' or known_concurrency or mutation:
        references.append('reference/status/collision.md')
    for reference in references:
        if f'<master>/{reference}' not in core:
            raise ValueError('missing core route')
        (master / reference).read_text()
    return mode, references


class StatusReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='directions-status-')
        self.root = Path(self.temp.name).resolve()
        self.master = self.root / 'master'
        (self.master / 'commands').mkdir(parents=True)
        shutil.copyfile(CORE, self.master / 'commands/status.md')
        shutil.copytree(MASTER / 'reference/status', self.master / 'reference/status')

    def tearDown(self):
        self.temp.cleanup()

    def test_mode_aliases_and_actual_load_triggers(self):
        cases = [('', 'status'), ('full', 'full'), ('context', 'full'),
                 ('arrive', 'arrive'), ('sit down', 'arrive'),
                 ('switch', 'arrive'), ('behind?', 'arrive')]
        for argument, mode in cases:
            for known in (False, True):
                with self.subTest(argument=argument, known=known):
                    selected, reads = fixture_reads(self.master, argument, known)
                    self.assertEqual(selected, mode)
                    expected = []
                    if mode == 'arrive':
                        expected.append('reference/status/arrive.md')
                    if mode == 'arrive' or known:
                        expected.append('reference/status/collision.md')
                    self.assertEqual(reads, expected)
        self.assertEqual(fixture_reads(self.master, '', mutation=True)[1],
                         ['reference/status/collision.md'])

    def test_master_fallback_ignores_consumer_decoys_and_installed_location(self):
        consumer = self.root / 'consumer'
        (consumer / 'reference/status').mkdir(parents=True)
        (consumer / 'reference/status/arrive.md').write_text('WRONG consumer procedure')
        installed = self.root / 'installed/commands/status.md'
        installed.parent.mkdir(parents=True)
        installed.symlink_to(self.master / 'commands/status.md')
        resolved = resolve_master(installed)
        self.assertEqual(resolved, self.master)
        self.assertNotIn('WRONG', (resolved / 'reference/status/arrive.md').read_text())
        installed.unlink()
        installed.write_text(CORE.read_text())
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            resolve_master(installed)

    def test_core_stays_lean_and_retains_output_contract(self):
        core = CORE.read_text()
        self.assertIn('≤8 lines', core)
        self.assertIn('last 3 from `sessions/_index.md`', core)
        self.assertIn('last 3 titles from `decisions.md`', core)
        self.assertIn('## Mode: arrive  (adds the old `/arrive`', core)
        self.assertIn('## Same-folder session collision check  (triggered)', core)
        self.assertIn('known concurrent sessions in any mode', core)
        self.assertIn('SessionStart hook is unchanged', core)
        self.assertIn('not during initial core loading', core)
        self.assertNotIn('git fetch', core)
        self.assertNotIn('bash ~/.claude/hooks/session-guard.sh', core)

    def test_arrival_identity_and_mutation_boundaries_remain(self):
        arrival = (self.master / 'reference/status/arrive.md').read_text()
        self.assertLess(arrival.index('Verify the intended repository'), arrival.index('git remote get-url'))
        self.assertLess(arrival.index('Do not fetch'), arrival.index('git fetch'))
        for text in ['After a failed `cd`, stop', 'pull only on **yes**',
                     'Rule 5 mutation preflight', 'No auto-pull/reset',
                     'never pulls/commits/switches without asking',
                     '<master>/reference/status/collision.md']:
            self.assertIn(text, arrival)

    def test_collision_host_limits_and_worktree_qualification_remain(self):
        collision = (self.master / 'reference/status/collision.md').read_text()
        start = collision.index('<!-- CLAUDE-ONLY:START')
        end = collision.index('<!-- CLAUDE-ONLY:END -->')
        self.assertTrue(start < collision.index('bash ~/.claude/hooks/session-guard.sh') < end)
        fallback = collision.split('**Codex fallback:**', 1)[1]
        for text in ['no Directions process detector is installed yet',
                     'Do not run the Claude detector', 'automatic detection is',
                     'unavailable', 'Ordinary status/full']:
            self.assertIn(text, fallback)
        for text in ['this is not proof of no collision', 'Preserve known concurrency',
                     'Known concurrent sessions, in any mode', 'distinct HEADs',
                     'shared\n  branch refs and worktree administration',
                     'Existing SessionStart hook', 'verify the intended checkout first']:
            self.assertIn(text, collision)


if __name__ == '__main__':
    unittest.main()
