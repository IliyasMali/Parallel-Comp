# Task 11 — Gustafson and Sun–Ni memory-bounded speedup

Gustafson's fixed-time model scales the parallel workload to hold runtime approximately constant. Sun–Ni's memory-bounded model instead asks how much workload can fit as aggregate memory grows with the processor system. Its key extra function is `g(M)`, which maps memory capacity to the largest problem size the application can store.

For the simplified Sun–Ni model, let `a` be the serial fraction and let `G(P)=g(PM)/g(M)` be the problem-size growth permitted by increasing memory from `M` to `PM`. The speedup is

`S_MB(P)=P [G(P)+a(1-G(P))] / [G(P)+a(P-G(P))]`.

This reduces to Amdahl's fixed-size speedup when `G(P)=1`, and to Gustafson's fixed-time speedup when `G(P)=P`:

- `G=1`: `S_MB=P/[1+a(P-1)]`.
- `G=P`: `S_MB=P-a(P-1)`.

Thus Sun–Ni is a bridge between the two laws, with the memory-to-workload function determining where a real application lies. Gustafson overestimates achievable throughput if additional memory does not let the useful problem grow linearly, or if replication, communication, or metadata consume a growing fraction of memory. It can underestimate throughput when extra memory enables a more efficient algorithm or removes out-of-core I/O, allowing the problem size to grow faster than the assumed linear workload model. These outcomes depend on `g(M)` and the algorithm's memory pattern; they are not automatic consequences of having more RAM.

Source: Sun and Ni, “Another View on Parallel Speedup” (1990), and “Scalable Problems and Memory-Bounded Speedup” (1993). [1993 paper](https://www.cs.iit.edu/~scs/psfiles/Sun_and_Ni_JPDC1993.pdf).
