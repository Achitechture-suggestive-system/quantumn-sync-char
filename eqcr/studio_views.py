"""Read-only presentations of the Studio's existing analysis and review data."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape


def tag(value: object, tone: str = "neutral") -> str:
    return f'<span class="qs-tag qs-tag--{tone}">{escape(str(value))}</span>'


def diagram_header(architecture, *, example: bool, analyzed: bool, pending: bool, feasible: bool) -> str:
    name = "Ticket Support" if example else "Sơ đồ đang chỉnh"
    status = "Chờ phân tích"
    if pending:
        status = "Có thay đổi chưa phân tích"
    elif analyzed:
        status = "Có kết quả phân tích" if feasible else "Không có phương án khả thi"
    status_tone = "warn" if pending or analyzed and not feasible else "accent" if analyzed else "neutral"
    links = ['<a href="#studio-diagrams">Sơ đồ</a>']
    if analyzed and not pending:
        if any(item.kind == "NFR" for item in architecture.requirements):
            links.append('<a href="#studio-iso">Ánh xạ ISO</a>')
        links.append('<a href="#studio-tradeoffs">So sánh</a>')
        if feasible:
            links.extend((
                '<a href="#studio-trace">Truy vết</a>',
                '<a href="#studio-review">Human Review</a>',
            ))
    counters = "".join(
        f'<div><dt>{label}</dt><dd>{value}</dd></div>'
        for label, value in (
            ("Component", len(architecture.components)), ("Kho", len(architecture.stores)),
            ("Requirement", len(architecture.requirements)),
        )
    )
    return f"""
    <header class="qs-header">
        <div class="qs-header-context">{escape(name)} {tag(status, status_tone)}</div>
        <div class="qs-header-main">
            <div><h1>Quantum Studio</h1><p>Phân chia kiến trúc, đối chiếu yêu cầu và so sánh trade-off.</p></div>
            <dl class="qs-header-counts">{counters}</dl>
        </div>
        <nav class="qs-nav" aria-label="Đi tới phần">{"".join(links)}</nav>
    </header>
    """


def iso_evidence(requirement, suggestions, mentions, confirmed, names: dict[str, str]) -> str:
    signals = "".join(
        f'<li><strong>{escape(label.value)}</strong><q>{escape(quote)}</q></li>'
        for label, quote in suggestions.items()
    )
    named = "".join(f'<li><strong>{escape(names[item])}</strong><q>{escape(quote)}</q></li>'
                    for item, quote in mentions.items())
    allocations = "".join(
        f'<li><strong>{escape(label.value)}</strong><span class="qs-muted">'
        f'{escape(", ".join(names[item] for item in item_allocation.component_ids))}</span>'
        f'{f"<q>{escape(item_allocation.source_quote)}</q>" if item_allocation.source_quote else ""}</li>'
        for label, item_allocation in confirmed.items()
    )
    state = tag("Đã lưu ánh xạ", "accent") if confirmed else tag("Chờ xác nhận", "warn")
    return f"""
    <div class="qs-evidence-grid">
        <article class="qs-card qs-source">
            <div class="qs-card-top"><span class="qs-code">{escape(requirement.id)}</span>{state}</div>
            <h3>Requirement gốc</h3>
            <blockquote>{escape(requirement.text)}</blockquote>
            <h4>Component có tên trong nguồn</h4>
            {f'<ul class="qs-evidence-list">{named}</ul>' if named else '<p class="qs-muted">Chưa xác định từ văn bản.</p>'}
        </article>
        <article class="qs-card">
            <h3>Đề xuất từ văn bản</h3>
            {f'<ul class="qs-evidence-list">{signals}</ul>' if signals else '<p class="qs-muted">Chưa tìm thấy đoạn khớp. Bạn có thể chọn nhãn bên dưới.</p>'}
            <h4>Ánh xạ đã xác nhận</h4>
            {f'<ul class="qs-evidence-list">{allocations}</ul>' if allocations else '<p class="qs-muted">Chưa có ánh xạ đưa vào phân nhóm.</p>'}
        </article>
    </div>
    """


def cost_matrix(axes, weights, candidates, slots: str) -> str:
    headings = "".join(f'<th scope="col">{slot} <span>{escape(item.id)}</span></th>'
                       for slot, item in zip(slots, candidates, strict=True))
    rows = []
    baseline = candidates[0]
    for index, (name, weight) in enumerate(zip(axes, weights, strict=True)):
        cells = []
        for candidate in candidates:
            units = candidate.vector[index]
            diff = units - baseline.vector[index]
            change = tag(f"{diff:+d}", "better" if diff < 0 else "worse") if diff else ""
            cells.append(f"<td><span>{units}</span> {change}</td>")
        rows.append(f'<tr><th scope="row"><span aria-hidden="true" class="qs-dot qs-axis-{index}"></span>'
                    f'{escape(name)}</th><td>×{weight}</td>{"".join(cells)}</tr>')
    return f"""
    <div class="qs-matrix">
        <h3>Ma trận chi phí</h3>
        <p class="qs-muted">Mỗi ô ghi số đơn vị và chênh lệch so với A. Thanh trong từng thẻ biểu diễn số điểm sau khi nhân hệ số.</p>
        <div class="qs-scroll" tabindex="0" role="region" aria-label="Cuộn ma trận chi phí nếu cần">
            <table><thead><tr><th scope="col">Tiêu chí</th><th scope="col">Hệ số</th>{headings}</tr></thead>
            <tbody>{"".join(rows)}</tbody></table>
        </div>
    </div>
    """


def candidate_card(slot, candidate, *, baseline, axes, weights, points, plan, names, ranked, frontier, dominator, scale):
    profile = "".join(
        f'<li><span class="qs-code">{escape(group["id"])}</span><span>'
        f'{escape(", ".join(names[item] for item in group["components"]))}</span></li>'
        for group in plan["groups"]
    )
    weighted = [units * weight for units, weight in zip(candidate.vector, weights, strict=True)]
    total = sum(weighted)
    bars = "".join(
        f'<span class="qs-cost-segment qs-axis-{index}" style="flex-basis:{100 * value / scale:.2f}%"></span>'
        for index, value in enumerate(weighted) if value
    )
    bars_label = ", ".join(f"{axis} {value} điểm" for axis, value in zip(axes, weighted, strict=True))
    status = tag("Pareto" if frontier else "Ngoài Pareto", "accent" if frontier else "neutral")
    if ranked:
        status += tag("Xếp đầu", "accent")
    notes = ""
    if candidate.id != baseline.id:
        score_delta = total - sum(units * weight for units, weight in zip(baseline.vector, weights, strict=True))
        changes = "".join(
            tag(f"{axis} {delta:+d}", "better" if delta < 0 else "worse")
            for axis, before, after in zip(axes, baseline.vector, candidate.vector, strict=True)
            if (delta := after - before)
        )
        notes = f'<div class="qs-trade"><h4>So với A · {escape(baseline.id)} · {score_delta:+d} điểm</h4>'
        notes += f'<div class="qs-tags">{changes or tag("Cùng bộ chi phí")}</div></div>'
    if dominator:
        notes += (f'<p class="qs-muted">{escape(dominator)} có ít nhất một chi phí thấp hơn '
                  'và các chi phí còn lại bằng hoặc thấp hơn.</p>')
    characteristics = [label for group in plan["groups"] for label in group["characteristics"]]
    if all(len(group["characteristics"]) == 1 for group in plan["groups"]) and len(set(characteristics)) == len(plan["groups"]):
        notes += '<p class="qs-muted">Ánh xạ đặc tính ↔ Quantum đạt 1:1.</p>'
    drivers = "".join(
        f'<li><strong>{escape(row["subject"])}</strong>'
        f'<span>{escape(row["axis"])} · {escape(" / ".join(row["quanta"]))}</span>'
        f'<span class="qs-code">{row["units"]} × {row["weight"]} = {row["weighted_cost"]} điểm</span>'
        f'<small>{escape(row["reason"])}</small></li>'
        for row in points
    )
    why = f'<ul class="qs-drivers">{drivers}</ul>' if drivers else '<p class="qs-muted">Tổng chi phí bằng 0 ở các tiêu chí đã khai báo.</p>'
    return f"""
    <article class="qs-card qs-candidate{' qs-candidate--first' if ranked else ''}">
        <div class="qs-card-top"><span class="qs-code">{slot} · {escape(candidate.id)}</span><div class="qs-tags">{status}</div></div>
        <div class="qs-score"><strong>{total}</strong><span>điểm trọng số</span><span>{len(plan["groups"])} Quantum</span></div>
        <div class="qs-cost-bar" role="img" aria-label="{escape(bars_label)}">{bars}</div>
        <ul class="qs-groups">{profile}</ul>
        {notes}
        <details class="qs-details"><summary>Điểm phát sinh từ đâu</summary>{why}</details>
    </article>
    """


def quantum_cards(plan, names) -> str:
    cards = []
    for group in plan["groups"]:
        rows = []
        for label, owners in group["characteristic_requirements"].items():
            scope = []
            for owner, requirements in owners.items():
                chips = "".join(tag(requirement) for requirement in requirements) or '<span class="qs-muted">Chưa gắn</span>'
                scope.append(f'<li><span>{escape(names[owner])}</span><div class="qs-tags">{chips}</div></li>')
            rows.append(f'<div class="qs-characteristic"><h4>{escape(label)}</h4><ul>{"".join(scope)}</ul></div>')
        owner_list = ", ".join(names[owner] for owner in group["components"])
        count = tag(f"{len(group['components'])} component")
        body = "".join(rows) or '<p class="qs-muted">Chưa gắn đặc tính.</p>'
        cards.append(
            f'<article class="qs-card"><div class="qs-card-top"><h3>{escape(group["id"])}</h3>'
            f'{count}</div><p class="qs-muted">{escape(owner_list)}</p>{body}</article>'
        )
    return '<div class="qs-report-grid">' + "".join(cards) + "</div>"


def interaction_cards(plan, names) -> str:
    cards = []
    for edge in plan["interactions"]:
        mode = edge["mode"]
        route = " → ".join((edge["from_quantum"], edge["to_quantum"])) if edge["placement"] == "CROSS_QUANTUM" else edge["from_quantum"]
        tone = {"SYNC": "warn", "ASYNC": "accent", "UNKNOWN": "neutral"}[mode]
        locality = "Qua ranh giới" if edge["placement"] == "CROSS_QUANTUM" else "Nội bộ"
        follow_up = ""
        if mode == "UNKNOWN":
            follow_up = "Cần xác định kiểu tương tác trước khi đưa cạnh này vào điểm."
        elif locality == "Qua ranh giới":
            follow_up = ("Cần thiết kế giao nhận, retry và xử lý trùng."
                         if mode == "ASYNC" else "Cần xác định độ trễ, timeout và xử lý lỗi qua ranh giới.")
        cards.append(f"""
        <article class="qs-card qs-relation">
            <div class="qs-card-top"><div class="qs-tags">{tag(mode, tone)}{tag(locality)}</div><span class="qs-code">{escape(route)}</span></div>
            <h3>{escape(names[edge["source"]])} <span aria-hidden="true">→</span> {escape(names[edge["target"]])}</h3>
            <p class="qs-muted">Mức ảnh hưởng {edge["weight"]}{' · Giao dịch cục bộ' if edge["local_transaction"] else ''}</p>
            <p>{escape(edge["basis"] or "Chưa khai báo căn cứ.")}</p>
            {f'<p class="qs-muted">{follow_up}</p>' if follow_up else ''}
        </article>
        """)
    return '<div class="qs-report-grid">' + ("".join(cards) or '<p class="qs-muted">Đầu vào chưa có quan hệ giữa các component.</p>') + "</div>"


def constraint_cards(architecture, plan, names) -> str:
    assignment = plan["assignment"]
    cards = []
    for store in architecture.stores:
        quanta = sorted({assignment[member] for member in store.members})
        footprint = "Cần đồng bộ giữa các Quantum" if len(quanta) > 1 else "Dùng trong một Quantum"
        owners = ", ".join(names[item] for item in store.members)
        label = "Giữ chung" if store.policy == "KEEP_SHARED" else "Cho phép tách"
        cards.append(f"""
        <article class="qs-card">
            <div class="qs-card-top"><h3>{escape(store.name)}</h3>{tag(label)}</div>
            <p class="qs-muted">{escape(owners)}</p>
            <p><strong>{footprint}</strong> · {escape(" / ".join(quanta))}</p>
            <p>{escape(store.basis or "Chưa khai báo căn cứ.")}</p>
        </article>
        """)
    rules = [
        ("Bắt buộc tách", item.left, item.right, item.basis)
        for item in architecture.keep_apart
    ]
    rules.extend(("Giao dịch cục bộ", item.source, item.target, item.basis)
                 for item in architecture.interactions if item.local_transaction)
    for label, left, right, basis in rules:
        placement = f"{assignment[left]} · {assignment[right]}" if assignment[left] != assignment[right] else assignment[left]
        cards.append(f"""
        <article class="qs-card">
            <div class="qs-card-top">{tag(label, "warn")}<span class="qs-code">{escape(placement)}</span></div>
            <h3>{escape(names[left])} / {escape(names[right])}</h3><p>{escape(basis)}</p>
        </article>
        """)
    return '<div class="qs-report-grid">' + ("".join(cards) or '<p class="qs-muted">Chưa có kho hoặc ràng buộc riêng.</p>') + "</div>"


def requirement_cards(architecture, plan, names) -> str:
    traces = defaultdict(list)
    for group in plan["groups"]:
        for label, owners in group["characteristic_requirements"].items():
            for owner, requirement_ids in owners.items():
                for requirement_id in requirement_ids:
                    traces[requirement_id].append((label, names[owner], group["id"]))
    cards = []
    for requirement in architecture.requirements:
        links = traces[requirement.id]
        body = "".join(
            f'<li><span>{escape(label)}</span><span>{escape(owner)}</span>{tag(group, "accent")}</li>'
            for label, owner, group in links
        )
        kind = requirement.kind if requirement.kind != "UNSPECIFIED" else "Chưa phân loại"
        status = f"{len(links)} liên kết" if links else "Chưa gắn"
        cards.append(f"""
        <article class="qs-card qs-requirement">
            <div class="qs-card-top"><h3>{escape(requirement.id)}</h3><div class="qs-tags">{tag(kind)}{tag(status, "accent" if links else "warn")}</div></div>
            <p>{escape(requirement.text)}</p>
            {f'<ul class="qs-chain" aria-label="Đặc tính, component và Quantum">{body}</ul>' if body else ''}
        </article>
        """)
    return '<div class="qs-report-grid qs-requirements">' + ("".join(cards) or '<p class="qs-muted">Chưa có requirement trong mô hình.</p>') + "</div>"


def review_receipt(recorded) -> str:
    selection = recorded["selected_candidate"]
    item = next((candidate for candidate in recorded["comparison"] if candidate["id"] == selection), None)
    timestamp = datetime.fromisoformat(recorded["recorded_at"]).astimezone().strftime("%H:%M · %d/%m/%Y %Z")
    choice = f'Đã lưu lựa chọn {escape(selection)}' if selection else "Đã lưu yêu cầu chỉnh"
    return f"""
    <article class="qs-card qs-receipt" role="status">
        <div class="qs-card-top"><h3>{choice}</h3><span class="qs-muted">{escape(timestamp)}</span></div>
        {f'<p class="qs-muted">{item["score"]} điểm trọng số · {len(item["groups"])} Quantum tại thời điểm lưu</p>' if item else ''}
        {f'<p class="qs-review-note">{escape(recorded["note"])}</p>' if recorded["note"] else ''}
    </article>
    """
