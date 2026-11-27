"""ISO/IEC 25010:2023 product quality labels and reviewable text matches."""

from enum import StrEnum
import re


class QualityCharacteristic(StrEnum):
    FUNCTIONAL_SUITABILITY = "Functional suitability"
    PERFORMANCE_EFFICIENCY = "Performance efficiency"
    COMPATIBILITY = "Compatibility"
    INTERACTION_CAPABILITY = "Interaction capability"
    RELIABILITY = "Reliability"
    SECURITY = "Security"
    MAINTAINABILITY = "Maintainability"
    FLEXIBILITY = "Flexibility"
    SAFETY = "Safety"


ISO_EDITION = "ISO/IEC 25010:2023"

# Studio heuristics. These expressions suggest labels and preserve the matching text.
SIGNALS = {
    QualityCharacteristic.FUNCTIONAL_SUITABILITY: r"functional completeness|functional correctness|functional appropriateness|đúng kết quả|đầy đủ chức năng",
    QualityCharacteristic.PERFORMANCE_EFFICIENCY: r"\d+(?:[.,]\d+)?\s*ms|\bp(?:95|99)\b|latency|throughput|response time|độ trễ|thông lượng|thời gian phản hồi",
    QualityCharacteristic.COMPATIBILITY: r"interoperab(?:ility|le)|co-existence|tương tác liên hệ thống|tương thích|trao đổi dữ liệu với",
    QualityCharacteristic.INTERACTION_CAPABILITY: r"user assistance|accessibility|keyboard navigation|learnability|bàn phím|trình đọc màn hình|dễ học",
    QualityCharacteristic.RELIABILITY: r"availability|fault tolerance|recoverability|failover|uptime|sẵn sàng|chịu lỗi|phục hồi|khôi phục",
    QualityCharacteristic.SECURITY: r"encrypt(?:ion|ed)|authentication|authori[sz]ation|confidentiality|mã hóa|xác thực|phân quyền|bảo mật",
    QualityCharacteristic.MAINTAINABILITY: r"testability|modifiability|modularity|maintainability|khả năng kiểm thử|dễ bảo trì|dễ sửa đổi|mô[- ]đun hóa",
    QualityCharacteristic.FLEXIBILITY: r"scalability|adaptability|installability|replaceability|co giãn|mở rộng ngang|thích nghi|khả năng thay thế",
    QualityCharacteristic.SAFETY: r"fail-safe|hazard warning|risk to life|chế độ an toàn|cảnh báo nguy hiểm|an toàn tính mạng",
}


def quality_suggestions(text: str) -> dict[QualityCharacteristic, str]:
    """Return one verbatim signal per proposed label, in ISO category order."""
    return {
        characteristic: match.group()
        for characteristic, signal in SIGNALS.items()
        if (match := re.search(rf"(?<!\w)(?:{signal})(?!\w)", text, re.IGNORECASE))
    }


def component_mentions(text: str, names: dict[str, str]) -> dict[str, str]:
    """Suggest existing components explicitly named by label or exact ID."""
    matches = {}
    for component_id, name in names.items():
        by_name = re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text, re.IGNORECASE) if len(name) >= 3 else None
        by_id = re.search(rf"(?<!\w){re.escape(component_id)}(?!\w)", text)
        if match := by_name or by_id:
            matches[component_id] = match.group()
    return matches
