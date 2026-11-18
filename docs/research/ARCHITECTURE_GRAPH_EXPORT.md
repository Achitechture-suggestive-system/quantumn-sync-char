# P8 — Architecture graph và Draw.io export

## Graph schema

`EQCR-ARCHITECTURE-GRAPH@1.0.0` giữ thứ tự lớp `ACTOR → PRESENTATION_APPLICATION → QUANTUM → INTEGRATION → INFRASTRUCTURE_STORAGE`. Lớp không được hỗ trợ bởi source được biểu diễn bằng node/edge `UNKNOWN` cùng provenance `ARCHITECTURAL_POLICY`; nó là placeholder của graph schema, không khẳng định component đó tồn tại trong hệ thống thật. Quantum boundaries vẫn là candidates cần review.

## Draw.io

`eqcr.drawio_export.architecture_graph_to_drawio` tạo mxfile XML chỉnh sửa được từ graph JSON. Cell IDs được băm ổn định từ logical node/edge IDs. Thứ tự layer, node, edge và tọa độ được xác định; XML encode labels theo ElementTree. Exporter dừng khi ID trùng hoặc edge có endpoint không tồn tại. Unknown/unresolved nodes và edges có nét đứt; quality profiles không được gắn vào node labels.

Streamlit cung cấp nút tải `.drawio` bên cạnh graph. Test parse XML và kiểm số node/edge, endpoint, unknown marker và tính ổn định byte-for-byte. Điều này kiểm cấu trúc/export; không phải Draw.io GUI round-trip hay xác nhận kiến trúc.

## QAME traceability edges

Traceability graph riêng nối `requirement → scenario → responsibility → quantum → interaction`, sau đó nối quality profile tới quantum/interaction, characteristic-mapping state và measurement state. Mapping node giữ ISO version, source label, characteristic ID, provenance và review status; measurement node giữ target, metric/method provenance, trạng thái và giá trị nếu có. Khi chưa có quyết định taxonomy hoặc observation, graph giữ `UNMAPPED`/`UNSPECIFIED`, `NOT_MEASURED`, `null` và `NOT_RECORDED`.

Các cạnh này không làm thay đổi kiến trúc graph xuất Draw.io, optimizer hoặc review state. Assertions `qame_trace_chain_resolves` và `qame_allocations_resolve` kiểm sự tồn tại của các node/cạnh và endpoint. `PASS` ở đây chỉ là kiểm tra cấu trúc.
