"""Compile and test the C parser with an injected sysctl fixture only.

The test dylib must have no unresolved native sysctl symbol, so no test can fall
through to a host process query. All build artifacts live in TemporaryDirectory.
"""

import ctypes as C
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import recovery_probe as probe


HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'recovery_inventory.c'

EMPTY = 0
CANDIDATE = 1
ERR_ARGUMENT = -1
ERR_QUERY = -3
ERR_MALFORMED = -4
ERR_CALLER_MISSING = -5

SIDL = 1
SRUN = 2
SSLEEP = 3
SSTOP = 4
SZOMB = 5

UID = 501
CALLER = 4100


HARNESS = r'''
#include <sys/param.h>
#include <sys/sysctl.h>

#include <stdint.h>
#include <string.h>

#define FIXTURE_RECORDS 64

static struct kinfo_proc fixture[FIXTURE_RECORDS];
static size_t fixture_count;
static size_t reported_bytes;
static int configured_result;
static int query_calls;
static size_t supplied_capacity;
static int captured_mib[4];

int mc_inventory(uid_t uid, pid_t caller);

void
mc_test_reset(int result)
{
    memset(fixture, 0, sizeof(fixture));
    fixture_count = 0;
    reported_bytes = 0;
    configured_result = result;
    query_calls = 0;
    supplied_capacity = 0;
    memset(captured_mib, 0, sizeof(captured_mib));
}

int
mc_test_add(int pid, unsigned int uid, int64_t seconds, int microseconds,
    int status, const char *name, int terminate)
{
    struct kinfo_proc *record;
    size_t length;

    if (fixture_count == FIXTURE_RECORDS || name == NULL) {
        return -1;
    }
    record = &fixture[fixture_count++];
    record->kp_proc.p_pid = (pid_t)pid;
    record->kp_proc.p_starttime.tv_sec = (time_t)seconds;
    record->kp_proc.p_starttime.tv_usec = (suseconds_t)microseconds;
    record->kp_proc.p_stat = (char)status;
    record->kp_eproc.e_ucred.cr_uid = (uid_t)uid;
    if (terminate) {
        length = strlen(name);
        if (length > MAXCOMLEN) {
            length = MAXCOMLEN;
        }
        memcpy(record->kp_proc.p_comm, name, length);
        record->kp_proc.p_comm[length] = '\0';
    } else {
        memset(record->kp_proc.p_comm, 'X', sizeof(record->kp_proc.p_comm));
    }
    reported_bytes = fixture_count * sizeof(struct kinfo_proc);
    return 0;
}

void
mc_test_set_reported_bytes(size_t bytes)
{
    reported_bytes = bytes;
}

size_t
mc_test_record_size(void)
{
    return sizeof(struct kinfo_proc);
}

size_t
mc_test_max_capacity(void)
{
    return (size_t)65536 * sizeof(struct kinfo_proc);
}

int
mc_test_maxcomlen(void)
{
    return MAXCOMLEN;
}

int mc_test_ctl_kern(void) { return CTL_KERN; }
int mc_test_kern_proc(void) { return KERN_PROC; }
int mc_test_kern_proc_uid(void) { return KERN_PROC_UID; }

int
mc_test_query_calls(void)
{
    return query_calls;
}

size_t
mc_test_supplied_capacity(void)
{
    return supplied_capacity;
}

int
mc_test_mib(int index)
{
    return index >= 0 && index < 4 ? captured_mib[index] : -1;
}

int
mc_test_sysctl(int *mib, u_int mib_count, void *output, size_t *output_size,
    void *input, size_t input_size)
{
    size_t copy_size;
    size_t available;

    query_calls++;
    if (mib != NULL && mib_count == 4) {
        memcpy(captured_mib, mib, sizeof(captured_mib));
    }
    if (output_size == NULL) {
        return configured_result;
    }
    supplied_capacity = *output_size;
    copy_size = reported_bytes < *output_size ? reported_bytes : *output_size;
    available = fixture_count * sizeof(struct kinfo_proc);
    if (copy_size > available) {
        copy_size = available;
    }
    if (output != NULL && copy_size > 0) {
        memcpy(output, fixture, copy_size);
    }
    *output_size = reported_bytes;
    (void)input;
    (void)input_size;
    return configured_result;
}
'''


@unittest.skipUnless(sys.platform == 'darwin', 'requires the installed macOS SDK')
class RecoveryInventoryTests(unittest.TestCase):
    def test_compiled_parser_through_opt_in_helper_and_parent_wire(self):
        # The existing test library compiles the real C parser, substituting only
        # sysctl. Enter the real loader, context adapter and subprocess protocol.
        path = Path(self.lib._name).resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for candidate in (False, True):
            command = probe._probe_command((str(path), digest))
            setup = f'''
import ctypes as C, os
import recovery_kernel_context as context
fixture = C.CDLL({str(path)!r})
fixture.mc_test_add.argtypes = [C.c_int, C.c_uint, C.c_int64, C.c_int, C.c_int, C.c_char_p, C.c_int]
fixture.mc_test_reset(0)
fixture.mc_test_add(os.getpid(), os.geteuid(), 123, 456, 2, b'python3', 1)
if {candidate!r}:
    fixture.mc_test_add(os.getpid() + 1, os.geteuid(), 123, 457, 2, b'StopSpikeWorker', 1)
class Kernel:
    def boot(self): return '12345678-1234-1234-1234-123456789abc'
    def session(self): return (42, 16)
context._Kernel = Kernel
'''
            source = command[4].replace('from supervisor import mac_clock;',
                                       'mac_clock = lambda: lambda: 987654321;')
            source = source.replace('raise SystemExit(', setup + '\nraise SystemExit(')
            with self.subTest(candidate=candidate), \
                 patch.object(probe, '_probe_command', return_value=[*command[:4], source]) as launch:
                if candidate:
                    with self.assertRaises(probe.ProbeFailure) as caught:
                        probe.capture_bounded_context(inventory_library=(str(path), digest))
                    self.assertEqual(caught.exception.stage, 'kernelInventoryCandidate')
                else:
                    result = probe.capture_bounded_context(inventory_library=(str(path), digest))
                    self.assertTrue(result['inventory_complete'])
                    self.assertEqual(result['executors'], [])
                    self.assertEqual(result['checked_ns'], 987654321)
                launch.assert_called_once_with((str(path), digest))

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        directory = Path(cls.temporary.name)
        harness = directory / 'inventory_harness.c'
        library = directory / 'librecovery_inventory.dylib'
        harness.write_text(HARNESS)
        subprocess.run([
            'xcrun', 'clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
            '-fsyntax-only', str(SOURCE),
        ], check=True, capture_output=True, text=True)
        subprocess.run([
            'xcrun', 'clang', '-dynamiclib', '-std=c11', '-Wall', '-Wextra',
            '-Werror', '-DMC_SYSCTL=mc_test_sysctl', str(SOURCE), str(harness),
            '-o', str(library),
        ], check=True, capture_output=True, text=True)
        undefined = subprocess.run(
            ['nm', '-u', str(library)], check=True, capture_output=True, text=True,
        ).stdout.splitlines()
        if any(line.split() and line.split()[-1] == '_sysctl' for line in undefined):
            raise AssertionError('test library retained a native sysctl reference')
        cls.lib = C.CDLL(str(library))
        cls.lib.mc_inventory.argtypes = [C.c_uint, C.c_int]
        cls.lib.mc_inventory.restype = C.c_int
        cls.lib.mc_test_reset.argtypes = [C.c_int]
        cls.lib.mc_test_add.argtypes = [
            C.c_int, C.c_uint, C.c_int64, C.c_int, C.c_int, C.c_char_p,
            C.c_int,
        ]
        cls.lib.mc_test_add.restype = C.c_int
        cls.lib.mc_test_set_reported_bytes.argtypes = [C.c_size_t]
        cls.lib.mc_test_record_size.restype = C.c_size_t
        cls.lib.mc_test_max_capacity.restype = C.c_size_t
        cls.lib.mc_test_maxcomlen.restype = C.c_int
        cls.lib.mc_test_ctl_kern.restype = C.c_int
        cls.lib.mc_test_kern_proc.restype = C.c_int
        cls.lib.mc_test_kern_proc_uid.restype = C.c_int
        cls.lib.mc_test_query_calls.restype = C.c_int
        cls.lib.mc_test_supplied_capacity.restype = C.c_size_t
        cls.lib.mc_test_mib.argtypes = [C.c_int]
        cls.lib.mc_test_mib.restype = C.c_int

    @classmethod
    def tearDownClass(cls):
        del cls.lib

    def setUp(self):
        self.lib.mc_test_reset(0)

    def add(self, pid, name=b'unrelated', *, uid=UID, seconds=1_700_000_000,
            microseconds=123_456, status=SSLEEP, terminate=True):
        result = self.lib.mc_test_add(
            pid, uid, seconds, microseconds, status, name, terminate,
        )
        self.assertEqual(result, 0)

    def valid_inventory(self):
        self.add(CALLER, b'python3', status=SRUN)
        self.add(4200, b'WindowServer')

    def test_valid_snapshot_uses_one_fixed_kern_proc_uid_query(self):
        self.valid_inventory()
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), EMPTY)
        self.assertEqual(self.lib.mc_test_query_calls(), 1)
        self.assertEqual(
            self.lib.mc_test_supplied_capacity(),
            self.lib.mc_test_max_capacity(),
        )
        self.assertEqual([self.lib.mc_test_mib(i) for i in range(4)],
                         [self.lib.mc_test_ctl_kern(),
                          self.lib.mc_test_kern_proc(),
                          self.lib.mc_test_kern_proc_uid(), UID])

    def test_unrelated_churn_does_not_require_global_set_equality(self):
        self.valid_inventory()
        self.add(4300, b'first-short-lived')
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), EMPTY)

        self.lib.mc_test_reset(0)
        self.add(CALLER, b'python3', status=SRUN)
        self.add(4400, b'different-process')
        self.add(4500, b'another-process', status=SSTOP)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), EMPTY)
        self.assertEqual(self.lib.mc_test_query_calls(), 1)

    def test_both_worker_names_are_candidates(self):
        for name in (b'MacControlExecutor', b'StopSpikeWorker'):
            with self.subTest(name=name):
                self.lib.mc_test_reset(0)
                self.add(CALLER, b'python3')
                self.add(4200, name)
                self.assertEqual(self.lib.mc_inventory(UID, CALLER), CANDIDATE)

    def test_sdk_truncation_and_long_name_collision_both_block(self):
        self.assertEqual(len(b'MacControlExecut'), self.lib.mc_test_maxcomlen())
        for name in (b'MacControlExecut', b'MacControlExecutorCollision'):
            with self.subTest(name=name):
                self.lib.mc_test_reset(0)
                self.add(CALLER, b'python3')
                self.add(4200, name)
                self.assertEqual(self.lib.mc_inventory(UID, CALLER), CANDIDATE)

    def test_near_names_are_not_candidates(self):
        self.add(CALLER, b'python3')
        self.add(4200, b'MacControlExecu')
        self.add(4201, b'maccontrolexecut')
        self.add(4202, b'StopSpikeWork')
        self.add(4203, b'StopSpikeWorkerExtra')
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), EMPTY)

    def test_matching_zombie_blocks(self):
        self.add(CALLER, b'python3')
        self.add(4200, b'StopSpikeWorker', status=SZOMB)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), CANDIDATE)

    def test_valid_unrelated_zombie_is_allowed(self):
        self.add(CALLER, b'python3')
        self.add(4200, b'unrelated', status=SZOMB)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), EMPTY)

    def test_query_failure_is_fixed_and_not_retried(self):
        self.valid_inventory()
        self.lib.mc_test_reset(-1)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_QUERY)
        self.assertEqual(self.lib.mc_test_query_calls(), 1)

    def test_zero_partial_full_and_oversized_output_are_malformed(self):
        record_size = self.lib.mc_test_record_size()
        capacity = self.lib.mc_test_max_capacity()
        for reported in (0, record_size - 1, capacity, capacity + record_size):
            with self.subTest(reported=reported):
                self.lib.mc_test_reset(0)
                self.valid_inventory()
                self.lib.mc_test_set_reported_bytes(reported)
                self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)
                self.assertEqual(self.lib.mc_test_query_calls(), 1)

    def test_duplicate_pid_is_malformed(self):
        self.add(CALLER, b'python3')
        self.add(CALLER, b'python3')
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)

    def test_candidate_does_not_hide_later_malformed_or_duplicate_row(self):
        for kind in ('malformed', 'duplicate'):
            with self.subTest(kind=kind):
                self.lib.mc_test_reset(0)
                self.add(CALLER, b'python3')
                self.add(4200, b'StopSpikeWorker')
                if kind == 'malformed':
                    self.add(4300, b'unrelated', uid=UID + 1)
                else:
                    self.add(4200, b'unrelated')
                self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)

    def test_missing_caller_has_distinct_fixed_status(self):
        self.add(4200, b'unrelated')
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_CALLER_MISSING)

    def test_wrong_effective_uid_is_malformed(self):
        self.add(CALLER, b'python3')
        self.add(4200, b'unrelated', uid=UID + 1)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)

    def test_nonpositive_pid_is_malformed(self):
        for pid in (0, -1):
            with self.subTest(pid=pid):
                self.lib.mc_test_reset(0)
                self.add(CALLER, b'python3')
                self.add(pid, b'unrelated')
                self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)

    def test_invalid_start_tuple_is_malformed(self):
        for seconds, microseconds in ((0, 0), (-1, 0), (1, -1), (1, 1_000_000)):
            with self.subTest(seconds=seconds, microseconds=microseconds):
                self.lib.mc_test_reset(0)
                self.add(CALLER, b'python3')
                self.add(4200, b'unrelated', seconds=seconds,
                         microseconds=microseconds)
                self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)

    def test_missing_comm_terminator_is_malformed(self):
        self.add(CALLER, b'python3')
        self.add(4200, b'ignored', terminate=False)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)

    def test_unknown_process_status_is_malformed(self):
        self.add(CALLER, b'python3')
        self.add(4200, b'unrelated', status=0)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), ERR_MALFORMED)

    def test_all_sdk_process_status_values_are_accepted(self):
        self.add(CALLER, b'python3')
        for offset, status in enumerate((SIDL, SRUN, SSLEEP, SSTOP, SZOMB), 1):
            self.add(CALLER + offset, b'unrelated', status=status)
        self.assertEqual(self.lib.mc_inventory(UID, CALLER), EMPTY)

    def test_invalid_arguments_do_not_query(self):
        for uid, caller in ((0, CALLER), (UID, 0), (UID, -1)):
            with self.subTest(uid=uid, caller=caller):
                self.lib.mc_test_reset(0)
                self.assertEqual(self.lib.mc_inventory(uid, caller), ERR_ARGUMENT)
                self.assertEqual(self.lib.mc_test_query_calls(), 0)


if __name__ == '__main__':
    unittest.main()
