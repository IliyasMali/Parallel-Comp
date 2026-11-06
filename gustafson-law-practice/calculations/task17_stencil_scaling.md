# Task 17 — 3D stencil surface-to-volume scaling

For a cubic grid of side `N`, interior updates cost `Θ(N³)` and the *outer* boundary area is `Θ(N²)`. If total grid volume grows proportionally with `P`, then `N³∝P`, so `N∝P^(1/3)` and the outer-boundary-to-volume ratio scales as

`N²/N³ = 1/N = Θ(P^(-1/3))`.

Under this global-domain measure, communication grows more slowly than computation and the ratio improves as the domain expands. For a distributed stencil, however, each worker also exchanges halo faces with neighboring subdomains. If local subdomain volume is held constant under weak scaling, its face area and interior work per worker are both approximately constant; per-worker halo-to-compute ratio therefore remains roughly constant, rather than falling as `P^(-1/3)`. Network topology, halo thickness, and process-grid shape determine actual traffic. Gustafson scaling alone does not guarantee reduced communication per worker.
