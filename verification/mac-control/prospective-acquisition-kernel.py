"""Fresh kernel-inventory acquisition caller; inspect is read-only, run writes evidence.

Run requires the separately agreed native storage scope. Never reuse a failed
transaction, migrate the marker, initialize recovery, activate or send input.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/mac-control/Spikes'))
from recovery_storage import flush_directory
from recovery_acquire_run import run_operations
from runtime_root import trusted_runtime_root

TXN = 'acquisition-c6448ce2f81c44f78af0752199fdae2b'
EVIDENCE_PARENT = Path('/Users/sim/Library/Application Support/Directions/MacControlEvidence')
ANCHOR_PARENT = Path('/Users/sim/.config/directions/mac-control-anchors')
TRANSACTION = EVIDENCE_PARENT / TXN
SLOTS = TRANSACTION / 'slots'
ARCHIVE = TRANSACTION / 'archive'
ANCHOR = ANCHOR_PARENT / TXN
MARKER = Path('/private/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike')
HISTORY = REPO / 'verification/mac-control/worker-crash-2026-09-09.json'
REPORT = REPO / 'verification/mac-control/prospective-acquisition-c6448ce2f81c44f78af0752199fdae2b.jsonl'
LIBRARY = Path('/private/tmp/directions-inventory.1aT0KH/recovery_inventory.dylib')
LIBRARY_SHA256 = 'b0d46b7fb180e1e04d29b538f18d19211fd90f6342106d917c7dcfa51c6eedfc'


def checked(path, private=False):
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError('noncanonical configured directory')
    for item in [path, *path.parents]:
        if not stat.S_ISDIR(item.lstat().st_mode):
            raise ValueError('unsafe configured directory')
    if private:
        info = path.stat()
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError('configured directory is not private')


def flush(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        flush_directory(fd)
    finally:
        os.close(fd)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv not in (['inspect'], ['run']):
        raise ValueError('choose inspect or run')
    trusted_runtime_root(MARKER)
    for path in (EVIDENCE_PARENT, ANCHOR_PARENT, MARKER):
        checked(path, private=True)
    if (LIBRARY.resolve(strict=True) != LIBRARY or not LIBRARY.is_file()
            or hashlib.sha256(LIBRARY.read_bytes()).hexdigest() != LIBRARY_SHA256):
        raise ValueError('inventory library changed')
    sync = ET.parse('/Users/sim/Library/Application Support/Syncthing/config.xml')
    sync_roots = [Path(f.attrib['path']).expanduser().resolve() for f in sync.findall('folder')]
    for root in (SLOTS, ARCHIVE, ANCHOR):
        for other in [MARKER.parent, *sync_roots]:
            if os.path.commonpath([root, other]) in (str(root), str(other)):
                raise ValueError('evidence namespace is not separate')
    for path in (TRANSACTION, SLOTS, ARCHIVE, ANCHOR, REPORT):
        if os.path.lexists(path):
            raise ValueError('transaction already exists; no retry')
    configuration = dict(transaction=TXN, marker_directory=str(MARKER),
        runtime_parent=str(MARKER.parent), history_source=str(HISTORY),
        evidence_directory=str(SLOTS), anchor_directory=str(ANCHOR), archive_directory=str(ARCHIVE),
        inventory_library=str(LIBRARY), inventory_sha256=LIBRARY_SHA256,
        synchronization_review='Disjoint from all configured Syncthing folders; other services not assessed.',
        configured_sync_folder_count=len(sync_roots))
    if argv == ['inspect']:
        print(json.dumps(configuration, indent=2))
        return 0
    os.umask(0o077)
    with REPORT.open('x') as report:
        report.write(json.dumps(dict(configuration=configuration, stage='prepared')) + '\n')
        report.flush()
        os.fsync(report.fileno())
    flush(REPORT.parent)
    for path in (TRANSACTION, SLOTS, ARCHIVE, ANCHOR):
        path.mkdir(mode=0o700)
        checked(path, private=True)
        flush(path)
        flush(path.parent)
    common = ['--evidence-directory', str(SLOTS), '--anchor-directory', str(ANCHOR),
              '--archive-directory', str(ARCHIVE)]
    base = [sys.executable, '-B', str(REPO / 'tools/mac-control/Spikes/recovery_acquire.py')]
    operations = [('capture', base + ['capture', *common, '--marker-directory', str(MARKER),
        '--inventory-library', str(LIBRARY), '--inventory-sha256', LIBRARY_SHA256,
        '--history-source', str(HISTORY), '--operator-record',
        '2026-09-10 shared-root and kernel-inventory continuation after reviewed integration and successful read-only native observation: new prospective baseline; preserve all five prior failed transactions and three consumed observation journals; original report pins not found; historical crash copy acquired now as failed/unknown, non-retryable context.']),
        ('reload', base + ['reload', *common])]
    run_operations(operations, report_path=REPORT, configuration=configuration, cwd=REPO)
    print('Verified capture and separate-process reload; marker unchanged; no launch authority.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
