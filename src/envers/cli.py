"""Definition of the CLI structure."""
from __future__ import annotations

import os

from pathlib import Path

import typer

from typing_extensions import Annotated

from envers.core import Envers


def envers_autocompletion() -> list[str]:
    return ["draft", "init"]


app = typer.Typer()


@app.command()
def init(path: str = "."):
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
    envers = Envers()
    envers.init(Path(path))


@app.command()
def deploy(version: str):
    """
    Deploy a specific version from the spec file.
    """
    envers = Envers()
    envers.deploy(version)


@app.command()
def draft(version: str, from_version: str = "", from_env: str = ""):
    """
    Create a new version draft in the spec file.
    """
    envers = Envers()
    envers.draft(version, from_version, from_env)


@app.command()
def profile_set(profile_name: str, spec_version: str):
    """
    Add new content to a profile.
    """
    # Implementation here
    pass


@app.command()
def profile_update(profile_name: str, spec_version: str):
    """
    Update existing content of a profile.
    """
    # Implementation here
    pass


@app.command()
def profile_load(profile: str, spec: str):
    """
    Load a specific environment profile to files.
    """
    # Implementation here
    pass


@app.command()
def profile_versions(profile_name: str, spec_version: str):
    """
    Return all the versions for the contents for a specific profile and spec version.
    """
    # Implementation here
    pass


if __name__ == "__main__":
    app()
