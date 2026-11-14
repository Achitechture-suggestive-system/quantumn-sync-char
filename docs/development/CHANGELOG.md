# Changelog

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