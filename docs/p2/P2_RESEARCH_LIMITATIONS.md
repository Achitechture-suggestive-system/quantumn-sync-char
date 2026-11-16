# P2 — Giới hạn và giới hạn suy luận

- Tutor Support là prepared case nhỏ, không phải requirements thu thập từ production hoặc bộ test đại diện ngành.
- Các qwen3:4b v6 artifacts có sẵn được tạo trước blind checkpoint; chúng mang trạng thái `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`. Chưa có inference mới sau source-only lock trong checkout hiện tại.
- Hash/timestamp checkpoint giúp phát hiện thay đổi và xác nhận thứ tự trong app; reviewer ID tự khai báo, chưa xác minh danh tính ngoài ứng dụng. Checkpoint không chứng minh việc tuân thủ blinding hoặc độc lập giữa reviewers.
- Chưa có hai source-only annotators, adjudication hay gold labels. Khoa học/trạng thái hiện tại là `ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`. Không báo cáo precision, recall, F1, accuracy, agreement hoặc semantic correctness score.
- `SOURCE_BACKED` chỉ nói citation ID/span đã ánh xạ. Nó không chứng minh entailment hoặc semantic correctness. `APPROVED` ghi nhận quyết định reviewer; nó không tự tạo nhãn gold hoặc xác nhận thực nghiệm.
- Cardinality là 0..N roles per FR và multi-FR per role. Schema exact optimizer giới hạn tối đa tám role; kết quả nhỏ này không đánh giá độ phù hợp khi case vượt giới hạn.
- Relation universe chỉ gồm 30 ordered `BUSINESS_PRECEDES` và 15 cặp cho mỗi predicate architecture. Universe này là lựa chọn protocol P2; predicate ngoài registry phải sửa/reject/defer. `NOT_ANNOTATED`, `UNKNOWN`, `SCOPED_ABSENT` là trạng thái khác nhau.
- Hai policy soft trong case là architectural policy giả định cho kiểm tra đường nhân quả, không phải constraint domain đã duyệt. Hiện không có hard domain constraints. Không nới hard constraints để tạo feasible result.
- Unit tests dùng synthetic proposal/review fixtures có provenance `P2_TEST_ONLY`. Chúng xác minh mapping constraint → partition → quantum assignment → interaction/quality allocation; không là kết quả LLM, label, hoặc semantic claim cho case thật.
- Partition enumeration là exhaustive Python cổ điển, Bell number; “Quantum” là tên group candidate, không phải quantum computing, architecture style hoặc deployability.
- Interaction modes và protocol behavior chưa được xác nhận. Quality scenario targets do fixture chuẩn bị; không chạy load test, benchmark, reliability measurement hoặc operational validation. Quality Profiles `NOT_MEASURED` không phải PASS.
- Traceability graph PASS chỉ kiểm cấu trúc ID/span/edge; nó không chứng minh nội dung quan hệ, đúng policy, correctness, deployability, performance hoặc resilience.
- QAME result có thể thay đổi do model proposal set, reviewer dispositions, pair mapping, policy, objective và selected display tie-break. Mỗi run cần lưu version/hash của những input đó trước diễn giải.
