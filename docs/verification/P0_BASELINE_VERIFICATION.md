# Xác minh baseline P0 (2026-11-14)

## Phạm vi và nguồn

Đây là kết quả chạy trực tiếp trên checkout `C:\disk D\quantumn-sync-char` ngày 14-11-2026 (giờ Asia/Saigon), trước khi có commit đầu tiên. Nội dung `AGENT_GOAL.md` được cung cấp qua tài liệu đính kèm; không có file `AGENT_GOAL.md` ở gốc checkout. Tài liệu đính kèm là kế hoạch, còn trạng thái dưới đây chỉ ghi nhận những gì đã kiểm tra trong checkout này.

## Môi trường thực tế

| Thành phần | Kết quả |
|---|---|
| Python | 3.13.13 |
| Pydantic | 2.14.3 |
| NetworkX | 3.7 |
| Streamlit | 1.67.0 |
| Graphviz Python package | 0.21 |
| pytest | 8.4.2 |
| Ollama | 0.40.16; model `qwen3:4b` có trong danh sách local sau khi daemon khởi động |
| Dependency declarations | `requirements.txt` dùng version ranges; checkout chưa có lock file |
| Git | Đã khởi tạo; nhánh `main`, chưa có local commit hoặc tag lúc bắt đầu audit |
| GitHub | Remote `origin` trỏ đến repo hiện có. Repo đã được đổi từ PUBLIC sang PRIVATE theo yêu cầu; API trả `private=true`, quyền tài khoản hiện hành `admin=true`, kích thước repo 0 trước baseline push |

`gh auth setup-git` làm Git đọc được remote. `git ls-remote origin` sau đó kết thúc thành công nhưng không liệt kê ref nào: remote chưa có branch/tag để đối chiếu. Không ghi thông tin xác thực vào repo.

## Lệnh và kết quả

| Kiểm tra | Lệnh / cách chạy | Kết quả |
|---|---|---|
| P0 regression suite | `.venv\Scripts\python.exe -m pytest -q` | PASS — `30 passed in 1.56s` |
| Biên dịch Python | `.venv\Scripts\python.exe -m compileall -q app.py eqcr` | PASS |
| Streamlit AppTest | `AppTest.from_file('app.py', default_timeout=30).run()` | PASS — `exceptions=0`; trang hiển thị title và fixture PetClinic |
| Streamlit server smoke | `.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8766` | PASS — server khởi động; `/_stcore/health` HTTP 200, body `ok`; `/` HTTP 200 |
| Deterministic baseline | `run_pipeline(get_fixture())` | 203 phân hoạch được liệt kê; 10 phân hoạch đồng hạng tối ưu với `J=0`; trạng thái `REVIEW_REQUIRED` |
| H3/H4 conflict | Thêm hard `MUST_LINK(R4,R6)` H4 khi H3 đang cấm cặp đó | 0 phân hoạch khả thi; trạng thái `INFEASIBLE`; báo conflict H3/H4 |
| Sửa conflict | Tắt H3, giữ H4 | 5 phân hoạch khả thi và đồng hạng tối ưu; trạng thái `REVIEW_REQUIRED` |
| Secret scan cho baseline | Tìm token/private-key/password/API-key patterns trên source, tests, docs và cấu hình dự định stage | Không có match. Không tìm thấy `gitleaks`, `detect-secrets`, hoặc `trufflehog`; đây là kiểm tra thủ công hẹp, không phải chứng nhận secret-free |

Lệnh kiểm tra các kết quả phân hoạch ở trên gọi implementation `eqcr.pipeline.run_pipeline`; đây không phải oracle độc lập. Oracle độc lập sẽ được bổ sung ở nhánh P1.

## Đánh giá trạng thái

- Regression suite, biên dịch, AppTest và HTTP smoke xác nhận code chạy cục bộ trong môi trường đã ghi.
- Các kết quả 203/10/0/5 xác nhận hành vi enumerator trên fixture và các constraint cụ thể; chúng không xác nhận responsibility semantics hoặc chất lượng kiến trúc.
- Mọi đề xuất semantic tiếp tục `REVIEW_REQUIRED`. Quan hệ Pet–Visit tiếp tục `UNRESOLVED`; Owner Search là `NOT_MEASURED`; scenario Pet–Visit là `INSUFFICIENT_EVIDENCE`.
- Việc kiểm tra HTTP là localhost smoke, không phải kiểm thử triển khai hoặc nhiều người dùng.
- Thư mục `runs/` có 38 run directory cục bộ trước commit. Các raw run, snapshot và export không nằm trong baseline; `.gitignore` loại chúng khỏi Git nhưng không xóa dữ liệu.
- Tại thời điểm ghi report, GitHub repo là private nhưng baseline chưa được push. SHA/nhánh remote phải được ghi nhận sau thao tác publish thật.