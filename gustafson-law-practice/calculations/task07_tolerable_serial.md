# Task 07 — Maximum tolerable serial fraction

Given `P=8,192` and the requirement `S(P) ≥ 7,500`, Gustafson's formula gives

`P-a(P-1) ≥ 7,500`.

Rearrange:

`a(P-1) ≤ P-7,500`,

`a ≤ (8,192-7,500)/(8,192-1) = 692/8,191 ≈ 0.0844829691`.

The maximum allowable parallel serial fraction is therefore **about 8.4483%**. At the boundary, `S=7,500`; any larger fraction misses the requirement.
