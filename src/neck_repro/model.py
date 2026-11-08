"""Explicit anatomical and task mappings, checked against the supplied sources."""
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

from .sources import read_mat, read_model_objects

DCE_RIGHT = (
    "semi_cerv_c3thx", "mult_sup_C45C2", "mult_sup_C56C2", "mult_sup_C67C2",
    "mult_sup_T1C4", "mult_sup_T1C5", "mult_sup_T2C6", "mult_deep_C45C2",
    "mult_deep_C56C3", "mult_deep_C67C4", "mult_deep_T1C5", "mult_deep_T1C6",
    "mult_deep_T2C7",
)
JOINTS = ("C6-C7", "C4-C5", "C0-C1")
COORDINATES = tuple(f"{j} {q}" for j in JOINTS for q in ("pitch", "roll", "yaw"))


@dataclass
class Model:
    parameters: dict
    directions: dict
    paper_order: list[str]
    source_audit: dict

    def torque_map(self, multiplier):
        if not np.isfinite(multiplier) or multiplier < 0:
            raise ValueError("Capacity multiplier must be finite and nonnegative")
        p = self.parameters
        forces = p["Fa"].copy()
        group = p["group_names"].index("DCE_R")
        forces[p["Sm"][:, group] == 1] *= multiplier
        return (p["R"] * forces) @ p["Sm"]


def supplement_tables(path):
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    return [[["".join(c.itertext()).strip() for c in row.findall("w:tc", ns)]
             for row in table.findall("w:tr", ns)] for table in root.findall(".//w:tbl", ns)]


def load_model(root, config):
    root = Path(root)
    i, j = config["model_cell_matlab"]
    objects = read_model_objects(root / config["model_file"])
    p = objects[i - 1][j - 1]
    if (p["model_name"], p["description"]) != ("3 joint (n = 9)", "anatomic (nM = 24)"):
        raise ValueError("Wrong model variant")
    for name, shape in {"J": (6, 9), "R": (9, 96), "Fa": (96,), "Sm": (96, 24),
                        "Rg": (9, 24), "Fg": (24,)}.items():
        if p[name].shape != shape or not np.isfinite(p[name]).all():
            raise ValueError(f"Invalid {name}")
    np.testing.assert_array_equal(p["Sm"].sum(axis=1), 1)
    np.testing.assert_array_equal(p["Sm"], np.eye(24)[p["group_idx"].astype(int) - 1])
    for g, members in enumerate(p["mm_groups"]):
        members = [members] if isinstance(members, str) else members
        actual = [n for n, selected in zip(p["muscle_names"], p["Sm"][:, g]) if selected]
        if members != actual:
            raise ValueError(f"Inconsistent group membership: {p['group_names'][g]}")
    affected = p["group_names"].index("DCE_R")
    if p["mm_groups"][affected] != list(DCE_RIGHT):
        raise ValueError("Affected DCE_R membership differs from supplement S3")
    np.testing.assert_allclose(p["Rg"] * p["Fg"], (p["R"] * p["Fa"]) @ p["Sm"], atol=2e-14)
    np.testing.assert_allclose(p["Fg"], np.sqrt((p["Fa"] ** 2) @ p["Sm"]))
    # Independent redundant source: the principal object is a row selection of
    # the supplied full 21-coordinate object: C6-C7, C4-C5, C0-C1.
    full = objects[0][1]
    rows = [0, 1, 2, 6, 7, 8, 18, 19, 20]
    np.testing.assert_array_equal(p["R"], full["R"][rows])
    np.testing.assert_array_equal(p["J"], full["J"][:, rows])

    d = read_mat(root / config["directions_file"])["markerInfo"]
    if d["Loc"].shape != (25, 3) or d["Uw"].shape != (6, 25) or len(set(d["names"])) != 25:
        raise ValueError("Unexpected directions")
    np.testing.assert_allclose(np.linalg.norm(d["Fu"], axis=1), 1, atol=1e-14)
    w = np.vstack((np.cross(d["Loc"], d["Fu"]).T, d["Fu"].T))
    # Verify the authors' stored convention only; never interpret this mixed-unit
    # Euclidean normalization or beta as a force in N.
    np.testing.assert_allclose(d["Uw"], w / np.linalg.norm(w, axis=0), atol=1e-14)

    tables = supplement_tables(root / "data/original/paper/supplement.docx")
    paper_order = [r[1] for r in tables[0][2:]]
    if set(paper_order) != set(d["names"]):
        raise ValueError("Direction names disagree with supplement")
    loc_err, wrench_err = [], []
    for row in tables[0][2:]:
        k = d["names"].index(row[1])
        expected = np.array(row[2:], dtype=float)
        actual = np.r_[d["Loc"][k], d["Fu"][k], d["Uw"][:, k]]
        np.testing.assert_allclose(actual, expected, atol=0.00050001, rtol=0)
        loc_err.append(float(np.max(abs(actual[:3] - expected[:3]))))
        wrench_err.append(float(np.max(abs(actual[6:] - expected[6:]))))
    parameter_rows = tables[1][2:]
    names = [r[1].replace(" ", "_") for r in parameter_rows]
    if names != p["muscle_names"]:
        raise ValueError("Element order disagrees with supplement S2")
    forces = np.array([float(r[2]) for r in parameter_rows])
    arms = np.array([[float(c) if c else 0 for c in r[3:]] for r in parameter_rows]).T
    np.testing.assert_allclose(p["Fa"], forces, atol=0.050001, rtol=0)
    np.testing.assert_allclose(p["R"], arms, atol=0.000050001, rtol=0)
    # Preserve, quantify and expose the conflicting ancillary export.
    kin = read_mat(root / "data/original/jm5dhwwmyd-v2/data/KinModels.mat")["models"]
    audit = {
        "supplement_R_max_abs_difference_m": float(abs(p["R"] - arms).max()),
        "supplement_F_max_abs_difference_N": float(abs(p["Fa"] - forces).max()),
        "supplement_location_max_abs_difference_m": max(loc_err),
        "supplement_Uw_max_abs_difference": max(wrench_err),
        "kinmodels_R_max_abs_difference_m": float(abs(kin["R"][1] - p["R"]).max()),
        "kinmodels_J_max_abs_difference": float(abs(kin["J"][1] - p["J"]).max()),
        "reference_force_outputs_available": False,
        "object_properties": p["source_paths"],
    }
    return Model(p, d, paper_order, audit)


def plane_views(model):
    """Geometric sections with angles from projected contacts, not wrench norms.

    Figure 2's transverse panel combines nearby heights. Its named contacts are
    matched to the supplement geometry and visible marker arrangement. No plotting
    script is supplied. We explicitly use a geometry-based angular layout; the
    paper's exact angular spacing is not claimed. See source_mapping.md.
    """
    loc, names = model.directions["Loc"], model.directions["names"]
    definitions = [
        ("sagittal", np.flatnonzero(np.isclose(loc[:, 2], 0)), [0, 1], [1, 1], [0, 0.05],
         "Anterior +x", "Superior +y"),
        ("transverse", [names.index(n) for n in (
            "noseBelow", "cheekR", "templeR", "earR", "backLowR", "backLow",
            "backLowL", "earL", "templeL", "cheekL")], [2, 0], [1, 1], [0, 0],
         "Right +z", "Anterior +x"),
        ("coronal", np.flatnonzero(np.isclose(loc[:, 0], 0)), [2, 1], [-1, 1], [0, 0.05],
         "Left −z", "Superior +y"),
    ]
    views = []
    for name, ids, axes, signs, center, horizontal, vertical in definitions:
        xy = (loc[ids][:, axes] - center) * signs
        angles = np.arctan2(xy[:, 1], xy[:, 0])
        order = np.argsort(angles)
        views.append(dict(name=name, indices=np.array(ids)[order].tolist(),
                          angles=angles[order].tolist(), horizontal=horizontal,
                          vertical=vertical, axes=axes, signs=signs, center=center))
    return views
