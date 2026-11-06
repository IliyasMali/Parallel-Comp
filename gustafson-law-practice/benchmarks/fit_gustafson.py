#!/usr/bin/env python3
"""Summarize repeated weak-scaling measurements and fit Gustafson's fraction."""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "benchmarks/weak_scale_bench/results.csv"
DEFAULT_SUMMARY = ROOT / "benchmarks/weak_scale_bench/fit_summary.json"
DEFAULT_REPORT = ROOT / "benchmarks/weak_scale_bench/fit_report.md"
DEFAULT_PLOT = ROOT / "plots/scaling_comparison.png"


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def mean_sd(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    sd = float(array.std(ddof=1)) if len(array) > 1 else 0.0
    return mean, sd


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[int(row["workers"])].append(row)
    summary = []
    for p in sorted(groups):
        records = groups[p]
        tp_mean, tp_sd = mean_sd([float(r["t_parallel_sec"]) for r in records])
        ts_mean, ts_sd = mean_sd([float(r["t_serial_sec"]) for r in records])
        speeds = [float(r["t_serial_sec"]) / float(r["t_parallel_sec"]) for r in records]
        s_mean, s_sd = mean_sd(speeds)
        summary.append({
            "workers": p,
            "n_runs": len(records),
            "t_parallel_mean_sec": tp_mean,
            "t_parallel_sd_sec": tp_sd,
            "t_serial_mean_sec": ts_mean,
            "t_serial_sd_sec": ts_sd,
            "speedup_mean": s_mean,
            "speedup_sd": s_sd,
            "speedup_se": s_sd / math.sqrt(len(records)),
        })

    # Gustafson: S(P)=P-alpha(P-1). Fit P-S against P-1 through the origin.
    x = np.asarray([item["workers"] - 1 for item in summary if item["workers"] > 1], dtype=float)
    y = np.asarray([
        item["workers"] - item["speedup_mean"]
        for item in summary if item["workers"] > 1
    ], dtype=float)
    alpha = float(np.dot(x, y) / np.dot(x, x)) if np.dot(x, x) else 0.0
    fitted = [
        {"workers": item["workers"],
         "observed_speedup": item["speedup_mean"],
         "gustafson_fitted_speedup": item["workers"] - alpha * (item["workers"] - 1),
         "amdahl_same_alpha_speedup": 1.0 / (alpha + (1.0 - alpha) / item["workers"])}
        for item in summary
    ]
    fit_points = [item for item in fitted if int(item["workers"]) > 1]
    observed_fit = [float(item["observed_speedup"]) for item in fit_points]
    residual_ss = sum(
        (float(item["observed_speedup"]) - float(item["gustafson_fitted_speedup"])) ** 2
        for item in fit_points
    )
    total_ss = sum((value - np.mean(observed_fit)) ** 2 for value in observed_fit)
    r_squared = 1.0 - residual_ss / total_ss if total_ss > 0 else 1.0
    return summary, alpha, fitted, r_squared


def write_report(path: Path, summary, alpha: float, r_squared: float, raw_count: int) -> None:
    lines = [
        "# Empirical weak-scaling fit",
        "",
        f"Raw measurements: {raw_count}",
        f"Least-squares Gustafson serial fraction: `alpha_observed = {alpha:.6f}`",
        f"R-squared against `S(P)=P-alpha(P-1)`: `{r_squared:.6f}`",
        "",
        "P=1 is excluded from the regression because it is the normalized baseline; its Pool startup time is still reported in the raw table. An alpha outside [0, 1] means the ideal Gustafson serial-fraction interpretation is not physically valid for this fit; process startup, communication, and timing variation can dominate measured speedup.",
        "",
        "| P | Runs | T_parallel mean ± SD (s) | T_serial mean ± SD (s) | Speedup mean ± SD |",
        "|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        lines.append(
            f"| {item['workers']} | {item['n_runs']} | "
            f"{item['t_parallel_mean_sec']:.6f} ± {item['t_parallel_sd_sec']:.6f} | "
            f"{item['t_serial_mean_sec']:.6f} ± {item['t_serial_sd_sec']:.6f} | "
            f"{item['speedup_mean']:.4f} ± {item['speedup_sd']:.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_fit(path: Path, summary, fitted, alpha: float) -> None:
    ps = np.asarray([int(item["workers"]) for item in summary], dtype=float)
    measured = np.asarray([float(item["speedup_mean"]) for item in summary])
    errors = np.asarray([float(item["speedup_se"]) for item in summary])
    grid = np.linspace(1, max(ps), 300)
    gust = grid - alpha * (grid - 1)
    amdahl = 1.0 / (alpha + (1.0 - alpha) / grid)

    fig, ax = plt.subplots(figsize=(9, 6), constrained_layout=True)
    ax.plot(grid, grid, ls=":", color="#666666", label="Ideal linear speedup")
    ax.plot(grid, gust, lw=2.2, color="#2463A6", label=f"Gustafson fit (α={alpha:.3f})")
    ax.plot(grid, amdahl, lw=2.0, ls="--", color="#D97706", label="Amdahl, same α")
    ax.errorbar(ps, measured, yerr=errors, fmt="o", ms=6, capsize=4,
                color="#9B2C2C", label="Measured mean ± standard error")
    ax.set_xlabel("Worker processes P")
    ax.set_ylabel("Speedup")
    ax.set_title("Measured weak scaling vs. theoretical models")
    ax.set_xticks(ps, [str(int(p)) for p in ps])
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--plot", type=Path, default=DEFAULT_PLOT)
    args = parser.parse_args()

    rows = load_rows(args.input)
    summary, alpha, fitted, r_squared = summarize(rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps({
        "alpha_observed": alpha,
        "r_squared": r_squared,
        "by_worker_count": summary,
        "fitted_curves": fitted,
    }, indent=2) + "\n", encoding="utf-8")
    write_report(args.report, summary, alpha, r_squared, len(rows))
    plot_fit(args.plot, summary, fitted, alpha)
    print(f"alpha_observed={alpha:.6f}; R^2={r_squared:.6f}")
    print(f"Wrote {args.report}")
    print(f"Wrote {args.plot}")


if __name__ == "__main__":
    main()
