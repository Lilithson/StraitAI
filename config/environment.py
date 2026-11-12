"""Small, dependency-free loader for the project's local environment file."""

import os
from pathlib import Path


def load_environment_file(path: Path) -> None:
    """Load unset environment variables from a simple KEY=VALUE file.

    The real process environment takes precedence so deployment-provided values
    cannot be overridden by a local file.
    """
    if not path.is_file():
        return

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue

        key, separator, value = entry.partition("=")
        key = key.strip()
        if not separator or not key:
            raise ValueError(f"Invalid environment entry on line {line_number}: {line!r}")

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)
