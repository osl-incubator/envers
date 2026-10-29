"""Regressions for private, cancellable profile editing."""

from __future__ import annotations

from pathlib import Path

import pytest

from envers.cli import app
from envers.core import Envers
from typer.testing import CliRunner

PASSWORD = "synthetic profile password"
LOCK_PATH = Path(".envers/data/base.lock")


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Envers:
    """Store synthetic profile values without requiring a terminal."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project._write_data_file(
        "base",
        {
            "releases": {
                "1.0": {
                    "data": {
                        "base": {
                            "files": {
                                ".env": {
                                    "vars": {
                                        "TOKEN": "synthetic-old-token",
                                        "RETRIES": 3,
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        PASSWORD,
    )
    return project


def test_profile_set_hides_values_and_keeps_unchanged_values(
    project: Envers,
) -> None:
    """Update a value privately and retain the type of an unchanged value."""
    result = CliRunner().invoke(
        app,
        ["profile-set", "--profile", "base", "--spec", "1.0"],
        input=f"{PASSWORD}\nsynthetic-new-token\n\n",
    )

    assert result.exit_code == 0, result.output
    for value in (PASSWORD, "synthetic-old-token", "synthetic-new-token"):
        assert value not in result.output
        assert value not in LOCK_PATH.read_text()
    assert "[3]" not in result.output
    assert "TOKEN" in result.output
    assert "RETRIES" in result.output
    data = project._read_data_file("base", PASSWORD)
    variables = data["releases"]["1.0"]["data"]["base"]["files"][".env"][
        "vars"
    ]
    assert variables == {"TOKEN": "synthetic-new-token", "RETRIES": 3}


def test_profile_set_cancel_preserves_encrypted_file(project: Envers) -> None:
    """Aborting after entering one value must discard the whole edit."""
    before = LOCK_PATH.read_bytes()

    result = CliRunner().invoke(
        app,
        ["profile-set", "--profile", "base", "--spec", "1.0"],
        input=f"{PASSWORD}\nsynthetic-discarded-token\n",
    )

    assert result.exit_code == 1
    assert "Aborted" in result.output
    assert "synthetic-old-token" not in result.output
    assert "synthetic-discarded-token" not in result.output
    assert LOCK_PATH.read_bytes() == before
