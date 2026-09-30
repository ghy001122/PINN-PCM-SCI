"""Re-render the six t=1.28 B1 atlas panels from frozen saved arrays.

This is a figure-layout repair only.  It reads the 2026-09-21 two-time
``physical-panels.npz`` cache and performs no model query, solver step, or
metric recomputation.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "paper/paper_revision_20260921/figure-data/physical-panels.npz"
SOURCE_SHA256 = "db32ebf09ca80f3f805232ef79082b30aef85cbd59132ba35a9cbe4d29dc10cb"
SHAPE = (120, 240)
TIME_INDEX = 1


def image(ax, values, cmap, norm, title):
    im = ax.imshow(
        values.reshape(SHAPE),
        origin="lower",
        extent=(-1, 1, 0, 1),
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        aspect="equal",
    )
    ax.plot([-.35, .35], [0, 0], color="#142d40", lw=2.5, clip_on=False)
    ax.set_title(title, fontsize=8)
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([0, .5, 1])
    ax.tick_params(labelsize=7, length=2)
    return im


def save_panel(path: Path, field: str, label: str, states, *, error: bool) -> None:
    fig, axs = plt.subplots(3, 3, figsize=(7.1, 4.7))
    # Explicit margins avoid the constrained-layout instability that clipped
    # the second-time historical exports while preserving the panel recipe.
    fig.subplots_adjust(left=.085, right=.835, bottom=.075, top=.89, wspace=.24, hspace=.42)
    panels = [axs.flat[i] for i in (0, 1, 3, 4, 5, 6, 7, 8)]
    axs.flat[2].axis("off")
    reference = states[0][1][field][TIME_INDEX]

    if error:
        values = [(name, state[field][TIME_INDEX] - reference) for name, state in states]
        limit = max(
            float(np.max(np.abs(state[field] - states[0][1][field])))
            for _, state in states
        )
        norm = Normalize(-max(limit, 1e-12), max(limit, 1e-12))
        cmap = "RdBu_r"
        note = "Signed error, common scale\nSeed 29: second row\nSeed 43: third row\nNo spatial crop"
        colorbar_label = "prediction - reference"
        title = f"B1: signed {label} error at fixed t=1.28"
    else:
        values = [(name, state[field][TIME_INDEX]) for name, state in states]
        max_value = max(float(np.max(state[field])) for _, state in states)
        norm = Normalize(0, 1 if field == "phase" else max(max_value, 1e-12))
        cmap = "viridis"
        note = "Shared reference and baseline\nSeed 29: second row\nSeed 43: third row\nV/T samples retained\nInside phase-label gap"
        colorbar_label = f"{label} (dimensionless)"
        title = f"B1: {label} at fixed t=1.28; native 240 x 120 fields"

    axs.flat[2].text(.5, .5, note, ha="center", va="center", fontsize=8)
    for ax, (name, values_i) in zip(panels, values):
        im = image(ax, values_i, cmap, norm, name)
    cax = fig.add_axes([.87, .13, .017, .68])
    fig.colorbar(im, cax=cax, label=colorbar_label)
    fig.suptitle(title, fontsize=10, y=.975)
    fig.savefig(path, dpi=320, facecolor="white")
    plt.close(fig)


def main() -> None:
    digest = sha256(SOURCE.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise RuntimeError(f"Unexpected physical-panels cache identity: {digest}")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    with np.load(SOURCE, allow_pickle=False) as data:
        if not np.array_equal(data["time"], np.array([.27, 1.28])):
            raise RuntimeError("Unexpected frozen display times")
        identities = [
            ("Reference", "reference"),
            ("B_E", "b1_shorter_B_E"),
            ("E, seed 29", "b1_shorter_29_E"),
            ("D_E, seed 29", "b1_shorter_29_D_E"),
            ("F, seed 29", "b1_shorter_29_F"),
            ("E, seed 43", "b1_shorter_43_E"),
            ("D_E, seed 43", "b1_shorter_43_D_E"),
            ("F, seed 43", "b1_shorter_43_F"),
        ]
        full_states = [
            {field: data[f"{key}__{field}"].copy() for field in ("temperature", "phase", "joule_density")}
            for _, key in identities
        ]
        for field, label in (("temperature", "T"), ("phase", "phase"), ("joule_density", "q")):
            states = [(name, full) for (name, _), full in zip(identities, full_states)]
            save_panel(HERE / "figures" / f"b1-{field}-t2.png", field, label, states, error=False)
            save_panel(HERE / "figures" / f"b1-{field}-error-t2.png", field, label, states, error=True)

    print("B1_T2_ATLAS_LAYOUT_REPAIRED_FROM_FROZEN_ARRAYS")


if __name__ == "__main__":
    main()
