# P8 — Architecture graph và Draw.io export

## Graph schema

`EQCR-ARCHITECTURE-GRAPH@1.0.0` giữ thứ tự lớp `ACTOR → PRESENTATION_APPLICATION → QUANTUM → INTEGRATION → INFRASTRUCTURE_STORAGE`. Lớp không được hỗ trợ bởi source được biểu diễn bằng node/edge `UNKNOWN` cùng provenance `ARCHITECTURAL_POLICY`; nó là placeholder của graph schema, không khẳng định component đó tồn tại trong hệ thống thật. Quantum boundaries vẫn là candidates cần review.

## Draw.io

`eqcr.drawio_export.architecture_graph_to_drawio` tạo mxfile XML chỉnh sửa được từ graph JSON. Cell IDs được băm ổn định từ logical node/edge IDs. Thứ tự layer, node, edge và tọa độ được xác định; XML encode labels theo ElementTree. Exporter dừng khi ID trùng hoặc edge có endpoint không tồn tại. Unknown/unresolved nodes và edges có nét đứt; quality profiles không được gắn vào node labels.

Streamlit cung cấp nút tải `.drawio` bên cạnh graph. Test parse XML và kiểm số node/edge, endpoint, unknown marker và tính ổn định byte-for-byte. Điều này kiểm cấu trúc/export; không phải Draw.io GUI round-trip hay xác nhận kiến trúc.
