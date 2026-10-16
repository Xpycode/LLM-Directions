# Log Decision

We just made a decision worth recording.

**Detect path mode:** `docs/decisions.md` exists → use `docs/decisions.md` (installed project);
else `./decisions.md` exists → use root `decisions.md` (master repo). Read only the first data row
of `sessions/_index.md` if you need session context — never the whole file.

Ask:
1. "What did we decide?"
2. "What were the alternatives?"
3. "Why this choice?"

Then append to the detected decisions file:

```markdown
### [DATE] - [Decision Title]
**Context:** [What prompted this]
**Options:** [What we considered]
**Decision:** [What we chose]
**Rationale:** [Why]
```

**Length budget:** an ADR should fit roughly one screen (~40 lines). If the decision needs more —
follow-up addenda, side-discoveries, multi-round investigation — put that detail in the session
log instead and link to it, or add a one-line pointer here ("see `sessions/YYYY-MM-DD.md` for
detail"). Don't let a single ADR grow past a screen; that's a sign it should be split or trimmed
to a Condensed Log entry once it's no longer current.
