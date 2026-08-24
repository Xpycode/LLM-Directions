# 169 — `mirror -R` clobbers server-written state with local seeds

**Tags:** lftp, mirror, deploy, rsync, sftp, feedback, counts.json, submissions.log, data loss, server-managed state, exclude, seed file, check-invariants

**Extracted from:** App-Websites (2026-07-27) — third occurrence of the same class

## The problem

`lftp mirror -R` (and `rsync` without `--exclude`) uploads a **directory**, not a file list. Any
file the *server* writes that happens to live inside that directory gets overwritten by whatever
local copy exists at the same path.

The local copy is almost always an **empty seed** — the placeholder committed so the feature works
on a fresh deploy. So the failure looks like this:

```
local  data/counts.json          20 B   {"downloads":0}
live   data/counts.json         4.1 KB  {"downloads":3847,...}
deploy →  live becomes 20 B. Counter reset. No error, no warning.
```

Nothing fails loudly. The deploy reports success. You find out when someone asks where the feedback
went.

## Why it keeps recurring

Each occurrence looks site-specific, so it gets fixed site-locally and the class survives:

| When | Symptom | Fix applied |
|---|---|---|
| 1st | `mirror` removes-then-transfers → sub-second 404s | `xfer:use-temp-file` atomic swap |
| 2nd | one site's download counter resettable | `--exclude-glob 'counts.json'` on that site |
| 3rd | two more sites overwriting feedback + counts | exclusions added to both |

The trap: **you cannot hoist the exclusion into the shared deploy library.** Other sites legitimately
publish files with the same names via the mirror — a shared `--exclude '*.dmg'` would silently stop
those sites releasing. The exclusion is genuinely per-site, which is exactly why it gets forgotten.

## The rule

> Any file written by server-side code — counters, logs, submissions, uploads, generated caches —
> must be **excluded from the mirror**, per site, and the exclusion needs a comment saying why.

```bash
# Server-managed state — NEVER overwrite on deploy:
#   data/private/submissions.log → written by api/feedback.php
#   data/counts.json             → download tallies written server-side
# Local copies are empty seeds (0 B / 20 B). Without these excludes every deploy
# wipes live data. FIRST deploy to an empty server dir: comment them out once so
# the seeds upload, then restore them.
deploy_mirror "${SITE_DIR}/public" "SITE" \
  --exclude data/counts.json \
  --exclude data/private/submissions.log
```

Note the first-deploy caveat in the comment — without it, someone bootstrapping a new site finds the
feature broken because the seed never uploaded, and "fixes" it by deleting the exclusions.

## The guard that actually stops recurrence

Site-local fixes don't prevent the next site. A repo-wide invariant does — fail the check when a
site *has* server-written files but its deploy call doesn't exclude them:

```bash
# check-invariants.sh — server-state exclusion guard
fail=0
for site in APPS/*/; do
  deploy="$site/deploy.sh"; [ -f "$deploy" ] || continue
  # any file the server writes, by convention
  while IFS= read -r f; do
    rel="${f#"$site"*/}"                       # path as the mirror sees it
    base="$(basename "$f")"
    if ! grep -q -- "--exclude.*$base" "$deploy"; then
      echo "FAIL: $site — '$rel' is server-written but not excluded in deploy.sh"
      fail=1
    fi
  done < <(find "$site" \( -name counts.json -o -name submissions.log \
                        -o -name 'public.json' \) -not -path '*/node_modules/*')
done
[ "$fail" -eq 0 ] && echo "PASS: server-state exclusions"
exit "$fail"
```

Convention-based (it keys off known filenames), so adding a new kind of server-written file means
adding it to the `find`. That's the maintenance cost of catching the class instead of the instance.

## Checklist for any new mirrored site

- [ ] List every path server-side code writes to. Grep for `file_put_contents`, `fopen(...'a')`,
      `>>`, and any DB/JSON write in the deployed tree.
- [ ] Confirm each is either **outside** the mirror root or **excluded**.
- [ ] Confirm the local copy is a seed, not real data pulled down for inspection.
- [ ] Add the exclusion **with a comment naming the writer**.
- [ ] Run the deploy in dry-run mode and read the file list before the first real push.

## Related

- The deploy root question is upstream of this: see the multisite lftp/netrc deploy pattern for how
  the upload root is chosen and why `.git`/docs must sit outside it.
- **#179** — the security-shaped exception to *how* you write the exclusion: if the excluded
  directory contains the `.htaccess` that denies access to it, excluding the container silently
  ships an unprotected site. Exclude the contents, not the container.
