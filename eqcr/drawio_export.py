"""Deterministic editable Draw.io export for the architecture graph artifact."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Any


class DrawioExportError(ValueError):
    """Raised when an architecture graph cannot be represented safely."""


LAYER_ORDER = [
    "ACTOR",
    "PRESENTATION_APPLICATION",
    "QUANTUM",
    "INTEGRATION",
    "INFRASTRUCTURE_STORAGE",
]
LAYER_Y = {layer: 50 + index * 130 for index, layer in enumerate(LAYER_ORDER)}


def _cell_id(kind: str, logical_id: str) -> str:
    digest = hashlib.sha256(f"{kind}:{logical_id}".encode("utf-8")).hexdigest()[:20]
    return f"eqcr_{kind}_{digest}"


def architecture_graph_to_drawio(graph: dict[str, Any]) -> str:
    """Serialize nodes and edges to a stable mxfile document without adding decisions."""
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise DrawioExportError("Architecture graph must contain node and edge lists.")

    node_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not all(isinstance(node.get(field), str) for field in ("id", "layer", "label")):
            raise DrawioExportError("Every graph node requires string id, layer, and label fields.")
        if node["id"] in node_by_id:
            raise DrawioExportError(f"Duplicate architecture graph node ID: {node['id']}.")
        node_by_id[node["id"]] = node

    edge_by_id: dict[str, dict[str, Any]] = {}
    for edge in edges:
        if not isinstance(edge, dict) or not all(isinstance(edge.get(field), str) for field in ("id", "from", "to")):
            raise DrawioExportError("Every graph edge requires string id, from, and to fields.")
        if edge["id"] in edge_by_id:
            raise DrawioExportError(f"Duplicate architecture graph edge ID: {edge['id']}.")
        if edge["from"] not in node_by_id or edge["to"] not in node_by_id:
            raise DrawioExportError(f"Graph edge {edge['id']} has an unresolved endpoint.")
        edge_by_id[edge["id"]] = edge

    root = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device"})
    diagram = ET.SubElement(root, "diagram", {"id": "eqcr-architecture", "name": "EQCR Architecture"})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1169",
            "dy": "827",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1169",
            "pageHeight": "827",
            "math": "0",
            "shadow": "0",
        },
    )
    cell_root = ET.SubElement(model, "root")
    ET.SubElement(cell_root, "mxCell", {"id": "0"})
    ET.SubElement(cell_root, "mxCell", {"id": "1", "parent": "0"})

    grouped_nodes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in node_by_id.values():
        grouped_nodes[node["layer"]].append(node)
    ordered_layers = [*LAYER_ORDER, *sorted(set(grouped_nodes) - set(LAYER_ORDER))]
    graph_cell_ids: dict[str, str] = {}
    for layer_index, layer in enumerate(ordered_layers):
        layer_nodes = sorted(grouped_nodes.get(layer, []), key=lambda item: item["id"])
        y = LAYER_Y.get(layer, 50 + layer_index * 130)
        for index, node in enumerate(layer_nodes):
            cell_id = _cell_id("node", node["id"])
            graph_cell_ids[node["id"]] = cell_id
            status = node.get("status", "UNKNOWN")
            style = "ellipse" if layer == "ACTOR" else "rounded=1"
            style += ";whiteSpace=wrap;html=1;align=center;verticalAlign=middle;"
            style += "dashed=1;dashPattern=6 4;" if status in {"UNKNOWN", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"} else ""
            value = f"{node['id']}: {node['label']} [{status}]"
            cell = ET.SubElement(
                cell_root,
                "mxCell",
                {"id": cell_id, "value": value, "style": style, "vertex": "1", "parent": "1"},
            )
            ET.SubElement(
                cell,
                "mxGeometry",
                {
                    "x": str(120 + index * 210),
                    "y": str(y),
                    "width": "180",
                    "height": "70",
                    "as": "geometry",
                },
            )

    for edge_id in sorted(edge_by_id):
        edge = edge_by_id[edge_id]
        status = edge.get("status", "UNKNOWN")
        style = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        if status in {"UNKNOWN", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"}:
            style += "dashed=1;dashPattern=6 4;"
        cell = ET.SubElement(
            cell_root,
            "mxCell",
            {
                "id": _cell_id("edge", edge_id),
                "value": f"{edge_id}: {edge.get('label', 'UNKNOWN')} [{status}]",
                "style": style,
                "edge": "1",
                "parent": "1",
                "source": graph_cell_ids[edge["from"]],
                "target": graph_cell_ids[edge["to"]],
            },
        )
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

    return ET.tostring(root, encoding="unicode", xml_declaration=True)
