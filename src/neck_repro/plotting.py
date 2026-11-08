"""Static figures and a standalone, offline interactive report."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS = ["#16a5cf", "#282378", "#33856c"]
VIEW_LABELS = {
    "sagittal": ("Side view (sagittal)", "Toward face", "Up"),
    "transverse": ("View from above (transverse)", "Person's right", "Toward face"),
    "coronal": ("Front view (coronal)", "Person's left", "Up"),
}


def render(root, result):
    root = Path(root)
    out = root / result["configuration"]["output_directory"]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), subplot_kw={"projection": "polar"})
    for ax, view in zip(axes, result["views"]):
        ids, theta = view["indices"], view["angles"]
        theta = np.r_[theta, theta[0]]
        for c, color, style in zip(result["conditions"], COLORS, ["--", "-", ":"]):
            values = [c["tasks"][i]["contact_force_N"] for i in ids]
            ax.plot(theta, values + values[:1], color=color, linestyle=style,
                    marker="o" if c["multiplier"] == 1 else "x", markersize=5,
                    label=["0× group switched off", "1× reference capacity", "2× double capacity"][c['multiplier']], linewidth=2)
        ax.set_ylim(0, 330)
        ax.set_yticks([100, 200, 300], ["100 N", "200 N", "300 N"])
        ax.set_xticks(np.mod(view["angles"], 2 * np.pi),
                      [str(result["directions"][i]["paper_index"]) for i in ids])
        ax.set_xlim(0, 2 * np.pi)
        ax.set_rlabel_position(90)
        title, right, up = VIEW_LABELS[view["name"]]
        ax.set_title(title, pad=22, fontweight="bold")
        ax.text(0.5, -0.17, f"Picture right: {right} · Picture top: {up}",
                transform=ax.transAxes, ha="center", fontsize=9)
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.01))
    fig.text(.5, .015, "Farther from center = stronger maximum push (N = newtons). Numbers identify tests; angles locate contacts, not push directions.\n"
             "Only the right back-of-neck group (DCE) changes capacity. Lines connect sampled tests; the head stays still.\n"
             "Abbott et al. (2024), Fig. 2 · doi:10.17632/jm5dhwwmyd.2 · Start with the guided tour in explorer.html", ha="center", fontsize=9)
    fig.subplots_adjust(top=.82, bottom=.23, left=.03, right=.97, wspace=.3)
    for ext in ("png", "svg"):
        fig.savefig(out / f"directional_capacity.{ext}", dpi=170)
    plt.close(fig)

    # A fixed-posture physical interpretation with real contact coordinates.
    k = next(i for i, d in enumerate(result["directions"]) if d["name"] == "backLow")
    d = result["directions"][k]
    fig, axes = plt.subplots(1, 3, figsize=(12, 5))
    loc = np.array([v["contact_m"] for v in result["directions"]])
    for ax, view in zip(axes, result["views"]):
        a, sign, center = view["axes"], np.array(view["signs"]), np.array(view["center"])
        xy = loc[:, a] * sign
        point = xy[k]
        force = np.array(d["force_unit"])[a] * sign
        from matplotlib.patches import Ellipse, Rectangle, Polygon, Arc
        if view["name"] != "transverse":
            ax.add_patch(Rectangle((-.02, -.14), .04, .09, fc="#eef2f6", ec="#a3aebf", zorder=0))
        ax.add_patch(Ellipse(center * sign, .22 if view["name"] != "coronal" else .19,
                            .25 if view["name"] != "transverse" else .22,
                            fc="#eef2f6", ec="#a3aebf", zorder=0))
        # Facial landmarks make the viewing direction recognizable without jargon.
        if view["name"] == "sagittal":
            ax.add_patch(Polygon([[.103, .09], [.13, .065], [.107, .05]],
                                 fc="#eef2f6", ec="#a3aebf"))
            ax.plot(.09, .103, ".", color="#67758a", markersize=4)
            ax.add_patch(Arc((.015, .055), .025, .04, theta1=50, theta2=300, ec="#a3aebf"))
        elif view["name"] == "transverse":
            ax.add_patch(Polygon([[-.012, .108], [0, .13], [.012, .108]],
                                 fc="#eef2f6", ec="#a3aebf"))
        else:
            ax.plot([-.035, .035], [.085, .085], ".", color="#67758a", markersize=4)
            ax.plot([0, -.008, .008], [.075, .045, .045], color="#a3aebf", lw=1)
            ax.add_patch(Arc((0, .015), .04, .02, theta1=190, theta2=350, ec="#a3aebf"))
        ax.scatter(*xy.T, s=12, color="#bbc3cf", label="Supplied contacts")
        ax.scatter(*point, s=65, color=COLORS[0], zorder=3)
        ax.annotate("", xy=point + .055 * force, xytext=point,
                    arrowprops={"arrowstyle": "->", "color": COLORS[1], "lw": 2.5})
        if np.linalg.norm(force) > 1e-8:
            offset = .009 * np.array([-force[1], force[0]]) / np.linalg.norm(force)
            ax.annotate("", xy=point + offset, xytext=point + .055 * force + offset,
                        arrowprops={"arrowstyle": "->", "color": "#b65119", "lw": 2, "linestyle": "--"})
        title, right, up = VIEW_LABELS[view["name"]]
        ax.set(xlim=(-.19, .19), ylim=(-.16, .22), aspect="equal",
               xlabel=right + " → (m)", ylabel=up + " → (m)", title=title)
        ax.grid(alpha=.15)
    fig.suptitle("Test 5 · lower back of head · the head stays still\nPurple: head pushes on resistance. Dashed orange: resistance pushes back on head.", fontsize=12)
    fig.text(.5, .01, "Same test, three views. Cyan = contact. Gray = other contacts. Schematic head; supplied contact positions.\n"
             "Arrows are offset for visibility; lengths are illustrative. In front view, only the downward part of the head's push is visible.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .15, 1, .89))
    fig.savefig(out / "selected_task.png", dpi=160)
    plt.close(fig)

    template = Path(__file__).with_name("explorer.html").read_text()
    (out / "explorer.html").write_text(template.replace("__DATA__", json.dumps(result, default=lambda x: x.tolist())))
