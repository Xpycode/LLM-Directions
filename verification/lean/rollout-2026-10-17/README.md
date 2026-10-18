# Local deployment and consumer routing migration — October 17, 2026

User explicitly requested “deploy and migrate then” after accepting the presented instruction-size
increases. This authorizes this Mac's local rollout despite the still-open host acceptance gate;
it does not pass E1, establish runtime savings, resume provider tests or authorize desktop control.

## Deployed installation

Both dry runs passed, followed by the authorized live deployers:

- `bash deploy-codex.sh`: active `/Users/sim/.codex` installation; live managed block matches
  rendered source, personal bytes outside the block are unchanged, and the Directions skill
  resolves to the actual master directory (the old symlink's capitalization differs only).
- `bash redeploy.sh`: `/Users/sim/.claude`; all 13 canonical command copies and global instructions
  match rendered source. Independent `mcp-profile.md` and `preview.md` are byte-identical to backups.
  Existing settings, permissions and hook registrations already matched; the authored shell-check
  skill was refreshed with its automatic backup. No application was restarted or controlled.

Retained automatic backups include:

- `/Users/sim/.codex/AGENTS.md.bak-20261017-222115`
- `/Users/sim/.claude/CLAUDE.md.bak-20261017-222123`
- `/Users/sim/.claude/commands.bak-20261017-222123`
- `/Users/sim/.claude/skills/shell-check.bak-20261017-222123`

No pull, checkout, branch mutation, commit or push was performed. This deploys the reviewed local
master, whose pre-existing dirty evidence/state is preserved. Other Macs are not deployed by this
operation. Start a new Codex session and restart Claude Code manually to refresh their loaded state.

## Consumer scope and preservation

Read-only discovery under `/Users/sim/ProgrammingProjects` selected 110 existing project roots
with `docs/PROJECT_STATE.md`, including three nested App-Websites project roots. Archive directories,
master verification fixtures, exports, dependencies and build trees were excluded. Nonstandard
root-only state files without that sentinel were not treated as Directions consumers.

The migration changes 261 instruction files:

| Action | Files | Preservation |
|---|---:|---|
| Add missing tool entry point | 117 | Read the existing companion for project facts; no invented build commands |
| Append shared-master routing | 111 | Entire original byte sequence remains an unchanged prefix |
| Replace identical generic placeholder | 33 | Exact originals backed up; replace guessed Swift commands with project/master discovery |

The routing section supersedes older generic workflow/copy-loading, automatic app-control and PR
instructions while preserving project-specific product, architecture, build and security rules.
Both tool entry points are present at each selected root; four additional nested website Claude
files also receive routing and matching Codex entry points. Complete canonical procedures are
read from the master; no command library or numbered universal guide was copied into a consumer.

Full Git status inspection found 59 roots with Git metadata (39 dirty), and 51 without local Git
metadata. No missing repository was reconstructed and no dirty tree was reset, stashed or cleaned.
All 1,950 numbered guide copies are retained byte-for-byte as legacy references, explicitly removed
from workflow authority. Differing copies can hold project-specific additions; migration does not
claim their contextual extraction or physical deletion is complete. Existing links keep resolving.

Consumer task/state schemas are unchanged. The master procedures support legacy records; this
rollout does not bulk-reconcile task mirrors, select competing plans, archive old plans or close gates.

## Verification and recovery

[Migration script](migrate.py) and [receipts](receipts.json) retain paths, actions, SHA-256 values,
pre-migration repository status digests and backup locations. Complete originals and the exact plan
are private and outside the repositories:

`/Users/sim/.local/state/directions-migrations/2026-10-17`

Before the first consumer write, the script rehashed every target and retained guide/state record,
then saved and verified all 144 existing originals. It rechecked each target immediately before
writing. Final verification passes for all 261 installed entries and original backups, unchanged
hashes for 1,950 guides, and 1,792 state/spec/plan/history records. Receipts have no copied file bodies.
An unchanged rerun uses `verify`; `plan`/`apply` refuse already migrated entries or existing receipts.

Disposable validation passed installation/prefix preservation, rejection of a concurrent edit before
backup or consumer writes, and detection of backup corruption. The first fixture setup had a
redundant directory creation and stopped before exercising the migration; the fixture was corrected
and all three checks passed. No consumer build, test script, network/model request or UI ran.

For recovery, compare current content with the recorded after-hash first. Restore only a matching,
selected file from its verified original backup; do not overwrite subsequent user work. Newly
created files have a null before-hash and must only be removed after checking their current hash
and incoming references. No recovery action was needed or performed.

Final shared integration validation passes for 47 routes, recursively reachable references,
reviewed guide pins and the unchanged Mac-control plan. Session index coverage is 63/63; edited
Markdown links/current handoff resolve and `git diff --check` passes. No independent agent review
of this rollout is claimed.

Observed-host instruction adherence and runtime effects remain unverified. The listed source-size
increases are accepted, while other unlisted tradeoffs, historical runtime regressions, the thirty
deferred Claude observations and E1 remain open. Pilot/upstream and Mac-control recovery stay parked.
