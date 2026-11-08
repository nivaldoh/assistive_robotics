# Reproduction report

Executed locally on 2026-11-07 using the locked CPU Python environment.
The run solves 25 directions × three right DCE capacity conditions from
`ModelObjects.mat / gobj{2,2}`. No parameters were adjusted to match a plot.

| Direction (paper ID) | 0× (N) | 1× (N) | 2× (N) |
|---|---:|---:|---:|
| backLow (5) |169.712|236.815|242.395|
| back (6) |141.584|197.370|201.769|
| backHigh (7) |191.367|265.601|270.003|
| backLowL (9) |112.728|121.690|121.690|
| backLowR (12) |114.011|121.690|121.690|
| forehead (1) |60.840|60.840|60.840|

See [all forces](../results/figure2/forces.csv),
[static capacities](../results/figure2/directional_capacity.png),
[physical task](../results/figure2/selected_task.png), and
[offline explorer](../results/figure2/explorer.html).

## Verification and reference strength

All **75 LPs succeeded** with finite outputs and valid activation bounds.
Maximum absolute equilibrium residual was **1.78e-14 N·m**, and maximum
row-scaled residual was **6.19e-16**. All 25 directions had positive, bounded
capacity in all conditions. Monotonicity passed (largest negative increment
was 1.14e-13 N, numerical noise). No arbitrary force cap was used.

Ten tests cover analytical fixtures, unsupported and unbounded tasks, signs,
model identity, exact right-side membership, grouping equivalence, independent
supplement parameter checks, all 75 tasks, and an independently parameterized
per-newton solve with the HiGHS interior-point method. Synthetic fixtures are
confined to the tests. The numerical output retains raw activations; comparisons
do not require a unique activation vector.

The offline explorer opens with a four-step beginner tour: the physical test,
viewing planes, changing one muscle group, and reading a chart. The original
25-test explorer and research diagnostics are expandable. Static figures use
plain-language view names and facial landmarks; the task figure shows both
head-on-resistance and resistance-on-head force directions.

Rendered figures and browser screenshots were visually inspected. Chromium
checks exercised all four tour steps, three views, nine beginner comparisons,
all 75 direction/condition combinations, 24 activation bars per view, and
mouse/keyboard selection with retained focus. Displayed force values and the
embedded dataset match `run.json`. At 390- and 320-pixel widths there was no
horizontal overflow. No JavaScript errors or network requests occurred.
Evidence: `results/browser_verification.json`. Fresh official downloads and
extraction were previously verified in a separate temporary directory;
offline regeneration passed after the presentation changes.

**Quantitative source-parameter agreement:** all 96 strengths and 864 moment
arms match Supplement Table S2 within its rounding. Locations match the printed
table; forces and wrenches match its rounding. The exact supplied grouping
identity and the contact-to-wrench transformation also pass.

**Approximate output agreement:** 20 manually read 0×/1× markers across the
three panels of [Figure 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11132632/)
give **1.63 N RMSE** and **4.06 N maximum absolute difference**. Conservative
graphical uncertainty is **±8 N**, not a statistical confidence interval.
Pixel coordinates, circle calibration and method are in
`provenance/figure2_digitization.json`; each comparison is in `run.json`.
Overlapping 2× markers could not be independently resolved and were not
digitized. Baseline agreement and posterior reductions are visually consistent.
There are **no author-generated optimal-force arrays** in the supplied archive,
so this is not an exact numerical output comparison or an independent MATLAB run.

## Differences and limits

1. `KinModels.mat` has different lower-joint parameters; using it produced
   substantially smaller posterior capacities. The selected model object
   matches the supplement. Both original files remain unchanged and hashed.
2. The stored anatomical grouping puts splenius cervicis with levator scapulae,
   unlike Supplement Table S3. This implementation follows the actual supplied
   map. Group memberships are exposed; no silent anatomical correction is made.
3. Doubling right DCE produces **4.40, 4.40 and 5.58 N** gains in `backHigh`,
   `back`, and `backLow` (about 1.7–2.4%). This is a small departure from the
   paper's broad statement of no increase; it is within graphical resolution.
   We retain the computed gains rather than forcing exact plateaus.
4. Source plotting angles are unavailable. The plots use declared geometric
   projections with the same relevant contact sets; radial capacities are the
   reproduction target. No interpolation is treated as a new solved task.
5. No OpenSim mesh/model was bundled. Head/neck outlines are schematic, with
   actual supplied contacts and force directions. Generic model predictions
   do not estimate this user's anatomy, pain or treatment response.

The exact formulation, frame/sign conventions, source anomalies and exclusions
are documented in [source_mapping.md](source_mapping.md); model boundaries also
appear beside the explorer's diagnostics. Activations are one optimum at each
condition's own maximal force, rather than a matched-demand physiological claim.

## Re-run

`uv sync --locked && uv run neck-repro fetch`, then
`uv run --offline neck-repro reproduce` and `uv run pytest -q`.
The explorer is a self-contained HTML file; no server or network is needed to
use its plots, direction selector, activation bars or diagnostics.
