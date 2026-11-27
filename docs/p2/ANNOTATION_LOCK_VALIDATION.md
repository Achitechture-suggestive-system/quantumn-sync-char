# P2.1 — Kiểm tra annotation lock

## Phạm vi

Protocol `P2-BLIND-ANNOTATION-v3` ràng buộc lock với raw Tutor input và SHA-256 của manifest source-only. Validator không tạo annotation hoặc lock thay reviewer.

Package chuẩn nằm tại `docs/p2/source_only_reviewer/`. Manifest version là `P2-SOURCE-ONLY-PACKAGE-v1`; manifest SHA-256 hiện tại là `5725d44f491c5b680f79773482b6a53a03810cb88978b073a6ec5aacac68fe81`.

## Các kiểm tra được thực hiện

1. Thư mục package tồn tại, chỉ chứa năm file được cho phép và không có symlink.
2. Mọi source file được liệt kê trong manifest tồn tại và có SHA-256 trùng khớp; manifest phải khớp phiên bản đã commit.
3. `SOURCE_DATA.json`, source IDs, quote, span offsets và source hashes khớp với Tutor input hiện tại. `SOURCE_MATERIAL.md` phải khớp nội dung hiển thị được tạo từ JSON.
4. `ANNOTATION_TEMPLATE.json` đúng schema, gắn đúng source bundle và manifest, không chứa responsibility labels hoặc relation status đã điền.
5. Lock phải qua schema `P2-BLIND-ANNOTATION-v3`, bao phủ mỗi FR bằng annotations hoặc unresolved IDs, giữ nguyên relation registry, có reviewer ID và cả hai attestation đúng.
6. Timestamp phải là ISO-8601 có timezone và không ở tương lai. Khi cung cấp thời điểm inference, lock phải có trước hoặc bằng thời điểm bắt đầu inference. `run_p2_experiment.py` cũng kiểm tra thứ tự này trong proposal bundle.
7. Annotation hash và lock hash được tính lại; thay đổi nội dung hay metadata làm lock không hợp lệ.

Lệnh chỉ kiểm tra, không gọi Ollama:

```powershell
.\.venv\Scripts\python.exe scripts\validate_p2_annotation_lock.py `
  --annotation-lock ".\P2_BLIND_ANNOTATION_LOCK.json" `
  --source-package ".\docs\p2\source_only_reviewer"
```

Sau inference, có thể truyền `--inference-started-at` với timestamp thực tế để kiểm tra thứ tự. Nếu không truyền, validator báo rõ `NOT_CHECKED_NO_INFERENCE_TIMESTAMP_SUPPLIED`; run script vẫn bắt buộc timestamp lock đứng trước inference.

Kết quả `ANNOTATION_LOCK_VALID` xác nhận integrity, schema và source binding. Nó **không** xác nhận reviewer là chuyên gia, danh tính thật, sự độc lập hoặc entailment ngữ nghĩa. `reviewer_id` và việc chưa tiếp xúc phân tích là self-attested. Một hash cục bộ không thể chứng minh lịch sử truy cập.

Hiện chưa có lock do annotator cung cấp trong workspace. Lock test trong unit tests có provenance test-only và không được dùng làm P2 annotation.
