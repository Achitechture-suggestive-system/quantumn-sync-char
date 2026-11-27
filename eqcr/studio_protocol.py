"""Explicit reference protocol; free-text contracts are never treated as executable specifications."""

VERSION = "OUTBOX_INBOX_V1"
TIMEOUT_SECONDS = 0.3
MAX_ATTEMPTS = 3


def reference_fields(mode: str) -> dict[str, str]:
    if mode not in {"SYNC", "ASYNC"}:
        raise ValueError("Reference protocol needs SYNC or ASYNC.")
    return {
        "operation": "APPLY_EVENT: persist one generic effect for an event_id; prepared reference operation, no domain logic",
        "data_dependency": "Separate producer and receiver SQLite files; no shared domain store",
        "request_fields": "v=1, event_id string of 1..100 characters, value signed 32-bit integer (not boolean)",
        "response_fields": ("202 means producer command and outbox committed; receiver completion is separate"
                            if mode == "ASYNC" else "200 means receiver effect committed before caller response; unavailable returns 503"),
        "versioning": "Envelope v=1 only; unsupported version returns 400",
        "consistency": "One committed generic effect per event_id in one receiver database; no cross-service atomicity",
        "latency_budget": "NOT_BENCHMARKED; configured 300 ms timeout per receiver attempt, no end-to-end SLO claim",
        "failure_handling": ("Durable outbox survives process restart; explicit dispatch after recovery, no automatic delivery guarantee"
                             if mode == "ASYNC" else "503 after bounded delivery attempts; a timed-out effect may already have committed"),
        "retry_policy": "At most 3 immediate attempts per invocation; caller/operator must trigger later redelivery",
        "timeout_policy": "300 ms per receiver HTTP attempt; no end-to-end deadline or cancellation guarantee",
        "idempotency_policy": "event_id and canonical payload stored with effect in one receiver transaction; same ID/different payload returns 409",
    }


def protocol_issues(review) -> list[str]:
    if review.reference_protocol != VERSION:
        return ["Chưa chọn reference protocol thực thi; hợp đồng tự do chưa có harness tương ứng."]
    if review.contract.selected_mode not in {"SYNC", "ASYNC"}:
        return ["Reference protocol cần hợp đồng đã duyệt mode."]
    if review.data_scope != "NONE" or review.store_ids:
        return ["Reference protocol chỉ kiểm hai kho SQLite riêng, chưa kiểm kho nghiệp vụ dùng chung."]
    if any(getattr(review.contract, key) != value for key, value in reference_fields(review.contract.selected_mode).items()):
        return ["Nội dung hợp đồng khác reference protocol; cần harness riêng cho thay đổi này."]
    return []
