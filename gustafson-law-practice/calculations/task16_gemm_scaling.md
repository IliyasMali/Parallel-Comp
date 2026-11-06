# Task 16 — Dense GEMM dimension growth

For dense `N×N` matrix multiplication, work is `Θ(N³)` while memory is `Θ(N²)`. Under Gustafson's fixed-time assumption, aggregate useful work should scale proportionally with processor count:

`N(P)^3 ∝ P`.

Therefore `N(P) ∝ P^(1/3)`. Relative to a baseline dimension `N_1` at one processor,

`N(P)=N_1 P^(1/3)`.

Doubling the matrix dimension increases arithmetic work eightfold and matrix storage fourfold. The work can thus expand linearly with `P` by increasing matrix dimension only with the cube root of `P`, subject to memory capacity, communication, and the GEMM implementation's ability to retain compute efficiency.

| P | N(P)/N₁ |
|---:|---:|
| 1 | 1.000 |
| 8 | 2.000 |
| 64 | 4.000 |
| 512 | 8.000 |
