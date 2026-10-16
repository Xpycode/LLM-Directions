# E1 — host acceptance pending

October 16, 2026. Source implementation and local fixtures do not establish model behavior.
No matched before/after host benchmark has run. E1 remains unchecked and blocks overall acceptance
and a rollout recommendation, not the completed local tasks.

## Availability evidence

The installed CLIs report Codex 0.163.0 and Claude Code 2.1.301. Neither OPENAI_API_KEY nor
ANTHROPIC_API_KEY was present in the execution environment (values were not read or printed).
A bounded probe in a disposable empty directory used Claude `--bare -p` with no tools and
`--no-session-persistence --output-format json`. It exited 1 with **Not logged in**.
Bare mode skips normal hooks/plugins/memory and OAuth/keychain discovery; this finding applies
to that isolated profile only. It does not claim the user's normal Claude login is broken.
Codex's normal authentication was not copied or changed. The unavailable isolated Claude login
already prevents the required paired-host matrix. No live profiles, installations or desktop
state were changed. Authentication setup is required before proceeding with E1.

## Exact remaining work

1. Supply isolated authenticated Codex and Claude test environments; record host version,
   model and effort. Use the same settings for paired baseline/final runs. Freeze final source
   hashes again if anything changed since LE13.
2. Replay `scenarios.md` S01–S23 in root and docs layouts, including explicit scope/control limits,
   legacy migration, current handoff and missing backends. Stub unsafe historical app operations;
   fixture success never authorizes real control. Use isolated repositories/remotes for Git handoff.
3. Exercise all `routing-cases.json` domains and semantic command/safety cases, with globals and
   repository-only fallback, in Directions and the retained Magpie/App-Websites snapshots.
   Keep consumer originals unchanged; rehearse preservation-first cleanup on copies.
4. Perform three fresh runs per representative workflow per host. Record initial/retrieved
   files and bytes separately, tool calls, writes, unnecessary questions, repeated validation,
   outcomes and any lost constraints. Report descriptive medians/ranges only for actual runs.
5. Resolve standalone-entry and complex-path byte regressions recorded in integration.md,
   or obtain an explicit tradeoff decision before recommending rollout. Fresh-agent policy
   remains unchanged; no dispatch-efficiency improvement is proven.

AC04–AC09 and AC11–AC13 remain open. Local source walkthroughs and fixtures are linked in
integration.md; missing runtime metrics are unavailable, not zero. Global deployment,
consumer migration, publication and pushes remain separately scoped.
