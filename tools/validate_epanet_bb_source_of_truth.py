"""Validate the EPANET-BB AnyTown Modified source-of-truth artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PUMPS = ("111", "222", "333")
CASE_IDS = {
    "atm-24h-na1": 1,
    "atm-24h-na2": 2,
    "atm-24h-na3": 3,
}


def transition_counts(best_x: list[int], pump_index: int) -> dict[str, int]:
    series = [best_x[hour * len(PUMPS) + pump_index] for hour in range(25)]
    starts_including_initial = 0
    stops_including_initial = 0
    starts_excluding_initial = 0
    stops_excluding_initial = 0

    for hour in range(1, 25):
        old = series[hour - 1]
        new = series[hour]
        if old == 0 and new == 1:
            starts_including_initial += 1
            if hour >= 2:
                starts_excluding_initial += 1
        elif old == 1 and new == 0:
            stops_including_initial += 1
            if hour >= 2:
                stops_excluding_initial += 1

    return {
        "starts_excluding_initial": starts_excluding_initial,
        "stops_excluding_initial": stops_excluding_initial,
        "starts_including_initial": starts_including_initial,
        "stops_including_initial": stops_including_initial,
    }


def validate(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["schema_version"] == "epanet-bb-anytown-source-v1"
    assert data["implemented_for"] == "michaelsouza/gopslpnlpbb#12"
    assert data["benchmark"]["name"] == "AnyTown Modified"
    assert data["benchmark"]["network_counts"]["junction_rows"] == 19
    assert data["benchmark"]["network_counts"]["tank_rows"] == 3
    assert data["benchmark"]["network_counts"]["pipe_rows"] == 41
    assert data["benchmark"]["network_counts"]["pump_rows"] == 3
    assert data["benchmark"]["network_counts"]["pipe_plus_pump_links"] == 44
    assert [tank["id"] for tank in data["benchmark"]["tanks"]] == ["65", "165", "265"]

    assert data["horizon"]["h_max"] == 24
    assert data["horizon"]["best_y_length"] == 25
    assert data["horizon"]["best_x_length"] == 75

    assert len(data["demand"]["pattern_values"]["DEM"]) == 24
    assert len(data["demand"]["junctions"]) == 19
    assert len(data["energy_tariff"]["values"]) == 24
    assert data["pumps"]["best_x_order"] == list(PUMPS)

    artifacts = data["published_schedule_artifacts"]
    assert len(artifacts) == 12
    for artifact in artifacts:
        assert artifact["best_x_length"] == 75
        assert artifact["best_y_length"] == 25
        assert artifact["NA_max"] in (1, 2, 3)

    cases = data["target_cases"]
    assert {case["case_id"] for case in cases} == set(CASE_IDS)

    for case in cases:
        case_id = case["case_id"]
        na_max = case["NA_max"]
        best_y = case["best_y"]
        best_x = case["best_x"]

        assert CASE_IDS[case_id] == na_max
        assert len(best_y) == 25
        assert len(best_x) == 75
        assert best_y[0] == 0
        assert best_x[:3] == [0, 0, 0]

        for hour in range(25):
            chunk = best_x[hour * len(PUMPS) : (hour + 1) * len(PUMPS)]
            assert sum(chunk) == best_y[hour], (case_id, hour, chunk, best_y[hour])

        recorded_counts = {item["pump"]: item for item in case["operative_transition_counts"]}
        assert set(recorded_counts) == set(PUMPS)

        for pump_index, pump in enumerate(PUMPS):
            counts = transition_counts(best_x, pump_index)
            assert counts == {
                key: recorded_counts[pump][key]
                for key in (
                    "starts_excluding_initial",
                    "stops_excluding_initial",
                    "starts_including_initial",
                    "stops_including_initial",
                )
            }
            assert counts["starts_excluding_initial"] <= na_max
            assert counts["stops_excluding_initial"] <= na_max


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "artifact",
        nargs="?",
        default="docs/epanet-bb-anytown-modified-source-of-truth.json",
        type=Path,
    )
    args = parser.parse_args()
    validate(args.artifact)
    print(f"validated {args.artifact}")


if __name__ == "__main__":
    main()
