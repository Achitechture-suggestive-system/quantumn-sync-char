# Kiểm tra runtime P0

**Ngày:** 14/11/2026. **Checkout:** quantumn-sync-char, branch main.
**Môi trường:** Python 3.13.13; Streamlit 1.67.0; Pydantic 2.14.3; NetworkX 3.7.

## Kết quả ghi nhận

- Regression suite chạy lại: 30 passed in 0.74s.
- python -m compileall -q app.py eqcr: exit 0.
- Streamlit AppTest: không có exception; fixture PetClinic được render.
- Server tại 127.0.0.1:8766 khởi động; /_stcore/health body ok và trang gốc đều HTTP 200.
- Ollama 0.40.16; qwen3:4b có trong danh sách local sau khi daemon khởi động. Baseline audit không gửi inference mới.
- GitHub CLI đã xác thực; repo Private; commit baseline trên main đã push.

Chi tiết lệnh, optimizer case, secret scan và giới hạn nằm trong [P0_BASELINE_VERIFICATION](verification/P0_BASELINE_VERIFICATION.md).

## Cách hiểu

HTTP 200 là smoke test localhost, không phải deployment test. AppTest không bao phủ mọi browser. Citation span, phân hoạch khả thi và human approval không xác minh semantics. Pet–Visit vẫn UNRESOLVED; Owner Search NOT_MEASURED. Input không có runtime topology hoặc benchmark.
