# Issue 20 Longer-Budget GOPS-Equivalent Comparison

GitHub issue: `michaelsouza/epanet-bb#20`

This note records the longer-budget EPANET-BB-equivalent GOPS adaptation
experiments requested by issue #20. These runs are not a direct reproduction of
the Bonvin et al. public artifacts and must not be presented as a Bonvin
benchmark row.

## Outcome

The LabMA attempts reached the GOPS environment but could not solve the model
because the available license was size-restricted and the expected academic
license was not readable on `labma-sol`. The successful fallback runs used the
academic Gurobi license on `DESKTOP-JC3R64S`.

The common 6-hour local campaign produced complete schedules for `NA_max = 1`
and `NA_max = 2`. The 6-hour `NA_max = 3` run produced no schedule. A subsequent
72-hour cold run for `NA_max = 3` was interrupted by a Windows restart after
about 13.5 hours. The replacement 72-hour cold run completed at the time limit
and exported a complete schedule.

All three exported schedules were audited post hoc with the EPANET-BB
fixed-schedule clamp auditor using a zero-flow threshold of `1e-6 cfs`.

## Solver Results

| Case | Budget | Threads | Start | GOPS status | Runtime (s) | GOPS objective | GOPS bound | Gap | Nodes | Reported real cost |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `atm-24h-na1` | 6 h | 8 | warm start rejected | `success` | 5,837.226 | 355.662823 | 355.662823 | 0.000% | 214,688 | 455.104705 |
| `atm-24h-na2` | 6 h | 8 | warm start rejected | `time_limit_with_schedule` | 21,601.747 | 355.662827 | 339.852602 | 4.445% | 488,297 | 455.511793 |
| `atm-24h-na3` | 72 h | 24 | cold | `time_limit_with_schedule` | 259,215.402 | 355.016475 | 339.398804 | 4.399% | 2,508,800 | 446.961202 |

The `GOPS objective`, `GOPS bound`, and solver gap belong to the internal GOPS
optimization scale. `Reported real cost` is the GOPS callback cost associated
with the exported commanded schedule. Neither field is the common EPANET-BB
audit cost.

## Common EPANET-BB Audit

| Case | Feasible | Audit effective cost | Tank boundary contacts | Tank clamps | Temporary closures | Commanded-on temp closed | Commanded-on zero flow |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `atm-24h-na1` | true | 4,300.753 | 0 | 0 | 0 | 0 | 0 |
| `atm-24h-na2` | true | 4,306.508 | 0 | 0 | 0 | 0 | 0 |
| `atm-24h-na3` | true | 4,223.968 | 0 | 0 | 0 | 0 | 0 |

The audit classifies all three schedules as feasible for actuation, pressure,
tank level, stability, and hydraulic timestep checks. Under the instrumented
EPANET-BB semantics, none of these GOPS schedules materially relies on an
observed tank clamp, tank-boundary contact, temporary link closure, or
commanded-on zero-flow event.

This supports an EPANET-simulated-feasibility statement for these schedules. It
does not establish a stronger simulator-independent commanded-operation
feasibility theorem.

## Comparison With Souza2026 Paper Schedules

| Case | GOPS audit effective cost | Souza2026 effective cost | GOPS minus Souza2026 | Delta |
| --- | ---: | ---: | ---: | ---: |
| `atm-24h-na1` | 4,300.753 | 3,567.989 | 732.764 | 20.537% |
| `atm-24h-na2` | 4,306.508 | 3,472.891 | 833.617 | 24.003% |
| `atm-24h-na3` | 4,223.968 | 3,443.459 | 780.509 | 22.666% |

The longer GOPS budgets do not overturn the paper-facing cost ordering under the
common EPANET-BB evaluator. The GOPS-equivalent adaptation produces feasible,
clamp-free commanded schedules, but their effective costs remain materially
higher than the corresponding Souza2026 schedules.

For `NA_max = 3`, the 72-hour run improves the matched-budget GOPS audit cost
from 4,379.530 to 4,223.968, a reduction of about 3.552%, while remaining about
22.666% above Souza2026. The 72-hour solver gap is still 4.399%, so this run does
not certify a GOPS optimum.

For `NA_max = 1`, GOPS closes its internal model gap to zero. This establishes
optimality only for the implemented GOPS-equivalent adaptation and its objective
scale. It is not evidence that EPANET-BB's aggregate reconstruction preserves
optimality for the original binary pump-status formulation.

## Execution Provenance

| Case | Host | Run ID | Commit | Dirty | Gurobi | License | Schedule audit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `atm-24h-na1` | `DESKTOP-JC3R64S` | `local-windows-academic-p4-20260713T1545Z` | `efde81d2309779c83e0ec40e2a609bc2726785b1` | true | 13.0.2 | valid academic | post hoc, succeeded |
| `atm-24h-na2` | `DESKTOP-JC3R64S` | `local-windows-academic-p4-20260713T1545Z` | `efde81d2309779c83e0ec40e2a609bc2726785b1` | true | 13.0.2 | valid academic | post hoc, succeeded |
| `atm-24h-na3` | `DESKTOP-JC3R64S` | `local-windows-academic-p6-na3-72h-20260715T185850Z` | `efde81d2309779c83e0ec40e2a609bc2726785b1` | true | 13.0.2 | valid academic | post hoc, succeeded |

The manifests record a dirty worktree. The solver source commit and run artifacts
remain explicit, but this condition must be retained in any reproducibility
claim rather than silently reporting a clean final run.

## Attempt History

- `issue20-six-hour-warm-p1-20260713T1457Z`: LabMA environment blocked because
  the system Python lacked `gurobipy`.
- `issue20-six-hour-warm-p2-20260713T1500Z`: LabMA virtualenv reached Gurobi
  13.0.2, but the model exceeded the available size-restricted license.
- `local-windows-academic-p4-20260713T1545Z`: common 6-hour local runs;
  `NA_max = 1` solved, `NA_max = 2` timed out with a schedule, and `NA_max = 3`
  timed out without a schedule.
- `local-windows-academic-p5-na3-72h-20260714T0900Z`: cold 72-hour local attempt
  interrupted by a Windows restart after about 13.5 hours; no final manifest or
  resumable checkpoint.
- `local-windows-academic-p6-na3-72h-20260715T185850Z`: replacement cold 72-hour
  run; timed out with a complete schedule.

## Artifact Paths

| Case | Run manifest | Schedule | Post-hoc audit |
| --- | --- | --- | --- |
| `atm-24h-na1` | `output/epanet_bb_equivalent_gops/atm-24h-na1/local-windows-academic-p4-20260713T1545Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na1/local-windows-academic-p4-20260713T1545Z/schedule.json` | `output/epanet_bb_equivalent_gops/atm-24h-na1/local-windows-academic-p4-20260713T1545Z/audit.json` |
| `atm-24h-na2` | `output/epanet_bb_equivalent_gops/atm-24h-na2/local-windows-academic-p4-20260713T1545Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/local-windows-academic-p4-20260713T1545Z/schedule.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/local-windows-academic-p4-20260713T1545Z/audit.json` |
| `atm-24h-na3` | `output/epanet_bb_equivalent_gops/atm-24h-na3/local-windows-academic-p6-na3-72h-20260715T185850Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/local-windows-academic-p6-na3-72h-20260715T185850Z/schedule.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/local-windows-academic-p6-na3-72h-20260715T185850Z/audit.json` |

## Issue 20 Conclusion

The longer-budget experiment answers the issue's main question. GOPS can produce
complete audit-compatible schedules for all three `NA_max` cases when given
sufficient local runtime. The common audit finds all three schedules feasible
and detects no clamp-related events. Additional runtime improves the
`NA_max = 3` GOPS result but does not make the adapted GOPS schedules competitive
with the Souza2026 effective costs under the same EPANET-BB evaluator.

The reviewer-facing use of this evidence should therefore be methodological and
qualified: Bonvin remains the closest relaxation-based exact comparator, the
executed model is an EPANET-BB-equivalent GOPS adaptation rather than a direct
Bonvin reproduction, and the longer run does not alter the paper's numerical
ordering.
