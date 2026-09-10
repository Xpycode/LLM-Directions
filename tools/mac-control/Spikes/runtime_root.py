"""One existing exclusion namespace for the current host-scoped spike.

This independent source pin is shared by supported launchers and native callers.
It is not discovered from TMPDIR, a report, a CLI argument or a surviving receipt.
Other Macs fail closed. Provisioning, changing the pin and migrating or replacing
the directory/marker are outside this contract. Offline tests patch the pin.
"""
import os
from pathlib import Path

from recovery_snapshot import require


TRUSTED_RUNTIME_ROOT = Path(
    '/private/var/folders/ly/b2sk443n0hq1_z9mgf4q8f4w0000gn/T/directions-stop-spike')


def trusted_runtime_root(expected=None):
    """Validate selection, then return only the independently pinned path.

    Canonicalizing the OS lookup permits Darwin's /var alias, but can never
    select an alternate root. The actual open must use MarkerLock(create=False)
    on the returned canonical pin, which walks without following symlinks and
    keeps descriptor/name identity checks through the consuming transaction.
    This function neither opens the marker nor creates any directory or file.
    """
    root = TRUSTED_RUNTIME_ROOT
    require(root.is_absolute() and root.resolve(strict=True) == root,
            'untrustedRuntimeRoot')
    if expected is not None:
        require(os.fspath(expected) == str(root), 'runtimeRootMismatch')
    # Python omits the Darwin extension from its name table; unistd.h ABI value.
    selected = os.confstr(65537)
    require(type(selected) is str and selected.startswith('/')
            and not selected.startswith('//') and '\x00' not in selected,
            'invalidRuntimeLookup')
    candidate = Path(selected) / 'directions-stop-spike'
    require(candidate.resolve(strict=True) == root, 'runtimeRootMismatch')
    return root
