# 157 — Faceted attribute filter (OR within a facet, AND across facets)

**Tags:** faceted filter, faceted search, attribute filter, multi-select filter, filter chips, OR within AND across, facet predicate, tag filter, Svelte, SvelteKit, URL filter param, checkbox filter

**Extracted from:** KinoBerlin (2026-07-05)

## Problem

You have items tagged with a flat list of attributes (`ov`, `omu`, `3d`, `imax`, `atmos`, …) and
a row of toggle pills. The naive predicate combines every selected pill with a single boolean:

```js
// flat OR — a screening passes if it has ANY selected attribute
const passes = active.size === 0 || item.attrs.some(a => active.has(a));
```

Both flat choices are wrong, in opposite ways:

- **Flat OR** makes selections a *union*. Selecting `OV + Atmos` shows *all* OV screenings **plus**
  *all* Atmos screenings. The tell-tale symptom: **removing** a pill makes the list *shrink*
  (deselect OV and you drop from the OV∪Atmos union to the Atmos subset) — the opposite of what a
  user expects when they loosen a filter.
- **Flat AND** makes it an *intersection across everything*, which breaks same-kind selection:
  `OV + OmU` (two language variants) becomes "OV **and** OmU" = ∅, because no single screening is
  both.

## The gotcha / why

The attributes aren't one flat set — they're **facets** (categories). Users intuitively want
**OR within a facet** ("either kind of original language") but **AND across facets** ("an original
screening that is *also* Atmos"). Neither a single `.some()` nor a single `.every()` expresses that.

## Solution

Group the attributes into facets, then loop the facets: a facet **only constrains** the result if
the user selected at least one pill in it, and when it does, the item must match at least one of
that facet's selected pills. Untouched facets never narrow the list; empty selection passes
everything. "OR-within / AND-across" falls out of the one loop — no special-casing.

```js
// Facets: OR within each array, AND across arrays.
const FACETS = [
  ['ov', 'omu', 'omeu', 'df'], // language / version
  ['3d', 'imax'],              // projection format
  ['atmos'],                   // sound
  ['hfr'],                     // frame rate
];

function passesFilter(item, active /* Set of selected attrs */) {
  if (active.size === 0) return true;              // nothing selected → all pass
  const attrs = new Set(item.attributes);
  for (const facet of FACETS) {
    const selected = facet.filter(a => active.has(a));
    // facet touched but item matches none of ITS selected pills → reject
    if (selected.length > 0 && !selected.some(a => attrs.has(a))) return false;
  }
  return true;                                     // survived every touched facet
}
```

## Verify (the three cases that prove it)

Diff the counts old-vs-new on real data — correctness lives in the cross-facet cases:

- **`OV + OmU`** (same facet) → **unchanged** vs flat-OR (still a union — OR preserved).
- **`OV + Atmos`** (cross facet) → the **intersection**, not the union (often far smaller; may be 0).
- **`Atmos` alone** ≥ **`OV + Atmos`** → loosening a filter now *grows* the list. This is the
  regression the flat-OR version failed.

## Notes

- Put `active` in the URL (`?filter=ov,atmos`) so filters are shareable/bookmarkable; derive the
  `Set` from the query param.
- The facet map is the only editorial decision — where each attribute belongs. Keep it beside the
  master attribute list so they don't drift.
- Pure function of `(item, active)` → trivially unit-testable and framework-agnostic (the snippet is
  plain JS; the Svelte/React wrapper just supplies `active` and renders the survivors).
