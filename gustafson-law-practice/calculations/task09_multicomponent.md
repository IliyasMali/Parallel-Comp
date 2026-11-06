# Task 09 — Composite serial fraction

The serial phases add: I/O and broadcast `2%` plus boundary synchronization `6%`, so

`a = 0.02 + 0.06 = 0.08`.

The core-domain flux calculation is the parallel portion `1-a=0.92`. Gustafson's speedup is `S(P)=P-0.08(P-1)`.

| P | Calculation | S(P) |
|---:|---|---:|
| 512 | `512 - 0.08 × 511` | 471.12 |
| 2,048 | `2,048 - 0.08 × 2,047` | 1,884.24 |

This assumes the stated 2% and 6% are disjoint shares of the same normalized parallel runtime. If the measurements overlap, the two percentages must not simply be added.
