# EQCR + QAME — MVP chạy cục bộ

MVP nghiên cứu chạy cục bộ, chuyển requirements chức năng/phi chức năng, workflow và quality scenarios thành các Architectural Quantum ứng viên có thể truy vết, giả thuyết tương tác và Quantum Quality Profiles.

> **Phạm vi demo:** mini-case PetClinic đóng băng với sáu responsibilities, chế độ xác định offline và đề xuất tùy chọn qua Ollama. Đây không phải bộ khuyến nghị kiến trúc tổng quát, không chọn architectural style, không chứng minh deployability, hiệu năng hay độ chính xác ngữ nghĩa.

## Chạy nhanh (Windows / PowerShell)

Yêu cầu Python 3.11 trở lên:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Mở URL cục bộ mà Streamlit in ra. Nếu đã có môi trường ảo:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Các chế độ

- **Xác định/offline:** nạp fixture PRECOMPUTED tại eqcr/fixture.py và chạy pipeline cục bộ. Cùng đầu vào và revisions sẽ tạo cùng kết quả.
- **JSON có cấu trúc:** tải template, cung cấp raw_requirements, responsibilities, evidence và constraints; ứng dụng kiểm tra schema, tham chiếu và source spans. Các ý nghĩa vẫn cần review.
- **Ollama tùy chọn:** tạo đề xuất JSON cục bộ, kiểm tra schema rồi ánh xạ ID được trích dẫn vào spans chính xác của đầu vào. Mọi đề xuất vẫn REVIEW_REQUIRED; span khớp không đồng nghĩa ngữ nghĩa được duyệt.

Luồng offline không cần Ollama. Để dùng model-assisted mode, chạy Ollama và cài model cục bộ như qwen3:4b; sau đó chọn **Check local Ollama models** trong UI.

## Kết quả kiểm tra đã chạy

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py eqcr
```

P0 baseline được kiểm tra ngày 14/11/2026: 30 test pass; compileall, Streamlit AppTest và HTTP smoke cục bộ pass. Nhánh P1 hiện có 44 test pass, compileall và AppTest pass; xem [P1 evaluation](docs/verification/P1_SEMANTIC_EVALUATION.md) để biết oracle, Ollama run và giới hạn. Đây là kiểm tra cấu trúc/chạy cục bộ, không phải xác minh semantic hoặc chất lượng kiến trúc.

## Tài liệu

[Đọc từ đây](docs/00_START_HERE.md) · [Vấn đề và phạm vi nghiên cứu](docs/01_RESEARCH_PROBLEM_AND_SCOPE.md) · [Pipeline 10 bước](docs/02_PIPELINE_01_TO_10.md) · [Kiến trúc và luồng dữ liệu](docs/03_ARCHITECTURE_AND_DATA_FLOW.md) · [Schema và truy vết](docs/04_DATA_SCHEMAS_AND_TRACEABILITY.md) · [Kiểm tra và giới hạn](docs/05_VALIDATION_AND_RESEARCH_LIMITS.md) · [Human-in-the-loop](docs/06_HUMAN_IN_THE_LOOP.md) · [Giải thích PetClinic](docs/07_CURRENT_SYSTEM_EXPLAINED_VI.md) · [Kịch bản demo offline](docs/08_MVP_DEMO_SCRIPT.md) · [P1 semantic evaluation](docs/verification/P1_SEMANTIC_EVALUATION.md) · [Lộ trình](docs/09_ROADMAP_AND_BACKLOG.md) · [Changelog](docs/development/CHANGELOG.md) · [Nhật ký GitHub](docs/development/GITHUB_PUBLISH_LOG.md).

## Giới hạn cần trình bày cùng demo

Với fixture, Bell(6)=203; có mười phân hoạch đạt chi phí nhỏ nhất bằng không. Đây là kết quả liệt kê theo các constraint được cấu hình, không chứng minh boundary nào là kiến trúc tốt. Pet–Visit vẫn UNRESOLVED; Sync/Async là giả thuyết có điều kiện; Owner Search là NOT_MEASURED; Pet–Visit là INSUFFICIENT_EVIDENCE. LLM không tự xác minh ngữ nghĩa đề xuất.
