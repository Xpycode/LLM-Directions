# Retained cross-project guidance — provenance review

October 17, 2026. Read-only inspection of existing project evidence; no app launch, live test,
registration, website transfer or remote profile change. This review qualifies shared guidance;
it does not rerun or close any project's acceptance. One serial owner reconciled source wording,
retained the incoming diff and computed receipts before checkpointing.

## Findings

| Directions source | Evidence and disposition |
|---|---|
| `20_swiftui-gotchas.md` | Penumbra repair README, runtime trace and red/green summaries support the native enabled-state overwrite, environment-based repair and mounted tests. Two tests/nine assertions failed before repair; 27 focused tests passed afterward. User acceptance is recorded in the README/session. Retained without changing this observation. |
| `22_macos-platform.md`: Reduce Motion | MousePlus September 13 session records user screenshots locating the setting under Accessibility → Motion on macOS 27. Retained as a dated observation, not today's UI verification. |
| `22_macos-platform.md`: helper registration | DiskVerdict September 12 corrects the previous day's `.notFound` diagnosis with captured `.requiresApproval`, a Code=1 error and successful operation after user approval. Removed the unproven pre-registration/XPC-persistence timing explanation, universal signing/process assertions and automatic live-reproduction recipe. Retained exact observed outcomes and added explicit authorization boundaries. |
| `29_web-strato-hosting.md` | App-Websites publication receipt records 27 equal-size cache-reference files explicitly uploaded after mirror skipped them, final HTTPS checks and PHP source readback. Official lftp manual distinguishes ignore-time from transfer-all. Retained the observation and linked that manual. |
| `44_my-glossary.md` | Penumbra October 12 session records Home/End scrolling without selection changes and accepted queue Up/Down navigation. Retained context-specific wording; removed an unnecessary exact keyboard-layout assertion. |
| `MACHINES.md` | ChargeMap location/destination evidence identifies M4 Pro, macOS 27.0 (26A5425a), Xcode 26.6 (17F113), isolated simulator results and device provisioning retry. Updated the previously unknown table fields as dated observations. XcodeGen 2.46.0 and the general sandbox diagnosis were not corroborated by the inspected task evidence; omitted from accepted inventory, preserved in incoming.patch. No current machine inspection claimed. |

## Local evidence inspected

Absolute paths allow inspection on this checkout's Mac; these sibling project files are not
copied into Directions or guaranteed to exist on another machine.

- `/Users/sim/ProgrammingProjects/1-macOS/Penumbra/docs/reviews/evidence/viewer-workflow-polish/apply-enabled-repair-2026-10-12/README.md`
- `/Users/sim/ProgrammingProjects/1-macOS/Penumbra/docs/reviews/evidence/viewer-workflow-polish/apply-enabled-repair-2026-10-12/diagnostic-trace.log`
- `/Users/sim/ProgrammingProjects/1-macOS/Penumbra/docs/reviews/evidence/viewer-workflow-polish/apply-enabled-repair-2026-10-12/red-test-summary.txt`
- `/Users/sim/ProgrammingProjects/1-macOS/Penumbra/docs/reviews/evidence/viewer-workflow-polish/apply-enabled-repair-2026-10-12/green-test-summary.txt`
- `/Users/sim/ProgrammingProjects/1-macOS/Penumbra/docs/sessions/2026-10-12.md`
- `/Users/sim/ProgrammingProjects/1-macOS/MousePlus/docs/sessions/2026-09-13.md`
- `/Users/sim/ProgrammingProjects/1-macOS/DiskVerdict/docs/sessions/2026-09-11.md`
- `/Users/sim/ProgrammingProjects/1-macOS/DiskVerdict/docs/sessions/2026-09-12.md`
- `/Users/sim/ProgrammingProjects/2-iOS/ChargeMap/docs/verification/location-destination.md`
- `/Users/sim/ProgrammingProjects/2-iOS/ChargeMap/docs/sessions/2026-09-11.md`
- `/Users/sim/ProgrammingProjects/3-Websites/App-Websites/docs/sessions/2026-10-15.md`
- `/Users/sim/ProgrammingProjects/3-Websites/App-Websites/docs/reviews/2026-10-15-site-consistency-publication.json`

Primary references inspected: [Use SwiftUI with AppKit](https://developer.apple.com/videos/play/wwdc2022/10075/),
[SMAppService](https://developer.apple.com/documentation/servicemanagement/smappservice?language=objc)
and [lftp manual](https://lftp.yar.ru/lftp-man.html). The specific application observations above
come from local records, not general vendor promises. Direct Apple enum-page Markdown retrieval
failed; no enum-specific guarantee is inferred from that attempt.

## Preservation and validation

[Incoming patch](incoming.patch) retains all five original uncommitted additions, including
wording narrowed during review. [Computed receipts](receipts.json) identify its bytes, the reviewed
source versions and the local evidence by executed SHA-256 and byte count. Historical lean
baseline/source receipts and replay outputs remain unchanged.

The integration byte guard now uses these explicit reviewed versions for the five intentionally
reviewed guides/profile; its original baseline remains frozen and the Mac-control plan remains
pinned to it. Other routing/reference assertions retain their previous contract. Check results
and the local commit are recorded in the current session handoff. No independent review claimed.
