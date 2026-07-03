#!/usr/bin/env python3
"""Compare final EPANET-BB-equivalent GOPS artifacts with paper artifacts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TRACK = "epanet-bb-equivalent-gops"
CONTRACT_VERSION = "epanet-bb-equivalent-gops-v1"
DEFAULT_SOURCE = ROOT / "docs" / "epanet-bb-anytown-modified-source-of-truth.json"
DEFAULT_RUN_ID = "issue18-matched-budget-20260703T115137Z"
DEFAULT_OUTPUT_ROOT = ROOT / "output" / "epanet_bb_equivalent_gops"
DEFAULT_JSON = DEFAULT_OUTPUT_ROOT / "issue19-matched-budget-comparison.json"
DEFAULT_MARKDOWN = DEFAULT_OUTPUT_ROOT / "issue19-matched-budget-comparison.md"
CASE_IDS = ("atm-24h-na1", "atm-24h-na2", "atm-24h-na3")
PAPER_METHOD_ORDER = ("Costa2016", "Cimorelli2020", "Paola2025", "Souza2026")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return _repo_relative(value)
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if math.isnan(value):
            return "nan"
        return "inf" if value > 0 else "-inf"
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(data), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _format_number(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        if abs(value) >= 1000:
            return f"{value:.{digits}f}"
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def _percent_delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline in (None, 0):
        return None
    return (value - baseline) / baseline * 100


def _hamming(left: list[int] | None, right: list[int] | None) -> int | None:
    if left is None or right is None or len(left) != len(right):
        return None
    return sum(int(a != b) for a, b in zip(left, right))


def schedule_behavior(schedule: dict[str, Any] | None, target_case: dict[str, Any]) -> dict[str, Any]:
    if schedule is None:
        return {
            "available": False,
            "best_x_hamming_vs_souza2026": None,
            "best_y_hamming_vs_souza2026": None,
            "aggregate_hours_matching_souza2026": None,
            "commanded_pump_hours": None,
            "souza2026_commanded_pump_hours": sum(target_case["best_y"][1:]),
            "peak_pumps": None,
            "off_hours": None,
            "pump_schedules_h1_to_h24": None,
            "souza2026_pump_schedules_h1_to_h24": target_case["pump_schedules_h1_to_h24"],
            "operative_transition_counts": None,
        }

    best_y = schedule["best_y"]
    target_best_y = target_case["best_y"]
    best_y_hamming = _hamming(best_y, target_best_y)
    aggregate_matches = None
    if best_y_hamming is not None:
        aggregate_matches = len(best_y) - best_y_hamming

    return {
        "available": True,
        "best_x_hamming_vs_souza2026": _hamming(schedule.get("best_x"), target_case.get("best_x")),
        "best_y_hamming_vs_souza2026": best_y_hamming,
        "aggregate_hours_matching_souza2026": aggregate_matches,
        "commanded_pump_hours": sum(best_y[1:]),
        "souza2026_commanded_pump_hours": sum(target_best_y[1:]),
        "peak_pumps": max(best_y[1:]),
        "off_hours": sum(1 for count in best_y[1:] if count == 0),
        "pump_schedules_h1_to_h24": schedule.get("pump_schedules_h1_to_h24"),
        "souza2026_pump_schedules_h1_to_h24": target_case["pump_schedules_h1_to_h24"],
        "operative_transition_counts": schedule.get("operative_transition_counts"),
    }


def paper_artifacts_by_na(source: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {1: [], 2: [], 3: []}
    rank = {method: index for index, method in enumerate(PAPER_METHOD_ORDER)}
    for artifact in source["published_schedule_artifacts"]:
        grouped[int(artifact["NA_max"])].append(artifact)
    for artifacts in grouped.values():
        artifacts.sort(key=lambda item: (rank.get(item["method"], 999), item["method"]))
    return grouped


def load_gops_case(output_root: Path, case_id: str, run_id: str) -> dict[str, Any]:
    run_path = output_root / case_id / run_id / "run.json"
    run = _read_json(run_path)

    schedule_path = run["outputs"].get("schedule_json")
    schedule = _read_json(ROOT / schedule_path) if schedule_path else None

    audit_path = run["outputs"].get("audit_json")
    audit = _read_json(ROOT / audit_path) if audit_path else None

    return {
        "run_path": _repo_relative(run_path),
        "run": run,
        "schedule_path": schedule_path,
        "schedule": schedule,
        "audit_path": audit_path,
        "audit": audit,
    }


def summarize_gops_case(
    output_root: Path,
    run_id: str,
    case_id: str,
    target_case: dict[str, Any],
    paper_artifacts: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    loaded = load_gops_case(output_root, case_id, run_id)
    run = loaded["run"]
    schedule = loaded["schedule"]
    audit = loaded["audit"]
    na_max = int(run["case"]["na_max"])
    source_souza = next(item for item in paper_artifacts[na_max] if item["method"] == "Souza2026")
    audit_cost = audit.get("effective_cost") if audit else None
    audit_cost_raw = audit.get("effective_cost_raw") if audit else None
    audit_feasible = audit.get("feasibility", {}).get("feasible") if audit else None
    audit_events = audit.get("event_counts") if audit else None
    solver_status = run["status"]
    behavior = schedule_behavior(schedule, target_case)

    return {
        "case_id": case_id,
        "na_max": na_max,
        "gops": {
            "run_status": solver_status["run_status"],
            "schedule_availability": solver_status["schedule_availability"],
            "solver_status": solver_status.get("gurobi_status_name"),
            "gurobi_runtime_seconds": solver_status.get("gurobi_runtime_seconds"),
            "wall_time_seconds": solver_status.get("wall_time_seconds"),
            "solution_count": solver_status.get("solution_count"),
            "objective_value": solver_status.get("objective_value"),
            "objective_bound": solver_status.get("objective_bound"),
            "mip_gap": solver_status.get("mip_gap"),
            "reported_real_cost": solver_status.get("reported_real_cost"),
            "schedule_cost": schedule.get("best_cost") if schedule else None,
            "schedule_duration_seconds": schedule.get("duration_seconds") if schedule else None,
            "audit_effective_cost": audit_cost,
            "audit_effective_cost_raw": audit_cost_raw,
            "audit_cost_units": audit.get("cost_units") if audit else None,
            "audit_feasible": audit_feasible,
            "audit_event_counts": audit_events,
        },
        "souza2026": {
            "artifact": source_souza["path"],
            "best_cost": source_souza["best_cost"],
            "duration_seconds": source_souza["duration_seconds"],
        },
        "cost_delta_vs_souza2026": {
            "audit_effective_cost_minus_paper": None if audit_cost is None else audit_cost - source_souza["best_cost"],
            "audit_effective_cost_percent_delta": _percent_delta(audit_cost, source_souza["best_cost"]),
        },
        "runtime_delta_vs_souza2026": {
            "gurobi_runtime_minus_paper": (
                None
                if solver_status.get("gurobi_runtime_seconds") is None
                else solver_status["gurobi_runtime_seconds"] - source_souza["duration_seconds"]
            ),
            "gurobi_runtime_percent_delta": _percent_delta(
                solver_status.get("gurobi_runtime_seconds"),
                source_souza["duration_seconds"],
            ),
        },
        "schedule_behavior": behavior,
        "artifacts": {
            "run_json": loaded["run_path"],
            "schedule_json": loaded["schedule_path"],
            "audit_json": loaded["audit_path"],
            "solver_log": run["outputs"].get("solver_log"),
        },
        "provenance": {
            "host": run["environment"]["host_name"],
            "run_class": run["environment"]["run_class"],
            "branch": run["git"]["branch"],
            "commit": run["git"]["commit"],
            "dirty": run["git"]["dirty"],
            "solver": run["solver"],
            "runtime_settings": run["runtime_settings"],
        },
    }


def build_comparison(source_path: Path, output_root: Path, run_id: str) -> dict[str, Any]:
    source = _read_json(source_path)
    paper_by_na = paper_artifacts_by_na(source)
    target_by_case = {case["case_id"]: case for case in source["target_cases"]}
    cases = [
        summarize_gops_case(output_root, run_id, case_id, target_by_case[case_id], paper_by_na)
        for case_id in CASE_IDS
    ]

    return {
        "contract_version": CONTRACT_VERSION,
        "track": TRACK,
        "artifact_type": "epanet-bb-equivalent-gops-paper-comparison",
        "issue": "michaelsouza/gopslpnlpbb#19",
        "parent_prd": "michaelsouza/gopslpnlpbb#10",
        "source_run_id": run_id,
        "source_of_truth": _repo_relative(source_path),
        "paper_context": {
            "published_schedule_artifacts": paper_by_na,
            "methods": list(PAPER_METHOD_ORDER),
        },
        "modeling_context": {
            "experiment_scope": (
                "EPANET-BB-equivalent GOPS adaptation on the AnyTown Modified paper assumptions; "
                "not a direct Bonvin public-artifact reproduction."
            ),
            "activation_semantics": source["activation_semantics"],
            "mismatches": source["mismatches"],
            "pump_order": source["pumps"]["best_x_order"],
            "source_priority": source.get("source_priority"),
        },
        "cost_methodology": {
            "comparison_cost": (
                "The report compares GOPS schedules using EPANET-BB audit effective_cost when an audit exists."
            ),
            "gops_internal_cost": (
                "GOPS schedule best_cost/reported_real_cost is retained as GOPS objective evidence, "
                "but is not used as the paper-facing comparison cost because it is computed in the GOPS model."
            ),
            "audit_effective_cost": (
                "The EPANET-BB audit applies the GOPS commanded schedule to the EPANET-BB hydraulic evaluator, "
                "sums pump adjustedTotalCost values, and reports effective_cost_raw / 100 as effective_cost."
            ),
            "delta_formula": "delta = GOPS audit effective_cost - Souza2026 best_cost; delta_percent = delta / Souza2026 best_cost * 100.",
            "no_schedule_policy": "If no complete commanded schedule exists, no audit-compatible GOPS cost is reported.",
        },
        "cases": cases,
    }


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def _cost_runtime_table(comparison: dict[str, Any]) -> str:
    rows = []
    for case in comparison["cases"]:
        gops = case["gops"]
        delta = case["cost_delta_vs_souza2026"]
        runtime_delta = case["runtime_delta_vs_souza2026"]
        rows.append(
            [
                case["case_id"],
                case["na_max"],
                f"`{gops['run_status']}`",
                f"`{gops['schedule_availability']}`",
                _format_number(gops["audit_effective_cost"]),
                _format_number(case["souza2026"]["best_cost"]),
                _format_number(delta["audit_effective_cost_minus_paper"]),
                _format_number(delta["audit_effective_cost_percent_delta"]) + ("%" if delta["audit_effective_cost_percent_delta"] is not None else ""),
                _format_number(gops["gurobi_runtime_seconds"]),
                _format_number(case["souza2026"]["duration_seconds"]),
                _format_number(runtime_delta["gurobi_runtime_percent_delta"]) + ("%" if runtime_delta["gurobi_runtime_percent_delta"] is not None else ""),
            ]
        )
    return _markdown_table(
        [
            "Case",
            "NA_max",
            "GOPS status",
            "Schedule",
            "GOPS audit cost",
            "Souza2026 cost",
            "Cost delta",
            "Cost delta %",
            "GOPS runtime",
            "Souza2026 runtime",
            "Runtime delta %",
        ],
        rows,
    )


def _paper_context_table(comparison: dict[str, Any]) -> str:
    rows = []
    for na_max in (1, 2, 3):
        by_method = {item["method"]: item for item in comparison["paper_context"]["published_schedule_artifacts"][na_max]}
        for method in PAPER_METHOD_ORDER:
            artifact = by_method[method]
            rows.append(
                [
                    method,
                    na_max,
                    _format_number(artifact["best_cost"]),
                    _format_number(artifact["duration_seconds"]),
                    f"`{artifact['path']}`",
                ]
            )
    return _markdown_table(["Method", "NA_max", "Paper cost", "Runtime s", "Artifact"], rows)


def _schedule_table(comparison: dict[str, Any]) -> str:
    rows = []
    for case in comparison["cases"]:
        behavior = case["schedule_behavior"]
        rows.append(
            [
                case["case_id"],
                case["na_max"],
                _format_number(behavior["commanded_pump_hours"]),
                _format_number(behavior["souza2026_commanded_pump_hours"]),
                _format_number(behavior["best_y_hamming_vs_souza2026"]),
                _format_number(behavior["best_x_hamming_vs_souza2026"]),
                _format_number(behavior["aggregate_hours_matching_souza2026"]),
                _format_number(behavior["peak_pumps"]),
                _format_number(behavior["off_hours"]),
            ]
        )
    return _markdown_table(
        [
            "Case",
            "NA_max",
            "GOPS pump-hours",
            "Souza pump-hours",
            "best_y diff",
            "best_x diff",
            "matching y slots",
            "GOPS peak",
            "GOPS off hours",
        ],
        rows,
    )


def _cost_methodology_section(comparison: dict[str, Any]) -> str:
    rows = []
    for case in comparison["cases"]:
        gops = case["gops"]
        has_schedule = gops["schedule_availability"] == "complete_commanded_schedule"
        rows.append(
            [
                case["case_id"],
                case["na_max"],
                _format_number(gops["reported_real_cost"] if has_schedule else None),
                _format_number(gops["schedule_cost"] if has_schedule else None),
                _format_number(gops["audit_effective_cost_raw"]),
                _format_number(gops["audit_effective_cost"]),
                gops["audit_cost_units"] or "n/a",
            ]
        )
    return "\n".join(
        [
            "## Cost Methodology",
            "",
            "The comparison table uses **EPANET-BB audit effective cost** whenever a GOPS schedule was audited. "
            "That is separate from the GOPS internal schedule cost.",
            "",
            "- GOPS internal cost: recorded as `reported_real_cost` in `run.json` and `best_cost` in `schedule.json`; it is computed by the GOPS model objective from commanded pump status and flow variables.",
            "- EPANET-BB audit cost: computed by replaying the GOPS `schedule.json` through the EPANET-BB fixed-schedule evaluator. The evaluator sums pump `adjustedTotalCost` values under EPANET-BB hydraulic simulation semantics and reports `effective_cost = effective_cost_raw / 100`.",
            "- Paper-facing delta: `GOPS audit effective_cost - Souza2026 best_cost`; percent delta divides that result by the Souza2026 paper cost.",
            "- If no complete commanded schedule exists, no audit-compatible GOPS cost is reported.",
            "",
            _markdown_table(
                [
                    "Case",
                    "NA_max",
                    "GOPS reported_real_cost",
                    "GOPS schedule best_cost",
                    "Audit raw cost",
                    "Audit effective cost",
                    "Audit units",
                ],
                rows,
            ),
        ]
    )


def _per_pump_schedule_table(comparison: dict[str, Any]) -> str:
    rows = []
    for case in comparison["cases"]:
        behavior = case["schedule_behavior"]
        gops_schedules = behavior["pump_schedules_h1_to_h24"] or {}
        souza_schedules = behavior["souza2026_pump_schedules_h1_to_h24"]
        for pump_id in ("111", "222", "333"):
            rows.append(
                [
                    case["case_id"],
                    case["na_max"],
                    pump_id,
                    f"`{gops_schedules[pump_id]}`" if pump_id in gops_schedules else "n/a",
                    f"`{souza_schedules[pump_id]}`",
                ]
            )
    return _markdown_table(["Case", "NA_max", "Pump", "GOPS h1-h24", "Souza2026 h1-h24"], rows)


def _artifact_table(comparison: dict[str, Any]) -> str:
    rows = []
    for case in comparison["cases"]:
        artifacts = case["artifacts"]
        rows.append(
            [
                case["case_id"],
                f"`{artifacts['run_json']}`",
                f"`{artifacts['schedule_json']}`" if artifacts["schedule_json"] else "none",
                f"`{artifacts['audit_json']}`" if artifacts["audit_json"] else "none",
            ]
        )
    return _markdown_table(["Case", "Run manifest", "Schedule", "Audit"], rows)


def _provenance_table(comparison: dict[str, Any]) -> str:
    rows = []
    for case in comparison["cases"]:
        provenance = case["provenance"]
        rows.append(
            [
                case["case_id"],
                provenance["host"],
                f"`{provenance['run_class']}`",
                f"`{provenance['commit'][:12]}`",
                str(provenance["dirty"]).lower(),
                provenance["solver"].get("gurobi_version", "n/a"),
                provenance["solver"].get("license_status", "n/a"),
                _format_number(provenance["runtime_settings"].get("time_limit_seconds")),
            ]
        )
    return _markdown_table(
        ["Case", "Host", "Class", "Commit", "Dirty", "Gurobi", "License", "Time limit"],
        rows,
    )


def render_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# Issue 19 GOPS vs EPANET-BB Paper Comparison",
        "",
        "GitHub issue: `michaelsouza/gopslpnlpbb#19`",
        "",
        f"Source run id: `{comparison['source_run_id']}`",
        "",
        "This note compares the EPANET-BB-equivalent GOPS adaptation against the EPANET-BB paper schedule artifacts. "
        "It is not a direct Bonvin public-artifact reproduction and must not be merged with the Bonvin public-artifact sufficiency conclusion.",
        "",
        "## Summary",
        "",
        _cost_runtime_table(comparison),
        "",
        "Interpretation:",
        "",
        "- `NA_max = 1` timed out under the matched 5-second budget without a complete GOPS commanded schedule, so no audit-compatible GOPS cost exists for that case.",
        "- `NA_max = 2` and `NA_max = 3` produced complete commanded schedules and EPANET-BB audit artifacts, but their audited effective costs are higher than the corresponding Souza2026 paper schedules.",
        "- GOPS solver schedule costs are recorded in the JSON comparison as GOPS-run objective evidence; the table above uses EPANET-BB audit effective cost when a schedule was audited.",
        "",
        _cost_methodology_section(comparison),
        "",
        "## Paper Context",
        "",
        "The downstream source material contains schedule JSON artifacts for Costa2016, Cimorelli2020, Paola2025, and Souza2026 for each `NA_max` case:",
        "",
        _paper_context_table(comparison),
        "",
        "## Schedule Behavior",
        "",
        _schedule_table(comparison),
        "",
        "The `best_y` and `best_x` differences compare GOPS schedules to the corresponding Souza2026 schedule artifact. The initial h=0 all-off slot is included in both vectors.",
        "",
        "### Per-Pump Commanded Schedules",
        "",
        _per_pump_schedule_table(comparison),
        "",
        "## Audit Events",
        "",
    ]

    audit_rows = []
    for case in comparison["cases"]:
        counts = case["gops"]["audit_event_counts"] or {}
        audit_rows.append(
            [
                case["case_id"],
                _format_number(case["gops"]["audit_feasible"]),
                _format_number(counts.get("temporary_link_closures")),
                _format_number(counts.get("commanded_on_temp_closed")),
                _format_number(counts.get("commanded_on_zero_flow")),
                _format_number(counts.get("tank_clamp_events")),
                _format_number(counts.get("tank_boundary_contacts")),
            ]
        )
    lines.extend(
        [
            _markdown_table(
                [
                    "Case",
                    "Audit feasible",
                    "Temporary closures",
                    "Commanded-on temp closed",
                    "Commanded-on zero flow",
                    "Tank clamps",
                    "Tank boundary contacts",
                ],
                audit_rows,
            ),
            "",
            "## Modeling And Source-Of-Truth Notes",
            "",
            "- Scope: EPANET-BB-equivalent GOPS adaptation on the AnyTown Modified paper assumptions, not a direct reproduction of Bonvin public GOPS artifacts.",
            "- Source priority: when manuscript prose conflicts with executable code or published schedule JSONs, the comparison target is the operative code/artifact behavior.",
            "- Activation semantics: separate per-pump start and stop budgets, each equal to `NA_max`; the explicit h=0 to h=1 initialization transition is represented but not charged.",
            "- Pump order: `best_x` uses `[111, 222, 333]`, even though INP pump rows use a different source order.",
            "- Network wording mismatch: the operative INP contains 41 pipe rows plus 3 pump rows, not 44 pipe rows.",
            "- The GOPS translated pump physics and source/tank representation are experiment assumptions recorded in the translation docs and run artifacts.",
            "",
            "## Remote Execution Provenance",
            "",
            _provenance_table(comparison),
            "",
            "Dirty-worktree note: the matched-budget summary records that `NA_max = 2` and `NA_max = 3` were serial remote runs after prior output artifacts from the same battery had already been written; all three matched-budget runs share the same source commit.",
            "",
            "## Artifact Paths",
            "",
            _artifact_table(comparison),
            "",
            "Machine-readable comparison: `output/epanet_bb_equivalent_gops/issue19-matched-budget-comparison.json`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    comparison = build_comparison(args.source, args.output_root, args.run_id)
    _write_json(args.json_output, comparison)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(comparison), encoding="utf-8")
    print(f"wrote {_repo_relative(args.json_output)}")
    print(f"wrote {_repo_relative(args.markdown_output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
