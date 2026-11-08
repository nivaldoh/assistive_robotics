# Source mapping and calculation

Source: Rebecca Abbott, Mendeley Data **jm5dhwwmyd v2**, DOI
[10.17632/jm5dhwwmyd.2](https://doi.org/10.17632/jm5dhwwmyd.2), retrieved 2026-11-07.
Original paths below are relative to `data/original/jm5dhwwmyd-v2/`.
The publication supplement is cached at `data/original/paper/supplement.docx`.

## Which model and why

Use **`data/ModelObjects.mat`, `gobj{2,2}`** in MATLAB's 1-based notation:
`model_name = '3 joint (n = 9)'`, `description = 'anatomic (nM = 24)'`.
The README identifies cell rows as kinematic variants and columns as grouping
variants. This is a stored `ModelCase` instance, not a result array.

Its nine rows represent pitch, roll and yaw at C6-C7, C4-C5 and C0-C1,
in that order. Their identities are independently checked against **every entry
of Supplement Table S2**, and against rows 1–3, 7–9, 19–21 of the full
21-coordinate object. Pitch is positive extension; roll is positive right
bending; yaw is positive left rotation. Neutral posture comes from the README
and `ModParams.m` constructor's zero-coordinate initialization.

**Do not interchange `KinModels.mat` and `ModelObjects.mat`.** The former contains
`models(2)` with coordinate names `pitch8,roll8,yaw8,pitch5,roll5,yaw5,pitch1,roll1,yaw1`.
Its first three rows differ from the object's lower-joint parameters. The full
`models(1)` even contains **24** coordinates, whereas the full object contains
21. For example, right semispinalis cervicis lower pitch moment arm is
0.00382488 m in `KinModels` but 0.04310272 m in the object and 0.0431 m in
Table S2. The source object's parameters agree with the published table, so the
choice is evidence-based, not a fitted modification. No `.osim` is present to
reconstruct the cause of the other export's discrepancy.

## Actual arrays

All four MAT files use MATLAB v7.3 / HDF5. HDF storage dimensions are reversed;
the loader transposes once and dereferences cells. Shapes below are logical
MATLAB/Python shapes after decoding.

| File / field | Shape | Meaning |
|---|---:|---|
| `ModelObjects / gobj{2,2}.J` | 6 × 9 | Skull-frame Jacobian; `J.T @ wrench` gives generalized torques |
| `.R`, `.Fa` | 9 × 96, 96 | Signed element moment arms in m; maximum forces in N |
| `.Sm`, `.group_idx` | 96 × 24, 96 | Binary element-to-group activation map; 1-based group IDs |
| `.Rg`, `.Fg` | 9 × 24, 24 | Equivalent grouped parameters, explained below |
| `.muscle_names`, `.group_names`, `.mm_groups` | 96, 24, 24 cells | Element names, group names, exact memberships |
| `TestDirections / markerInfo.Loc` | 25 × 3 | Contact locations in m, skull origin |
| `.Fu` | 25 × 3 | Unit task force directions |
| `.Uw` | 6 × 25 | Stored normalized wrench directions, moments first |
| `.names`, `.info` | 25 cells, text | Marker names and conventions |
| `KinModels / models` | 1 × 3 struct array | Alternative exports; retained and audited, not used |
| `MuscleGroups / muscle_groups` | 1 × 4 struct array | Group definitions; anatomical grouping is entry 2 |

The README calls the last file `MuscleModels.mat`; the actual filename is
`MuscleGroups.mat`. Its names abbreviate DCE as `mf-R`/`mf-L`, while the object
uses `DCE_R`/`DCE_L`. The archive has only eight files: README, two classes, four
MAT files and `functions/computeFWS.m`. It has no optimal-force reference arrays,
plot script, OpenSim model, or geometry mesh despite README mentions of a model.

## Decoding the serialized object

`sources.read_model_objects` is intentionally scoped to this file's SHA-256.
The `#subsystem#/MCOS` metadata header has version 4 and 16 named strings: 15
properties and the class `ModelCase`. Its counted property records contain
triples `(name ID, encoding=1, value ID)`. Each value ID refers to an HDF entry
at MCOS index `value ID + 2` in zero-based indexing. `gobj` cells carry scalar
object IDs that select these records. Thus properties are recovered by their
serialized names, rather than guessed from matrix sizes. The decoder checks
the class, all 12 object records, scalar payload format and dimensions.

For independent inspection, the principal object's HDF paths are `/#refs#/Px`
for J, `Qx` for R, `Rx` for Fa, `tz` for Rg, `uz` for Fg, `wz` for group_idx,
`xz` for Sm, `yz` for memberships and `wB` for group names. The complete mapping
is written to `run.json`. These paths are audit evidence, not lookup heuristics.
Additional checks compare the redundant grouped and element maps and the
independent printed parameter table. No MATLAB code is executed by this reader.

## Muscle conditions and grouping

The affected group is exactly **DCE_R, group 17** (Python column 16). Its
1-based element indices and literal names are:

| Index | Name |
|---:|---|
|55|semi_cerv_c3thx|
|73|mult_sup_C45C2|
|75|mult_sup_C56C2|
|77|mult_sup_C67C2|
|79|mult_sup_T1C4|
|81|mult_sup_T1C5|
|83|mult_sup_T2C6|
|85|mult_deep_C45C2|
|87|mult_deep_C56C3|
|89|mult_deep_C67C4|
|91|mult_deep_T1C5|
|93|mult_deep_T1C6|
|95|mult_deep_T2C7|

This includes multifidus and **semispinalis cervicis**, not semispinalis capitis.
Each condition copies the reference `Fa`, scales these 13 entries, then forms
`B = (R * Fa_condition) @ Sm`. Every other force capacity stays unchanged.

`ModelCase.equivGroupedParams` computes `tau = R @ diag(Fa) @ Sm`, uses the
**Euclidean norm** of the element force capacities for each `Fg`, and divides
each torque column by that norm to form `Rg`. Consequently
`Rg @ diag(Fg) = R @ diag(Fa) @ Sm`. Neither arithmetic averaging of moment arms
nor summing capacities reproduces that decomposition. Group members share one
activation, including elements with zero moment arms in this model.

**A second source discrepancy:** both stored anatomical maps put
`splen_cerv_c3thx` in the `levator_scap_R` group (and its left counterpart in
`levator_scap_L`). Table S3 instead lists it in the splenius cervicis group.
The stored `splenius_cerv` group contains longissimus cervicis and iliocostalis.
We preserve the supplied mapping, expose every membership in `run.json`, and
use descriptive activation labels to prevent the group names misleading users.

## Wrenches, signs, units and LP

Skull axes: **+x anterior, +y superior, +z right**. Origin: C0-C1.
Wrench ordering: **[Mx, My, Mz, Fx, Fy, Fz]**. Given contact `p` in m and unit
force `f`, the wrench **per newton** is `W = [cross(p,f), f]`.

The supplement describes normalizing this six-component array, and the stored
`Uw` agrees with `W / norm(W)` to floating-point precision. This numerical
normalization mixes lengths and dimensionless force directions; its scalar
`beta` is **not itself a force in N**. We preserve `Uw` in the source LP and
recover contact force as **`F_contact = beta * norm(Uw[3:6])`**. An independent
solve using `W` directly returns the same value as its scalar, in N.

`computeFWS.m` and `ModelCase.computeFWS` both maximize beta with
`[B, -J.T @ Uw] @ [alpha, beta] = 0`, `0 <= alpha <= 1`, `beta >= 0`, no upper
force cap. SciPy/HiGHS minimizes `-beta`; tolerance is 1e-9, compared with the
source MATLAB interior-point constraint tolerance 1e-3. Tests compare HiGHS
simplex/default and interior-point force solutions without requiring identical
activations. Source clipping of activations below 1e-4 is presentation only;
we retain raw values so the recorded equilibrium remains valid.

The algebra treats +w as the task wrench generated by muscles; balancing
external resistance is −w. Although source text calls Fu an applied vector,
the explorer labels its outward arrow **task force exerted by the head**, with
opposing resistance explicitly stated. Posture never changes.

## Direction identity and display

Paper numbers come from the supplement's named marker table, not MAT order.
For example paper direction 5 `backLow` is MAT row 17; paper direction 6 `back`
is MAT row 20. `forces.csv` and `run.json` retain both IDs.

Sagittal contacts satisfy `Loc.z = 0`; coronal contacts satisfy `Loc.x = 0`.
For the transverse panel, Figure 2's visible marker arrangement is matched to
`noseBelow`, `cheekL/R`, `templeL/R`, `earL/R`, `backLowL/R`, `backLow`. This is
a projection of nearby heights, not a literal constant-y slice. The contact
names, geometry, and independently read radial values support this matching;
the missing plotting script prevents verification of the authors' exact angles.

Our angular ordering is `atan2` of projected **contact positions**: (x,y) for
sagittal, (z,x) for transverse, and (−z,y) for front-view coronal. Sagittal and
coronal use a declared display center y=0.05 m to separate contact heights.
This is a visualization choice only, not a change to the skull-frame wrench.
The paper's exact angular spacing is not reproduced. The physical diagrams
use the actual Fu projections, and their outlines are explicitly schematic.
