"""Project boundaries and export preflight checks."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from dotenv import dotenv_values
from envers.core import Envers

PASSWORD = "synthetic path password"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Envers:
    """Initialize a project without any deployed files."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project.init(Path("."))
    return project


def _store_outputs(project: Envers, names: list[str]) -> None:
    files = {name: {"vars": {"TOKEN": "synthetic-value"}} for name in names}
    project._write_data_file(
        "base",
        {"releases": {"1.0": {"data": {"base": {"files": files}}}}},
        PASSWORD,
    )


@pytest.mark.parametrize("profile", ["../escape", r"prod\other"])
def test_profile_names_cannot_select_paths(
    project: Envers, profile: str
) -> None:
    """Reject path separators before creating or replacing profile files."""
    project._write_data_file("base", {}, PASSWORD)
    with pytest.raises(typer.Exit):
        project._write_data_file(profile, {}, PASSWORD)
    assert set(Path(".envers/data").iterdir()) == {
        Path(".envers/data/base.lock")
    }
    assert not Path(".envers/escape.lock").exists()


@pytest.mark.parametrize(
    "name", ["../escape.env", ".envers/specs.yaml", ".git/config", "absolute"]
)
def test_unsafe_output_preserves_all_files(
    project: Envers, tmp_path: Path, name: str
) -> None:
    """Validate every destination before writing even a valid first file."""
    if name == "absolute":
        name = str(tmp_path / "absolute.env")
    _store_outputs(project, ["valid.env", name])
    Path("valid.env").write_text("synthetic previous output")
    spec = Path(".envers/specs.yaml").read_bytes()
    lock = Path(".envers/data/base.lock").read_bytes()

    with pytest.raises(typer.Exit):
        project.profile_load("base", "1.0", PASSWORD)

    assert Path("valid.env").read_text() == "synthetic previous output"
    assert Path(".envers/specs.yaml").read_bytes() == spec
    assert Path(".envers/data/base.lock").read_bytes() == lock


def test_metadata_symlink_cannot_redirect_spec_updates(
    project: Envers, tmp_path: Path
) -> None:
    """Reject redirected project metadata without changing its destination."""
    redirected = tmp_path / "metadata-copy"
    Path(".envers").rename(redirected)
    try:
        Path(".envers").symlink_to(redirected, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation is not available")
    before = (redirected / "specs.yaml").read_bytes()

    with pytest.raises(typer.Exit):
        project.draft("1.0")

    assert (redirected / "specs.yaml").read_bytes() == before


def test_output_symlink_cannot_redirect_plaintext(
    project: Envers, tmp_path: Path
) -> None:
    """Reject a symlinked output parent before exporting any secrets."""
    outside = tmp_path.parent / f"{tmp_path.name}-external"
    outside.mkdir()
    (outside / "token.env").write_text("synthetic previous output")
    try:
        Path("redirect").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation is not available")
    _store_outputs(project, ["valid.env", "redirect/token.env"])

    with pytest.raises(typer.Exit):
        project.profile_load("base", "1.0", PASSWORD)

    assert not Path("valid.env").exists()
    assert (outside / "token.env").read_text() == "synthetic previous output"


@pytest.mark.parametrize(
    "names",
    [[".env", "./.env"], [".env", ".ENV"], ["config", "config/.env"]],
)
def test_output_collisions_are_rejected_before_writing(
    project: Envers, names: list[str]
) -> None:
    """Reject aliases and file/parent conflicts as one invalid export."""
    _store_outputs(project, ["valid.env", *names])

    with pytest.raises(typer.Exit):
        project.profile_load("base", "1.0", PASSWORD)

    assert not Path("valid.env").exists()


def test_explicit_root_supports_nested_outputs_after_chdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep import, metadata and recreated output directories in one root."""
    root = tmp_path / "project"
    project = Envers(root)
    project.init(Path("."))
    source = root / "config/.env"
    source.parent.mkdir()
    source.write_text("TOKEN=synthetic-value\n")
    project.draft("1.0", from_env="config/.env")
    project.deploy("base", "1.0", PASSWORD)
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    project.profile_import("base", "1.0", "config/.env", password=PASSWORD)
    source.unlink()
    source.parent.rmdir()

    project.profile_load("base", "1.0", PASSWORD)

    assert dotenv_values(source, interpolate=False) == {
        "TOKEN": "synthetic-value"
    }
    assert list(other.iterdir()) == []
