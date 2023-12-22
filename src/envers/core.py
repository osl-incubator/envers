"""Envers class for containers."""
from __future__ import annotations

import copy
import io
import os

from pathlib import Path
from typing import Any

import typer
import yaml  # type: ignore

from cryptography.fernet import InvalidToken
from dotenv import dotenv_values

from envers import crypt


def merge_dicts(
    dict_lhs: dict[str, Any], dict_rhs: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge two dictionaries recursively.

    Parameters
    ----------
    dict_lhs : dict
        The primary dictionary to retain values from.
    dict_rhs : dict
        The secondary dictionary to merge values from.

    Returns
    -------
    dict
        The merged dictionary.
    """
    dict_lhs = copy.deepcopy(dict_lhs)

    for key in dict_rhs:
        if key in dict_lhs:
            if isinstance(dict_lhs[key], dict) and isinstance(
                dict_rhs[key], dict
            ):
                merge_dicts(dict_lhs[key], dict_rhs[key])
            else:
                dict_lhs[key] = dict_rhs[key]
        else:
            dict_lhs[key] = dict_rhs[key]
    return dict_lhs


# constants
ENVERS_SPEC_FILENAME = "specs.yaml"
ENVERS_DATA_FILENAME = "data.lock"


def escape_template_tag(v: str) -> str:
    """Escape template tags for template rendering."""
    return v.replace("{{", r"\{\{").replace("}}", r"\}\}")


def unescape_template_tag(v: str) -> str:
    """Unescape template tags for template rendering."""
    return v.replace(r"\{\{", "{{").replace(r"\}\}", "}}")


class Envers:
    """EnversBase defined the base structure for the Envers classes."""

    def _read_data_file(self, password: str = "") -> dict[str, Any]:
        data_file = Path(".envers") / ENVERS_DATA_FILENAME

        with open(data_file, "r") as file:
            try:
                raw_data = file.read()
                if not raw_data:
                    return {}
                data_content = crypt.decrypt_data(raw_data, password)
                data_lock = yaml.safe_load(io.StringIO(data_content)) or {}
            except InvalidToken:
                typer.echo("The given password is not correct. Try it again.")
                raise typer.Exit()
            except Exception:
                typer.echo(
                    "The data.lock is not valid. Please remove it to proceed."
                )
                raise typer.Exit()

        return data_lock

    def _write_data_file(
        self, data: dict[str, Any], password: str = ""
    ) -> None:
        data_file = Path(".envers") / ENVERS_DATA_FILENAME

        with open(data_file, "w") as file:
            data_content = yaml.dump(data, sort_keys=False)
            file.write(crypt.encrypt_data(data_content, password))

    def init(self, path: Path) -> None:
        """
        Initialize Envers instance.

        Initialize the envers environment at the given path. This includes
        creating a .envers folder and a spec.yaml file within it with default
        content.

        Parameters
        ----------
        path : str, optional
            The directory path where the envers environment will be
            initialized. Defaults to the current directory (".").

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
            file.write("version: '0.1'\nreleases:\n")

    def draft(
        self, version: str, from_spec: str = "", from_env: str = ""
    ) -> None:
        """
        Create a new draft version in the spec file.

        Parameters
        ----------
        version : str
            The version number for the new draft.
        from_spec : str, optional
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
                f"The given version {version} is already defined in the "
                "specs.yaml file."
            )
            return

        if not specs["releases"].get(version, {}):
            specs["releases"][version] = {
                "status": "draft",
                "docs": "",
                "profiles": ["base"],
                "spec": {"files": {}},
            }

        if from_spec:
            if not specs.get("releases", {}).get(from_spec, ""):
                typer.echo(
                    f"Source version {from_spec} not found in specs.yaml."
                )
                raise typer.Exit()

            specs["releases"][version] = merge_dicts(
                specs["releases"][from_spec],
                specs["releases"][version],
            )

        elif from_env:
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
                    }
                    for var, value in env_vars.items()
                },
            }
            spec_files = specs["releases"][version]["spec"]["files"]
            spec_files[from_env] = file_spec

        with open(spec_file, "w") as file:
            yaml.dump(specs, file, sort_keys=False)

    def deploy(self, profile: str, spec: str) -> None:
        """
        Deploy a specific version, updating the .envers/data.lock file.

        Parameters
        ----------
        spec : str
            The version number to be deployed.

        Returns
        -------
        None
        """
        specs_file = Path(".envers") / ENVERS_SPEC_FILENAME
        data_file = Path(".envers") / ENVERS_DATA_FILENAME

        password = crypt.get_password()

        if not specs_file.exists():
            typer.echo("Spec file not found. Please initialize envers first.")
            raise typer.Exit()

        with open(specs_file, "r") as file:
            specs = yaml.safe_load(file) or {}

        if not specs.get("releases", {}).get(spec, ""):
            typer.echo(f"Version {spec} not found in specs.yaml.")
            raise typer.Exit()

        spec_data = copy.deepcopy(specs["releases"][spec])

        # all data in the data.lock file are deployed
        del spec_data["status"]

        if data_file.exists():
            data_lock = self._read_data_file(password)

            if not data_lock:
                typer.echo("data.lock is not valid. Creating a new file.")
                data_lock = {
                    "version": spec_data["version"],
                    "releases": {},
                }
            data_lock["releases"][spec] = {"spec": spec_data, "data": {}}
        else:
            data_lock = {
                "version": specs["version"],
                "releases": {spec: {"spec": spec_data, "data": {}}},
            }

        # Populate data with default values
        for profile_name in spec_data.get("profiles", []):
            profile_data: dict["str", dict[str, Any]] = {"files": {}}
            for file_path, file_info in (
                spec_data.get("spec", {}).get("files", {}).items()
            ):
                file_data = {
                    "type": file_info.get("type", "dotenv"),
                    "vars": {},
                }
                for var_name, var_info in file_info.get("vars", {}).items():
                    default_value = var_info.get("default", "")
                    file_data["vars"][var_name] = default_value
                profile_data["files"][file_path] = file_data
            data_lock["releases"][spec]["data"][profile_name] = profile_data

        self._write_data_file(data_lock, password)

        with open(specs_file, "w") as file:
            specs["releases"][spec]["status"] = "deployed"
            yaml.dump(specs, file, sort_keys=False)

    def profile_set(self, profile: str, spec: str) -> None:
        """
        Set the profile values for a given spec version.

        Parameters
        ----------
        profile : str
            The name of the profile to set values for.
        spec : str
            The version of the spec to use.

        Returns
        -------
        None
        """
        data_file = Path(".envers") / ENVERS_DATA_FILENAME

        if not data_file.exists():
            typer.echo(
                "Data lock file not found. Please deploy a version first."
            )
            raise typer.Exit()

        password = crypt.get_password()

        data_lock = self._read_data_file(password)

        if not data_lock.get("releases", {}).get(spec, ""):
            typer.echo(f"Version {spec} not found in data.lock.")
            raise typer.Exit()

        release_data = data_lock["releases"][spec]
        profile_data = release_data.get("data", {}).get(profile, {})

        if not (profile_data and profile_data.get("files", {})):
            typer.echo(
                f"There is no data spec for version '{spec}' "
                f"and profile '{profile}'"
            )
            raise typer.Exit()

        # Iterate over files and variables
        size = os.get_terminal_size()

        profile_title = f" Profile: {profile} ".center(size.columns, "=")
        typer.echo(f"\n{profile_title}\n")

        for file_path, file_info in profile_data.get("files", {}).items():
            file_title = f">>> File: {file_path} "
            typer.echo(f"{file_title}\n")
            for var_name, var_info in file_info.get("vars", {}).items():
                current_value = var_info
                new_value = typer.prompt(
                    f"Enter value for `{var_name}`",
                    default=current_value,
                )
                profile_data["files"][file_path]["vars"][var_name] = new_value

            # update the size for each iteration
            size = os.get_terminal_size()
            typer.echo(f"\n{size.columns * '-'}\n")

        # Update data.lock file
        data_lock["releases"][spec]["data"][profile] = profile_data
        self._write_data_file(data_lock, password)

    def profile_load(self, profile: str, spec: str) -> None:
        """
        Load a specific environment profile to files.

        Load a specific environment profile to files based on the given
        spec version.

        Parameters
        ----------
        profile : str
            The name of the profile to load.
        spec : str
            The version of the spec to use.

        Returns
        -------
        None
        """
        data_lock_file = Path(".envers") / "data.lock"

        if not data_lock_file.exists():
            typer.echo(
                "Data lock file not found. Please deploy a version first."
            )
            raise typer.Exit()

        password = crypt.get_password()

        data_lock = self._read_data_file(password)

        if not data_lock.get("releases", {}).get(spec, ""):
            typer.echo(f"Version {spec} not found in data.lock.")
            raise typer.Exit()

        release_data = data_lock["releases"][spec]
        profile_data = release_data.get("data", {}).get(profile, {"files": {}})

        # Iterate over files and variables
        for file_path, file_info in profile_data.get("files", {}).items():
            file_content = ""
            for var_name, var_value in file_info.get("vars", {}).items():
                file_content += f"{var_name}={var_value}\n"

            # Create or update the file
            with open(file_path, "w") as file:
                file.write(file_content)

        typer.echo(
            f"Environment files for profile '{profile}' and spec version "
            f"'{spec}' have been created/updated."
        )
