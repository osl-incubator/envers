"""Check a built wheel in a fresh environment outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import venv

from pathlib import Path


def main() -> None:
    """Install runtime dependencies and exercise the distributed CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dist", type=Path, help="Directory containing one wheel"
    )
    args = parser.parse_args()
    wheels = list(args.dist.glob("*.whl"))
    if len(wheels) != 1:
        parser.error(
            "Expected exactly one wheel in the distribution directory"
        )
    wheel = wheels[0].resolve()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    with tempfile.TemporaryDirectory(prefix="envers-install-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        windows = os.name == "nt"
        bin_dir = environment / ("Scripts" if windows else "bin")
        python = bin_dir / ("python.exe" if windows else "python")
        cli = bin_dir / ("envers.exe" if windows else "envers")
        work = root / "project"
        work.mkdir()

        def run(*command: str | Path, input: str = "") -> str:
            result = subprocess.run(
                command,
                input=input,
                text=True,
                capture_output=True,
                cwd=work,
                env=env,
            )
            if result.returncode:
                print(result.stdout, end="")
                print(result.stderr, end="", file=sys.stderr)
                result.check_returncode()
            return result.stdout.strip()

        run(
            python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            wheel,
        )
        run(python, "-m", "pip", "check")
        version = run(
            python,
            "-I",
            "-c",
            "import sys, envers; from pathlib import Path; "
            "from importlib.metadata import version; "
            "assert Path(envers.__file__).is_relative_to(sys.prefix); "
            "print(version('envers'))",
        )
        assert run(cli, "--version") == f"Version: {version}"
        assert (
            run(python, "-m", "envers", "--version") == f"Version: {version}"
        )

        password = "synthetic install password"
        (work / ".env").write_text("TOKEN=synthetic-${REFERENCE}\n")
        run(cli, "init")
        run(cli, "draft", "1.0", "--from-env", ".env")
        run(
            cli,
            "deploy",
            "--profile",
            "base",
            "--spec",
            "1.0",
            input=f"{password}\n{password}\n",
        )
        run(
            cli,
            "profile-import",
            "--profile",
            "base",
            "--spec",
            "1.0",
            "--from-env",
            ".env",
            input=f"{password}\n",
        )
        run(
            cli,
            "profile-load",
            "--profile",
            "base",
            "--spec",
            "1.0",
            input=f"{password}\n",
        )
        expected = 'TOKEN="synthetic-${REFERENCE}"\n'
        assert (work / ".env").read_text() == expected
        print(f"Installed Envers {version}: version and encrypted workflow OK")


if __name__ == "__main__":
    main()
