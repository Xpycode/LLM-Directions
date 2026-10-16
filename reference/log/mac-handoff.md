# Mac / Git handoff

Load only in Mac-handoff mode or for an explicitly requested logging commit. Respect no-commit
and no-push independently: save the log/state/index and report the unsynced work when either
action is restricted. A commit request alone does not authorize push. Ordinary plain/pre-clear
logging does not commit; existing execution commits do not authorize a new logging commit.
Read `<master>/37_multi-mac-discipline.md` before cross-Mac reconciliation.

```bash
MAC=$(cat ~/.config/directions/this-mac 2>/dev/null \
  || cat ~/.claude/this-mac 2>/dev/null \
  || scutil --get LocalHostName 2>/dev/null \
  || hostname -s)
```

1. **Stage only what this session touched.** If `git status` shows unrelated in-flight code, name it
   and ask whether to include it (default: only the docs/session files).
2. **Commit, stamped with this Mac** — a `Handoff-from:` trailer lives in git history (immutable,
   conflict-free); never write "pushed at HH:MM on MacN" into a tracked `.md` (that invites the
   two-Macs-edit-the-same-line conflict). `/status arrive` reads the trailer back.
   ```bash
   git commit -m "session: $(date +%F) + sync state

   Handoff-from: $MAC"
   ```
   ⚠️ **Keep every trailer in ONE final paragraph — no blank line between them.** Git parses only
   the *last* paragraph as trailers, so a `Co-Authored-By:` (or any second trailer) separated by a
   blank line silently demotes `Handoff-from:` to ordinary body text. It still *looks* right in
   `git log`, but `%(trailers:key=Handoff-from,valueonly)` — what `/status arrive` actually reads —
   returns empty, and the other Mac falls back to author/date with no Mac name. Correct shape:
   ```
   session: 2026-08-20 + sync state

   <body…>

   Handoff-from: M4-Pro
   Co-Authored-By: …
   ```
   Verify before moving on — a stamp that doesn't parse is worse than none, because it reads as
   present:
   ```bash
   git log -1 --format='%(trailers:key=Handoff-from,valueonly)'   # must print the Mac, not empty
   ```
   *(Recorded 2026-08-20, after `ed7eaec` shipped with exactly this defect — unfixable without
   force-pushing already-pushed history, so it stands as the example.)*
3. **Push only when authorized and not prohibited** — an *unpushed* commit is as invisible to the other Mac as an uncommitted file.
   - **No remote** → say so: the commit stays on this Mac; offer to add a remote.
   - **Rejected ("fetch first")** → origin moved (other Mac pushed). **STOP, don't force.** Reconcile
     via `37_multi-mac-discipline.md` Rule 1, then push.
   - **Feature branch + git rules forbid pushing `main`** → push the branch; don't auto-merge.
   - **Nothing to commit** → still push any unpushed local commits.
4. **Confirm honestly.** Verify the scoped tree and remote status. Do not call a switch safe while
   unrelated unsaved work or original-Mac recovery remains unresolved. On full success:
   `✓ <Project> wrapped on <MAC> · log + state synced · committed · pushed — safe to switch; run /status arrive on the other Mac after Syncthing settles.`
   If something didn't happen (no remote, nothing to push), **say that** — never claim "pushed" if it wasn't.


Return to the logging core. Under no-push/no-commit or any unresolved recovery, report exact
local/remote and recovery limits instead of the full-success message. Never force-push.
