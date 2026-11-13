"""Zero-dependency benchmark and verifiable 64-bit hash functions.
The PDF has typographical whitespace errors; this is a syntactically valid
implementation of Listing 1's algorithm.
"""
from dataclasses import dataclass
from typing import Callable
import multiprocessing as mp
import time


@dataclass
class BenchStats:
    min_ms: float
    median_ms: float
    iqr_ms: float
    max_ms: float


def fnv1a_hash(s: str) -> int:
    h = 14695981039346656037
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


def summarize_ms(samples: list[float]) -> BenchStats:
    samples = sorted(samples)
    n = len(samples)
    mid = n // 2
    med = samples[mid] if n % 2 else 0.5 * (samples[mid - 1] + samples[mid])
    return BenchStats(samples[0], med, samples[(3 * n) // 4] - samples[n // 4], samples[-1])


def run_benchmark(fn: Callable[[], None], warmup_runs: int = 3, timed_runs: int = 9) -> BenchStats:
    for _ in range(warmup_runs):
        fn()
    samples = []
    for _ in range(timed_runs):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        samples.append((t1 - t0) / 1e6)
    return summarize_ms(samples)


def emit_verify_tag(task_id: str, student_seed: int, primary_metric: float, secondary_metric: float) -> str:
    hw = mp.cpu_count()
    payload = f"{task_id}|{student_seed}|{hw}|{primary_metric:.4f}|{secondary_metric:.4f}"
    sig = fnv1a_hash(payload)
    return f"VERIFY_HASH[{task_id}]: {sig:016X} (P_log={hw})"
