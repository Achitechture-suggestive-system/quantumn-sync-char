# Hướng dẫn worksheet gán nhãn độc lập

`semantic_annotation_worksheet.csv` chỉ chứa header, không chứa nhãn hay kết quả tự tạo. Tạo một bản cho mỗi reviewer, bảo toàn `case_id`, `item_id` và reference nguồn; adjudication nên được ghi riêng sau khi reviewer độc lập hoàn tất.

## Trường cần điền

- `case_id`, `item_id`, `item_type`: xác định case và loại proposal.
- `source_ids`, `source_spans`: source ID cùng offset/quote mà proposal viện dẫn.
- `proposal_text`: văn bản proposal nguyên trạng, không biên tập lại.
- `citation_exact`: YES/NO/UNCERTAIN — citation có khớp source span.
- `semantic_support`: SUPPORTED/CONTRADICTED/INSUFFICIENT/UNCERTAIN — nguồn có hỗ trợ cách hiểu không.
- `decomposition_label`: ACCEPT/REVISE/REJECT/UNCERTAIN cho responsibility decomposition.
- `boundary_label`: SAME_QUANTUM/SEPARATE_QUANTA/UNCERTAIN nếu item là boundary proposal.
- `evidence_label`, `interaction_label`, `quality_allocation_label`: dùng nhãn đã thống nhất trong protocol của nghiên cứu; để trống khi không áp dụng.
- `reviewer_id`, `review_date`, `rationale`, `adjudication_status`: nguồn gốc nhãn, lý do ngắn và trạng thái adjudication.

Trước khi tính metric, cần hướng dẫn nhãn cụ thể, ít nhất hai reviewer độc lập, tập adjudication và cách xử lý uncertain/missing. Không tính precision/recall từ proposal đã được cùng người tạo và review.
