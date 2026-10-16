# Global settings mirror — `CLAUDE-SETTINGS-TEMPLATE.json`

`~/.claude/settings.json` lives **outside** the repo and outside Syncthing, so it is the last piece
of the global config that never travels between Macs. `CLAUDE-GLOBAL-TEMPLATE.md` solved this for
`CLAUDE.md`; this file is the same idea for the settings **preferences**.

**Why it exists:** on 2026-07-28 two output-style plugins (`explanatory-output-style`,
`learning-output-style`) were found enabled together. They inject a system prompt that adds teaching
blocks to every reply and explicitly says *"you may exceed typical length constraints"* — which
silently overrode the length budgets written into the command specs (`/status` says "≤8 lines"). The
commands had been trimmed twice; the plugin above them undid it each session. Nothing in the repo
recorded the plugin set, so the fix would have been Mac-local and would have drifted straight back.

## What the template carries — and what it deliberately does not

| Key | Carried? | Why |
|---|---|---|
| `enabledPlugins` | ✅ | The actual bug above. A plugin set is a house decision, not a per-Mac one. |
| `extraKnownMarketplaces` | ✅ | Prerequisite for `enabledPlugins` — a plugin from an unknown marketplace can't resolve. |
| `effortLevel`, `alwaysThinkingEnabled` | ✅ | How hard every turn works. Should be identical on both Macs. |
| `autoCompactEnabled`, `tui`, `theme` | ✅ | Stable appearance/behaviour preferences. |
| `model` | ❌ | The `/model` picker **rewrites this key live** — it changed mid-session during the very session this file was written. Carrying it would let a redeploy flip the other Mac's model. |
| `permissions.allow` | 🔶 union-merge only | Grows organically per Mac as you approve tools, so the recursive merge above must never see it (jq `*` replaces arrays wholesale). Instead, **house rules** live in `CLAUDE-SETTINGS-PERMISSIONS.json` (a bare JSON array; `[HOME]` renders to the Mac's `$HOME`) and `redeploy.sh` step 2c **appends only the missing ones** — nothing is ever removed or reordered. Curated to read-only commands + the fixture-copy path the auto-mode classifier kept blocking mid-task (2026-07-29 usage report). |
| `hooks`, `statusLine` | ❌ | Owned by `hooks/install.sh`, which registers them idempotently and preserves non-Directions entries. Two writers on one key is how you get a fight. |

## Merge semantics

`redeploy.sh` step 2b merges the template into the live file with `jq`; it never overwrites the file
wholesale. Template values win for the keys it names; every other key in `settings.json` is left
untouched. `enabledPlugins` is a **deep** merge, so a plugin you're trialling on one Mac and which
the template says nothing about survives — but any plugin the template *does* name is forced to the
template's value. That is the point: an accidentally-enabled plugin gets switched back off.

The live file is backed up before any edit, and the result is validated as JSON.

## Updating it

After deliberately changing a preference, re-export from the live file:

```bash
cd <directions-master>
python3 - <<'PY'
import json, collections, os
live = json.load(open(os.path.expanduser('~/.claude/settings.json')), object_pairs_hook=collections.OrderedDict)
KEEP = ['effortLevel','alwaysThinkingEnabled','autoCompactEnabled','tui','theme',
        'extraKnownMarketplaces','enabledPlugins']
out = collections.OrderedDict((k, live[k]) for k in KEEP if k in live)
out['enabledPlugins'] = collections.OrderedDict(sorted(out['enabledPlugins'].items()))
json.dump(out, open('CLAUDE-SETTINGS-TEMPLATE.json','w'), indent=2)
open('CLAUDE-SETTINGS-TEMPLATE.json','a').write('\n')
PY
```

Then commit, and run `bash redeploy.sh` on the other Mac. **The repo is public** — keep this template
free of anything machine-identifying or secret. The excluded `permissions.allow` list is the most
likely place for a private path to hide, which is a second reason it stays out.

See `37_multi-mac-discipline.md`.
