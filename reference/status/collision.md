# Same-folder session collision procedure

Two agent sessions in the **same folder** share one git checkout (one HEAD) — if either runs
`git checkout`, it switches the branch for **both**. Use this trigger table:

| Entry | Collision check |
|---|---|
| Ordinary read-only status or full, no known concurrency | Skip the detector; omit collision status. |
| Arrive, including its aliases | Check with the supported detector; report limitations if unavailable. |
| Known concurrent sessions, in any mode | Check and surface the known risk even if the detector is silent. |
| Before branch, checkout or worktree mutation | Apply `37_multi-mac-discipline.md` Rule 5 mutation preflight, including merge/rebase/pull and recovery operations. |
| Existing SessionStart hook | Unchanged; narrowing status does not disable startup checks. |

For a triggered check, verify the intended checkout first, then use the host's supported detector:

<!-- CLAUDE-ONLY:START — this process detector currently recognizes Claude Code CLI sessions -->
```bash
bash ~/.claude/hooks/session-guard.sh 2>/dev/null \
  || bash /Users/sim/ProgrammingProjects/0-DIRECTIONS/__DIRECTIONS/hooks/session-guard.sh 2>/dev/null
```

- **No output** → no warning was detected; this is not proof of no collision (missing tools or
  uninspectable processes can also be silent). Preserve known concurrency and report unavailable
  detection when relevant to arrival or a mutation.
- **A warning block** → show it plainly: *another agent session shares this checkout; coordinate git
  in one session, or split off with `/worktree`.* Different worktrees have distinct HEADs; shared
  branch refs and worktree administration still require coordination.
<!-- CLAUDE-ONLY:END -->

**Codex fallback:** no Directions process detector is installed yet. Do not run the Claude detector
or claim there is no collision. At arrival or before a mutation, state that automatic detection is
unavailable and use known session/worktree information under Rule 5. If another live session shares
this checkout, warn and coordinate one Git driver or offer `/worktree`. Ordinary status/full with
no known concurrency omits collision status.

Read-only — it inspects running processes, never touches git.
