# Task 12 — Communication-penalized Gustafson model

Let `a` be the serial fraction of the ideal parallel runtime, and measure communication time `C(P)` in units of that ideal runtime. The equivalent one-processor time for the expanded computation is `a+(1-a)P`; the actual parallel time is `1+C(P)`. A simple modified model is

`S_C(P) = [a+(1-a)P]/[1+C(P)]`.

The corresponding efficiency is

`E_C(P) = [a+(1-a)P]/[P(1+C(P))]`.

For `C(P)=c log(P)`, speedup grows approximately as `(1-a)P/(c log P)` and efficiency falls approximately as `(1-a)/(c log P)`. For `C(P)=c sqrt(P)`, speedup grows approximately as `(1-a)sqrt(P)/c` and efficiency falls approximately as `(1-a)/(c sqrt(P))`. In either case, superlinear growth of elapsed communication overhead destroys constant-runtime weak scaling at sufficiently large `P`.

This is an illustrative model, not a universal network law. `C(P)` must be measured or derived for the actual topology, message pattern, and workload. The normalization ensures `C(1)=0` so `S_C(1)=1`.
