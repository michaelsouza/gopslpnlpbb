# Issue 18 Matched-Budget GOPS Runs

GitHub issue: `michaelsouza/gopslpnlpbb#18`

Run id: `issue18-matched-budget-20260703T115137Z`

Commit: `77bb8f6aeefc0986f93c5280faea521f30439790`

Host: `labma-sol`

Runner mode: `lpnlpbb`

Gurobi license file: `/home/michael/opt/gurobi1302/gurobi.lic`

## Time Budget

These runs replace the earlier 60-second smoke/final artifacts for the
comparative conclusion. The time limits were rounded up from the EPANET-BB
paper runtimes:

| Case | NA_max | EPANET-BB paper runtime | GOPS time limit |
| ---- | ------ | ----------------------- | --------------- |
| `atm-24h-na1` | 1 | `3.69s` | `5s` |
| `atm-24h-na2` | 2 | `493.11s` | `500s` |
| `atm-24h-na3` | 3 | `10011.23s` | `10020s` |

## Outcome

All three runs used the explicit academic Gurobi license on `labma-sol`.
`NA_max = 2` and `NA_max = 3` produced complete commanded GOPS schedules and
were evaluated by the EPANET-BB fixed-schedule audit path. `NA_max = 1` still
timed out without a GOPS incumbent schedule under its matched 5-second budget.

| Case | Status | Solver objective | Bound | Gap | Solutions | Gurobi runtime | Schedule | Audit |
| ---- | ------ | ---------------- | ----- | --- | --------- | -------------- | -------- | ----- |
| `atm-24h-na1` | `time_limit_no_schedule` | none | `335.1473651125699` | `inf` | 0 | `5.002s` | none | none |
| `atm-24h-na2` | `time_limit_with_schedule` | `355.6628272193992` | `339.4903372923342` | `4.5471%` | 3 | `501.640s` | `schedule.json` | `audit.json` |
| `atm-24h-na3` | `time_limit_with_schedule` | `356.8842681578085` | `339.1549739258375` | `4.9678%` | 5 | `10023.349s` | `schedule.json` | `audit.json` |

## Audit Results

| Case | Feasible | Audit effective cost | Temporary closures | Zero-flow commanded-on | Tank clamps | Tank boundary contacts |
| ---- | -------- | -------------------- | ------------------ | ---------------------- | ----------- | ---------------------- |
| `atm-24h-na2` | `true` | `4301.814242845227` | 0 | 0 | 0 | 0 |
| `atm-24h-na3` | `true` | `4379.529815587469` | 0 | 0 | 0 | 0 |

The audit metadata records:

- `method = "GOPS LP-NLP branch-and-bound"`
- `network_file = "networks/any-town.inp"`
- `h_max = 24`
- `hydraulic_timestep_seconds = 1800`
- `zero_flow_threshold = 1e-6`

## Artifact Paths

| Case | Run manifest | Solver log | Schedule | Audit |
| ---- | ------------ | ---------- | -------- | ----- |
| `atm-24h-na1` | `output/epanet_bb_equivalent_gops/atm-24h-na1/issue18-matched-budget-20260703T115137Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na1/issue18-matched-budget-20260703T115137Z/solver.log` | none | none |
| `atm-24h-na2` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-matched-budget-20260703T115137Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-matched-budget-20260703T115137Z/solver.log` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-matched-budget-20260703T115137Z/schedule.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-matched-budget-20260703T115137Z/audit.json` |
| `atm-24h-na3` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-matched-budget-20260703T115137Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-matched-budget-20260703T115137Z/solver.log` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-matched-budget-20260703T115137Z/schedule.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-matched-budget-20260703T115137Z/audit.json` |

## Notes

The earlier 60-second run id `issue18-final-academic-clean-20260703T110430Z`
remains a preliminary negative artifact only. It is not sufficient for the
final comparison for `NA_max = 2` or `NA_max = 3`; both cases produced
audit-feasible schedules when allowed the matched budget.

The `NA_max = 1` manifest records `git.dirty = false`. The `NA_max = 2` and
`NA_max = 3` manifests record `git.dirty = true` because previous output
artifacts from this same matched-budget battery were already present in the
remote worktree during the serial execution. The recorded source commit is the
same for all three runs.
