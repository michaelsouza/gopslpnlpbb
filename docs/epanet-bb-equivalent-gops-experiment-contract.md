# EPANET-BB-equivalent GOPS Experiment Contract

Contract version: `epanet-bb-equivalent-gops-v1`

Parent PRD: `michaelsouza/gopslpnlpbb#10`

Implemented for: `michaelsouza/gopslpnlpbb#11`

## Purpose

This contract defines the durable artifact shape for the
EPANET-BB-equivalent GOPS experiment track. It is the handoff between the
benchmark translation, GOPS/Gurobi execution, schedule export, downstream
EPANET-BB audit, and final comparison issues.

This track is a new GOPS-method experiment on EPANET-BB paper assumptions. It
is not a Bonvin public-artifact reproduction. Artifacts from this track must be
named and described separately from the Bonvin public-artifact sufficiency
notes and outputs.

## First-Class Cases

The experiment surface contains exactly three first-class cases:

| Case id | `NA_max` | Benchmark target | Horizon | Pump target | Tank target |
| ------- | -------- | ---------------- | ------- | ----------- | ----------- |
| `atm-24h-na1` | 1 | AnyTown Modified | 24 one-hour periods | Three parallel fixed-speed pumps | Tanks 65, 165, and 265 |
| `atm-24h-na2` | 2 | AnyTown Modified | 24 one-hour periods | Three parallel fixed-speed pumps | Tanks 65, 165, and 265 |
| `atm-24h-na3` | 3 | AnyTown Modified | 24 one-hour periods | Three parallel fixed-speed pumps | Tanks 65, 165, and 265 |

Every run artifact, schedule artifact, audit artifact, and comparison row must
carry the case id and `NA_max`. Case ids are immutable and must appear in
output paths, so separate `NA_max` runs cannot overwrite each other.

## Output Namespace

EPANET-BB-equivalent GOPS outputs belong under:

```text
output/epanet_bb_equivalent_gops/<case_id>/<run_id>/
```

The expected files in a completed run directory are:

| File | Required when | Purpose |
| ---- | ------------- | ------- |
| `run.json` | Always | Primary run manifest and status artifact |
| `schedule.json` | A complete commanded pump schedule exists | EPANET-BB-compatible schedule export |
| `audit.json` | A complete schedule has been audited downstream | EPANET-BB audit result summary |
| `solver.log` | Solver emitted a useful log | Solver-side diagnostic evidence |

Do not put this track's outputs under `output/bonvin_*`, and do not reuse
Bonvin public-artifact sufficiency filenames for adapted EPANET-BB-equivalent
experiments.

## Run Classes

Each run must declare one of these run classes:

| Run class | Meaning | Host rule |
| --------- | ------- | --------- |
| `final` | Candidate evidence for the paper-facing comparison | Must run on `labma-sol` |
| `smoke` | Minimal environment or wiring check | May run locally or remotely |
| `dev` | Development run while building the experiment path | May run locally or remotely |
| `diagnostic` | Explicitly non-final investigation, including nonstandard settings or instrumentation | May run locally or remotely |

Only `final` runs should be used in the final comparison. A local run can help
develop or test the path, but it is not final evidence unless a later ADR or
issue explicitly promotes that policy.

## Required Metadata

The primary `run.json` manifest must include the following metadata groups.
The JSON Schema in
`docs/schemas/epanet-bb-equivalent-gops-run.schema.json` defines the
machine-readable contract.

The source-of-truth benchmark extraction for the three cases is recorded in
`docs/epanet-bb-source-of-truth-cases.md`, with a machine-readable companion at
`docs/epanet-bb-source-of-truth-cases.json`.

| Group | Required fields |
| ----- | --------------- |
| Contract | `contract_version`, `track` |
| Case | `case_id`, benchmark identity, horizon, `NA_max`, pump set, tank representation, activation semantics |
| Git provenance | repository URL, branch, commit SHA, dirty-worktree flag |
| Execution environment | host name, run class, working directory, Python version, command |
| Solver | solver name, Gurobi version when available, `gurobipy` version when available, license status |
| Runtime settings | time limit, MIP gap, GOPS mode/options, random seed if used |
| Status | run status, schedule availability, status detail |
| Outputs | run manifest path, schedule path when present, audit path when present, solver log path when present |

The manifest may include additional implementation-specific fields, but these
fields are the minimum needed to audit a result without reading terminal
history.

## Status Vocabulary

Use these status values for `status.run_status`:

| Status | Meaning |
| ------ | ------- |
| `success` | Solver finished and produced an accepted complete commanded schedule |
| `time_limit_with_schedule` | Solver hit a time limit but produced an accepted complete commanded schedule |
| `time_limit_no_schedule` | Solver hit a time limit and no complete commanded schedule is available |
| `infeasible` | Solver or model concluded the case is infeasible |
| `license_blocked` | Gurobi could not run because the license was missing, expired, restricted, or invalid for the host/model |
| `environment_blocked` | Required runtime environment, data, repo state, or dependency is missing |
| `solver_error` | Solver failed for a reason other than a declared license blocker |
| `validation_failed` | The run produced an artifact that violates this contract or the case contract |
| `audit_failed` | A complete schedule exists, but the downstream EPANET-BB audit failed or could not run |

Use these values for `status.schedule_availability`:

| Schedule availability | Meaning |
| --------------------- | ------- |
| `complete_commanded_schedule` | A fixed-period commanded pump schedule is available for all 24 periods |
| `adjusted_only` | Only an adjusted or variable-duration heuristic schedule is available |
| `incomplete` | Some commanded pump decisions are missing |
| `none` | No commanded pump schedule is available |

A missing or blocked Gurobi license must be reported as `license_blocked`; it
is not evidence that the model is infeasible, that GOPS fails scientifically,
or that no schedule exists.

## Schedule Contract

When `schedule.json` exists, it must be a commanded pump schedule before
downstream hydraulic simulator boundary handling. It must include:

- The same `contract_version`, `track`, `case_id`, and `NA_max` as `run.json`.
- `best_y`, representing the 24-period pump-count or aggregate commanded
  schedule used by EPANET-BB comparison tooling.
- `best_x` when per-pump statuses are available from GOPS.
- A deterministic pump mapping from GOPS identifiers to EPANET-BB pump ids.
- A reconstruction rule if `best_y` is expanded into per-pump statuses.
- Cost and duration fields when they are available from the run.

Aggregate cost, runtime, gap, or bound values are never schedule substitutes.
If a run has no complete fixed-period commanded schedule, the run must still
write `run.json`, but it must not fabricate `schedule.json`.

## Activation Semantics

The case metadata must declare the operative activation semantics used for the
run. For this PRD, the target is the EPANET-BB operative artifact/code
semantics, not the public GOPS hardcoded start-limit semantics. Later issues
must document the exact start/stop and initialization accounting before a run
can be treated as comparable.

The original Bonvin/GOPS start-limit path remains a separate reproduction
surface. Any adapted `NA_max` implementation must be labeled as
EPANET-BB-equivalent GOPS.

## Final Execution Host

Final experiment runs must execute on `labma-sol` through `ssh labma-sol`.
`run.json` must record:

- `environment.host_name = "labma-sol"` for `final` runs.
- The remote repository path.
- The checked-out branch and commit.
- Whether the remote worktree was dirty.
- Gurobi and `gurobipy` versions when the solver can be imported.
- License status without printing, copying, or committing license contents.

## Validation Rules

A future validator or runner should reject an artifact when:

- `track` is not `epanet-bb-equivalent-gops`.
- `contract_version` is not `epanet-bb-equivalent-gops-v1`.
- `case_id` and `NA_max` do not match one of the three first-class cases.
- A `final` run was not executed on `labma-sol`.
- Required benchmark, horizon, pump, tank, solver, status, or output metadata
  is missing.
- A run reports `success` or `time_limit_with_schedule` without a complete
  commanded schedule.
- The artifact is named or stored as a Bonvin public-artifact sufficiency
  output.
