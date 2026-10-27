# App handoff and outstanding recovery

Apply when this session produced a runnable build, launched an app, or has an unresolved app/test
recovery obligation. Otherwise skip. A successful build requires a handoff; it grants no control.

**Standing fresh-build handoff authorization — October 27, 2026:** the user approved gracefully
quitting only the target app, launching its successful fresh build, and verifying the running
version, stopping if the app is busy, refuses to quit, or asks about unsaved work. This extends
the October 18 launch permission; do not ask again for actions already inside this scope.
After a successful runnable build for user testing, identify the exact artifact and any existing
target instance. If replacement is needed, request normal quit only for that identified instance,
confirm exit, then launch the exact fresh artifact. Stop on active work (such as an export), a
quit refusal/timeout or save prompt; never force quit, discard work, or answer the prompt.
Verify the running executable path and version against the fresh artifact and report the actual
result; an open command succeeding alone does not prove the new version is running.
This permission excludes failed/intermediate test builds, app-hosted tests, installation,
unrelated apps, simulated input, window/Space manipulation, clipboard and live-profile changes.
Newer no-control or keep-running instructions override it. It does not reopen deferred recovery
or test scopes. Decision: [standing build handoff](../../decisions.md#2026-10-27---authorize-graceful-fresh-build-handoff).

**Current explicit user scope governs every action.** A newer no-control restriction overrides
older automatic quit/relaunch preferences. Without explicit permission for the specific target and
actions, do not launch, quit, kill or relaunch apps, manipulate windows/Spaces, simulate input, or
replace the clipboard or a live app profile. This includes indirect control through app-hosted
tests, scripts or helpers. A timer expiring, a successful check, a log request or a Mac handoff
never creates or extends permission. An explicit keep-running instruction prevents cleanup of
that app; retain its identity and the instruction in the handoff.

Read-only identification remains available: match executable paths and session-owned process
evidence to the exact app/build before proposing cleanup. A path-pattern match is only a candidate,
not permission to terminate it. Do not act on unrelated processes or infer ownership from a shell
wrapper that mentions the app path.

```bash
# Match the EXECUTABLE path (ps comm), never the command line.
ps -Ao pid,comm | grep -E "(DerivedData|\.build)/.*\.app/Contents/MacOS/"
```

⚠️ **Do not use `ps -Ao pid,command` here.** It matches any process whose *command line* merely
mentions those paths — including the grep itself and the shell wrapper running it — so it reports a
stray build on a clean machine. That false positive fired the first time this step ran (2026-08-06);
`comm` is the executable path, so wrappers can't match it. And since this check normally passes,
**prove it can fail** before trusting a clean result — pipe a fake DerivedData path through the same
grep and confirm it fires ([[negative-checks-pass-vacuously]]).

When control is explicitly authorized, perform only the agreed actions on the agreed target and
Mac within the agreed scope. Prefer graceful termination so pending saves can finish; never bypass
a save prompt or discard unsaved work. Confirm the old instance exited before an authorized
replacement launch, then verify the running executable path against the exact artifact. Permission
to quit a test build does not imply permission to launch the installed app. Report only verified
actions and results. If scope expires or is withdrawn, stop control; recovery needs authority that
still covers that exact recovery action. An unresolved obligation is not permission to perform it.

For every successful runnable build, give the **full absolute containing-folder path** as visible,
copyable text for Finder's Go to Folder, plus the exact artifact name and validation result. For
example: folder `/Users/sim/Builds/Example/Release`, app `Example.app` (illustrative paths only;
substitute the verified build location). When current scope excludes the standing handoff, provide user-operated launch/quit
steps and say that the build was not launched. Never substitute a relative path, `~`, or a hidden
link target for the visible absolute folder path.

Record unresolved cleanup/recovery in the session handoff even in plain mode: originating Mac,
exact app/build and owned process identity if known, affected data/profile/clipboard state,
original state or backup, original authorization and current limit/expiry, intended restoration
steps, evidence of what actually happened,
and the next permitted or user-operated step. Preserve this obligation across clear/Mac handoff;
do not claim restoration or a safe Mac switch while it remains unverified. Another Mac cannot
satisfy an original-Mac recovery obligation merely by receiving the log.

*Why this step exists:* an Aloft Debug build outlived its session by nine days, kept the
Command+Shift+V hotkey, and broke auto-paste system-wide while reporting every paste as successful
(2026-08-06). Nothing in git or the working tree can show you this — only `ps` can.


For test recovery, apply the recovery contract in `<master>/34_testing.md`. Return to the
calling logging core after recording the obligation; missing control permission does not block
authorized logging.
