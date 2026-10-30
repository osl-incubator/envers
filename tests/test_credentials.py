"""Credential input must be explicit and preserve password whitespace."""

from __future__ import annotations

import io
import sys

from pathlib import Path

import pytest
import typer

from envers import crypt
from envers.cli import app
from envers.core import Envers
from typer.testing import CliRunner


def test_stdin_password_preserves_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remove the line ending without changing the password itself."""
    password = " synthetic password \t "
    monkeypatch.setattr(sys, "stdin", io.StringIO(password + "\r\n"))
    assert crypt.get_password() == password
    encrypted = crypt.encrypt_data("synthetic data", password)
    assert crypt.decrypt_data(encrypted, password) == "synthetic data"


@pytest.mark.parametrize("input", ["", "\n"])
def test_missing_stdin_password_cannot_create_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, input: str
) -> None:
    """Reject EOF and empty credentials before changing saved files."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project.init(Path("."))
    project.draft("1.0")
    spec_path = Path(".envers/specs.yaml")
    before = spec_path.read_bytes()

    result = CliRunner().invoke(
        app, ["deploy", "--profile", "base", "--spec", "1.0"], input=input
    )

    assert result.exit_code != 0
    assert "password" in result.output.lower()
    assert not Path(".envers/data/base.lock").exists()
    assert spec_path.read_bytes() == before


def test_empty_api_password_cannot_replace_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Python callers cannot accidentally create an empty-password store."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project._write_data_file("base", {"TOKEN": "synthetic-old"}, "password")
    lock = Path(".envers/data/base.lock")
    before = lock.read_bytes()
    with pytest.raises(typer.BadParameter, match="Password cannot be empty"):
        project._write_data_file("base", {"TOKEN": "synthetic-new"}, "")
    assert lock.read_bytes() == before
