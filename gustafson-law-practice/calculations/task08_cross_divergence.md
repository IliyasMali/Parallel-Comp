# Task 08 — Amdahl/Gustafson comparison at P=128

Let `s=a=0.08`.

**Amdahl, fixed work:**

`S_A = 1/[s+(1-s)/P]`

`= 1/[0.08+0.92/128] = 1/0.0871875 ≈ 11.469534`.

**Gustafson, scaled work:**

`S_G = P-a(P-1) = 128-0.08(127) = 117.84`.

The absolute difference is `117.84-11.469534 ≈ 106.370466`. Relative to Amdahl's prediction, the discrepancy is

`(S_G-S_A)/S_A × 100% ≈ 927.42%`.

Equivalently, the Amdahl result is 90.27% below the Gustafson result when the latter is used as the denominator. These large percentages arise because the models answer different questions: the first holds total work fixed; the second expands the parallel work while retaining a fixed-time parallel execution.
