"""Render saved conditional-response arrays; no solve, fit, or history replay."""
from pathlib import Path
import json
import os
for _key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_key] = "4"
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "paper/paper_revision_20260928_conditional_thermal"
OUT = HERE / "figures"
COLORS = {"saved": "#252525", "Q_ref": "#938181", "V_ref": "#27834e",
          "P": "#2468b4", "CS": "#d7741c"}
LABELS = {"saved": "Saved source", "Q_ref": "Q ref", "V_ref": "V ref",
          "P": "PCHIP", "CS": "Cubic spline"}
TITLES = {"single_9V": "Single device, 9 V", "single_12p5V": "Single device, 12.5 V",
          "single_15p8V": "Single device, 15.8 V",
          "pair_excitation": "Coupled excitation, 11 / 9.4 V",
          "pair_inhibition": "Coupled inhibition, 11 / 14 V"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.titlesize": 11, "axes.labelsize": 10,
                     "legend.fontsize": 9, "figure.titlesize": 14,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.facecolor": "white", "pdf.fonttype": 42})


def load(path):
    with np.load(path, allow_pickle=False) as file:
        return {key: file[key] for key in file.files}


def record(item):
    folder = HERE / "arrays" / item["id"]
    source = load(ROOT / item["source"])
    thermal = load(folder / "thermal.npz")
    history = {key: load(folder / ("history-" + key + ".npz")) for key in ("P", "CS")}
    prediction = {key: load(ROOT / item["predictions"][method])
                  for key, method in (("P", "PCHIP"), ("CS", "CS"))}
    return source, thermal, history, prediction


def format_axis(axis, label):
    axis.set_ylabel(label)
    axis.grid(alpha=.22, linewidth=.6)
    axis.tick_params(axis="both", labelsize=9)


def save(fig, stem, footer):
    fig.text(.075, .013, footer, fontsize=8, color="#444444")
    fig.tight_layout(rect=(0, .045, 1, .965), h_pad=1.25)
    fig.savefig(OUT / (stem + ".png"), dpi=160)
    fig.savefig(OUT / (stem + ".pdf"))
    plt.close(fig)
    return stem


def case_figure(item, source, thermal, history, device):
    t = thermal["time"] * 1e6
    fig, axes = plt.subplots(3, 1, figsize=(12.4, 8.5), sharex=True)
    fig.suptitle(f"{TITLES[item['case']]} | device {'AB'[device]} | 0.5 ns source")
    axes[0].plot(t, source["temperature"][:, device], color=COLORS["saved"],
                 linewidth=1.4, label=LABELS["saved"])
    for key in ("Q_ref", "V_ref", "P", "CS"):
        style = ":" if key == "Q_ref" else "--" if key == "V_ref" else "-"
        axes[0].plot(t, thermal["T_" + key][:, device], color=COLORS[key],
                     linestyle=style, linewidth=1.05, label=LABELS[key])
        axes[1].plot(t, thermal["T_" + key][:, device] - source["temperature"][:, device],
                     color=COLORS[key], linestyle=style, linewidth=1.0, label=LABELS[key])
    for key in ("P", "CS"):
        axes[2].plot(t, history[key]["r_close"][:, device] * 1e3,
                     color=COLORS[key], linewidth=1.0, label=LABELS[key])
    axes[0].legend(ncol=5, loc="lower left", bbox_to_anchor=(0, 1.01), borderaxespad=0)
    axes[2].legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.01), borderaxespad=0)
    for axis, label in zip(axes, ("Temperature (K)", "T - saved source (K)",
                                  r"$I_R-I_{KCL}$ (mA)")):
        format_axis(axis, label)
        axis.set_xlim(0, 20)
        axis.axvline(10, color="#777777", linestyle=":", linewidth=.7)
    for axis in axes[1:]:
        axis.axhline(0, color="#555555", linewidth=.6, zorder=0)
    axes[-1].set_xlabel("Time (microseconds)")
    return save(fig, f"conditional-{item['case']}-{'AB'[device]}",
                "Q ref: native saved power; V ref: native saved voltage. All curves use saved arrays; no alignment or feedback.")


def history_exhibit(item, source, thermal, history, prediction):
    t = thermal["time"] * 1e6
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 8.1), sharex=True)
    fig.suptitle("Prespecified 12.5 V exhibit | constitutive history and current closure")
    for axis, field, factor, label in ((axes[0, 0], "g", 1, "Insulating fraction g"),
                                       (axes[0, 1], "resistance", 1e-3, "Resistance (kohm)")):
        axis.plot(t, source[field][:, 0] * factor, color=COLORS["saved"],
                  linewidth=1.2, label=LABELS["saved"])
        for key in ("P", "CS"):
            axis.plot(t, history[key][field][:, 0] * factor, color=COLORS[key],
                      linewidth=1.0, label=LABELS[key])
        format_axis(axis, label)
        axis.legend(ncol=3, loc="lower left", bbox_to_anchor=(0, 1.01), borderaxespad=0)
    axes[0, 1].set_yscale("log")
    axes[1, 0].plot(t, source["device_current"][:, 0] * 1e3,
                    color=COLORS["saved"], linewidth=1.2, label="Saved source")
    for key in ("P", "CS"):
        axes[1, 0].plot(t, prediction[key]["device_current"][:, 0] * 1e3,
                        color=COLORS[key], linestyle="--", linewidth=.9, label=LABELS[key] + " KCL")
        axes[1, 0].plot(t, history[key]["I_R"][:, 0] * 1e3,
                        color=COLORS[key], linewidth=1.0, label=LABELS[key] + " R-law")
        axes[1, 1].plot(t, history[key]["r_close"][:, 0] * 1e3,
                        color=COLORS[key], linewidth=1.0, label=LABELS[key])
    format_axis(axes[1, 0], "Device current (mA)")
    format_axis(axes[1, 1], r"$I_R-I_{KCL}$ (mA)")
    axes[1, 0].legend(ncol=3, loc="lower left", bbox_to_anchor=(0, 1.01), borderaxespad=0, fontsize=8)
    axes[1, 1].legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.01), borderaxespad=0)
    for axis in axes.flat:
        axis.set_xlim(0, 20)
        axis.axvline(10, color="#777777", linestyle=":", linewidth=.7)
    for axis in axes[1]:
        axis.set_xlabel("Time (microseconds)")
        axis.axhline(0, color="#555555", linewidth=.6, zorder=0)
    return save(fig, "single_12p5V-history-closure", "0.5 ns source. Same legal initial history; R-law current is a no-feedback diagnostic and does not replace KCL current.")


def fixed_zoom(item, source, thermal, history, prediction):
    t = thermal["time"] * 1e6
    mask = (t >= 2.362) & (t <= 2.862)
    fig, axes = plt.subplots(3, 1, figsize=(12.4, 8.5), sharex=True)
    fig.suptitle("Prespecified 12.5 V first-peak window | 2.362-2.862 microseconds")
    axes[0].plot(t[mask], source["temperature"][mask, 0], color=COLORS["saved"],
                 linewidth=1.5, label=LABELS["saved"])
    for key in ("Q_ref", "V_ref", "P", "CS"):
        axes[0].plot(t[mask], thermal["T_" + key][mask, 0], color=COLORS[key],
                     linewidth=1.2, linestyle=":" if key in ("Q_ref", "V_ref") else "-", label=LABELS[key])
    axes[1].plot(t[mask], source["device_current"][mask, 0] * 1e3, color=COLORS["saved"],
                 linewidth=1.5, label="Saved source")
    for key in ("P", "CS"):
        axes[1].plot(t[mask], prediction[key]["device_current"][mask, 0] * 1e3,
                     color=COLORS[key], linestyle="--", linewidth=1.1, label=LABELS[key] + " KCL")
        axes[1].plot(t[mask], history[key]["I_R"][mask, 0] * 1e3,
                     color=COLORS[key], linewidth=1.1, label=LABELS[key] + " R-law")
        axes[2].plot(t[mask], history[key]["r_close"][mask, 0] * 1e3,
                     color=COLORS[key], linewidth=1.2, label=LABELS[key])
    for axis, label in zip(axes, ("Temperature (K)", "Device current (mA)", r"$I_R-I_{KCL}$ (mA)")):
        format_axis(axis, label)
        axis.set_xlim(2.362, 2.862)
        axis.legend(ncol=5 if axis is axes[0] else 3, loc="lower left", bbox_to_anchor=(0, 1.01), borderaxespad=0, fontsize=8)
    axes[2].axhline(0, color="#555555", linewidth=.6, zorder=0)
    axes[2].set_xlabel("Time (microseconds)")
    return save(fig, "single_12p5V-fixed-first-peak", "Window inherited from the preceding cubic-energy comparison; no peak shift, smoothing, time warping, or new selection.")


def main():
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    rendered = []
    for item in config["records"]:
        if item["dt_s"] != .5e-9:
            continue
        source, thermal, history, prediction = record(item)
        for device in range(source["voltage"].shape[1]):
            rendered.append(case_figure(item, source, thermal, history, device))
        if item["case"] == "single_12p5V":
            rendered.append(history_exhibit(item, source, thermal, history, prediction))
            rendered.append(fixed_zoom(item, source, thermal, history, prediction))
    fig, axes = plt.subplots(3, 3, figsize=(19.5, 13.2))
    for axis, stem in zip(axes.flat, rendered):
        axis.imshow(plt.imread(OUT / (stem + ".png")))
        axis.set_axis_off()
        axis.set_title(stem, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "contact-sheet.png", dpi=120)
    plt.close(fig)
    lines = ["# 条件热响应与本构闭合图件索引", "",
             "所有图件仅从已保存数组绘制，不重新推进温度、不重放历史、不改变冻结插值。",
             "固定主展示为12.5 V、0.5 ns；以下覆盖全部五工况、七个器件角色。源步长比较见结果表，不将细步源记录视为连续真解。", "",
             "## 固定12.5 V展示", "",
             "- [全程温度、误差与闭合](figures/conditional-single_12p5V-A.png)",
             "- [全程迟滞、电阻与两类电流](figures/single_12p5V-history-closure.png)",
             "- [沿用2.362–2.862 μs窗口](figures/single_12p5V-fixed-first-peak.png)", "",
             "## 全工况图件", "",
             "| 工况／角色 | PNG | 矢量PDF |", "|---|---|---|"]
    for stem in rendered:
        lines.append(f"| {stem} | [查看](figures/{stem}.png) | [下载](figures/{stem}.pdf) |")
    lines += ["", "## 全部十套输入对应的条件数组", "",
              "热响应包含Q_ref、V_ref、P、CS和4/8点求积逐点差；分解、历史与原始输入的关联见冻结配置。", "",
              "| 保存系统 | 热响应 | 误差分解 | P历史 | CS历史 | 来源核对 |", "|---|---|---|---|---|---|"]
    for item in config["records"]:
        prefix = "arrays/" + item["id"]
        lines.append(f"| {item['id']} | [NPZ]({prefix}/thermal.npz) | [NPZ]({prefix}/decomposition.npz) | "
                     f"[NPZ]({prefix}/history-P.npz) | [NPZ]({prefix}/history-CS.npz) | [JSON]({prefix}/source-history-check.json) |")
    lines += ["", "边界：本包是作者模型记录上的条件响应分析。图中R-law电流为无反馈诊断，不替换既有KCL电流。",
              "温度差使用绝对K；没有工程用途容差，不能凭视觉接近宣布工程合格、PINN增量或材料验证。", ""]
    (HERE / "figures-index.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "render-record.json").write_text(json.dumps({
        "mode": "saved_arrays_only", "figures": rendered, "native_time_points_used": True,
        "smoothing": False, "time_alignment": False, "temperature_or_history_recomputation": False,
        "fixed_zoom_us": [2.362, 2.862], "figure_window_source": "preceding cubic-energy comparison",
        "runtime": {"numpy": np.__version__, "matplotlib": matplotlib.__version__},
        "visual_review_status": "PENDING"
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"figures": len(rendered), "directory": str(OUT)}))


if __name__ == "__main__":
    main()
