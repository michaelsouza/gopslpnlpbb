from __future__ import annotations

import json
from pathlib import Path

from run_epanet_bb_gops_experiment import (
    CONTRACT_VERSION,
    TRACK,
    classify_exception,
    make_case_metadata,
    make_output_paths,
    make_run_manifest,
    parse_args,
    run,
)


def test_runner_output_paths_are_namespaced_by_case_and_run_id() -> None:
    paths = make_output_paths("atm-24h-na2", "unit-run")

    assert paths.root == Path("output/epanet_bb_equivalent_gops/atm-24h-na2/unit-run")
    assert paths.run_manifest == paths.root / "run.json"
    assert paths.solver_log == paths.root / "solver.log"


def test_case_metadata_declares_epanet_bb_activation_semantics() -> None:
    case = make_case_metadata("atm-24h-na3")

    assert case["case_id"] == "atm-24h-na3"
    assert case["na_max"] == 3
    assert case["activation_semantics"]["target"] == "operative-epanet-bb-artifacts"
    assert "separate per-pump start and stop budgets" in case["activation_semantics"]["accounting"]
    assert "h=0 -> h=1" in case["activation_semantics"]["initialization"]
    assert [pump["epanet_id"] for pump in case["pumps"]] == ["111", "222", "333"]


def test_environment_blocked_manifest_is_contract_shaped(tmp_path: Path) -> None:
    paths = make_output_paths("atm-24h-na1", "blocked-run")
    manifest = make_run_manifest(
        case_id="atm-24h-na1",
        run_class="final",
        command=["runner", "atm-24h-na1"],
        paths=paths,
        host_name="not-labma-sol",
        working_directory=tmp_path,
        runtime_settings={"time_limit_seconds": 1.0, "mip_gap": 1e-6, "mode": "build"},
        status={
            "run_status": "environment_blocked",
            "schedule_availability": "none",
            "detail": "final runs must identify labma-sol as host",
        },
        solver={"name": "Gurobi", "license_status": "not_checked"},
    )

    assert manifest["contract_version"] == CONTRACT_VERSION
    assert manifest["track"] == TRACK
    assert manifest["environment"]["run_class"] == "final"
    assert manifest["environment"]["host_name"] == "not-labma-sol"
    assert manifest["status"]["run_status"] == "environment_blocked"
    assert manifest["outputs"]["root"] == "output/epanet_bb_equivalent_gops/atm-24h-na1/blocked-run"
    json.dumps(manifest)


def test_classify_license_exception() -> None:
    err = RuntimeError("No Gurobi license found")
    status = classify_exception(err)

    assert status["run_status"] == "license_blocked"
    assert status["schedule_availability"] == "none"


def test_final_run_on_non_labma_host_writes_blocked_manifest(tmp_path: Path) -> None:
    args = parse_args(
        [
            "atm-24h-na1",
            "--run-class",
            "final",
            "--host-name",
            "local-dev-host",
            "--run-id",
            "blocked-final",
            "--output-root",
            str(tmp_path / "output"),
        ]
    )

    exit_code = run(args, ["runner", "atm-24h-na1"])

    assert exit_code == 2
    manifest = json.loads((tmp_path / "output" / "atm-24h-na1" / "blocked-final" / "run.json").read_text())
    assert manifest["environment"]["run_class"] == "final"
    assert manifest["environment"]["host_name"] == "local-dev-host"
    assert manifest["status"]["run_status"] == "environment_blocked"
