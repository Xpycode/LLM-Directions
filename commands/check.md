# Check — one review command

Audit the work and report. **`/check` replaces `/code-review`, `/quality`, `/reflect`, `/review`,
and `/minimums`.** It has three modes:

| `/check <mode>` | Absorbs | Use when |
|---|---|---|
| **`code`** (default) | code-review + quality + reflect | before a commit/merge, after AI-generated code or a refactor |
| **`ship`** | review + minimums | before a release — production readiness + baseline features |
| **`security`** | security-audit | before deploy, after auth/input/upload changes |

## Golden rule — audit and present, don't interrogate

The old `/review` + `/minimums` walked 40+ checklist items asking "✓ this? ✓ that?". **Don't.**
Claude does the audit itself, then presents **one bucketed findings table** and asks **at most one**
question. Pattern-matching finds candidates; **context decides if they're real** — verify each match,
don't just grep. For deep contextual analysis on a large diff, hand off to the `feature-dev:code-reviewer`
agent (it filters by confidence and understands structure, not just patterns).

---

## Mode: `code`  (default)

Review the diff across perspectives, measure health, report a verdict.

1. **Collect** — `git diff --cached` (staged), `git diff HEAD` (all), or `git diff main...HEAD` (branch).
   List the changed files + what changed.
2. **Multi-perspective pass** — read each changed file through five lenses:
   | Lens | Asks |
   |---|---|
   | Bug hunter | What crashes? What's unhandled? Force-unwraps, swallowed `try?`, off-by-one? |
   | Security | Hardcoded secrets? Unvalidated input? Auth on protected paths? Internal detail in errors? |
   | Quality | Duplication? File > 400 lines / function > 50 / nesting > 3-4? Magic numbers? Dead/commented code? |
   | Test coverage | New code tested? Error paths covered? Edge cases (empty/nil/max/concurrent)? |
   | Architecture | Fits existing patterns? Technical debt introduced? |
3. **AI-typical smells** (recently-changed files) — happy-path bias (every `if` has an `else`/handling;
   network + file ops have failure paths), verbosity (near-duplicate impls, abstractions used once),
   unguarded `print()` in production paths. **Verify `print(`/`try?` in context** — OK inside
   `#if DEBUG` / `#Preview` / `Logger` / CLI output; a flag is only a flag once context confirms it.
4. **Health metrics** (on request or for a "codebase feels bloated" check):
   `find . -name '*.swift' -not -path './.build/*' | xargs wc -l | tail -1` (LOC), file count, top-10
   largest. Thresholds: LOC <10k healthy / >30k review; largest file <300 healthy / >500 review;
   feature interactions `2^n−1−n` (>100 → review boundaries); test coverage >60% healthy / <40% review.
5. **Report** — severity buckets + verdict:
   ```
   Critical (must fix before commit): crash / security / data-loss — `file:line`
   Important (fix soon): missing error handling, untested paths
   Minor (note): style, small refactors    ·    Nitpick: ignore
   Verdict: ✅ Approved · ⚠️ Needs work · 🚫 Blocked (security)
   ```
   A security finding is always Critical — **STOP and fix before any commit.** SwiftUI specifics
   (`20_swiftui-gotchas.md`): view bodies < 100 lines, clear state ownership, no heavy compute in body.
   Reference: `35_ai-code-quality.md`.

## Mode: `ship`

Production readiness + baseline features, as an audit — not a 40-question walk.

1. **Load** `30_production-checklist.md` (release prep), `33_app-minimums.md` (baseline: auto-update,
   version visibility, signing, icons, logging, prefs, error/empty/loading states, shortcuts, About,
   menu bar, window state), and `62_final-stretch-triage.md` (the *methodology*: capture-don't-fix).
2. **Audit against them yourself** — walk the code/app, don't quiz the user. Capture every gap; **do
   not fix mid-pass** (#62 Rule 1).
3. **Triage into three buckets** honestly (most "seems off" items are 2 or 3 wearing bucket-1 clothes):
   | Bucket | Definition | Default |
   |---|---|---|
   | **1 — Ship-blocker** | crash, data loss, core feature broken | fix before ship |
   | **2 — Should-fix** | annoying but survivable | fix if cheap, else v1.1 |
   | **3 — Polish** | nobody will notice | v1.1 |
   A large bucket 3 is good — it means the worst thing left is cosmetic.
4. **Present one table** grouped by bucket + a summary line: "X/Y passed · N ship-blockers · [ready once
   bucket 1 clears]". If there's no written "done for v1" line yet, write one now (#62 Rule 8) — it's
   what gives bucket 3 permission to wait. Then one question: "add bucket-1 gaps to this session's tasks?"

## Mode: `security`

Run the full checklist in **`63_security-audit.md`** (OWASP / VibeSec: access control / IDOR /
injection / secrets / auth / uploads). That doc is the home; this mode loads and applies it, then
reports findings in the same three-bucket table as `ship` (a real vuln is always bucket 1). For the
always-on security *rules*, see `54_security-rules.md`.

---

## What `/check` does NOT do

- **Interrogate** — no item-by-item "✓?" prompts (the deliberate reversal of old `/review` + `/minimums`).
- **Fix mid-pass** in `ship`/`security` — capture first, triage, then fix (#62).
- **Extract learnings** — that's `/log` §4 (the old `/reflect`→`/compound` handoff now lives there).

Source: `35_ai-code-quality.md`, `30_production-checklist.md`, `33_app-minimums.md`,
`62_final-stretch-triage.md`, `63_security-audit.md`; `feature-dev:code-reviewer` agent for deep passes.
