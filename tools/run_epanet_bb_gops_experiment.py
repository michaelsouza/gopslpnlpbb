#!/usr/bin/env python3
"""Run or smoke-build an EPANET-BB-equivalent GOPS experiment case."""

from __future__ import annotations

import argparse
import json
import math
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
    solver_log: Path


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
            {"epanet_id": "111", "gops_id": "111", "gops_arc": ["R111", "J20"]},
            {"epanet_id": "222", "gops_id": "222", "gops_arc": ["R222", "J20"]},
            {"epanet_id": "333", "gops_id": "333", "gops_arc": ["R333", "J20"]},
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
            "schedule_json": None,
            "audit_json": None,
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


def _run_solver(args: argparse.Namespace, gp: Any, instance: Any, model: Any) -> dict[str, Any]:
    if args.execution_mode == "build":
        return {
            "run_status": "environment_ready",
            "schedule_availability": "none",
            "detail": "Gurobi model built without optimizing",
        }

    started = time.time()
    if args.execution_mode == "cvx":
        model.optimize()
        cost = None
    else:
        import lpnlpbb as bb

        adjust_mode = "" if args.adjust_mode == "plain" else args.adjust_mode
        cost = bb.lpnlpbb(model, instance, drawsolution=False, adjust_mode=adjust_mode)

    status_name = _status_name(gp, model.Status)
    if model.Status == gp.GRB.INFEASIBLE:
        run_status = "infeasible"
    elif model.Status == gp.GRB.TIME_LIMIT:
        run_status = "time_limit_no_schedule"
    elif model.Status == gp.GRB.OPTIMAL:
        run_status = "time_limit_no_schedule"
    else:
        run_status = "solver_error"

    return {
        "run_status": run_status,
        "schedule_availability": "none",
        "detail": f"solver status {status_name}; schedule export belongs to issue #17",
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


def run(args: argparse.Namespace, command: list[str]) -> int:
    paths = args.paths
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
    try:
        gp, instance, model, solver, model_data = _build_model(args)
        status = _run_solver(args, gp, instance, model)
        exit_code = 0
    except Exception as exc:
        status = classify_exception(exc)
        exit_code = 2 if status["run_status"] in {"environment_blocked", "license_blocked"} else 1
    finally:
        if model is not None:
            model.dispose()

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
    )
    _write_json(ROOT / paths.run_manifest, manifest)
    print(f"wrote {paths.run_manifest}")
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
