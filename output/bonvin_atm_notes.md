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

- Compare GOPS `ANY`/`Anytown` against the AT(M) comparator before treating them as the same case.
- Record network, pump set, tank/source structure, demand and tariff profile, horizon, and any known mismatch.

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
