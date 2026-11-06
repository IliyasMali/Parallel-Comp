# Task 13 — When Gustafson's assumptions fail

Gustafson's ideal result requires the parallel work to grow with `P` while elapsed parallel time remains approximately fixed. Two concrete workloads violate that premise in different ways.

## Distributed breadth-first search on a power-law graph

Adding vertices and edges does not guarantee balanced work per worker. A frontier may contain a small number of high-degree hubs, while most vertices are inactive. Workers then wait at level-synchronous barriers for the slowest partition. Cut edges require remote frontier updates, and irregular adjacency-list accesses produce cache misses. Problem size may grow linearly but the active frontier, communication volume, and imbalance need not. Runtime rises even when total work expands.

## Direct all-pairs N-body simulation

The force calculation costs `Θ(N²)`. If particle count `N` were increased linearly with processor count to mimic Gustafson's workload expansion, total work would grow as `Θ(P²)`, not `Θ(P)`, and time per core would rise. To keep the force calculation constant-time on `P` processors, one would instead need `N∝sqrt(P)` under ideal distribution. Global particle exchange, tree construction (for accelerated methods), and synchronization add costs that can also grow with `N`.

Both examples require a model that includes algorithmic complexity, communication, and load balance, rather than assuming a constant serial fraction and linear work expansion.
