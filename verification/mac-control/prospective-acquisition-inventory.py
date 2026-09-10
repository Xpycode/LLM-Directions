"""Fresh September 10 caller after inventory-contract validation; one attempt only.

Prepared from prospective-acquisition-wrapper.py with fresh transaction/report
names and operator record. Native use requires the reviewed execution scope. Merely importing this file performs
the location preflight. Reports written by this revision are append-only JSONL.
"""
import json
import os
from pathlib import Path
import stat
import sys
import xml.etree.ElementTree as ET

REPO = Path('/Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS')
sys.path.insert(0, str(REPO / 'tools/mac-control/Spikes'))
from recovery_storage import flush_directory
from recovery_acquire_run import run_operations

TXN = 'acquisition-cd911942b7cb40adb20dc1753668b3ae'
EVIDENCE_PARENT = Path('/Users/sim/Library/Application Support/Directions/MacControlEvidence')
ANCHOR_PARENT = Path('/Users/sim/.config/directions/mac-control-anchors')
TRANSACTION = EVIDENCE_PARENT / TXN
SLOTS = TRANSACTION / 'slots'
ARCHIVE = TRANSACTION / 'archive'
ANCHOR = ANCHOR_PARENT / TXN
# Explicit caller configuration: supervisor.experiment_lock uses this Darwin temp root.
MARKER = Path('/private/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike')
RUNTIME_PARENT = MARKER.parent
HISTORY = REPO / 'verification/mac-control/worker-crash-2026-09-09.json'
REPORT = REPO / 'verification/mac-control/prospective-acquisition-cd911942b7cb40adb20dc1753668b3ae.jsonl'

def checked(path, private=False):
    assert path.is_absolute() and path.resolve(strict=True) == path, str(path)
    for item in [path, *path.parents]:
        info = item.lstat()
        assert stat.S_ISDIR(info.st_mode), str(item)
    if private:
        info = path.stat()
        assert info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700

def flush(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        flush_directory(fd)
    finally:
        os.close(fd)

assert (Path(os.confstr(65537)) / 'directions-stop-spike').resolve(strict=True) == MARKER
for path in [EVIDENCE_PARENT, ANCHOR_PARENT, MARKER]:
    checked(path, private=True)
sync = ET.parse('/Users/sim/Library/Application Support/Syncthing/config.xml')
sync_roots = [Path(f.attrib['path']).expanduser().resolve() for f in sync.findall('folder')]
for root in [SLOTS, ARCHIVE, ANCHOR]:
    for other in [RUNTIME_PARENT, *sync_roots]:
        assert os.path.commonpath([root, other]) not in [str(root), str(other)]
for path in [TRANSACTION, SLOTS, ARCHIVE, ANCHOR, REPORT]:
    assert not os.path.lexists(path), str(path)

configuration = dict(transaction=TXN, marker_directory=str(MARKER),
    runtime_parent=str(RUNTIME_PARENT), history_source=str(HISTORY),
    evidence_directory=str(SLOTS), anchor_directory=str(ANCHOR), archive_directory=str(ARCHIVE),
    synchronization_review='Disjoint from all configured Syncthing folders; other services not assessed.',
    configured_sync_folder_count=len(sync_roots))
if sys.argv[1:] == ['inspect']:
    print(json.dumps(configuration, indent=2))
    raise SystemExit(0)
assert sys.argv[1:] == ['run']
os.umask(0o077)
# Exclusive report and directories; failure preserves all partial artifacts.
with REPORT.open('x') as report:
    report.write(json.dumps(dict(configuration=configuration, stage='prepared')) + '\n')
    report.flush()
    os.fsync(report.fileno())
flush(REPORT.parent)
for path in [TRANSACTION, SLOTS, ARCHIVE, ANCHOR]:
    path.mkdir(mode=0o700)
    checked(path, private=True)
    flush(path)
    flush(path.parent)
common = ['--evidence-directory', str(SLOTS), '--anchor-directory', str(ANCHOR),
          '--archive-directory', str(ARCHIVE)]
base = [sys.executable, '-B', str(REPO / 'tools/mac-control/Spikes/recovery_acquire.py')]
operations = [('capture', base + ['capture', *common, '--marker-directory', str(MARKER),
    '--history-source', str(HISTORY), '--operator-record',
    '2026-09-10 Wave 1 continuation after reviewed inventory disappearance contract and successful read-only native observation: new prospective baseline; preserve all four prior failed transactions; original report pins not found; historical crash copy acquired now as failed/unknown, non-retryable context.']),
    ('reload', base + ['reload', *common])]
run_operations(operations, report_path=REPORT, configuration=configuration, cwd=REPO)
print('Verified capture and separate-process reload; marker unchanged; no launch authority.')
