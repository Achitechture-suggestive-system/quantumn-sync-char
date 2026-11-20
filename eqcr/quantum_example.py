"""Editable demonstration transcribed from the supplied ticket diagrams."""

from .quantum_tradeoff import Architecture


def ticket_example() -> Architecture:
    return Architecture.model_validate({
        "components": [
            {"id": "LOGIN", "name": "Customer Login", "characteristics": ["Trải nghiệm khách hàng"]},
            {"id": "PROFILE", "name": "Customer Profile", "characteristics": ["Trải nghiệm khách hàng"]},
            {"id": "CREATE", "name": "Ticket Creation", "characteristics": ["Trải nghiệm khách hàng"]},
            {"id": "ROUTE", "name": "Ticket Router", "characteristics": ["Nhất quán luồng ticket"]},
            {"id": "COMPLETE", "name": "Ticket Completion", "characteristics": ["Nhất quán luồng ticket"]},
            {"id": "REPORT", "name": "Operations Reporting", "characteristics": ["Cô lập tải báo cáo"]},
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
