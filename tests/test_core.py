"""Tests for envers package."""
import copy
import os
import tempfile

from pathlib import Path

import pytest
import yaml

from envers.core import Envers


@pytest.fixture
def spec_v1():
    """Return dummy data for spec v1."""
    return {
        "status": "draft",
        "docs": "",
        "profiles": ["base"],
        "spec": {
            "files": {
                ".env": {
                    "type": "dotenv",
                    "vars": {
                        "var": {
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

    def setup(self):
        """Create a temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)

    def teardown(self):
        """Clean up temporary data."""
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_temp_dir(self):
        """Test the temp_dir created by the setup."""
        assert self.temp_dir.name == str(Path(".").absolute())

    def test_draft(self):
        """Test draft method."""
        envers = Envers()
        envers.init(Path("."))
        spec_version = "1.0"
        envers.draft(spec_version)

        expected_data = {
            "version": "0.1",
            "releases": {
                spec_version: {
                    "status": "draft",
                    "docs": "",
                    "profiles": ["base"],
                    "spec": {"files": {}},
                }
            },
        }

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

    def test_draft_from_spec(self, spec_v1):
        """Test draft method with from_spec."""
        envers = Envers()
        envers.init(Path("."))

        v1 = "1.0"
        v2 = "2.0"

        initial_specs = {"version": "0.1", "releases": {v1: spec_v1}}

        with open(".envers/specs.yaml", "w") as f:
            yaml.safe_dump(initial_specs, f)

        envers.draft(v2, from_spec=v1)

        expected_data = copy.deepcopy(initial_specs)
        expected_data["releases"][v2] = copy.deepcopy(spec_v1)

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

    def test_draft_from_env(self, spec_v1):
        """Test draft method with from_env."""
        envers = Envers()
        envers.init(Path("."))

        v1 = "1.0"

        with open(".env", "w") as f:
            f.write("var=hello")

        envers.draft(v1, from_env=".env")

        expected_data = {"version": "0.1", "releases": {v1: spec_v1}}

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

    def test_draft_from_multi_env(self, spec_v1):
        """Test draft method with multiple from_env."""
        envers = Envers()
        envers.init(Path("."))

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

        envers.draft(v1, from_env=env_path_0)

        expected_data = {"version": "0.1", "releases": {v1: spec_v1}}

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        assert expected_data == result_data

        # test with .env, and folder1/.env

        envers.draft(v1, from_env=env_path_1)

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        spec_files = expected_data["releases"][v1]["spec"]["files"]
        spec_files[env_path_1] = {
            "type": "dotenv",
            "vars": {
                "var1": {
                    "type": "string",
                    "default": "hello1",
                }
            },
        }

        assert expected_data == result_data

        # test with .env, and folder1/.env, and folder2/.env

        envers.draft(v1, from_env=env_path_2)

        with open(".envers/specs.yaml", "r") as f:
            result_data = yaml.safe_load(f)

        spec_files = expected_data["releases"][v1]["spec"]["files"]
        spec_files[env_path_2] = {
            "type": "dotenv",
            "vars": {
                "var2": {
                    "type": "string",
                    "default": "hello2",
                }
            },
        }

        assert expected_data == result_data
