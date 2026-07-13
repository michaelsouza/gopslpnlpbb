from __future__ import annotations

import json
import os
from pathlib import Path
import textwrap

import run_epanet_bb_gops_experiment as runner
from run_epanet_bb_gops_experiment import (
    CONTRACT_VERSION,
    TRACK,
    _lpnlpbb_schedule_candidate,
    _load_warm_start,
    _make_schedule_artifact,
    classify_license_status,
    classify_exception,
    make_case_metadata,
    make_output_paths,
    make_run_manifest,
    parse_args,
    run,
)


class FakePump:
    def __init__(self, pump_id: str) -> None:
        self.id = pump_id


class FakeInstance:
    pumps = {
        ("R111", "J20"): FakePump("111"),
        ("R222", "J20"): FakePump("222"),
        ("R333", "J20"): FakePump("333"),
    }

    def horizon(self) -> range:
        return range(24)


class DisposableModel:
    def __init__(self) -> None:
        self.disposed = False

    def dispose(self) -> None:
        self.disposed = True


def one_pump_on_plan() -> dict[int, dict[tuple[str, str], int]]:
    return {
        period: {
            ("R111", "J20"): 1,
            ("R222", "J20"): 0,
            ("R333", "J20"): 0,
        }
        for period in range(24)
    }


def test_runner_output_paths_are_namespaced_by_case_and_run_id() -> None:
    paths = make_output_paths("atm-24h-na2", "unit-run")

    assert paths.root == Path("output/epanet_bb_equivalent_gops/atm-24h-na2/unit-run")
    assert paths.run_manifest == paths.root / "run.json"
    assert paths.schedule_json == paths.root / "schedule.json"
    assert paths.audit_json == paths.root / "audit.json"
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
    assert manifest["outputs"]["schedule_json"] is None
    json.dumps(manifest)


def test_manifest_records_schedule_path_only_when_schedule_is_written(tmp_path: Path) -> None:
    paths = make_output_paths("atm-24h-na1", "scheduled-run")
    manifest = make_run_manifest(
        case_id="atm-24h-na1",
        run_class="dev",
        command=["runner", "atm-24h-na1"],
        paths=paths,
        host_name="local-dev-host",
        working_directory=tmp_path,
        runtime_settings={"time_limit_seconds": 1.0, "mip_gap": 1e-6, "mode": "lpnlpbb"},
        status={
            "run_status": "success",
            "schedule_availability": "complete_commanded_schedule",
        },
        solver={"name": "Gurobi", "license_status": "valid"},
        schedule_written=True,
    )

    assert manifest["outputs"]["schedule_json"] == "output/epanet_bb_equivalent_gops/atm-24h-na1/scheduled-run/schedule.json"
    assert manifest["outputs"]["audit_json"] is None


def test_schedule_artifact_exports_epanet_bb_best_y_and_best_x() -> None:
    args = parse_args(["atm-24h-na1", "--execution-mode", "lpnlpbb"])
    artifact = _make_schedule_artifact(
        args,
        FakeInstance(),
        one_pump_on_plan(),
        source={"kind": "unit-test", "adjusted": False},
        cost=123.45,
        duration=6.7,
    )

    assert artifact["case_id"] == "atm-24h-na1"
    assert artifact["na_max"] == 1
    assert artifact["method_name"] == "GOPS LP-NLP branch-and-bound"
    assert artifact["best_y"] == [0, *([1] * 24)]
    assert len(artifact["best_x"]) == 75
    assert artifact["best_x"][:6] == [0, 0, 0, 1, 0, 0]
    assert artifact["pump_schedules_h1_to_h24"] == {
        "111": "1" * 24,
        "222": "0" * 24,
        "333": "0" * 24,
    }
    assert artifact["pump_mapping"]["best_x_order"] == ["111", "222", "333"]
    assert artifact["best_cost"] == 123.45
    assert artifact["duration_seconds"] == 6.7


def test_warm_start_translates_epanet_bb_best_x_and_keeps_provenance(tmp_path: Path) -> None:
    schedule_path = tmp_path / "best_global.json"
    schedule_path.write_text(
        json.dumps(
            {
                "track": "epanet-bb-warm-start-source-v1",
                "case_id": "atm-24h-na1",
                "na_max": 1,
                "h_max": 24,
                "max_actuations": 1,
                "best_x": [0, 0, 0, *([1, 0, 0] * 24)],
            }
        ),
        encoding="utf-8",
    )
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(
        json.dumps(
            {
                "source_issue": "michaelsouza/epanet-bb#22",
                "run_tag": "labma-sol-20260705T170040Z-default-p64",
                "epanet_bb_commit": "da60da9",
                "case_id": "atm-24h-na1",
                "na_max": 1,
                "hydraulic_accuracy": 1e-4,
                "feasibility_semantics": "default_epanet_simulated",
                "best_artifact_path": str(schedule_path),
            }
        ),
        encoding="utf-8",
    )
    args = parse_args(
        [
            "atm-24h-na1",
            "--warm-start-schedule",
            str(schedule_path),
            "--warm-start-provenance",
            str(provenance_path),
        ]
    )

    warm_start = _load_warm_start(args, FakeInstance())

    assert warm_start is not None
    assert warm_start.plan[0][("R111", "J20")] == 1
    assert warm_start.plan[0][("R222", "J20")] == 0
    assert warm_start.metadata["provenance"]["run_tag"] == "labma-sol-20260705T170040Z-default-p64"


def test_warm_start_requires_matching_case_provenance(tmp_path: Path) -> None:
    schedule_path = tmp_path / "best_global.json"
    schedule_path.write_text(
        json.dumps(
            {
                "track": "epanet-bb-warm-start-source-v1",
                "case_id": "atm-24h-na1",
                "na_max": 1,
                "h_max": 24,
                "max_actuations": 1,
                "best_x": [0, 0, 0, *([1, 0, 0] * 24)],
            }
        ),
        encoding="utf-8",
    )
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(
        json.dumps(
            {
                "source_issue": "michaelsouza/epanet-bb#22",
                "run_tag": "labma-sol-20260705T170040Z-default-p64",
                "epanet_bb_commit": "da60da9",
                "case_id": "atm-24h-na1",
                "na_max": 2,
                "hydraulic_accuracy": 1e-4,
                "feasibility_semantics": "default_epanet_simulated",
                "best_artifact_path": str(schedule_path),
            }
        ),
        encoding="utf-8",
    )
    args = parse_args(
        [
            "atm-24h-na1",
            "--warm-start-schedule",
            str(schedule_path),
            "--warm-start-provenance",
            str(provenance_path),
        ]
    )

    try:
        _load_warm_start(args, FakeInstance())
    except ValueError as exc:
        assert "NA_max=2" in str(exc)
    else:
        raise AssertionError("expected mismatched warm-start provenance to be rejected")


def test_adjusted_only_lpnlpbb_solution_is_not_promoted_to_schedule() -> None:
    args = parse_args(["atm-24h-na1", "--execution-mode", "lpnlpbb"])
    model = type(
        "FakeModel",
        (),
        {
            "_solutions": [
                {
                    "plan": one_pump_on_plan(),
                    "cost": 123.45,
                    "cpu": 6.7,
                    "adjusted": True,
                    "flows": None,
                    "volumes": None,
                }
            ]
        },
    )()

    candidate = _lpnlpbb_schedule_candidate(args, FakeInstance(), model)

    assert candidate.schedule_availability == "adjusted_only"
    assert candidate.artifact is None


def test_empty_lpnlpbb_solution_list_reports_no_schedule() -> None:
    args = parse_args(["atm-24h-na1", "--execution-mode", "lpnlpbb"])
    model = type("FakeModel", (), {"_solutions": []})()

    candidate = _lpnlpbb_schedule_candidate(args, FakeInstance(), model)

    assert candidate.schedule_availability == "none"
    assert candidate.artifact is None


def test_incomplete_lpnlpbb_solution_is_not_promoted_to_schedule() -> None:
    args = parse_args(["atm-24h-na1", "--execution-mode", "lpnlpbb"])
    incomplete = one_pump_on_plan()
    del incomplete[23]
    model = type(
        "FakeModel",
        (),
        {
            "_solutions": [
                {
                    "plan": incomplete,
                    "cost": 123.45,
                    "cpu": 6.7,
                    "adjusted": False,
                    "flows": {},
                    "volumes": {},
                }
            ]
        },
    )()

    candidate = _lpnlpbb_schedule_candidate(args, FakeInstance(), model)

    assert candidate.schedule_availability == "incomplete"
    assert candidate.artifact is None


def test_run_writes_schedule_artifact_and_manifest_path(tmp_path: Path, monkeypatch) -> None:
    model = DisposableModel()

    def fake_build_model(args):
        return (
            object(),
            FakeInstance(),
            model,
            {"name": "Gurobi", "license_status": "valid"},
            {"variables": 1, "constraints": 1},
        )

    def fake_run_solver(args, gp, instance, model):
        return (
            {
                "run_status": "success",
                "schedule_availability": "complete_commanded_schedule",
                "detail": "unit-test schedule",
            },
            {
                "contract_version": CONTRACT_VERSION,
                "track": TRACK,
                "case_id": args.case_id,
                "na_max": 1,
                "best_y": [0, *([1] * 24)],
                "best_x": [0, 0, 0, *([1, 0, 0] * 24)],
            },
        )

    monkeypatch.setattr(runner, "_build_model", fake_build_model)
    monkeypatch.setattr(runner, "_run_solver", fake_run_solver)
    args = parse_args(
        [
            "atm-24h-na1",
            "--run-class",
            "dev",
            "--run-id",
            "scheduled-run",
            "--execution-mode",
            "lpnlpbb",
            "--output-root",
            str(tmp_path / "output"),
        ]
    )

    exit_code = run(args, ["runner", "atm-24h-na1"])

    run_manifest = tmp_path / "output" / "atm-24h-na1" / "scheduled-run" / "run.json"
    schedule_json = tmp_path / "output" / "atm-24h-na1" / "scheduled-run" / "schedule.json"
    manifest = json.loads(run_manifest.read_text())
    schedule = json.loads(schedule_json.read_text())

    assert exit_code == 0
    assert model.disposed is True
    assert manifest["outputs"]["schedule_json"].endswith("atm-24h-na1/scheduled-run/schedule.json")
    assert schedule["best_y"] == [0, *([1] * 24)]


def test_final_run_audits_exported_schedule_and_records_audit_path(tmp_path: Path, monkeypatch) -> None:
    model = DisposableModel()

    def fake_build_model(args):
        return (
            object(),
            FakeInstance(),
            model,
            {"name": "Gurobi", "license_status": "valid"},
            {"variables": 1, "constraints": 1},
        )

    def fake_run_solver(args, gp, instance, model):
        return (
            {
                "run_status": "success",
                "schedule_availability": "complete_commanded_schedule",
                "detail": "unit-test schedule",
            },
            {
                "contract_version": CONTRACT_VERSION,
                "track": TRACK,
                "case_id": args.case_id,
                "na_max": 1,
                "method": "GOPS LP-NLP branch-and-bound",
                "max_actuations": 1,
                "h_max": 24,
                "inp_file": "networks/any-town.inp",
                "best_y": [0, *([1] * 24)],
                "best_x": [0, 0, 0, *([1, 0, 0] * 24)],
            },
        )

    fake_audit = tmp_path / "fake-audit"
    fake_audit.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            import sys
            from pathlib import Path

            schedule = Path(sys.argv[1])
            output = Path(sys.argv[2])
            payload = json.loads(schedule.read_text())
            output.write_text(json.dumps({
                "schema_version": 1,
                "metadata": {
                    "schedule_file": str(schedule),
                    "method": payload["method"],
                    "actuation_limit": payload["max_actuations"]
                },
                "feasibility": {"feasible": True},
                "effective_cost": 12.3,
                "event_counts": {"tank_clamp_events": 0}
            }))
            """
        )
    )
    os.chmod(fake_audit, 0o755)

    monkeypatch.setattr(runner, "_build_model", fake_build_model)
    monkeypatch.setattr(runner, "_run_solver", fake_run_solver)
    monkeypatch.setattr(runner.platform, "node", lambda: "sol")
    warm_schedule = tmp_path / "warm-start.json"
    warm_schedule.write_text(
        json.dumps(
            {
                "track": "epanet-bb-warm-start-source-v1",
                "case_id": "atm-24h-na1",
                "na_max": 1,
                "h_max": 24,
                "max_actuations": 1,
                "best_x": [0, 0, 0, *([1, 0, 0] * 24)],
            }
        ),
        encoding="utf-8",
    )
    warm_provenance = tmp_path / "warm-start-provenance.json"
    warm_provenance.write_text(
        json.dumps(
            {
                "source_issue": "michaelsouza/epanet-bb#22",
                "run_tag": "labma-sol-20260705T170040Z-default-p64",
                "epanet_bb_commit": "3caddcc",
                "case_id": "atm-24h-na1",
                "na_max": 1,
                "hydraulic_accuracy": 1e-4,
                "feasibility_semantics": "default_epanet_simulated",
                "best_artifact_path": str(warm_schedule),
            }
        ),
        encoding="utf-8",
    )
    args = parse_args(
        [
            "atm-24h-na1",
            "--run-class",
            "final",
            "--host-name",
            "labma-sol",
            "--run-id",
            "audited-run",
            "--execution-mode",
            "lpnlpbb",
            "--time-limit",
            "21600",
            "--warm-start-schedule",
            str(warm_schedule),
            "--warm-start-provenance",
            str(warm_provenance),
            "--output-root",
            str(tmp_path / "output"),
            "--audit-binary",
            str(fake_audit),
        ]
    )

    exit_code = run(args, ["runner", "atm-24h-na1"])

    manifest = json.loads((tmp_path / "output" / "atm-24h-na1" / "audited-run" / "run.json").read_text())
    audit = json.loads((tmp_path / "output" / "atm-24h-na1" / "audited-run" / "audit.json").read_text())

    assert exit_code == 0
    assert manifest["outputs"]["audit_json"].endswith("atm-24h-na1/audited-run/audit.json")
    assert manifest["status"]["audit"]["status"] == "succeeded"
    assert manifest["status"]["audit"]["summary"]["effective_cost"] == 12.3
    assert audit["event_counts"]["tank_clamp_events"] == 0


def test_run_sets_explicit_gurobi_license_file_before_model_build(tmp_path: Path, monkeypatch) -> None:
    model = DisposableModel()
    license_file = tmp_path / "academic-gurobi.lic"
    license_file.write_text("placeholder\n", encoding="utf-8")
    seen = {}

    def fake_build_model(args):
        seen["license_file"] = os.environ.get("GRB_LICENSE_FILE")
        return (
            object(),
            FakeInstance(),
            model,
            {
                "name": "Gurobi",
                "license_status": "valid",
                "license_file": os.environ.get("GRB_LICENSE_FILE"),
            },
            {"variables": 1, "constraints": 1},
        )

    monkeypatch.delenv("GRB_LICENSE_FILE", raising=False)
    monkeypatch.setattr(runner, "_build_model", fake_build_model)
    args = parse_args(
        [
            "atm-24h-na1",
            "--run-class",
            "dev",
            "--run-id",
            "explicit-license-run",
            "--execution-mode",
            "build",
            "--output-root",
            str(tmp_path / "output"),
            "--gurobi-license-file",
            str(license_file),
        ]
    )

    exit_code = run(args, ["runner", "atm-24h-na1"])

    manifest = json.loads((tmp_path / "output" / "atm-24h-na1" / "explicit-license-run" / "run.json").read_text())
    assert exit_code == 0
    assert seen["license_file"] == str(license_file)
    assert manifest["runtime_settings"]["gurobi_license_file"] == str(license_file)
    assert manifest["solver"]["license_file"] == str(license_file)


def test_classify_license_exception() -> None:
    err = RuntimeError("No Gurobi license found")
    status = classify_exception(err)

    assert status["run_status"] == "license_blocked"
    assert status["schedule_availability"] == "none"


def test_classify_size_limited_license_as_restricted() -> None:
    assert (
        classify_license_status(
            "Model too large for size-limited license; visit https://gurobi.com/unrestricted for more information"
        )
        == "restricted"
    )


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
    assert manifest["environment"]["host_name"] == "labma-sol"
    assert manifest["status"]["run_status"] == "environment_blocked"
