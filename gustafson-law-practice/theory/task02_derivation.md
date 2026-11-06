# Task 02 — Derive Gustafson's scaled speedup

Let a parallel run on `P` cores take normalized time 1. Split that time into a serial portion `s` and a parallel portion `p`, so

`s + p = 1`.

The parallel portion occupies `p` time on `P` processors. If the same parallel work were executed serially, it would take `P p` time. The serial portion still takes `s`. Thus the one-processor equivalent time for the scaled problem is

`T_1(scaled) = s + P p`.

The actual `P`-processor elapsed time is `T_P(scaled)=s+p=1`. Therefore the scaled speedup is

`S(P) = T_1(scaled) / T_P(scaled) = s + P p`.

Substitute `p=1-s`:

`S(P) = s + P(1-s) = P - s(P-1)`.

If the serial fraction is written `a` instead of `s`, this is `S(P)=P-a(P-1)`. At `P=1`, `S(1)=1`; at `s=0`, `S(P)=P`; and at `s=1`, `S(P)=1`. The derivation assumes the parallel work expands with `P` while the normalized parallel runtime remains fixed. Communication and other overheads must be added to the model when that assumption fails.
