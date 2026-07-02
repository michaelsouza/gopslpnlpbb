"""Validate the EPANET-BB-equivalent GOPS case translation."""

from __future__ import annotations

import argparse
import json
import math
import sys
import types
from pathlib import Path
from typing import Any


PUMP_ARCS = [("R111", "J20"), ("R222", "J20"), ("R333", "J20")]
CASE_TO_NA_MAX = {
    "atm-24h-na1": 1,
    "atm-24h-na2": 2,
    "atm-24h-na3": 3,
}


def install_pandas_stub_if_needed() -> None:
    """Allow Instance construction where pandas is absent.

    The translation validator does not read HDF bounds. The legacy Instance
    module imports pandas for parse_bounds(), so a tiny stub keeps this
    construction-only check independent of optional solver-run dependencies.
    """

    try:
        import pandas  # noqa: F401
    except ModuleNotFoundError:
        stub = types.ModuleType("pandas")

        def read_hdf(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("pandas is required only when parse_bounds() is used")

        stub.read_hdf = read_hdf  # type: ignore[attr-defined]
        sys.modules["pandas"] = stub


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-6) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tol):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def construct_instance(repo: Path, translation: dict[str, Any]):
    install_pandas_stub_if_needed()
    sys.path.insert(0, str(repo / "src"))
    from instance import Instance

    dataset = translation["translated_dataset"]
    Instance.DATADIR = repo / "data"
    Instance.BNDSDIR = repo / "bounds"
    return Instance(
        dataset["instance_name"],
        dataset["gops_profile_name"],
        dataset["start_time"],
        dataset["end_time"],
        dataset["aggregate_steps"],
    )


def validate_cases(translation: dict[str, Any]) -> None:
    cases = translation["first_class_cases"]
    seen = {case["case_id"]: case["na_max"] for case in cases}
    assert seen == CASE_TO_NA_MAX
    for case in cases:
        assert case["gops_base_instance_key"] == "ATM e 24 1"
        assert "pending michaelsouza/gopslpnlpbb#15" == case["na_max_implementation_status"]


def validate_instance_shape(inst: Any, source: dict[str, Any]) -> None:
    counts = source["benchmark_identity"]["operational_network_counts_from_inp"]
    assert inst.name == "EpanetBB_Anytown"
    assert inst.nperiods() == source["horizon"]["periods"]
    assert_close(inst.tsinhours(), source["horizon"]["period_duration_hours"], "period duration")
    assert len(inst.junctions) == counts["junctions"]
    assert len(inst.reservoirs) == 3
    assert len(inst.tanks) == counts["tanks"]
    assert len(inst.pipes) == counts["pipes"]
    assert len(inst.pumps) == counts["pumps"]
    assert len(inst.valves) == counts["valves"]
    assert inst.symmetries == PUMP_ARCS


def validate_profiles(inst: Any, source: dict[str, Any]) -> None:
    expected_dem = source["demand"]["patterns"]["DEM"]
    expected_tariff = source["tariff"]["values"]
    for profile_id in ("DEM", "DEM55", "DEM90", "DEM170"):
        assert inst.profiles[profile_id] == expected_dem
    assert inst.tariff == expected_tariff


def validate_junction_demands(inst: Any, source: dict[str, Any]) -> None:
    for source_junction in source["demand"]["junctions"]:
        gops_id = f"J{source_junction['id']}"
        expected = round(source_junction["base_demand"] / 3.6, 6)
        actual = inst.junctions[gops_id].dmean
        assert_close(actual, expected, f"junction {gops_id} demand")
        assert inst.junctions[gops_id].profileid == source_junction["pattern"]


def validate_tanks(inst: Any, source: dict[str, Any]) -> None:
    tank_source = source["tanks"]
    for tank_id in tank_source["target_ids"]:
        tank = inst.tanks[f"T{tank_id}"]
        assert_close(tank.head(tank.vmin), tank_source["minimum_level_m"], f"T{tank_id} min level")
        assert_close(tank.head(tank.vinit), tank_source["initial_level_m"], f"T{tank_id} initial level")
        assert_close(tank.head(tank.vmax), tank_source["maximum_level_m"], f"T{tank_id} max level")


def validate_sources(inst: Any, source: dict[str, Any]) -> None:
    expected_head = source["source"]["head"]
    assert sorted(inst.reservoirs) == ["R111", "R222", "R333"]
    for reservoir in inst.reservoirs.values():
        assert reservoir.profileid == "constant"
        assert_close(reservoir.altitude(), expected_head, f"{reservoir.id} source head")
        assert reservoir.heads == [expected_head] * 24


def validate_pumps(inst: Any, translation: dict[str, Any]) -> None:
    decisions = translation["representation_decisions"]["pumps"]
    expected_arcs = [tuple(item["gops_arc"]) for item in decisions["mapping"]]
    assert expected_arcs == PUMP_ARCS
    assert list(inst.pumps) == PUMP_ARCS
    for item in decisions["mapping"]:
        arc = tuple(item["gops_arc"])
        pump = inst.pumps[arc]
        assert pump.id == item["gops_pump_id"]


def validate(repo: Path, source_path: Path, translation_path: Path) -> None:
    source = load_json(source_path)
    translation = load_json(translation_path)
    assert translation["implemented_for"] == "michaelsouza/gopslpnlpbb#14"
    assert translation["source_of_truth"] == "docs/epanet-bb-source-of-truth-cases.json"

    validate_cases(translation)
    inst = construct_instance(repo, translation)
    validate_instance_shape(inst, source)
    validate_profiles(inst, source)
    validate_junction_demands(inst, source)
    validate_tanks(inst, source)
    validate_sources(inst, source)
    validate_pumps(inst, translation)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("docs/epanet-bb-source-of-truth-cases.json"),
    )
    parser.add_argument(
        "--translation",
        type=Path,
        default=Path("docs/epanet-bb-gops-case-translation.json"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    validate(repo, repo / args.source, repo / args.translation)
    print(f"validated {args.translation}")


if __name__ == "__main__":
    main()
