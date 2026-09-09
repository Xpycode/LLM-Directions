# Native context visibility and legacy marker baseline

September 9, 2026 · M1-Max.local · arm64 · macOS27.0 (26A5425a) · Python3.14.7.

**Native read-only visibility passed outside the Codex shell sandbox.** The first bounded probe
inside the sandbox returned unresolved in90.47575ms. The same probe with approved outside-sandbox
execution returned complete, empty managed-executor inventory in158.812542ms. This verifies the
actual installed Darwin enumeration/context API path; it does not establish input recovery.

A second read-only operation acquired the existing historical marker using
`MarkerLock.acquire(root)` with its default `create=False`. It retained that ownership while taking
two fresh `capture_bounded_context(clock=mac_clock())` samples, then rechecked owner and marker bytes.
Both samples agreed on boot and security session and reported complete empty executor inventories.
Their combined duration was305.131667ms. All helper processes completed through the wrapper's owned
exit checks. No native GUI app was launched and no event was posted.

The marker remains the ten-byte legacy value `unresolved`, unchanged before/after the locked scan.
Its SHA-256 is `27a888c9d5e6c6c2d1530d15680651f4eefc9a98aaba319953362e3cf5a24996`.
Exact boot/session IDs, continuous-clock readings, environment and marker namespace are retained
in [the prospective baseline](native-context-2026-09-09.json). This observation is dated after the
historical failure; it does not retrofit boot/run identity into that failure's missing ledger.

A final locked check completed the baseline metadata: two fresh agreeing native samples bracketed
the marker read; directory and marker fingerprints (device/inode, mode, ownership, link count,
size and modification/change times) remained identical. Those exact stamps and samples are also
retained in the JSON. This additional check used `fingerprint(root.stat())` and
`fingerprint((root / 'lock').stat())` before and after, under the same live owner.

## Invocation and assertions

From the repository root, `python3 -B` imported `tools/mac-control/Spikes` and ran:

```python
clock = mac_clock()
root = (Path(os.confstr(65537)) / 'directions-stop-spike').resolve(strict=True)
owner = MarkerLock.acquire(root)
try:
    before = owner.read_marker(139)
    start = clock()
    first = capture_bounded_context(clock=clock)
    second = capture_bounded_context(clock=clock)
    owner.recheck()
    after = owner.read_marker(139)
    assert before == after == b'unresolved'
    assert (first['boot'], first['session']) == (second['boot'], second['session'])
    assert start <= first['checked_ns'] <= second['checked_ns'] <= clock()
finally:
    owner.close()
```

The probe itself requires complete empty inventory and bounds output/exit. No marker write,
creation, clear, repair or signal to an enumerated process occurred. Prior offline validation
remains243 passing tests and one sandbox-dependent skip; the suite was not rerun for these reports.

## Recovery decision and next task

Keep the historical marker unresolved. Empty inventory alone does not settle old event uncertainty.
The current verifier correctly refuses a legacy marker without a run record, including its new-boot
branch. Protocol bootstrap is a separate procedure requiring actual login/boot freshness evidence.

The [legacy bootstrap review](legacy-bootstrap-review.md) specifies the next bounded preparation:
implement and test that separate verification/initialization transaction offline, preserving this
prospective baseline. A later independently verified different boot can provide freshness evidence;
today's current UUID alone cannot. No reboot or marker mutation is requested by this preflight.
Swift checkpoint compilation and a new crash experiment still need their prepared, agreed window.
Task1.3/Gate A, broker-death recovery, clipboard and broader intervention proof remain open.
