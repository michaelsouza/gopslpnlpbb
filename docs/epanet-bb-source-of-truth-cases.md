# EPANET-BB Source-of-Truth Cases

Implemented for: `michaelsouza/gopslpnlpbb#12`

Parent PRD: `michaelsouza/gopslpnlpbb#10`

Machine-readable companion: `docs/epanet-bb-source-of-truth-cases.json`

## Purpose

This document extracts the benchmark surface that later GOPS work must target
for the EPANET-BB-equivalent GOPS experiment track. It deliberately uses the
neighboring EPANET-BB repository's executable code and published schedule
artifacts as the comparison target, not the older Bonvin public-artifact
sufficiency path.

The extraction was made from local repository `../epanet-bb`, branch
`reviewer-fixes`, commit `7c37c68de38993828f08ba2e70453da2583f4754`, observed
with no dirty worktree changes on 2026-07-01.

## Source-Of-Truth Order

Use these as primary sources:

- `../epanet-bb/networks/any-town.inp`
- `../epanet-bb/paper/data/run_*_a_*.json`
- `../epanet-bb/src/CLI/BBSolver.cpp`
- `../epanet-bb/src/CLI/BBConstraints.cpp`
- `../epanet-bb/src/CLI/BBAudit.cpp`

Use these as secondary explanatory sources:

- `../epanet-bb/paper/paper.tex`
- `../epanet-bb/README.md`
- `../epanet-bb/scripts/*.py`

If manuscript equations or prose conflict with executable code and published
artifacts, later GOPS translation should target the executable code and
published artifacts.

## Benchmark Surface

The operative network is `../epanet-bb/networks/any-town.inp`. It is the
AnyTown Modified paper case used by the EPANET-BB paper artifacts.

The INP file defines:

- Reservoir/source node `10`, head `3.048`.
- Storage tanks `65`, `165`, and `265`, each with initial level `66.93 m`,
  minimum level `66.53 m`, maximum level `71.53 m`, and diameter `21.55 m`.
- Three fixed-speed pumps `111`, `222`, and `333`, each from node `10` to node
  `20`, using head curve `1`, efficiency curve `2`, and the hourly `PRICES`
  energy pattern.
- A 24-hour duration, 30-minute hydraulic timestep, 1-hour pattern timestep,
  and 1-hour report timestep.
- Demand pattern `DEM`, with node-specific patterns `DEM55`, `DEM90`, and
  `DEM170` carrying the same 24 values in the operative INP file.
- Per-junction base demands from the `[JUNCTIONS]` section, in CMH, assigned
  to the demand patterns listed below.
- Tariff pattern `PRICES` with 24 hourly values.

Operational counts from the INP file are 19 junctions, 1 reservoir, 3 tanks,
41 pipe rows, 3 pump links, no valves, and 44 total links. The manuscript prose
describes "44 pipes" and "25 nodes"; the executable target for this workstream
is the INP structure, where the 44 count is total links when pumps are included.

## Demand Surface

The executable demand surface is the product of each junction's base demand and
its assigned hourly pattern.

| Junction | Elevation | Base demand | Pattern |
| --- | ---: | ---: | --- |
| `20` | 6.096 | 113.56235 | `DEM` |
| `30` | 15.24 | 45.42494 | `DEM` |
| `110` | 15.24 | 113.56235 | `DEM` |
| `70` | 15.24 | 113.56235 | `DEM` |
| `60` | 15.24 | 113.56235 | `DEM` |
| `90` | 15.24 | 227.1247 | `DEM90` |
| `100` | 15.24 | 113.56235 | `DEM` |
| `40` | 15.24 | 45.42494 | `DEM` |
| `50` | 15.24 | 45.42494 | `DEM` |
| `80` | 15.24 | 113.56235 | `DEM` |
| `150` | 36.576 | 45.42494 | `DEM` |
| `140` | 24.384 | 45.42494 | `DEM` |
| `170` | 36.576 | 45.42494 | `DEM170` |
| `130` | 36.576 | 45.42494 | `DEM` |
| `160` | 36.576 | 181.69976 | `DEM` |
| `120` | 36.576 | 45.42494 | `DEM` |
| `55` | 24.384 | 22.71247 | `DEM55` |
| `75` | 24.384 | 22.71247 | `DEM` |
| `115` | 24.384 | 22.71247 | `DEM` |

## First-Class Cases

The EPANET-BB-equivalent GOPS experiment has exactly three target cases:

| Case id | `NA_max` | Benchmark target | Horizon | Published EPANET-BB schedule |
| --- | ---: | --- | --- | --- |
| `atm-24h-na1` | 1 | AnyTown Modified | 24 one-hour periods | `../epanet-bb/paper/data/run_Souza2026_a_01.json` |
| `atm-24h-na2` | 2 | AnyTown Modified | 24 one-hour periods | `../epanet-bb/paper/data/run_Souza2026_a_02.json` |
| `atm-24h-na3` | 3 | AnyTown Modified | 24 one-hour periods | `../epanet-bb/paper/data/run_Souza2026_a_03.json` |

The paper comparison corpus contains 12 schedule JSON files, one each for
Costa2016, Cimorelli2020, Paola2025, and Souza2026 at `NA_max = 1, 2, 3`.
Every file has `best_y` length 25 and `best_x` length 75.

## Schedule Shape

EPANET-BB schedule JSONs use:

- `best_y`: aggregate commanded pump-count schedule, length `h_max + 1`.
- `best_x`: flattened binary per-pump schedule, length `(h_max + 1) * 3`.
- `h_max`: optional in published files; defaults to 24 in eval/audit code.
- `max_actuations`: the artifact's `NA_max` value.
- `inp_file`: usually `networks/any-town.inp`.

The initial slot is explicit: `best_y[0] = 0` and `best_x[0:3]` are the hour-0
all-off pump states. Hours 1 through 24 occupy the remaining groups.

The per-pump order is `111`, `222`, `333`. This is the order used by
`BBConstraints` through its `std::map` pump keys and by the Python plotting and
checking scripts' `PUMP_ORDER`. The INP file lists the pump rows as `222`,
`111`, `333`, so later GOPS code should not derive schedule column order from
raw row order alone.

## Activation Semantics

The manuscript equation in `paper.tex` defines a total bidirectional transition
limit:

```text
sum_{h=2}^T |x_{j,h} - x_{j,h-1}| <= NA_max
```

The operative code is different. `BBSolver::updateX`, `main-eval`, and
`BBAudit` maintain separate per-pump budgets for starts (`0 -> 1`) and stops
(`1 -> 0`). Each budget is initialized to `max_actuations`.
`computeAllowedSwitches` starts counting historical transitions from `h = 2`,
so the explicit hour-0 to hour-1 initialization is present in `best_x` but is
not depleted as a historical actuation budget when constructing later hours.

For the EPANET-BB-equivalent GOPS experiment, the target is therefore:

- Separate start and stop budgets per pump.
- Each start budget and stop budget equals `NA_max`.
- The explicit hour-0 all-off initialization is retained.
- The hour-0 to hour-1 change must be represented in artifacts but should not
  be treated as evidence that the paper equation's total-transition semantics
  are the operative comparison target.

This mismatch must remain visible in later GOPS translation and validation.

## Hydraulic Checks

The executable constraints check:

- Tank levels for tanks `65`, `165`, `265` in `[66.53, 71.53] m`.
- Final stability against initial tank level `66.93 m`.
- Pressure thresholds: node `55 >= 42.0 m`, node `90 >= 51.0 m`, and node
  `170 >= 30.0 m`.
- Cost from the three pump energy totals.

The fixed-schedule clamp audit consumes `best_y`, reconstructs `x` under the
operative `max_actuations` semantics, runs the same simulation path, and emits
feasibility and clamp/boundary event summaries.

## Translation Requirements For #14

A GOPS-runnable representation for the next issue should validate these facts
before solver execution:

- It targets `../epanet-bb/networks/any-town.inp`, not GOPS `Anytown` by name.
- It preserves each junction base demand and assigned demand pattern from the
  INP source.
- It keeps three tanks `65`, `165`, and `265` with the level bounds above.
- It keeps three pumps `111`, `222`, and `333`, mapped to `best_x` columns in
  that order.
- It keeps 24 one-hour commanded periods plus the explicit hour-0 all-off slot.
- It uses the `DEM` demand pattern family and `PRICES` tariff pattern from the
  INP file, or documents any deliberate representation difference.
- It creates independent cases for `atm-24h-na1`, `atm-24h-na2`, and
  `atm-24h-na3`.
- It implements the operative separate start/stop `NA_max` accounting, not the
  manuscript equation's total bidirectional transition limit, unless a later
  ADR changes the target.

## Evidence Commands

The extraction used these commands:

```bash
git -C ../epanet-bb status --short --branch
git -C ../epanet-bb rev-parse HEAD
awk '
  BEGIN {
    want["[OPTIONS]"]=1
    want["[JUNCTIONS]"]=1
    want["[TANKS]"]=1
    want["[PUMPS]"]=1
    want["[PATTERNS]"]=1
    want["[TIMES]"]=1
  }
  {gsub(/\r/, "")}
  /^\[/ {section=$0}
  want[section] {print}
' ../epanet-bb/networks/any-town.inp
jq -r '[input_filename, .max_actuations, .inp_file, (.best_y|length), (.best_x|length), .best_cost, .duration] | @tsv' ../epanet-bb/paper/data/run_*_a_*.json
nl -ba ../epanet-bb/networks/any-town.inp
nl -ba ../epanet-bb/src/CLI/BBSolver.cpp
nl -ba ../epanet-bb/src/CLI/BBConstraints.cpp
nl -ba ../epanet-bb/src/CLI/BBAudit.cpp
nl -ba ../epanet-bb/paper/paper.tex
```
