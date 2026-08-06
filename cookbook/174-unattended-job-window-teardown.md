# 174 — Unattended-job UI: every terminal state must schedule its own teardown

**Tags:** launchd, StartInterval, single instance, LaunchAgent, cron, Tkinter, mainloop, tkinter destroy, root.after, progress window, unattended job, scheduled task, watchdog, wedged process, launchctl list, silent failure, TclError

**Extracted from:** KinoBerlin (2026-08-06)

## The problem

A scheduled job (launchd `StartInterval`, cron, Task Scheduler) shows a GUI progress window. The
window runs on the **main thread**; the work runs on a worker thread. Success closes the window.
**Failure shows an error and waits to be dismissed** — which feels right, and is catastrophic.

**launchd will not start a second instance of a job whose previous instance is still running.**
So the window that is politely waiting for a human *is* the job, still "running". Every subsequent
tick is suppressed. In the real case: one failed deploy → **8 days of zero runs**, discovered only
when a human happened to look at the screen.

What makes it vicious is the **absence of symptoms**. The failure emits nothing:

- no repeating error — the run failed once, 8 days ago
- no growing log — nothing is executing
- no held lockfile — the app's own lock had been released
- the app's *own* recovery machinery (stale-lock breaking, retry-on-next-tick) never fires, because
  the scheduler never invokes it again

It is indistinguishable from a machine with nothing to do. Any self-healing you built lives one
level *below* the thing that broke.

## Diagnosis

Don't ask "is it broken?" — ask the scheduler whether it thinks the job is still running:

```bash
launchctl list | grep <label>
#  PID  Status  Label
#  76969  0  de.kinob.scraper   <- a PID in column 1 = still "running" = wedged
#  -      0  de.kinob.scraper   <- healthy: not running, last exit 0
```

Then read the **last scheduler-side log line**, not the app's log:

```bash
grep '\[guard\]' ~/Library/Logs/<App>/launchd.log | tail -3
```

A last line days old, with no "skipping" entries after it, is the signature. Confirm with
`ps -o lstart,etime -p <PID>`.

## The fix

Two layers. The first fixes the bug; the second makes the whole class impossible.

```python
ERROR_LINGER_MS = 30_000                  # readable if you're there, always exits if not
MAX_LIFETIME_MS = 6 * 60 * 60 * 1000      # ~16x a normal run

class ProgressWindow:
    def __init__(self, ...):
        self.closing = False
        ...
        self.root.after(MAX_LIFETIME_MS, self._watchdog)   # layer 2: caps ANY state

    def _apply(self, msg):
        if msg["type"] == "done":
            self.root.after(2500, self._close)
        elif msg["type"] == "error":
            self.phase_var.set("Error")
            self.detail_var.set(msg.get("message", "see logs"))
            self.root.after(ERROR_LINGER_MS, self._close)  # layer 1: the missing line

    def _close(self):
        """Idempotent: the watchdog can race a pending close, and a second
        destroy() raises TclError — turning a clean failure exit into a crash."""
        if self.closing:
            return
        self.closing = True
        try:
            self.root.destroy()
        except tk.TclError:
            pass
```

**Sizing the watchdog:** measure real runs from your own logs (here: 14–23 min; the only longer ones
had straddled a sleep and failed anyway). Its job is preventing an *indefinite* wedge, not policing
slow runs. Cost of aborting a genuine long run = **one tick**; cost of a wedge = **every tick**.
Note Tk/most timers hold **absolute** deadlines, so sleeping past the cap fires it on wake — usually
exactly the run you want killed, since a job resuming after wake often finds the network still down.

## Test the observable behaviour, not the diff

Asserting "`root.after` appears in the error branch" proves nothing. Assert that **`mainloop()`
returns**:

```python
q.put({"type": "error", "message": "deploy failed (exit 1)"})
win = ProgressWindow(q)
t0 = time.monotonic()
win.run()                       # before the fix: never returns
assert win.closing and time.monotonic() - t0 < 10
```

## Generalizes to

Any UI state reachable by an unattended process: modal alerts, "press any key to continue", an
`input()` on a failure path, `git`/`ssh` prompting for credentials, a debugger breakpoint, a crash
dialog. **If a scheduled job can reach it, it must time out.**

Related: log the failure somewhere durable *before* showing it. A window on one screen is not a
record — and if the cause was a network outage, your remote alerting died with it.
