# Task 01 — Strong vs. weak scaling

## Definitions

Let `P` be the number of processing units, `W` the useful work, and `T(P,W)` the elapsed time.

**Strong (fixed-size) scaling** keeps `W` constant as `P` grows. Ideal runtime falls as `1/P`; speedup is `S_A(P)=T(1,W)/T(P,W)`. Amdahl's model with serial fraction `s` gives `S_A(P)=1/[s+(1-s)/P]`. For `s>0`, its asymptotic ceiling is `1/s`.

**Weak (fixed-time) scaling** grows the parallel work with `P`, commonly `W(P)=P W(1)`, while keeping work per processor approximately constant. If the parallel execution time is normalized to one and its serial share is `a`, Gustafson's scaled speedup is `S_G(P)=P-a(P-1)=a+(1-a)P`.

## What happens as P grows

Under strong scaling, each additional core divides the same finite parallel workload more finely. Serial work, synchronization, and communication become a larger share of elapsed time; the fixed serial fraction eventually limits speedup. Under ideal weak scaling, the aggregate problem grows with the machine, so each processor remains busy with a similar amount of parallel work. The target is nearly constant runtime, while the single-processor equivalent work grows.

## Philosophical and physical difference

Amdahl asks, “How much faster can this same job finish?” It is a useful model for latency reduction on a fixed input. Gustafson asks, “How much more useful work can this larger machine finish in the same time?” It is a throughput and capacity model. They describe different experiments, not contradictory predictions. Real weak scaling departs from ideal behavior when memory capacity, communication, synchronization, load balance, or the serial setup path fails to scale.

**Conclusion:** use Amdahl for a fixed workload and Gustafson for a workload whose parallel portion expands with available processing capacity. Always state which work and runtime form the reference.
