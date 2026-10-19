# Method sources and contribution boundary — v1.1.0

The mean–CVaR risk representation and the MILP solver are established methods. This revision contributes a corrected, reproducible integration and a transparent empirical comparison, not a novel risk measure or a new storage optimization method.

Rockafellar and Uryasev's CVaR representation supplies the auxiliary threshold/excess-loss objective. The exact empirical fixed-mass estimator is additionally verified against an independent LP in `tests/test_cvar.py`: [Optimization of Conditional Value-at-Risk (2000), author copy](https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf).

SciPy supplies the mixed-integer interface, including explicit integrality and bounds: [official `scipy.optimize.milp` documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html). The underlying solver is [HiGHS](https://highs.dev/). Local experiments used SciPy 1.17.0.

Common Gaussian factors, quantile interpolation and clipped interval-width scaling are transparent scenario heuristics. This benchmark does not prove calibrated joint paths or conformal guarantees for decisions. The oracle uses future prices. The timing record does not establish operational day-ahead forecast availability.

The original broader literature map remains at `historical_v102/RELATED_WORK.md`, with its original scope and bibliography. The corrected report relies on the directly relevant primary method sources above; it makes no first-of-its-kind claim.
