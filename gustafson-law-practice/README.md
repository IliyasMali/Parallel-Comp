# Gustafson's Law Practice Repository

Comprehensive practice set covering fixed-size (Amdahl), fixed-time (Gustafson), and memory-bounded (Sun–Ni) speedup; worked calculations; simulation; and empirical weak scaling on the local Apple M3 machine.

## Quick start

Requires Python 3.13, NumPy, and Matplotlib. From this folder:

```bash
python benchmarks/simulator.py
python benchmarks/weak_scale_bench/benchmark.py --runs 5 --elements-per-worker 300000 --repeats 5
python benchmarks/fit_gustafson.py
```

The simulator writes `benchmarks/generated/simulator_results.csv` and `plots/simulator_scaling.png`. The empirical benchmark writes raw measurements to `benchmarks/weak_scale_bench/results.csv` and hardware metadata to `benchmarks/weak_scale_bench/hardware.json`. The fit script writes grouped means/standard deviations, the observed serial-fraction fit, and `plots/scaling_comparison.png`.

## Repository map

### Theory

1. [Strong vs. weak scaling](theory/task01_scaling_models.md)
2. [Gustafson derivation](theory/task02_derivation.md)
3. [Serial-fraction invariance](theory/task03_serial_invariance.md)
4. [Asymptotic efficiency](theory/task04_asymptotic_limits.md)
5. [Historical nCUBE results](theory/task05_historical_ncube.md)
11. [Sun–Ni memory-bounded scaling](theory/task11_sun_ni_comparison.md)
12. [Communication penalty model](theory/task12_communication_penalty.md)
13. [Failure cases](theory/task13_failure_cases.md)
14. [Isoefficiency](theory/task14_isoefficiency.md)
15. [Energy scaling](theory/task15_energy_scaling.md)

### Calculations

6. [Parametric speedup table](calculations/task06_parametric_table.md)
7. [Maximum serial fraction](calculations/task07_tolerable_serial.md)
8. [Amdahl/Gustafson crossover](calculations/task08_cross_divergence.md)
9. [Multi-component workload](calculations/task09_multicomponent.md)
10. [Memory-limited grid sizes](calculations/task10_memory_growth.md)
16. [GEMM dimension scaling](calculations/task16_gemm_scaling.md)
17. [3D stencil surface/volume](calculations/task17_stencil_scaling.md)

### Domain analyses and empirical work

18. [N-body scaling](analysis/task18_nbody_scaling.md)
19. [Monte Carlo](analysis/task19_monte_carlo.md)
20. [Graph workloads](analysis/task20_graph_processing.md)
21. [Amdahl/Gustafson simulator](benchmarks/simulator.py)
22. [Weak-scaling benchmark and run guide](benchmarks/weak_scale_bench/README.md)
23. [Raw five-run dataset](benchmarks/weak_scale_bench/results.csv), [fit script](benchmarks/fit_gustafson.py), [fit summary](benchmarks/weak_scale_bench/fit_report.md)
24. [Hardware audit](analysis/task24_hardware_audit.md), [comparison plot](plots/scaling_comparison.png)
25. This README synthesizes the mathematical and empirical findings below.

## Executive synthesis

Gustafson's law is useful when adding processors lets the user solve a larger problem in roughly the same elapsed time. Its ideal efficiency tends to `1-a`, where `a` is the serial share of the scaled parallel run. Amdahl's law keeps the problem fixed and has efficiency tending to zero for any nonzero fixed serial fraction. Sun–Ni adds the memory limit that determines whether problem size can actually grow.

The analytic calculations show near-linear ideal scaling when `a` is modest, but real performance depends on memory, communication, load balance, and algorithm complexity. For example, an `O(N³)` GEMM problem needs only `N∝P^(1/3)` growth for work to grow linearly; direct N-body needs `N∝P^(1/2)` to keep pairwise work per processor constant.

On this MacBook Air M3, the local weak-scaling kernel did not achieve speedup above one because process startup and dispatch are large relative to each short computation. Across P=2–7, measured mean speedup rose from 0.2504 to 0.5154; at P=8 it averaged 0.4722 with high run-to-run variation. Least-squares fitting gave `alpha_observed=1.108025`, outside the physical serial-fraction interval, and poor `R²`; this is evidence that a constant-fraction Gustafson curve is a poor model for this implementation and workload, not a claim that more than 100% of work is inherently serial.

The strongest design guidance is to state the scaling model and memory constraint explicitly, amortize process launch over larger tasks, keep local work and data placement regular, reduce communication and synchronization, and report repeated measurements with variation. For real deployments, choose Gustafson scaling when users value larger solved problems, but validate that memory capacity, algorithmic complexity, and data movement grow compatibly with the machine.

## Sources

- Gustafson, Montry, and Benner (1988), [“Development of Parallel Methods for a 1024-Processor Hypercube”](https://rsim.cs.illinois.edu/arch/qual_papers/systems/6.pdf).
- Sun and Ni (1993), [“Scalable Problems and Memory-Bounded Speedup”](https://www.cs.iit.edu/~scs/psfiles/Sun_and_Ni_JPDC1993.pdf).
- Apple, [MacBook Air M3 technical specifications](https://support.apple.com/en-us/118551).
