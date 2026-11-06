#!/usr/bin/env python3
"""Generate Amdahl/Gustafson speedup tables and an overlay plot."""

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


P_MAX = 65_536
SERIAL_FRACTIONS = (0.001, 0.01, 0.04, 0.10, 0.20)


def processor_counts() -> list[int]:
    values = np.geomspace(1, P_MAX, 160).round().astype(int)
    return sorted(set([1, P_MAX, *values.tolist()]))


def run(output_csv: Path, output_plot: Path) -> None:
    ps = processor_counts()
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_plot.parent.mkdir(parents=True, exist_ok=True)

    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["processors", "serial_fraction", "gustafson_speedup",
                        "gustafson_efficiency", "amdahl_speedup", "amdahl_efficiency"],
        )
        writer.writeheader()
        for alpha in SERIAL_FRACTIONS:
            for p in ps:
                s_g = p - alpha * (p - 1)
                s_a = 1.0 / (alpha + (1.0 - alpha) / p)
                writer.writerow({
                    "processors": p,
                    "serial_fraction": alpha,
                    "gustafson_speedup": s_g,
                    "gustafson_efficiency": s_g / p,
                    "amdahl_speedup": s_a,
                    "amdahl_efficiency": s_a / p,
                })

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)
    palette = plt.get_cmap("viridis")(np.linspace(0.05, 0.95, len(SERIAL_FRACTIONS)))
    for alpha, color in zip(SERIAL_FRACTIONS, palette):
        gust = [p - alpha * (p - 1) for p in ps]
        amdahl = [1.0 / (alpha + (1.0 - alpha) / p) for p in ps]
        axes[0].plot(ps, gust, color=color, lw=2.1, label=f"Gustafson α={alpha:.3f}")
        axes[0].plot(ps, amdahl, color=color, lw=1.8, ls="--", label=f"Amdahl α={alpha:.3f}")
        axes[1].plot(ps, np.array(gust) / ps, color=color, lw=2.1, label=f"Gustafson α={alpha:.3f}")
        axes[1].plot(ps, np.array(amdahl) / ps, color=color, lw=1.8, ls="--", label=f"Amdahl α={alpha:.3f}")

    axes[0].plot(ps, ps, color="#333333", ls=":", lw=1.4, label="Ideal linear")
    axes[0].set(title="Strong vs. weak scaled speedup", ylabel="Speedup", xlabel="Processors")
    axes[1].set(title="Parallel efficiency", ylabel="Efficiency", xlabel="Processors")
    for axis in axes:
        axis.set_xscale("log", base=2)
        axis.grid(True, which="both", alpha=0.25)
    axes[0].set_yscale("log", base=2)
    axes[1].set_ylim(0, 1.03)
    axes[1].axhline(1, color="#333333", ls=":", lw=1.2)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3, frameon=False)
    fig.suptitle("Amdahl fixed-size and Gustafson fixed-time models", fontsize=15)
    fig.savefig(output_plot, dpi=240, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path(__file__).parent / "generated/simulator_results.csv")
    parser.add_argument("--plot", type=Path, default=Path(__file__).parents[1] / "plots/simulator_scaling.png")
    args = parser.parse_args()
    run(args.csv, args.plot)
    print(f"Wrote {args.csv}")
    print(f"Wrote {args.plot}")


if __name__ == "__main__":
    main()
