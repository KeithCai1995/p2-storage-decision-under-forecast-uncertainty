# Related work and contribution boundary

This note positions the portfolio against representative primary research. It is an
application-level literature map, not a systematic review and not proof that no similar
work exists.

## Closest strands

| Strand | Representative work | Consequence for this portfolio |
|---|---|---|
| CVaR optimisation | Rockafellar and Uryasev (2000) | The linear mean-CVaR formulation is established and is used as a transparent baseline. |
| Decision-focused learning | Donti, Amos and Kolter (2017); Elmachtoub and Grigas (2022) | Predictive loss and downstream decision loss can differ; decision value is not a new observation. |
| Stochastic storage scheduling | Kim, Sioshansi and Conejo (2020) | Storage scheduling under price uncertainty is an established research area. |
| Probabilistic guarantees for storage markets | Toubeau et al. (2021) | Risk-aware storage participation can incorporate probabilistic constraints and richer market stages. |
| Decision-aware conformal optimisation | Yeh et al. (2024) | Conformal uncertainty has already been connected to downstream optimisation. |
| Conformal uncertainty for storage arbitrage | Alghumayjan, Yi and Xu (2025) | The portfolio cannot claim the first conformal or risk-averse storage application. |

## Narrow contribution

The portfolio contributes a compact and inspectable research-training benchmark that:

- passes Project 1 forecast distributions into an explicit linear battery model;
- compares risk-neutral and mean-CVaR schedules using the same information set;
- reports realised benchmark profit, regret, tail loss and feasibility together;
- includes an unattainable oracle only as an information upper bound; and
- documents negative results, sensitivity and deployment gaps.

The portfolio does **not** claim a new CVaR formulation, validated joint scenarios, a
complete market-bidding model, market impact, real revenue, operational safety or live
deployment readiness.

## References

1. Rockafellar, R. T. and Uryasev, S. (2000). Optimization of Conditional Value-at-Risk. Journal of Risk, 2(3), 21-41. https://www.risk.net/journal-risk/2161159/optimization-conditional-value-risk
2. Donti, P. L., Amos, B. and Kolter, J. Z. (2017). Task-based End-to-end Model Learning in Stochastic Optimization. NeurIPS 30. https://proceedings.neurips.cc/paper/2017/hash/3fc2c60b5782f641f76bcefc39fb2392-Abstract.html
3. Elmachtoub, A. N. and Grigas, P. (2022). Smart Predict, then Optimize. Management Science, 68(1), 9-26. https://doi.org/10.1287/mnsc.2020.3922
4. Kim, H. J., Sioshansi, R. and Conejo, A. J. (2020). Benefits of Stochastic Optimization for Scheduling Energy Storage in Wholesale Electricity Markets. Journal of Modern Power Systems and Clean Energy, 8(3), 421-433. https://ieeexplore.ieee.org/document/9096503
5. Toubeau, J.-F., Bottieau, J., De Greve, Z., Vallee, F. and Bruninx, K. (2021). Data-Driven Scheduling of Energy Storage in Day-Ahead Energy and Reserve Markets With Probabilistic Guarantees on Real-Time Delivery. IEEE Transactions on Power Systems, 36(4), 2815-2828. https://ieeexplore.ieee.org/document/9305967
6. Yeh, C., Christianson, N., Wu, A., Wierman, A. and Yue, Y. (2024). End-to-end conformal calibration for optimization under uncertainty. arXiv:2409.20534. https://arxiv.org/abs/2409.20534
7. Alghumayjan, S., Yi, M. and Xu, B. (2025). Conformal uncertainty quantification of electricity price predictions for risk-averse storage arbitrage. IEEE Power & Energy Society General Meeting. https://doi.org/10.1109/PESGM52009.2025.11225098
