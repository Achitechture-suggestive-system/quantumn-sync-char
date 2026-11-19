# Quantum Studio · EQCR + QAME

Quantum Studio nhận component, characteristics, quan hệ Sync/Async và kho dữ liệu. App đề xuất các cách chia Quantum, vẽ hai phương án cạnh nhau, tính trade-off và ghi quyết định khi người review chọn phương án.

## Chạy nhanh (Windows / PowerShell)

Yêu cầu Python 3.11 trở lên:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Mở URL cục bộ mà Streamlit in ra. Màn đầu hiển thị mẫu Ticket Support. Bấm **Phân tích Quantum** để xem hai cách chia, đổi ưu tiên trên màn so sánh và ghi quyết định trong **Human Review**. Xem [cách tính và kịch bản demo](docs/demo/QUANTUM_STUDIO.md).

## Chạy giao diện nghiên cứu lưu trữ

PetClinic, Tutor Support và các walkthrough nghiên cứu dùng entrypoint lưu trữ `research_app.py`.

```powershell
.\.venv\Scripts\python.exe -m streamlit run research_app.py --server.port 8502
```

- **Xác định/offline:** nạp fixture PRECOMPUTED tại eqcr/fixture.py và chạy pipeline cục bộ. Cùng đầu vào và revisions sẽ tạo cùng kết quả.
- **JSON có cấu trúc:** tải template, cung cấp raw_requirements, responsibilities, evidence và constraints; ứng dụng kiểm tra schema, tham chiếu và source spans. Các ý nghĩa vẫn cần review.
- **Tutor Exploratory Demo (unblinded):** chỉ mở sau khi người vận hành xác nhận unblinded; proposals chưa vào optimizer trước Human Review, run lưu dưới `runs/demo-unblinded/` và luôn `EXCLUDED_FROM_BLIND_RESEARCH`. Mode này không thay thế P2 blind experiment.
- **Tutor Blind Research:** vẫn lock-first, cần source-only annotation độc lập hợp lệ; thiếu lock thì model proposals bị khóa.
- **Ollama tùy chọn:** tạo đề xuất JSON cục bộ, kiểm tra schema rồi ánh xạ ID được trích dẫn vào spans chính xác của đầu vào. Mọi đề xuất vẫn REVIEW_REQUIRED; span khớp không đồng nghĩa ngữ nghĩa được duyệt.

Luồng offline không cần Ollama. Để dùng model-assisted mode, chạy Ollama và cài model cục bộ như qwen3:4b; sau đó chọn **Check local Ollama models** trong UI.

## Kết quả kiểm tra đã chạy

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py research_app.py eqcr tests
```

P0 baseline được kiểm tra ngày 14/11/2026: 30 test pass; compileall, Streamlit AppTest và HTTP smoke cục bộ pass. Nhánh P1 có 44 test pass. Feature branch gần nhất đạt 138 test pass, compileall và AppTest; xem [P2 validation](docs/p2/P2_VALIDATION_REPORT.md), [P2 human worksheet](docs/p2/HUMAN_REVIEW_WORKSHEET.md) và [demo acceptance matrix](docs/demo/DEMO_ACCEPTANCE_MATRIX.md). Đây là kiểm tra code/fixture; không tự xác nhận semantic hoặc chất lượng kiến trúc. P2 blind case vẫn chờ independent annotation lock.

## Tài liệu

[Đọc từ đây](docs/00_START_HERE.md) · [Vấn đề và phạm vi nghiên cứu](docs/01_RESEARCH_PROBLEM_AND_SCOPE.md) · [Pipeline 10 bước](docs/02_PIPELINE_01_TO_10.md) · [Kiến trúc và luồng dữ liệu](docs/03_ARCHITECTURE_AND_DATA_FLOW.md) · [Schema và truy vết](docs/04_DATA_SCHEMAS_AND_TRACEABILITY.md) · [Kiểm tra và giới hạn](docs/05_VALIDATION_AND_RESEARCH_LIMITS.md) · [Human-in-the-loop](docs/06_HUMAN_IN_THE_LOOP.md) · [Giải thích PetClinic](docs/07_CURRENT_SYSTEM_EXPLAINED_VI.md) · [P2 Tutor Support](docs/p2/NEW_CASE_STUDY.md) · [P1 semantic evaluation](docs/verification/P1_SEMANTIC_EVALUATION.md) · [P2 validation](docs/p2/P2_VALIDATION_REPORT.md) · [Lộ trình](docs/09_ROADMAP_AND_BACKLOG.md) · [Changelog](docs/development/CHANGELOG.md) · [Nhật ký GitHub](docs/development/GITHUB_PUBLISH_LOG.md).

Hướng dẫn và giới hạn riêng cho [Tutor exploratory demo](docs/demo/TUTOR_EXPLORATORY_DEMO_WALKTHROUGH.md), [logic pipeline tiếng Việt](docs/demo/CURRENT_MVP_LOGIC_VI.md), [so sánh demo với nghiên cứu mù](docs/demo/DEMO_VS_BLIND_RESEARCH.md), [kết quả E2E](docs/demo/TUTOR_E2E_DEMO_RESULT.md) và [acceptance matrix](docs/demo/DEMO_ACCEPTANCE_MATRIX.md).

## Giới hạn cần trình bày cùng demo

Với fixture, Bell(6)=203; có mười phân hoạch đạt chi phí nhỏ nhất bằng không. Đây là kết quả liệt kê theo các constraint được cấu hình, không chứng minh boundary nào là kiến trúc tốt. Pet–Visit vẫn UNRESOLVED; Sync/Async là giả thuyết có điều kiện; Owner Search là NOT_MEASURED; Pet–Visit là INSUFFICIENT_EVIDENCE. LLM không tự xác minh ngữ nghĩa đề xuất.
