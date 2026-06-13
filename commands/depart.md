# Depart

Run when you're **leaving a Mac** — switching to the other one, or done for the session. It does the
end-of-session hygiene **and** the cross-Mac handover: wraps the log + state, commits with this Mac's
name stamped in, pushes, and confirms it's safe to switch.

Think of it as `/session-close` with the handover bits added. It does **not** duplicate that
checklist — it runs it, then adds the machine-stamp and push-safety. Pairs with `/arrive`.

**Detect mode:**
- `docs/PROJECT_STATE.md` exists → `docs/` paths (installed project)
- else `./PROJECT_STATE.md` → root paths (master repo)

## Step 1 — Who am I?

```bash
MAC=$(cat ~/.claude/this-mac 2>/dev/null || scutil --get LocalHostName 2>/dev/null || hostname -s)
echo "Departing from: $MAC"
```

## Step 2 — Run the close-session hygiene

Do **Steps 1–5 of `/session-close`** (`commands/session-close.md`): identify today's session log and
ensure its required sections, extract any real decisions into `decisions.md`, sync `PROJECT_STATE.md`
(bump *Last updated*, update Focus / Next / Recent), and sync `sessions/_index.md`. Don't re-document
those steps here — run them. (Confirm with the user, as that checklist does.)

## Step 3 — Commit, stamped with this Mac

Stage what this session touched. If `git status` shows unrelated in-flight code, name it and ask
whether to include it (default: only what this session changed — same rule as session-close Step 6).

Commit with a `Handoff-from:` trailer so the other Mac's `/arrive` can say "from <Mac>":

```bash
git commit -m "session: $(date +%F) handover

Handoff-from: $MAC"
```

**Why a commit trailer and not a timestamp in a .md file:** the trailer lives in git history —
immutable and conflict-free. Writing "pushed at HH:MM on MacN" into a tracked `.md` would duplicate
what git already records *and* invite the two-Macs-edit-the-same-line sync-conflict. Let git hold it;
`/arrive` reads it back.

## Step 4 — Push (the whole point of departing)

```bash
git push
```

Handle the cases:
- **No remote** → "This project has no GitHub remote, so this commit stays on this Mac — the other Mac
  won't see it (git history doesn't travel by Syncthing). Add a remote so handover works?"
- **Rejected ("fetch first")** → origin moved (the other Mac pushed). **STOP, don't force.** Reconcile
  via `37_multi-mac-discipline.md` Rule 1, then push.
- **On a feature branch** and your git rules forbid pushing to `main` → push the feature branch; don't
  auto-merge to main.
- **Nothing to commit** → skip the commit, but still `git push` any unpushed local commits so the other
  Mac sees them.

## Step 5 — Confirm (honestly)

On full success:

```
✓ <Project> wrapped on <Mac> · <local time>
  log + state synced · committed · pushed
  Safe to switch Macs — run /arrive on the other one after Syncthing settles.
```

If something didn't happen (no remote, nothing to push, push deferred), **say that** instead of the
clean line. Never claim "pushed" if it wasn't.

## When to invoke

- Before switching to the other Mac.
- End of a working session you'll resume later.
- Before walking away mid-session for a while.

## What it intentionally does NOT do

- Force-push or auto-resolve a diverged branch — it stops and points you at the reconcile rule.
- Write handover timestamps into tracked files — git's commit metadata is the source of truth.

Source: `commands/session-close.md` (hygiene steps), `commands/arrive.md` (the other half),
`37_multi-mac-discipline.md`.
