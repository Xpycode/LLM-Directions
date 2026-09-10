/*
 * Isolated KERN_PROC_UID inventory prototype.
 *
 * This file is not linked into recovery_context.py or any runtime caller.  A
 * zero result only means that this one validated SDK-native result contained
 * no fixed-name worker candidate.  It is not an inventory-completeness claim
 * and must never authorize recovery, restart, marker changes, or signalling.
 */

#include <sys/param.h>
#include <sys/sysctl.h>

#include <limits.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define MC_INVENTORY_MAX_RECORDS ((size_t)65536)

enum mc_inventory_status {
    MC_INVENTORY_EMPTY = 0,
    MC_INVENTORY_CANDIDATE = 1,
    MC_INVENTORY_ERR_ARGUMENT = -1,
    MC_INVENTORY_ERR_ALLOC = -2,
    MC_INVENTORY_ERR_QUERY = -3,
    MC_INVENTORY_ERR_MALFORMED = -4,
    MC_INVENTORY_ERR_CALLER_MISSING = -5,
};

#ifndef MC_SYSCTL
#define MC_SYSCTL sysctl
#else
extern int MC_SYSCTL(int *, u_int, void *, size_t *, void *, size_t);
#endif

static int
mc_compare_pid(const void *left, const void *right)
{
    pid_t lhs = *(const pid_t *)left;
    pid_t rhs = *(const pid_t *)right;

    return (lhs > rhs) - (lhs < rhs);
}

static int
mc_valid_status(char status)
{
    return status == SIDL || status == SRUN || status == SSLEEP ||
        status == SSTOP || status == SZOMB;
}

static int
mc_comm_equals_truncated(const char comm[MAXCOMLEN + 1], const char *worker)
{
    size_t worker_length = strlen(worker);
    size_t expected_length = worker_length < MAXCOMLEN ? worker_length : MAXCOMLEN;

    return comm[expected_length] == '\0' &&
        memcmp(comm, worker, expected_length) == 0;
}

static int
mc_is_candidate(const char comm[MAXCOMLEN + 1])
{
    return mc_comm_equals_truncated(comm, "MacControlExecutor") ||
        mc_comm_equals_truncated(comm, "StopSpikeWorker");
}

int
mc_inventory(uid_t uid, pid_t caller)
{
    const size_t record_size = sizeof(struct kinfo_proc);
    struct kinfo_proc *records;
    pid_t *pids;
    size_t capacity;
    size_t bytes;
    size_t count;
    size_t index;
    int caller_seen = 0;
    int candidate_seen = 0;
    int mib[4];
    int query_result;

    if (uid == 0 || uid > INT_MAX || caller <= 0) {
        return MC_INVENTORY_ERR_ARGUMENT;
    }
    if (record_size == 0 || MC_INVENTORY_MAX_RECORDS > SIZE_MAX / record_size) {
        return MC_INVENTORY_ERR_ALLOC;
    }

    capacity = MC_INVENTORY_MAX_RECORDS * record_size;
    records = calloc(MC_INVENTORY_MAX_RECORDS, record_size);
    if (records == NULL) {
        return MC_INVENTORY_ERR_ALLOC;
    }

    mib[0] = CTL_KERN;
    mib[1] = KERN_PROC;
    mib[2] = KERN_PROC_UID;
    mib[3] = (int)uid;
    bytes = capacity;
    query_result = MC_SYSCTL(mib, 4, records, &bytes, NULL, 0);
    if (query_result != 0) {
        free(records);
        return MC_INVENTORY_ERR_QUERY;
    }
    if (bytes == 0 || bytes >= capacity || bytes % record_size != 0) {
        free(records);
        return MC_INVENTORY_ERR_MALFORMED;
    }

    count = bytes / record_size;
    pids = malloc(count * sizeof(*pids));
    if (pids == NULL) {
        free(records);
        return MC_INVENTORY_ERR_ALLOC;
    }

    for (index = 0; index < count; index++) {
        const struct kinfo_proc *record = &records[index];
        const struct extern_proc *process = &record->kp_proc;

        if (process->p_pid <= 0 ||
            record->kp_eproc.e_ucred.cr_uid != uid ||
            process->p_starttime.tv_sec <= 0 ||
            process->p_starttime.tv_usec < 0 ||
            process->p_starttime.tv_usec >= 1000000 ||
            !mc_valid_status(process->p_stat) ||
            memchr(process->p_comm, '\0', sizeof(process->p_comm)) == NULL) {
            free(pids);
            free(records);
            return MC_INVENTORY_ERR_MALFORMED;
        }

        pids[index] = process->p_pid;
        caller_seen |= process->p_pid == caller;
        candidate_seen |= mc_is_candidate(process->p_comm);
    }

    qsort(pids, count, sizeof(*pids), mc_compare_pid);
    for (index = 1; index < count; index++) {
        if (pids[index - 1] == pids[index]) {
            free(pids);
            free(records);
            return MC_INVENTORY_ERR_MALFORMED;
        }
    }

    free(pids);
    free(records);
    if (!caller_seen) {
        return MC_INVENTORY_ERR_CALLER_MISSING;
    }
    return candidate_seen ? MC_INVENTORY_CANDIDATE : MC_INVENTORY_EMPTY;
}
