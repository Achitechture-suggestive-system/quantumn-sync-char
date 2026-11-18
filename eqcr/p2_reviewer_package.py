"""Build and validate the source-only Tutor reviewer package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .p2_protocol import (
    BLIND_PROTOCOL_VERSION,
    BlindAnnotationSubmission,
    build_relation_registry,
    source_bundle_sha256,
)


SOURCE_PACKAGE_VERSION = "P2-SOURCE-ONLY-PACKAGE-v1"
EXPECTED_SOURCE_PACKAGE_MANIFEST_SHA256 = "5725d44f491c5b680f79773482b6a53a03810cb88978b073a6ec5aacac68fe81"
SOURCE_DATA_FILE = "SOURCE_DATA.json"
SOURCE_MATERIAL_FILE = "SOURCE_MATERIAL.md"
REVIEWER_GUIDE_FILE = "README.md"
ANNOTATION_TEMPLATE_FILE = "ANNOTATION_TEMPLATE.json"
MANIFEST_FILE = "MANIFEST.json"
PACKAGE_FILES = {
    SOURCE_DATA_FILE,
    SOURCE_MATERIAL_FILE,
    REVIEWER_GUIDE_FILE,
    ANNOTATION_TEMPLATE_FILE,
    MANIFEST_FILE,
}


class SourceOnlyPackageError(ValueError):
    """Raised when reviewer materials are missing, changed, or contain extras."""


def default_source_package_root() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "p2" / "source_only_reviewer"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _source_items(raw: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    if kind == "requirement":
        key = "requirements"
    elif kind == "workflow":
        key = "workflows"
    elif kind == "quality_scenario":
        key = "scenarios"
    else:
        raise SourceOnlyPackageError(f"Unsupported source kind: {kind}.")

    output = []
    for item in raw.get(key, []):
        source_ref = item.get("source_ref")
        if not isinstance(source_ref, dict):
            raise SourceOnlyPackageError(f"{kind} {item.get('id')} has no source span.")
        quote = source_ref.get("quote")
        start, end = source_ref.get("start"), source_ref.get("end")
        if not isinstance(quote, str) or not quote or not isinstance(start, int) or not isinstance(end, int):
            raise SourceOnlyPackageError(f"{kind} {item.get('id')} has an invalid source span.")
        if start < 0 or end < start or end - start != len(quote):
            raise SourceOnlyPackageError(f"{kind} {item.get('id')} has inconsistent source span offsets.")
        if kind != "quality_scenario" and item.get("text") != quote:
            raise SourceOnlyPackageError(f"{kind} {item.get('id')} source quote differs from its source text.")
        output.append(
            {
                "id": item["id"],
                "source_id": source_ref["source_id"],
                "text": quote,
                "start": start,
                "end": end,
            }
        )
    return output


def source_only_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Return only source material; omit curated mappings and pipeline helper fields."""
    return {
        "case_id": raw["case_id"],
        "context_id": raw["context_id"],
        "context_description": raw["context_description"],
        "requirements": _source_items(raw, "requirement"),
        "workflows": _source_items(raw, "workflow"),
        "quality_scenarios": _source_items(raw, "quality_scenario"),
    }


def _reviewer_guide() -> str:
    return """# Hướng dẫn người ghi annotation độc lập

## Phạm vi tài liệu

Chỉ sử dụng `SOURCE_MATERIAL.md` và `SOURCE_DATA.json` trong thư mục này. Hoàn tất và khóa annotation trước khi mở tài liệu phân tích nào khác của case.

Đây là case Tutor Support nhỏ được chuẩn bị cho nghiên cứu; nội dung không đến từ hệ thống production. Tài liệu không cung cấp source code, topology triển khai hoặc quyết định kiến trúc đã được xác nhận.

## Cách ghi responsibility

- Một FR có thể có không, một hoặc nhiều diễn giải responsibility; một responsibility có thể được hỗ trợ bởi nhiều FR.
- Chỉ ghi activity/operation mà bạn thấy có căn cứ trong nguồn. Không chia nhỏ một hành động thành nhiều responsibility nếu nguồn không hỗ trợ granularity đó.
- Nếu chưa diễn giải được FR, để FR đó trong `unresolved_requirement_ids`.
- Ghi `requirement_ids`, `source_requirement_ids`, các `workflow_ids` được hỗ trợ, `source_workflow_ids` và rationale ngắn.

## Cách ghi relation

Giữ nguyên toàn bộ relation registry trong JSON. Các predicate là `BUSINESS_PRECEDES` (có hướng), `SHARES_STATE_OR_INVARIANT` và `REQUIRES_INDEPENDENT_CHANGE` (không hướng).

- `PRESENT`: nguồn hỗ trợ relation; nêu lý do và cite cả hai FR endpoint.
- `UNKNOWN`: đã cân nhắc nhưng nguồn chưa đủ để kết luận.
- `SCOPED_ABSENT`: chỉ dùng khi phạm vi nguồn nêu rõ relation bị loại trừ.
- `NOT_ANNOTATED`: chưa đưa ra quyết định; để trống citation và rationale.

Thứ tự nghiệp vụ tự nó không xác định cách nhóm, giao tiếp hay triển khai responsibility. Không điền quan hệ ngoài registry.

## Hoàn tất và khóa

1. Bắt đầu từ `ANNOTATION_TEMPLATE.json`; không đổi `case_id`, hash, protocol version, predicate hoặc endpoint trong registry.
2. Điền reviewer ID và xác nhận hai trường attestation chỉ khi đúng sự thật.
3. Với mỗi FR, thêm một hay nhiều responsibility annotations hoặc ghi rõ FR unresolved. Không để hai nhóm trùng nhau hay thiếu FR.
4. Để relation chưa đánh giá ở `NOT_ANNOTATED`; chỉ thêm rationale/citation khi đã quyết định.
5. Dùng ứng dụng EQCR + QAME để khóa JSON. Ứng dụng ghi timestamp UTC và hash nội dung. Lưu nguyên bản JSON đã khóa.
6. Chạy `python scripts/validate_p2_annotation_lock.py --annotation-lock <locked-json> --source-package <package-directory>` để kiểm tra file/hash/schema/thời điểm.

Danh tính và lịch sử tiếp xúc tài liệu được tự khai báo; phần mềm không thể xác thực độc lập reviewer đã đọc gì.
"""


def render_source_material(payload: dict[str, Any]) -> str:
    lines = [
        "# Tutor Support — tài liệu nguồn",
        "",
        f"- Case ID: `{payload['case_id']}`",
        f"- Context ID: `{payload['context_id']}`",
        f"- Context: {payload['context_description']}",
        "",
        "Các đoạn trích và offsets bên dưới được giữ nguyên theo SOURCE_DATA.json.",
    ]
    sections = (
        ("Yêu cầu chức năng", "requirements", "FR"),
        ("Hoạt động workflow", "workflows", "WF"),
        ("Quality scenarios", "quality_scenarios", "SC"),
    )
    for title, key, _prefix in sections:
        lines.extend(["", f"## {title}"])
        for item in payload[key]:
            lines.extend(
                [
                    "",
                    f"### {item['id']} — source `{item['source_id']}`",
                    f"Span: `{item['start']}:{item['end']}`",
                    "",
                    f"> {item['text']}",
                ]
            )
    lines.append("")
    return "\n".join(lines)


def build_source_only_reviewer_package(raw: dict[str, Any], package_root: Path) -> dict[str, Any]:
    package_root = Path(package_root)
    package_root.mkdir(parents=True, exist_ok=True)
    payload = source_only_payload(raw)
    source_data_bytes = _json_bytes(payload)
    source_material_bytes = render_source_material(payload).encode("utf-8")
    guide_bytes = _reviewer_guide().encode("utf-8")

    (package_root / SOURCE_DATA_FILE).write_bytes(source_data_bytes)
    (package_root / SOURCE_MATERIAL_FILE).write_bytes(source_material_bytes)
    (package_root / REVIEWER_GUIDE_FILE).write_bytes(guide_bytes)

    files = [
        {"path": name, "sha256": _sha256_bytes(content)}
        for name, content in (
            (REVIEWER_GUIDE_FILE, guide_bytes),
            (SOURCE_DATA_FILE, source_data_bytes),
            (SOURCE_MATERIAL_FILE, source_material_bytes),
        )
    ]
    source_entries = []
    for key, kind in (
        ("requirements", "requirement"),
        ("workflows", "workflow"),
        ("quality_scenarios", "quality_scenario"),
    ):
        for item in payload[key]:
            source_entries.append(
                {
                    "source_id": item["source_id"],
                    "kind": kind,
                    "item_id": item["id"],
                    "source_file": SOURCE_DATA_FILE,
                    "start": item["start"],
                    "end": item["end"],
                    "text_sha256": _sha256_bytes(item["text"].encode("utf-8")),
                }
            )
    manifest = {
        "manifest_version": SOURCE_PACKAGE_VERSION,
        "protocol_version": BLIND_PROTOCOL_VERSION,
        "case_id": raw["case_id"],
        "source_bundle_sha256": source_bundle_sha256(raw),
        "source_data_sha256": _sha256_bytes(source_data_bytes),
        "source_entries": source_entries,
        "files": files,
    }
    manifest_bytes = _json_bytes(manifest)
    (package_root / MANIFEST_FILE).write_bytes(manifest_bytes)
    manifest_sha256 = _sha256_bytes(manifest_bytes)

    from .p2_protocol import build_relation_registry

    template = {
        "protocol_version": BLIND_PROTOCOL_VERSION,
        "case_id": raw["case_id"],
        "source_bundle_sha256": source_bundle_sha256(raw),
        "source_package_manifest_sha256": manifest_sha256,
        "reviewer_id": "",
        "source_only_attested": False,
        "no_prior_model_output_exposure": False,
        "responsibility_annotations": [],
        "unresolved_requirement_ids": [],
        "relation_registry": build_relation_registry(raw),
    }
    (package_root / ANNOTATION_TEMPLATE_FILE).write_bytes(_json_bytes(template))
    return validate_source_only_reviewer_package(raw, package_root)


def validate_source_only_reviewer_package(raw: dict[str, Any], package_root: Path | None = None) -> dict[str, Any]:
    package_root = Path(package_root) if package_root is not None else default_source_package_root()
    if not package_root.is_dir():
        raise SourceOnlyPackageError(f"Source-only reviewer package directory is missing: {package_root}.")
    if any(path.is_symlink() for path in package_root.rglob("*")):
        raise SourceOnlyPackageError("Source-only reviewer package cannot contain symbolic links.")
    present = {path.relative_to(package_root).as_posix() for path in package_root.rglob("*") if path.is_file()}
    if present != PACKAGE_FILES:
        raise SourceOnlyPackageError(
            f"Source-only reviewer package file set differs from the allowlist: missing={sorted(PACKAGE_FILES - present)}, "
            f"unexpected={sorted(present - PACKAGE_FILES)}."
        )

    manifest_path = package_root / MANIFEST_FILE
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_data = json.loads((package_root / SOURCE_DATA_FILE).read_text(encoding="utf-8"))
        template = json.loads((package_root / ANNOTATION_TEMPLATE_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceOnlyPackageError(f"A required reviewer package file is unreadable or invalid JSON: {exc}.") from exc

    expected_files = {REVIEWER_GUIDE_FILE, SOURCE_DATA_FILE, SOURCE_MATERIAL_FILE}
    if manifest.get("manifest_version") != SOURCE_PACKAGE_VERSION:
        raise SourceOnlyPackageError("Unsupported source-only package manifest version.")
    if manifest.get("protocol_version") != BLIND_PROTOCOL_VERSION:
        raise SourceOnlyPackageError("Reviewer package protocol version does not match the lock schema.")
    if manifest.get("case_id") != raw.get("case_id") or manifest.get("source_bundle_sha256") != source_bundle_sha256(raw):
        raise SourceOnlyPackageError("Reviewer package is bound to a different case or source bundle.")

    expected_payload = source_only_payload(raw)
    if source_data != expected_payload:
        raise SourceOnlyPackageError("Source data file differs from the exact Tutor source IDs, text, or spans.")
    expected_material = render_source_material(expected_payload).encode("utf-8")
    if (package_root / SOURCE_MATERIAL_FILE).read_bytes() != expected_material:
        raise SourceOnlyPackageError("Readable source material differs from the canonical source data.")

    files = manifest.get("files")
    if not isinstance(files, list) or {item.get("path") for item in files if isinstance(item, dict)} != expected_files:
        raise SourceOnlyPackageError("Manifest must hash every source-only package file except itself and the bound template.")
    file_hashes = {}
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise SourceOnlyPackageError("Manifest contains a malformed file-hash entry.")
        rel = entry["path"]
        if rel not in expected_files:
            raise SourceOnlyPackageError("Manifest references an unexpected package path.")
        content = (package_root / rel).read_bytes()
        digest = _sha256_bytes(content)
        if entry["sha256"] != digest:
            raise SourceOnlyPackageError(f"Source-only file hash mismatch: {rel}.")
        file_hashes[rel] = digest

    source_entries = manifest.get("source_entries")
    expected_entries = []
    for key, kind in (
        ("requirements", "requirement"),
        ("workflows", "workflow"),
        ("quality_scenarios", "quality_scenario"),
    ):
        for item in expected_payload[key]:
            expected_entries.append(
                {
                    "source_id": item["source_id"],
                    "kind": kind,
                    "item_id": item["id"],
                    "source_file": SOURCE_DATA_FILE,
                    "start": item["start"],
                    "end": item["end"],
                    "text_sha256": _sha256_bytes(item["text"].encode("utf-8")),
                }
            )
    if manifest.get("source_data_sha256") != file_hashes[SOURCE_DATA_FILE] or source_entries != expected_entries:
        raise SourceOnlyPackageError("Manifest source IDs, spans, or source-text hashes do not match the package.")

    manifest_sha256 = _sha256_bytes(manifest_path.read_bytes())
    if manifest_sha256 != EXPECTED_SOURCE_PACKAGE_MANIFEST_SHA256:
        raise SourceOnlyPackageError("Reviewer package manifest differs from the committed, versioned source package.")
    if template.get("source_package_manifest_sha256") != manifest_sha256:
        raise SourceOnlyPackageError("Blank annotation template is not bound to this exact package manifest.")
    try:
        parsed_template = BlindAnnotationSubmission.model_validate(template)
    except ValidationError as exc:
        raise SourceOnlyPackageError(f"Blank annotation template does not match the protocol schema: {exc}.") from exc
    expected_relation_registry = build_relation_registry(raw)
    if (
        parsed_template.responsibility_annotations
        or parsed_template.unresolved_requirement_ids
        or [item.model_dump(mode="json") for item in parsed_template.relation_registry] != expected_relation_registry
        or parsed_template.reviewer_id
        or parsed_template.source_only_attested
        or parsed_template.no_prior_model_output_exposure
    ):
        raise SourceOnlyPackageError("Annotation template contains pre-filled labels or differs from the blank protocol form.")
    return {
        "status": "SOURCE_ONLY_PACKAGE_VALID",
        "manifest_version": SOURCE_PACKAGE_VERSION,
        "protocol_version": BLIND_PROTOCOL_VERSION,
        "case_id": raw["case_id"],
        "manifest_sha256": manifest_sha256,
        "source_bundle_sha256": source_bundle_sha256(raw),
        "source_count": len(expected_entries),
        "file_sha256": file_hashes,
    }
