# Task 04 — Asymptotic efficiency

Under Gustafson's model,

`S_G(P)=P-a(P-1)=a+(1-a)P`.

Parallel efficiency is

`E_G(P)=S_G(P)/P = 1-a+a/P`.

For `0 ≤ a ≤ 1`,

`lim(P→∞) E_G(P) = 1-a`.

The proof is direct: `a/P→0`, so only the constant term `1-a` remains. This does not mean any fixed fraction of cores becomes permanently idle; it says the scaled model's useful-work rate per core approaches the parallel share of the normalized runtime.

For Amdahl's fixed-size model,

`S_A(P)=1/[a+(1-a)/P]`,

so

`E_A(P)=1/[aP+(1-a)]`.

If `a>0`, `lim(P→∞) E_A(P)=0`; if `a=0`, the limit is 1. Amdahl speedup tends to `1/a`, while Gustafson speedup grows linearly with slope `1-a`. The comparison is valid only if the distinct workload assumptions are kept explicit.
