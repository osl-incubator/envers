"""Definition of the CLI structure."""
from __future__ import annotations

from pathlib import Path

import typer

from typing_extensions import Annotated

from envers.core import Envers

app = typer.Typer()


@app.command()
def init(path: str = ".") -> None:
    """
    Initialize the .envers directory and specs file.

    Initialize the envers environment at the given path. This includes creating
    a .envers folder and a spec.yaml file within it with default content.

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
def deploy(version: str) -> None:
    """Deploy a specific version from the spec file."""
    envers = Envers()
    envers.deploy(version)


@app.command()
def draft(version: str, from_version: str = "", from_env: str = "") -> None:
    """Create a new version draft in the spec file."""
    envers = Envers()
    envers.draft(version, from_version, from_env)


@app.command()
def profile_set(
    profile: Annotated[
        str, typer.Option(help="The name of the profile to set values for.")
    ] = "",
    spec: Annotated[
        str, typer.Option(help="The version of the spec to use.")
    ] = "",
) -> None:
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
    envers = Envers()
    envers.profile_set(profile, spec)


@app.command()
def profile_load(
    profile: Annotated[
        str, typer.Option(help="The name of the profile to set values for.")
    ] = "",
    spec: Annotated[
        str, typer.Option(help="The version of the spec to use.")
    ] = "",
) -> None:
    """Load a specific environment profile to files."""
    envers = Envers()
    envers.profile_load(profile, spec)


@app.command()
def profile_versions(profile_name: str, spec_version: str) -> None:
    """
    Return the profile's version.

    Return all the versions for the contents for a specific profile and spec
    version.
    """
    print(profile_name, spec_version)


if __name__ == "__main__":
    app()
