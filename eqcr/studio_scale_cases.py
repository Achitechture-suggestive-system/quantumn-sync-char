"""Prepared synthetic scale workloads; no LLM generation or independent semantic labels."""

from .quantum_tradeoff import Architecture


def scale_case(size: int, family: str = "chain") -> Architecture:
    if not 1 <= size <= 50 or family not in {"chain", "pressure"}:
        raise ValueError("Scale fixture needs 1..50 components and chain/pressure family.")
    components = [{"id": f"C{index:02d}", "name": f"Prepared component {index}"} for index in range(size)]
    labels = {index: index // 3 if family == "chain" else index % 4 for index in range(size)}
    requirements = []
    for label in sorted(set(labels.values())):
        members = [f"C{index:02d}" for index in range(size) if labels[index] == label]
        text = f"Prepared benchmark assumption {family}/{label}: {', '.join(members)} share one Reliability target. No measured threshold is supplied."
        requirements.append({"id": f"BENCH-{label:02d}", "kind": "NFR", "text": text, "component_ids": members,
                             "quality_allocations": [{"characteristic": "Reliability", "component_ids": members, "source_quote": text}]})
    stores = []
    for index in range(0, size - 1, 3):
        members = [f"C{index:02d}", f"C{(index + (1 if family == 'chain' else 4)) % size:02d}"]
        if members[0] != members[1]:
            stores.append({"id": f"D{index:02d}", "name": f"Prepared store {index}", "members": members,
                           "policy": "SPLITTABLE", "basis": "Prepared scale policy", "weight": 1})
    interactions = [{"source": f"C{index:02d}", "target": f"C{index+1:02d}", "mode": "SYNC" if index % 3 != 2 else "ASYNC", "weight": 1 + index % 2}
                    for index in range(size - 1)]
    if family == "pressure":
        interactions.extend({"source": f"C{index:02d}", "target": f"C{(index+7) % size:02d}", "mode": "ASYNC", "weight": 1}
                            for index in range(size) if (index + 7) % size != index and (index + 7) % size != index + 1)
    return Architecture.model_validate({"input_origin": "PREPARED_FIXTURE", "components": components, "requirements": requirements, "interactions": interactions, "stores": stores,
        "keep_apart": [{"left": "C00", "right": f"C{size-1:02d}", "basis": "Prepared scale isolation"}] if size > 1 else []})
