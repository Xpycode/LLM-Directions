# Create Feature Spec

Create a specification before implementation. **`/spec` absorbs `/interview` (deep mode) and
`/example-map` (examples mode)**; `/new-feature` is retired (the spec replaces the feature-doc scaffold).

| `/spec <arg>` | Mode | Use when |
|---|---|---|
| (none) + a feature name | **mini-PRD** | you know roughly what you want — a focused feature spec |
| "deep", "interview", or a whole new project | **discovery** | new project / complex system / many unknowns — multi-phase triangulation |
| "examples", "example map" | **examples** | complex business logic — discover requirements through concrete examples |

## Step 0 — Model tier check (nudge, don't gate)

Speccing resolves ambiguity and shapes a feature — **Opus-tier** judgment (Fable if gnarly).

```bash
SID=$(ls -t "$HOME"/.claude/.current-model-* 2>/dev/null | head -1 | sed "s:.*/.current-model-::")
[ -n "$SID" ] && printf 'spec' > "$HOME/.claude/.session-phase-$SID"
MODEL=$(cat "$HOME/.claude/.current-model-$SID" 2>/dev/null)
echo "phase: spec · current model: ${MODEL:-unknown}"
```

If `MODEL` is Sonnet/Haiku, **nudge once then continue** (don't gate — a mis-tiered spec is rarely costly):
> 🔴 **You're on `<MODEL>` — speccing is Opus-tier judgment work. Consider `/model opus`.**
Already Opus/Fable → say nothing.

## Mode: mini-PRD  (default)

Ask in three short rounds (one question at a time; "I don't know" is valid — note it as an open question):
1. **Core** — feature name (→ filename) · problem it solves (one sentence) · who has it.
2. **Solution** — one-sentence solution · 3–5 key capabilities · the user flow.
3. **Criteria & boundaries** — for each capability: *"Given [state], when [action], then [result]?"*
   (Given/When/Then, see `56_acceptance-criteria.md`) · what's explicitly OUT of scope · technical
   constraints · open questions.

**If the feature involves UI:** check `47_project-ui-conventions.md` and flag conflicts (NavigationSplitView,
SwiftUI Button, HSplitView are not allowed).

Then write `specs/[feature-name].md` from `55_spec-template.md` (Problem / Proposed Solution /
Acceptance Criteria / Technical Considerations / Out of Scope / Open Questions). Update `PROJECT_STATE.md`
with the spec reference, and confirm: *"Spec created. Next: resolve open questions, then `/make-plan`."*

## Mode: discovery  (adds the old `/interview` — for whole projects / big unknowns)

Multi-phase discovery with triangulation. One question at a time; don't solve during discovery — understand.

1. **Scope** — the one thing it must do (one sentence) · how we'll know it works · what's explicitly NOT in scope.
2. **Explore** — always ask the six core questions, then branch on the answers:
   | # | Question | Informs |
   |---|---|---|
   | 1 | Who uses it? | complexity level |
   | 2 | What platform? | tech stack |
   | 3 | Persists data? | storage architecture |
   | 4 | Works with files? | security, coordinates |
   | 5 | Talks to internet/devices? | async, error handling |
   | 6 | What similar thing exists? | UX expectations |
   Follow-up doc-flags: images/video → flag `21_coordinate-systems.md`; macOS + outside-sandbox/startup →
   `22_macos-platform.md`; for distribution → notarization/sandboxing (`61_distribution-notarization.md`);
   complex UI → `20_swiftui-gotchas.md`.
3. **Triangulate** — cross-check for contradictions (e.g. "just for me" + complex = scope-creep risk;
   web app + native file access = architecture mismatch). If found: *"[X] and [Y] seem to conflict — clarify?"*
4. **Synthesize** — write `specs/[feature-name].md` (Overview / User Stories / Acceptance Criteria /
   Technical Considerations / Edge Cases / Out of Scope); set PROJECT_STATE funnel to `define` + note
   doc flags; map answers to tech via `04_architecture-decisions.md`.
5. **Validate** — read back a 3-point summary + the acceptance criteria; correct and re-triangulate if needed.
6. **TASKS.md** — extract actionable tasks from the acceptance criteria into `TASKS.md` Backlog (create
   from template if absent). Report "Added N tasks. Run `/make-plan` to move them to Current Sprint."

## Mode: examples  (adds the old `/example-map`)

Discover requirements through concrete examples — for features with real business logic. Full
methodology: `59_example-mapping.md`. Run the four card types:
- **Story** (yellow) — "User can [action]".
- **Rules** (blue) — business rules / validation / limits that govern it.
- **Examples** (green) — per rule, a concrete happy-path + edge + error case, each as Given/When/Then.
- **Questions** (red) — anything unclear: decisions to make, ambiguities, things to research.

Write into `specs/[feature-name].md` under an `## Example Map` section (Story · Rules & Examples as
Given/When/Then · Open Questions). Report counts (rules / examples / questions), then: *"Resolve open
questions, then `/make-plan` (or `/spec` to formalize the full spec first)."*

Source: `55_spec-template.md`, `56_acceptance-criteria.md`, `59_example-mapping.md`, `04_architecture-decisions.md`.
