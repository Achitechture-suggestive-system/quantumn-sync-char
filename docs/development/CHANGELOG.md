# Changelog

## P2 unseen Tutor Support validation — 2026-11-16

- Added a new source-backed Tutor Support case, live local `qwen3:4b` extraction path, explicit review gate, policy-based evidence constraint derivation, optimizer input tracing, and downstream interaction/quality generation.
- Added the independent human-review worksheet and documented the actual live run, proposal limitations, provenance, and test-only before/after revision path. The actual case still awaits human decisions; no semantic metric is claimed.
- Verification before publish: 54 tests pass; compileall and staged diff checks pass. Commit `4bbdb03d419ab6b556e3447de0b2130dd3f95fdb` was pushed to `feat/p1-semantic-validation`; GitHub Actions run `43818037929` passed tests and compile.
- The live candidate reached all ten stages, but its evidence proposal was unreviewed and self-referential. The actual case therefore produced zero accepted evidence-derived constraints; see the [P2 validation report](../p2/P2_VALIDATION_REPORT.md) and [review worksheet](../p2/HUMAN_REVIEW_WORKSHEET.md).

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
