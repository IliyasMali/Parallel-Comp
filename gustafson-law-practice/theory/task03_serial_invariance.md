# Task 03 — The serial-fraction invariance paradox

The apparent paradox comes from using the same symbol for two fractions measured against different reference runs.

Let a `P`-processor scaled run take time `T_P = t_s + t_p`, where `t_s` is the serial portion and `t_p` the parallel portion of the elapsed time. Gustafson's serial fraction is

`a = t_s / (t_s + t_p)`.

The one-processor equivalent of this scaled workload takes `T_1 = t_s + P t_p`, so

`S_G = (t_s + P t_p)/(t_s+t_p) = P-a(P-1)`.

The serial fraction for the one-processor execution of that *expanded* problem is instead

`s_A(P) = t_s/(t_s+P t_p) = a/[a+P(1-a)] = a/S_G(P)`.

Thus the serial fraction is not invariant across the two experiments. `a` is measured on the parallel execution of the larger problem; `s_A(P)` is measured on a single processor executing that same larger problem. As the parallel work expands, the fixed serial setup becomes a smaller share of the one-processor equivalent workload. Amdahl's ceiling applies when the problem remains fixed and its serial fraction remains fixed. Gustafson's linear prediction applies when the parallel portion of the problem grows. There is no contradiction once the baseline is named.
