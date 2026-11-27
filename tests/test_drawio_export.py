"""Draw.io exports preserve the reviewed graph structure and unknown markers."""

import xml.etree.ElementTree as ET

import pytest

from eqcr.drawio_export import DrawioExportError, architecture_graph_to_drawio
from eqcr.fixture import get_fixture
from eqcr.pipeline import run_pipeline


def test_drawio_export_is_editable_deterministic_and_preserves_graph_references():
    graph = run_pipeline(get_fixture())["quanta"]["architecture_graph"]
    first = architecture_graph_to_drawio(graph)
    second = architecture_graph_to_drawio(graph)
    assert first == second

    root = ET.fromstring(first)
    assert root.tag == "mxfile"
    assert root.find("diagram/mxGraphModel/root") is not None
    cells = root.findall("diagram/mxGraphModel/root/mxCell")
    vertices = [cell for cell in cells if cell.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    assert len(vertices) == len(graph["nodes"])
    assert len(edges) == len(graph["edges"])
    vertex_ids = {cell.get("id") for cell in vertices}
    assert all(cell.get("source") in vertex_ids and cell.get("target") in vertex_ids for cell in edges)
    assert any("INTEGRATION-UNKNOWN" in (cell.get("value") or "") for cell in vertices)
    assert any("[UNKNOWN]" in (cell.get("value") or "") for cell in vertices)
    assert all(
        "dashed=1" in cell.get("style", "")
        for cell in vertices
        if "[UNKNOWN]" in (cell.get("value") or "")
    )


def test_drawio_export_rejects_dangling_graph_edges():
    graph = {
        "nodes": [{"id": "N1", "layer": "ACTOR", "label": "Actor", "status": "PRESENT"}],
        "edges": [{"id": "E1", "from": "N1", "to": "MISSING", "status": "UNKNOWN"}],
    }
    with pytest.raises(DrawioExportError, match="unresolved endpoint"):
        architecture_graph_to_drawio(graph)
