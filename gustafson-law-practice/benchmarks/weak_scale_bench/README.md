# Weak-scaling benchmark

The benchmark uses Python multiprocessing. Every worker computes the same `k`-element slice; the aggregate input grows as `P*k`. For each configuration it measures both a sequential execution of all `P` slices and a `P`-process execution of the same expanded workload. Pool creation and shutdown are included in parallel wall time. Checksums are compared to catch partition or numeric errors.

From the practice-repository root, run five independent measurements for each process count:

```bash
python benchmarks/weak_scale_bench/benchmark.py --runs 5 --elements-per-worker 300000 --repeats 5
python benchmarks/weak_scale_bench/fit_gustafson.py
```

The first command writes raw rows to `benchmarks/weak_scale_bench/results.csv` and machine metadata to `hardware.json`. It measures every worker count from 1 through the host maximum (up to 16 unless `--max-workers` is supplied). The second groups observations, reports means and sample standard deviations, fits the Gustafson serial fraction by least squares, and generates `plots/scaling_comparison.png` plus a summary JSON. Use a quiet, plugged-in machine for comparable runs. The recorded measurements remain raw; do not delete outliers after looking at results.

Dependencies: Python 3.10+, NumPy, and Matplotlib. A memory-heavy run can be limited with `--max-workers`.
