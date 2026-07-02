# EPANET-BB GOPS Case Translation

Implemented for: `michaelsouza/gopslpnlpbb#14`

Parent PRD: `michaelsouza/gopslpnlpbb#10`

Machine-readable companion: `docs/epanet-bb-gops-case-translation.json`

## Purpose

This document records the GOPS-runnable representation of the EPANET-BB
AnyTown Modified paper case. It turns the source-of-truth extraction in
`docs/epanet-bb-source-of-truth-cases.json` into a GOPS `Instance` input while
keeping this EPANET-BB-equivalent experiment separate from the Bonvin public
artifact sufficiency path.

The translated base instance is:

```text
ATM e 24 1
```

`ATM` selects the new `data/EpanetBB_Anytown` dataset, `e` selects the
EPANET-BB 1-hour profile, `24` selects a 24-hour horizon, and the final token
remains the GOPS day selector. It is not an `NA_max` selector; `NA_max = 1, 2,
3` handling belongs to issue #15.

## Runnable GOPS Inputs

The translated dataset lives under:

```text
data/EpanetBB_Anytown/
```

It contains the normal GOPS CSV files consumed by `src/instance.py`:

- `Junction.csv`
- `Reservoir.csv`
- `History_V_0.csv`
- `Source.csv`
- `Pump.csv`
- `Pipe.csv`
- `Valve_Set.csv`
- `Profile_epanet_bb_1d_1h.csv`

`src/gops.py` now exposes benchmark key `ATM` and profile key `e`, so a
Gurobi-capable GOPS environment can construct the base case with
`makeinstance("ATM e 24 1")`. The module-level benchmark run in `gops.py` is
guarded behind `if __name__ == "__main__"`, so importing `gops` no longer
starts unrelated public benchmark solves.

The validation tool constructs the translated case through `Instance`
directly:

```text
python tools/validate_epanet_bb_gops_case.py
```

The direct `Instance` path avoids requiring Gurobi for this translation check.

## Representation Decisions

### Demand

EPANET-BB stores base demands in `CMH`; GOPS `Instance` expects junction base
demands in `L/s`. The translation divides every EPANET-BB base demand by
`3.6`.

The 24 hourly demand multipliers match the EPANET-BB source-of-truth `DEM`
pattern. `DEM55`, `DEM90`, and `DEM170` are represented separately because the
INP assigns those pattern names, but their values are the same as `DEM`, as in
the operative source-of-truth file.

### Tariff

`Profile_epanet_bb_1d_1h.csv` uses the 24 hourly `PRICES` values from
`docs/epanet-bb-source-of-truth-cases.json` directly:

```text
[18.14, 18.14, 18.14, 18.14, 18.14, 18.14, 18.14, 35.28, 35.28,
 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 35.28, 80.97,
 80.97, 80.97, 80.97, 18.14, 18.14, 18.14]
```

This deliberately differs from public GOPS `data/Anytown/Profile_1d_1h.csv`,
which uses a different tariff scale and demand pattern.

### Tanks

The EPANET-BB tanks `65`, `165`, and `265` are represented explicitly as GOPS
tanks `T65`, `T165`, and `T265`.

The GOPS tank volume fields are computed from the EPANET-BB levels and
diameter:

```text
surface = pi * (21.55 / 2)^2
vmin = 66.53 * surface
vinit = 66.93 * surface
vmax = 71.53 * surface
```

This avoids the public GOPS `Anytown` collapse where tanks `165` and `265`
appear as a single larger `T165` storage element.

### Source And Pumps

EPANET-BB has one reservoir/source node `10` and three parallel fixed-speed
pumps from `10` to `20`.

The current GOPS `Instance` stores pumps in a dictionary keyed by `(start,
end)` node pair, so three pumps with the same start and end would collide. The
translation therefore represents source node `10` as three GOPS source rows:
`R111`, `R222`, and `R333`, each with head `3.048` and constant profile. This
is a deliberate representation decision that preserves one source head per
pump while keeping all three pump arcs distinct for GOPS.

The deterministic pump mapping is:

| GOPS pump arc | GOPS pump id | EPANET-BB pump id | `best_x` column |
| --- | --- | --- | ---: |
| `R111 -> J20` | `111` | `111` | 0 |
| `R222 -> J20` | `222` | `222` | 1 |
| `R333 -> J20` | `333` | `333` | 2 |

`src/instance.py` marks these three arcs as symmetric for
`EpanetBB_Anytown`.

### Pipes

The translated pipe table keeps the public GOPS AnyTown polynomial pipe
coefficients, with the topology corrected to the EPANET-BB source-of-truth
tank set: pipe `T178` is `J140 -> T265`, not `J140 -> T165`.

This is a recorded representation assumption. The GOPS model consumes
polynomial head-loss coefficients, whereas the EPANET-BB INP is the operative
hydraulic source. Later solver/audit issues should keep this assumption in run
metadata.

## First-Class Cases

The three first-class EPANET-BB-equivalent GOPS cases share the translated
base instance and differ only by the `NA_max` value that issue #15 will attach:

| Case id | `NA_max` | GOPS base instance |
| --- | ---: | --- |
| `atm-24h-na1` | 1 | `ATM e 24 1` |
| `atm-24h-na2` | 2 | `ATM e 24 1` |
| `atm-24h-na3` | 3 | `ATM e 24 1` |

No schedule is inferred or imported from EPANET-BB paper costs or aggregate
statistics. The published EPANET-BB schedules remain comparison artifacts, not
GOPS schedules.

## Validation

`tools/validate_epanet_bb_gops_case.py` checks:

- The three case ids and `NA_max` values are present.
- The translated `Instance` constructs with 24 one-hour periods.
- Demand and tariff profiles match the EPANET-BB source-of-truth values.
- Every junction base demand matches the source demand after `CMH -> L/s`
  conversion.
- Tanks `T65`, `T165`, and `T265` reconstruct the EPANET-BB levels from GOPS
  volume/surface fields.
- The source decomposition uses three constant-head source rows at the
  EPANET-BB source head.
- Pump arcs, pump ids, `best_x` columns, and symmetry metadata are
  deterministic.
- The translated dataset has 41 pipe rows, 3 pump rows, 3 tanks, and no valves.

This is a construction and validation slice. It intentionally does not solve a
Gurobi model and does not implement `NA_max`; those are later issues.
