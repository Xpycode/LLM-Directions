# Task state and current handoff

Read when creating a plan, changing task status, reconciling legacy records or computing progress.
Resolve this file from the Directions master, never a copied consumer reference.

The **selected plan** owns task IDs, dependencies, gates, status and evidence. Identify tasks by
plan path plus ID. Status is pending, implemented-unverified, blocked (with exact gate), or complete
(all required task evidence present). Check a task only when complete. External acceptance remains
separate; completing source code does not pass an unperformed device or manual check.

`TASKS.md` owns Backlog and Inbox plus an Active plan link, not duplicate plan checkboxes. Standalone
work without a plan stays in TASKS. PROJECT_STATE's Execution pointer names the selected plan,
current IDs and ready/blocked/awaiting-acceptance reason. Report completed/total tasks **for that
plan**, plus open external gates. Never add unrelated backlog/archive counts to that denominator.

Selection order: explicit current request, state Execution pointer, then a single unambiguous active
plan at established root/docs/specs paths. If multiple plans remain ambiguous, ask which; do not
aggregate equal task IDs from different plans. Missing plan/evidence is unknown, not complete.

PROJECT_STATE's **Current handoff** links one specific session-log Resume anchor. That record is
the current pickup; older Resume/Next blocks are historical evidence. On close, append/update one
clearly identified current handoff and replace the pointer. Retain old evidence and original-Mac
recovery obligations; pointer replacement does not close them. Plain logging may refresh the current
pointer when facts change without requiring a full pre-clear ceremony.

## Legacy reconciliation (only when migration is in scope)

1. Preserve exact originals and record their hashes/locations before edits. Never overwrite the
   original backup on a rerun. If it already exists with different content, stop and investigate.
   Obtain hashes from an executed standard checksum tool/library or a trusted receipt identifying
   the exact bytes; never invent a digest or claim a computation that did not run. If unavailable,
   retain the originals and mark hash verification unavailable; reconciliation remains blocked.
   Verify every recorded digest against its retained file before claiming all hashes match.
2. Inventory all plans, mirrored checkboxes, evidence/gates and incoming links. Record discrepancies;
   do not promote a task from a checked tracker alone. Resolve against actual evidence or leave open.
3. Write the selected plan's reconciled statuses and evidence, then validate counts, links and gates.
4. Update state selection/current-handoff pointers and TASKS Active plan link. Only after those
   validate may reconciled duplicate mirrors be retired; retain the original evidence copy.
5. On interruption, read the last durable step and original records. Repeating produces the same
   task identity, counts and links without duplicating history. Never remove mirrors before the
   canonical replacement is validated. Report unresolved discrepancies explicitly.

New plans use this contract. Legacy records remain readable until explicitly migrated; read-only
status does not initiate migration. No bulk consumer migration follows from updating these commands.

On full acceptance (or explicit scoped deferral), archive the completed plan **and its evidence**,
update incoming links, verify archived links resolve, then retire the active copy. Preserve partial
work and open gates in place. TASKS standalone completed items may still move to tasks-archive;
that historical total is separate from active-plan progress.
