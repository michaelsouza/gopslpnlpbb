"""Activation-limit semantics for GOPS experiment cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


EPANET_BB_TRACK = "epanet-bb-equivalent-gops"
EPANET_BB_OPERATIVE_SEMANTICS = "epanet-bb-operative-separate-start-stop-budgets-v1"
PUBLIC_GOPS_START_LIMIT_SEMANTICS = "bonvin-gops-hardcoded-symmetric-start-limit-v1"
EPANET_BB_PUMP_ORDER = ("111", "222", "333")


@dataclass(frozen=True)
class ActivationConfig:
    """Model-side activation-limit configuration."""

    semantics: str
    na_max: int | None = None
    public_start_limit: int = 6
    exclude_initial_transition: bool = True
    uses_separate_stop_budget: bool = False
    enforce_symmetric_ordering: bool = True


@dataclass(frozen=True)
class EpanetBBExperimentCase:
    """First-class EPANET-BB-equivalent GOPS case metadata."""

    case_id: str
    na_max: int
    gops_base_instance_key: str = "ATM e 24 1"
    track: str = EPANET_BB_TRACK
    activation_semantics: str = EPANET_BB_OPERATIVE_SEMANTICS
    pump_order: tuple[str, ...] = EPANET_BB_PUMP_ORDER

    def activation_config(self) -> ActivationConfig:
        return ActivationConfig(
            semantics=self.activation_semantics,
            na_max=self.na_max,
            exclude_initial_transition=True,
            uses_separate_stop_budget=True,
            enforce_symmetric_ordering=False,
        )


EPANET_BB_CASES = {
    "atm-24h-na1": EpanetBBExperimentCase("atm-24h-na1", 1),
    "atm-24h-na2": EpanetBBExperimentCase("atm-24h-na2", 2),
    "atm-24h-na3": EpanetBBExperimentCase("atm-24h-na3", 3),
}


def public_gops_start_limit_config() -> ActivationConfig:
    return ActivationConfig(
        semantics=PUBLIC_GOPS_START_LIMIT_SEMANTICS,
        na_max=None,
        public_start_limit=6,
        exclude_initial_transition=False,
        uses_separate_stop_budget=False,
        enforce_symmetric_ordering=True,
    )


def iter_epanet_bb_cases() -> Iterable[EpanetBBExperimentCase]:
    return EPANET_BB_CASES.values()


def resolve_epanet_bb_case(case_id: str) -> EpanetBBExperimentCase:
    try:
        return EPANET_BB_CASES[case_id]
    except KeyError as err:
        known = ", ".join(sorted(EPANET_BB_CASES))
        raise ValueError(f"unknown EPANET-BB GOPS case {case_id!r}; expected one of: {known}") from err


def count_start_stop_transitions(series: list[int], *, count_initial: bool = False) -> dict[str, int]:
    """Count 0->1 starts and 1->0 stops in an hour-indexed binary series.

    The EPANET-BB operative comparison target keeps an explicit hour-0 all-off
    state, but does not charge the hour-0 to hour-1 initialization transition.
    """

    if len(series) < 2:
        return {"starts": 0, "stops": 0}

    starts = 0
    stops = 0
    for hour in range(1, len(series)):
        if hour == 1 and not count_initial:
            continue
        old = series[hour - 1]
        new = series[hour]
        if old == 0 and new == 1:
            starts += 1
        elif old == 1 and new == 0:
            stops += 1
    return {"starts": starts, "stops": stops}


def split_best_x_by_pump(best_x: list[int], pump_order: tuple[str, ...] = EPANET_BB_PUMP_ORDER) -> dict[str, list[int]]:
    if not pump_order:
        raise ValueError("pump_order must not be empty")
    if len(best_x) % len(pump_order) != 0:
        raise ValueError(
            f"best_x length {len(best_x)} is not divisible by pump count {len(pump_order)}"
        )

    horizon = len(best_x) // len(pump_order)
    by_pump = {pump: [] for pump in pump_order}
    for hour in range(horizon):
        chunk = best_x[hour * len(pump_order):(hour + 1) * len(pump_order)]
        for pump, value in zip(pump_order, chunk):
            if value not in (0, 1):
                raise ValueError(f"best_x contains non-binary value {value!r} for pump {pump} at hour {hour}")
            by_pump[pump].append(value)
    return by_pump


def validate_epanet_bb_best_x(
    best_x: list[int],
    *,
    na_max: int,
    pump_order: tuple[str, ...] = EPANET_BB_PUMP_ORDER,
) -> dict[str, dict[str, int]]:
    if na_max not in (1, 2, 3):
        raise ValueError(f"EPANET-BB-equivalent cases support NA_max 1, 2, or 3; got {na_max}")

    counts_by_pump = {}
    violations = []
    for pump, series in split_best_x_by_pump(best_x, pump_order).items():
        if series[0] != 0:
            violations.append(f"pump {pump} hour-0 state={series[0]} must be 0")
        counts = count_start_stop_transitions(series, count_initial=False)
        counts_by_pump[pump] = counts
        if counts["starts"] > na_max:
            violations.append(f"pump {pump} starts={counts['starts']} > NA_max={na_max}")
        if counts["stops"] > na_max:
            violations.append(f"pump {pump} stops={counts['stops']} > NA_max={na_max}")

    if violations:
        raise ValueError("; ".join(violations))
    return counts_by_pump
