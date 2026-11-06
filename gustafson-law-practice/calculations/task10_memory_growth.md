# Task 10 — Memory-limited 3D grid dimensions

With a strict per-node memory cap of 32 GB and `P` nodes, total memory is `32×10^9 P` bytes. Let `b` be bytes stored per grid cell. For a cubic grid, `bN^3 ≤ 32×10^9P`, hence

`N_max(P) = floor[(32×10^9 P / b)^(1/3)]`.

The prompt does not specify bytes per cell. The table uses one 64-bit scalar (`b=8`) and decimal GB; real solvers need additional storage for state variables, halos, and work arrays, so these are upper bounds.

| Nodes P | Aggregate cap | Max cells (float64) | Approx. N per cube edge |
|---:|---:|---:|---:|
| 64 | 2,048 GB | 256,000,000,000 | 6,349 |
| 512 | 16,384 GB | 2,048,000,000,000 | 12,699 |

Increasing nodes eightfold increases available memory eightfold and therefore permits the cube edge to double (`N∝P^(1/3)`). For a general cell size, use the formula above rather than assuming float64.
