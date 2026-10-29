"""Regressions for accidental changes to deployed configuration releases."""

from __future__ import annotations

import copy

from pathlib import Path

import pytest
import typer
import yaml

from envers.cli import app
from envers.core import Envers
from typer.testing import CliRunner

PASSWORD = "synthetic test password"
SPEC_PATH = Path(".envers/specs.yaml")
LOCK_PATH = Path(".envers/data/base.lock")


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Envers:
    """Create a release with two declared profiles and example values."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project.init(Path("."))
    Path(".env").write_text("ENV=dev\nSHARED=example\n")
    project.draft("1.0", from_env=".env")
    specs = yaml.safe_load(SPEC_PATH.read_text())
    specs["releases"]["1.0"]["profiles"] = ["base", "prod"]
    variables = specs["releases"]["1.0"]["spec"]["files"][".env"]["vars"]
    variables["ENV"]["default"] = "dev"
    variables["SHARED"]["default"] = "example"
    SPEC_PATH.write_text(yaml.safe_dump(specs))
    return project


def test_redeploy_preserves_saved_values(project: Envers) -> None:
    """Repeated CLI deployment must preserve configured values."""
    project.deploy("base", "1.0", PASSWORD)
    data = project._read_data_file("base", PASSWORD)
    data["releases"]["1.0"]["data"]["base"]["files"][".env"]["vars"]["ENV"] = (
        "custom value"
    )
    project._write_data_file("base", data, PASSWORD)
    before_lock, before_specs = LOCK_PATH.read_bytes(), SPEC_PATH.read_bytes()

    result = CliRunner().invoke(
        app,
        ["deploy", "--profile", "base", "--spec", "1.0"],
        input=f"{PASSWORD}\n",
    )

    assert result.exit_code == 1
    assert "already deployed" in result.output
    assert "new version" in result.output
    assert LOCK_PATH.read_bytes() == before_lock
    assert SPEC_PATH.read_bytes() == before_specs
    project.profile_load("base", "1.0", PASSWORD)
    assert "ENV=custom value\n" in Path(".env").read_text()


def test_draft_cannot_modify_deployed_release(project: Envers) -> None:
    """Importing into a deployed schema must preserve both stored files."""
    project.deploy("base", "1.0", PASSWORD)
    Path("extra.env").write_text("NEW_VAR=example\n")
    before_lock, before_specs = LOCK_PATH.read_bytes(), SPEC_PATH.read_bytes()

    with pytest.raises(typer.Exit):
        project.draft("1.0", from_env="extra.env")

    assert SPEC_PATH.read_bytes() == before_specs
    assert LOCK_PATH.read_bytes() == before_lock


def test_draft_from_deployed_spec_preserves_overrides(project: Envers) -> None:
    """Copy a schema into an editable draft and retain nested overrides."""
    project.deploy("base", "1.0", PASSWORD)
    source = yaml.safe_load(SPEC_PATH.read_text())["releases"]["1.0"]
    Path(".env").write_text("ENV=override\nEXTRA=example\n")
    project.draft("2.0", from_env=".env")
    specs = yaml.safe_load(SPEC_PATH.read_text())
    variables = specs["releases"]["2.0"]["spec"]["files"][".env"]["vars"]
    variables["ENV"]["default"] = "override"
    SPEC_PATH.write_text(yaml.safe_dump(specs))
    project.draft("2.0", from_spec="1.0")

    releases = yaml.safe_load(SPEC_PATH.read_text())["releases"]
    variables = releases["2.0"]["spec"]["files"][".env"]["vars"]
    assert releases["2.0"]["status"] == "draft"
    assert variables["ENV"]["default"] == "override"
    assert variables["SHARED"]["default"] == "example"
    assert "EXTRA" in variables
    assert releases["1.0"] == source


@pytest.mark.parametrize(
    ("profile", "status"), [("unknown", "draft"), ("base", "cancelled")]
)
def test_deploy_rejects_invalid_selection(
    project: Envers, profile: str, status: str
) -> None:
    """Reject undeclared profiles and unavailable releases before writes."""
    specs = yaml.safe_load(SPEC_PATH.read_text())
    specs["releases"]["1.0"]["status"] = status
    SPEC_PATH.write_text(yaml.safe_dump(specs))
    before = SPEC_PATH.read_bytes()

    with pytest.raises(typer.Exit):
        project.deploy(profile, "1.0", PASSWORD)

    assert not Path(".envers/data").exists()
    assert SPEC_PATH.read_bytes() == before


def test_empty_lock_is_not_reinitialized(project: Envers) -> None:
    """An existing empty lock must fail without changing either file."""
    LOCK_PATH.parent.mkdir()
    LOCK_PATH.write_text("")
    before = SPEC_PATH.read_bytes()

    with pytest.raises(typer.Exit):
        project.deploy("base", "1.0", PASSWORD)

    assert LOCK_PATH.read_bytes() == b""
    assert SPEC_PATH.read_bytes() == before


def test_new_deployments_preserve_existing_releases(project: Envers) -> None:
    """Allow another profile and a new release without losing saved data."""
    project.deploy("base", "1.0", PASSWORD)
    original = copy.deepcopy(project._read_data_file("base", PASSWORD))
    before = LOCK_PATH.read_bytes()
    project.deploy("prod", "1.0", "separate synthetic password")
    assert LOCK_PATH.read_bytes() == before

    project.draft("2.0", from_spec="1.0")
    draft = yaml.safe_load(SPEC_PATH.read_text())["releases"]["2.0"]
    assert draft["status"] == "draft"
    assert draft["profiles"] == ["base", "prod"]
    project.deploy("base", "2.0", PASSWORD)
    data = project._read_data_file("base", PASSWORD)
    assert set(data["releases"]) == {"1.0", "2.0"}
    assert data["releases"]["1.0"] == original["releases"]["1.0"]
    assert "status" not in data["releases"]["2.0"]["spec"]
