from __future__ import annotations

import subprocess
import sys
import tarfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def test_epanet_bb_source_of_truth_validator() -> None:
    from tools.validate_epanet_bb_source_of_truth import validate

    validate(REPO / "docs" / "epanet-bb-anytown-modified-source-of-truth.json")


def test_epanet_bb_gops_case_translation_validator() -> None:
    from tools.validate_epanet_bb_gops_case import validate

    validate(
        REPO,
        REPO / "docs" / "epanet-bb-source-of-truth-cases.json",
        REPO / "docs" / "epanet-bb-gops-case-translation.json",
    )


def test_epanet_bb_gops_case_constructs_from_clean_archive(tmp_path: Path) -> None:
    tracked_path = "data/EpanetBB_Anytown/Reservoir.csv"
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", tracked_path],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert tracked.returncode == 0, tracked.stderr

    archive = tmp_path / "repo.tar"
    extract_to = tmp_path / "repo"
    extract_to.mkdir()

    subprocess.run(["git", "archive", "HEAD", "-o", str(archive)], cwd=REPO, check=True)
    with tarfile.open(archive) as tar:
        tar.extractall(extract_to, filter="data")

    subprocess.run(
        [
            sys.executable,
            str(extract_to / "tools" / "validate_epanet_bb_gops_case.py"),
            "--repo",
            str(extract_to),
        ],
        check=True,
    )
