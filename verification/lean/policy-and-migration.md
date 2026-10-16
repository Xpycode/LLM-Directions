# LE06 accepted contracts and disposable transition examples

Decision: `decisions.md`, October 16 lean workflow entry. No command policy is edited by LE06.
This contract consumes S01/S04–S07/S15–S21. Observations below are record walkthroughs, not host runs.

## Record contract

Identity is (selected plan path, task ID), never a bare number shared by different plans. A task is
pending, implemented-unverified, blocked (named missing dependency/gate), or complete with evidence.
Only complete is checked. External acceptance is listed separately. Progress is complete/total tasks
in the selected plan plus named open external gates; it is not combined with unrelated backlog totals.
The state Execution pointer names plan, current IDs and readiness. The state's Current handoff pointer
selects a log Resume anchor. Older anchors are historical even if their prose says “next”.

| Example input | Expected and walkthrough result |
|---|---|
| Plan A/1 checked with valid evidence; tracker A/1 unchecked | Preserve both originals; reconcile discrepancy, derive 1/2 from A after checking evidence, not tracker. |
| Plan A/2 implemented, device gate open; tracker says done | Leave A/2 unchecked, 1/2 and E1 open; discrepancy recorded, no acceptance invented. |
| Plan B also has task 1 | State selects A; B excluded from A denominator and kept intact. |
| No plan, one standalone backlog fix | TASKS remains authoritative for that item; do not create an empty plan. |
| Two plans and no reliable pointer or request | Selection required; do not merge their IDs/counts. |
| Old Resume says capture pending, new evidence says capture passed/recovery pending | New current handoff links both outcomes and outstanding recovery; old bytes retained as history. |
| Migration stops after backup before pointer update | Legacy remains readable; resume from preserved source; never remove mirrors first. |
| Migration runs twice | Same selected-plan counts and links; no duplicated tasks/history; original backup immutable. |
| All implementation checked but manual E1 open | Plan remains active, not archived or reported complete. |
| Fully accepted plan | Archive plan plus evidence; update all incoming links, then retire active copy. |

Each row was traced against the stated contract. `policy-examples.json` supplies a concrete legacy
and selected-plan record: a Python check derived [1, 2] and both expected mirror discrepancies without
altering the input. LE10's executable disposable fixtures will verify
counts, identity, preservation and idempotence. No production records were migrated here.

## Proportionality and boundary choices

| Work | Decision | Cost considered |
|---|---|---|
| Two tiny edits in the same lifecycle command | Serial owner; one coherent validated commit may record both IDs | Dispatch adds packet/review/integration with no safe independent writer. |
| Independent generator and test-guidance changes | Fresh agents with disjoint files; coordinator integrates | Extra packets/reviews justified by independent work and fault-finding; no timing claim. |
| User says no agents/no commits or only wave X | Honor limit and report serial reason/scope | Never infer broad authorization from the default. |
| Novel workflow | Concrete source→action→destination→outcome journey before substantial implementation | Catch mistaken product assumptions before broad work. |
| Spike needs new subsystem | Report current result and agreed limit, choose simplify/continue/park within explicit scope | Avoid uncontrolled expansion; preserve failed evidence. |

The delegation exception is **not adopted**. Existing independent-task delegation stays; AC08's
efficiency claim remains unverified. Other adopted choices are the approved plan's routine defaults.

Collision matrix: ordinary status has no detector; arrival and known concurrency use a supported
detector; checkout/switch/merge/rebase and worktree operations check identity/concurrency before
mutation. Existing SessionStart remains. Codex without a reliable detector reports limitations,
never “no collision” from missing output. Separate worktrees are distinct HEADs. A failed `cd` means
the intended repository was not inspected. LE12 must trace all command entry paths before narrowing.
