# Focus-loss retry — September 9

**Result:** interrupted before input; focus-loss proof remains pending. The user explicitly asked
to resolve the marker and run again. One fresh window ran; no further retry followed.

## Reconciliation

Compared the original raw trace's SHA-256 and rows with the portable evidence. Required exactly
the recorded worker/sink launches, no bound/active/input/focus-injection records, worker stopped
with empty held keys, worker exit 0, sink exit -5, and failed client/supervisor outcome. Under an
exclusive nonblocking lock, verified private directory/file ownership, modes, no symlinks and no
remaining spike/recorded processes. Preserved an audit of the old unresolved marker before writing
`clean` and syncing. This reconciles that retained pre-input crash only, not general crash recovery.

## Retry evidence

- Corrected fresh artifact directory: `directions-stop-build.IdAV2D`. Worker preflight all true.
- Ran the actual client with `--case focus-loss` and that exact artifact directory.
- Worker PID 68422; sink PID 68423. Sink reached `ready`, confirming the singleton startup fix.
- Worker stopped on `unownedInput` approximately 0.47 seconds after launch, before sink readiness.
  The trace does not record the unowned event's type or origin; do not attribute it to user activity.
- No original text target launched; zero input events admitted/posted/received. No focus transfer.
- Worker reported held-keys-empty; both native children exited 0. Client/supervisor exited 2,
  `casePassed:false`. Final process scan empty, marker clean, screen control ended.
- A post-stop observation request reached the inactive sink before any activation and it closed
  with `invalidOrRepeatedCommand`, as designed. This secondary diagnostic did not cause the initial
  interruption and does not establish focus or drain evidence.
- [Portable retry trace, client evidence, artifact hashes and reconciliation audit](focus-loss-interrupted-2026-09-09.json).
  Trace directory `directions-stop-spike-q71q9vji`; client directory `directions-stop-client-myp16w7n`.

No source changes, TCC changes, installation, deployment or commits in this retry. Next: prepare
bounded input-origin diagnostics before another agreed focus-loss window, keeping physical-input
protection enabled. Task 1.3/Gate A, clipboard and broader recovery/intervention remain incomplete.
