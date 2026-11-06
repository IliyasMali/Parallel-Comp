# Task 18 — Direct N-body vs. Barnes–Hut

## Direct all-pairs method

An iteration costs `Θ(N²)`. With ideal distribution over `P` processors, compute time is `Θ(N²/P)`. Holding that time constant implies `N=Θ(P^(1/2))`, not `Θ(P)`. A linear particle-count expansion would make work grow quadratically and violate Gustafson's constant-time premise. A serial `Θ(N)` setup or input phase grows as `P^(1/2)` under this scaling, so it can eventually dominate unless it is parallelized too.

## Barnes–Hut tree method

The common expected work is `Θ(N log N)`, with a tree-construction phase and irregular traversals. Constant compute time on `P` processors requires `N log N=Θ(P)`, or approximately `N=Θ(P/log P)` (more precisely, `N` is proportional to `P/W(P)` where `W` here denotes Lambert's W function). This is closer to linear than the direct method, but less than linear. Serial or poorly balanced tree construction, remote tree access, and data-dependent traversal can raise the serial/communication share as the problem grows.

The asymptotic workload laws differ, so the same processor increase cannot imply the same particle-count expansion in both algorithms. Direct N-body has regular all-pairs compute with high communication potential; Barnes–Hut reduces arithmetic but adds irregular data structures and synchronization. Actual ratios depend on implementation and distribution.
