# P2.1 — Quy trình chạy thí nghiệm Tutor thật

## Cổng trước inference

Chỉ chạy khi có đủ cả ba điều kiện sau:

1. Một annotator đã làm việc từ riêng package `docs/p2/source_only_reviewer/`, chưa xem model outputs Tutor, và tự khai báo đúng hai attestation trong worksheet.
2. Annotation lock do annotator gửi đã qua `scripts/validate_p2_annotation_lock.py`, khớp input hiện tại và manifest source-only. Validator không xác thực danh tính/lịch sử truy cập; đây là giới hạn self-attestation.
3. Code đã commit, checkout sạch, Ollama đang chạy và exact local tag `qwen3:4b` có sẵn. CLI kiểm tra điều kiện này trước khi inference.

Không sử dụng lock trong test fixture hoặc tự tạo nhãn thay reviewer. Khi chưa có lock, trạng thái là `P2_BLOCKED_INDEPENDENT_ANNOTATION` và không gửi request tới model.

## Xác minh lock

```powershell
.\.venv\Scripts\python.exe scripts\validate_p2_annotation_lock.py `
  --annotation-lock ".\P2_BLIND_ANNOTATION_LOCK.json" `
  --source-package ".\docs\p2\source_only_reviewer"
```

## Chạy inference sau khi qua cổng

```powershell
.\.venv\Scripts\python.exe scripts\run_p2_experiment.py `
  --annotation-lock ".\P2_BLIND_ANNOTATION_LOCK.json" `
  --source-package ".\docs\p2\source_only_reviewer" `
  --model qwen3:4b
```

Runner tạo thư mục mới trong `runs/p2-experiments/`; không ghi đè run cũ. Manifest ghi model tag/metadata phản hồi, prompt/schema versions, hashes input/package/lock, timestamp và checksums artifacts. Raw model response được giữ riêng với structural audit. Các lỗi citation, endpoint, duplicate, self-relation và registry là structural findings; chúng không đo semantic correctness.

## Human review và chạy downstream

Sau khi lưu raw output:

1. Giữ mọi model proposal ở `REVIEW_REQUIRED` cho tới khi người review thực sự chọn `APPROVE`, `CORRECT`, `REJECT` hoặc `DEFER` và ghi rationale/citation.
2. Giữ source interpretation, evidence relation và architectural implication trong các trường riêng. Business ordering không tạo architecture constraint.
3. Chỉ relation được review, có citation bao phủ hai FR, responsibility endpoints được approve, implication/rationale riêng và policy phù hợp mới có thể sinh soft constraint.
4. Chạy optimizer cổ điển trên accepted responsibility IDs và constraints đã phát sinh; kiểm mọi partition với hard constraints hiện hành.
5. Tạo candidate Quanta, interaction hypotheses và QAME profiles. Contract mặc định `UNDECIDED`; quality measurement vẫn `NOT_MEASURED` nếu không có target system/observations hợp lệ.
6. Thực hiện một human correction thật từ Human Review, lưu revision/snapshot, chạy lại và so hashes/diffs của evidence, constraints, partitions, quanta, interactions, QAME và traceability.

Không quảng bá selected optimum thành kiến trúc tối ưu đã được kiểm chứng độc lập. Nếu annotation độc lập/adjudication không tồn tại, không tính semantic precision/recall/F1.

## Tình trạng hiện tại

Tại lần recheck 2026-11-19, lock do reviewer bên ngoài chưa được cung cấp. Vì vậy mọi bước từ inference hậu-lock trở đi vẫn `BLOCKED_EXTERNAL`; lệnh trên là hướng dẫn chạy sau này, chưa phải bằng chứng một lần chạy đã xảy ra.
