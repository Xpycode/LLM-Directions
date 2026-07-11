# 159 — Meta: blind-spot checklist — inject the perspectives Claude structurally forgets

**Tags:** meta, blind-spots, checklist, prompt-injection, self-review, quality, solo, review, /check, llm-failure-modes, @observable, mainactor, swift-concurrency, coordinate-systems, sandbox, security-scoped-bookmark, keychain, @appstorage, notarization, gatekeeper, gitignore, ui-changes

**Extracted from:** reverse-engineered from `claude-octopus`'s `config/blind-spots/` (2026-07-11).
Kept the *mechanism*, dropped the multi-vendor engine — seeds are sourced from **this repo's own**
numbered gotcha docs, not a stranger's SaaS.

## The idea

An LLM misses the *same categories* of thing over and over — not random errors, structural omissions
(threading, coordinate origins, sandbox scope, migration paths). `claude-octopus` surfaces these by
running a paid "council" of Codex/Gemini/Qwen and hoping their *different* blind spots cover Claude's.
That needs external CLIs, API keys, per-Mac wiring, and a ~2,500-line consensus engine — and its own
`debate.sh` admits *"convergent agreement between models may indicate shared blind spots, not
correctness."* So consensus ≠ correctness anyway.

The **transferable** half is the part that actually manufactures a second perspective from **one**
model at **zero** cost: a tiny keyword→prompt library that injects a *"did you check…"* checklist into
a review, plan, or spec. Same goal ("see what you'd otherwise skip"), none of the vendor machinery.
Instead of *renting other models' blind spots*, you *encode your own hard-won ones* — turning the 40+
numbered docs from passively-referenced into **actively-injected**.

## The mechanism (≈15 lines, no dependencies)

Each entry is `{ trigger_keywords[], injection_prompt }`. Match keywords against the task text,
concatenate the matched prompts into a bullet list, prepend it to the brief (or hand it to a subagent
as *"also verify these"*).

```bash
# blind-spots match: lowercase the task, emit the injection_prompt of every entry whose
# trigger regex hits. Requires jq + a blind-spots.json (seed below).  Usage:
#   ./bs-match.sh "add a crop offset for the retina thumbnail"
task=$(printf '%s' "$*" | tr '[:upper:]' '[:lower:]')
jq -r --arg t "$task" '
  .[] | select(any(.trigger_keywords[] as $k | ($t | test($k)); .)) | "- " + .injection_prompt
' blind-spots.json
# → "- Points vs pixels: a Retina image is 2×/3× its point size — are you multiplying …"
# NOTE: capture the keyword as $k first. `$t | test(.)` would re-bind `.` to $t and
# match every entry against itself — the keyword must be the regex, not the task.
```

No file, no cron, no hook required — you can also just **eyeball the table below** before a `/check`
and paste the 2–3 rows that match. The library is the value; the matcher is optional sugar.

## The seed library (grounded in THIS repo's docs)

Drop this as `blind-spots.json` if you automate, or read it as a table. Every `injection_prompt` cites
the doc it came from, so a match is a jump-off, not a dead end.

```json
[
  { "id": "swiftui-observable-state",
    "trigger_keywords": ["@observable","@state","viewmodel","not updating","view.?refresh","binding","nested mutation"],
    "injection_prompt": "@Observable tracks DIRECT property mutations only — mutating a nested object or array element won't redraw (20_ §1). @State holding a class ref won't re-render on internal change (20_ §2). Is the property observed at the level SwiftUI diffs?" },

  { "id": "swift-concurrency-mainactor",
    "trigger_keywords": ["async","await","\\btask\\b","@mainactor","sendable","background thread","data race","swift 6","\\bactor\\b"],
    "injection_prompt": "UI mutation must run on @MainActor; publishing from a background thread is a runtime warning / data race (20_ Threading). Swift 6 strict concurrency: is every value crossing an actor boundary Sendable? (swift-concurrency skill)." },

  { "id": "coordinate-points-pixels",
    "trigger_keywords": ["crop","offset","pixel","\\bpoint\\b","coordinate","retina","thumbnail","position","flipped","origin","exif"],
    "injection_prompt": "Points vs pixels: a Retina asset is 2×/3× its point size — multiply by scale before indexing pixels (21_). Origin: AppKit is bottom-left, SwiftUI/CG top-left — is Y flipped? (21_). EXIF orientation applied before cropping? (21_)." },

  { "id": "macos-sandbox-bookmarks",
    "trigger_keywords": ["sandbox","entitlement","security-scoped","bookmark","keychain","file access","hardened runtime","permission"],
    "injection_prompt": "Every user-chosen path outside the container needs a security-scoped bookmark with BALANCED start/stopAccessingSecurityScopedResource (22_). Keychain calls in a loop are slow — batch them (22_). Required entitlements present for hardened runtime?" },

  { "id": "appstorage-persistence",
    "trigger_keywords": ["@appstorage","userdefaults","\\bsettings\\b","persist","preference","migration","scenestorage"],
    "injection_prompt": "@AppStorage is VIEW-only — read from a service/model and you get the default, not the stored value (38_ P1). Many defaults → one service, not N duplicate @AppStorage (38_ P2). Migration path for existing users on a renamed/retyped key?" },

  { "id": "ship-notarization",
    "trigger_keywords": ["ship","release","distribute","notariz","staple","gatekeeper","developer id","\\bdmg\\b","codesign"],
    "injection_prompt": "Direct-distribution chain IN ORDER: sign (Developer ID) → notarize (notarytool, wait for verdict) → staple → verify Gatekeeper reads 'Notarized Developer ID' (61_). Skipping staple = fails offline. Hardened runtime + secure timestamp on the signature?" },

  { "id": "git-root-gitignore",
    "trigger_keywords": ["git init","\\.git\\b","new repo","clone","gitignore","first commit","\\bignore\\b"],
    "injection_prompt": ".git belongs at the PROJECT root, never inside 01_Project/ — clone-into-subfolder makes a nested repo (32_). Add .gitignore BEFORE the first stage so DerivedData/04_Exports/.DS_Store never enter history. Glob-anchoring + case-sensitivity traps checked? (32_)." },

  { "id": "web-css-token-cascade",
    "trigger_keywords": ["\\bcss\\b",":root","design token","dark mode","stylesheet","prefers-color-scheme","strato","lftp","deploy"],
    "injection_prompt": "A shared token file that redefines :root and loads LAST silently beats every earlier :root — override by specificity, not source order (#158). Remap tokens not components for dark mode (#62). Strato deploy: lftp mirror perms + .htaccess? (29_)." },

  { "id": "ui-placement-protocol",
    "trigger_keywords": ["add a button","add a toggle","add a menu","new control","where should","ui element","place the"],
    "injection_prompt": "UI-changes protocol BEFORE coding: found a similar existing control, traced its wiring, proposed exact file/line, waited for OK? (36_). Destructive/one-off controls go on the content body, not a toolbar item (#147, #153)." }
]
```

*This is a **seed**, not a spec — add a row the next time you catch Claude skipping the same thing
twice. The keyword regexes are deliberately loose; a false-positive costs one extra checklist line,
a false-negative costs the bug.*

## How to use it

1. **Manual (start here):** before a `/check`, `/spec`, or hand-off to a subagent, skim the table,
   paste the 2–3 matching `injection_prompt`s into the brief as *"also verify:"*. Zero infra.
2. **Scripted:** save the JSON + the 15-line matcher above; pipe your task text in, paste the output.
3. **Automated (only if it earns it):** wire the matcher as a `UserPromptSubmit` hook so a matching
   prompt auto-appends its checklist. Deferred on purpose — automate after the manual version proves
   it fires usefully more than it nags. See `27_mcp-gotchas`/`hooks/` for the hook plumbing.

## Why this beats octopus's version (for a solo Claude-only dev)

- **No external providers, keys, or per-Mac wiring** — the exact bloat/cross-Mac tax `37_` warns about.
- **One file**, not 52 commands + 58 hooks + a vendored 2,500-line consensus engine littered with
  bug-number patches (#1992/#2007/…). The maintenance surface is a JSON array you own.
- **Diversity from your OWN failures, not a rented model's** — multiple Claude personas share Claude's
  blind spots (octopus's own `debate.sh` says so); a curated checklist doesn't pretend to be a second
  brain, it's a *memory* of what this one forgets.

## Pairs with

- **`53_llm-failure-modes.md`** — the general theory this is the operational tool for.
- **`02_mental-model.md`** / **`/check`** — where the injected checklist does its work (review time).
- The cited docs: **20_** (SwiftUI), **21_** (coordinates), **22_** (macOS platform), **38_** (state),
  **61_** (notarization), **32_** (git), **36_** (UI changes), plus **#62/#158** (web tokens).
