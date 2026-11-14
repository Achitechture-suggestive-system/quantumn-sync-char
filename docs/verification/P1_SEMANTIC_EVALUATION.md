# Báo cáo P1 — kiểm tra semantics, provenance và oracle

- Ngày chạy: 14/11/2026
- Nhánh: `feat/p1-semantic-validation`
- Commit P1: `f14b534`; push status được ghi trong GitHub publish log.
- CI workflow commit: `8b9cf21`; first GitHub Actions run `43609423803` passed.
- Runner pin commit: `cd583c7` uses Ubuntu 24.04.

## Phạm vi

P1 bổ sung kiểm tra chéo độc lập cho enumerator, negative tests cho dữ liệu cấu trúc/citation, provenance graph hiển thị trong UI, model-proposed evidence provenance, và bộ input tổng hợp được gắn nhãn. Mục tiêu là kiểm tra sự nhất quán của luồng dữ liệu và những tham chiếu đã khai báo. Đây không phải nhãn chuyên gia hay phép đo semantic accuracy.

## Bằng chứng chạy được

| Kiểm tra | Lệnh/cách chạy | Kết quả quan sát |
|---|---|---|
| Regression + P1 tests | `.venv\Scripts\python.exe -m pytest -q` | **44 passed in 1.27s** sau khi sửa biểu diễn `context:C0` và concept ngoài input scope trong graph. |
| Biên dịch | `.venv\Scripts\python.exe -m compileall -q app.py eqcr tests` | Exit 0. |
| Streamlit AppTest | `AppTest.from_file('app.py', default_timeout=30).run()` | `exceptions=0`, không có UI warning; trang khởi tạo fixture. |
| Streamlit localhost | Process từ checkout hiện tại trên `127.0.0.1:8766`; GET `/_stcore/health` và `/` | Cả hai HTTP 200; health body `ok`. |
| GitHub Actions | [Run 43609423803](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43609423803) trên SHA `8b9cf21066453f048bc78f29133061cf40281d83` | PASS; `44 passed in 1.19s`, compileall thành công. |
| GitHub Actions, runner cố định | [Run 43609850489](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43609850489) trên SHA `cd583c7939e07bf6d098ab2c252ec57d4aa47702` | PASS trên Ubuntu 24.04; `44 passed in 0.65s`, compileall thành công. |
| Live local Ollama proposal | `qwen3:4b`, prompt `petclinic-context-responsibility-evidence-boundary-v5` | Hoàn tất; sáu responsibility proposals, sáu normalized requirement refs, một evidence proposal, một boundary hypothesis; source spans chính xác; bundle và mọi proposal REVIEW_REQUIRED. |

AppTest được chạy trong môi trường Python 3.13.13 với Streamlit 1.67.0 và Pydantic 2.14.3. Live Ollama là quan sát một lần trong môi trường local đã cài model; bộ test tự động không phụ thuộc Ollama.

## Oracle partition độc lập

`tests/test_partition_oracle.py` tạo phép gán label cho sáu phần tử bằng `itertools.product`, rồi canonicalize các block tương đương. Oracle không gọi `_partitions` hoặc helper private từ `eqcr.pipeline`. Mỗi constraint được đánh giá lại trong test theo quan hệ MUST_LINK/CANNOT_LINK, hardness và weight.

| Ca | Oracle độc lập | Pipeline | Kết luận trong phạm vi test |
|---|---:|---:|---|
| Toàn bộ partitions cho n=6 | 203 | 203 enumerated | Số lượng khớp Bell(6). |
| Fixture ban đầu | 10 optimum, J=0 | 10 optimum, J=0 | Tập signature của partition tối ưu bằng nhau. |
| Thêm H4 MUST_LINK(R4,R6), H3 CANNOT_LINK còn bật | 0 feasible | 0 feasible, `INFEASIBLE` | Xung đột được phát hiện. |
| Tắt H3 trong ca trên | 5 feasible/optimal | 5 feasible/optimal, `REVIEW_REQUIRED` | Hard feasibility được phục hồi; không có claim kiến trúc được duyệt. |

Oracle và production đều là Python chạy trên cùng fixture; đây là cross-check độc lập ở mức triển khai thuật toán nhỏ, không phải proof formal hay đánh giá objective có đại diện cho chất lượng kiến trúc hay không.

## Kiểm tra negative và provenance

Test cases từ chối trách nhiệm không có FR/citation, quote không khớp, evidence PRESENT không có source/assumption, citation tới source ngoài package, constraint trỏ tới responsibility không tồn tại, JSON sai cú pháp/UTF-8/top-level type không phải object. JSON hợp lệ được giải mã riêng trước package validation.

Graph kiểm endpoint/node IDs, requirement-to-responsibility links, citations, evidence review-state, constraint endpoints và explicit evidence links, candidate membership, workflow mapping gaps và unresolved reference issues. Context C0 là node input riêng; evidence `SCOPED_ABSENT` trỏ tới runtime topology được ghi thành concept ngoài scope. Constraint H1–H3 vẫn được ghi `NO_EXPLICIT_EVIDENCE_LINK`; rationale/source của what-if không được nhầm thành evidence link.

Human approval test cập nhật review-state/graph nhưng status tổng thể còn `REVIEW_REQUIRED`; Owner Search vẫn `NOT_MEASURED`. LLM proposal test xác nhận `MODEL_PROPOSED`, evidence proposals và boundary hypotheses vẫn `REVIEW_REQUIRED`.

## LLM-assisted run quan sát

- Model: `qwen3:4b`
- Prompt: `petclinic-context-responsibility-evidence-boundary-v5`
Kết quả: `bundle_status=REVIEW_REQUIRED`, `citations_resolve_to_exact_input_spans=True`, `all_semantics_remain_review_required=True`, `can_apply_to_fixture=True`.

`can_apply_to_fixture=True` chỉ nói bundle vượt điều kiện kỹ thuật để ghép vào fixture. Nó không phải semantic acceptance. Không có expert annotations, adjudication, precision/recall, boundary correctness score hay measurement kiến trúc trong run này.

## Synthetic fixture

`tests/fixtures/synthetic_tool_checkout_case.json` là ví dụ hư cấu về workshop cho mượn dụng cụ. Nó mang nhãn `SYNTHETIC_TEST_FIXTURE`; test hiện dùng để xác nhận schema/source spans/nội dung workflow, không chạy như package end-to-end vì hiện chưa có bộ responsibilities/evidence/constraints tương ứng. Không trộn fixture này với case PetClinic hoặc trình bày như validation thực tế.

## Giới hạn còn lại

- Traceability PASS kiểm tra cấu trúc liên kết; không đánh giá entailment hay tính đúng của diễn giải.
- Ollama run là một mẫu quan sát, không đo độ chính xác model.
- UI/Pipeline case study vẫn neo một số quy tắc allocation vào scenario/responsibility ID PetClinic; input tổng hợp không thay thế demo PetClinic.
- Cần reviewer độc lập gán nhãn và adjudicate để tính semantic metrics; cần runtime/load-test evidence để đánh giá quality target.
- GitHub CI xác nhận test/compile trên Ubuntu 24.04; không gọi Ollama. Localhost smoke chỉ xác nhận server local trả trang và health endpoint trong phiên kiểm tra, không phải deployment test.
