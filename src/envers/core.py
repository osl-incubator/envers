"""Envers class for containers."""
from __future__ import annotations
import copy
import io
import os
import sys

from pathlib import Path

import sh
import typer
import yaml  # type: ignore

from dotenv import dotenv_values
from jinja2 import Template

from envers import __version__
from envers.logs import EnversErrorType, EnversLogs

# constants
ENVERS_SPEC_FILENAME = "specs.yaml"


def escape_template_tag(v: str) -> str:
    """Escape template tags for template rendering."""
    return v.replace("{{", r"\{\{").replace("}}", r"\}\}")


def unescape_template_tag(v: str) -> str:
    """Unescape template tags for template rendering."""
    return v.replace(r"\{\{", "{{").replace(r"\}\}", "}}")


class Envers:
    """EnversBase defined the base structure for the Envers classes."""

    def init(self, path: Path) -> None:
        """
        Initialize the envers environment at the given path. This includes creating a .envers folder
        and a spec.yaml file within it with default content.

        Parameters
        ----------
        path : str, optional
            The directory path where the envers environment will be initialized.
            Defaults to the current directory (".").

        Returns
        -------
        None
        """
        envers_path = path / ".envers"
        spec_file = envers_path / ENVERS_SPEC_FILENAME

        # Create .envers directory if it doesn't exist
        os.makedirs(envers_path, exist_ok=True)

        if spec_file.exists():
            return

        # Create and write the default content to spec.yaml
        with open(spec_file, "w") as file:
            file.write("version: 0.1\nrelease:\n")

    def draft(
        self, version: str, from_version: str = "", from_env: str = ""
    ) -> None:
        """
        Create a new draft version in the spec file.

        Parameters
        ----------
        version : str
            The version number for the new draft.
        from_version : str, optional
            The version number from which to copy the spec.
        from_env : str, optional
            The .env file from which to load environment variables.

        Returns
        -------
        None
        """
        spec_file = Path(".envers") / ENVERS_SPEC_FILENAME

        if not spec_file.exists():
            typer.echo("Spec file not found. Please initialize envers first.")
            raise typer.Exit()

        with open(spec_file, "r") as file:
            specs = yaml.safe_load(file) or {}

        if not specs.get("releases", {}):
            specs["releases"] = {}

        if specs.get("releases", {}).get("version", ""):
            typer.echo(
                f"The given version {version} is already defined in the specs.yaml file."
            )
            return

        if from_version:
            if not specs.get("releases", {}).get(from_version, ""):
                typer.echo(
                    f"Source version {from_version} not found in specs.yaml."
                )
                raise typer.Exit()
            specs["releases"][version] = copy.deepcopy(
                specs["releases"][from_version]
            )

        else:
            specs["releases"][version] = {
                "status": "draft",
                "help": "",
                "profiles": ["base"],
                "spec": {"files": {}},
            }

            if from_env:
                env_path = Path(from_env)
                if not env_path.exists():
                    typer.echo(f".env file {from_env} not found.")
                    raise typer.Exit()

                # Read .env file and populate variables
                env_vars = dotenv_values(env_path)
                file_spec = {
                    "type": "dotenv",
                    "vars": {
                        var: {
                            "type": "string",
                            "default": value,
                            "encrypted": False,
                        }
                        for var, value in env_vars.items()
                    },
                }
                specs["releases"][version]["spec"]["files"][
                    env_path.name
                ] = file_spec

        with open(spec_file, "w") as file:
            yaml.dump(specs, file, sort_keys=False)

    def deploy(self, version: str):
        """
        Deploy a specific version, updating the .envers/data.lock file.

        Parameters
        ----------
        version : str
            The version number to be deployed.

        Returns
        -------
        None
        """
        specs_file = Path(".envers") / ENVERS_SPEC_FILENAME
        data_lock_file = Path(".envers") / "data.lock"

        if not specs_file.exists():
            typer.echo("Spec file not found. Please initialize envers first.")
            raise typer.Exit()

        with open(specs_file, "r") as file:
            specs = yaml.safe_load(file) or {}

        if not specs.get("releases", {}).get(version, ""):
            typer.echo(f"Version {version} not found in specs.yaml.")
            raise typer.Exit()

        spec = specs["releases"][version]

        data_lock = {
            "version": specs["version"],
            "releases": {version: {"spec": spec, "data": {}}},
        }

        # Populate data with default values
        for profile_name in spec.get("profiles", []):
            profile_data = {"files": {}}
            for file_path, file_info in (
                spec.get("spec", {}).get("files", {}).items()
            ):
                file_data = {
                    "type": file_info.get("type", "dotenv"),
                    "vars": {},
                }
                for var_name, var_info in file_info.get("vars", {}).items():
                    default_value = var_info.get("default", "")
                    file_data["vars"][var_name] = default_value
                profile_data["files"][file_path] = file_data
            data_lock["releases"][version]["data"][profile_name] = profile_data

        with open(data_lock_file, "w") as file:
            yaml.dump(data_lock, file, sort_keys=False)
