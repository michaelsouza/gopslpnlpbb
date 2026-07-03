# Issue 18 Final GOPS Runs

GitHub issue: `michaelsouza/gopslpnlpbb#18`

Run id: `issue18-final-academic-clean-20260703T110430Z`

Commit: `43dff0366689a258d7e718059e842386597cab6b`

Host: `labma-sol`

Runner mode: `lpnlpbb`

Runtime settings: `time_limit_seconds = 60`, `mip_gap = 1e-6`,
`gurobi_output = true`

Gurobi license file: `/home/michael/opt/gurobi1302/gurobi.lic`

## Outcome

All three EPANET-BB-equivalent GOPS final runs used the explicit academic
Gurobi license on `labma-sol`. The previous size-limited package license was
not used.

Each case reached Gurobi optimization and ran to the 60-second time limit, but
no incumbent complete commanded pump schedule was found. Therefore no
`schedule.json` was written and the EPANET-BB fixed-schedule audit was not run.

| Case | NA_max | Solver status | Best bound | Solutions | Run manifest | Solver log | Schedule | Audit |
| ---- | ------ | ------------- | ---------- | --------- | ------------ | ---------- | -------- | ----- |
| `atm-24h-na1` | 1 | `TIME_LIMIT` | `339.1489102091635` | 0 | `output/epanet_bb_equivalent_gops/atm-24h-na1/issue18-final-academic-clean-20260703T110430Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na1/issue18-final-academic-clean-20260703T110430Z/solver.log` | none | none |
| `atm-24h-na2` | 2 | `TIME_LIMIT` | `338.1129241760381` | 0 | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-final-academic-clean-20260703T110430Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na2/issue18-final-academic-clean-20260703T110430Z/solver.log` | none | none |
| `atm-24h-na3` | 3 | `TIME_LIMIT` | `337.9120362641078` | 0 | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-final-academic-clean-20260703T110430Z/run.json` | `output/epanet_bb_equivalent_gops/atm-24h-na3/issue18-final-academic-clean-20260703T110430Z/solver.log` | none | none |

All three run manifests record:

- `environment.host_name = "labma-sol"`
- `git.dirty = false`
- `solver.license_status = "valid"`
- `solver.license_file = "/home/michael/opt/gurobi1302/gurobi.lic"`
- `status.run_status = "time_limit_no_schedule"`
- `status.schedule_availability = "none"`

This is now a solver-runtime/time-limit outcome with no complete GOPS schedule,
not a Gurobi license blocker.
