# Changelog

## P2 reproducible experiment runner — 2026-11-16

- Bổ sung protocol lock v2 với timestamp timezone-aware và hash integrity cho metadata; ghi rõ identity và việc chưa tiếp xúc model là tự khai báo, không xác minh bên ngoài.
- Thêm CLI preflight để chỉ gọi Ollama khi có source-only lock hợp lệ, checkout sạch, đúng `qwen3:4b`, prompt/schema và metadata model; xuất proposal, structural audit, manifest, checksums và ZIP vào thư mục run mới.
- Structural audit chỉ kiểm tra ID/span, coverage, duplicate và lỗi định dạng; semantic correctness vẫn `NOT_MEASURED` khi thiếu nhãn độc lập. Không chạy inference vì chưa có annotator đủ điều kiện cung cấp lock.
- Verification: 72 tests pass; compileall và `git diff --check` pass; secret scan staged không có match; [GitHub Actions run 43849233685](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43849233685) success. Commit `1fe23ed7886e02b02e44e5ebb850e1b1e6dd6628` đã push và khớp remote branch SHA.

## Research completion capability audit — 2026-11-16

- Audited the actual feature-branch modules, schemas, docs, tests, CI and P0 tag against the research-completion prompt. Added a P0–P11 capability audit, implementation gap matrix and staged implementation plan under `docs/research/`.
- Confirmed the bounded current strengths: P0/P1 local flow and six-role partition oracle; P2 protocol/wiring tests; exhaustive optimizer up to R8; graph JSON, interaction hypotheses, QAME allocation and snapshot ZIP exports.
- Recorded gaps without relabeling them complete: actual independent Tutor experiment, versioned tactic catalog, CP-SAT path, six-part ISO-mapped scenario validation, measurement adapters, integration-layer graph, editable Draw.io, and full reproducibility manifest.
- Verification: relative links in the audit docs resolve; staged diff and secret/path checks pass. Commit `93c7edc06c25d9fd39cdf48355ca31377d5ec8d1` is on `feat/p1-semantic-validation`; [GitHub Actions run 43846206356](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43846206356) passed.

## P2 blind annotation and causal review protocol — 2026-11-16

- Tách source-only annotation khỏi post-lock model review, thêm checkpoint hash/thời gian trước inference, cardinality 0..N cho FR-role mapping, relation registry cố định và action `APPROVE/CORRECT/REJECT/DEFER`.
- Chỉ evidence relation đã qua human review, có implication kiến trúc riêng và responsibility pairs tường minh mới được policy đã khai báo chuyển thành soft optimizer constraint. Business ordering không tự sinh constraint.
- Thêm exact-citation checks, unknown-relation rationale gate, regression coverage, và hai artifact canonical `P2_BLIND_ANNOTATION.md` / `P2_MODEL_REVIEW.md`; giữ `HUMAN_REVIEW_WORKSHEET.md` là lối vào tương thích.
- Verification: 63 tests pass; compileall và staged diff/secret/path checks pass. Commit `1ec2c1b649901873a12cb43dba703bf7a723a411` được push lên `feat/p1-semantic-validation`; [GitHub Actions run 43841700612](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43841700612) success.
- Case study thật vẫn chờ source-only annotation do người review cung cấp, inference `qwen3:4b` sau lock, model-review decisions và revision experiment. Test-only wiring không được trình bày như kết quả LLM; chưa có semantic metric.

## P2 Tutor Support initial prototype (pre-blind protocol) — 2026-11-16

- Added a new source-backed Tutor Support case, live local `qwen3:4b` extraction path, explicit review gate, policy-based evidence constraint derivation, optimizer input tracing, and downstream interaction/quality generation.
- Added the independent human-review worksheet and documented the actual live run, proposal limitations, provenance, and test-only before/after revision path. The actual case still awaits human decisions; no semantic metric is claimed.
- Verification before publish: 54 tests pass; compileall and staged diff checks pass. Commit `4bbdb03d419ab6b556e3447de0b2130dd3f95fdb` was pushed to `feat/p1-semantic-validation`; GitHub Actions run `43818037929` passed tests and compile.
- Historical v6 model output was unblinded and pre-protocol; its self-referential evidence was not accepted and the run produced zero accepted evidence-derived constraints. It is preserved as `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`, not as a blind experiment. See the [P2 validation report](../p2/P2_VALIDATION_REPORT.md) and [source-only blind annotation](../p2/P2_BLIND_ANNOTATION.md).

## P1 semantic-validation branch — 2026-11-14

- Added an independent six-item partition oracle and negative validation tests for citation spans, evidence support, unknown references, and malformed project JSON.
- Added a provenance graph across inputs, model proposals, evidence, constraints, partitions, quality allocations, and human decisions; graph PASS is limited to structural checks.
- Added a labeled synthetic workshop fixture and an empty annotation worksheet; no expert labels or semantic metric claims were added.
- P1 verification: 44 automated tests pass, compileall passes, Streamlit AppTest has zero exceptions; one local qwen3:4b proposal run resolves exact spans and remains REVIEW_REQUIRED. See [P1 evaluation](../verification/P1_SEMANTIC_EVALUATION.md).
- Implementation commit `f14b534` was pushed to `feat/p1-semantic-validation`; GitHub SHA and private visibility are recorded in [publish log](GITHUB_PUBLISH_LOG.md).
- Added a read-only Ubuntu 24.04/Python 3.13 GitHub Actions workflow for pytest and compileall. Runs `43609423803`, `43609612692`, `43609850489`, and final run `43610739439` passed; latest run has 44 tests and compileall green.
- Browser walkthrough verified baseline → H4 conflict → H3 correction, graph refresh, ZIP with traceability/snapshots, and ten-step JSON report. UI status copy now accurately states that a human correction recomputes the full pipeline.

Các mục dưới đây ghi nhận thay đổi đã được kiểm tra, không phải kế hoạch.

## 14/11/2026 — Baseline P0

- Bảo toàn ứng dụng P0, regression tests, tài liệu và quy trình chạy cục bộ.
- Tạo .gitignore an toàn; thêm docs/verification/P0_BASELINE_VERIFICATION.md.
- Bằng chứng: 30 tests pass; compileall, AppTest và HTTP localhost pass; fixture 203/10; xung đột H3/H4 không có nghiệm; tắt H3 còn năm candidate.
- Commit: `3d517b1a39158e539239dc73d594bc0938649feb` — chore: establish verified P0 research MVP baseline.
- Push main và tag p0-demo-2026-11-14 đã xác minh trên repo Private. Xem GITHUB_PUBLISH_LOG.md.
## 14/11/2026 — Tài liệu kỹ thuật tiếng Việt

- Tạo hướng dẫn đọc, phạm vi RQ1–RQ4, giải thích nguồn thực tế của pipeline 10 bước, kiến trúc, schema/provenance, validation, human-in-the-loop, walkthrough PetClinic, demo và roadmap; thêm AGENTS.md.
- Làm README và tài liệu runtime/test/review hiện có nhất quán với code và kết quả P0. Đổi đường dẫn demo sang docs/08_MVP_DEMO_SCRIPT.md.
- Commit: 0dbd90675beb193c92d4fd06bd7ccf4bf95c61f3 — docs: explain implemented ten-step architecture pipeline.
- Kiểm tra: 30 tests pass (1.10s), compileall PASS, AppTest zero exceptions, 21 Markdown files không có relative link hỏng, localhost health/root HTTP 200; staged secret scan không có match.
- Push nhánh main được GitHub xác nhận cùng SHA; CI chưa có workflow.
