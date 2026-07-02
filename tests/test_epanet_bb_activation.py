from __future__ import annotations

import json
from pathlib import Path

import pytest

from activation import (
    EPANET_BB_OPERATIVE_SEMANTICS,
    PUBLIC_GOPS_START_LIMIT_SEMANTICS,
    count_start_stop_transitions,
    public_gops_start_limit_config,
    resolve_epanet_bb_case,
    validate_epanet_bb_best_x,
)


REPO = Path(__file__).resolve().parents[1]


def flatten_by_hour(series_by_pump: dict[str, list[int]], pump_order: tuple[str, ...]) -> list[int]:
    horizon = len(next(iter(series_by_pump.values())))
    return [
        series_by_pump[pump][hour]
        for hour in range(horizon)
        for pump in pump_order
    ]


def test_epanet_bb_cases_are_first_class_and_labeled() -> None:
    assert PUBLIC_GOPS_START_LIMIT_SEMANTICS != EPANET_BB_OPERATIVE_SEMANTICS

    for case_id, na_max in {
        "atm-24h-na1": 1,
        "atm-24h-na2": 2,
        "atm-24h-na3": 3,
    }.items():
        case = resolve_epanet_bb_case(case_id)
        assert case.case_id == case_id
        assert case.na_max == na_max
        assert case.gops_base_instance_key == "ATM e 24 1"
        assert case.activation_semantics == EPANET_BB_OPERATIVE_SEMANTICS
        assert case.activation_config().uses_separate_stop_budget is True
        assert case.activation_config().enforce_symmetric_ordering is False

    assert public_gops_start_limit_config().uses_separate_stop_budget is False
    assert public_gops_start_limit_config().enforce_symmetric_ordering is True


def test_epanet_bb_transition_counts_do_not_charge_initial_start() -> None:
    counts = count_start_stop_transitions([0, 1, 0, 1, 1])
    assert counts == {"starts": 1, "stops": 1}


def test_epanet_bb_best_x_validator_accepts_separate_start_stop_budgets() -> None:
    pump_order = ("111", "222", "333")
    best_x = flatten_by_hour(
        {
            "111": [0, 1, 0, 1],
            "222": [0, 0, 1, 1],
            "333": [0, 0, 0, 0],
        },
        pump_order,
    )

    counts = validate_epanet_bb_best_x(best_x, na_max=1, pump_order=pump_order)

    assert counts["111"] == {"starts": 1, "stops": 1}
    assert counts["222"] == {"starts": 1, "stops": 0}


def test_epanet_bb_best_x_validator_rejects_start_or_stop_budget_violation() -> None:
    pump_order = ("111", "222", "333")
    best_x = flatten_by_hour(
        {
            "111": [0, 1, 0, 1, 0, 1],
            "222": [0, 0, 0, 0, 0, 0],
            "333": [0, 0, 0, 0, 0, 0],
        },
        pump_order,
    )

    with pytest.raises(ValueError, match="pump 111"):
        validate_epanet_bb_best_x(best_x, na_max=1, pump_order=pump_order)


def test_epanet_bb_best_x_validator_rejects_nonzero_hour_zero_state() -> None:
    pump_order = ("111", "222", "333")
    best_x = flatten_by_hour(
        {
            "111": [1, 1, 0],
            "222": [0, 0, 0],
            "333": [0, 0, 0],
        },
        pump_order,
    )

    with pytest.raises(ValueError, match="hour-0"):
        validate_epanet_bb_best_x(best_x, na_max=1, pump_order=pump_order)


def test_epanet_bb_source_schedule_artifacts_match_operating_semantics() -> None:
    source = json.loads(
        (REPO / "docs" / "epanet-bb-anytown-modified-source-of-truth.json").read_text(encoding="utf-8")
    )

    for case in source["target_cases"]:
        validate_epanet_bb_best_x(
            case["best_x"],
            na_max=case["NA_max"],
            pump_order=tuple(source["pumps"]["best_x_order"]),
        )
