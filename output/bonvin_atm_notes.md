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

- Record how GOPS instance keys map to benchmark, profile, horizon, and day.
- Record whether the Bonvin-Costa activation limit `N = 1, 2, 3` is represented in public GOPS code or data.

### Schedule Availability

- Record whether public outputs or local GOPS runs contain complete commanded pump schedules.
- Reject aggregate runtime, cost, or optimality-gap values as schedule substitutes.
- Preserve per-pump status provenance if available.

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
