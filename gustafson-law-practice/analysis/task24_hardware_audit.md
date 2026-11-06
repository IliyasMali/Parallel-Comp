# Task 24 — Hardware audit and measured/theoretical gap

## Host

The benchmark host is a MacBook Air with Apple M3, macOS 15.2 arm64, Python 3.13.2, NumPy 2.5.4, and 8 GiB unified memory. System telemetry reports eight physical cores and eight logical threads. Apple's product specification describes four performance cores plus four efficiency cores and 100 GB/s memory bandwidth. The operating-system report does not expose a memory-channel count, so this audit records bandwidth but does not infer channels.

The M3's cache topology is not fully specified in Apple's product sheet. Public third-party estimates report a 16 MB L2 shared by the performance-core cluster, a 4 MB L2 shared by the efficiency-core cluster, and an 8 MB system-level cache. These are approximate cluster-level values, not per-core L3 sizes. Apple Silicon's shared system cache is not directly equivalent to a conventional x86 per-core L3.

## Measurements

Five runs were collected at every worker count from 1 through 8, with 300,000 elements per worker and five kernel repetitions. The fitted Gustafson fraction was `alpha_observed=1.108025`, outside the physical interval `[0,1]`; the constrained-form model fit had `R²=-13.355103`. Mean speedup rose from 0.2504 at P=2 to 0.5154 at P=7, then fell to 0.4722 at P=8. At P=8, speedup standard deviation was 0.0901, substantially larger than at P=2–7. Thus the simple constant-serial-fraction curve does not describe these measurements well.

Pool startup dominates the smallest runs: P=1's measured pool time averaged 0.062387 s, versus 0.008347 s for the equivalent sequential work. At higher P, process dispatch, NumPy array allocation, shared-cache pressure, and memory traffic all contribute. Apple's 100 GB/s figure is peak specification, not measured bandwidth; this benchmark did not use hardware counters to prove DRAM saturation.

The M3 uses unified memory and the OS reports no NUMA node boundary for this machine. Temperature and frequency were not recorded, so thermal throttling cannot be confirmed. The high P=8 variability could reflect scheduling, contention, or thermal state, but attributing it to one cause would require additional telemetry.

## Evidence and limits

- Raw observations: `benchmarks/weak_scale_bench/results.csv` (40 runs).
- Summary and regression: `benchmarks/weak_scale_bench/fit_report.md` and `fit_summary.json`.
- Plot: `plots/scaling_comparison.png`.
- Apple M3 core and memory-bandwidth specifications: [Apple MacBook Air M3 technical specifications](https://support.apple.com/en-us/118551).
- Cache sizes are third-party estimates: [EveryMac M3 specifications](https://everymac.com/systems/apple/macbook_pro/specs/macbook-pro-m3-8-core-cpu-10-core-gpu-14-late-2023-specs.html), [HMC M3 specifications](https://hmc-tech.com/cpus/apple-m3-8c10g).
