"""Source-only, hash-bound Studio reference protocol; never generates human labels."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from . import storage
from .quantum_tradeoff import Architecture, InputModel, Key, Label, QualityAllocation, Interaction, SeparatePair
from .studio_extraction import PROMPT_VERSION, build_request
from .studio_oracles import oracle_ticket_cases
from .quantum_example import ticket_example


PROTOCOL = "STUDIO-EVALUATION@1"
MATCHING = "SOURCE-TASK-CONDITION-ATOMIC-LINK@1"
ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = ("studio_extraction.py", "studio_semantics.py", "studio_quality.py", "quantum_tradeoff.py",
              "studio_evidence.py", "studio_evaluation_protocol.py", "studio_evaluation.py", "studio_sentence_extraction.py")
PACKAGE_FILES = {"SOURCE.json", "ANNOTATION_TEMPLATE.json", "README.md", "MANIFEST.json"}


class EvaluationBlocked(ValueError):
    status = "STUDIO_EVALUATION_BLOCKED"


def digest(value) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def timestamp(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("Timestamp needs a timezone.")
        return result
    except (ValueError, AttributeError) as exc:
        raise EvaluationBlocked("Thời điểm cần ISO-8601 và múi giờ.") from exc


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def code_hashes() -> dict:
    return {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in CODE_FILES}


class SourceComponent(InputModel):
    id: Key
    name: Label


class SourceRequirement(InputModel):
    id: Key
    kind: Literal["FR", "NFR", "UNSPECIFIED"]
    text: str = Field(min_length=1, max_length=600)
    component_ids: list[Key] = Field(default_factory=list, max_length=50)


class SourceCase(InputModel):
    id: Key
    document_group: Key
    split: Literal["DEVELOPMENT", "HELD_OUT"]
    provenance: Literal["PREPARED_FIXTURE", "USER_SUPPLIED"]
    authorship: str = Field(min_length=1, max_length=300)
    components: list[SourceComponent] = Field(min_length=1, max_length=50)
    requirements: list[SourceRequirement] = Field(min_length=1, max_length=40)

    def architecture(self) -> Architecture:
        return Architecture.model_validate({"input_origin": self.provenance,
            "components": [item.model_dump() for item in self.components],
            "requirements": [item.model_dump() for item in self.requirements]})


class Query(InputModel):
    id: Key
    case_id: Key
    task: Literal["QUALITY", "INTERACTION", "SEPARATION"]
    source_ids: list[Key] = Field(min_length=1, max_length=8)


class StudySource(InputModel):
    schema_id: Literal["STUDIO-EVALUATION@1"] = PROTOCOL
    id: Key
    curation_rationale: str = Field(min_length=1, max_length=2000)
    no_known_paraphrase_leakage_attested: bool = False
    cases: list[SourceCase] = Field(min_length=1, max_length=40)
    queries: list[Query] = Field(min_length=1, max_length=120)


def unit_key(case_id, task, source_id) -> str:
    return f"{case_id}/{task}/{source_id}"


def validate_source(raw: dict) -> StudySource:
    source = StudySource.model_validate(raw)
    if not source.no_known_paraphrase_leakage_attested:
        raise EvaluationBlocked("Cần khai báo việc tách document và kiểm paraphrase trước khi freeze.")
    cases = {case.id: case for case in source.cases}
    if len(cases) != len(source.cases) or len({q.id for q in source.queries}) != len(source.queries):
        raise EvaluationBlocked("Case/query IDs cần duy nhất.")
    if not any(case.split == "HELD_OUT" for case in source.cases):
        raise EvaluationBlocked("Study cần ít nhất một document held-out.")
    groups, texts, units, queried = {}, {}, set(), set()
    known = {digest(" ".join(item["text"].split()).casefold()) for item in oracle_ticket_cases().values()}
    known.update(digest(" ".join(item.text.split()).casefold()) for item in ticket_example().requirements)
    for case in source.cases:
        case.architecture()  # Existing ID/catalog/requirement-scope validation.
        if case.document_group in groups and groups[case.document_group] != case.split:
            raise EvaluationBlocked("Không chia cùng document_group qua development và held-out.")
        groups[case.document_group] = case.split
        for requirement in case.requirements:
            signature = digest(" ".join(requirement.text.split()).casefold())
            if case.split == "HELD_OUT" and signature in known:
                raise EvaluationBlocked("Nguồn held-out trùng ca phát triển đã biết của repo.")
            if signature in texts and texts[signature] != case.split:
                raise EvaluationBlocked("Nguồn trùng giữa development và held-out.")
            texts[signature] = case.split
    for query in source.queries:
        if query.case_id not in cases:
            raise EvaluationBlocked("Query tham chiếu case không tồn tại.")
        queried.add(query.case_id)
        build_request(cases[query.case_id].architecture(), query.source_ids, query.task)
        for source_id in query.source_ids:
            key = unit_key(query.case_id, query.task, source_id)
            if key in units:
                raise EvaluationBlocked("Một source/task chỉ có trong một query; repetition được khai báo riêng.")
            units.add(key)
    if queried != set(cases):
        raise EvaluationBlocked("Mỗi case cần query đã khai báo.")
    return source


def source_units(source: StudySource) -> dict:
    cases = {case.id: case for case in source.cases}
    result = {}
    for query in source.queries:
        for identifier in query.source_ids:
            case = cases[query.case_id]
            requirement = next(item for item in case.requirements if item.id == identifier)
            result[unit_key(case.id, query.task, identifier)] = (case, query.task, requirement)
    return result


def annotation_template(source: StudySource, package_digest: str) -> dict:
    return {"protocol": PROTOCOL, "package_digest": package_digest, "annotator_id": "",
            "provenance": "UNDECLARED", "source_only_attested": False,
            "no_prior_model_output_exposure": False, "independent_of_other_annotators": False,
            "completed_at": None, "rows": [{"unit": key, "status": "NOT_ANNOTATED", "claims": [], "rationale": ""}
                                             for key in source_units(source)]}


REVIEWER_GUIDE = """# Studio — source-only worksheet

Chỉ nhận thư mục này; không xem repository reports, prompt, model output hoặc đáp án của annotator khác trước khi khóa bài riêng.
Đọc SOURCE.json: component catalog, văn bản nguyên gốc, kind/scope đầu vào và query task. Kind đã khai báo là điều kiện đầu vào, không phải kết quả classifier đang được chấm.
Mỗi unit là một case/task/source. Giữ NOT_ANNOTATED đến khi đọc; chọn COMPLETE chỉ khi đã liệt kê tất cả claim cho task đó.
COMPLETE + claims=[] là kết luận rõ không có claim hoạt động trong nguồn. UNRESOLVED cần rationale và claims=[]; không suy thành absence.
Tách các mệnh đề độc lập. QUALITY ghi mỗi characteristic với đúng component phụ trách; bối cảnh lỗi không tự là owner.
INTERACTION ghi source, target, mode SYNC/ASYNC/UNKNOWN và local_transaction; thứ tự workflow không đủ suy ra chờ đồng bộ.
SEPARATION ghi left/right chỉ khi có chính sách tách bắt buộc; cùng giao dịch và async không tự cho phép suy thành tách.
Mỗi claim gồm kind, quote nguyên văn, condition (nguyên văn hoặc null), rồi các trường task như mô tả dưới đây. Không tự điền threshold hoặc ID ngoài catalog.

- QUALITY: characteristic (một trong chín nhãn dưới đây), component_ids (không rỗng, không trùng).
- INTERACTION: source, target (khác nhau), mode, local_transaction (boolean; true chỉ cùng giao dịch cục bộ, mode SYNC).
- SEPARATION: left, right (khác nhau).

Chín nhãn ISO/IEC 25010:2023: Functional suitability; Performance efficiency; Compatibility; Interaction capability; Reliability; Security; Maintainability; Flexibility; Safety.
Chỉ gán nhãn từ nội dung; nếu không đủ căn cứ, ghi UNRESOLVED và lý do. Tập nhãn là taxonomy, không phải bằng chứng target đã đạt.
Matching @1 chấm atomic link: QUALITY tách từng owner; INTERACTION giữ hướng/mode/local_transaction; SEPARATION không hướng.
Mọi key có case/source/task và condition chính xác (null khác câu điều kiện); quote dùng kiểm citation, không đưa toàn quote vào key.
Matching không chấm frame/entailment/target số hoặc chứng minh deployment; rationale và unresolved được giữ để adjudication.
Không ghi claim cho câu miễn nghĩa vụ chỉ vì có từ khóa chất lượng. Điều cấm có thể tạo nghĩa vụ; đọc đầy đủ phạm vi phủ định.
Không dùng LLM để điền reference. Chọn provenance HUMAN_SOURCE_ONLY chỉ khi bản thân annotator thực hiện độc lập; fixture/test không đủ điều kiện.
Hai annotator khóa riêng trước inference. Người adjudicate (một annotator hoặc người thứ ba) xem source và hai bài đã khóa, không xem model, ghi lý do cho mọi unit.
ID/dấu thời gian và attestation là tự khai báo; công cụ không xác thực danh tính hoặc lịch sử truy cập của con người.
"""


def _write_new(path: Path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n" if not isinstance(value, str) else value)


def prepare_study(raw: dict, folder: Path, *, model_digest: str, code_sha: str, repetitions=3, prepared_at=None) -> dict:
    source = validate_source(raw)
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or not 1 <= repetitions <= 10:
        raise EvaluationBlocked("Repetition phải là số nguyên 1..10.")
    if len(model_digest) != 64 or any(ch not in "0123456789abcdef" for ch in model_digest):
        raise EvaluationBlocked("Cần SHA-256 digest của exact qwen3:4b model.")
    if len(code_sha) != 40 or any(ch not in "0123456789abcdef" for ch in code_sha):
        raise EvaluationBlocked("Cần commit SHA đầy đủ đã chốt.")
    created = prepared_at or now()
    timestamp(created)
    canonical = source.model_dump(mode="json")
    source_digest = digest(canonical)
    exposed, history = set(), {}
    for path in (storage.ARTIFACT_ROOT / "quantum-studio" / "extractions").glob("*/request.json"):
        request = json.loads(path.read_text(encoding="utf-8"))
        try:
            entries = json.loads(request["messages"][-1]["content"])
            if isinstance(entries, dict):
                entries = entries["sources"]
            exposed.update(digest(" ".join(item["text"].split()).casefold()) for item in entries)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise EvaluationBlocked("Không đọc được source ledger từ extraction request đã có; cần audit trước freeze.") from exc
        history[path.parent.name] = sha256(path.read_bytes()).hexdigest()
    for case in source.cases:
        if case.split == "HELD_OUT" and any(digest(" ".join(r.text.split()).casefold()) in exposed for r in case.requirements):
            raise EvaluationBlocked("Nguồn held-out đã xuất hiện trong một extraction local trước freeze.")
    payloads = {q.id: build_request(next(c for c in source.cases if c.id == q.case_id).architecture(), q.source_ids, q.task)
                for q in source.queries}
    frozen = {"protocol": PROTOCOL, "matching": MATCHING, "recorded_at": created, "source_digest": source_digest,
              "code_sha": code_sha, "code_hashes": code_hashes(), "model": "qwen3:4b", "model_digest": model_digest,
              "prompt_version": PROMPT_VERSION, "repetitions": repetitions, "request_digests": {key: digest(v) for key, v in payloads.items()},
              "prior_extraction_request_hashes": history, "prior_exposed_source_digests": sorted(exposed)}
    frozen["study_digest"] = digest(frozen)
    folder.mkdir(parents=True, exist_ok=False)
    package = folder / "source_only"
    package.mkdir()
    _write_new(package / "SOURCE.json", canonical)
    _write_new(package / "ANNOTATION_TEMPLATE.json", annotation_template(source, source_digest))
    _write_new(package / "README.md", REVIEWER_GUIDE)
    _write_new(package / "MANIFEST.json", {"protocol": PROTOCOL, "source_digest": source_digest,
               "files": {p.name: sha256(p.read_bytes()).hexdigest() for p in package.iterdir()}})
    _write_new(folder / "frozen.json", frozen)
    _write_new(folder / "requests.json", payloads)
    return frozen


def load_study(folder: Path) -> tuple[StudySource, dict]:
    package = folder / "source_only"
    if {p.name for p in package.iterdir()} != PACKAGE_FILES or any(not p.is_file() or p.is_symlink() for p in package.iterdir()):
        raise EvaluationBlocked("Source-only package có file thiếu/thừa hoặc symlink.")
    manifest = json.loads((package / "MANIFEST.json").read_text(encoding="utf-8"))
    files = manifest.get("files", {})
    if set(files) != PACKAGE_FILES - {"MANIFEST.json"} or any(sha256((package / name).read_bytes()).hexdigest() != value for name, value in files.items()):
        raise EvaluationBlocked("Hash source-only package không khớp.")
    source = validate_source(json.loads((package / "SOURCE.json").read_text(encoding="utf-8")))
    frozen = json.loads((folder / "frozen.json").read_text(encoding="utf-8"))
    unsigned = {key: value for key, value in frozen.items() if key != "study_digest"}
    if frozen.get("study_digest") != digest(unsigned) or frozen.get("protocol") != PROTOCOL or frozen.get("matching") != MATCHING:
        raise EvaluationBlocked("Frozen protocol/digest không khớp.")
    if frozen.get("source_digest") != digest(source.model_dump(mode="json")) or manifest.get("source_digest") != frozen["source_digest"]:
        raise EvaluationBlocked("Source/frozen hash không khớp.")
    if any(digest(" ".join(r.text.split()).casefold()) in frozen.get("prior_exposed_source_digests", []) for c in source.cases if c.split == "HELD_OUT" for r in c.requirements):
        raise EvaluationBlocked("Held-out source đã có trong ledger exposure lúc freeze.")
    if frozen.get("code_hashes") != code_hashes() or frozen.get("prompt_version") != PROMPT_VERSION:
        raise EvaluationBlocked("Code/prompt thay đổi sau freeze; không chấm như cùng protocol.")
    payloads = json.loads((folder / "requests.json").read_text(encoding="utf-8"))
    expected = {q.id: build_request(next(c for c in source.cases if c.id == q.case_id).architecture(), q.source_ids, q.task)
                for q in source.queries}
    if payloads != expected or frozen.get("request_digests") != {key: digest(v) for key, v in expected.items()}:
        raise EvaluationBlocked("Request khác bản freeze.")
    if manifest.get("protocol") != PROTOCOL or json.loads((package / "ANNOTATION_TEMPLATE.json").read_text(encoding="utf-8")) != annotation_template(source, frozen["source_digest"]) or (package / "README.md").read_text(encoding="utf-8") != REVIEWER_GUIDE:
        raise EvaluationBlocked("Hướng dẫn/template source-only đã bị đổi.")
    return source, frozen


def validate_claim(case: SourceCase, task: str, requirement: SourceRequirement, claim: dict) -> dict:
    keys = {"QUALITY": {"characteristic", "component_ids"}, "INTERACTION": {"source", "target", "mode", "local_transaction"}, "SEPARATION": {"left", "right"}}[task]
    if not isinstance(claim, dict) or set(claim) != {"kind", "quote", "condition", *keys} or claim["kind"] != task:
        raise EvaluationBlocked("Reference claim cần đúng trường theo task, quote và condition rõ ràng.")
    quote, condition = claim["quote"], claim["condition"]
    if not isinstance(quote, str) or not quote.strip() or quote not in requirement.text:
        raise EvaluationBlocked("Reference quote cần nguyên văn trong đúng source.")
    if condition is not None and (not isinstance(condition, str) or not condition.strip() or condition not in quote):
        raise EvaluationBlocked("Condition cần nguyên văn trong quote, hoặc null.")
    catalog = {item.id for item in case.components}
    if task == "QUALITY":
        item = QualityAllocation(characteristic=claim["characteristic"], component_ids=claim["component_ids"], source_quote=quote)
        if len(set(item.component_ids)) != len(item.component_ids) or not set(item.component_ids) <= catalog:
            raise EvaluationBlocked("Owner IDs ngoài catalog hoặc trùng.")
    elif task == "INTERACTION":
        item = Interaction(**{key: claim[key] for key in keys}, basis=quote)
        if type(claim["local_transaction"]) is not bool or item.source == item.target or not {item.source, item.target} <= catalog:
            raise EvaluationBlocked("Reference interaction cần hai endpoint hợp lệ và boolean transaction.")
    else:
        item = SeparatePair(**{key: claim[key] for key in keys}, basis=quote)
        if item.left == item.right or not {item.left, item.right} <= catalog:
            raise EvaluationBlocked("Reference separation cần hai endpoint hợp lệ.")
    return claim


def claim_links(unit: str, claim: dict) -> set[tuple]:
    context = unit, claim["condition"]
    if claim["kind"] == "QUALITY":
        return {(*context, claim["characteristic"], owner) for owner in claim["component_ids"]}
    if claim["kind"] == "INTERACTION":
        return {(*context, claim["source"], claim["target"], claim["mode"], claim["local_transaction"])}
    return {(*context, *sorted((claim["left"], claim["right"])))}


def validate_rows(source: StudySource, rows: list[dict]) -> list[dict]:
    units = source_units(source)
    if not isinstance(rows, list) or len(rows) != len(units) or any(not isinstance(r, dict) or set(r) != {"unit", "status", "claims", "rationale"} for r in rows):
        raise EvaluationBlocked("Mỗi unit cần đúng một row với status/claims/rationale.")
    if {r["unit"] for r in rows} != set(units):
        raise EvaluationBlocked("Unit thiếu, thừa hoặc trùng.")
    normalized = []
    for row in rows:
        if row["status"] not in {"COMPLETE", "UNRESOLVED"} or not isinstance(row["rationale"], str) or not row["rationale"].strip() or not isinstance(row["claims"], list):
            raise EvaluationBlocked("Chưa annotate hoặc thiếu rationale.")
        if row["status"] == "UNRESOLVED" and row["claims"]:
            raise EvaluationBlocked("UNRESOLVED không trở thành nhãn âm hoặc claim đã xác nhận.")
        links = set()
        for claim in row["claims"]:
            validate_claim(*units[row["unit"]], claim)
            additions = claim_links(row["unit"], claim)
            if links & additions:
                raise EvaluationBlocked("Reference atomic link trùng; hợp nhất hoặc làm rõ condition.")
            links.update(additions)
        normalized.append(row)
    return sorted(normalized, key=lambda row: row["unit"])


def lock_annotation(source: StudySource, frozen: dict, submission: dict, *, locked_at=None) -> dict:
    keys = {"protocol", "package_digest", "annotator_id", "provenance", "source_only_attested", "no_prior_model_output_exposure", "independent_of_other_annotators", "completed_at", "rows"}
    if not isinstance(submission, dict) or set(submission) != keys or submission.get("protocol") != PROTOCOL or submission.get("package_digest") != frozen["source_digest"]:
        raise EvaluationBlocked("Annotation không gắn đúng source/protocol.")
    if submission.get("provenance") != "HUMAN_SOURCE_ONLY" or any(submission.get(k) is not True for k in ("source_only_attested", "no_prior_model_output_exposure", "independent_of_other_annotators")):
        raise EvaluationBlocked("Cần annotation source-only do người review độc lập; fixture/agent không đủ điều kiện.")
    if not isinstance(submission["annotator_id"], str) or not submission["annotator_id"].strip():
        raise EvaluationBlocked("Thiếu annotator ID tự khai báo.")
    locked = locked_at or now()
    if not timestamp(frozen["recorded_at"]) <= timestamp(submission["completed_at"]) <= timestamp(locked):
        raise EvaluationBlocked("Annotation cần hoàn tất sau freeze và trước lock.")
    result = {"protocol": PROTOCOL, "study_digest": frozen["study_digest"], "locked_at": locked,
              "identity_status": "SELF_REPORTED_NOT_AUTHENTICATED", "submission": {**submission, "rows": validate_rows(source, submission["rows"])}}
    result["lock_digest"] = digest(result)
    return result


def verify_annotation(source, frozen, locked):
    if not isinstance(locked, dict) or lock_annotation(source, frozen, locked.get("submission"), locked_at=locked.get("locked_at")) != locked:
        raise EvaluationBlocked("Annotation lock đã đổi hoặc không khớp study.")


def adjudicate(source: StudySource, frozen: dict, locks: list[dict], submission: dict, *, locked_at=None) -> dict:
    if not isinstance(locks, list) or len(locks) != 2:
        raise EvaluationBlocked("Cần hai annotation lock độc lập.")
    for lock in locks:
        verify_annotation(source, frozen, lock)
    annotators = [lock["submission"]["annotator_id"].strip() for lock in locks]
    if len(set(annotators)) != 2:
        raise EvaluationBlocked("Hai annotator phải khác nhau.")
    keys = {"protocol", "package_digest", "adjudicator_id", "provenance", "no_model_output_exposure", "completed_at", "rows"}
    if not isinstance(submission, dict) or set(submission) != keys or submission.get("protocol") != PROTOCOL or submission.get("package_digest") != frozen["source_digest"]:
        raise EvaluationBlocked("Adjudication không gắn đúng source/protocol.")
    actor = submission.get("adjudicator_id")
    if not isinstance(actor, str) or not actor.strip() or submission.get("provenance") != "HUMAN_SOURCE_ONLY" or submission.get("no_model_output_exposure") is not True:
        raise EvaluationBlocked("Adjudicator cần độc lập với model output; không dùng fixture làm reference.")
    locked = locked_at or now()
    if not max(timestamp(item["locked_at"]) for item in locks) <= timestamp(submission["completed_at"]) <= timestamp(locked):
        raise EvaluationBlocked("Adjudication cần sau hai lock và trước reference lock.")
    result = {"protocol": PROTOCOL, "study_digest": frozen["study_digest"], "locked_at": locked,
              "annotation_locks": locks, "submission": {**submission, "rows": validate_rows(source, submission["rows"])},
              "identity_status": "SELF_REPORTED_NOT_AUTHENTICATED"}
    result["reference_digest"] = digest(result)
    return result


def verify_reference(source, frozen, reference, *, before=None):
    if not isinstance(reference, dict) or adjudicate(source, frozen, reference.get("annotation_locks"), reference.get("submission"), locked_at=reference.get("locked_at")) != reference:
        raise EvaluationBlocked("Reference lock đã đổi hoặc thiếu annotation độc lập/adjudication.")
    if before is not None and timestamp(reference["locked_at"]) > timestamp(before):
        raise EvaluationBlocked("Reference phải khóa trước inference; không tạo nhãn sau khi xem output.")
    units = source_units(source)
    if not any(row["status"] == "COMPLETE" and units[row["unit"]][0].split == "HELD_OUT" for row in reference["submission"]["rows"]):
        raise EvaluationBlocked("Reference chưa có unit held-out COMPLETE; UNKNOWN không thay nhãn âm.")
