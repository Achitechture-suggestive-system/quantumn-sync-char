"""Small boundary for parsing user-supplied structured project JSON."""

from __future__ import annotations

import json
from typing import Any


def load_project_json(payload: bytes | str) -> dict[str, Any]:
    """Decode a JSON project object and surface invalid input as a user-safe error."""
    try:
        text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    except UnicodeDecodeError as exc:
        raise ValueError(f"Project JSON must be UTF-8: {exc}") from exc

    try:
        project = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid project JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    if not isinstance(project, dict):
        raise ValueError("The JSON document must contain a project object.")
    return project
