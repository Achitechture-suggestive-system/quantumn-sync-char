"use strict";

const $ = id => document.getElementById(id);
const inputGraph = $("input-graph");
const outputGraph = $("output-graph");
const modeStyle = {
    SYNC: ["#a74635", []], ASYNC: ["#007765", [7, 4]], UNKNOWN: ["#65746e", [2, 4]],
    DATA: ["#80968b", []], SPLIT: ["#966426", [3, 4]], APART: ["#866196", [2, 4]]
};
let options, model, positions, revision, selected, focusKey, tool, first, currentPlan, previousTop;
let dirty = false;
let submission = 0;
let nextRequirement = 1;
let lastHeight = 0;
let dragging = false;
let frameRequested = false;
const key = (type, id) => type + ":" + id;
const componentKey = id => key("component", id);
const storeKey = id => key("store", id);
const clone = value => JSON.parse(JSON.stringify(value));

function send(type, fields) {
    window.parent.postMessage({isStreamlitMessage: true, type, ...fields}, "*");
}

function emit(action, data = {}) {
    send("streamlit:setComponentValue", {
        dataType: "json", value: {token: Date.now() + "-" + (++submission), action, ...data}
    });
}

function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    if (tag === "button") node.type = "button";
    return node;
}

function sizeFrame() {
    const height = Math.ceil(document.body.getBoundingClientRect().height) + 2;
    if (height !== lastHeight) {
        lastHeight = height;
        send("streamlit:setFrameHeight", {height});
    }
}

function scheduleWires() {
    if (!model || frameRequested) return;
    frameRequested = true;
    requestAnimationFrame(() => {
        frameRequested = false;
        paint(inputGraph, inputWires(), $("input-edges"));
        paint(outputGraph, outputWires());
        sizeFrame();
    });
}

function graphNodes() {
    return [
        ...model.components.map(item => ({item, type: "component", key: componentKey(item.id)})),
        ...model.stores.map(item => ({item, type: "store", key: storeKey(item.id)}))
    ];
}

function arrangeDefaults() {
    const lists = [model.components, model.stores];
    lists.forEach((items, kind) => items.forEach((item, index) => {
        const type = kind ? "store" : "component";
        const grid = kind ? 8 : 4;
        const columns = Math.ceil(items.length / grid);
        const column = index % columns;
        const row = Math.floor(index / columns);
        const rows = Math.ceil(items.length / columns);
        positions[key(type, item.id)] ??= [
            kind ? (columns === 1 ? .83 : .66 + column * .20) : (columns === 1 ? .25 : .18 + column * .34),
            (row + 1) / (rows + 1)
        ];
    }));
}

function highlighted(id) {
    if (id === focusKey) return true;
    if (selected?.type === "edge") {
        return id === componentKey(selected.item.source) || id === componentKey(selected.item.target);
    }
    if (selected?.type === "apart") {
        return id === componentKey(selected.item.left) || id === componentKey(selected.item.right);
    }
    return false;
}

function updatePosition(button, id, x, y) {
    const left = (button.offsetWidth / 2 + 2) / inputGraph.clientWidth;
    const top = (button.offsetHeight / 2 + 2) / inputGraph.clientHeight;
    positions[id] = [
        Math.max(left, Math.min(1 - left, x)),
        Math.max(top, Math.min(1 - top, y))
    ];
    button.style.left = positions[id][0] * 100 + "%";
    button.style.top = positions[id][1] * 100 + "%";
    scheduleWires();
}

function markDirty() {
    if (!dirty) {
        dirty = true;
        emit("dirty");
    }
    $("message").textContent = "";
    $("inspector").querySelector(".matching-output")?.remove();
    updateStatus();
}

function selectNode(node) {
    if (tool) {
        if (!first) first = node;
        else if (first.key !== node.key) {
            const pair = [first, node];
            first = null;
            if (tool === "apart") {
                if (pair.some(item => item.type === "store")) return setMessage("Chọn hai component để đặt ràng buộc tách.");
                const [left, right] = pair.map(item => item.item.id);
                let rule = model.keep_apart.find(row => [row.left, row.right].includes(left) && [row.left, row.right].includes(right));
                if (!rule) {
                    rule = {left, right, basis: ""};
                    model.keep_apart.push(rule);
                    markDirty();
                }
                selected = {type: "apart", item: rule};
            } else if (pair.every(item => item.type === "component")) {
                const [source, target] = pair.map(item => item.item.id);
                let edge = model.interactions.find(row => row.source === source && row.target === target);
                if (!edge) {
                    edge = {source, target, mode: "UNKNOWN", weight: 1, local_transaction: false, basis: ""};
                    model.interactions.push(edge);
                    markDirty();
                }
                selected = {type: "edge", item: edge};
            } else if (pair.some(item => item.type === "component")) {
                const store = pair.find(item => item.type === "store");
                const component = pair.find(item => item.type === "component");
                if (!store.item.members.includes(component.item.id)) {
                    store.item.members.push(component.item.id);
                    markDirty();
                }
                selected = store;
            } else return setMessage("Một quan hệ kho cần ít nhất một component.");
            tool = null;
        }
    } else {
        selected = node;
        focusKey = node.key;
    }
    render();
}

function approvedIsoLabels(component, architecture) {
    return architecture.requirements.flatMap(requirement => (requirement.quality_allocations ?? [])
        .filter(allocation => allocation.component_ids.includes(component.id))
        .map(allocation => allocation.characteristic + " · " + requirement.id));
}

function makeNode(node, outputId) {
    const button = element("button", undefined, "node" + (node.type === "store" ? " store" : ""));
    button.dataset.node = outputId || node.key;
    button.dataset.origin = node.key;
    const tags = node.type === "store" ? node.item.policy :
        [...node.item.characteristics, ...approvedIsoLabels(node.item, outputId ? options.model : model)].join(" · ") || "Chưa có đặc tính";
    button.title = node.item.name + " · " + tags;
    button.setAttribute("aria-label", (outputId ? "Đầu ra " : "") + node.item.name);
    button.append(element("strong", node.item.name), element("small", tags));
    if (highlighted(node.key) || first?.key === node.key) button.classList.add("active");
    if (outputId) {
        button.addEventListener("click", () => {
            selected = graphNodes().find(item => item.key === node.key);
            focusKey = node.key;
            render();
        });
        return button;
    }
    button.style.left = positions[node.key][0] * 100 + "%";
    button.style.top = positions[node.key][1] * 100 + "%";
    let start;
    let moved = false;
    button.addEventListener("pointerdown", event => {
        if (event.button !== 0 || tool) return;
        start = {x: event.clientX, y: event.clientY, position: [...positions[node.key]]};
        moved = false;
        button.setPointerCapture(event.pointerId);
    });
    button.addEventListener("pointermove", event => {
        if (!start) return;
        const dx = event.clientX - start.x;
        const dy = event.clientY - start.y;
        if (!moved && Math.abs(dx) + Math.abs(dy) < 5) return;
        moved = dragging = true;
        updatePosition(button, node.key, start.position[0] + dx / inputGraph.clientWidth,
            start.position[1] + dy / inputGraph.clientHeight);
    });
    for (const event of ["pointerup", "pointercancel"]) button.addEventListener(event, () => {
        start = null;
        dragging = false;
        scheduleWires();
    });
    button.addEventListener("click", () => {
        if (moved) { moved = false; return; }
        selectNode(node);
    });
    button.addEventListener("keydown", event => {
        const steps = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]};
        if (!steps[event.key]) return;
        event.preventDefault();
        const [dx, dy] = steps[event.key];
        updatePosition(button, node.key, positions[node.key][0] + dx * .025, positions[node.key][1] + dy * .025);
    });
    return button;
}

function inputWires() {
    const wires = model.interactions.map(item => ({
        from: componentKey(item.source), to: componentKey(item.target), mode: item.mode, arrow: true,
        label: item.mode, edit: {type: "edge", item}
    }));
    for (const item of model.stores) {
        for (const member of item.members) wires.push({from: componentKey(member), to: storeKey(item.id), mode: "DATA"});
    }
    for (const item of model.keep_apart) {
        wires.push({from: componentKey(item.left), to: componentKey(item.right), mode: "APART",
            label: "TÁCH", edit: {type: "apart", item}});
    }
    return wires;
}

function activePlan() {
    return options.plans.find(plan => plan.id === currentPlan);
}

function outputWires() {
    const plan = activePlan();
    if (!plan) return [];
    const wires = options.model.interactions.map(item => ({
        from: componentKey(item.source), to: componentKey(item.target), mode: item.mode, arrow: true
    }));
    for (const store of options.model.stores) {
        const groups = [...new Set(store.members.map(id => plan.assignment[id]))].sort();
        for (const member of store.members) wires.push({
            from: componentKey(member), to: storeKey(store.id) + ":" + plan.assignment[member], mode: "DATA"
        });
        groups.slice(1).forEach((group, index) => wires.push({
            from: storeKey(store.id) + ":" + groups[index], to: storeKey(store.id) + ":" + group, mode: "SPLIT"
        }));
    }
    return wires;
}

function paint(graph, wires, labels) {
    const surface = graph.querySelector("canvas");
    const width = graph.clientWidth, height = graph.clientHeight;
    if (!width || !height) return;
    const scale = window.devicePixelRatio || 1;
    surface.width = width * scale;
    surface.height = height * scale;
    const ctx = surface.getContext("2d");
    ctx.scale(scale, scale);
    const frame = graph.getBoundingClientRect();
    const geometry = new Map([...graph.querySelectorAll("[data-node]")].map(node => {
        const r = node.getBoundingClientRect();
        return [node.dataset.node, {x: r.left - frame.left + r.width / 2, y: r.top - frame.top + r.height / 2,
            w: r.width / 2, h: r.height / 2}];
    }));
    if (labels && !dragging) labels.replaceChildren();
    for (const wire of wires) {
        const a = geometry.get(wire.from), b = geometry.get(wire.to);
        if (!a || !b) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        if (Math.abs(dx) + Math.abs(dy) < 1) continue;
        const av = Math.min(a.w / Math.abs(dx), a.h / Math.abs(dy), .48);
        const bv = Math.min(b.w / Math.abs(dx), b.h / Math.abs(dy), .48);
        const x1 = a.x + dx * av, y1 = a.y + dy * av;
        const x2 = b.x - dx * bv, y2 = b.y - dy * bv;
        const [color, dash] = modeStyle[wire.mode];
        const parallel = wires.filter(item => (item.from === wire.from && item.to === wire.to) ||
            (item.from === wire.to && item.to === wire.from));
        const sign = wire.from < wire.to ? 1 : -1;
        const bend = sign * (parallel.indexOf(wire) - (parallel.length - 1) / 2) * 54;
        const distance = Math.hypot(dx, dy);
        const mx = (x1 + x2) / 2 - dy * bend / distance;
        const my = (y1 + y2) / 2 + dx * bend / distance;
        ctx.strokeStyle = color;
        ctx.lineWidth = highlighted(wire.from) || highlighted(wire.to) ? 2.4 : 1.35;
        ctx.setLineDash(dash);
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.quadraticCurveTo(mx, my, x2, y2); ctx.stroke();
        if (wire.arrow) {
            const angle = Math.atan2(y2 - my, x2 - mx);
            ctx.fillStyle = color;
            ctx.beginPath(); ctx.moveTo(x2, y2);
            ctx.lineTo(x2 - 8 * Math.cos(angle - .46), y2 - 8 * Math.sin(angle - .46));
            ctx.lineTo(x2 - 8 * Math.cos(angle + .46), y2 - 8 * Math.sin(angle + .46));
            ctx.fill();
        }
        if (wire.edit && labels && !dragging) {
            const label = element("button", wire.label, "edge-label");
            label.style.left = ((x1 + x2) / 4 + mx / 2) + "px";
            label.style.top = ((y1 + y2) / 4 + my / 2) + "px";
            label.style.color = color;
            label.title = wire.edit.item.basis || wire.label;
            label.setAttribute("aria-label", wire.label + " " + wire.from.split(":")[1] + " → " + wire.to.split(":")[1]);
            label.onclick = () => {
                selected = wire.edit;
                focusKey = first = tool = null;
                render();
            };
            labels.append(label);
        }
    }
}

function field(parent, labelText, input, wide = false) {
    const label = element("label", labelText, wide ? "wide" : "");
    parent.append(label);
    label.append(input);
    return input;
}

function textField(parent, label, initial, update, max, wide = false) {
    const input = element("input");
    input.value = initial;
    input.maxLength = max;
    field(parent, label, input, wide);
    input.oninput = () => {
        update(input.value);
        markDirty();
        renderInput();
    };
}

function selectField(parent, label, initial, choices, update) {
    const input = element("select");
    choices.forEach(choice => input.append(new Option(choice, choice)));
    input.value = initial;
    field(parent, label, input);
    input.onchange = () => { update(input.value); markDirty(); render(); };
}

function weightField(parent, item) {
    const input = element("input");
    input.type = "number";
    input.min = "0"; input.max = "10"; input.step = "1"; input.value = item.weight;
    field(parent, "Mức ảnh hưởng (0–10)", input);
    input.oninput = () => { item.weight = input.valueAsNumber; markDirty(); };
}

function focusRequirement(id) {
    $("requirements-editor").open = true;
    $("source-" + id)?.focus();
}

function renderRequirements() {
    const list = $("requirement-list");
    list.replaceChildren();
    $("requirement-count").textContent = "· " + model.requirements.length;
    $("add-requirement").disabled = model.requirements.length >= 40;
    for (const requirement of model.requirements) {
        const row = element("div", undefined, "requirement-row");
        const meta = element("div", undefined, "requirement-meta");
        const label = element("label", requirement.id, "requirement-id");
        const kind = element("select");
        kind.append(new Option("Chưa phân loại", "UNSPECIFIED"), new Option("FR", "FR"), new Option("NFR", "NFR"));
        kind.value = requirement.kind ?? "UNSPECIFIED";
        kind.setAttribute("aria-label", "Loại " + requirement.id);
        kind.onchange = () => {
            requirement.kind = kind.value;
            requirement.quality_allocations = [];
            markDirty();
            render();
        };
        const input = element("textarea");
        input.id = "source-" + requirement.id;
        label.htmlFor = input.id;
        input.setAttribute("aria-label", "Nội dung " + requirement.id);
        input.rows = 2;
        input.maxLength = 600;
        input.value = requirement.text;
        input.oninput = () => {
            requirement.text = input.value;
            requirement.quality_allocations = [];
            markDirty();
            renderInput();
        };
        const remove = element("button", "Xóa", "requirement-remove");
        remove.setAttribute("aria-label", "Xóa " + requirement.id + " và các liên kết");
        remove.onclick = () => {
            model.requirements = model.requirements.filter(item => item !== requirement);
            for (const component of model.components) {
                component.characteristic_requirements = Object.fromEntries(
                    Object.entries(component.characteristic_requirements ?? {}).map(([label, ids]) =>
                        [label, ids.filter(id => id !== requirement.id)])
                );
            }
            markDirty();
            render();
        };
        meta.append(label, kind);
        row.append(meta, input, remove);
        list.append(row);
    }
}

function renderCharacteristicLinks(area, component) {
    area.replaceChildren();
    const assignments = new Map(Object.entries(component.characteristic_requirements ?? {}));
    for (const label of component.characteristics) {
        const ids = assignments.get(label) ?? [];
        const row = element("div", undefined, "characteristic-links");
        row.append(element("strong", label));
        function setLinks(updated) {
            component.characteristic_requirements = {...component.characteristic_requirements, [label]: updated};
            markDirty();
            renderCharacteristicLinks(area, component);
        }
        for (const id of ids) {
            const remove = element("button", id + " ×", "requirement-chip");
            remove.setAttribute("aria-label", `Gỡ ${id} khỏi ${label}`);
            remove.onclick = () => setLinks(ids.filter(link => link !== id));
            row.append(remove);
        }
        const available = model.requirements.filter(item => !ids.includes(item.id));
        if (available.length) {
            const picker = element("select");
            picker.setAttribute("aria-label", "Gắn requirement cho " + label);
            picker.append(new Option("Gắn requirement…", ""));
            for (const item of available) picker.append(new Option(item.id, item.id));
            picker.onchange = () => { if (picker.value) setLinks([...ids, picker.value]); };
            row.append(picker);
        }
        if (!ids.length && !available.length) row.append(element("small", "Thêm requirement bên dưới để gắn nguồn."));
        area.append(row);
    }
}

function removeSelection() {
    const {type, item} = selected;
    if (type === "component") {
        model.components = model.components.filter(row => row !== item);
        model.interactions = model.interactions.filter(row => row.source !== item.id && row.target !== item.id);
        model.keep_apart = model.keep_apart.filter(row => row.left !== item.id && row.right !== item.id);
        model.stores.forEach(store => { store.members = store.members.filter(id => id !== item.id); });
        for (const requirement of model.requirements) {
            requirement.quality_allocations = (requirement.quality_allocations ?? []).map(allocation => ({
                ...allocation, component_ids: allocation.component_ids.filter(id => id !== item.id),
            })).filter(allocation => allocation.component_ids.length);
        }
    } else {
        const list = {store: "stores", edge: "interactions", apart: "keep_apart"}[type];
        model[list] = model[list].filter(row => row !== item);
    }
    if (selected.key) delete positions[selected.key];
    selected = focusKey = null;
    markDirty();
    render();
}

function renderInspector() {
    const area = $("inspector");
    area.replaceChildren();
    if (!selected) {
        area.append(element("p", "Chọn một component, kho hoặc nhãn cạnh để chỉnh thuộc tính."));
        return;
    }
    const {type, item} = selected;
    const label = item.id || (type === "edge" ? item.source + " → " + item.target : item.left + " ↔ " + item.right);
    area.append(element("h3", label));
    const plan = activePlan();
    const group = type === "component" && !dirty && plan?.assignment[item.id];
    if (group) area.append(element("p", "Đầu ra " + plan.id + " → " + group, "matching-output"));
    const fields = element("div", undefined, "fields");
    area.append(fields);
    const list = value => [...new Set(value.split(";").map(part => part.trim()).filter(Boolean))];
    if (type === "component" || type === "store") {
        textField(fields, "Tên", item.name, value => { item.name = value; }, 100, true);
    }
    if (type === "component") {
        const links = element("div", undefined, "wide");
        textField(fields, "Characteristics phụ trách (phân cách bằng ;)", item.characteristics.join("; "),
            value => {
                item.characteristics = list(value);
                renderCharacteristicLinks(links, item);
            }, 1200, true);
        renderCharacteristicLinks(links, item);
        fields.append(links);
        const iso = approvedIsoLabels(item, model);
        if (iso.length) fields.append(element("p", "ISO đã gán · " + iso.join(" / "), "wide"));
    } else if (type === "edge") {
        selectField(fields, "Kiểu tương tác", item.mode, ["SYNC", "ASYNC", "UNKNOWN"], value => {
            item.mode = value;
            if (value !== "SYNC") item.local_transaction = false;
        });
        weightField(fields, item);
        const check = element("input");
        check.type = "checkbox"; check.checked = item.local_transaction; check.disabled = item.mode !== "SYNC";
        field(fields, "Giao dịch cục bộ", check);
        check.onchange = () => { item.local_transaction = check.checked; markDirty(); };
    } else if (type === "store") {
        selectField(fields, "Chính sách kho", item.policy, ["KEEP_SHARED", "SPLITTABLE"], value => { item.policy = value; });
        weightField(fields, item);
        textField(fields, "ID component dùng kho (phân cách bằng ;)", item.members.join("; "),
            value => { item.members = list(value); }, 320, true);
    }
    if (type !== "component") textField(fields, "Căn cứ", item.basis, value => { item.basis = value; }, type === "apart" ? 100 : 240, true);
    const remove = element("button", "Xóa phần tử", "remove");
    remove.disabled = type === "component" && model.components.length <= 1;
    remove.onclick = removeSelection;
    area.append(remove);
}

function quantumCharacteristics(plan, group, names, requirements) {
    const section = element("section", undefined, "quantum-characteristics");
    section.setAttribute("aria-label", "Characteristics của " + group.id);
    section.append(element("h4", "Characteristics"));
    const characteristics = Object.entries(group.characteristic_sources);
    if (!characteristics.length) section.append(element("p", "Chưa gắn đặc tính"));
    for (const [label, owners] of characteristics) {
        const entry = element("div", undefined, "characteristic");
        entry.append(element("strong", label));
        for (const owner of owners) {
            const line = element("div", undefined, "characteristic-owner");
            line.append(element("span", names.get(owner) || owner));
            const ids = group.characteristic_requirements?.[label]?.[owner] ?? [];
            for (const id of ids) {
                const ref = element("button", id, "requirement-chip");
                ref.title = requirements.get(id) ?? id;
                ref.disabled = !$("source-" + id);
                ref.onclick = () => focusRequirement(id);
                line.append(ref);
            }
            if (!ids.length) line.append(element("small", "Chưa gắn requirement"));
            entry.append(line);
        }
        const shared = plan.groups.filter(other => other.id !== group.id && other.characteristics.includes(label));
        if (shared.length) entry.append(element("small", "Cùng phụ trách: " + shared.map(other => other.id).join(", ")));
        section.append(entry);
    }
    return section;
}

function renderOutput() {
    const area = $("quanta");
    const chooser = $("plan");
    chooser.replaceChildren();
    chooser.disabled = !options.plans.length;
    for (const plan of options.plans) chooser.append(new Option(plan.label, plan.id));
    chooser.value = currentPlan || "";
    const plan = activePlan();
    $("output-count").textContent = plan ? plan.groups.length + " Quantum" : "";
    area.replaceChildren();
    area.className = plan ? "quanta" : "empty";
    if (!plan) area.textContent = options.no_solution ? "Bộ ràng buộc hiện tại không có phương án khả thi." : "Quantum sẽ xuất hiện tại đây.";
    if (plan) {
        const names = new Map(options.model.components.map(item => [item.id, item.name]));
        const requirements = new Map(options.model.requirements.map(item => [item.id, item.text]));
        const selectedGroups = new Set();
        for (const id of Object.keys(plan.assignment)) {
            if (highlighted(componentKey(id))) selectedGroups.add(plan.assignment[id]);
        }
        if (focusKey?.startsWith("store:")) {
            const store = options.model.stores.find(item => storeKey(item.id) === focusKey);
            store?.members.forEach(id => selectedGroups.add(plan.assignment[id]));
        }
        for (const group of plan.groups) {
            const region = element("div", undefined, "quantum" + (selectedGroups.has(group.id) ? " active" : ""));
            const groupHeader = element("div", undefined, "quantum-head");
            groupHeader.append(element("h3", group.id), element("small", group.components.length + " component"));
            region.append(groupHeader, quantumCharacteristics(plan, group, names, requirements));
            for (const id of group.components) {
                const item = options.model.components.find(row => row.id === id);
                region.append(makeNode({type: "component", item, key: componentKey(id)}, componentKey(id)));
            }
            for (const item of options.model.stores) {
                if (!item.members.some(id => plan.assignment[id] === group.id)) continue;
                const split = new Set(item.members.map(id => plan.assignment[id])).size > 1;
                region.append(makeNode({type: "store", item: split ? {...item, name: item.name + " · phần " + group.id} : item,
                    key: storeKey(item.id)}, storeKey(item.id) + ":" + group.id));
            }
            area.append(region);
        }
    }
    renderTrace(plan);
}

function traceDetails(trace, entries) {
    const fields = element("dl", undefined, "trace-fields");
    for (const [label, value] of entries) fields.append(element("dt", label), element("dd", value));
    trace.append(fields);
}

function renderTrace(plan) {
    const trace = $("trace");
    trace.replaceChildren();
    if (!plan) return;
    trace.append(element("h3", "Truy vết đầu vào → đầu ra"));
    if (!dirty && selected?.type === "edge") {
        const {source, target, mode, weight, basis} = selected.item;
        const names = new Map(model.components.map(item => [item.id, item.name]));
        trace.append(element("p", names.get(source) + " → " + names.get(target), "trace-title"));
        traceDetails(trace, [
            ["Vị trí", plan.assignment[source] === plan.assignment[target] ? "Nội bộ " + plan.assignment[source]
                : plan.assignment[source] + " → " + plan.assignment[target]],
            ["Kiểu & ảnh hưởng", mode + " · " + weight],
            ["Căn cứ", basis || "Chưa khai báo"],
        ]);
        return;
    }
    const source = graphNodes().find(node => node.key === focusKey);
    const groups = source?.type === "store"
        ? [...new Set(options.model.stores.find(item => storeKey(item.id) === focusKey)?.members.map(id => plan.assignment[id]))]
        : [plan.assignment[source?.item.id]].filter(Boolean);
    if (!source || dirty || !groups.length) trace.append(element("p", "Bấm một component hoặc kho trên hai sơ đồ để xem nhóm tương ứng."));
    else {
        trace.append(element("p", source.item.name, "trace-title"));
        if (source.type === "component") {
            const labels = [...source.item.characteristics, ...approvedIsoLabels(source.item, model)];
            traceDetails(trace, [["Quantum", groups.join(", ")], ["Đặc tính phụ trách", labels.join(" / ") || "Chưa khai báo"]]);
        } else {
            traceDetails(trace, [
                ["Quantum dùng kho", groups.join(", ")],
                ["Chính sách", source.item.policy === "KEEP_SHARED" ? "Giữ chung"
                    : groups.length > 1 ? "Tách kho · cần đồng bộ" : "Cho phép tách"],
                ["Căn cứ", source.item.basis || "Chưa khai báo"],
            ]);
        }
    }
}

function setMessage(text) { $("message").textContent = text; }

function updateStatus() {
    $("connect").setAttribute("aria-pressed", tool === "connect");
    $("separate").setAttribute("aria-pressed", tool === "apart");
    $("hint").textContent = tool
        ? (first ? "Đã chọn " + first.item.name + ". Chọn đầu còn lại." : "Chọn phần tử đầu tiên trên sơ đồ.")
        : "Kéo thả để đổi bố cục. Bấm component để sửa đặc tính, bấm nhãn cạnh để sửa quan hệ.";
    const plan = activePlan();
    const showLegend = Boolean(plan) && !dirty;
    $("wire-legend").hidden = !showLegend;
    $("unknown-legend").hidden = !plan?.interactions.some(edge => edge.mode === "UNKNOWN");
    $("output-hint").hidden = showLegend;
    $("output-hint").textContent = dirty && options.plans.length ? "Mô hình đã đổi. Bấm Phân tích sơ đồ để cập nhật kết quả."
        : "Chọn Phân tích sơ đồ để xem các Quantum.";
}

function renderInput() {
    arrangeDefaults();
    $("input-nodes").replaceChildren(...graphNodes().map(node => makeNode(node)));
    $("input-count").textContent = model.components.length + " component · " + model.stores.length + " kho";
    $("add-component").disabled = model.components.length >= 8;
    $("add-store").disabled = model.stores.length >= 16;
    scheduleWires();
}

function render() {
    renderInput();
    renderInspector();
    renderRequirements();
    renderOutput();
    updateStatus();
    scheduleWires();
}

function addNode(type) {
    const items = type === "store" ? model.stores : model.components;
    const prefix = type === "store" ? "DB" : "C";
    let index = 1;
    while (items.some(item => item.id === prefix + index)) index += 1;
    const id = prefix + index;
    const item = type === "store"
        ? {id, name: "Kho " + id, members: [], policy: "KEEP_SHARED", weight: 1, basis: ""}
        : {id, name: "Component " + id, characteristics: []};
    items.push(item);
    selected = {key: key(type, id), type, item};
    focusKey = selected.key;
    first = tool = null;
    markDirty();
    render();
}

$("add-component").onclick = () => addNode("component");
$("add-store").onclick = () => addNode("store");
$("add-requirement").onclick = () => {
    const used = new Set(model.requirements.map(item => item.id));
    let id;
    do { id = "REQ-" + String(nextRequirement++).padStart(2, "0"); } while (used.has(id));
    model.requirements.push({id, text: ""});
    markDirty();
    render();
    focusRequirement(id);
};
for (const [id, value] of [["connect", "connect"], ["separate", "apart"]]) {
    $(id).onclick = () => { tool = tool === value ? null : value; first = null; render(); };
}
$("plan").onchange = event => { currentPlan = event.target.value; render(); };
$("reset").onclick = () => {
    model = clone(options.example);
    positions = {};
    focusKey = selected = first = tool = null;
    markDirty();
    render();
};
$("analyze").onclick = () => {
    setMessage("Đang phân tích…");
    const submitted = clone(model);
    for (const component of submitted.components) {
        component.characteristic_requirements = Object.fromEntries(
            Object.entries(component.characteristic_requirements ?? {}).filter(([label, ids]) =>
                component.characteristics.includes(label) && ids.length)
        );
    }
    emit("analyze", {model: submitted, layout: positions});
};
new ResizeObserver(scheduleWires).observe(document.body);
new ResizeObserver(scheduleWires).observe(outputGraph);
window.addEventListener("message", event => {
    if (event.source !== window.parent || event.data?.type !== "streamlit:render") return;
    options = event.data.args;
    const newRevision = revision !== options.revision;
    if (newRevision) {
        model = clone(options.model);
        positions = clone(options.layout);
        if (selected?.key) selected = graphNodes().find(item => item.key === selected.key);
        else selected = null;
        tool = first = null;
        dirty = options.pending;
        revision = options.revision;
    }
    const top = options.plans[0]?.id;
    if (newRevision || top !== previousTop || !options.plans.some(plan => plan.id === currentPlan)) currentPlan = top;
    previousTop = top;
    setMessage(options.error || "");
    if (newRevision) render();
    else {
        const inspector = $("inspector");
        inspector.querySelector(".matching-output")?.remove();
        if (selected?.type === "component" && !dirty && activePlan()?.assignment[selected.item.id]) {
            const plan = activePlan();
            inspector.querySelector("h3").after(element("p", "Đầu ra " + plan.id + " → " +
                plan.assignment[selected.item.id], "matching-output"));
        }
        renderOutput();
        updateStatus();
        scheduleWires();
    }
});
send("streamlit:componentReady", {apiVersion: 1});
sizeFrame();
