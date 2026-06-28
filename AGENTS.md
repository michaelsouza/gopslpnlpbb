## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for the fork `michaelsouza/gopslpnlpbb`; external PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label triage vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses a single-context domain-doc layout: root `CONTEXT.md` plus ADRs in `docs/adr/`. See `docs/agents/domain.md`.

## Current workstream

The active collaboration branch is `bonvin-atm-audit`, tracking `origin/bonvin-atm-audit` on the fork `michaelsouza/gopslpnlpbb`. The original public repository is kept as `upstream` at `https://github.com/sofdem/gopslpnlpbb.git`.

The active PRD is GitHub issue `michaelsouza/gopslpnlpbb#1`: "PRD: Auditable Bonvin AT(M) GOPS reproduction for EPANET-BB clamp audit".

This workstream should produce an auditable reproduction outcome: either complete GOPS/Bonvin schedules normalized and audited with EPANET-BB, or a documented insufficiency note showing that public GOPS artifacts are not enough. Do not invent schedules from aggregate runtime, cost, or gap values. Use Gurobi/`gurobipy` as the solver-faithful path; any non-Gurobi solver attempt is only a separately documented diagnostic fallback.
