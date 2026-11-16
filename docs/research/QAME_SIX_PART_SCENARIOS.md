# P9 — Sáu phần quality attribute scenario và ISO mapping

## Biểu diễn scenario

QAME xuất `QAME-SIX-PART-SCENARIO@1.0.0` với sáu trường:

1. `stimulus_source`
2. `stimulus`
3. `environment`
4. `stimulated_artifact`
5. `response`
6. `response_measure`

Mỗi phần giữ `value`, trạng thái `SPECIFIED`, `UNKNOWN` hoặc `UNSUPPORTED`, provenance và SourceRef khi source quote chứa đúng giá trị. `scenario_completeness` là `COMPLETE` chỉ khi đủ cả sáu phần được SourceRef hỗ trợ; field không được hỗ trợ giữ trong `unresolved_scenario_parts`. Nếu một giá trị có trong prepared package nhưng không nằm trong SourceRef quote, nó được ghi `UNSUPPORTED`/`PREPARED_FIXTURE` và không nhận citation. Không suy ra actor, môi trường, artifact hay response từ văn xuôi gần giống. SourceRef resolution vẫn không chứng minh semantic entailment.

Tutor Support hiện cung cấp stimulus và response measure; bốn phần còn lại tiếp tục `UNKNOWN`, vì vậy hai profile có trạng thái `PARTIAL`. Target được đánh `SPECIFIED` chỉ khi nó xuất hiện trong scenario SourceRef; target không được hỗ trợ là `UNSUPPORTED` và measurement giữ `INSUFFICIENT_EVIDENCE`. Target được hỗ trợ vẫn là `NOT_MEASURED`; không tạo pass/fail. Nguồn của `proposed_metric`, method và characteristic label được ghi riêng là source-backed hoặc `PREPARED_FIXTURE`.

## ISO/IEC 25010:2023

Output ghi phiên bản taxonomy `ISO/IEC 25010:2023` và giữ nhãn characteristic. Mapping xuất riêng với `status=UNMAPPED` khi có nhãn nhưng chưa có characteristic ID đã review; khi không có nhãn là `UNSPECIFIED`. `characteristic_id` hiện là `null`, `review_status=REVIEW_REQUIRED`; label có provenance `SOURCE_BACKED_SCENARIO_TRACE` chỉ nếu xuất hiện trong SourceRef, còn label fixture-only ghi `PREPARED_FIXTURE`; `mapping_provenance=DETERMINISTIC_TRANSFORMATION`. Không khẳng định chứng nhận hoặc tự đổi tên nhãn sang characteristic ID. Edition tham chiếu: [trang chính thức ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html).

## Measurement status

Targets là giá trị `SPECIFIED`, không phải quan sát `MEASURED`. Profile tiếp tục xuất `measurement=null` và `measurement_status=NOT_MEASURED` khi có target/measure plan; thiếu target giữ `INSUFFICIENT_EVIDENCE`. Chưa có target system hoặc adapter, môi trường, lần chạy, raw observation hay repeat protocol. `PREDICTED` và `UNSUPPORTED` chưa được gán bởi pipeline hiện tại.

Các field scenario được mở rộng theo hướng backward-compatible; vì Scenario model dump có thêm field null, hash canonical của raw Tutor requirements có thể thay đổi. Không có source-only annotation lock được cấp trong branch, nhưng sau thay đổi này cần khóa lại input hash trước khi chạy P2 experiment.
