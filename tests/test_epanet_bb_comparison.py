from __future__ import annotations

from pathlib import Path

from compare_epanet_bb_gops_results import (
    DEFAULT_RUN_ID,
    build_comparison,
    render_markdown,
    schedule_behavior,
)


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "docs" / "epanet-bb-anytown-modified-source-of-truth.json"
OUTPUT_ROOT = REPO / "output" / "epanet_bb_equivalent_gops"


def test_schedule_behavior_keeps_missing_gops_schedule_explicit() -> None:
    target = {
        "best_y": [0, 1, 0],
        "pump_schedules_h1_to_h24": {"111": "10", "222": "00", "333": "00"},
    }

    behavior = schedule_behavior(None, target)

    assert behavior["available"] is False
    assert behavior["commanded_pump_hours"] is None
    assert behavior["souza2026_commanded_pump_hours"] == 1
    assert behavior["pump_schedules_h1_to_h24"] is None


def test_build_comparison_summarizes_all_issue19_cases() -> None:
    comparison = build_comparison(SOURCE, OUTPUT_ROOT, DEFAULT_RUN_ID)

    assert comparison["artifact_type"] == "epanet-bb-equivalent-gops-paper-comparison"
    assert [case["case_id"] for case in comparison["cases"]] == [
        "atm-24h-na1",
        "atm-24h-na2",
        "atm-24h-na3",
    ]
    assert comparison["paper_context"]["methods"] == [
        "Costa2016",
        "Cimorelli2020",
        "Paola2025",
        "Souza2026",
    ]
    assert "audit_effective_cost" in comparison["cost_methodology"]


def test_build_comparison_does_not_promote_na1_to_audited_schedule() -> None:
    comparison = build_comparison(SOURCE, OUTPUT_ROOT, DEFAULT_RUN_ID)
    na1 = comparison["cases"][0]

    assert na1["case_id"] == "atm-24h-na1"
    assert na1["gops"]["run_status"] == "time_limit_no_schedule"
    assert na1["gops"]["audit_effective_cost"] is None
    assert na1["schedule_behavior"]["available"] is False
    assert na1["artifacts"]["schedule_json"] is None
    assert na1["artifacts"]["audit_json"] is None


def test_build_comparison_uses_epanet_bb_audit_cost_for_schedule_cases() -> None:
    comparison = build_comparison(SOURCE, OUTPUT_ROOT, DEFAULT_RUN_ID)
    na2 = comparison["cases"][1]
    na3 = comparison["cases"][2]

    assert na2["gops"]["audit_effective_cost"] == 4301.8142428452275
    assert na2["gops"]["audit_effective_cost_raw"] == 430181.42428452277
    assert na2["gops"]["audit_feasible"] is True
    assert na2["cost_delta_vs_souza2026"]["audit_effective_cost_minus_paper"] > 0
    assert na3["gops"]["audit_effective_cost"] == 4379.529815587469
    assert na3["gops"]["audit_effective_cost_raw"] == 437952.98155874683
    assert na3["gops"]["audit_feasible"] is True
    assert na3["cost_delta_vs_souza2026"]["audit_effective_cost_minus_paper"] > 0


def test_render_markdown_states_scope_and_paper_context() -> None:
    comparison = build_comparison(SOURCE, OUTPUT_ROOT, DEFAULT_RUN_ID)
    markdown = render_markdown(comparison)

    assert "not a direct Bonvin public-artifact reproduction" in markdown
    assert "Costa2016" in markdown
    assert "Cimorelli2020" in markdown
    assert "Paola2025" in markdown
    assert "Souza2026" in markdown
    assert "`time_limit_no_schedule`" in markdown
    assert "Cost Methodology" in markdown
    assert "effective_cost = effective_cost_raw / 100" in markdown
    assert "| atm-24h-na1 | 1 | n/a | n/a | n/a | n/a | n/a |" in markdown
    assert "| atm-24h-na1 | 1 | 0 |" not in markdown
    assert "Per-Pump Commanded Schedules" in markdown
    assert "`100000000000000011110011`" in markdown
