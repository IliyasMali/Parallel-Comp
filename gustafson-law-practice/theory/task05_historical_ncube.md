# Task 05 — Reconstructing the nCUBE result

## Historical setup

Gustafson, Montry, and Benner reported scientific applications on Sandia's 1,024-processor nCUBE hypercube: wave mechanics, fluid dynamics, and structural analysis. Their 1988 paper reported measured fixed-problem speedups of 502–637 and scaled speedups of 1,009–1,020. The scaled result is a throughput comparison: the 1,024-processor machine did roughly 1,009–1,020 times the work of one processor in comparable elapsed time by solving a larger problem.

## Why the number can exceed Amdahl's apparent ceiling

The fixed-size and scaled experiments have different work definitions. Amdahl's law holds total work constant; scaled speedup holds execution time approximately constant while expanding parallel work. The nCUBE result therefore does not violate Amdahl's law. It answers a different question. The authors also discuss communication and serial overhead and introduce operation efficiency, so the measurements should not be reduced to an idealized formula alone.

For scale, the ideal Gustafson inversion `a=(P-S)/(P-1)` at `P=1024` maps the reported scaled-speedup endpoints to approximately 1.466% (`S=1009`) and 0.391% (`S=1020`). These are equivalent model fractions inferred from the formula, not a claim that every application had one identical measured serial fraction.

The fixed-size speedups are smaller because the amount of useful work is held constant while processor count rises, leaving less work per processor and exposing communication, load imbalance, and serial work. The scaled speedups reflect larger scientific runs that use the full machine productively.

## Source

Gustafson, J. L., Montry, G. R., and Benner, R. E. “Development of Parallel Methods for a 1024-Processor Hypercube.” *SIAM Journal on Scientific and Statistical Computing* 9(4), 609–638 (1988). [Full paper](https://rsim.cs.illinois.edu/arch/qual_papers/systems/6.pdf).
