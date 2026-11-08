"""Artificial analytical fixtures are tests only, never anatomical results."""
from pathlib import Path
import json

import numpy as np
import pytest

from neck_repro.model import DCE_RIGHT, load_model
from neck_repro.solver import solve_direction, validate_solution
from neck_repro.sources import read_mat, verify_sources

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def model():
    verify_sources(ROOT)
    return load_model(ROOT, json.loads((ROOT / "configs/figure2.json").read_text()))


@pytest.mark.parametrize("B,q,expected", [
    ([[6]], [2], 3),                  # one torque source, known mechanical ratio
    ([[1, 1], [1, -1]], [1, 0], 2), # both independent equilibrium constraints
    ([[1]], [-1], 0),                # unsupported sign: muscles cannot push
    ([[0]], [1], 0),                 # zero capacity, bounded task
    ([[41]], [1], 41),               # 2*3 + 5*7, two elements sharing activation
])
def test_analytical_fixtures(B, q, expected):
    result = solve_direction(B, q)
    validate_solution(result)
    assert result.beta == pytest.approx(expected, abs=1e-9)


def test_unbounded_task_is_reported_without_cap():
    result = solve_direction([[1]], [0])
    assert result.status == 3
    assert result.beta is None
    with pytest.raises(RuntimeError, match="LP failed"):
        validate_solution(result)


def test_bad_dimensions_rejected():
    with pytest.raises(ValueError):
        solve_direction([[1, 2]], [1, 2])


def test_identity_grouping_and_independent_supplement(model):
    p = model.parameters
    assert p["nDOFs"] == 9 and p["nGroups"] == 24 and p["nMuscles"] == 96
    affected = np.flatnonzero(p["Sm"][:, p["group_names"].index("DCE_R")])
    assert (affected + 1).tolist() == [55, 73, 75, 77, 79, 81, 83, 85, 87, 89, 91, 93, 95]
    assert [p["muscle_names"][i] for i in affected] == list(DCE_RIGHT)
    assert "semi_cap_sklc5" not in DCE_RIGHT
    assert model.source_audit["supplement_R_max_abs_difference_m"] <= 0.00005
    assert model.source_audit["supplement_F_max_abs_difference_N"] <= 0.050001
    np.testing.assert_allclose(model.torque_map(1), p["Rg"] * p["Fg"], atol=1e-14)
    for factor in [2, 0, 1, 2]:
        fg = p["Fg"].copy()
        fg[p["group_names"].index("DCE_R")] *= factor
        np.testing.assert_allclose(model.torque_map(factor), p["Rg"] * fg, atol=1e-14)
    # The source anomaly is measurable, not hidden by the decoding checks.
    kin = read_mat(ROOT / "data/original/jm5dhwwmyd-v2/data/KinModels.mat")["models"]
    assert kin["nDOFs"][0] == 24
    assert np.max(abs(kin["R"][1] - p["R"])) > .06


def test_all_tasks_valid_monotone_and_force_units(model):
    p, d = model.parameters, model.directions
    forces = []
    for factor in [0, 1, 2]:
        B = model.torque_map(factor)
        row = []
        for i, u in enumerate(d["Uw"].T):
            result = solve_direction(B, p["J"].T @ u)
            validate_solution(result)
            assert result.scaled_residual < 1e-9
            newtons = result.beta * np.linalg.norm(u[3:])
            # Independently solve with a wrench PER NEWTON of contact force.
            wrench_per_N = np.r_[np.cross(d["Loc"][i], d["Fu"][i]), d["Fu"][i]]
            direct = solve_direction(B, p["J"].T @ wrench_per_N, method="highs-ipm")
            validate_solution(direct)
            assert newtons == pytest.approx(direct.beta, rel=1e-8, abs=1e-7)
            row.append(newtons)
        forces.append(row)
    assert np.min(np.diff(forces, axis=0)) >= -1e-7
    assert np.isfinite(forces).all() and np.min(forces) > 0


def test_one_newton_contact_wrench_has_correct_sign():
    # Artificial lever: force +x at y=0.1 m creates -0.1 Nm about +z.
    moment = np.cross([0, .1, 0], [1, 0, 0])
    np.testing.assert_array_equal(moment, [0, 0, -.1])
