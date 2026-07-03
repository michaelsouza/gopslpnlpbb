#!/usr/bin/env python3
"""Run or smoke-build an EPANET-BB-equivalent GOPS experiment case."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CONTRACT_VERSION = "epanet-bb-equivalent-gops-v1"
TRACK = "epanet-bb-equivalent-gops"
DEFAULT_OUTPUT_ROOT = Path("output/epanet_bb_equivalent_gops")


@dataclass(frozen=True)
class OutputPaths:
    root: Path
    run_manifest: Path
    schedule_json: Path
    audit_json: Path
    solver_log: Path


@dataclass(frozen=True)
class ScheduleCandidate:
    schedule_availability: str
    detail: str
    artifact: dict[str, Any] | None
    summary: dict[str, Any]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return _repo_relative(value)
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if math.isnan(value):
            return "nan"
        return "inf" if value > 0 else "-inf"
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _git(args: list[str], default: str = "unknown") -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return default


def _git_metadata() -> dict[str, Any]:
    return {
        "repository": _git(["remote", "get-url", "origin"]),
        "branch": _git(["branch", "--show-current"]),
        "commit": _git(["rev-parse", "HEAD"]),
        "dirty": bool(_git(["status", "--porcelain"], default="")),
    }


def _utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def make_output_paths(
    case_id: str,
    run_id: str,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> OutputPaths:
    root = output_root / case_id / run_id
    return OutputPaths(
        root=root,
        run_manifest=root / "run.json",
        schedule_json=root / "schedule.json",
        audit_json=root / "audit.json",
        solver_log=root / "solver.log",
    )


def make_case_metadata(case_id: str) -> dict[str, Any]:
    _ensure_src_imports()
    from activation import EPANET_BB_OPERATIVE_SEMANTICS, resolve_epanet_bb_case

    case = resolve_epanet_bb_case(case_id)
    return {
        "case_id": case.case_id,
        "benchmark_identity": {
            "family": "AnyTown Modified",
            "target": "EPANET-BB paper case",
            "source_of_truth": "docs/epanet-bb-source-of-truth-cases.json",
        },
        "horizon": {
            "periods": 24,
            "period_duration_hours": 1,
        },
        "na_max": case.na_max,
        "pumps": [
            {"epanet_id": "111", "gops_id": "111", "gops_arc": ["R111", "J20"], "best_x_column": 0},
            {"epanet_id": "222", "gops_id": "222", "gops_arc": ["R222", "J20"], "best_x_column": 1},
            {"epanet_id": "333", "gops_id": "333", "gops_arc": ["R333", "J20"], "best_x_column": 2},
        ],
        "tanks": {
            "target_ids": ["65", "165", "265"],
            "gops_representation": "explicit tanks T65, T165, and T265",
        },
        "activation_semantics": {
            "id": EPANET_BB_OPERATIVE_SEMANTICS,
            "target": "operative-epanet-bb-artifacts",
            "accounting": "separate per-pump start and stop budgets, each equal to NA_max",
            "initialization": "explicit h=0 all-off state; h=0 -> h=1 transition is not charged",
        },
        "gops_base_instance_key": case.gops_base_instance_key,
    }


def make_run_manifest(
    *,
    case_id: str,
    run_class: str,
    command: list[str],
    paths: OutputPaths,
    host_name: str,
    working_directory: Path,
    runtime_settings: dict[str, Any],
    status: dict[str, Any],
    solver: dict[str, Any],
    model: dict[str, Any] | None = None,
    git_metadata: dict[str, Any] | None = None,
    schedule_written: bool = False,
    audit_written: bool = False,
) -> dict[str, Any]:
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "track": TRACK,
        "case": make_case_metadata(case_id),
        "git": git_metadata or _git_metadata(),
        "environment": {
            "run_class": run_class,
            "host_name": host_name,
            "working_directory": str(working_directory),
            "python_version": sys.version,
            "command": command,
            "platform": platform.platform(),
        },
        "solver": solver,
        "runtime_settings": runtime_settings,
        "status": status,
        "outputs": {
            "root": _repo_relative(ROOT / paths.root),
            "run_manifest": _repo_relative(ROOT / paths.run_manifest),
            "schedule_json": _repo_relative(ROOT / paths.schedule_json) if schedule_written else None,
            "audit_json": _repo_relative(ROOT / paths.audit_json) if audit_written else None,
            "solver_log": _repo_relative(ROOT / paths.solver_log),
        },
    }
    if model is not None:
        manifest["model"] = model
    return manifest


def classify_exception(exc: BaseException) -> dict[str, Any]:
    message = str(exc)
    lowered = message.lower()
    if "license" in lowered or "hostid" in lowered:
        return {
            "run_status": "license_blocked",
            "schedule_availability": "none",
            "detail": message,
        }
    if isinstance(exc, (ImportError, ModuleNotFoundError, FileNotFoundError)):
        return {
            "run_status": "environment_blocked",
            "schedule_availability": "none",
            "detail": message,
        }
    return {
        "run_status": "solver_error",
        "schedule_availability": "none",
        "detail": message,
    }


def classify_license_status(message: str) -> str:
    lowered = message.lower()
    if "size-limited" in lowered or "restricted" in lowered:
        return "restricted"
    if "expired" in lowered:
        return "expired"
    if "hostid" in lowered:
        return "hostid_mismatch"
    if "no gurobi license" in lowered or "no license" in lowered or "not found" in lowered:
        return "missing"
    return "invalid"


def _status_name(gp: Any, status: int | None) -> str | None:
    if status is None:
        return None
    mapping = {
        gp.GRB.OPTIMAL: "OPTIMAL",
        gp.GRB.INFEASIBLE: "INFEASIBLE",
        gp.GRB.INF_OR_UNBD: "INF_OR_UNBD",
        gp.GRB.UNBOUNDED: "UNBOUNDED",
        gp.GRB.TIME_LIMIT: "TIME_LIMIT",
        gp.GRB.INTERRUPTED: "INTERRUPTED",
        gp.GRB.NUMERIC: "NUMERIC",
        gp.GRB.SUBOPTIMAL: "SUBOPTIMAL",
    }
    return mapping.get(status, f"STATUS_{status}")


def _safe_attr(obj: Any, name: str) -> Any:
    try:
        return getattr(obj, name)
    except Exception as exc:
        return {"unavailable": str(exc)}


def _solver_dict(gp: Any | None = None, license_status: str = "not_checked") -> dict[str, Any]:
    solver = {
        "name": "Gurobi",
        "license_status": license_status,
    }
    license_file = os.environ.get("GRB_LICENSE_FILE")
    if license_file:
        solver["license_file"] = license_file
    if gp is not None:
        version = ".".join(str(part) for part in gp.gurobi.version())
        solver.update(
            {
                "gurobi_version": version,
                "gurobipy_version": getattr(gp, "__version__", version),
            }
        )
    return solver


def _ensure_src_imports() -> None:
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))


def _method_name(args: argparse.Namespace) -> str:
    names = {
        "build": "GOPS Gurobi model build",
        "cvx": "GOPS convex-relaxation Gurobi diagnostic",
        "lpnlpbb": "GOPS LP-NLP branch-and-bound",
    }
    return names[args.execution_mode]


def _finite_number(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    return None


def _binary_value(value: Any, context: str) -> int:
    numeric = float(value)
    rounded = int(round(numeric))
    if rounded not in (0, 1) or abs(numeric - rounded) > 1e-5:
        raise ValueError(f"{context} has non-binary commanded value {value!r}")
    return rounded


def _pump_arc_by_epanet_id(instance: Any, pump_order: tuple[str, ...]) -> dict[str, tuple[str, str]]:
    arcs_by_id = {str(pump.id): arc for arc, pump in instance.pumps.items()}
    missing = [pump_id for pump_id in pump_order if pump_id not in arcs_by_id]
    if missing:
        raise ValueError(f"GOPS instance is missing EPANET-BB pump ids: {', '.join(missing)}")
    return {pump_id: arcs_by_id[pump_id] for pump_id in pump_order}


def _schedule_vectors_from_plan(
    plan: dict[int, dict[tuple[str, str], Any]],
    instance: Any,
) -> dict[str, Any]:
    _ensure_src_imports()
    from activation import EPANET_BB_PUMP_ORDER, count_start_stop_transitions

    pump_order = EPANET_BB_PUMP_ORDER
    periods = list(instance.horizon())
    if len(periods) != 24:
        raise ValueError(f"expected 24 GOPS periods, got {len(periods)}")

    arc_by_pump = _pump_arc_by_epanet_id(instance, pump_order)
    statuses_by_pump = {pump_id: [] for pump_id in pump_order}
    best_y = [0]
    best_x = [0 for _ in pump_order]

    for period in periods:
        if period not in plan:
            raise ValueError(f"missing GOPS commanded activity for period {period}")

        hour_values = []
        for pump_id in pump_order:
            arc = arc_by_pump[pump_id]
            if arc not in plan[period]:
                raise ValueError(f"missing GOPS commanded activity for pump {pump_id} in period {period}")
            value = _binary_value(plan[period][arc], f"pump {pump_id} period {period}")
            statuses_by_pump[pump_id].append(value)
            hour_values.append(value)

        best_x.extend(hour_values)
        best_y.append(sum(hour_values))

    transition_counts = []
    for pump_id in pump_order:
        series_with_initial = [0, *statuses_by_pump[pump_id]]
        excluding_initial = count_start_stop_transitions(series_with_initial, count_initial=False)
        including_initial = count_start_stop_transitions(series_with_initial, count_initial=True)
        transition_counts.append(
            {
                "pump": pump_id,
                "starts_excluding_initial": excluding_initial["starts"],
                "stops_excluding_initial": excluding_initial["stops"],
                "starts_including_initial": including_initial["starts"],
                "stops_including_initial": including_initial["stops"],
            }
        )

    return {
        "best_y": best_y,
        "best_x": best_x,
        "statuses_by_pump": statuses_by_pump,
        "transition_counts": transition_counts,
        "pump_order": pump_order,
        "arc_by_pump": arc_by_pump,
    }


def _make_schedule_artifact(
    args: argparse.Namespace,
    instance: Any,
    plan: dict[int, dict[tuple[str, str], Any]],
    *,
    source: dict[str, Any],
    cost: Any,
    duration: Any,
) -> dict[str, Any]:
    _ensure_src_imports()
    from activation import EPANET_BB_PUMP_ORDER, validate_epanet_bb_best_x

    vectors = _schedule_vectors_from_plan(plan, instance)
    case = make_case_metadata(args.case_id)
    validate_epanet_bb_best_x(vectors["best_x"], na_max=case["na_max"], pump_order=EPANET_BB_PUMP_ORDER)

    pump_mapping = []
    for column, pump_id in enumerate(vectors["pump_order"]):
        arc = vectors["arc_by_pump"][pump_id]
        pump_mapping.append(
            {
                "epanet_id": pump_id,
                "gops_id": str(instance.pumps[arc].id),
                "gops_arc": list(arc),
                "best_x_column": column,
            }
        )

    artifact: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "track": TRACK,
        "artifact_type": "epanet-bb-compatible-commanded-pump-schedule",
        "case_id": args.case_id,
        "na_max": case["na_max"],
        "max_actuations": case["na_max"],
        "h_max": 24,
        "inp_file": "networks/any-town.inp",
        "method_name": _method_name(args),
        "method": _method_name(args),
        "gops_method": {
            "execution_mode": args.execution_mode,
            "adjust_mode": args.adjust_mode,
        },
        "benchmark_identity": case["benchmark_identity"],
        "horizon": {
            "h_max": 24,
            "periods": 24,
            "period_duration_hours": 1,
            "explicit_initial_slot": True,
            "gops_period_t0_maps_to_epanet_hour": 1,
        },
        "pump_mapping": {
            "best_x_order": list(vectors["pump_order"]),
            "gops_to_epanet": pump_mapping,
        },
        "conversion": {
            "source": "GOPS commanded binary activity variables xk/gurobi _svar by pump arc and period",
            "best_x": (
                "best_x starts with explicit h=0 all-off states, then appends GOPS periods "
                "t=0..23 as EPANET-BB hours h=1..24 flattened by pump order 111,222,333."
            ),
            "best_y": "best_y[h] is the aggregate commanded pump count for the corresponding best_x hour.",
            "policy": "Only complete non-adjusted fixed-period commanded schedules are audit-compatible.",
        },
        "schedule_source": source,
        "best_y": vectors["best_y"],
        "best_x": vectors["best_x"],
        "pump_schedules_h1_to_h24": {
            pump_id: "".join(str(value) for value in values)
            for pump_id, values in vectors["statuses_by_pump"].items()
        },
        "operative_transition_counts": vectors["transition_counts"],
    }

    cost_value = _finite_number(cost)
    if cost_value is not None:
        artifact["best_cost"] = cost_value
    duration_value = _finite_number(duration)
    if duration_value is not None:
        artifact["duration_seconds"] = duration_value
    return artifact


def _audit_schedule(args: argparse.Namespace, paths: OutputPaths) -> dict[str, Any]:
    audit_binary = args.audit_binary
    if not audit_binary.exists():
        return {
            "status": "failed",
            "detail": f"EPANET-BB audit binary not found: {audit_binary}",
            "command": [],
        }

    command = [
        str(audit_binary),
        str((ROOT / paths.schedule_json).resolve()),
        str((ROOT / paths.audit_json).resolve()),
        "--zero-flow-threshold",
        f"{args.audit_zero_flow_threshold:g}",
    ]
    result = subprocess.run(command, cwd=audit_binary.parent.parent, text=True, capture_output=True, check=False)
    audit_result: dict[str, Any] = {
        "status": "succeeded" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "zero_flow_threshold": args.audit_zero_flow_threshold,
    }
    if result.returncode != 0:
        return audit_result

    try:
        payload = json.loads((ROOT / paths.audit_json).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        audit_result.update(
            {
                "status": "failed",
                "detail": f"Audit command succeeded, but audit JSON could not be read: {exc}",
            }
        )
        return audit_result

    summary: dict[str, Any] = {}
    if "feasibility" in payload:
        summary["feasibility"] = payload["feasibility"]
    if "effective_cost" in payload:
        summary["effective_cost"] = payload["effective_cost"]
    if "event_counts" in payload:
        summary["event_counts"] = payload["event_counts"]
    audit_result["summary"] = summary
    return audit_result


def _plan_from_model_values(model: Any, instance: Any) -> dict[int, dict[tuple[str, str], int]]:
    plan = {}
    for period in instance.horizon():
        plan[period] = {}
        for arc in instance.pumps:
            value = getattr(model._svar[arc, period], "X")
            plan[period][arc] = _binary_value(value, f"pump arc {arc} period {period}")
    return plan


def _candidate_from_plan(
    args: argparse.Namespace,
    instance: Any,
    plan: dict[int, dict[tuple[str, str], Any]],
    *,
    source: dict[str, Any],
    cost: Any,
    duration: Any,
    summary: dict[str, Any],
) -> ScheduleCandidate:
    try:
        artifact = _make_schedule_artifact(args, instance, plan, source=source, cost=cost, duration=duration)
    except ValueError as exc:
        return ScheduleCandidate("incomplete", str(exc), None, summary)
    return ScheduleCandidate(
        "complete_commanded_schedule",
        "complete fixed-period commanded pump schedule exported",
        artifact,
        summary,
    )


def _lpnlpbb_schedule_candidate(
    args: argparse.Namespace,
    instance: Any,
    model: Any,
) -> ScheduleCandidate:
    solutions = list(getattr(model, "_solutions", []))
    records = []
    adjusted_count = 0
    incomplete_details = []

    for index, solution in enumerate(solutions):
        adjusted = bool(solution.get("adjusted"))
        adjusted_count += int(adjusted)
        record = {
            "index": index,
            "adjusted": adjusted,
            "cost": solution.get("cost"),
            "cpu": solution.get("cpu"),
            "has_flows": solution.get("flows") is not None,
            "has_volumes": solution.get("volumes") is not None,
        }
        try:
            _schedule_vectors_from_plan(solution["plan"], instance)
            record["complete_commanded_pump_schedule"] = True
        except (KeyError, ValueError) as exc:
            record["complete_commanded_pump_schedule"] = False
            record["detail"] = str(exc)
            incomplete_details.append(str(exc))
        records.append(record)

    summary = {
        "source": "lpnlpbb_callback_solutions",
        "solution_count": len(solutions),
        "adjusted_solution_count": adjusted_count,
        "unadjusted_solution_count": len(solutions) - adjusted_count,
        "solutions": records,
    }

    for index, solution in reversed(list(enumerate(solutions))):
        if solution.get("adjusted"):
            continue
        source = {
            "kind": "lpnlpbb_model_solution",
            "solution_index": index,
            "adjusted": False,
            "cost_source": "lpnlpbb_real_cost",
            "duration_source": "gurobi_callback_runtime",
        }
        candidate = _candidate_from_plan(
            args,
            instance,
            solution.get("plan", {}),
            source=source,
            cost=solution.get("cost"),
            duration=solution.get("cpu"),
            summary=summary,
        )
        if candidate.artifact is not None:
            return candidate
        incomplete_details.append(candidate.detail)

    if solutions and adjusted_count == len(solutions):
        return ScheduleCandidate(
            "adjusted_only",
            "only adjusted or variable-duration heuristic solutions are available; no audit-compatible schedule exported",
            None,
            summary,
        )
    if solutions:
        detail = incomplete_details[-1] if incomplete_details else "no complete commanded schedule in GOPS solutions"
        return ScheduleCandidate("incomplete", detail, None, summary)
    return ScheduleCandidate("none", "no GOPS incumbent schedule is available", None, summary)


def _cvx_schedule_candidate(
    args: argparse.Namespace,
    instance: Any,
    model: Any,
    status_metrics: dict[str, Any],
) -> ScheduleCandidate:
    solution_count = _finite_number(status_metrics.get("solution_count")) or 0
    summary = {
        "source": "gurobi_model_solution_values",
        "solution_count": int(solution_count),
    }
    if solution_count < 1:
        return ScheduleCandidate("none", "Gurobi did not report an incumbent solution", None, summary)

    try:
        plan = _plan_from_model_values(model, instance)
    except (AttributeError, KeyError, ValueError) as exc:
        return ScheduleCandidate("incomplete", str(exc), None, summary)

    return _candidate_from_plan(
        args,
        instance,
        plan,
        source={
            "kind": "gurobi_variable_values",
            "solution_index": 0,
            "cost_source": "gurobi_objective_value",
            "duration_source": "gurobi_runtime_seconds",
        },
        cost=status_metrics.get("objective_value"),
        duration=status_metrics.get("gurobi_runtime_seconds"),
        summary=summary,
    )


def _no_schedule_candidate(reason: str) -> ScheduleCandidate:
    return ScheduleCandidate(
        "none",
        reason,
        None,
        {
            "source": "not_applicable",
            "solution_count": 0,
        },
    )


def _run_status_for_solver(gp: Any, solver_status: int, schedule_availability: str) -> str:
    if solver_status == gp.GRB.INFEASIBLE:
        return "infeasible"
    if schedule_availability == "complete_commanded_schedule":
        if solver_status == gp.GRB.TIME_LIMIT:
            return "time_limit_with_schedule"
        if solver_status == gp.GRB.OPTIMAL:
            return "success"
        return "solver_error"
    if solver_status == gp.GRB.TIME_LIMIT:
        return "time_limit_no_schedule"
    if solver_status == gp.GRB.OPTIMAL:
        return "validation_failed"
    return "solver_error"


def _build_model(args: argparse.Namespace) -> tuple[Any, Any, Any, dict[str, Any], dict[str, Any]]:
    _ensure_src_imports()
    import gurobipy as gp
    from activation import resolve_epanet_bb_case
    from gops import makeinstance
    from instance import Instance
    import convexrelaxation as rel

    Instance.DATADIR = ROOT / "data"
    Instance.BNDSDIR = ROOT / "bounds"

    case = resolve_epanet_bb_case(args.case_id)
    instance = makeinstance(case.gops_base_instance_key)
    bounds_file = ROOT / "bounds" / f"{instance.name}.hdf"
    bounds_status = "missing_skipped"
    if bounds_file.exists():
        instance.parse_bounds()
        bounds_status = "parsed"
    elif args.require_bounds:
        raise FileNotFoundError(f"required bounds file is missing: {bounds_file}")

    model = rel.build_model(instance, args.epsilon, activation_config=case.activation_config())
    model.Params.TimeLimit = args.time_limit
    model.Params.MIPGap = args.mip_gap
    if args.threads:
        model.Params.Threads = args.threads
    model.Params.LogFile = str((ROOT / args.paths.solver_log).resolve())
    if not args.gurobi_output:
        model.Params.OutputFlag = 0

    model_data = {
        "instance": {
            "name": instance.name,
            "basic": instance.tostr_basic(),
            "network": instance.tostr_network(),
            "periods": instance.nperiods(),
            "period_duration_hours": instance.tsinhours(),
        },
        "bounds": {
            "path": _repo_relative(bounds_file),
            "status": bounds_status,
        },
        "variables": model.NumVars,
        "constraints": model.NumConstrs,
        "binary_variables": model.NumBinVars,
        "integer_variables": model.NumIntVars,
        "activation_semantics": model._activation_config.semantics,
        "enforce_symmetric_ordering": model._activation_config.enforce_symmetric_ordering,
        "stop_variables": len(model._stopvar),
    }
    return gp, instance, model, _solver_dict(gp, "valid"), model_data


def _run_solver(args: argparse.Namespace, gp: Any, instance: Any, model: Any) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if args.execution_mode == "build":
        return (
            {
                "run_status": "environment_ready",
                "schedule_availability": "none",
                "detail": "Gurobi model built without optimizing",
            },
            None,
        )

    started = time.time()
    if args.execution_mode == "cvx":
        model.optimize()
        cost = None
    else:
        import lpnlpbb as bb

        adjust_mode = "" if args.adjust_mode == "plain" else args.adjust_mode
        cost = bb.lpnlpbb(model, instance, drawsolution=False, adjust_mode=adjust_mode)

    status_name = _status_name(gp, model.Status)
    status_metrics = {
        "gurobi_status": model.Status,
        "gurobi_status_name": status_name,
        "gurobi_runtime_seconds": _safe_attr(model, "Runtime"),
        "wall_time_seconds": round(time.time() - started, 3),
        "node_count": _safe_attr(model, "NodeCount"),
        "solution_count": _safe_attr(model, "SolCount"),
        "objective_value": _safe_attr(model, "ObjVal"),
        "objective_bound": _safe_attr(model, "ObjBound"),
        "mip_gap": _safe_attr(model, "MIPGap"),
        "reported_real_cost": cost,
    }

    if args.execution_mode == "lpnlpbb":
        schedule_candidate = _lpnlpbb_schedule_candidate(args, instance, model)
    elif args.execution_mode == "cvx":
        schedule_candidate = _cvx_schedule_candidate(args, instance, model, status_metrics)
    else:
        schedule_candidate = _no_schedule_candidate("execution mode does not solve for a commanded schedule")

    run_status = _run_status_for_solver(gp, model.Status, schedule_candidate.schedule_availability)
    status = {
        "run_status": run_status,
        "schedule_availability": schedule_candidate.schedule_availability,
        "detail": f"solver status {status_name}; {schedule_candidate.detail}",
        **status_metrics,
        "schedule_export": schedule_candidate.summary,
    }
    if schedule_candidate.artifact is not None:
        schedule_candidate.artifact["status"] = {
            "run_status": run_status,
            "schedule_availability": schedule_candidate.schedule_availability,
            "detail": status["detail"],
        }
        schedule_candidate.artifact["solver_status"] = {
            key: status_metrics[key]
            for key in (
                "gurobi_status",
                "gurobi_status_name",
                "gurobi_runtime_seconds",
                "wall_time_seconds",
                "solution_count",
                "objective_value",
                "objective_bound",
                "mip_gap",
                "reported_real_cost",
            )
        }
    return status, schedule_candidate.artifact


def run(args: argparse.Namespace, command: list[str]) -> int:
    paths = args.paths
    if args.gurobi_license_file is not None:
        os.environ["GRB_LICENSE_FILE"] = str(args.gurobi_license_file)

    git_metadata = _git_metadata()
    (ROOT / paths.root).mkdir(parents=True, exist_ok=True)
    host_name = args.host_name or platform.node()
    runtime_settings = {
        "time_limit_seconds": args.time_limit,
        "mip_gap": args.mip_gap,
        "mode": args.execution_mode,
        "adjust_mode": args.adjust_mode,
        "epsilon": args.epsilon,
        "threads": args.threads or None,
        "gurobi_license_file": os.environ.get("GRB_LICENSE_FILE"),
    }

    if args.run_class == "final" and host_name != "labma-sol":
        manifest = make_run_manifest(
            case_id=args.case_id,
            run_class=args.run_class,
            command=command,
            paths=paths,
            host_name=host_name,
            working_directory=ROOT,
            runtime_settings=runtime_settings,
            solver=_solver_dict(),
            status={
                "run_status": "environment_blocked",
                "schedule_availability": "none",
                "detail": "final runs must identify labma-sol as host",
            },
            git_metadata=git_metadata,
        )
        _write_json(ROOT / paths.run_manifest, manifest)
        print(f"wrote {paths.run_manifest}")
        return 2

    model = None
    solver = _solver_dict()
    model_data = None
    schedule_artifact = None
    schedule_written = False
    audit_written = False
    try:
        gp, instance, model, solver, model_data = _build_model(args)
        status, schedule_artifact = _run_solver(args, gp, instance, model)
        exit_code = 0
    except Exception as exc:
        status = classify_exception(exc)
        if status["run_status"] == "license_blocked":
            solver = {**solver, "license_status": classify_license_status(status["detail"])}
        exit_code = 2 if status["run_status"] in {"environment_blocked", "license_blocked"} else 1
    finally:
        if model is not None:
            model.dispose()

    if schedule_artifact is not None:
        try:
            _write_json(ROOT / paths.schedule_json, schedule_artifact)
            schedule_written = True
        except Exception as exc:
            status = {
                "run_status": "validation_failed",
                "schedule_availability": "none",
                "detail": f"failed to write schedule artifact: {exc}",
            }
            schedule_written = False
            exit_code = 1

    should_audit = schedule_written and (args.audit_schedule or args.run_class == "final")
    if should_audit:
        audit_result = _audit_schedule(args, paths)
        status["audit"] = audit_result
        audit_written = audit_result["status"] == "succeeded" and (ROOT / paths.audit_json).exists()
        if audit_result["status"] != "succeeded":
            status = {
                **status,
                "run_status": "audit_failed",
                "detail": f"{status.get('detail', '')}; EPANET-BB audit failed",
            }
            exit_code = 1

    manifest = make_run_manifest(
        case_id=args.case_id,
        run_class=args.run_class,
        command=command,
        paths=paths,
        host_name=host_name,
        working_directory=ROOT,
        runtime_settings=runtime_settings,
        solver=solver,
        status=status,
        model=model_data,
        git_metadata=git_metadata,
        schedule_written=schedule_written,
        audit_written=audit_written,
    )
    _write_json(ROOT / paths.run_manifest, manifest)
    print(f"wrote {paths.run_manifest}")
    if schedule_written:
        print(f"wrote {paths.schedule_json}")
    if audit_written:
        print(f"wrote {paths.audit_json}")
    print(f"run status: {status['run_status']}")
    print(f"schedule availability: {status['schedule_availability']}")
    return exit_code


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id", choices=["atm-24h-na1", "atm-24h-na2", "atm-24h-na3"])
    parser.add_argument("--run-class", choices=["final", "smoke", "dev", "diagnostic"], default="dev")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--host-name", default=None, help="override recorded host name, e.g. labma-sol")
    parser.add_argument("--execution-mode", choices=["build", "cvx", "lpnlpbb"], default="build")
    parser.add_argument("--adjust-mode", choices=["plain", "SOLVE", "CUT"], default="plain")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--time-limit", type=float, default=60.0)
    parser.add_argument("--mip-gap", type=float, default=1e-6)
    parser.add_argument("--epsilon", type=float, default=1e-2)
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--require-bounds", action="store_true")
    parser.add_argument("--gurobi-output", action="store_true")
    parser.add_argument(
        "--gurobi-license-file",
        type=Path,
        default=None,
        help="explicit Gurobi license path to set via GRB_LICENSE_FILE before importing gurobipy",
    )
    parser.add_argument(
        "--audit-schedule",
        action="store_true",
        help="run the EPANET-BB fixed-schedule audit when a complete schedule is exported",
    )
    parser.add_argument(
        "--audit-binary",
        type=Path,
        default=ROOT.parent / "epanet-bb" / "build" / "run-epanet3-bb-audit",
    )
    parser.add_argument("--audit-zero-flow-threshold", type=float, default=1e-6)
    args = parser.parse_args(argv)
    run_id = args.run_id or _utc_run_id()
    args.paths = make_output_paths(args.case_id, run_id, args.output_root)
    return args


def main(argv: list[str] | None = None) -> int:
    actual_argv = sys.argv[1:] if argv is None else argv
    args = parse_args(actual_argv)
    return run(args, [Path(sys.argv[0]).name, *actual_argv])


if __name__ == "__main__":
    raise SystemExit(main())
