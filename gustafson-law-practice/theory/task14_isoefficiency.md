# Task 14 — Isoefficiency under Gustafson scaling

Efficiency is `E(P,W)=S(P,W)/P`. For an ideal Gustafson workload, the parallel fraction is expanded so per-processor work remains constant. With fixed serial fraction `a`,

`E_G(P)=1-a+a/P → 1-a`.

Therefore ideal weak scaling maintains a constant asymptotic efficiency without increasing work faster than `Θ(P)`: one fixed-size local workload is assigned per processor, so total useful work is `W(P)=Θ(P)`. This is the linear isoefficiency case.

For an algorithm with overhead `T_o(P,W)`, cost is `P T_P = W + T_o`. Efficiency can be written `E=1/[1+T_o/W]`. To maintain target efficiency `E_0`, require

`W(P) ≥ T_o(P,W) / (1/E_0 - 1)`.

Thus if overhead is `Θ(P log P)`, problem work must grow at least `Θ(P log P)` to keep a fixed efficiency (up to constants); if overhead is `Θ(P^γ)`, the required isoefficiency is at least that order. A pure Gustafson `Θ(P)` expansion is insufficient when communication or synchronization overhead grows faster than `P`.
