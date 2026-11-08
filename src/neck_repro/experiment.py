"""Numerical experiment independent of figures or browser code."""
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import csv
import json
import platform

import numpy as np

from .model import COORDINATES, load_model, plane_views
from .solver import solve_direction, validate_solution
from .sources import digest, verify_sources


def jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, default=jsonable, indent=2, allow_nan=False) + "\n")


def run(root, config_path="configs/figure2.json"):
    root = Path(root)
    config = json.loads((root / config_path).read_text())
    if config["capacity_multipliers"] != [0, 1, 2] or config["affected_group"] != "DCE_R":
        raise ValueError("This reproduction is scoped to right DCE 0x, 1x, 2x")
    verify_sources(root)
    model = load_model(root, config)
    p, d = model.parameters, model.directions
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": config, "configuration_path": config_path,
        "model_identity": {"name": p["model_name"], "grouping": p["description"],
                           "coordinates": COORDINATES, "group_names": p["group_names"],
                           "group_elements": p["mm_groups"], "neutral_posture": True},
        "source_audit": model.source_audit,
        "source_hashes": {str(q.relative_to(root)): digest(q)
                          for q in sorted((root / "data/original/jm5dhwwmyd-v2").rglob("*")) if q.is_file()},
        "implementation_hashes": {str(q.relative_to(root)): digest(q)
                                  for q in sorted((root / "src/neck_repro").glob("*")) if q.is_file()},
        "environment": {"python": platform.python_version(),
                        **{name: version(name) for name in ("neck-repro", "numpy", "scipy", "h5py", "matplotlib")}},
        "lockfile_sha256": digest(root / "uv.lock"),
        "provenance_manifest_sha256": digest(root / "provenance/manifest.json"),
        "reference_hashes": {str(q): digest(root / q) for q in (
            Path("data/original/paper/supplement.docx"), Path("data/original/paper/figure2.jpg"),
            Path("provenance/figure2_digitization.json"))},
        "directions": [], "conditions": [], "views": plane_views(model),
    }
    for k, name in enumerate(d["names"]):
        result["directions"].append({"name": name, "source_index_matlab": k + 1,
                                    "paper_index": model.paper_order.index(name) + 1,
                                    "contact_m": d["Loc"][k], "force_unit": d["Fu"][k],
                                    "unit_wrench_source": d["Uw"][:, k]})
    for factor in config["capacity_multipliers"]:
        B = model.torque_map(factor)
        tasks = []
        for u in d["Uw"].T:
            s = solve_direction(B, p["J"].T @ u, method=config["solver"],
                                tolerance=config["feasibility_tolerance"])
            force_scale = float(np.linalg.norm(u[3:]))
            row = asdict(s)
            row["contact_force_N"] = None if s.beta is None else s.beta * force_scale
            row["beta_to_newtons"] = force_scale
            row["upper_bound_sensitivity_N"] = (None if s.upper_marginal is None
                                                 else -s.upper_marginal * force_scale)
            tasks.append(row)
        result["conditions"].append({"multiplier": factor, "tasks": tasks})
    out = root / config["output_directory"]
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "run.json", result)
    # Validate original unrounded alpha; MATLAB's presentation-only 1e-4 clipping
    # is intentionally not applied to numerical equilibrium diagnostics.
    for c in result["conditions"]:
        for t in c["tasks"]:
            from .solver import Solution
            validate_solution(Solution(**{key: t[key] for key in Solution.__dataclass_fields__}))
    forces = np.array([[t["contact_force_N"] for t in c["tasks"]] for c in result["conditions"]])
    if np.min(np.diff(forces, axis=0)) < -1e-6:
        raise RuntimeError("Capacity monotonicity failed")
    result["validation"] = {
        "successful_tasks": 75,
        "max_scaled_equilibrium_residual": max(t["scaled_residual"] for c in result["conditions"] for t in c["tasks"]),
        "max_equilibrium_residual_Nm": max(t["residual"] for c in result["conditions"] for t in c["tasks"]),
        "minimum_capacity_increment_N": float(np.diff(forces, axis=0).min()),
        "unsupported_directions": [d["names"][k] for k in range(25) if np.any(forces[:, k] <= 1e-8)],
        "unbounded_directions": [],
    }
    # Approximate plot digitization, explicitly distinct from author numeric output.
    reference = json.loads((root / "provenance/figure2_digitization.json").read_text())
    comparisons = []
    for pt in reference["points"]:
        cal = reference["panels"][pt["panel"]]
        ref_N = np.linalg.norm(np.array(pt["pixel_xy"]) - cal["center_pixel_xy"]) * 300 / cal["radius_300N_px"]
        k = d["names"].index(pt["direction"])
        computed = forces[pt["multiplier"], k]
        comparisons.append({**pt, "digitized_N": float(ref_N), "computed_N": float(computed),
                            "difference_N": float(computed - ref_N)})
    errors = np.array([pt["difference_N"] for pt in comparisons])
    result["reference_comparison"] = {"kind": "approximate manual plot digitization",
                                       "uncertainty_N": reference["uncertainty_N"],
                                       "n_points": len(comparisons),
                                       "rmse_N": float(np.sqrt(np.mean(errors ** 2))),
                                       "max_absolute_error_N": float(abs(errors).max()),
                                       "points": comparisons}
    write_json(out / "run.json", result)
    with (out / "forces.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["paper_index", "source_index_matlab", "name", "0x_N", "1x_N", "2x_N"])
        for name in model.paper_order:
            k = d["names"].index(name)
            writer.writerow([model.paper_order.index(name) + 1, k + 1, name, *forces[:, k]])
    return result
