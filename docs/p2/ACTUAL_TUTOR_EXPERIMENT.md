# P2.1 — Trạng thái thí nghiệm Tutor Support

## Kết quả trạng thái hiện tại — 2026-11-19

| Thành phần | Trạng thái | Nguồn bằng chứng |
|---|---|---|
| Case requirements/workflows/scenarios | Đã chuẩn bị: 6 FR, 4 WF, 2 quality scenarios, 12 source IDs/spans | `PREPARED_FIXTURE` trong `eqcr/tutor_support.py`; package source-only có manifest/hashes |
| Source-only reviewer package | Có, 5 file allowlisted; không chứa proposal hoặc downstream outputs | Artifact đã commit sau milestone package; kiểm tra package validator và test |
| Annotation lock do người review | Chưa có | Không tìm thấy lock JSON do reviewer cung cấp trong checkout |
| Ollama `qwen3:4b` khả dụng | Có tag local (ID prefix `359d7dd4bcda`) | `ollama list`, 2026-11-19; chỉ là kiểm tra khả dụng |
| Inference P2 hậu-lock | Chưa chạy | Không có run bundle; không gọi model vì thiếu lock |
| Citation/unsupported/duplicate/ambiguous của inference mới | Chưa thể đánh giá | Không có output inference hậu-lock |
| Human approve/correct/reject/defer cho proposals | Chưa có | Worksheet app chưa chứa quyết định thật |
| Evidence-derived optimizer run | Chưa chạy cho case thật | Test-only pipeline path hiện có không phải case evidence |
| Interaction hypotheses / QAME profiles cho actual reviewed case | Chưa sinh | Chỉ có test-only deterministic coverage; không có actual decisions |
| Before/after human correction | Chưa thực hiện | Không có correction thật; không thay bằng fixture |
| Semantic evaluation | `NOT_MEASURED_NO_ADJUDICATED_REFERENCE` | Không có labels độc lập/adjudication |
| Quality measurement | `NOT_MEASURED` / `INSUFFICIENT_EVIDENCE` | Không có target system và observations |

## Phân loại output đã có

- Source requirements và scenario text là `PREPARED_FIXTURE`; source hash/span xác nhận nội dung package khớp fixture, không chứng minh nguồn ngoài hay tính đại diện.
- Historical Qwen v6 output là `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`, không phải inference P2 đủ điều kiện.
- Proposal/review/evidence/constraint/optimizer/interaction/QAME test results là `P2_TEST_ONLY`.
- Chưa có `LOCAL_OLLAMA_PROPOSAL` hậu-lock hoặc `HUMAN_DECISION` thật trong checkout.

## Kết luận

Trạng thái experiment: `P2_BLOCKED_INDEPENDENT_ANNOTATION`. Khả dụng model và kiểm thử causal code path không trả lời được câu hỏi nghiên cứu trên case mới. Cần reviewer lock từ package source-only trước khi có thể chạy inference thật. Tài liệu này không ghi semantic accuracy score, expert label hoặc output giả lập.

## Demo branch tách biệt

Nhánh `feat/tutor-exploratory-demo` bổ sung exploratory UI để trình diễn model và downstream pipeline không cần blind lock. Bất kỳ live demo output nào cũng là `EXCLUDED_FROM_BLIND_RESEARCH` và được ghi ở `docs/demo/TUTOR_E2E_DEMO_RESULT.md`; nó không thay đổi trạng thái thí nghiệm mù ở trên, không tạo annotation độc lập và không cung cấp gold labels.

## Demo branch tách biệt

Nhánh `feat/tutor-exploratory-demo` bổ sung exploratory UI để có thể trình diễn model và downstream pipeline không cần blind lock. Bất kỳ live demo output nào cũng là `EXCLUDED_FROM_BLIND_RESEARCH` và được ghi ở `docs/demo/TUTOR_E2E_DEMO_RESULT.md`; nó không thay đổi trạng thái thí nghiệm mù ở trên, không tạo annotation độc lập và không cung cấp gold labels.
