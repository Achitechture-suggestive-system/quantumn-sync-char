# P2 — Giới hạn nghiên cứu

- Case Tutor Support là input nhỏ, nguyên bản nhưng do nhóm chuẩn bị; không phải requirements production được thu thập độc lập.
- Hai lần gọi cùng `qwen3:4b`, cùng input SHA-256 (`aef49…`) và temperature 0 cho wording/citation khác nhau; lần pipeline trên source-case hash cuối `41af…` tạo output khác nữa. Chưa lưu seed hoặc toàn bộ response envelope để giải thích variation; không tuyên bố tái lập.
- Sáu responsibility proposal là mẫu nhỏ. Citation exact-span thành công không chứng minh semantic entailment; E1/B1 cho thấy source IDs có thể resolve nhưng nội dung relation/boundary vẫn unsupported hoặc ambiguous.
- Không có human annotation/adjudication hoặc gold labels. Không tính accuracy, precision, recall hay F1; test-only reviewer không phải chuyên gia.
- Constraint policy soft MUST_LINK là lựa chọn nghiên cứu có chủ đích, do reviewer cần chấp nhận evidence trước. Nó không đại diện luật nghiệp vụ hay boundary production. Không có hard domain constraints trong ca P2 hiện tại.
- Partition enumeration là thuật toán exhaustive Python cổ điển; “Quantum” là tên nhóm responsibility ứng viên. Kết quả không phải quantum computing hoặc architecture recommendation.
- Interaction Sync/Async là hypothesis, hợp đồng và consistency vẫn `UNKNOWN`/`UNRESOLVED`.
- Quality targets là input scenario; không chạy benchmark, load test, delivery measurement hay operational validation. Profile `NOT_MEASURED` không phải quality PASS.
- Structural traceability graph `PASS` kiểm IDs, spans và links được khai báo; không chứng minh nghĩa, tính đúng policy, deployability, resilience hoặc performance.
- Kết quả case thật sau human review, before/after artifacts, push SHA, branch ref và GitHub CI cần được thêm sau khi reviewer hoàn tất và commit docs kế tiếp.
