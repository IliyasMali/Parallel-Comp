# Task 15 — Energy and power under weak scaling

Let each active node draw static/idle power `P_idle` and additional dynamic power `P_active` while computing. With `P` nodes and elapsed time `T_P`, total energy is

`E(P)=P(P_idle+P_active)T_P`.

Under ideal Gustafson weak scaling, `T_P≈T` is constant while workload and active node count grow. Therefore `E(P)≈P(P_idle+P_active)T`, linear in `P`. The single-node case consumes `E(1)=(P_idle+P_active)T`; using `P` nodes for the same wall-clock duration consumes `P` times as much energy if per-node power is unchanged.

If only the fraction `u(P)` of each node is active, a more detailed model is `E(P)=P[P_idle+u(P)P_active]T_P`. Idle power is still paid by every powered-on node. Energy per unit of useful work may improve or worsen depending on the extra throughput, power-management state, and whether the larger weak-scaled problem is valuable. The comparison assumes identical elapsed time and equal node-level power; actual dynamic power is workload- and frequency-dependent.
