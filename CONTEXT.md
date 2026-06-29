# GOPS Bonvin Audit Recovery

This context covers the investigation of whether public GOPS artifacts can produce Bonvin-style AnyTown Modified schedules suitable for the EPANET-BB clamp audit.

## Language

**AT(M)**:
AnyTown Modified, the benchmark family used in the Bonvin, Costa, and EPANET-BB comparison context. Do not use this term for a GOPS dataset until its network, horizon, profile, and scheduling constraints have been checked against the intended comparator.
_Avoid_: AnyTown as a synonym when identity has not been validated.

**Benchmark identity**:
The evidence that two benchmark instances represent the same comparison case for audit purposes. It covers network topology and parameters, demand and tariff profile, scheduling horizon, pump set, and activation constraints.
_Avoid_: Assuming identity from a matching dataset name.

**Audit-compatible schedule**:
A complete pump operation artifact that can be evaluated by the EPANET-BB clamp audit without inventing missing decisions. It must identify the horizon, pump activity over time, source method, and any mapping needed to compare it with EPANET-BB schedules.
_Avoid_: Aggregate runtime, cost, or optimality-gap reports.

**Auditable reproduction**:
A reproduction attempt whose conclusion can be checked from recorded commands, source files, solver/runtime conditions, generated artifacts, and explicit mapping decisions. A documented negative conclusion is acceptable when public artifacts are insufficient.
_Avoid_: Treating a failed schedule recovery as a failed investigation.

**Commanded pump schedule**:
The pump operation requested by an optimization method before hydraulic simulator boundary handling changes the effective operation. It may be represented by per-pump status or by a pump-count schedule plus a documented reconstruction rule.
_Avoid_: Effective hydraulic operation.

**Effective hydraulic operation**:
The operation actually simulated after hydraulic solver behavior such as tank-boundary handling, step shortening, or temporary link closure. It is not automatically identical to the commanded pump schedule.
_Avoid_: Commanded pump schedule.

**Activation limit**:
The maximum number of pump operation changes allowed in a scheduling case. This term is ambiguous unless the artifact states whether it limits starts only or both start and stop transitions.
_Avoid_: Treating horizon length as an activation limit.

**Start limit**:
A limit on commanded pump starts, i.e. `0 -> 1` transitions. In Bonvin's formulation this is represented by `N` through start variables, and public GOPS currently models this with ignition variables.
_Avoid_: Bidirectional actuation limit.

**Bidirectional actuation limit**:
A limit that separately constrains commanded pump starts and stops, i.e. `0 -> 1` and `1 -> 0` transitions. EPANET-BB's `max_actuations` uses this semantics.
_Avoid_: Start limit.

**EPANET-BB-equivalent GOPS experiment**:
A new experiment that adapts the GOPS method to run on the benchmark assumptions used by the EPANET-BB paper, including network, profile, horizon, pump reconstruction, and the operative actuation semantics of the published EPANET-BB artifacts. It is not a direct Bonvin public-artifact reproduction.
_Avoid_: Bonvin reproduction when GOPS semantics or data have been changed.

**Public artifact sufficiency**:
The standard for deciding whether the public GOPS repository contains enough information to support a clamp-audit comparison. If complete schedules or reproducible schedule generation are absent, the result is a documented insufficiency rather than a fabricated comparison.
_Avoid_: Filling gaps from literature summaries.

**Public-artifacts-only scope**:
An investigation boundary that uses the public GOPS repository, local article text, local EPANET-BB notes, and locally reproducible commands, without contacting Bonvin et al. for private reproduction materials. Missing private materials are recorded as required follow-up data rather than blockers to completing this PRD.
_Avoid_: Open-ended author outreach inside this workstream.

**Solver-faithful run**:
A GOPS execution attempt that uses the solver stack expected by the public code, especially `gurobipy` and a valid Gurobi license when the model size requires it. Results from another solver may be useful diagnostics, but they are not treated as a Bonvin/GOPS reproduction unless a separate decision justifies the substitution.
_Avoid_: Silent solver replacement.
