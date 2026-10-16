# Test App — scoped app verification

Prepare and, within existing authorization, run a finite test batch for the named app. Read the
master `34_testing.md` execution-effects, isolation, results and acceptance contract before running.

## 1. Identify the app and test boundary

Use the argument and project context to identify the app, bundle identifier, absolute source path,
scheme and exact artifact. Ask only if the target is ambiguous. Read relevant source, startup,
scheme/test-host settings, scripts and setup/teardown before choosing tests. Classify each command
as headless, app-hosted or interactive; record its data namespace, startup behavior, required
authorization, owned process and result source. Unknown effects must be inspected first.

No-control scope excludes indirect launches through `xcodebuild test`, app-hosted tests, discovery
or build hooks. Use an available inspected headless subset and report remaining gates. A successful
build is not launch permission. For a user-operated handoff show the real full absolute containing
folder path as copyable text and name the app to open there; never launch, quit or relaunch it by
default. Respect newer user restrictions and a keep-running exception.

## 2. Establish an available backend

Inspect project instructions and local files/tool inventory for AppProbe or another supported
backend. Verify its actual path/version and documented CLI/schema; inspect unknown startup effects
before even running a check/discovery command. Do not presume a particular AppProbe checkout,
hardcode an unverified invocation, or claim optional tooling is present.

If AppProbe is missing, use an actually available documented alternative within the same scope, or
prepare manual steps. Record the missing backend and which automated cases cannot run. This is not
authorization to install software or substitute a desktop-control tool. Discover an accessibility
tree only with an available backend whose effects fit authorization; source inspection and a manual
plan remain possible without it.

## 3. Prepare one finite batch

Derive cases from requested behavior and integrated implementation: the primary journey, relevant
menus/windows and error paths. Do not automatically expand a focused check to every UI element.
Reuse valid evidence and state why any repeated case is necessary.

For each case specify ID, setup/data, action, expected result and evidence. Include source and
artifact identity, backend/version, exact command and working directory, results/log paths, owned
process tracking, timeout/completion conditions and remaining manual gates. Verify expectations
through the same entry point the user uses. Label service-only coverage accordingly.

Use disposable namespaces across all layers and isolate startup from production sync/updaters,
defaults, Keychain and support data. For unavoidable live changes, prepare the authorized ending
and recovery plan described in `34_testing.md`, attached to the originating Mac. Cleanup is part
of scope, not blanket permission to close windows, delete support data or terminate apps.

Save the plan/evidence in the project's established test location with unique run outputs, using
the installed backend's verified schema. Present test count, effects, command and ending behavior.
Existing explicit authorization for these exact actions is sufficient; do not ask again. If control
permission is missing, finish the reviewable plan and safe checks first, then request only the
specific missing scope or deliver the user-operated batch. Time elapsed is never permission.

## 4. Execute and report honestly

Run only authorized cases. Preserve raw progress logs and structured results, the producer's real
exit code (not just a successful formatter), and actual owned-process identity. Wait for completion
and required teardown; a timeout, orphan child or missing result cannot pass. Keep project-specific
safe serial commands local. Diagnose harness/query/environment faults before changing product code.

Report passed/failed/blocked/not-run cases, evidence provenance, failure screenshots if available,
and limits. Give one finite remaining user acceptance batch with integrated expected behavior and
a completion condition. A repeat requires a concrete reason; preserve valid earlier evidence.
Keep unresolved recovery in the current handoff: originating Mac, exact target and state, authorized
scope/expiry, recovery steps and evidence still needed. If scope expired, do not infer authority to
restore state on either Mac; arrange authorized or user-operated recovery and leave it open.
