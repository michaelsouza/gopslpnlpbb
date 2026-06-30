#!/usr/bin/env python3
"""Run the candidate GOPS Anytown instance for the Bonvin AT(M) audit.

This script intentionally avoids importing ``src/gops.py`` because that module
executes a benchmark batch at import time. The candidate configuration below is
the direct expansion of ``makeinstance("ANY s 24 1")``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "output" / "bonvin_atm_anytown_candidate_run.json"

CANDIDATE = {
    "public_instance_id": "ANY s 24 1",
    "network": "Anytown",
    "profile": "Profile_5d_30m_smooth",
    "start_time": "01/01/2013 00:00",
    "end_time": "02/01/2013 00:00",
    "aggregate_steps": 2,
    "periods": 24,
    "period_duration_hours": 1.0,
    "pump_arcs": [["R1", "J20"], ["R2", "J20"], ["R3", "J20"]],
    "activation_limit_caveat": (
        "The public GOPS model has no configurable Bonvin/EPANET-BB N or "
        "NA_max token. For Anytown it applies the hardcoded symmetric-group "
        "start cap from convexrelaxation.py."
    ),
    "benchmark_caveat": (
        "GOPS Anytown is an AnyTown-family public benchmark, but its tank, "
        "source, and profile representation is not a literal EPANET-BB "
        "any-town.inp match."
    ),
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if math.isnan(value):
            return "nan"
        return "inf" if value > 0 else "-inf"
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prepare_src_imports() -> None:
    sys.path.insert(0, str(SRC))
    os.chdir(SRC)


def _status_name(gp: Any, status: int | None) -> str | None:
    if status is None:
        return None
    mapping = {
        gp.GRB.OPTIMAL: "OPTIMAL",
        gp.GRB.INFEASIBLE: "INFEASIBLE",
        gp.GRB.INF_OR_UNBD: "INF_OR_UNBD",
        gp.GRB.UNBOUNDED: "UNBOUNDED",
        gp.GRB.CUTOFF: "CUTOFF",
        gp.GRB.ITERATION_LIMIT: "ITERATION_LIMIT",
        gp.GRB.NODE_LIMIT: "NODE_LIMIT",
        gp.GRB.TIME_LIMIT: "TIME_LIMIT",
        gp.GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
        gp.GRB.INTERRUPTED: "INTERRUPTED",
        gp.GRB.NUMERIC: "NUMERIC",
        gp.GRB.SUBOPTIMAL: "SUBOPTIMAL",
    }
    return mapping.get(status, f"STATUS_{status}")


def _safe_model_attr(model: Any, name: str) -> Any:
    try:
        return getattr(model, name)
    except Exception as exc:  # Gurobi raises if an attribute is unavailable.
        return {"unavailable": str(exc)}


def _schedule_from_plan(plan: dict[int, dict[tuple[str, str], int]], instance: Any) -> list[dict[str, Any]]:
    schedule = []
    periods = list(instance.horizon())
    for arc in sorted(instance.pumps.keys()):
        values = [int(round(plan[t][arc])) for t in periods]
        schedule.append(
            {
                "pump_id": instance.pumps[arc].id,
                "arc": list(arc),
                "status": values,
            }
        )
    return schedule


def _classify_solutions(model: Any, instance: Any) -> dict[str, Any]:
    solutions = getattr(model, "_solutions", [])
    records = []
    best_unadjusted = None

    for index, solution in enumerate(solutions):
        adjusted = bool(solution.get("adjusted"))
        schedule = _schedule_from_plan(solution["plan"], instance)
        complete = all(len(row["status"]) == instance.nperiods() for row in schedule)
        record = {
            "index": index,
            "cost": solution.get("cost"),
            "cpu": solution.get("cpu"),
            "adjusted": adjusted,
            "has_flows": solution.get("flows") is not None,
            "has_volumes": solution.get("volumes") is not None,
            "complete_commanded_pump_schedule": complete,
        }
        records.append(record)
        if not adjusted and complete:
            best_unadjusted = {
                "solution_index": index,
                "cost": solution.get("cost"),
                "cpu": solution.get("cpu"),
                "schedule": schedule,
            }

    return {
        "solution_count": len(solutions),
        "adjusted_solution_count": sum(1 for solution in solutions if solution.get("adjusted")),
        "unadjusted_solution_count": sum(1 for solution in solutions if not solution.get("adjusted")),
        "solutions": records,
        "schedule_availability": (
            "complete_unadjusted_commanded_pump_schedule"
            if best_unadjusted
            else "no_complete_unadjusted_commanded_pump_schedule"
        ),
        "best_unadjusted_schedule": best_unadjusted,
    }


def describe_candidate() -> dict[str, Any]:
    return {
        "issue": "michaelsouza/gopslpnlpbb#7",
        "candidate": CANDIDATE,
        "runner": {
            "path": str(Path(__file__).relative_to(ROOT)),
            "avoids_gops_import_side_effect": True,
            "expected_working_directory_for_legacy_modules": str(SRC),
        },
    }


def run_candidate(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        **describe_candidate(),
        "command": [str(Path(sys.argv[0]).name), *sys.argv[1:]],
        "runtime": {
            "original_cwd": str(Path.cwd()),
            "solver_cwd": str(SRC),
            "time_limit_seconds": args.time_limit,
            "mip_gap": args.mip_gap,
            "epsilon": args.epsilon,
            "mode": args.mode,
        },
        "environment": {
            "GUROBI_HOME_set": bool(os.environ.get("GUROBI_HOME")),
            "GRB_LICENSE_FILE_set": bool(os.environ.get("GRB_LICENSE_FILE")),
            "LD_LIBRARY_PATH_set": bool(os.environ.get("LD_LIBRARY_PATH")),
        },
    }

    _prepare_src_imports()

    import gurobipy as gp
    from instance import Instance
    import convexrelaxation as rel
    import lpnlpbb as bb

    result["solver"] = {
        "gurobipy_version": gp.gurobi.version(),
    }

    instance = Instance(
        CANDIDATE["network"],
        CANDIDATE["profile"],
        CANDIDATE["start_time"],
        CANDIDATE["end_time"],
        CANDIDATE["aggregate_steps"],
    )
    result["instance"] = {
        "basic": instance.tostr_basic(),
        "network": instance.tostr_network(),
        "nperiods": instance.nperiods(),
        "period_duration_hours": instance.tsinhours(),
        "pumps": [{"id": pump.id, "arc": list(arc)} for arc, pump in sorted(instance.pumps.items())],
    }

    bounds_file = ROOT / "bounds" / f"{instance.name}.hdf"
    if bounds_file.exists():
        instance.parse_bounds()
        result["bounds"] = {
            "path": str(bounds_file.relative_to(ROOT)),
            "status": "parsed",
        }
    elif args.require_bounds:
        raise FileNotFoundError(f"required bounds file is missing: {bounds_file}")
    else:
        result["bounds"] = {
            "path": str(bounds_file.relative_to(ROOT)),
            "status": "missing_skipped",
            "public_solve_path_caveat": (
                "src/gops.py solve() calls instance.parse_bounds() unconditionally "
                "and only catches UnicodeDecodeError, so the direct public path "
                "would fail before model construction for ANY s 24 1."
            ),
        }

    start = time.time()
    model = rel.build_model(instance, args.epsilon)
    model.Params.MIPGap = args.mip_gap
    model.Params.TimeLimit = args.time_limit
    if args.threads:
        model.Params.Threads = args.threads
    if not args.gurobi_output:
        model.Params.OutputFlag = 0

    result["model"] = {
        "variables": model.NumVars,
        "constraints": model.NumConstrs,
        "binary_variables": model.NumBinVars,
        "integer_variables": model.NumIntVars,
    }

    try:
        if args.mode == "CVX":
            cost_real = bb.solveconvex(model, instance, drawsolution=False)
            result["solution_classification"] = {
                "schedule_availability": "cvx_mode_not_a_gops_lpnlpbb_incumbent_export",
                "solution_count": model.SolCount,
            }
        else:
            adjust_mode = "" if args.mode == "plain" else args.mode
            cost_real = bb.lpnlpbb(model, instance, drawsolution=False, adjust_mode=adjust_mode)
            result["solution_classification"] = _classify_solutions(model, instance)

        result["runtime_status"] = {
            "completed": True,
            "wall_time_seconds": round(time.time() - start, 3),
            "gurobi_status": model.Status,
            "gurobi_status_name": _status_name(gp, model.Status),
            "gurobi_runtime_seconds": _safe_model_attr(model, "Runtime"),
            "node_count": _safe_model_attr(model, "NodeCount"),
            "solution_count": _safe_model_attr(model, "SolCount"),
            "objective_value": _safe_model_attr(model, "ObjVal"),
            "objective_bound": _safe_model_attr(model, "ObjBound"),
            "mip_gap": _safe_model_attr(model, "MIPGap"),
            "reported_real_cost": cost_real,
        }
    finally:
        model.terminate()

    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--describe-only", action="store_true", help="print candidate metadata without importing Gurobi")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="JSON summary path")
    parser.add_argument("--time-limit", type=float, default=60.0, help="Gurobi time limit in seconds")
    parser.add_argument("--mip-gap", type=float, default=1e-6, help="Gurobi MIPGap parameter")
    parser.add_argument("--epsilon", type=float, default=1e-2, help="outer-approximation epsilon")
    parser.add_argument("--mode", choices=["plain", "CUT", "SOLVE", "CVX"], default="plain")
    parser.add_argument("--threads", type=int, default=0, help="optional Gurobi Threads parameter")
    parser.add_argument("--require-bounds", action="store_true", help="fail if bounds/Anytown.hdf is missing")
    parser.add_argument("--gurobi-output", action="store_true", help="leave Gurobi solver logging enabled")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.output.is_absolute():
        args.output = ROOT / args.output
    if args.describe_only:
        print(json.dumps(describe_candidate(), indent=2, sort_keys=True))
        return 0

    try:
        result = run_candidate(args)
        _write_json(args.output, result)
        print(f"wrote {args.output}")
        print(f"runtime status: {result['runtime_status']['gurobi_status_name']}")
        print(f"schedule availability: {result['solution_classification']['schedule_availability']}")
        return 0
    except Exception as exc:
        failure = {
            **describe_candidate(),
            "command": [str(Path(sys.argv[0]).name), *sys.argv[1:]],
            "runtime_status": {
                "completed": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        }
        _write_json(args.output, failure)
        print(f"wrote failure summary to {args.output}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
