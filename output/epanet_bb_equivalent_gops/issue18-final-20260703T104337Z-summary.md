# Issue 18 Final GOPS Runs

GitHub issue: `michaelsouza/gopslpnlpbb#18`

Run id: `issue18-final-20260703T104337Z`

Commit: `a864695f7857e8a507d4d9eea7e231f17cdddc4a`

Host: `labma-sol`

Runner mode: `lpnlpbb`

Runtime settings: `time_limit_seconds = 60`, `mip_gap = 1e-6`,
`gurobi_output = true`

## Outcome

All three EPANET-BB-equivalent GOPS final runs reached Gurobi on `labma-sol`,
but optimization was blocked by the available size-limited Gurobi license before
any complete commanded schedule could be exported.

| Case | NA_max | Run manifest | Solver log | Status | Schedule | Audit |
| ---- | ------ | ------------ | ---------- | ------ | -------- | ----- |
| `atm-24h-na1` | 1 | `output/epanet_bb_equivalent_gops/atm-24h-na1/issue18-final-20260703T104337Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na1/issue18-final-20260703T104337Z/solver.log` | `license_blocked` | none | none |
| `atm-24h-na2` | 2 | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-final-20260703T104337Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-final-20260703T104337Z/solver.log` | `license_blocked` | none | none |
| `atm-24h-na3` | 3 | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-final-20260703T104337Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-final-20260703T104337Z/solver.log` | `license_blocked` | none | none |

The common status detail is:

```text
Model too large for size-limited license; visit https://gurobi.com/unrestricted for more information
```

Because no run produced a complete commanded 24-hour pump schedule,
`schedule.json` was not written for any case and the EPANET-BB fixed-schedule
audit was not run. This is a runtime/license blocker artifact, not evidence of
GOPS infeasibility and not a substitute for schedule comparison in issue #19.
