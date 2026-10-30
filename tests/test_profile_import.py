"""Encrypted dotenv import and literal export behavior."""

from __future__ import annotations

import os
import stat

from pathlib import Path

import pytest

from dotenv import dotenv_values
from envers.cli import app
from envers.core import Envers
from typer.testing import CliRunner

PASSWORD = "synthetic import password"
LOCK_PATH = Path(".envers/data/base.lock")
SPEC_PATH = Path(".envers/specs.yaml")


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Envers:
    """Deploy two releases so import isolation can be checked."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project.init(Path("."))
    Path(".env").write_text("TOKEN=\nEMPTY=\nKEEP=\n")
    project.draft("1.0", from_env=".env")
    project.deploy("base", "1.0", PASSWORD)
    project.draft("2.0", from_spec="1.0")
    project.deploy("base", "2.0", PASSWORD)
    return project


def test_import_and_export_preserve_literal_values(
    project: Envers, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Import privately, retain unrelated data, and export losslessly."""
    monkeypatch.setenv("ENVERS_INTERPOLATION_TEST", "synthetic-host-value")
    Path("input.env").write_text(
        'TOKEN="synthetic # \\"quoted\\" \\\\path\\nnext\\rline '
        '${ENVERS_INTERPOLATION_TEST} $BARE café"\nEMPTY=\n',
        encoding="utf-8",
    )
    expected = dotenv_values("input.env", interpolate=False)
    before_specs = SPEC_PATH.read_bytes()
    before = project._read_data_file("base", PASSWORD)
    result = CliRunner().invoke(
        app,
        [
            "profile-import",
            "--profile",
            "base",
            "--spec",
            "1.0",
            "--from-env",
            "input.env",
            "--file",
            ".env",
        ],
        input=f"{PASSWORD}\n",
    )

    assert result.exit_code == 0, result.output
    assert SPEC_PATH.read_bytes() == before_specs
    after = project._read_data_file("base", PASSWORD)
    variables = after["releases"]["1.0"]["data"]["base"]["files"][".env"][
        "vars"
    ]
    assert variables == {**expected, "KEEP": ""}
    assert after["releases"]["2.0"] == before["releases"]["2.0"]
    for text in (PASSWORD, "synthetic #", "synthetic-host-value"):
        assert text not in result.output
        assert text not in LOCK_PATH.read_text()

    project.profile_load("base", "1.0", PASSWORD)
    assert dotenv_values(".env", interpolate=False) == variables
    if os.name == "posix":
        assert stat.S_IMODE(Path(".env").stat().st_mode) == 0o600


@pytest.mark.parametrize(
    "content",
    [
        "TOKEN=synthetic-partial-value\nUNKNOWN=synthetic-rejected-value\n",
        "TOKEN=synthetic-partial-value\nEMPTY\n",
        'TOKEN=synthetic-partial-value\nEMPTY="synthetic-unclosed\n',
    ],
)
def test_invalid_import_preserves_saved_files(
    project: Envers, content: str
) -> None:
    """Reject the entire input without saving or printing any values."""
    Path(".env").write_text(content)
    before_lock, before_specs = LOCK_PATH.read_bytes(), SPEC_PATH.read_bytes()

    result = CliRunner().invoke(
        app,
        [
            "profile-import",
            "--profile",
            "base",
            "--spec",
            "1.0",
            "--from-env",
            ".env",
        ],
        input=f"{PASSWORD}\n",
    )

    assert result.exit_code == 1
    assert "synthetic-" not in result.output
    assert LOCK_PATH.read_bytes() == before_lock
    assert SPEC_PATH.read_bytes() == before_specs


def test_import_requires_a_declared_target(project: Envers) -> None:
    """A source file cannot silently add a new file to a deployed schema."""
    Path("other.env").write_text("TOKEN=synthetic-rejected-value\n")
    before = LOCK_PATH.read_bytes()
    result = CliRunner().invoke(
        app,
        [
            "profile-import",
            "--profile",
            "base",
            "--spec",
            "1.0",
            "--from-env",
            "other.env",
        ],
        input=f"{PASSWORD}\n",
    )
    assert result.exit_code == 1
    assert "not declared" in result.output
    assert "synthetic-rejected-value" not in result.output
    assert LOCK_PATH.read_bytes() == before
