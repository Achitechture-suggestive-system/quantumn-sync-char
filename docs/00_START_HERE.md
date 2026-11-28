# 00 — Bắt đầu tại đây

Tài liệu này hướng dẫn đọc những gì checkout hiện thực sự triển khai. [README](../README.md) có quickstart; [AGENTS.md](../AGENTS.md) nêu quy tắc thay đổi.

Giao diện mặc định là Quantum Studio. Xem [pipeline và kịch bản Ticket Support](demo/QUANTUM_STUDIO.md) để chạy từ component đến Human Review và trade-off. Phần đọc bên dưới mô tả pipeline nghiên cứu lưu trữ.

Rà soát hiện tại của Studio, các phép đối chứng và hướng nghiên cứu nằm trong [gap analysis ngày 26/11/2026](research/STUDIO_GAP_ANALYSIS_2026-11-26.md).

[Tiến độ từng gap](research/STUDIO_COMPLETION_STATUS.md), [bảng đối chiếu nguồn](research/STUDIO_SOURCE_LEDGER.md), [quality scenario có điều kiện](research/STUDIO_QUALITY_SCENARIOS.md) và [hợp đồng boundary/ownership cùng probe cục bộ](research/STUDIO_BOUNDARY_EVIDENCE.md) ghi các mốc triển khai tiếp theo và giới hạn đã kiểm tra.

[Review mệnh đề, phủ định và vai trò component](research/STUDIO_CLAUSE_REVIEW.md) mô tả prompt @2, các guard, proposal do reviewer bổ sung và phản hồi Ollama còn lỗi đã quan sát; không coi structured output là semantic accuracy.

[Backend Studio 9–50 component](research/STUDIO_LARGE_BACKEND.md) ghi mã hóa bảo toàn năm trục, giới hạn thời gian, sửa xung đột có bảo vệ và benchmark tổng hợp. Các số lượng/Pareto cỡ lớn chỉ nói về tập đã tìm.

[Báo cáo phản hồi LLM hiện có](research/STUDIO_LLM_OUTPUT_EVALUATION.md) đối chiếu bảy run thật, 12 proposal, citation, lỗi nghĩa và tác động sau correction; không có semantic accuracy khi thiếu nhãn độc lập.

[Protocol đánh giá extraction Studio](research/STUDIO_EVALUATION_PROTOCOL.md) mô tả source-only package, hai annotation độc lập và adjudication trước inference, request/code freeze, repetition và matching theo atomic link. Bộ nguồn mới chưa có reference hoặc inference.

## Thứ tự đọc

1. [Bài toán và phạm vi RQ1–RQ4](01_RESEARCH_PROBLEM_AND_SCOPE.md)
2. [Pipeline thực tế 01–10](02_PIPELINE_01_TO_10.md)
3. [Kiến trúc/luồng dữ liệu](03_ARCHITECTURE_AND_DATA_FLOW.md) và [schema/truy vết](04_DATA_SCHEMAS_AND_TRACEABILITY.md)
4. [Validation và giới hạn](05_VALIDATION_AND_RESEARCH_LIMITS.md)
5. [Human-in-the-loop](06_HUMAN_IN_THE_LOOP.md) và [giải thích PetClinic](07_CURRENT_SYSTEM_EXPLAINED_VI.md)
6. [Kịch bản demo offline năm phút](08_MVP_DEMO_SCRIPT.md)
7. [Roadmap](09_ROADMAP_AND_BACKLOG.md), [P0 verification](verification/P0_BASELINE_VERIFICATION.md), [P1 semantic evaluation](verification/P1_SEMANTIC_EVALUATION.md), changelog và publish log.
8. [P2 Tutor Support case](p2/NEW_CASE_STUDY.md), [source-only blind annotation](p2/P2_BLIND_ANNOTATION.md), [post-lock model review](p2/P2_MODEL_REVIEW.md), [Ollama-to-Quantum audit](p2/INPUT_TO_QUANTUM_TRACE.md), [P2.1 reviewer package](p2/SOURCE_ONLY_REVIEWER_GUIDE.md), [lock validator](p2/ANNOTATION_LOCK_VALIDATION.md), [actual experiment protocol](p2/ACTUAL_EXPERIMENT_PROTOCOL.md), [experiment status](p2/ACTUAL_TUTOR_EXPERIMENT.md), [before/after causal trace](p2/BEFORE_AFTER_CAUSAL_TRACE.md), [validity report](p2/P2_RESEARCH_VALIDITY_REPORT.md), và [research limitations](p2/P2_RESEARCH_LIMITATIONS.md). Worksheet tương thích nằm ở [HUMAN_REVIEW_WORKSHEET.md](p2/HUMAN_REVIEW_WORKSHEET.md) và [P2_MODEL_REVIEW_WORKSHEET.md](p2/P2_MODEL_REVIEW_WORKSHEET.md); trạng thái case thật nằm trong [P2 validation report](p2/P2_VALIDATION_REPORT.md).
9. [Repository capability audit](research/REPOSITORY_CAPABILITY_AUDIT.md), [pipeline gap matrix](research/PIPELINE_GAP_MATRIX.md), [P7 optimizer](research/PARTITION_OPTIMIZATION.md), [P8 graph/export](research/ARCHITECTURE_GRAPH_EXPORT.md), [interaction contracts](research/INTERACTION_CONTRACTS.md), [P9 QAME scenarios](research/QAME_SIX_PART_SCENARIOS.md), [P11 evaluation tracks](research/EVALUATION_TRACKS.md), [reproducibility bundle](research/REPRODUCIBILITY_BUNDLE.md), [final completion report](research/FINAL_RESEARCH_COMPLETION_REPORT.md) và [research-grade implementation plan](research/IMPLEMENTATION_PLAN.md) ghi trạng thái đã kiểm tra cho P0–P11; đây là audit snapshot, không phải claim hoàn tất research.
10. [Tutor exploratory demo walkthrough](demo/TUTOR_EXPLORATORY_DEMO_WALKTHROUGH.md), [MVP logic tiếng Việt](demo/CURRENT_MVP_LOGIC_VI.md), [demo so với blind research](demo/DEMO_VS_BLIND_RESEARCH.md), [E2E demo result](demo/TUTOR_E2E_DEMO_RESULT.md) và [acceptance matrix](demo/DEMO_ACCEPTANCE_MATRIX.md). Demo không được nạp như evidence cho blind P2.

## Chạy luồng xác định

Trong PowerShell tại thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -m streamlit run research_app.py --server.port 8502
```

Nạp **PetClinic demo data** rồi chạy fixture offline. Ollama không bắt buộc. Cách cài môi trường nằm trong README.

## Kết quả tham chiếu

Đầu vào gồm C0, sáu FR, workflow dạng tường thuật, hai quality scenarios, sáu responsibility PRECOMPUTED và H1–H3 dạng what-if. Baseline: 203 phân hoạch được liệt kê, 10 đồng tối ưu với J=0, status REVIEW_REQUIRED. Thêm H4=MUST_LINK(R4,R6) khi H3 còn hiệu lực tạo 0 phương án khả thi và INFEASIBLE. Tắt H3 tạo 5 phương án khả thi/tối ưu, status REVIEW_REQUIRED.

Các con số là hành vi của fixture và constraint đã nhập, không phải kết luận về PetClinic thực tế. Runs thô được giữ local và loại khỏi Git; có thể tái tạo từ fixture.
