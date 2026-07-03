# Issue 19 GOPS vs EPANET-BB Paper Comparison

GitHub issue: `michaelsouza/gopslpnlpbb#19`

Source run id: `issue18-matched-budget-20260703T115137Z`

This note compares the EPANET-BB-equivalent GOPS adaptation against the EPANET-BB paper schedule artifacts. It is not a direct Bonvin public-artifact reproduction and must not be merged with the Bonvin public-artifact sufficiency conclusion.

## Summary

| Case | NA_max | GOPS status | Schedule | GOPS audit cost | Souza2026 cost | Cost delta | Cost delta % | GOPS runtime | Souza2026 runtime | Runtime delta % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| atm-24h-na1 | 1 | `time_limit_no_schedule` | `none` | n/a | 3567.989 | n/a | n/a | 5.002 | 3.692 | 35.487% |
| atm-24h-na2 | 2 | `time_limit_with_schedule` | `complete_commanded_schedule` | 4301.814 | 3472.891 | 828.923 | 23.868% | 501.64 | 493.114 | 1.729% |
| atm-24h-na3 | 3 | `time_limit_with_schedule` | `complete_commanded_schedule` | 4379.530 | 3443.459 | 936.071 | 27.184% | 10023.349 | 10011.229 | 0.121% |

Interpretation:

- `NA_max = 1` timed out under the matched 5-second budget without a complete GOPS commanded schedule, so no audit-compatible GOPS cost exists for that case.
- `NA_max = 2` and `NA_max = 3` produced complete commanded schedules and EPANET-BB audit artifacts, but their audited effective costs are higher than the corresponding Souza2026 paper schedules.
- GOPS solver schedule costs are recorded in the JSON comparison as GOPS-run objective evidence; the table above uses EPANET-BB audit effective cost when a schedule was audited.

## Paper Context

The downstream source material contains schedule JSON artifacts for Costa2016, Cimorelli2020, Paola2025, and Souza2026 for each `NA_max` case:

| Method | NA_max | Paper cost | Runtime s | Artifact |
| --- | --- | --- | --- | --- |
| Costa2016 | 1 | 3916.980 | 425 | `paper/data/run_Costa2016_a_01.json` |
| Cimorelli2020 | 1 | 3634.670 | 663 | `paper/data/run_Cimorelli2020_a_01.json` |
| Paola2025 | 1 | 3911.520 | 72 | `paper/data/run_Paola2025_a_01.json` |
| Souza2026 | 1 | 3567.989 | 3.692 | `paper/data/run_Souza2026_a_01.json` |
| Costa2016 | 2 | 3618.590 | 36914 | `paper/data/run_Costa2016_a_02.json` |
| Cimorelli2020 | 2 | 3580.110 | 663 | `paper/data/run_Cimorelli2020_a_02.json` |
| Paola2025 | 2 | 3606.220 | 904 | `paper/data/run_Paola2025_a_02.json` |
| Souza2026 | 2 | 3472.891 | 493.114 | `paper/data/run_Souza2026_a_02.json` |
| Costa2016 | 3 | 3578.670 | 292032.000 | `paper/data/run_Costa2016_a_03.json` |
| Cimorelli2020 | 3 | 3575.540 | 663 | `paper/data/run_Cimorelli2020_a_03.json` |
| Paola2025 | 3 | 3577.400 | 960 | `paper/data/run_Paola2025_a_03.json` |
| Souza2026 | 3 | 3443.459 | 10011.229 | `paper/data/run_Souza2026_a_03.json` |

## Schedule Behavior

| Case | NA_max | GOPS pump-hours | Souza pump-hours | best_y diff | best_x diff | matching y slots | GOPS peak | GOPS off hours |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| atm-24h-na1 | 1 | n/a | 27 | n/a | n/a | n/a | n/a | n/a |
| atm-24h-na2 | 2 | 27 | 32 | 15 | 35 | 10 | 2 | 1 |
| atm-24h-na3 | 3 | 27 | 33 | 14 | 20 | 11 | 2 | 4 |

The `best_y` and `best_x` differences compare GOPS schedules to the corresponding Souza2026 schedule artifact. The initial h=0 all-off slot is included in both vectors.

### Per-Pump Commanded Schedules

| Case | NA_max | Pump | GOPS h1-h24 | Souza2026 h1-h24 |
| --- | --- | --- | --- | --- |
| atm-24h-na1 | 1 | 111 | n/a | `111111100000000000000111` |
| atm-24h-na1 | 1 | 222 | n/a | `000011111111111100000000` |
| atm-24h-na1 | 1 | 333 | n/a | `000000000000011111000000` |
| atm-24h-na2 | 2 | 111 | `100000000000000011110011` | `111000000000011110001111` |
| atm-24h-na2 | 2 | 222 | `001000000001110000000000` | `111111111111000110000000` |
| atm-24h-na2 | 2 | 333 | `011111111111111100000100` | `000000111111000010000000` |
| atm-24h-na3 | 3 | 111 | `100001111001100000000000` | `100000111111000010000000` |
| atm-24h-na3 | 3 | 222 | `111000000000001110111000` | `111000000000011110001100` |
| atm-24h-na3 | 3 | 333 | `010000011111111000000110` | `111111111111000110000110` |

## Audit Events

| Case | Audit feasible | Temporary closures | Commanded-on temp closed | Commanded-on zero flow | Tank clamps | Tank boundary contacts |
| --- | --- | --- | --- | --- | --- | --- |
| atm-24h-na1 | n/a | n/a | n/a | n/a | n/a | n/a |
| atm-24h-na2 | true | 0 | 0 | 0 | 0 | 0 |
| atm-24h-na3 | true | 0 | 0 | 0 | 0 | 0 |

## Modeling And Source-Of-Truth Notes

- Scope: EPANET-BB-equivalent GOPS adaptation on the AnyTown Modified paper assumptions, not a direct reproduction of Bonvin public GOPS artifacts.
- Source priority: when manuscript prose conflicts with executable code or published schedule JSONs, the comparison target is the operative code/artifact behavior.
- Activation semantics: separate per-pump start and stop budgets, each equal to `NA_max`; the explicit h=0 to h=1 initialization transition is represented but not charged.
- Pump order: `best_x` uses `[111, 222, 333]`, even though INP pump rows use a different source order.
- Network wording mismatch: the operative INP contains 41 pipe rows plus 3 pump rows, not 44 pipe rows.
- The GOPS translated pump physics and source/tank representation are experiment assumptions recorded in the translation docs and run artifacts.

## Remote Execution Provenance

| Case | Host | Class | Commit | Dirty | Gurobi | License | Time limit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| atm-24h-na1 | labma-sol | `final` | `77bb8f6aeefc` | false | 13.0.2 | valid | 5 |
| atm-24h-na2 | labma-sol | `final` | `77bb8f6aeefc` | true | 13.0.2 | valid | 500 |
| atm-24h-na3 | labma-sol | `final` | `77bb8f6aeefc` | true | 13.0.2 | valid | 10020.000 |

Dirty-worktree note: the matched-budget summary records that `NA_max = 2` and `NA_max = 3` were serial remote runs after prior output artifacts from the same battery had already been written; all three matched-budget runs share the same source commit.

## Artifact Paths

| Case | Run manifest | Schedule | Audit |
| --- | --- | --- | --- |
| atm-24h-na1 | `output/epanet_bb_equivalent_gops/atm-24h-na1/issue18-matched-budget-20260703T115137Z/run.json` | none | none |
| atm-24h-na2 | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-matched-budget-20260703T115137Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-matched-budget-20260703T115137Z/schedule.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-matched-budget-20260703T115137Z/audit.json` |
| atm-24h-na3 | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-matched-budget-20260703T115137Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-matched-budget-20260703T115137Z/schedule.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-matched-budget-20260703T115137Z/audit.json` |

Machine-readable comparison: `output/epanet_bb_equivalent_gops/issue19-matched-budget-comparison.json`
