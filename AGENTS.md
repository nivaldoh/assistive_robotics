# Repository Guidelines

## Project Structure & Module Organization

- `src/neck_repro/`: `sources.py` fetches and verifies inputs; `model.py` loads anatomy; `solver.py` solves force limits; `experiment.py` runs the experiment; `plotting.py` generates figures and HTML; `cli.py` exposes commands.
- `src/neck_repro/explorer.html`: editable offline explorer template. Regenerate its counterpart in `results/figure2/` rather than editing generated HTML.
- `tests/test_science.py`: numerical tests. `scripts/check_explorer.py`: browser audit.
- `configs/figure2.json`: experiment configuration. `provenance/`: source records and plot comparisons. `data/original/`: ignored source cache.
- `docs/`, `README.md`, and `PROJECT_STATE.md`: explanations, reproduction evidence, and current status. `results/figure2/`: generated figures, CSV, and run metadata.

## Build, Test, and Development Commands

Run from the repository root with Python 3.13 and `uv`:

- `uv sync --locked`: install locked dependencies into `.venv`.
- `uv run neck-repro fetch`: download and verify original artifacts; requires network access and curl.
- `uv run --offline neck-repro reproduce`: solve all 75 tasks and regenerate outputs after setup/download.
- `uv run pytest -q`: run scientific tests using cached sources.
- `uv run neck-repro explore`: open the generated explorer; open the printed HTML path manually if browser launching fails.
- `uv run neck-repro inspect`: inspect model/source mapping diagnostics.
- `uv build`: build the Python package using Hatchling.

For explorer changes, install Chromium once with `uv run --with playwright playwright install chromium`, then run `uv run --with playwright python scripts/check_explorer.py`.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions/modules, `PascalCase` classes, and uppercase constants. Preserve explicit physical units and frame/sign conventions. Keep numerical calculations separate from presentation. No formatter or linter is configured; match surrounding style. Keep the explorer self-contained and usable offline, with plain-language labels and optional technical detail.

## Testing Guidelines

Use pytest and `test_*.py` files with `test_*` functions. Cover analytical cases, equilibrium, capacity bounds, and source consistency for numerical changes. Browser checks validate saved values, controls, keyboard navigation, and mobile layouts. Inspect regenerated visuals. No percentage coverage threshold is configured.

## Commit & Pull Request Guidelines

There are currently no commits, so no historical convention exists. Use concise imperative subjects, such as `Clarify force arrow labels`. PRs should describe purpose, affected outputs, verification commands/results, and relevant issues. Include screenshots for visual changes and explain numerical differences.

## Reproducibility

Never edit cached originals or tune parameters merely to match a plot. Preserve provenance and checksums, regenerate affected outputs, and document changed assumptions or limitations.
