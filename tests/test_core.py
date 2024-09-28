"""Tests for envers package."""

from __future__ import annotations

import copy
import os
import tempfile

from pathlib import Path
from typing import Any

import pytest
import yaml

from envers.core import Envers


def rmdir(directory: Path) -> None:
    """Remove directory recursively."""
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()


@pytest.fixture
def spec_v1() -> dict[str, Any]:
    """Return dummy data for spec v1."""
    return {
        "docs": "",
        "status": "draft",
        "profiles": ["base"],
        "spec": {
            "files": {
                ".env": {
                    "docs": "",
                    "type": "dotenv",
                    "vars": {
                        "var": {
                            "docs": "",
                            "type": "string",
                            "default": "hello",
                        }
                    },
                }
            }
        },
    }


class TestEnvers:
    """Tests for Envers class."""

    temp_dir: tempfile.TemporaryDirectory
    original_cwd: str
    envers: Envers

    def setup_method(self) -> None:
        """Create a temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)

        self.envers = Envers()
        self.envers.init(Path("."))

    def teardown_method(self) -> None:
        """Clean up temporary data."""
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_temp_dir(self) -> None:
        """Test the temp_dir created by the setup."""
        tmp_dir = self.temp_dir.name
        cwd = str(Path(".").absolute())

        cwd_undesired_prefix = "/private"

        if cwd.startswith(cwd_undesired_prefix):
            cwd = cwd[len(cwd_undesired_prefix) :]
        assert tmp_dir == cwd

    def test_draft(self) -> None:
        """Test draft method."""
        spec_version = "1.0"
        self.envers.draft(spec_version)

        expected_data = {
            "version": "0.1",
            "releases": {
                spec_version: {
                    "docs": "",
                    "status": "draft",
                    "profiles": ["base"],
                    "spec": {"files": {}},
                }
            },
        }

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

    def test_draft_from_spec(self, spec_v1) -> None:
        """Test draft method with from_spec."""
        v1 = "1.0"
        v2 = "2.0"

        initial_specs = {"version": "0.1", "releases": {v1: spec_v1}}

        with open(".envers/specs.yaml", "w") as f:
            yaml.safe_dump(initial_specs, f)

        self.envers.draft(v2, from_spec=v1)

        expected_data = copy.deepcopy(initial_specs)
        expected_data["releases"][v2] = copy.deepcopy(spec_v1)

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

    def test_draft_from_env(self, spec_v1) -> None:
        """Test draft method with from_env."""
        v1 = "1.0"

        with open(".env", "w") as f:
            f.write("var=hello")

        self.envers.draft(v1, from_env=".env")

        expected_data = {"version": "0.1", "releases": {v1: spec_v1}}

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

    def test_draft_from_multi_env(self, spec_v1) -> None:
        """Test draft method with multiple from_env."""
        v1 = "1.0"

        env_path_0 = ".env"
        env_path_1 = "folder1/.env"
        env_path_2 = "folder2/.env"

        os.makedirs("folder1", exist_ok=True)
        os.makedirs("folder2", exist_ok=True)

        with open(env_path_0, "w") as f:
            f.write("var=hello")

        with open(env_path_1, "w") as f:
            f.write("var1=hello1")

        with open(env_path_2, "w") as f:
            f.write("var2=hello2")

        # test with .env

        self.envers.draft(v1, from_env=env_path_0)

        expected_data = {"version": "0.1", "releases": {v1: spec_v1}}

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

        # test with .env, and folder1/.env

        self.envers.draft(v1, from_env=env_path_1)

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        spec_files = expected_data["releases"][v1]["spec"]["files"]
        spec_files[env_path_1] = {
            "docs": "",
            "type": "dotenv",
            "vars": {
                "var1": {
                    "docs": "",
                    "type": "string",
                    "default": "hello1",
                }
            },
        }

        assert expected_data == result_data

        # test with .env, and folder1/.env, and folder2/.env

        self.envers.draft(v1, from_env=env_path_2)

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        spec_files = expected_data["releases"][v1]["spec"]["files"]
        spec_files[env_path_2] = {
            "docs": "",
            "type": "dotenv",
            "vars": {
                "var2": {
                    "docs": "",
                    "type": "string",
                    "default": "hello2",
                }
            },
        }

        assert expected_data == result_data

        rmdir(Path("folder1"))
        rmdir(Path("folder2"))

    def test_deploy(self) -> None:
        """Test draft method."""
        spec_version = "1.0"
        password = "Envers everywhere!"
        profile = "base"

        self.envers.draft(spec_version)
        self.envers.deploy(
            profile=profile, spec=spec_version, password=password
        )

        data_dir = Path(self.temp_dir.name) / ".envers" / "data"

        assert data_dir.exists()
        assert (data_dir / f"{profile}.lock").exists()

    def test_profile_load(self, spec_v1) -> None:
        """Test draft method."""
        spec_version = "1.0"
        password = "Envers everywhere!"
        profile = "base"

        initial_specs = {"version": "0.1", "releases": {spec_version: spec_v1}}

        with open(".envers/specs.yaml", "w") as f:
            yaml.safe_dump(initial_specs, f)

        self.envers.deploy(
            profile=profile, spec=spec_version, password=password
        )
        self.envers.profile_load(
            profile=profile, spec=spec_version, password=password
        )

        dotenv_path = Path(self.temp_dir.name) / ".env"
        assert dotenv_path.exists()

        with open(dotenv_path, "r") as f:
            dotenv_content = f.read()

        assert dotenv_content == "var=hello\n"
