# EPANET-BB AnyTown Modified Source Of Truth

Implemented for: `michaelsouza/gopslpnlpbb#12`

Parent PRD: `michaelsouza/gopslpnlpbb#10`

Machine-readable companion: `docs/epanet-bb-anytown-modified-source-of-truth.json`

## Purpose

This document extracts the operative EPANET-BB AnyTown Modified benchmark
surface that the EPANET-BB-equivalent GOPS track must target. It uses the
neighboring EPANET-BB repository as the source of truth and keeps this target
separate from the Bonvin public-artifact sufficiency workstream.

When manuscript prose conflicts with code or schedule artifacts, later GOPS
translation should target the code and published artifacts and record the
conflict.

## Source Snapshot

Source project:

```text
C:\Users\Michael\gitrepos\epanet-bb
```

Snapshot inspected:

| Field | Value |
| ----- | ----- |
| Branch | `reviewer-fixes` |
| Commit | `34cabb94eae4f85f90efd49ada0a0f2fb019a326` |
| Dirty worktree | `false` |

Key source files:

| File | Role | SHA-256 |
| ---- | ---- | ------- |
| `networks/any-town.inp` | Operative network/profile/tariff input | `c6104ab9283c9b7eb06bd3ace44bca2a4dcf4776f86886fd7508a35ce2dad9c3` |
| `paper/data/run_Souza2026_a_01.json` | EPANET-BB schedule artifact, `NA_max = 1` | `0b996d0539c60bc0c94a55518d8eae039957893983e173f6eafa19def22ccc38` |
| `paper/data/run_Souza2026_a_02.json` | EPANET-BB schedule artifact, `NA_max = 2` | `4b912a0701d469521579f8e9f74f3d1f60f66d211e55ab343a1aec25694cfba6` |
| `paper/data/run_Souza2026_a_03.json` | EPANET-BB schedule artifact, `NA_max = 3` | `9f1b78b77bdfa0734927116f9781941e58114b72b51bc9a82457473ead43e9bc` |
| `src/CLI/BBSolver.cpp` | Operative `best_y -> best_x` and actuation accounting | `88938c70792e43bec83e6eb8566d7fe2d5f6323152a253bf951a57632a8a0437` |
| `src/CLI/main-eval.cpp` | Fixed-schedule evaluator mirroring `best_y -> best_x` accounting | `8928a681d6cb86f9b9e4f48580bc63f0a198280be8b717011b32335ace1daede` |
| `src/CLI/BBConstraints.cpp` | Pump/tank/node IDs, pump-order map, output shape | `a23ea9f0a7785abc375f76a5912be71ca9ef78f1ce5238ac5a0f3e5a2b7ba72d` |
| `paper/paper.tex` | Manuscript prose/equations and reported results | `97e669d0e0609b5450581572774c555268ebcece428be15fdf163d05ac35e778` |

## Benchmark Surface

The GOPS target is the 24-hour AnyTown Modified benchmark from
`networks/any-town.inp`.

Network counts from the operative INP:

| Element | Count |
| ------- | ----- |
| Junction rows | 19 |
| Reservoir rows | 1 |
| Tank rows | 3 |
| Pipe rows | 41 |
| Pump rows | 3 |
| Valve rows | 0 |
| Pipe plus pump links | 44 |

The manuscript describes the network as having 44 pipes. The INP has 41
`[PIPES]` rows plus 3 `[PUMPS]` rows, for 44 pipe-or-pump link rows. Later
translation should treat the INP representation as the operative target.

Hydraulic/profile horizon:

| Field | Value |
| ----- | ----- |
| Optimization horizon | 24 one-hour decision periods |
| `best_y` length | `h_max + 1 = 25`, including `best_y[0] = 0` |
| `best_x` length | `(h_max + 1) * 3 = 75`, flattened by hour and pump |
| Hydraulic timestep in INP | 30 minutes |
| Pattern timestep in INP | 1 hour |
| Duration in INP | 24 hours |

Demand pattern IDs `DEM`, `DEM55`, `DEM90`, and `DEM170` all carry the same
24 hourly multipliers:

```text
[0.7, 0.7, 0.7, 0.6, 0.6, 0.6, 1.2, 1.2, 1.2, 1.3, 1.3, 1.3,
 1.2, 1.2, 1.2, 1.0, 1.0, 1.0, 0.9, 0.9, 0.9, 0.7, 0.7, 0.7]
```

Energy tariff pattern `PRICES`:

```text
[18.14, 18.14, 18.14, 18.14, 18.14, 18.14, 18.14, 35.28, 35.28,
 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 80.97,
 80.97, 80.97, 80.97, 18.14, 18.14, 18.14]
```

Demand nodes:

| Node | Elevation m | Base demand CMH | Pattern |
| ---- | ----------- | --------------- | ------- |
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

Reservoir and tanks:

| Element | ID | Operative representation |
| ------- | -- | ------------------------ |
| Reservoir | `10` | Head `3.048` m |
| Tank | `65` | Elevation `0`, init `66.93` m, min `66.53` m, max `71.53` m, diameter `21.55` m |
| Tank | `165` | Elevation `0`, init `66.93` m, min `66.53` m, max `71.53` m, diameter `21.55` m |
| Tank | `265` | Elevation `0`, init `66.93` m, min `66.53` m, max `71.53` m, diameter `21.55` m |

Pumps:

| INP order | Pump id | From | To | Head curve | Speed pattern |
| --------- | ------- | ---- | -- | ---------- | ------------- |
| 1 | `222` | `10` | `20` | `1` | `PMP222` |
| 2 | `111` | `10` | `20` | `1` | `PMP111` |
| 3 | `333` | `10` | `20` | `1` | `PMP333` |

The B&B code and analysis scripts use the pump-order map `111`, `222`, `333`
for `best_x`. A `best_x` vector is flattened as:

```text
[h0_111, h0_222, h0_333, h1_111, h1_222, h1_333, ... h24_333]
```

## First-Class GOPS Target Cases

The EPANET-BB-equivalent GOPS track has exactly these target cases:

| Case id | `NA_max` | Source schedule artifact |
| ------- | -------- | ------------------------ |
| `atm-24h-na1` | 1 | `paper/data/run_Souza2026_a_01.json` |
| `atm-24h-na2` | 2 | `paper/data/run_Souza2026_a_02.json` |
| `atm-24h-na3` | 3 | `paper/data/run_Souza2026_a_03.json` |

Each case targets the same network, demand profile, tariff profile, pump set,
tank set, and 24-hour horizon. The only target-case parameter that changes is
the operative `max_actuations`/`NA_max` value.

## Operative Actuation Semantics

The manuscript equation states a total-transition limit:

```text
sum_{h=2..T} |x[j,h] - x[j,h-1]| <= NA_max
```

The operative code and artifacts do not behave like a single total-transition
budget. They behave like separate per-pump budgets for starts and stops:

- Starts are `0 -> 1` transitions.
- Stops are `1 -> 0` transitions.
- `allowed_01` starts at `NA_max` for every pump.
- `allowed_10` starts at `NA_max` for every pump.
- The all-off initial state is encoded at `h = 0`.
- `computeAllowedSwitches` iterates historical transitions from `i = 2` to
  `i < current_h`, so the initial transition between `h = 0` and `h = 1` is
  not charged to either budget.
- The current transition is allowed only if the corresponding remaining
  start/stop budget is positive; it is then reflected in future historical
  counts.
- Pump selection uses Least Used Selection when pump sorting is enabled:
  switch-ons prefer the most remaining starts, then stops; switch-offs prefer
  the most remaining stops, then starts.

This is the target semantics for `atm-24h-na1`, `atm-24h-na2`, and
`atm-24h-na3`. Later GOPS work must not implement the manuscript total
transition equation as the comparison target unless it deliberately labels the
run as a different experiment.

Evidence from the published EPANET-BB schedules confirms the difference. For
`run_Souza2026_a_01.json`, pump `111` has two starts if the initial `h=0 -> h=1`
transition is counted, but only one start under the operative accounting.
Therefore it satisfies the operative `NA_max = 1` case while violating a
single total-transition reading.

## Published Schedule Artifacts

The schedule-bearing paper artifacts are:

| File | `NA_max` | Cost | Duration s |
| ---- | -------- | ---- | ---------- |
| `paper/data/run_Costa2016_a_01.json` | 1 | 3916.98 | 425 |
| `paper/data/run_Costa2016_a_02.json` | 2 | 3618.59 | 36914 |
| `paper/data/run_Costa2016_a_03.json` | 3 | 3578.67 | 292032 |
| `paper/data/run_Cimorelli2020_a_01.json` | 1 | 3634.67 | 663 |
| `paper/data/run_Cimorelli2020_a_02.json` | 2 | 3580.11 | 663 |
| `paper/data/run_Cimorelli2020_a_03.json` | 3 | 3575.54 | 663 |
| `paper/data/run_Paola2025_a_01.json` | 1 | 3911.52 | 72 |
| `paper/data/run_Paola2025_a_02.json` | 2 | 3606.22 | 904 |
| `paper/data/run_Paola2025_a_03.json` | 3 | 3577.40 | 960 |
| `paper/data/run_Souza2026_a_01.json` | 1 | 3567.988684015254 | 3.692231000000002 |
| `paper/data/run_Souza2026_a_02.json` | 2 | 3472.8912332008294 | 493.1143470000003 |
| `paper/data/run_Souza2026_a_03.json` | 3 | 3443.458721124687 | 10011.228562000002 |

Every listed JSON contains:

- `best_x` with 75 flattened pump states.
- `best_y` with 25 pump-count states.
- `max_actuations`.
- `inp_file = "networks/any-town.inp"`.
- `best_cost`.
- `duration`.

For GOPS translation, these artifacts are comparator evidence, not substitutes
for a GOPS-derived schedule. The later GOPS runner must produce its own
schedule artifacts under `output/epanet_bb_equivalent_gops/<case_id>/<run_id>/`.

## Mismatches To Carry Forward

- **Paper actuation equation vs code/artifacts:** the paper states a total
  transition budget, while code and artifacts use separate start and stop
  budgets and do not count the initial `h=0 -> h=1` transition.
- **Paper network count wording vs INP rows:** the paper says 44 pipes; the
  INP has 41 pipe rows plus 3 pump rows. Use the INP.
- **INP pump order vs `best_x` order:** the INP lists pumps as `222`, `111`,
  `333`, while `BBConstraints` and analysis scripts use `111`, `222`, `333`.
  GOPS export must record this mapping explicitly.
- **Cost table drift:** `paper/data/comparison_summary.csv` has a stale or
  inconsistent `EPANET-BB` value for `NA_max = 3` (`3444.71`), while
  `paper/data/run_Souza2026_a_03.json` and manuscript prose report
  approximately `3443.46`. Use the schedule JSON for artifact-level work.

## Handoff To GOPS Translation

Issue #14 should treat `docs/epanet-bb-anytown-modified-source-of-truth.json`
as the local, durable extraction of the target. The GOPS translated case should
validate at least:

- Case id and `NA_max` are one of `atm-24h-na1`, `atm-24h-na2`,
  `atm-24h-na3`.
- Horizon is 24 one-hour periods with `best_y`/`best_x` compatibility.
- Network target is `networks/any-town.inp` from the EPANET-BB snapshot.
- Demand and tariff vectors match the 24 values recorded here.
- Pump IDs and export order are deterministic.
- Tanks `65`, `165`, and `265` are represented separately.
- Actuation accounting follows the operative separate start/stop budgets with
  the initial transition uncharged.
- GOPS outputs remain under the EPANET-BB-equivalent GOPS output namespace, not
  the Bonvin public-artifact namespace.
