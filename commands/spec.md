# Create Feature Spec

Create a specification before implementation. **`/spec` absorbs `/interview` (deep mode) and
`/example-map` (examples mode)**; `/new-feature` is retired (the spec replaces the feature-doc scaffold).

| `/spec <arg>` | Mode | Use when |
|---|---|---|
| (none) + a feature name | **mini-PRD** | you know roughly what you want — a focused feature spec |
| "deep", "interview", or a whole new project | **discovery** | new project / complex system / many unknowns — multi-phase triangulation |
| "examples", "example map" | **examples** | complex business logic — discover requirements through concrete examples |

Before starting, apply `60_model-selection.md` → **User-Facing Model-Fit Notice**. Spec work normally
starts at deep capability with high reasoning. Show one provider-neutral notice only when that is a
change or a consequential recommendation. The Claude-specific block below fulfils this step for
Claude Code; do not emit both notices.

<!-- CLAUDE-ONLY:START — Codex skips this model-marker integration -->
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
<!-- CLAUDE-ONLY:END -->

## New-project assessment

For a whole new project or a substantial uncommitted expansion, use this assessment before
technical discovery, scaffolding or a build plan, including natural-language requests to start
something new. Skip it for routine fixes, adding Directions to existing work, and resuming approved
implementation. Reuse the user's stated choices and existing answers; ask only what is missing,
one question at a time. Do not reopen a settled choice without new evidence or changed scope.

1. **Outcome:** What do you want to accomplish, and what would make it worthwhile? Personal use,
   publishing/selling, learning, enjoyment and craft are valid purposes. Preserve the intended
   finish line; do not substitute a personal-use prototype for a requested commercial release.
2. **Pain:** Think of the last time this came up. What did you use, what was unsatisfactory, and
   how often does that happen? Ask about its cost where useful; learning or craft need no pain story.
3. **Alternatives:** Could an existing app, configuration, small script or improvement to one of
   your projects solve enough of it? Use known alternatives first; research only a decision-relevant
   gap. Building may itself be the benefit for learning or enjoyment.
4. **Investment:** What is the smallest result that achieves your purpose, and how much time,
   attention and ongoing maintenance is it worth before reconsidering? This is an investment limit,
   not a promised completion estimate.
5. **Competing commitments:** If this starts now, what gets less attention, and is that intentional?
   Include non-project commitments when relevant; no portfolio inventory or fixed work-in-progress cap.

Recommend **use existing / improve existing / bounded experiment / build now / park**, with a brief
reason. The user chooses; an explicit choice already supplied needs no renewed approval. For use
existing or park, end without scaffolding, a full spec or implementation backlog. For improve
existing, route to that project and its scoped change. For an experiment, plan only that experiment.
Continue build discovery within the chosen scope; assessment alone does not authorize implementation.

For substantial work whose usefulness is uncertain, identify the critical benefit assumption,
the smallest representative check, expected observation and what result would change the decision.
Distinguish usefulness from technical feasibility; a working import need not improve the real task.
Learning can use demonstrated understanding, without market-demand evidence. Reuse the check's
resource limit and stop/replan fields in `55_spec-template.md`; an inconclusive check remains unresolved.
Further investigation needs a plausible decision-changing result within the remaining limit.

Record a reconsideration trigger: failed critical assumption, investment limit or material scope
expansion. At that trigger, compare remaining benefit/cost with alternatives and current assets and
obligations; continue, simplify, replace or park with a reason. Past effort alone is not a reason to
continue. Stop the affected approach or expansion, while unrelated authorized ready work continues.

Keep the conclusion once in the existing spec's problem/solution fields, linking a consequential
decision if already recorded. If no spec is warranted, summarize in the conversation or an existing
session/decision record; do not create a project or a separate commitment tracker to store a rejection.

## Workflow journey and feasibility (all modes)

Before substantial workflow implementation, establish one concrete user journey: source/input →
user action → destination/output → observable success. Example: the user selects an existing CSV,
imports it into a named collection, then exports that collection to a chosen CSV path; success means
the exported rows match the accepted fixture and the user can locate the file. Resolve missing
destinations or success conditions before broad implementation. Use existing answers where available.
If feasibility is unknown, specify a spike's observable result, agreed limit and stop/replan condition;
new subsystems require a scoped decision. See `commands/make-plan.md` for a bounded example.

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

Start with the **New-project assessment** when its trigger applies; honor its selected route before
continuing below. Multi-phase discovery with triangulation: understand before choosing technical
solutions. One question at a time; reuse known answers throughout.

1. **Scope** — the one thing it must do (one sentence) · how we'll know it works · what's explicitly NOT in scope.
2. **Explore** — establish the six core answers, asking only for gaps, then branch:
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
3. **Triangulate** — cross-check requirements against the intended outcome and investment limit
   (e.g. scope exceeds the chosen limit, or a web app needs unsupported native file access).
   Personal use plus complexity is not itself a contradiction. If found:
   *"[X] and [Y] seem to conflict — clarify?"*
4. **Synthesize** — write `specs/[feature-name].md` using `55_spec-template.md`, carrying the assessment
   conclusion once when applicable; set PROJECT_STATE funnel to `define` + note doc flags; map answers
   to tech via `04_architecture-decisions.md`.
5. **Validate** — read back a 3-point summary + the acceptance criteria; correct and re-triangulate if needed.
6. **TASKS.md** — extract actionable tasks from the acceptance criteria into the task tracker's
   Backlog (`docs/TASKS.md` in an installed project; root `TASKS.md` in the Directions master). Create
   it from the master template if absent. Report "Added N backlog items. Run `/make-plan` to create the
   selected plan and link it under Active plan." The plan owns task status/evidence; retain backlog
   mappings without mirrored checkboxes, following the master `reference/task-state.md`.

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
