# Task 19 — Monte Carlo as an ideal weak-scaling workload

Independent Monte Carlo paths are nearly embarrassingly parallel. If each worker generates and evaluates a fixed number `k` of paths, increasing `P` yields `Pk` samples while leaving local compute approximately constant. With negligible communication, Gustafson predicts speedup close to `P` and efficiency near 1.

Nonzero serial/overhead terms include initialization, allocating path buffers, seed-stream setup, combining partial sums, and writing results. Independent, reproducible random streams require careful seed or counter-based generator partitioning; naively reusing the same seed can duplicate samples. A tree reduction of one partial sum per worker has `Θ(log P)` stages and usually small data volume, while centralized collection can create a synchronization bottleneck. Output serialization can become significant if every path is written rather than reduced to summary statistics.

For fixed local sample count `k`, useful computation grows as `Θ(Pk)`. A logarithmic reduction adds latency that grows slowly with `P`, so its share can shrink relative to fixed local work; a centralized serialized collector may instead limit scaling.
