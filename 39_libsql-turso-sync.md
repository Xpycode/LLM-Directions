<!--
TRIGGERS: libsql, @libsql/client, turso, @tursodatabase/sync, db.push, db.sync, embedded replica, CDC, change data capture, "UNIQUE constraint failed", "no such column", DDL replication, sqlite3 DELETE, direct sqlite3 manipulation, schema migration remote, divergence local remote, libsql divergence
PHASE: implementation, debugging
LOAD: when working with @tursodatabase/sync embedded replicas, or before any DELETE/UPDATE on a Turso-backed local DB
-->

# libSQL / Turso Sync Discipline

*Two distinct rules with the same root cause: the sync layer is **opt-in** — it watches operations the libSQL client makes, and ignores everything else. Bypass it once, and your local replica silently diverges from remote until the next `db.push()` blows up.*

---

## The mental model

`@tursodatabase/sync` is **change-data-capture (CDC) at the client level.** When you write through `@libsql/client`, the sync layer records the operation and replays it remotely on `db.push()`. When you write through any other path — the `sqlite3` CLI, another process, a different SQLite library — the file changes but **the sync layer has no idea**.

Two consequences fall out of this:

1. **DDL isn't watched** even when issued through the sync client (CDC only replicates row-level changes, not schema).
2. **DML through any non-sync-aware tool is invisible** (raw `sqlite3`, GUI tools, file copies).

Both surface as runtime errors at `db.push()` time, never at the moment of the actual mistake — which makes them especially bitey.

---

## Rule 1: DDL never replicates — apply migrations to **both** sides

`@tursodatabase/sync` only replicates `INSERT`/`UPDATE`/`DELETE`. `ALTER TABLE`, `CREATE TABLE`, `CREATE INDEX`, etc. are silently dropped from the sync stream.

### Symptom

You add a column locally, run your app, and `db.push()` fails:

```
SQLITE_UNKNOWN: no such column: thumbnail_url
```

The local DB has the column. Remote doesn't. The sync engine tried to push a row with the new column, the remote DB had no place to put it, push aborted.

### The fix: a dedicated remote-migration helper

Ship a reusable script that uses `@libsql/client` (HTTP — not the embedded replica) to apply a SQL file directly against the remote URL. Reusable for every future migration.

`03_Scripts/migrate-remote.ts`:

```typescript
import { createClient } from "@libsql/client";
import { readFileSync } from "node:fs";

const file = process.argv[2];
if (!file) {
  console.error("usage: tsx migrate-remote.ts <path/to/NNN_name.sql>");
  process.exit(1);
}

const sql = readFileSync(file, "utf8");
const statements = sql.split(/;\s*$/m).map(s => s.trim()).filter(Boolean);

const db = createClient({
  url: process.env.TURSO_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

for (const stmt of statements) {
  await db.execute(stmt);
  console.log(`[migrate-remote] applied: ${stmt.slice(0, 60)}…`);
}
console.log(`[migrate-remote] done`);
```

`package.json`:

```json
{
  "scripts": {
    "migrate-remote": "tsx 03_Scripts/migrate-remote.ts"
  }
}
```

### The discipline

Every migration follows the same two-step routine:

```bash
# 1. Apply locally (sqlite3 is fine here — DDL doesn't need CDC)
sqlite3 04_Data/feed.db < 03_Scripts/migrations/008_feed_runs.sql

# 2. Apply remotely via the libSQL HTTP client
npm run migrate-remote -- 03_Scripts/migrations/008_feed_runs.sql
```

If you skip step 2, the next time the curator runs you'll hit "no such column" on push. Test by running both steps every time, even if you "just added an index."

Source: LEARNING `2026-05-01` (first hit, migration 002), `2026-05-02` (re-confirmed, migration 003), `2026-05-03` (006/007/008 batch — proven routine).

---

## Rule 2: DML against the local replica must go through `@libsql/client`

The whole point of `@tursodatabase/sync` is that it watches client operations to know what to push. Any DML that goes around the client is invisible to the sync layer and **never reaches remote**.

### Symptom

You clear out yesterday's test data with `sqlite3 04_Data/feed.db "DELETE FROM items WHERE curator_profile='rss'"`, then re-run your inserter. The local insert succeeds (25 rows). Push fails partway:

```
UNIQUE constraint failed: items.url
```

The first ~19 rows pushed fine. Then the collision: remote still has yesterday's `items` rows for the same URLs because the sqlite3 DELETE never propagated. New local rows have no remote conflict (you just inserted them); old remote rows are still there, blocking your "fresh" reinserts when their URLs match.

### The recovery recipe

When you've already created divergence and need to clean it up:

```typescript
// 03_Scripts/clean-remote.ts
import { createClient } from "@libsql/client";

const db = createClient({
  url: process.env.TURSO_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

await db.execute("DELETE FROM items WHERE curator_profile='rss'");
await db.execute("DELETE FROM feed_runs");
console.log("remote cleaned");
```

Run that against remote, then **re-clean local** through the sync client (or just re-run it through sqlite3 *and* through the same script — both must end up cleared), then re-run your inserter. Push will be clean.

The pattern mirrors `migrate-remote.ts` exactly — same `@libsql/client` HTTP connection, same direct execution, just different SQL.

### The discipline

| You want to… | Use |
|---|---|
| Read rows for diagnostic / debugging (SELECT) | `sqlite3 04_Data/feed.db` ✓ — read-only is safe |
| Inspect schema (`.schema`, `.tables`) | `sqlite3` ✓ — read-only |
| Insert / update / delete rows | `@libsql/client` from a script that uses your sync setup |
| Apply DDL | Both: `sqlite3` locally + `migrate-remote.ts` for remote (Rule 1) |
| Drop and recreate the local replica | Delete the file, let next sync rebuild from remote — **never** edit out chunks of the file via `sqlite3` |

Source: LEARNING `2026-05-05`. The lesson logged in that session: *"For DML against the curator DB, use `@libsql/client` directly (mirrors `migrate-remote.ts` pattern). Raw sqlite3 is fine for read-only diagnostic SELECT queries."*

---

## Detection: catch divergence before push

If you suspect divergence (after a tool crash, a sqlite3 mistake, a manual edit), don't push blind. Compare counts first:

```typescript
// Quick row-count diff
import { createClient } from "@libsql/client";

const local = createClient({ url: "file:04_Data/feed.db" });
const remote = createClient({
  url: process.env.TURSO_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

const tables = ["items", "feed_runs", "source_weights"];
for (const t of tables) {
  const l = (await local.execute(`SELECT COUNT(*) as n FROM ${t}`)).rows[0].n;
  const r = (await remote.execute(`SELECT COUNT(*) as n FROM ${t}`)).rows[0].n;
  console.log(`${t}: local=${l}  remote=${r}  ${l === r ? "✓" : "DRIFT"}`);
}
```

If any table shows DRIFT, decide: **does local or remote have the canonical state?** Then make the other side match by issuing the equivalent DML through the libSQL client against whichever side is wrong.

For LEARNING, the canonical answer is clear: **the curator runs locally and writes via the sync client, then `db.push()`**. So local is the writer, remote is the replica. If remote has rows local doesn't, those rows are stale (left over from a previous sqlite3 mistake) and remote should be cleaned to match local. If local has rows remote doesn't, local was probably mid-edit before push — finish the push.

---

## Quick-reference cheatsheet

| Symptom | Cause | First move |
|---|---|---|
| `db.push()` fails with `no such column: X` | DDL added locally, never applied remotely | `npm run migrate-remote -- NNN_X.sql` |
| `db.push()` fails with `UNIQUE constraint failed` | Local DELETE bypassed CDC; remote still has the rows | Recovery recipe — DELETE on remote via `@libsql/client`, then redo locally through sync client |
| Local row count ≠ remote row count, no recent push | Divergence from out-of-band write | Decide canonical side, make other side match through `@libsql/client` |
| Want to inspect data | Read-only operation | `sqlite3 04_Data/feed.db` is fine |
| Want to clear test data quickly | Tempted to use `sqlite3 DELETE` | **Don't** — write a 5-line `@libsql/client` script instead |
| New environment / fresh checkout | Local replica missing | First `db.sync()` rebuilds from remote |

---

## The cross-cutting rule

> **Sync is opt-in. The CDC layer only sees what `@libsql/client` does.** Anything else — raw `sqlite3`, another process, file copies, GUI tools — is invisible to the sync engine and creates silent divergence that surfaces minutes or hours later as a `db.push()` error.

If you're tempted to reach for `sqlite3` to "just quickly delete some test rows," stop. Write the 5-line `@libsql/client` script. Reuse it next time. The 30 seconds saved by `sqlite3 DELETE` becomes 30 minutes of recovery when push fails halfway and you have to figure out which side has what.

---

*Related: `30_production-checklist.md` (pre-deploy data integrity), `31_debugging.md` (incident-response patterns), `54_security-rules.md` (auth tokens for Turso URLs in env, never in repo).*
