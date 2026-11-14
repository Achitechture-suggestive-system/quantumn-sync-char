# Báo cáo test và validation

**Ngày:** 14/11/2026. **Môi trường:** Windows, Python 3.13.13, Pydantic 2.14.3, Streamlit 1.67.0, pytest 8.4.2.

## Lệnh và kết quả

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py eqcr
```

Lần chạy xác định sau khi hoàn thiện bộ tài liệu: **30 passed in 1.10s**; compileall exit 0; Streamlit AppTest không có exception; health/root localhost HTTP 200. Lần chạy baseline đầu ghi 30 passed in 1.56s; thời lượng có thể thay đổi. Kiểm tra 21 tệp Markdown không phát hiện liên kết tương đối hỏng. [P0 verification](verification/P0_BASELINE_VERIFICATION.md) ghi baseline code và scope.

Tests hiện có cover schema/IDs/spans; provenance/UNKNOWN; Bell(6)=203 và mười optima; conflict; exactly-once membership; interaction unresolved; NOT_MEASURED/INSUFFICIENT_EVIDENCE; status-only review; edits/impact; JSON package; citations cho bundle; Ollama fallback; ZIP/snapshots/metadata.

Suite không cần Ollama; call ngoài được monkeypatch. Nó không ước lượng độ đúng semantic, không kiểm deploy production, không load-test. PASS chỉ áp dụng cho assertion cụ thể.
