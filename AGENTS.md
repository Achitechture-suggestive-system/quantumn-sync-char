# Hướng dẫn cho agent kỹ thuật

## Phạm vi và bảo toàn dữ liệu

- Tiếp tục MVP EQCR + QAME hiện có; không viết lại ứng dụng hoặc âm thầm thay fixture P0 bằng kết quả model.
- Giữ main ổn định cho demo. Phát triển P1 trên feat/p1-semantic-validation.
- Không xóa runs/, snapshots, lịch sử review hay thay đổi cục bộ. Không stage runs hàng loạt.
- Không đưa .venv, thông tin xác thực, .env, cache, log, ZIP/export sinh ra hoặc artifact trình duyệt vào Git.

## Cách diễn đạt bằng chứng

Phân biệt nguồn dữ liệu, provenance, trạng thái review, kiểm tra cấu trúc, xác nhận ngữ nghĩa và đo lường thực nghiệm. SOURCE_BACKED chỉ nói rằng reference/span đã được ánh xạ; không chứng minh cách diễn giải đúng. APPROVED ghi nhận quyết định của người review; không phải thử nghiệm. Giữ UNKNOWN, UNRESOLVED, NOT_MEASURED và INSUFFICIENT_EVIDENCE đúng theo trường dữ liệu.

Không tuyên bố precision/recall khi thiếu labels độc lập, deployability khi thiếu bằng chứng vận hành, hoặc quality PASS khi chưa đo. Không tự nới hard constraints.

## Quy trình thay đổi

Đọc file này, docs/00_START_HERE.md, mã nguồn và tests liên quan. Với mỗi milestone: implement → test → cập nhật docs/bằng chứng → xem staged diff và quét secret → stage đường dẫn cụ thể → Conventional Commit → push không force → xác minh SHA/ref/CI. Ghi changelog và publish log trong commit tài liệu kế tiếp, không điền trước SHA chưa tồn tại. Không dùng force push, git reset --hard, sửa lịch sử hoặc git add ..

## Lệnh PowerShell

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py eqcr
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ollama là tùy chọn; tests xác định không yêu cầu daemon hay credential. Chỉ ghi nhận inference chạy thật khi đã gọi model cục bộ thực tế.

Optimizer hiện tại là enumerator Python cổ điển/exhaustive; NetworkX dùng cho graph. “Quantum” là tên đơn vị ứng viên, không phải quantum computing. P2 schema hỗ trợ tối đa R1–R8 do exact partition enumerator. Boundaries, interactions và quality profiles là ứng viên cần review, không phải sự thật production.
