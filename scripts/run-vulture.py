"""Run Vulture."""

import os
import re
import subprocess


def find_python_files(source_path: str, exclude_pattern: str) -> list[str]:
    """
    Find all Python files in the given source path.

    It excludes those that match the exclude pattern.

    Parameters
    ----------
    source_path : str
        The path to search for Python files.
    exclude_pattern : str
        The regex pattern for files to exclude.

    Returns
    -------
    List[str]
        A list of Python file paths that do not match the exclude pattern.
    """
    python_files = []
    exclude_regex = re.compile(exclude_pattern)

    for root, dirs, files in os.walk(source_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if not exclude_regex.search(file_path):
                    python_files.append(file_path)

    return python_files


def run_vulture_on_files(file_paths: list[str]) -> None:
    """
    Run vulture on a list of file paths.

    Parameters
    ----------
    file_paths : List[str]
        List of Python file paths to run vulture on.
    """
    for file_path in file_paths:
        subprocess.run(["vulture", file_path], check=False)


# Example usage
SOURCE_PATH = "."  # Set your source path here
# Set your exclude pattern here
EXCLUDE_PATTERN = "docs/|scripts"

python_files = find_python_files(SOURCE_PATH, EXCLUDE_PATTERN)
run_vulture_on_files(python_files)
