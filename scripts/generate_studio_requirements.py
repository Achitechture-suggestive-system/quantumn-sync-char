"""Generate synthetic Ticket Support inputs with local Ollama and retain the raw runs.

Run from the repo root with `python -m scripts.generate_studio_requirements`.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from eqcr.ollama import _host, _request, get_ollama_version, list_model_details
from eqcr.quantum_example import ticket_example
from eqcr.studio_quality import QualityCharacteristic


BRIEFS = {
    "CAPACITY": (
        "Tải cao và xử lý ticket",
        "Mùa cao điểm. Xét gửi lặp khi nhấp hai lần, điều phối viên đổi nhóm xử lý, mở rộng ngang khâu "
        "tạo ticket, công bằng khi hàng đợi dồn tải, báo cáo chạy đồng thời với việc tiếp nhận, và phục hồi khi worker ngừng.",
    ),
    "RECOVERY": (
        "Gián đoạn và khôi phục",
        "Gián đoạn từng phần. Xét phát lại bản ghi, cảnh báo tồn đọng, khôi phục ticket sau mất kết nối, "
        "kiểm tra phân quyền người xem dấu vết, kho báo cáo không truy cập được, và tỷ lệ phát lại trùng.",
    ),
    "CHANGE": (
        "Thay đổi và tích hợp",
        "Thay đổi và tích hợp. Xét xuất dữ liệu báo cáo, lịch hẹn bảo trì trên hồ sơ, hệ thống đối tác đọc dữ liệu, "
        "thao tác bằng bàn phím, kiểm thử khi đổi luật định tuyến và tương thích với hợp đồng dữ liệu phiên bản cũ.",
    ),
}

TOPICS = {
    "CAPACITY": (
        ("FR", "idempotent submission on double-click"),
        ("FR", "manual team reassignment before a technician accepts work"),
        ("NFR", "horizontal scaling of new ticket intake"),
        ("NFR", "end-to-end time from submission to assigned team during a campaign"),
        ("NFR", "effects of simultaneous report generation on ticket intake speed"),
        ("NFR", "worker crash during ticket completion"),
        ("NFR", "correct creation and assignment under overload"),
    ),
    "RECOVERY": (
        ("FR", "replay unprocessed records after disruption"),
        ("FR", "manager downloads a status audit trail"),
        ("NFR", "accepted requests still assigned after a network failure"),
        ("NFR", "avoid missing or duplicate ticket states during replay between routing and completion"),
        ("NFR", "authorization and refusal to disclose the managers' audit trail"),
        ("NFR", "ticket completion while reporting is offline"),
        ("NFR", "latency from routing backlog to operations dashboard"),
    ),
    "CHANGE": (
        ("FR", "customer changes a maintenance appointment on their profile"),
        ("FR", "manager filters and exports completed ticket records"),
        ("NFR", "partner reads report exports in both old and new contract versions"),
        ("NFR", "customer signs in and files tickets using only a keyboard"),
        ("NFR", "testing changed routing rules without editing completion code"),
        ("NFR", "time to attach the profile appointment when filing a ticket under normal load"),
        ("NFR", "move profile and reporting independently to a new storage environment"),
    ),
}


def proposal_schema(case_id: str, component_ids: list[str]) -> dict:
    rows = {}
    for position, (kind, _) in enumerate(TOPICS[case_id], 1):
        is_nfr = kind == "NFR"
        rows[f"r{position}"] = {
            "type": "object", "additionalProperties": False,
            "required": ["text", "component_ids", "characteristic", "quote"],
            "properties": {
                "text": {"type": "string"},
                "component_ids": {"type": "array", "minItems": 1, "maxItems": 3,
                                  "items": {"enum": component_ids}},
                "characteristic": {"enum": list(QualityCharacteristic) if is_nfr else [None]},
                "quote": {"type": "string", "description": "Exact measurable phrase from text."} if is_nfr else {"enum": [""]},
            },
        }
    return {"type": "object", "properties": rows, "required": list(rows), "additionalProperties": False}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def serialize(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def prompt_for(case_id: str, brief: str) -> str:
    ticket = ticket_example()
    return (
        "Write 7 NEW synthetic Ticket Support requirements, with `text` in Vietnamese. Return only JSON. "
        "Write 2 functional requirements (FR) and 5 quality scenarios (NFR). FR has characteristic=null and quote=\"\". "
        "Write a complete acceptance statement in Vietnamese, not a headline or translation of the brief. "
        "For each NFR, specify a trigger, operating condition, response, AND a numerical acceptance target in `text`. "
        "Choose an ISO label in `characteristic`; copy the exact measurable Vietnamese phrase from `text` into `quote`. "
        "Example for a different system: if text ends with 'trong vòng 45 giây.', quote may be 'trong vòng 45 giây'. "
        "A quote is NEVER the English ISO label. Use a different scenario and target per item. Prefer at least 3 distinct ISO labels. "
        "Keep text under 450 characters. Choose only the 1–3 directly responsible component IDs. In each pack, include at least "
        "two NFRs with multiple components that jointly influence one outcome. Do not invent components, stores, links or Quanta. "
        "Do not claim measured results. Do not repeat these baseline topics: self-service login/profile/ticket creation, "
        "basic router-to-completion state consistency, read operations report, 200 ms ticket p95, 10-minute reporting recovery, "
        "or encryption of profile data in transit. Follow the seven distinct topics below in order. "
        "A component that is slow, unavailable or a source of data is in scope only if its behavior is part of the target.\n\n"
        f"Kịch bản {case_id}: {brief}\n"
        f"Component hợp lệ: {', '.join(f'{item.id} = {item.name}' for item in ticket.components)}\n"
        "Nhãn ISO hợp lệ: " + ", ".join(item.value for item in QualityCharacteristic) + "\n"
        + "\n".join(f"r{position} ({kind}): {topic}" for position, (kind, topic) in enumerate(TOPICS[case_id], 1))
    )


def generate(model: str, run_dir: Path) -> Path:
    service = urlsplit(_host())
    metadata = next((item for item in list_model_details() if item["name"] == model), None)
    if not metadata or not metadata.get("digest"):
        raise ValueError(f"Model {model} không có digest trong Ollama tại {service.hostname}.")
    version = get_ollama_version()
    run_dir.mkdir(parents=True, exist_ok=False)
    packs = []
    component_ids = [item.id for item in ticket_example().components]
    for number, (case_id, (title, brief)) in enumerate(BRIEFS.items(), start=1):
        payload = {
            "model": model, "stream": False, "think": False, "format": proposal_schema(case_id, component_ids),
            "options": {"temperature": 0.2, "seed": 150 + number, "num_ctx": 6144, "num_predict": 2800},
            "messages": [{"role": "user", "content": prompt_for(case_id, brief)}],
        }
        request_text = serialize(payload)
        case_path = run_dir / case_id.lower()
        case_path.mkdir()
        (case_path / "request.json").write_bytes(request_text.encode("utf-8"))
        print(f"Ollama | {model} | {case_id}", flush=True)
        response = _request("/api/chat", payload=payload, timeout=480)
        (case_path / "response.json").write_bytes(serialize(response).encode("utf-8"))
        content = response["message"]["content"]
        if response.get("model") != model or response.get("done_reason") != "stop" or not response.get("eval_count"):
            raise ValueError(f"Phản hồi {case_id} chưa hoàn tất, kiểm tra {case_path}.")
        output = json.loads(content)
        packs.append({
            "id": case_id, "title": title, "brief": brief,
            "created_at": response["created_at"], "ollama_version": version,
            "model": model, "model_digest": metadata["digest"],
            "request_sha256": digest(request_text), "response_sha256": digest(content),
            "generated_tokens": response["eval_count"],
            "proposals": [
                {"kind": kind, **output[f"r{position}"]}
                for position, (kind, _) in enumerate(TOPICS[case_id], 1)
            ],
        })
        print(f"{case_id} | {len(packs[-1]['proposals'])} proposals | {response['eval_count']} tokens", flush=True)
    output = run_dir / "proposals.json"
    output.write_bytes(serialize(packs).encode("utf-8"))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--run-dir", type=Path, default=Path("runs") / datetime.now(timezone.utc).strftime(
        "studio-llm-%Y%m%dT%H%M%S%fZ"))
    args = parser.parse_args()
    print(generate(args.model, args.run_dir))


if __name__ == "__main__":
    main()
