# Research audit reconciliation, 2026-09-25

The supplied handoff and complete audit were read before selecting work. The
live repository, not the report's older PR snapshot, determines current status.

| Finding class | Decision and action |
|---|---|
| Already implemented | PRs #13/#14 were already merged and main's run 36134631550 passed. Passive selected-component study, immutable result values, MCScap provenance, strict tooling, Hypothesis and native CI were retained, not re-added. |
| Relevant/actionable now | #15 generation-bound artifacts implemented in PR #19; its exact-head run 36165609993 passed before merge 59cb94de2af9808b61a81d777e62a37538ac094a. The first bounded BIAS linear model is PR #20, advancing #17 without claiming all nonlinear/physical work complete. |
| Useful later | TPS7A20 compatibility pilot; EVM firmware-source mining; exact schematic/ERC; explicit S3 target compile; settling-data semantics when live reconfiguration exists. These were not falsely described as completed by the BIAS increment. |
| Redundant | Another type checker, second simulator wrapper, general workflow/electrode/DDD framework, mandatory whole-repository mutation gate. No dependency added. |
| Unsupported/too speculative | A calibrated MCScap contact/noise/cable model from family limits; full ADS1299 silicon emulation; physical stability or body-use approval from numerical agreement. Rejected as current claims. |

The research changed execution order: run identity directly threatened the
meaning of simulation evidence, so it was addressed before adding BIAS. The
existing passive solver remains unchanged; the new coupled BIAS circuit has a
small explicit nodal formulation and reuses the existing ngspice process boundary.

One material additional primary-source finding: ADS1299 Rev. C contradicts itself
on 220 kohm versus 330 kohm BIAS summing resistors. TI explicitly corrects the
latter to 220 kohm. The model/source record preserves that correction and a
published two-input limiting case. See `docs/REV_A_BIAS_STUDY.md` and its source
record for exact URLs/locators. Typical 100 kHz GBW is not promoted to guaranteed
bounds; the single-pole/open-loop-gain family and dummy loads remain assumptions.

Owned electrode suffix, actual lead length/shielding and bench equipment remain
unknown. Those did not block an explicitly unmeasured dummy-load study. Selected
ADS1299/S3 parts are not assumed purchased. All hardware/firmware/body-use gates
remain unchanged and false.
