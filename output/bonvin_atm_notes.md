# Bonvin AT(M) GOPS Reproduction Notes

This file is the audit trail for GitHub issue `michaelsouza/gopslpnlpbb#2` and the parent PRD `michaelsouza/gopslpnlpbb#1`. It records whether public GOPS artifacts can produce an audit-compatible Bonvin AT(M) schedule for the EPANET-BB clamp audit.

## Baseline

- Date started: 2026-06-28
- GOPS fork: `michaelsouza/gopslpnlpbb`
- Active branch: `bonvin-atm-audit`
- Upstream repository: `https://github.com/sofdem/gopslpnlpbb.git`
- Parent PRD: `michaelsouza/gopslpnlpbb#1`
- First implementation issue: `michaelsouza/gopslpnlpbb#2`
- Issue workflow: GitHub Issues on the fork, using `ready-for-agent` for agent-ready work
- Downstream audit consumer: `/home/michael/gitrepos/epanet-bb`

The downstream EPANET-BB audit accepts complete schedule JSON artifacts. Do not invent schedules from aggregate Bonvin runtime, cost, or optimality-gap values.

## Evidence Log

Record each investigation step here, with enough detail for another agent to rerun it.

| Date | Issue | Command or file inspected | Result summary |
| ---- | ----- | ------------------------- | -------------- |
| 2026-06-28 | #2 | `git remote -v` | `origin` points at `git@github.com:michaelsouza/gopslpnlpbb.git`; `upstream` points at `https://github.com/sofdem/gopslpnlpbb.git`. |
| 2026-06-28 | #2 | `git status --short --branch` | Branch is `bonvin-atm-audit`, tracking `origin/bonvin-atm-audit`. |
| 2026-06-28 | #2 | `AGENTS.md`, `CONTEXT.md` | Workstream, issue tracker, branch, and domain vocabulary are documented. |
| 2026-06-28 | #2 | `.gitignore` | Local virtual environments, caches, Gurobi license files, solver dumps, bulky logs, and scratch output are excluded from commits. |
| 2026-06-28 | #3 | `src/gops.py` | `ANY` maps to `Anytown`; profile key `s` maps to `Profile_5d_30m_smooth`; `STEPLENGTH['24'] = 2`; `ANY s 24 1` spans `01/01/2013 00:00` to `02/01/2013 00:00`. |
| 2026-06-28 | #3 | `src/instance.py` | `Instance._parse_profiles` skips by `aggregatesteps` rather than averaging; for `ANY s 24 1`, every second 30-minute row becomes one 1-hour period. |
| 2026-06-28 | #3 | `data/Anytown/*.csv` | GOPS `Anytown` has 19 junctions, 41 pipes, 3 fixed-speed pumps, 0 valves, 3 source rows, and 2 tank rows. |
| 2026-06-28 | #3 | `/home/michael/gitrepos/epanet-bb/networks/any-town.inp` | EPANET-BB AnyTown has 19 junctions, 41 pipes, 3 pumps, 0 valves, 1 reservoir, and 3 tanks. |
| 2026-06-28 | #3 | `/home/michael/gitrepos/epanet-bb/references/bonvin2021pump.md` | Bonvin Table 2 describes AT(M) as 41 pipes, 0 valves, 3 pumps, 3 tanks, 1 source, and 19 junctions; footnote 3 says Bonvin connects tanks 165 and 265 with a zero-length pipe relative to Costa et al. |
| 2026-06-29 | #5 | `/home/michael/gurobi13.0.2_linux64.tar.gz` | Gurobi 13.0.2 was extracted to `/home/michael/gurobi1302`; `gurobi_cl` and `grbgetkey` are available. |
| 2026-06-29 | #5 | `.venv/bin/python -m pip install ...` | Local `.venv` was populated with `gurobipy 13.0.2`, `numpy`, `pandas`, `matplotlib`, and `tables`. |
| 2026-06-29 | #5 | SSH SOCKS via `labma-sol` | `grbgetkey` was run locally using a SOCKS proxy through `michael@146.164.27.3:5121`; the proxy egress IP was `146.164.27.3`. |
| 2026-06-29 | #5 | `/home/michael/gurobi.lic` | Academic Gurobi license was retrieved locally and saved outside the repo; it expires on 2027-06-29. Do not commit or print the license file. |
| 2026-06-29 | #5 | `gurobi_cl` outside sandbox | `coins.lp` solved successfully with the academic license. |
| 2026-06-29 | #5 | `gurobipy` outside sandbox | GOPS AnyTown relaxation model built and optimization started with 1778 variables and 206160 constraints; a 1-second limit ended with status 9, confirming the unrestricted academic license path works for a large GOPS model. |
| 2026-06-29 | #4 | `src/gops.py` | Instance ids have exactly four tokens: benchmark, profile, horizon, and day. There is no activation-limit token. `solvebench` writes only statistics CSVs, and the file has an unguarded `solvebench(FASTBENCH[:7], mode='')` call at import/execution time. |
| 2026-06-29 | #4 | `src/instance.py` | `Instance` builds network data, profiles, dependencies, and symmetries. `ANY s 24 1` uses skipped 30-minute smooth-profile rows to create 24 one-hour periods. `parsesolution` expects a CSV status table and returns inactive arcs by period. |
| 2026-06-29 | #4 | `src/convexrelaxation.py` | Pump activity variables are `svar`/`xk`; pump ignition variables are `ivar`/`ik`. The only public switching cap is hardcoded at 6 starts per unique pump abstraction, or `6 * len(sympumps)` for a symmetric group. |
| 2026-06-29 | #4 | `src/lpnlpbb.py`, `src/primalheuristic.py`, `src/stats.py` | Incumbent schedules are held in memory as `activity`/`inactive` dictionaries. Time-adjusted heuristic solutions are separately flagged, but the adjusted subperiod-duration schedule is not exported as a normal fixed-period pump schedule. |
| 2026-06-29 | #4 | `rg -n -i "activation\|actuation\|ignition\|switch\|switching\|start\|stop\|dependency\|dependencies\|symmetry\|symmetries\|symmetric\|NA_max\|max_actuations\|max_act\|N =" src data docs output` | Relevant GOPS code hits are `convexrelaxation.py` for switching/ignition, `instance.py` for dependencies/symmetries, `lpnlpbb.py`/`primalheuristic.py` for fixed-period and adjusted incumbents. No public GOPS code/data hit exposes configurable `N = 1, 2, 3` or EPANET-BB-style `NA_max`. |
| 2026-06-29 | #6 | `rg --files`, `git ls-files`, `find output -maxdepth 3 -type f -print`, `find . -maxdepth 3 -type f -name '*.csv' -print` | The tracked public artifacts contain one output CSV, `output/sol.csv`; no tracked `.json`, `.sol`, `.lp`, generated `res*.csv`, or Anytown schedule artifact was found. |
| 2026-06-29 | #6 | `output/sol.csv`, `data/Richmond/Pump.csv`, `data/Richmond/Valve_Set.csv`, `src/gops.py`, `src/instance.py` | `output/sol.csv` is a complete 12-period Richmond active-element status table accepted by `Instance.parsesolution`, not an Anytown/AT(M) 24-period schedule. |
| 2026-06-29 | #6 | `bounds/*.hdf`, inspected with pandas/PyTables | Bounds files expose a single `/w` table whose secondary index labels are `flow` and `head`; they are OBBT bound artifacts, not pump-status schedules. |
| 2026-06-29 | #6 | `rg -n -i "sol\.csv\|solution\|solutions\|output\|pumpvals\|parsesolution\|testsolution\|activity\|inactive\|xk\(\|svar" README.md src output data docs` | Public code has an input-validation path for externally supplied schedules and in-memory incumbent schedules, but no tracked Bonvin/GOPS output writes complete `svar`/`activity` schedules. |
| 2026-06-29 | #7 | `./.venv/bin/python tools/run_candidate_anytown.py --describe-only` | The runner records the candidate as public instance `ANY s 24 1`: `Anytown`, `Profile_5d_30m_smooth`, `01/01/2013 00:00` to `02/01/2013 00:00`, 24 one-hour periods, pump arcs `R1/R2/R3 -> J20`, with the known benchmark and activation-limit caveats. |
| 2026-06-29 | #7 | `env GUROBI_HOME=/home/michael/gurobi1302/linux64 PATH=/home/michael/gurobi1302/linux64/bin:$PATH LD_LIBRARY_PATH=/home/michael/gurobi1302/linux64/lib:${LD_LIBRARY_PATH:-} GRB_LICENSE_FILE=/home/michael/gurobi.lic ./.venv/bin/python tools/run_candidate_anytown.py --time-limit 60 --output output/bonvin_atm_anytown_candidate_run.json` | Gurobi academic license was recognized and the controlled GOPS Anytown model ran for a 60-second limit. It ended with Gurobi status `TIME_LIMIT`, 1325 nodes, no accepted solution, and no complete unadjusted commanded pump schedule. Durable summary: `output/bonvin_atm_anytown_candidate_run.json`. |
| 2026-06-30 | setup | `mv /home/michael/gurobi1302 /opt/gurobi`, `mv /home/michael/gurobi.lic /opt/gurobi/gurobi.lic`, `~/.zshrc`, `env -u GUROBI_HOME -u GRB_LICENSE_FILE -u LD_LIBRARY_PATH ./.venv/bin/python tools/run_candidate_anytown.py --time-limit 1 --output /tmp/gurobi_move_runner_check.json` | Completed local Gurobi migration. Shell setup and repo runner now use `GUROBI_HOME=/opt/gurobi/linux64` and `GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic`. The runner recognized the academic license from `/opt/gurobi` and started the model without manually supplied Gurobi environment variables. |

## Evidence Categories

Later issues should fill these sections instead of scattering conclusions across terminal output.

### Commands Run

- Record exact commands, working directories, and relevant environment assumptions.
- Summarize large terminal outputs instead of pasting bulky logs.

### Files Inspected

- Record source files, data files, output artifacts, and EPANET-BB references inspected.
- Distinguish code evidence from paper/literature evidence.

### Solver And Runtime Status

- Record Python version, package versions, `gurobipy` version, and Gurobi license status when tested.
- Treat missing or restricted Gurobi licensing as a partial blocker, not as evidence that public schedules do or do not exist.
- Gurobi/`gurobipy` is the solver-faithful path. Any non-Gurobi attempt must be documented as a diagnostic fallback, not a Bonvin/GOPS reproduction.
- Current local solver setup as of 2026-06-30:
  - Gurobi install root: `/opt/gurobi/linux64`.
  - License file: `/opt/gurobi/gurobi.lic`, outside the repository.
  - Python environment: repo-local `.venv` with `gurobipy 13.0.2`.
  - Required runtime environment: set `GUROBI_HOME`, add `$GUROBI_HOME/bin` to `PATH`, add `$GUROBI_HOME/lib` to `LD_LIBRARY_PATH`, and set `GRB_LICENSE_FILE=/opt/gurobi/gurobi.lic`.
  - `tools/run_candidate_anytown.py` defaults to these `/opt/gurobi` paths when the shell has not already set Gurobi environment variables.
  - Gurobi commands must run outside the Codex sandbox when license validation needs the machine hostid; inside the sandbox `grbprobe` cannot read the hostid and reports a mismatch.
  - `gurobipy` initially exposed a size-limited restricted license, but the GOPS AnyTown model is too large for that restricted license. The academic license resolves this size limit outside the sandbox.

### Benchmark Identity Findings

Issue #3 conclusion: **partially matched, but not identical to the EPANET-BB audit network and not fully evidenced as the same AT(M) instance for clamp-audit comparison.**

The GOPS `ANY` benchmark is clearly intended to be an AnyTown-family case and it matches the Bonvin AT(M) counts for internal junctions, pipes, pumps, and valves. It does not literally match the Bonvin table or the EPANET-BB `any-town.inp` representation for sources and tanks. The main caveats are the GOPS split source representation, the apparent aggregation or redirection of tanks 165 and 265, and profile differences.

#### GOPS `ANY` Instance Construction

- `BENCH['ANY']` in `src/gops.py` selects network `Anytown`, start day `D0 = 1`, and base time `/01/2013 00:00`.
- `PROFILE['s']` and `PROFILE['n']` both select `Profile_5d_30m_smooth`.
- `STEPLENGTH['24'] = 2`.
- `makeinstance('ANY s 24 1')` therefore constructs an `Instance('Anytown', 'Profile_5d_30m_smooth', '01/01/2013 00:00', '02/01/2013 00:00', 2)`.
- `Instance._parse_profiles` skips rows by `aggregatesteps`; it does not call `_parse_profiles_aggregate`. For the 30-minute smooth profile, this selects every second row and yields 24 one-hour periods.
- `Profile_1d_1h.csv` exists but is not selected by the public `solveinstance('ANY s 24 1')` code path.

#### Structural Comparison

| Element | Bonvin AT(M) table/article | GOPS `data/Anytown` | EPANET-BB `any-town.inp` | Finding |
| ------- | -------------------------- | ------------------- | ------------------------- | ------- |
| Junctions | 19 internal junctions | 19 rows in `Junction.csv` | 19 `[JUNCTIONS]` | Matches by count; IDs align after removing GOPS `J` prefix. |
| Pipes | 41 pipes | 41 rows in `Pipe.csv` | 41 `[PIPES]` | Count matches; IDs align after removing GOPS `T` prefix, except pipe 178 endpoint differs. |
| Valves | 0 valves | 0 rows in `Valve_Set.csv` | 0 `[VALVES]` | Matches. |
| Pumps | 3 identical fixed-speed pumps | `1A`, `2A`, `3A`, all `FSD`, identical coefficients | `111`, `222`, `333`, all parallel source-to-node-20 pumps | Pump-count abstraction is structurally compatible; pump IDs and source-node representation differ. |
| Sources | 1 source | `R1`, `R2`, `R3`, each with head 3.048 and constant profile | reservoir `10` with head 3.048 | GOPS splits the single source into three equivalent source nodes feeding the three pumps. |
| Tanks | 3 tanks | `T65`, `T165` only | tanks `65`, `165`, `265` | Mismatch. GOPS appears to combine or redirect the 165/265 tank representation. |

Pipe endpoint check:

- GOPS pipe IDs match EPANET-BB pipe IDs after stripping the GOPS `T` prefix.
- The only endpoint mismatch found is pipe `178`: GOPS has `J140 -> T165`; EPANET-BB has `140 -> 265`.
- Bonvin footnote 3 says their AT(M) variant connects tanks 165 and 265 with a zero-length pipe relative to Costa et al.; the public GOPS data instead exposes only `T165`, with no explicit `T265` row and no zero-length pipe row.

Tank representation check:

- GOPS `Reservoir.csv` has `T65` and `T165` only.
- `T65` has volume range `24266..26090` and surface `364.74`.
- `T165` has volume range `48532..52180` and surface `729.48`, exactly double the `T65` surface and volume range.
- EPANET-BB has three distinct tanks `65`, `165`, and `265`, all with the same diameter and level bounds.
- Interpretation: GOPS likely represents tanks 165 and 265 as a combined storage element, but this is an inference from public data, not a literal match to the EPANET-BB audit network.

Pump-set check:

- GOPS pumps `1A`, `2A`, and `3A` are all `FSD` with the same pressure and power coefficients.
- They connect `R1/R2/R3 -> J20`.
- EPANET-BB pumps `111`, `222`, and `333` connect `10 -> 20`.
- Because GOPS source rows `R1`, `R2`, and `R3` all have head `3.048`, this is plausibly equivalent for pump-count scheduling, but the network representation is not identical.

#### Profile And Horizon Comparison

- Bonvin describes daily pump scheduling as one day divided into `T = 12`, `24`, or `48`, with smoothed electrical tariff and demand profiles when needed. It also says the five daily electricity tariffs correspond to SEM prices over a five-day period.
- GOPS `ANY s 24 1` uses `Profile_5d_30m_smooth.csv`, not the hourly `Profile_1d_1h.csv`.
- GOPS `ANY s 24 1` yields 24 one-hour periods from 2013-01-01 00:00 to 2013-01-02 00:00 by selecting every second 30-minute row.
- EPANET-BB `any-town.inp` has `Duration 24:00`, `Hydraulic Timestep 0:30`, `Pattern Timestep 1:00`, and `Report Timestep 1:00`.
- EPANET-BB schedule JSONs reference `inp_file: networks/any-town.inp` and `max_actuations`.

Profile differences:

- GOPS smooth day-1 selected demand multipliers are `[0.7, 0.7, 0.65, 0.65, 0.6, 0.6, 1.2, 1.2, 1.25, 1.25, 1.3, 1.3, 1.2, 1.2, 1.1, 1.1, 1.0, 1.0, 0.9, 0.9, 0.8, 0.8, 0.7, 0.7]`.
- EPANET-BB `DEM` multipliers are `[0.7, 0.7, 0.7, 0.6, 0.6, 0.6, 1.2, 1.2, 1.2, 1.3, 1.3, 1.3, 1.2, 1.2, 1.2, 1.0, 1.0, 1.0, 0.9, 0.9, 0.9, 0.7, 0.7, 0.7]`.
- GOPS smooth day-1 selected tariffs are `[49.68, 49.68, 49.68, 49.68, 49.68, 49.68, 45.2325, 45.2325, 60.935, 60.935, 67.0425, 67.0425, 66.865, 66.865, 64.38, 64.38, 67.3925, 67.3925, 64.3225, 64.3225, 63.0125, 63.0125, 53.295, 53.295]`.
- EPANET-BB `PRICES` are `[18.14, 18.14, 18.14, 18.14, 18.14, 18.14, 18.14, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 80.97, 80.97, 80.97, 80.97, 18.14, 18.14, 18.14]`.
- The unused GOPS `Profile_1d_1h.csv` has tariffs shaped like EPANET-BB `PRICES` at a 10x scale, but its demand multipliers still differ from EPANET-BB at several hours.

#### Benchmark Identity Classification

- **Matched:** AnyTown-family structure; 19 junctions; 41 pipes by count; 0 valves; 3 identical fixed-speed pumps; 24 one-hour periods for `ANY s 24 1`.
- **Mismatched:** GOPS public data has 2 tank rows and 3 source rows, while Bonvin Table 2 and EPANET-BB use 3 tanks and 1 source; GOPS pipe 178 is connected to `T165` instead of tank `265`; GOPS selected profiles differ from EPANET-BB `any-town.inp` demand and tariff patterns.
- **Insufficiently evidenced:** Public GOPS data may encode Bonvin's 165/265 tank handling by aggregating storage, but the repository does not make that equivalence explicit. A recovered GOPS schedule would therefore need a clear caveat before any EPANET-BB clamp-audit comparison.

Practical implication for later issues: GOPS `ANY` is suitable for investigating whether public Bonvin/GOPS artifacts can generate a schedule, but it is **not yet a drop-in schedule source for EPANET-BB `networks/any-town.inp`**. If a GOPS schedule is recovered, normalization must document the source/tank/profile differences rather than presenting it as the same benchmark instance without caveats.

### Scheduling Semantics And Activation Limit

Issue #4 conclusion: **the public GOPS code does not expose Bonvin-Costa `N = 1, 2, 3` as a configurable parameter and does not implement EPANET-BB `NA_max` semantics.** It uses pump-on binary variables plus ignition/start binary variables, with a hardcoded start cap of `6`. For `Anytown`, all three pumps are treated as one symmetric group, so the public model applies an aggregate cap of `6 * 3 = 18` ignition variables across the group rather than a strict per-pump `N`.

#### Instance Key Syntax

`makeinstance(instid)` in `src/gops.py` requires exactly four whitespace-separated tokens:

| Token | Meaning | `ANY s 24 1` value |
| ----- | ------- | ------------------ |
| 1 | benchmark key in `BENCH` | `ANY`, selecting network `Anytown`, base day `D0 = 1`, and base time `/01/2013 00:00` |
| 2 | profile key in `PROFILE` | `s`, selecting `Profile_5d_30m_smooth` |
| 3 | horizon/discretization key in `STEPLENGTH` | `24`, selecting `aggregatesteps = 2` |
| 4 | day offset | `1`, selecting day 1 from `01/01/2013 00:00` to `02/01/2013 00:00` |

There is no token for an activation limit, start limit, actuation budget, solver mode, or output schedule path. `FASTBENCH` also contains only FSD/Richmond entries; `ANY s 24 1` must be requested explicitly. Caveat: `src/gops.py` ends with an unguarded `solvebench(FASTBENCH[:7], mode='')`, so importing `gops` as a module can unexpectedly run benchmark solves unless guarded or bypassed.

#### `ANY s 24 1` Construction Trace

- `BENCH['ANY']` selects `Anytown`, `D0 = 1`, and `H0 = '/01/2013 00:00'`.
- `PROFILE['s']` selects `Profile_5d_30m_smooth`; `PROFILE['n']` currently selects the same file.
- `STEPLENGTH['24'] = 2`, meaning the parser advances by two profile rows at a time.
- `makeinstance('ANY s 24 1')` constructs `Instance('Anytown', 'Profile_5d_30m_smooth', '01/01/2013 00:00', '02/01/2013 00:00', 2)`.
- `Instance.__init__` parses tanks, junctions, sources, pumps, pipes, valves, profiles, dependencies, and symmetries from `data/Anytown`.
- `Instance._parse_profiles` skips rows by `aggregatesteps`; it does not use `_parse_profiles_aggregate`. For the smooth 30-minute profile, `ANY s 24 1` selects every second row and yields 24 one-hour periods.
- `Instance._dependencies()` returns `None` for Anytown.
- `Instance._pump_symmetric()` returns the three Anytown pump arcs `('R1', 'J20')`, `('R2', 'J20')`, and `('R3', 'J20')`.

Direct `solveinstance('ANY s 24 1')` still has an operational caveat: `solve()` calls `instance.parse_bounds()`, and this repository does not contain `bounds/Anytown.hdf`. The current exception handler only catches `UnicodeDecodeError`, so a normal direct solve path can fail on missing bounds before model construction. The #5 solver smoke test bypassed that path by constructing the relaxation model directly.

#### Commanded Schedule Representation

The model uses:

- `svar[(i, j), t]`, named `xk(i,j,t)` for pumps, as the commanded pump-on status for arc `(i, j)` at period `t`.
- `ivar[(i, j), t]`, named `ik(i,j,t)`, as an ignition/start indicator used by switching constraints.
- `activity[t][a]` in `lpnlpbb.py` as the in-memory commanded schedule, where `activity[t][a] = 1` means arc `a` is commanded active in period `t`.
- `inactive[t]` as the complement set consumed by `HydraulicNetwork.extended_period_analysis(inactive)`.

For Anytown, there are no valves, so schedule normalization can focus on the three pump arcs. A later extraction issue should map GOPS pump arcs in deterministic order to EPANET-BB pump IDs with caveats:

| GOPS arc | GOPS pump row | Likely EPANET-BB pump |
| -------- | ------------- | --------------------- |
| `('R1', 'J20')` | `1A` | `111` |
| `('R2', 'J20')` | `2A` | `222` |
| `('R3', 'J20')` | `3A` | `333` |

This mapping is schedule-compatible for the parallel-pump abstraction, but it is not a proof that the GOPS and EPANET-BB hydraulic instances are identical. The source/tank/profile caveats from issue #3 still apply.

`solvebench()` currently writes only aggregate statistics to `../output/resYYMMDD-MODE.csv`. The public branch does not write complete incumbent pump schedules. `testsolution()` can read a CSV schedule and use `pumpvals` to fix `svar`, but that is a validation path for an externally supplied schedule, not evidence that Bonvin/GOPS public outputs contain one.

#### Activation, Starts, Stops, And Symmetry

The public switching logic is in `convexrelaxation.build_model`:

- `ivar[a, t] >= svar[a, t] - svar[a, t - 1]` for `t = 1..T-1`.
- `sum_t ivar[a, t] <= 6 - svar[a, 0]` for a non-symmetric pump abstraction.
- If a benchmark has a symmetric group, `pumps_without_sym()` replaces all pumps in the group by fictional key `'sym'`, and `getv(ivar, 'sym', t)` sums `ivar` over all pumps in the group.
- For a symmetric group, the cap becomes `sum_t sum_p ivar[p, t] <= 6 * len(sympumps)`.
- An ordering constraint also enforces `ivar[p_i, t] >= ivar[p_{i+1}, t]` and `svar[p_i, t] >= svar[p_{i+1}, t]` inside the symmetric group.

Implications:

- The code counts pump starts (`0 -> 1`) through ignition variables. It does not count stops (`1 -> 0`) and has no separate stop variable.
- The code has no `N`, `NA`, `NA_max`, `max_actuations`, or command-line option that selects `N = 1, 2, 3`.
- For `ANY s 24 1`, because all three pumps are symmetric, the only public cap is an aggregate symmetric-group start cap of 18 starts across the day.
- The `6 - svar[a, 0]` non-symmetric expression suggests the author intended starts from an initially-off state to be bounded by 6, with special handling if the pump is already on at period 0. The code comment says `make ivar[a,0] = svar[a,0]`, but no such constraint is implemented.
- `ivar` has lower-bound transition constraints but no upper-bound equivalence constraints and no objective coefficient. It is sufficient for restricting starts through the cap, but raw `ivar` values are not a reliable schedule artifact. Use `svar`/`activity` to reconstruct commanded pump status.
- The minimum one-hour activity constraint is only added when the instance timestep is 30 minutes. `ANY s 24 1` has one-hour periods, so that constraint is not active for the target case.
- Dependency constraints are benchmark-specific and apply only when `inst.dependencies` is not `None`; Anytown has none.

#### Exact/Incumbent Versus Adjusted Heuristic Solutions

`lpnlpbb.py` distinguishes two solution types:

- Hydraulically feasible incumbent: an integer `svar` plan passes `extended_period_analysis(inactive)`, is costed with simulated flows, and is appended to `_solutions` with `adjusted = False`, plus `flows` and `volumes`.
- Time-adjusted heuristic incumbent: an integer `svar` plan first violates the fixed-period hydraulic audit, then `primalheuristic.adjust_steplength()` tries to shift neighboring configurations by variable subperiod durations. If accepted in `CUT` mode, it is appended with `adjusted = True`, `flows = None`, and `volumes = None`; adjusted candidates are also tracked in `_adjust_solutions`.

The adjusted heuristic is not a fixed 24-period commanded pump schedule suitable for EPANET-BB JSON export by itself. The stored `plan` remains the original period-indexed `activity` dictionary; the heuristic's subperiod-duration decisions are local to `primalheuristic.py` and are not exported as a complete schedule artifact. For the Bonvin public-artifact audit, only non-adjusted incumbent schedules should be treated as directly auditable fixed-period schedules unless a later issue implements and documents a separate adjusted-schedule export format.

#### Relationship To EPANET-BB `NA_max`

Bonvin's general formulation uses start variables for pump starts (`0 -> 1`) and applies `N` to starts. EPANET-BB `max_actuations` is different in the operative artifacts: it tracks starts (`0 -> 1`) and stops (`1 -> 0`) separately by pump, with initialization details that do not reduce to the public GOPS hardcoded start cap.

Therefore, running GOPS on the same `NA_max = 1, 2, 3` cases as EPANET-BB is a new EPANET-BB-equivalent GOPS experiment, not a direct Bonvin public-artifact reproduction. That experiment is tracked separately by GitHub issue `michaelsouza/gopslpnlpbb#10`.

The new experiment should keep Bonvin/GOPS public-artifact sufficiency and EPANET-BB-equivalent GOPS comparison results separate in outputs and prose. `../epanet-bb/paper/paper.tex` defines the comparison target as AnyTown Modified, `T = 24`, three parallel fixed-speed pumps, tanks 65/165/265, and `NA_max = 1, 2, 3`. It also includes EPANET-BB-specific parameter tuning, ablation, and MPI scalability experiments; those are contextual for GOPS unless a later issue designs explicit GOPS analogues.

The minimum GOPS comparison surface for the paper is: run the GOPS method on the same 24-hour AnyTown Modified benchmark assumptions for `NA_max = 1, 2, 3`; export schedule JSONs compatible with EPANET-BB's audit/figure scripts; compare cost, runtime, feasibility/audit events, and pump schedules against `paper/data/run_*_a_*.json`. Note a source-of-truth conflict: `paper.tex` states `sum |x_h - x_{h-1}| <= NA_max`, but the published JSON schedules and EPANET-BB code use a looser operative semantics with separate start/stop budgets and initialization details. The GOPS experiment should target the operative artifacts/code semantics, while documenting the paper-text mismatch.

### Schedule Availability

Issue #6 conclusion: **the public GOPS artifacts do not contain an audit-compatible Bonvin AT(M) / `ANY s 24 1` commanded pump schedule.**

The only tracked public output file with a complete binary activity table is `output/sol.csv`. It is schedule-bearing for a Richmond instance, but unrelated to the target Bonvin AT(M) / Anytown audit. Public data and code artifacts document benchmark construction, input data, bound tightening, and result-statistics formats; they do not publish a complete GOPS incumbent for the 24-hour Anytown case.

#### Public Artifact Inventory

| Artifact | Classification | Schedule evidence | AT(M) audit compatibility |
| -------- | -------------- | ----------------- | ------------------------- |
| `output/sol.csv` | schedule-bearing, but unrelated | CSV rows encode active-element status by arc for 12 periods; `Instance.parsesolution()` treats status `0` as inactive and status `1` as active. | Not compatible. Rows match Richmond pumps/valves, not Anytown pumps; first line says `2013-05-23 07:00:00, 12`; it is not a 24-period `ANY`/AT(M) schedule. |
| `output/resYYMMDD-*.csv` generated by `solvebench()` | aggregate-only | `src/gops.py` writes status, upper/lower bounds, gap, CPU, nodes, callback counters, and adjusted-solution summaries through `Stat.tocsv_basic()`. | Not compatible. These files do not contain per-period `svar`/`activity` decisions, and no tracked public `res*.csv` file is present. |
| `data/Anytown/*.csv` | provenance-only | Defines the Anytown-family network, pumps, tanks, sources, initial volumes, tariffs, and demand profiles. | Insufficient. It identifies the relevant 3-pump set and profiles, but contains no commanded pump decisions. |
| `data/Richmond/*.csv` | provenance-only | Defines the Richmond network used by the `output/sol.csv` active-element rows. | Unrelated to the AT(M) audit target. |
| `data/Simple_Network/*.csv` | provenance-only | Defines a smaller benchmark network. | Unrelated to the AT(M) audit target. |
| `bounds/Simple_Network.hdf`, `bounds/Richmond.hdf`, `bounds/Richmond_Smooth.hdf` | provenance-only / insufficient | Each HDF exposes a `/w` table with `flow` and `head` labels; `Instance.parse_bounds()` consumes it as OBBT arc bounds. | Not compatible. They contain continuous bounds, no Anytown file, and no discrete pump-status sequence. |
| `src/convexrelaxation.py`, `src/lpnlpbb.py`, `src/primalheuristic.py` | provenance-only | Defines `svar`/`ivar`, in-memory `activity`/`inactive`, and adjusted heuristic solution handling. | Insufficient by itself. The code can create schedules during a run, but the public artifact set does not export them. |
| `src/gops.py` and `src/stats.py` | aggregate-only / provenance-only | `testsolution()` can read an external schedule and fix pump `svar` values through `pumpvals`; `solvebench()` writes aggregate statistics. | Not compatible. The validation path is not evidence of a public Bonvin AT(M) schedule, and aggregate stats must not be promoted into schedules. |
| `README.md` | provenance-only | Links the repository to the Bonvin, Demassey, and Lodi GOPS paper. | Insufficient. It contains no instance-specific schedule data. |

Ignored local byproducts such as Python caches and `gurobi.log` are not public tracked GOPS artifacts and are excluded from this inventory.

#### Solution-Like Artifact Mapping

`output/sol.csv` is the only solution-like tracked artifact. Its format matches `Instance.parsesolution(filename)`:

- Row 1 stores a timestamp-like label and horizon length. The parser checks only the horizon value against `instance.nperiods()`.
- Each subsequent row stores `start node`, `end node`, then one binary status per period.
- `Instance.parsesolution()` returns `inactive[t] = {(start, end) rows with status 0 at period t}`.
- `testsolution()` uses that `inactive` dictionary for hydraulic evaluation, then builds `pumpvals[(pump_arc, t)] = 0/1` for pump arcs and passes those values into `convexrelaxation.build_model()`, where they fix `svar[pump_arc, t]`.

The artifact therefore maps to GOPS commanded activity semantics for a Richmond validation input: period status `1` means commanded active, and status `0` means inactive. It is not an exported incumbent schedule from `lpnlpbb.py`, and it is not tied to `ANY`/`Anytown`.

Per-pump provenance preserved from `output/sol.csv`:

| Richmond pump row | Arc | 12-period status sequence |
| ----------------- | --- | ------------------------- |
| `1A` | `209 -> 766` | `1 0 0 0 0 0 0 0 0 0 0 0` |
| `2A` | `196 -> 768` | `1 1 1 1 1 0 1 1 1 1 1 0` |
| `3A` | `175 -> 186` | `1 1 1 1 1 0 1 1 0 1 0 0` |
| `4B` | `125 -> 353` | `1 1 1 0 1 0 1 1 0 1 0 0` |
| `5C` | `635 -> 636` | `1 0 0 0 1 0 0 0 0 1 0 0` |
| `6D` | `264 -> 112` | `1 0 1 1 1 0 1 1 1 1 0 1` |
| `7F` | `745 -> 753` | `0 0 0 0 0 0 0 1 0 0 0 0` |

The same file also contains four Richmond valve rows. Anytown has no valves, and its public pump arcs are `R1 -> J20`, `R2 -> J20`, and `R3 -> J20`, so none of the Richmond per-pump rows can be mapped to the AT(M) three-pump set without inventing decisions.

#### `ANY` / Anytown Schedule Check

No inspected public artifact provides all of the following at once:

- Benchmark identity tied to GOPS `ANY` / `data/Anytown`.
- A 24-period horizon corresponding to `ANY s 24 1`.
- Per-period commanded status for the Anytown pump arcs `('R1', 'J20')`, `('R2', 'J20')`, and `('R3', 'J20')`.
- Provenance connecting the status table to Bonvin AT(M) or the GOPS LP/NLP branch-and-bound comparison.

Therefore, existing public outputs alone cannot produce an EPANET-BB schedule JSON for the Bonvin AT(M) clamp audit. Producing such a JSON from the current public artifacts would require inventing the missing Anytown pump decisions. The next valid paths are either to run GOPS and export a new solver-derived schedule, or to document final public-artifact insufficiency if a solver-derived schedule cannot be produced.

### Candidate GOPS Run

Issue #7 conclusion: **a solver-faithful GOPS Anytown execution was attempted, but it did not produce a complete commanded pump schedule.**

The selected candidate run is public instance `ANY s 24 1`, expanded without importing `src/gops.py`:

- Network: `Anytown`
- Profile: `Profile_5d_30m_smooth`
- Horizon: `01/01/2013 00:00` to `02/01/2013 00:00`
- Discretization: 24 one-hour periods (`aggregate_steps = 2`)
- Pump arcs: `('R1', 'J20')`, `('R2', 'J20')`, and `('R3', 'J20')`
- Activation-limit caveat: no public `N` or `NA_max` token exists; the public model uses the hardcoded symmetric-group start cap from `src/convexrelaxation.py`
- Benchmark caveat: GOPS `Anytown` remains AnyTown-family but not a literal EPANET-BB `any-town.inp` match because of the tank/source/profile differences recorded in issue #3

The runner is `tools/run_candidate_anytown.py`. It avoids the unguarded `solvebench(FASTBENCH[:7], mode='')` side effect in `src/gops.py`, changes the solver working directory to `src` for the legacy `../data` and `../bounds` paths, and records a JSON summary in `output/bonvin_atm_anytown_candidate_run.json`.

The direct public `solveinstance('ANY s 24 1')` path remains operationally blocked before model construction because `solve()` calls `instance.parse_bounds()` and the repository has no `bounds/Anytown.hdf`. The exception handler only catches `UnicodeDecodeError`, not a missing file. The controlled run therefore recorded the missing bounds file and skipped bounds parsing so that the solver-faithful model could still be exercised with the public CSV data.

#### Run Command And Environment

Command from repository root:

```sh
env GUROBI_HOME=/home/michael/gurobi1302/linux64 PATH=/home/michael/gurobi1302/linux64/bin:$PATH LD_LIBRARY_PATH=/home/michael/gurobi1302/linux64/lib:${LD_LIBRARY_PATH:-} GRB_LICENSE_FILE=/home/michael/gurobi.lic ./.venv/bin/python tools/run_candidate_anytown.py --time-limit 60 --output output/bonvin_atm_anytown_candidate_run.json
```

After the local Gurobi migration on 2026-06-30, the same runner defaults to `/opt/gurobi` paths, so the normal command is:

```sh
./.venv/bin/python tools/run_candidate_anytown.py --time-limit 60 --output output/bonvin_atm_anytown_candidate_run.json
```

Runtime assumptions and observed solver state:

- Original working directory: `/home/michael/gitrepos/gopslpnlpbb`
- Legacy solver working directory: `/home/michael/gitrepos/gopslpnlpbb/src`
- Python environment: repo-local `.venv`
- `gurobipy` version: `13.0.2`
- Gurobi license environment variables were set, and the terminal output reported the academic license expiring on 2027-06-29
- Gurobi model size: 1778 variables, 144 binary variables, 144 integer variables, and 206160 constraints
- Parameters: `MIPGap = 1e-6`, `TimeLimit = 60`, `epsilon = 1e-2`, LP/NLP B&B mode `plain` (`adjust_mode = ''`)

Terminal output summary:

- The model recognized Anytown pump symmetry as `['sym']`.
- The callback reached 37 integer leaves.
- Every reported integer leaf violated the hydraulic simulation, mainly at tank `T65` and sometimes at `T165`.
- Representative violations included `t=3 tk=T65: -54.35`, `t=3 tk=T165: -111.60`, and `t=8 tk=T65: 547.02`.
- The run ended with `Optimization was stopped with status 9` and `no solution found`.

JSON summary:

- Path: `output/bonvin_atm_anytown_candidate_run.json`
- Gurobi status: `TIME_LIMIT` (`9`)
- Gurobi runtime: `60.16815900802612` seconds
- Wall time: `61.523` seconds
- Node count: `1325`
- Objective bound: `687.2836868303827`
- Gurobi solution count: `0`
- GOPS accepted solution count: `0`
- Adjusted solution count: `0`
- Schedule availability: `no_complete_unadjusted_commanded_pump_schedule`

Artifact classification:

| Artifact | Classification | Schedule evidence | AT(M) audit compatibility |
| -------- | -------------- | ----------------- | ------------------------- |
| `tools/run_candidate_anytown.py` | reproduction runner | Selects and runs the candidate GOPS Anytown path without importing `src/gops.py`; can export any accepted unadjusted incumbent schedule if one is found. | Provenance-only for this run. It produced no schedule because no GOPS incumbent was accepted. |
| `output/bonvin_atm_anytown_candidate_run.json` | run summary | Records candidate metadata, environment assumptions, missing bounds status, model size, runtime status, and solution classification. | Not a schedule. It explicitly records `no_complete_unadjusted_commanded_pump_schedule`. |
| Terminal callback output | solver/runtime evidence | Shows integer leaf candidates were evaluated and rejected by hydraulic simulation. | Not a schedule. Violated candidates must not be promoted into EPANET-BB schedule JSON. |
| `output/res*.csv` | absent | The controlled runner does not call `solvebench()`, and no aggregate stats CSV was generated. | No schedule evidence. |

This run does not prove that a longer controlled execution could never find a feasible GOPS schedule. It does complete the public-artifact reproduction slice for issue #7: the direct public path is blocked by missing Anytown bounds, and the controlled solver-faithful run did not recover a complete commanded pump schedule within the recorded execution. There is therefore no schedule-bearing artifact to hand to issue #8 from this run.

### Mapping Decisions

- If a GOPS schedule is recovered, record how GOPS pump activity maps to EPANET-BB `best_y` and optional `best_x`.
- Record initial-state, horizon, pump identity, and activation-limit caveats.

### EPANET-BB Audit Results

- Record schedule JSON paths, audit JSON paths, command lines, zero-flow threshold, and event-count summaries.
- Distinguish commanded pump schedules from effective hydraulic operation under EPANET-BB simulator semantics.

### Final Outcome

Choose exactly one final outcome when the dependent issues are complete.

- **Outcome A: Auditable schedules recovered.** List normalized schedule files, EPANET-BB audit outputs, mapping caveats, and audit event counts.
- **Outcome B: Public GOPS artifacts are not enough.** List inspected files and commands, local run status, schedule availability evidence, insufficiency rationale, and exact data that would need to be requested from Bonvin et al.

## Artifact Hygiene

Commit durable, evidence-focused artifacts only.

Allowed when relevant:

- `output/bonvin_atm_notes.md`
- Small normalized `output/bonvin_atm_*.json` schedules that are supported by GOPS output
- Small EPANET-BB audit JSON files produced from supported schedules
- Narrow helper scripts and tests created for extraction or normalization

Do not commit:

- Virtual environments or dependency caches
- Python caches and test caches
- Gurobi license files, access tokens, credentials, or proxy credentials
- Bulky solver logs or scratch output
- Solver model dumps unless a later issue explicitly justifies a small fixture
- Generated schedules that require invented decisions
