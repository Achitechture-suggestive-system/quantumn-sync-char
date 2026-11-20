"""Editable demonstration transcribed from the supplied ticket diagrams."""

from .quantum_tradeoff import Architecture


def ticket_example() -> Architecture:
    customer_experience = "Trải nghiệm khách hàng"
    ticket_consistency = "Nhất quán luồng ticket"
    reporting_isolation = "Cô lập tải báo cáo"
    return Architecture.model_validate({
        "requirements": [
            {"id": "REQ-01", "text": "Khách hàng có thể đăng nhập, quản lý hồ sơ và gửi ticket trong luồng tự phục vụ."},
            {"id": "REQ-02", "text": "Định tuyến và hoàn tất phải sử dụng trạng thái nhất quán của cùng một ticket."},
            {"id": "REQ-03", "text": "Quản lý có thể xem báo cáo vận hành với tải báo cáo được cô lập khỏi luồng xử lý ticket."},
        ],
        "components": [
            {"id": "LOGIN", "name": "Customer Login", "characteristics": [customer_experience],
             "characteristic_requirements": {customer_experience: ["REQ-01"]}},
            {"id": "PROFILE", "name": "Customer Profile", "characteristics": [customer_experience],
             "characteristic_requirements": {customer_experience: ["REQ-01"]}},
            {"id": "CREATE", "name": "Ticket Creation", "characteristics": [customer_experience],
             "characteristic_requirements": {customer_experience: ["REQ-01"]}},
            {"id": "ROUTE", "name": "Ticket Router", "characteristics": [ticket_consistency],
             "characteristic_requirements": {ticket_consistency: ["REQ-02"]}},
            {"id": "COMPLETE", "name": "Ticket Completion", "characteristics": [ticket_consistency],
             "characteristic_requirements": {ticket_consistency: ["REQ-02"]}},
            {"id": "REPORT", "name": "Operations Reporting", "characteristics": [reporting_isolation],
             "characteristic_requirements": {reporting_isolation: ["REQ-03"]}},
        ],
        "interactions": [
            {"source": "CREATE", "target": "ROUTE", "mode": "ASYNC", "weight": 1,
             "basis": "Hình có đường nét đứt. Giả định demo: có thể định tuyến sau khi tiếp nhận ticket."},
            {"source": "ROUTE", "target": "COMPLETE", "mode": "SYNC", "weight": 2,
             "basis": "Giả định demo: hai component trao đổi trạng thái ticket trước khi trả kết quả."},
        ],
        "stores": [
            {"id": "CUSTOMER_DB", "name": "Customer DB", "members": ["LOGIN", "PROFILE"], "policy": "KEEP_SHARED",
             "basis": "Hình 1 vẽ một kho dùng chung. Demo giữ kho này trong một Quantum."},
            {"id": "TICKET_DB", "name": "Ticket DB", "members": ["CREATE", "ROUTE", "COMPLETE"], "policy": "SPLITTABLE",
             "basis": "Hình 3 minh hoạ hai kho và một tiến trình đồng bộ. Demo cho phép tách với chi phí dữ liệu."},
            {"id": "REPORT_DB", "name": "Reporting DB", "members": ["REPORT"], "policy": "KEEP_SHARED",
             "basis": "Hình 1 vẽ kho riêng cho báo cáo."},
        ],
        "keep_apart": [
            {"left": "LOGIN", "right": "ROUTE",
             "basis": "Giả định demo: tài khoản khách hàng và xử lý định tuyến phải ở hai Quantum riêng."},
        ],
    })
