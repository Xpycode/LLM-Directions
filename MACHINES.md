# Machine Profiles

> **What this is:** the standing per-Mac capability registry — signing identities, tooling,
> OS/Xcode versions, and known permission blocks with their workarounds. Read the section for
> the Mac you are on (label = `~/.config/directions/this-mac`, with legacy
> `~/.claude/this-mac` fallback; one line, lives outside Syncthing) **before
> resuming machine-dependent work**: builds that need signing, UI automation, fixture capture.
>
> This is the *registry* companion to `37_multi-mac-discipline.md` Rule 2, which says to stamp
> per-doc `## Environment` blocks on spike journals. Those blocks record where one piece of work
> happened; this file records what each machine can *do*. Both exist because OS-level state —
> certs, installed tools, mounted volumes — is per-machine by default and Syncthing does not
> carry it.
>
> **Update discipline:** when a session discovers a new machine fact the hard way (a missing
> cert, an absent tool, a permission block), append it here in the same session — that is the
> entire point. Rot makes this file worse than useless. Stale-date check: each section carries
> a **Verified:** date; treat anything older than ~2 months as a hypothesis, not a fact.
>
> ⚠️ **This repo is public.** Machine facts only — no serial numbers, no personal names
> (identities are listed by type + team, not certificate CN), no secrets.

---

## M1 Max

**Verified:** 2026-07-29 · hostname `M1-Max`

| Fact | State |
|---|---|
| Hardware | MacBook Pro, Apple M1 Max |
| macOS | 27.0 beta (build 26A5388g) |
| Xcode | 26.6 (build 17F113) |
| Signing: Developer ID Application | ✅ present (team FDMSRXXN73) — Release/notarized builds work |
| Signing: Apple Development ("Mac Development") | ❌ **absent** — Debug builds needing a dev cert fail; use ad-hoc (`CODE_SIGN_IDENTITY="-"`) or `CODE_SIGNING_ALLOWED=NO`, don't stop |
| AppProbe (UI automation) | ❌ not installed (no app, nothing on PATH) — fall back to AX-by-name automation (never coordinate clicks; display scaling breaks them) |
| jq | ✅ (required by `hooks/install.sh` / `redeploy.sh`) |

**Known permission-classifier blocks on this Mac** (and the sanctioned way around them):
- Compound identity probes (`cat X; hostname; sysctl …`) get blocked — run the pieces as
  separate simple commands, or rely on the allowlist rules deployed from
  `CLAUDE-SETTINGS-PERMISSIONS.json` (see `redeploy.sh` step 2c).
- Fixture copies out of `~/ClaudeSessions/` used to be blocked mid-task (left 10/29 tests
  failing once) — now allow-listed via the same file.

## M4 Pro

**Verified:** *(never — fill in on that Mac)*

| Fact | State |
|---|---|
| Hardware | Mac mini(?), Apple M4 Pro |
| macOS | ? |
| Xcode | ? |
| Signing: Developer ID Application | ? |
| Signing: Apple Development ("Mac Development") | ? |
| AppProbe (UI automation) | ? (FSKit/system-extension spikes happened here — see `37` Rule 2 sources) |
| jq | ? |

**To fill this in:** on the M4 Pro, run each as its own command —
`security find-identity -v -p codesigning` (record *type + team only*, not the name),
`xcodebuild -version`, `sw_vers`, `ls /Applications/AppProbe.app`, `command -v jq` —
then update the table and the Verified date.

---

*Referenced from `~/.claude/CLAUDE.md` (multi-Mac pre-flight) and `37_multi-mac-discipline.md` Rule 2.*
