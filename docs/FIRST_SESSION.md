# Start here: a five-minute first look

Open [the visual tour](../results/figure2/explorer.html) in your browser.
No installation or calculation is needed. Take one step at a time:

1. **Picture the test.** Imagine a pad behind the head. The head pushes on it;
   the pad pushes back. Muscles hold the head still. The question is how strong
   that push can get. “Isometric” means the posture stays fixed in this test.
2. **Change your view.** Side = sagittal, above = transverse, front = coronal.
   These names refer to imaginary flat planes through the body. Switch views
   and notice the nose: the head stays still; only your viewpoint changes.
3. **Change one muscle group.** DCE means deep cervical extensors: a group deep
   in the back of the neck. Only the right group's capacity changes. For the
   lower-back-of-head test, the model predicts about **170 N** with it off,
   **237 N** at reference capacity, and **242 N** with twice its capacity.
   N means newtons, a unit of force. Other muscles and joint balances also
   limit the team, so doubling one group does not double the whole push.
4. **Read one chart point.** Find test **5**. Farther from the center means a
   stronger maximum push. The colors compare the three muscle settings.
   The number locates a test; the curve is not a movement of the head.

You can stop here. One useful idea to take away is that a head can exert force
without moving, and a team's strength depends on more than one muscle group.

The repo connects **muscle and contact data → a simplified neck model → a
calculation of the largest balanced push → pictures and tables**. The tour's
optional “How the pieces of this repo fit together” section links to each part.
These are generic model predictions, not measurements of your own neck.

Terminology reference: [OpenStax, Anatomical Terminology](https://openstax.org/books/anatomy-and-physiology-2e/pages/1-6-anatomical-terminology).

## Later, if you want more: a 45–90 minute fit check

Aim: experience reading a model, predicting its behavior and explaining one
constraint. This is a computer session; no physical neck-strength testing is
part of these activities. Open the repository in your editor alongside the
browser. Keep notes in your own file using the template below.

Run `uv run neck-repro explore`, or open `results/figure2/explorer.html` directly.
Expand **Full explorer · all 25 tests** below the tour. Exact coordinates,
activation bars, and research diagnostics each have their own expandable section.
Results are already saved. If desired, regenerate them with
`uv run --offline neck-repro reproduce`.

## 1. Understand one direction — 15–25 minutes

Start with **5 · backLow**, the default selection. Read its contact coordinates
and task vector. Identify anterior, superior and right in the three views.
Explain aloud which way the head exerts force and which way resistance acts.
Check why the arrow differs between projections even though the posture is fixed.

Look at the **1×** maximum force, then open diagnostics. Find the corresponding
activation vector, `beta`, `beta_to_newtons`, and `contact_force_N`. Multiply the
first two scalars: why is beta not automatically a force in newtons?

Open `src/neck_repro/solver.py`, find `A_eq`, and connect each side of the
equilibrium equation to the picture. Then inspect `Model.torque_map` in
`src/neck_repro/model.py`. Describe what one column of its nine-by-24 matrix means.
You do not need to memorize muscle names.

## 2. Predict before comparing — 10–20 minutes

Before selecting **7 · backHigh**, write a prediction: if only right DCE
capacity is removed, will that posterior/superior task change little, fall
moderately, or become impossible? Explain which fixed constraints informed
your guess. Also predict whether doubling capacity will double the task force.

Now select **7 · backHigh**. Record all three forces. Expand the secondary
activation view and switch between 1× and 2×. Read the achieved-force label each
time. Identify one changed activation, then write why you cannot interpret it
as a unique physiological response or as a matched-demand comparison.

## 3. Investigate a plateau and asymmetry — 15–30 minutes

Select **9 · backLowL**. Compare 1× with 2×, including right DCE's activation.
Read the list of active constraints below the bars. Is right DCE among the
constraints that currently limit output? Can other groups prevent additional
right DCE capacity from increasing force?

Next select **12 · backLowR**. Compare the two sides at 1× and at 0×. Predict
which symmetry was present initially and which was broken by the intervention.
Use the force values, not a presumed rule that right muscle changes must affect
only rightward tasks. If time permits, inspect the groups listed below the bars
and their actual elements in `results/figure2/run.json`.

Spend the final **5–15 minutes** on the note template. A good stopping point is
one explained result and one unresolved assumption, even if every muscle name
is still unfamiliar. Return later via `PROJECT_STATE.md`.

## Suggested interpretations — read after trying

<details>
<summary>Activity 1</summary>

backLow is at (−0.090, 0.025, 0) m. Its +Fu is approximately
(−0.949, −0.316, 0): posterior and inferior. The outward task force and inward
resistance oppose each other. The source's six-component normalization includes
moment and force terms, so the conversion to contact force is required.
At 1× the capacity is **236.815 N**. A torque-map column contains the nine joint
torques produced by unit activation of all elements sharing that group.

</details>

<details>
<summary>Activity 2</summary>

backHigh gives **191.367, 265.601, 270.003 N** at 0×, 1× and 2×.
Removing the right group lowers force about 28%; doubling adds only about 1.7%.
The force does not double because other group capacities and simultaneous torque
balances still constrain it. Right DCE activation in this solver's chosen optima
changes from 1.000 at reference capacity to about 0.591 at doubled capacity.
The two tasks also achieve different forces, and alternative optima may exist.

</details>

<details>
<summary>Activity 3</summary>

backLowL gives **112.728, 121.690, 121.690 N**. It has an exact numerical plateau
between 1× and 2×. In these returned solutions, right DCE activation changes
from about 0.614 to 0.307: halving activation of doubled capacity preserves
that group's contribution. Other constraints remain active. The left levator
group and the group labeled splenius cervicis have positive local force
sensitivities of about 58.96 and 40.97 N per unit activation-bound relaxation.
These are LP sensitivities, not validated physiological interventions.

backLowR has the same **121.690 N** reference capacity, but its 0× capacity is
**114.011 N**, compared with 112.728 N on the left. Unilateral removal breaks
the symmetry of the available muscle set. Coupled torque balance makes the
directional effect more complicated than the side of the altered muscles.

</details>

## Note template

- One result I can now explain:
- One assumption I still do not understand:
- Something I enjoyed or found draining:
- A question I would want to investigate next:
- A question for a biomechanics advisor:
