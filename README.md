# Understanding a neck-strength model

This repo asks **how hard a modeled head can push against resistance while
staying still**, and how that changes when one neck muscle group becomes
unavailable or stronger. Biomechanics is the study of bodies using forces and
motion; no prior knowledge is needed to start here.

**Start with the [5-minute visual tour](results/figure2/explorer.html)**: open
the file in a browser. It works offline, with no setup or server. Four short
steps introduce the physical test, side/front/above views (including what
“sagittal” means), changing one muscle group, and reading one chart point.
The full explorer and research details are available below the tour.

For a written starting point, see the [first-session guide](docs/FIRST_SESSION.md).
Its longer activities are optional for later.

The calculation reproduces **Abbott et al. (2024), Figure 2**, using the authors'
supplied parameters: a neutral 3-joint / 9-DOF / 24-group model with right deep
cervical extensor (DCE) capacity at 0×, 1× and 2×. It runs locally on a CPU.

## Reproduce

From this directory, using Python 3.13 and [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked
uv run neck-repro fetch       # once; verifies and reuses cached originals
uv run neck-repro reproduce   # 75 LPs, figures, CSV, diagnostics and offline HTML
uv run pytest -q
uv run neck-repro explore     # opens the generated HTML in your browser
```

The isolated environment is `.venv`; exact dependencies are in `uv.lock`.
After the first setup/download, `uv run --offline neck-repro reproduce` needs no
network. The numerical experiment is also independently callable as
`neck_repro.experiment.run(Path('.'))`; plotting is a separate function.

In WSL, if automatic browser opening fails, run
`explorer.exe "$(wslpath -w results/figure2/explorer.html)"`, or open that file in
your Windows browser. No OpenSim, MATLAB, GPU, paid API or service is required.

## Inspect and resume

- [PROJECT_STATE.md](PROJECT_STATE.md): canonical current state and next action.
- [Reproduction report](docs/REPRODUCTION_REPORT.md): results, comparison strength, discrepancies.
- [Source mapping](docs/source_mapping.md): exact arrays, indices, transformations and model selection.
- [Provenance](provenance/manifest.json): URLs, version, licenses, checksums and retrieval date.
- [Force table](results/figure2/forces.csv), [static capacity figure](results/figure2/directional_capacity.png), [physical task](results/figure2/selected_task.png).
- `results/figure2/run.json`: configuration, hashes, versions, all activations and solver diagnostics.

All 75 tasks pass. The 20-point **approximate plot comparison** has 1.63 N RMSE
(estimated graphical uncertainty ±8 N). Author-generated force-output arrays
were not supplied. The repository documents conflicting source exports and a
grouping discrepancy; it preserves the supplied model object without tuning.

Original files are cached under `data/original/`, never edited, and excluded from
Git. Small derived outputs are retained for inspection without rerunning.
`fetch` retrieves the official v2 archive using curl and checks hashes before
loading. If access fails, open [dataset v2](https://data.mendeley.com/datasets/jm5dhwwmyd/2),
choose **Download All**, and save the ZIP as `data/original/jm5dhwwmyd-v2.zip`.
Re-run `uv run neck-repro fetch`; it extracts and verifies the files. For manual
extraction, put `readme.txt`, `classes/`, `data/` and `functions/` directly inside
`data/original/jm5dhwwmyd-v2/`. Required paper artifacts and their official URLs
are in the manifest.

Sources: [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11132632/),
[Rebecca Abbott's dataset v2](https://doi.org/10.17632/jm5dhwwmyd.2).
