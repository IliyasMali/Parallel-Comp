# Task 20 — Graph traversal and irregular workloads

Gustafson weak scaling is difficult for BFS and PageRank because equal vertex counts do not imply equal work or communication per worker.

- **BFS:** work depends on frontier size and degree distribution. A few hubs can create uneven partitions; level-by-level synchronization forces every worker to wait for the slowest. Frontier exchange and visited-state updates cross partition boundaries.
- **PageRank:** each iteration resembles sparse matrix–vector multiplication. Irregular edge lists lead to cache misses and bandwidth-bound gathers; vertices with many incoming/outgoing edges cause load imbalance. Partition boundaries require message exchange or reductions every iteration.

As a power-law graph grows, edge cuts and high-degree hubs can grow differently from vertex count. Random access and synchronization may increase faster than local arithmetic, so a larger graph can consume more time per iteration even when edges are divided among more processors. Graph partitioning, compressed sparse formats, edge-centric layouts, asynchronous methods, and locality-aware scheduling can improve scaling, but no single linear work-expansion rule captures the behavior.
