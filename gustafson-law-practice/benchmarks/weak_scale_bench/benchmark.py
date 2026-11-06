#!/usr/bin/env python3
"""Empirical weak-scaling benchmark with fixed work per worker."""

import argparse
import csv
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import multiprocessing as mp
import numpy as np


def compute_slice(task: tuple[int, int, int, int]) -> float:
    start_idx, count, total_elements, repeats = task
    if count <= 0:
        return 0.0
    scale = 1.0 / total_elements
    x = np.arange(start_idx, start_idx + count, dtype=np.float64) * scale
    result = 0.0
    for iteration in range(repeats):
        phase = 1.0 + iteration * 0.001
        values = np.sqrt(1.0 + phase * x * x) * np.sin(x + phase)
        result += float(np.sum(values, dtype=np.float64))
    return result * scale


def partition_tasks(workers: int, elements_per_worker: int, repeats: int):
    total = workers * elements_per_worker
    tasks = []
    for worker in range(workers):
        begin = worker * elements_per_worker
        tasks.append((begin, elements_per_worker, total, repeats))
    return tasks


def run_one(workers: int, elements_per_worker: int, repeats: int) -> dict[str, Any]:
    tasks = partition_tasks(workers, elements_per_worker, repeats)
    start = time.perf_counter()
    serial_parts = [compute_slice(task) for task in tasks]
    t_serial = time.perf_counter() - start

    start = time.perf_counter()
    with mp.Pool(processes=workers) as pool:
        parallel_parts = pool.map(compute_slice, tasks)
    t_parallel = time.perf_counter() - start

    serial_checksum = float(sum(serial_parts))
    parallel_checksum = float(sum(parallel_parts))
    if not np.isclose(serial_checksum, parallel_checksum, rtol=1e-11, atol=1e-10):
        raise RuntimeError(f"Numerical mismatch at P={workers}")
    speedup = t_serial / t_parallel
    return {
        "workers": workers,
        "elements_per_worker": elements_per_worker,
        "total_elements": workers * elements_per_worker,
        "repeats": repeats,
        "t_parallel_sec": t_parallel,
        "t_serial_sec": t_serial,
        "speedup": speedup,
        "checksum": parallel_checksum,
    }


def core_counts(max_workers: int) -> list[int]:
    return list(range(1, max_workers + 1))


def command_output(args: list[str]) -> str:
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def hardware_metadata() -> dict[str, Any]:
    logical = os.cpu_count() or 1
    physical = None
    memory_bytes = None
    processor = platform.processor() or platform.machine()
    if platform.system() == "Darwin":
        for key, target in (("hw.physicalcpu", "physical"), ("hw.memsize", "memory")):
            raw = command_output(["sysctl", "-n", key])
            try:
                value = int(raw)
            except ValueError:
                continue
            if target == "physical":
                physical = value
            else:
                memory_bytes = value
        for line in command_output(["system_profiler", "SPHardwareDataType"]).splitlines():
            stripped = line.strip()
            if stripped.startswith("Chip:"):
                processor = stripped.split(":", 1)[1].strip()
                break
    if physical is None:
        physical = max(1, logical // 2)
    return {
        "platform": platform.platform(),
        "processor": processor,
        "physical_cores": physical,
        "logical_cores": logical,
        "memory_bytes": memory_bytes,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--elements-per-worker", type=int, default=300_000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--seed", type=int, default=230103344)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results.csv"))
    parser.add_argument("--metadata", type=Path, default=Path(__file__).with_name("hardware.json"))
    args = parser.parse_args()
    if args.runs < 5:
        raise SystemExit("Use at least five runs per configuration.")
    if args.elements_per_worker < 1 or args.repeats < 1:
        raise SystemExit("Elements and repeats must be positive.")

    counts = core_counts(max(1, args.max_workers))
    rng = random.Random(args.seed)
    all_rows = []
    for run_number in range(1, args.runs + 1):
        order = counts[:]
        rng.shuffle(order)
        for workers in order:
            print(f"Run {run_number}/{args.runs}, P={workers}", flush=True)
            row = run_one(workers, args.elements_per_worker, args.repeats)
            row["run"] = run_number
            all_rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run", "workers", "elements_per_worker", "total_elements", "repeats",
              "t_parallel_sec", "t_serial_sec", "speedup", "checksum"]
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)

    metadata = hardware_metadata()
    args.metadata.write_text(__import__("json").dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(all_rows)} measurements across P={counts}.")
    print(f"Results: {args.output}")
    print(f"Hardware: {args.metadata}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
