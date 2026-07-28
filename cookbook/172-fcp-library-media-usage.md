# 172 — Which media does a Final Cut Pro library actually use?

**Tags:** fcpbundle, fcpevent, Final Cut Pro, FCPX library, SQLite, Core Data, NSKeyedArchiver, bplist, plistlib, FFAsset, FFAssetRef, FFClipRef, FFMediaRep, FFAnchoredSequence, unused media, cull footage, media management, ZCOLLECTIONMD

**Extracted from:** MacroVision 1 footage cull (2026-07-28)

## What this is for

Answering "which of these 500 camera files can I delete?" against a `.fcpbundle` — without opening
Final Cut, and without trusting a single traversal for an irreversible decision.

## The format (none of this is guessable from the extension)

- **`CurrentVersion.fcpevent` is a SQLite database** (Core Data). `file` on it says so outright.
  Tables: `ZCOLLECTION` (one row per object, `ZTYPE` = the FCP class name), `ZCOLLECTIONMD`
  (metadata blobs), `Z_3CHILDCOLLECTIONS` (the parent→child object graph).
- The metadata is an **NSKeyedArchiver bplist** in `ZCOLLECTIONMD.ZDICTIONARYDATA`. `plistlib`
  reads it but hands back the raw `$objects` graph — you must resolve `plistlib.UID` refs and
  rebuild `NS.keys`/`NS.objects` pairs yourself.
- Open **read-only** so you can't lock or WAL-write someone's library:
  `sqlite3.connect(f'file:{path}?immutable=1', uri=True)`.

## The gotcha that makes a naive answer wrong

**The event-level `.fcpevent` is a stub.** Each project's real timeline lives in its own nested
`<Event>/<ProjectName>/CurrentVersion.fcpevent`. One library here had **115** of them, not the 5 the
top level suggests.

Reading only the event database reported **16** used assets across 128 projects instead of 76 — and
it *looked* like it worked. The tell: 110 of the event's 133 `FFClipRef`s pointed at IDs that
existed nowhere in the library. Grepping the raw bytes for one such ID found it in the project's
own database.

## Object model

| Link | How |
|---|---|
| asset ↔ file | `FFAsset.mediaIdentifier` (32-hex MD5) == `FFMediaRep.md5Seed` |
| file on disk | `FFMediaRep.projectRelativePath` → `<Event>/Original Media/<name>`, which is a **symlink** when media is referenced rather than copied — so `os.path.realpath()` is the mapping |
| clip → asset | `FFAssetRef.mediaIdentifier` |
| clip → clip | `FFClipRef.mediaIdentifier` → an `FFAnchoredSequence.mediaIdentifier` (22-char base64), **possibly in a different database** — compound clips live in their own event |

```python
def unarchive(blob):                      # NSKeyedArchiver bplist -> plain dict
    pl = plistlib.loads(blob); objs = pl['$objects']
    def res(v, d=0):
        if d > 8: return '<deep>'
        u = getattr(v, 'data', None)                    # plistlib.UID
        if u is not None: return res(objs[u], d + 1)
        if isinstance(v, dict):
            if 'NS.keys' in v:
                return dict(zip([res(k, d+1) for k in v['NS.keys']],
                                [res(x, d+1) for x in v['NS.objects']]))
            if 'NS.objects' in v: return [res(x, d+1) for x in v['NS.objects']]
            if '$classname' in v: return v['$classname']
            return {k: res(x, d+1) for k, x in v.items() if k != '$class'}
        return None if v == '$null' else v
    return {k: res(v) for k, v in pl['$top'].items()}

# walk: project sequence -> children -> FFClipRef hops across DBs -> collect FFAssetRef
def walk(db, pk, seen):
    t = G[db]['types'].get(pk)
    if t == 'FFAssetRef': return {G[db]['md'][pk]['mediaIdentifier']}
    if t == 'FFClipRef':
        tgt = seq_by_id.get(G[db]['md'][pk]['mediaIdentifier'])   # global: seqID -> (db, pk)
        return walk(*tgt[:2], seen) if tgt else set()
    return set().union(*(walk(db, c, seen) for c in G[db]['ch'].get(pk, [])), set())
```

## Cross-validate before deleting anything

FCP keeps its own registry: `FFMediaEventProject.referencedLibraryItemIDs` and the event's
`FFAssetRef` set. That's a completely different code path from the graph walk. Both gave 76.
For a 1.6 TB irreversible action, one traversal agreeing with itself is not evidence.

Then make the arithmetic close: `keep + cull + review == files on disk`, exactly, no overlaps.
That check caught 6 phantom entries a plausible-looking count would have hidden.

## Three classes of edge case, all of which bite

- **Broken symlinks** — the library links to media already deleted by an earlier cull. Don't leave
  them in a delete list as phantoms; and note one of ours was a *used* clip.
- **Name variants** (`_TC`, `_1`, `-00.00.00.000-…`) — `…6496.MOV` classified as "never imported"
  while the library used `…6496_TC.MOV`, which was offline. Same footage, renamed; deleting it
  would have destroyed 100+ GB that is in an edit. Emit a third **REVIEW** bucket rather than
  forcing keep/delete.
- **Case-insensitive filesystems** — FCP's symlinks are `.mov`, the camera writes `.MOV`. A
  case-sensitive set difference reported *every* file as unimported. Separately, `rm used.txt`
  silently deleted `USED.txt`; never let a generated filename differ from a temp file only by case.
