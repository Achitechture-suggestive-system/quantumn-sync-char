"""Streamlit bridge for the architecture editor and trace view."""

from __future__ import annotations

import math
from pathlib import Path

import streamlit.components.v1 as components

from .quantum_tradeoff import Architecture


_canvas = components.declare_component("quantum_canvas", path=str(Path(__file__).with_name("studio_canvas")))


def read_layout(architecture: Architecture, raw: object) -> dict[str, list[float]]:
    """Keep view coordinates separate from the model and ignore stale node IDs."""
    if not isinstance(raw, dict):
        return {}
    keys = {f"component:{item.id}" for item in architecture.components}
    keys.update(f"store:{item.id}" for item in architecture.stores)
    layout = {}
    for key in keys & raw.keys():
        pair = raw[key]
        if isinstance(pair, list) and len(pair) == 2 and all(
            type(value) in (float, int) and 0 <= value <= 1 and math.isfinite(value) for value in pair
        ):
            layout[key] = list(pair)
    return layout


def render_board(**kwargs):
    return _canvas(key="quantum_canvas", default=None, **kwargs)
