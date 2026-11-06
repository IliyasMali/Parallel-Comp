# Task 06 — Parametric speedup table (`a=0.04`)

Use `S(P)=P-a(P-1)=0.96P+0.04` and `E(P)=S(P)/P=0.96+0.04/P`.

| P | S(P) | E(P) | Efficiency (%) |
|---:|---:|---:|---:|
| 16 | 15.40 | 0.962500 | 96.2500 |
| 64 | 61.48 | 0.960625 | 96.0625 |
| 256 | 246.28 | 0.960156 | 96.0156 |
| 1,024 | 983.08 | 0.960039 | 96.0039 |
| 4,096 | 3,932.20 | 0.960010 | 96.0010 |
| 16,384 | 15,728.68 | 0.960002 | 96.0002 |

As `P` grows, efficiency approaches `1-a=0.96` from above. The serial runtime is amortized over an expanding parallel workload, but the fixed 4% serial share still limits the asymptotic efficiency to 96%.
