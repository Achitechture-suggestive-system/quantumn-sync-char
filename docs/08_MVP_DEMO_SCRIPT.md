# 08 — Kịch bản demo offline trong năm phút

## Chuẩn bị

PowerShell tại thư mục dự án:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Trong tab Input, nạp PetClinic demo data và chạy fixture xác định. Kịch bản chính không cần Ollama hay network. Fixture là requirements minh họa; responsibilities đã PRECOMPUTED.

## Lời dẫn theo thời gian

### 00:00–00:45 — Đầu vào

Hiển thị C0, FR-01…FR-06, workflow và hai scenarios. Nêu rõ case không có source code, runtime topology hay business policies đã xác nhận.

### 00:45–01:30 — Evidence và policy

Tab Evidence & Constraints: chỉ ra một relation PRESENT có source, relation UNKNOWN về consistency Pet–Visit, SCOPED_ABSENT trong scope khai báo và H1/H2/H3 là what-if. Không gọi chúng là quy tắc kinh doanh thật.

### 01:30–02:30 — Optimization và boundaries

Tab Quantum & Contracts: Bell(6)=203, 10 feasible/optimal với J=0 và tie-break xác định. Kiểm tra coverage đúng một lần; presentation/infrastructure là UNKNOWN.

### 02:30–03:15 — Interaction và quality

Cho thấy Pet → Visit UNRESOLVED, hai phương án Sync/Async có điều kiện, các contract fields chưa biết. QAME: Owner Search NOT_MEASURED; Pet–Visit INSUFFICIENT_EVIDENCE.

### 03:15–04:20 — Conflict và correction

Tab Human Review & Validation: thêm H4 bằng ADD MUST_LINK(R4,R6), xác nhận INFEASIBLE và 0 candidates. Sau đó disable H3 với lý do, revalidate và chỉ ra 5 feasible/optimal; status vẫn REVIEW_REQUIRED. Đừng giấu trường hợp infeasible.

### 04:20–05:00 — Phiên bản và export

So sánh v1/v2/v3, actor/reason/diff và validation report. Tải ZIP và JSON report. ZIP chứa artifacts và snapshots được UI đưa vào.

## Kết quả mong đợi

- v1: 203 enumerated; 10 feasible/optimal; REVIEW_REQUIRED.
- v2: H3/H4 xung đột; 0 feasible; INFEASIBLE.
- v3: H3 disabled; 5 feasible/optimal; REVIEW_REQUIRED.
- Pet–Visit UNRESOLVED; Owner Search NOT_MEASURED; Pet–Visit quality INSUFFICIENT_EVIDENCE.

## Ollama tùy chọn

Dùng Check local Ollama models, chọn model đã cài và chạy Run local Ollama proposals. Cho xem prompt version, input hash, citation refs và REVIEW_REQUIRED. Chạy trước phần demo hẹn giờ vì độ trễ có thể lớn. Nếu Ollama lỗi, tiếp tục kịch bản offline; không giả vờ inference thành công.
