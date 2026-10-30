"""Regressions for encrypted profile saves."""

from __future__ import annotations

import os
import stat

from pathlib import Path
from typing import Any

import pytest
import yaml

from envers import crypt
from envers.core import Envers

PASSWORD = "synthetic storage password"
LOCK_PATH = Path(".envers/data/base.lock")
OLD_DATA = {"token": "synthetic-old-token"}
NEW_DATA = {"token": "synthetic-new-token"}
SPEC_PATH = Path(".envers/specs.yaml")


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Envers:
    """Save an encrypted profile in an isolated project."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project._write_data_file("base", OLD_DATA, PASSWORD)
    return project


def test_encryption_failure_preserves_profile(
    project: Envers, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Encryption must succeed before touching the saved profile."""
    before = LOCK_PATH.read_bytes()

    def fail_encrypt(*args: Any, **kwargs: Any) -> str:
        raise ValueError("synthetic encryption failure")

    monkeypatch.setattr(crypt, "encrypt_data", fail_encrypt)
    with pytest.raises(ValueError, match="synthetic encryption failure"):
        project._write_data_file("base", NEW_DATA, PASSWORD)

    assert LOCK_PATH.read_bytes() == before
    assert project._read_data_file("base", PASSWORD) == OLD_DATA
    assert list(LOCK_PATH.parent.iterdir()) == [LOCK_PATH]


@pytest.mark.parametrize("operation", ["fsync", "replace"])
def test_failed_save_preserves_profile_and_removes_temporary_file(
    project: Envers, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    """Disk errors before replacement must leave the old data readable."""
    before = LOCK_PATH.read_bytes()

    def fail_save(*args: Any, **kwargs: Any) -> None:
        raise OSError("synthetic disk failure")

    monkeypatch.setattr(os, operation, fail_save)
    with pytest.raises(OSError, match="synthetic disk failure"):
        project._write_data_file("base", NEW_DATA, PASSWORD)

    assert LOCK_PATH.read_bytes() == before
    assert project._read_data_file("base", PASSWORD) == OLD_DATA
    assert list(LOCK_PATH.parent.iterdir()) == [LOCK_PATH]


def test_save_replaces_profile_with_private_encrypted_data(
    project: Envers,
) -> None:
    """A completed save must contain new encrypted values and no leftovers."""
    if os.name == "posix":
        LOCK_PATH.chmod(0o644)

    project._write_data_file("base", NEW_DATA, PASSWORD)

    assert project._read_data_file("base", PASSWORD) == NEW_DATA
    assert NEW_DATA["token"] not in LOCK_PATH.read_text()
    assert list(LOCK_PATH.parent.iterdir()) == [LOCK_PATH]
    if os.name == "posix":
        assert stat.S_IMODE(LOCK_PATH.stat().st_mode) == 0o600


@pytest.mark.parametrize("failure", ["serialize", "replace"])
def test_failed_draft_preserves_spec(
    project: Envers, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """Failed schema saves must preserve existing releases and clean up."""
    project.init(Path("."))
    project.draft("1.0")
    before = SPEC_PATH.read_bytes()

    def fail_save(*args: Any, **kwargs: Any) -> None:
        raise OSError("synthetic spec failure")

    if failure == "serialize":
        monkeypatch.setattr(yaml, "dump", fail_save)
    else:
        monkeypatch.setattr(os, "replace", fail_save)

    with pytest.raises(OSError, match="synthetic spec failure"):
        project.draft("2.0")

    assert SPEC_PATH.read_bytes() == before
    assert set(SPEC_PATH.parent.iterdir()) == {SPEC_PATH, LOCK_PATH.parent}


def test_failed_deployment_spec_save_keeps_both_files_readable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A spec replacement error must leave both stored files readable."""
    monkeypatch.chdir(tmp_path)
    project = Envers()
    project.init(Path("."))
    project.draft("1.0")
    before = SPEC_PATH.read_bytes()
    replace = os.replace

    def fail_spec_replace(source: Any, destination: Any) -> None:
        if Path(destination) == SPEC_PATH.resolve():
            raise OSError("synthetic spec failure")
        replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_spec_replace)
    with pytest.raises(OSError, match="synthetic spec failure"):
        project.deploy("base", "1.0", PASSWORD)

    assert SPEC_PATH.read_bytes() == before
    assert "1.0" in project._read_data_file("base", PASSWORD)["releases"]
    assert set(SPEC_PATH.parent.iterdir()) == {SPEC_PATH, LOCK_PATH.parent}
    assert list(LOCK_PATH.parent.iterdir()) == [LOCK_PATH]
