# Project state

Current experiment: Abbott et al. (2024), Figure 2, neutral **3-joint / 9-DOF /
24 anatomical groups**, right DCE capacity **0× / 1× / 2×**. Dataset
**jm5dhwwmyd v2**, obtained 2026-11-07. The full requested computational slice is
implemented; no OpenSim/MATLAB installation is required.

Beginner entry point: `results/figure2/explorer.html` now opens with a four-step,
five-minute tour. It starts with a head pushing against a pad, then introduces
side/front/above views and their anatomical planes, the right DCE comparison,
and one highlighted chart point. Full results and technical detail are optional
expansions. The README and first-session guide lead here first.

## Verified

- Eight original dataset files downloaded via the official archive route,
  preserved unchanged and SHA-256 recorded; supplement and Figure 2 cached.
- Principal model decoded from `ModelObjects.mat / gobj{2,2}` with named MCOS
  metadata, exact group membership, and 25 named contact directions.
- All 96 capacities and 864 moment arms agree with the supplement's rounding;
  grouped torque-map identity and source wrench transform checked.
- All 75 optimizations succeeded; finite, positive bounded capacities, valid
  activations, small equilibrium residuals and capacity monotonicity.
- Ten meaningful tests passed, including analytical cases and a second
  per-newton LP formulation / solver method.
- Saved force table, run metadata, static figures, offline HTML, a five-minute
  introduction, and optional 45–90 minute activities with actual computed examples.
- Static figures use plain view names, facial landmarks and explicit force
  legends. The explorer has selectable opposing arrows, switchable views and
  plane diagrams, three beginner examples, and shared-scale force bars.
- Inspected rendered figures and browser screenshots; all four tour steps,
  three views, nine beginner comparisons, and all 75 detailed direction/condition
  combinations passed in Chromium. Mouse/keyboard selection retains focus.
  All displayed force values and embedded data match `run.json`. No JavaScript
  errors, network requests, or horizontal overflow at 390 or 320 px. Evidence:
  `results/browser_verification.json` (screenshots cached locally).
- Re-downloaded all required binary artifacts into a fresh temporary directory
  and verified extraction/checksums; locked setup and offline regeneration pass.

## Latest result

`results/figure2/run.json` is the complete run record. For direction 5,
`backLow`: **169.712 / 236.815 / 242.395 N**. For direction 9, `backLowL`:
**112.728 / 121.690 / 121.690 N**. Approximate Figure 2 digitization comparison:
20 markers, **1.63 N RMSE**, graphical uncertainty **±8 N**. No author-generated
optimal-force reference arrays were supplied; no claim of exact output agreement.

## Known differences / limits

No data-access blocker remains. `KinModels.mat` disagrees with the principal
object at the lower joint; the object matches the supplement. The supplied
anatomical grouping also differs from Table S3 for splenius cervicis; actual
stored grouping is retained. Three extension tasks gain 4–6 N when right DCE
is doubled, rather than the paper's broad description of no gain. Plot angles
are reconstructed from contact geometry because the plotting script is absent.
See `docs/source_mapping.md` and `docs/REPRODUCTION_REPORT.md` for evidence.

This environment has no registered desktop browser, so the `explore` command
prints the file path but cannot launch a GUI here. The report was exercised in
headless Chromium. Open the HTML in your normal browser; the README includes
the Windows/WSL command.

## Next concrete action

Open `results/figure2/explorer.html` in a browser and start with **Picture the
test**. Stop after any step; the full explorer and longer activities can wait.
To regenerate: `uv run --offline neck-repro reproduce`. To verify the science:
`uv run pytest -q`. To verify the tour (with Chromium installed):
`uv run --with playwright python scripts/check_explorer.py`.
To inspect mapping: `uv run neck-repro inspect`.

## Deferred

Thesis questions, individualized anatomy, devices, gravity compensation,
fatigue, pain, disc loading and dynamic models remain future work. An advisor
could help resolve source-export and grouping discrepancies before any extension.
