# Empirical weak-scaling fit

Raw measurements: 40
Least-squares Gustafson serial fraction: `alpha_observed = 1.108025`
R-squared against `S(P)=P-alpha(P-1)`: `-13.355103`

P=1 is excluded from the regression because it is the normalized baseline; its Pool startup time is still reported in the raw table. An alpha outside [0, 1] means the ideal Gustafson serial-fraction interpretation is not physically valid for this fit; process startup, communication, and timing variation can dominate measured speedup.

| P | Runs | T_parallel mean ± SD (s) | T_serial mean ± SD (s) | Speedup mean ± SD |
|---:|---:|---:|---:|---:|
| 1 | 5 | 0.062387 ± 0.000951 | 0.008347 ± 0.000120 | 0.1338 ± 0.0025 |
| 2 | 5 | 0.064670 ± 0.000924 | 0.016186 ± 0.000797 | 0.2504 ± 0.0140 |
| 3 | 5 | 0.068368 ± 0.000566 | 0.023410 ± 0.000519 | 0.3424 ± 0.0067 |
| 4 | 5 | 0.072978 ± 0.000939 | 0.030410 ± 0.000332 | 0.4168 ± 0.0077 |
| 5 | 5 | 0.083297 ± 0.001199 | 0.037951 ± 0.000619 | 0.4556 ± 0.0065 |
| 6 | 5 | 0.092068 ± 0.002288 | 0.045469 ± 0.000457 | 0.4941 ± 0.0140 |
| 7 | 5 | 0.100920 ± 0.000867 | 0.052019 ± 0.001028 | 0.5154 ± 0.0090 |
| 8 | 5 | 0.132911 ± 0.028802 | 0.060688 ± 0.001958 | 0.4722 ± 0.0901 |
