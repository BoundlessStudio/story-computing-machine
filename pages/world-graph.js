/* A dependency-free network reader. Connections and classifications stay separate. */
(() => {
  "use strict";
  const UNCLASSIFIED = "__unclassified__";
  const PALETTE = ["#438fbd", "#c2813c", "#8d6bbb", "#399887", "#ce6979", "#8a9948", "#ba70aa", "#628ba0"];

  function connectionsFor(data, mode) {
    if (mode === "none") return [];
    if (mode === "recorded") return data.edges;
    if (mode !== "era" && mode !== "history") return data.edges.filter(edge => edge.kind === mode);
    const pairs = new Map();
    for (const group of data.classifications[mode].values) {
      const members = data.nodes.filter(node => node.classes[mode].includes(group.id));
      for (let a = 0; a < members.length; a++) {
        for (let b = a + 1; b < members.length; b++) {
          const [source, target] = [members[a].id, members[b].id].sort();
          const id = `${source}:${target}`;
          if (!pairs.has(id)) pairs.set(id, {
            id, source, target, kind: "shared", basis: "editorial", ordering: "none", labels: [],
            note: mode === "era" ? "Grouped in the same proposed era; this does not establish an encounter or exact contemporaneity."
              : "Both are cited anchors in this editorial history thread; this does not establish descent or a shared cause.",
          });
          pairs.get(id).labels.push(group.label);
        }
      }
    }
    return [...pairs.values()].map(edge => ({ ...edge, label: edge.labels.join(" · ") }));
  }

  function layout(nodes, edges) {
    // Seeded positions and a bounded simulation keep reloads stable and avoid motion.
    const points = nodes.map((node, i) => ({ id: node.id,
      x: Math.cos(i * 2.399963) * Math.sqrt(i + 1) * 23,
      y: Math.sin(i * 2.399963) * Math.sqrt(i + 1) * 23, vx: 0, vy: 0 }));
    const byId = new Map(points.map(point => [point.id, point]));
    const links = edges.map(edge => [byId.get(edge.source), byId.get(edge.target)]).filter(([a, b]) => a && b);
    // Dense shared-category views should remain spacious instead of collapsing.
    const strength = 0.014 / Math.max(1, links.length / Math.max(1, points.length));
    for (let step = 0; step < 300; step++) {
      for (let a = 0; a < points.length; a++) {
        const p = points[a];
        for (let b = a + 1; b < points.length; b++) {
          const q = points[b];
          const dx = p.x - q.x, dy = p.y - q.y;
          const d = Math.max(1, Math.hypot(dx, dy));
          const force = 1800 / (d * d) + Math.max(0, 30 - d) * 0.08;
          const fx = dx / d * force, fy = dy / d * force;
          p.vx += fx; p.vy += fy; q.vx -= fx; q.vy -= fy;
        }
      }
      for (const [p, q] of links) {
        const dx = q.x - p.x, dy = q.y - p.y, d = Math.max(1, Math.hypot(dx, dy));
        const force = (d - 58) * strength;
        const fx = dx / d * force, fy = dy / d * force;
        p.vx += fx; p.vy += fy; q.vx -= fx; q.vy -= fy;
      }
      for (const p of points) {
        p.vx = (p.vx - p.x * 0.003) * 0.65; p.vy = (p.vy - p.y * 0.003) * 0.65;
        p.x += p.vx; p.y += p.vy;
      }
    }
    const xExtent = Math.max(1, ...points.map(p => Math.abs(p.x) / 470));
    const yExtent = Math.max(1, ...points.map(p => Math.abs(p.y) / 290));
    return new Map(points.map(p => [p.id, { x: 550 + p.x / xExtent, y: 360 + p.y / yExtent }]));
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { connectionsFor, layout };
  if (typeof document === "undefined") return;
  const dataElement = document.getElementById("world-graph-data");
  if (!dataElement) return;
  const data = JSON.parse(dataElement.textContent);
  const $ = id => document.getElementById(id);
  const svg = $("world-network"), camera = $("network-camera");
  const nodeLayer = $("network-nodes"), edgeLayer = $("network-edges");
  const nodesById = new Map(data.nodes.map(node => [node.id, node]));
  const svgElement = (name, attributes = {}) => {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
    return element;
  };
  const element = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  let connectionMode = "recorded", colorMode = "cycle", category = null;
  let selected = null, visible = data.nodes, visibleIds = new Set();
  let edges = connectionsFor(data, connectionMode), shownEdges = [], basePositions = layout(data.nodes, edges);
  let viewHeight = 720, positions = basePositions;
  let nodeElements = new Map(), edgeElements = [], zoom = 1, panX = 0, panY = 0;
  const valuesFor = node => node.classes[colorMode].length ? node.classes[colorMode] : [UNCLASSIFIED];
  const labelFor = (dimension, id) => data.classifications[dimension].values.find(value => value.id === id)?.label || "Unclassified";
  function colorFor(id) {
    if (id === UNCLASSIFIED) return "#87909a";
    const index = data.classifications[colorMode].values.findIndex(value => value.id === id);
    return PALETTE[Math.max(0, index) % PALETTE.length];
  }
  function applyCamera() {
    camera.setAttribute("transform", `translate(${panX} ${panY}) scale(${zoom})`);
    svg.classList.toggle("is-zoomed", zoom > 1.8);
    $("graph-zoom-in").disabled = zoom >= 6;
    $("graph-zoom-out").disabled = zoom <= 0.4;
  }
  function fit() {
    if (!visible.length) { zoom = 1; panX = panY = 0; applyCamera(); return; }
    const points = visible.map(node => positions.get(node.id));
    const minX = Math.min(...points.map(p => p.x)) - 48, maxX = Math.max(...points.map(p => p.x)) + 48;
    const minY = Math.min(...points.map(p => p.y)) - 35, maxY = Math.max(...points.map(p => p.y)) + 35;
    zoom = Math.min(2.8, 1050 / Math.max(1, maxX - minX), (viewHeight - 40) / Math.max(1, maxY - minY));
    panX = 550 - (minX + maxX) / 2 * zoom; panY = viewHeight / 2 - (minY + maxY) / 2 * zoom;
    applyCamera();
  }
  function zoomAt(factor, x = 550, y = viewHeight / 2) {
    const next = Math.max(0.4, Math.min(6, zoom * factor));
    panX = x - (x - panX) * next / zoom; panY = y - (y - panY) * next / zoom;
    zoom = next; applyCamera();
  }
  function showTooltip(node) {
    const tooltip = $("graph-tooltip");
    tooltip.replaceChildren(element("strong", node.title), element("span", valuesFor(node).map(id => labelFor(colorMode, id)).join(" · ")));
    tooltip.hidden = false;
  }
  function paintNetwork() {
    edgeLayer.replaceChildren(); nodeLayer.replaceChildren(); nodeElements = new Map(); edgeElements = [];
    const nodeScale = Math.max(1, 900 / Math.max(300, svg.clientWidth));
    const degree = new Map();
    for (const edge of shownEdges) for (const id of [edge.source, edge.target]) degree.set(id, (degree.get(id) || 0) + 1);
    const overviewLabels = new Set(), labelBounds = [];
    for (const node of [...visible].sort((a, b) => (degree.get(b.id) || 0) - (degree.get(a.id) || 0))) {
      if (!degree.get(node.id) || overviewLabels.size >= (svg.clientWidth < 600 ? 3 : 8)) break;
      const p = positions.get(node.id), width = node.title.length * 7 * nodeScale;
      const left = p.x > 750 ? p.x - width - 14 * nodeScale : p.x + 14 * nodeScale;
      const bounds = { left, right: left + width, top: p.y - 14 * nodeScale, bottom: p.y + 12 * nodeScale };
      if (bounds.left < 10 || bounds.right > 1090 || labelBounds.some(b => bounds.left < b.right + 10 && bounds.right > b.left - 10 && bounds.top < b.bottom + 10 && bounds.bottom > b.top - 10)) continue;
      overviewLabels.add(node.id); labelBounds.push(bounds);
    }
    for (const edge of shownEdges) {
      const a = positions.get(edge.source), b = positions.get(edge.target);
      const line = svgElement("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: `network-edge edge-${edge.kind}` });
      edgeLayer.append(line); edgeElements.push({ edge, line });
    }
    for (const node of visible) {
      const p = positions.get(node.id), colors = valuesFor(node).map(colorFor);
      const group = svgElement("g", { transform: `translate(${p.x} ${p.y})`, class: "network-node", role: "button", tabindex: "0",
        "aria-label": `${node.title}. ${valuesFor(node).map(id => labelFor(colorMode, id)).join(", ")}. Select story.` });
      const title = svgElement("title"); title.textContent = node.title; group.append(title);
      group.append(svgElement("circle", { r: 14 * nodeScale, class: "node-hit" }));
      group.append(svgElement("circle", { r: 8 * nodeScale, fill: colors[0], class: "node-dot" }));
      if (colors.length > 1) {
        colors.forEach((color, i) => group.append(svgElement("circle", {
          r: 9 * nodeScale, fill: "none", stroke: color, "stroke-width": 4 * nodeScale,
          "stroke-dasharray": `${2 * Math.PI * 9 * nodeScale / colors.length} ${2 * Math.PI * 9 * nodeScale * (1 - 1 / colors.length)}`,
          transform: `rotate(${i * 360 / colors.length - 90})`,
        })));
      }
      const label = svgElement("text", { x: (p.x > 750 ? -14 : 14) * nodeScale, y: 4 * nodeScale,
        "text-anchor": p.x > 750 ? "end" : "start", class: "node-title" }); label.textContent = node.title; group.append(label);
      label.style.fontSize = `${14 * nodeScale}px`;
      group.classList.toggle("has-overview-label", overviewLabels.has(node.id));
      group.addEventListener("click", () => selectStory(node.id));
      group.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectStory(node.id, true); }
      });
      group.addEventListener("mouseenter", () => showTooltip(node));
      group.addEventListener("mouseleave", () => { $("graph-tooltip").hidden = true; });
      group.addEventListener("focus", () => showTooltip(node));
      group.addEventListener("blur", () => { $("graph-tooltip").hidden = true; });
      nodeLayer.append(group); nodeElements.set(node.id, group);
    }
    for (const id of overviewLabels) nodeLayer.append(nodeElements.get(id));
    highlight();
  }
  function highlight() {
    const neighbors = new Set([selected]);
    shownEdges.filter(edge => edge.source === selected || edge.target === selected).forEach(edge => {
      neighbors.add(edge.source); neighbors.add(edge.target);
    });
    for (const [id, group] of nodeElements) {
      group.classList.toggle("is-dimmed", Boolean(selected) && !neighbors.has(id));
      group.classList.toggle("is-selected", id === selected);
      group.classList.toggle("is-neighbor", Boolean(selected) && id !== selected && neighbors.has(id));
      group.setAttribute("aria-pressed", String(id === selected));
    }
    for (const { edge, line } of edgeElements) {
      const linked = selected && (edge.source === selected || edge.target === selected);
      line.classList.toggle("is-highlighted", Boolean(linked));
      line.classList.toggle("is-dimmed", Boolean(selected) && !linked);
    }
    if (selected && nodeElements.has(selected)) nodeLayer.append(nodeElements.get(selected));
    for (const button of $("graph-story-list").querySelectorAll("button")) button.setAttribute("aria-pressed", String(button.dataset.story === selected));
  }
  function selectStory(id, focusDetails = false) {
    selected = id; setExplorer(true); highlight(); renderDetail();
    $("graph-sidebar").scrollTop = 0;
    if (focusDetails) document.querySelector(".graph-read-link").focus({ preventScroll: true });
    if (window.matchMedia("(max-width: 760px)").matches) $("graph-sidebar").scrollIntoView({ block: "start" });
  }
  function clearSelection() {
    const previous = selected; selected = null; highlight(); renderDetail();
    if (previous) nodeElements.get(previous)?.focus({ preventScroll: true });
    $("graph-tooltip").hidden = true;
  }
  function setExplorer(open) {
    $("graph-sidebar").hidden = !open;
    document.querySelector(".graph-workspace").classList.toggle("explorer-open", open);
    $("graph-explorer").setAttribute("aria-expanded", String(open));
  }
  $("graph-explorer").addEventListener("click", () => {
    const open = $("graph-sidebar").hidden; setExplorer(open);
    if (open) $("graph-sidebar").querySelector(".graph-read-link, #graph-story-list button")?.focus();
  });
  $("graph-close-explorer").addEventListener("click", () => {
    setExplorer(false);
    const controls = document.querySelector(".graph-controls-toggle");
    (controls.open ? $("graph-explorer") : controls.querySelector("summary")).focus();
  });
  function renderDetail() {
    const panel = $("graph-detail"); panel.replaceChildren();
    if (!selected) {
      panel.append(element("p", "Start anywhere", "graph-eyebrow"), element("h2", "Every point opens a story."),
        element("p", "Select a point to see its classifications and the stories connected to it. Use the color key to focus on a group.", "graph-detail-hint"));
      const help = element("p", "Stories can belong to several history threads. Their colored rings show every membership.", "graph-detail-hint");
      panel.append(help); return;
    }
    const node = nodesById.get(selected);
    const heading = element("div", undefined, "graph-detail-heading");
    heading.append(element("p", "Selected story", "graph-eyebrow"));
    const close = element("button", "Clear", "graph-clear-selection"); close.type = "button";
    close.addEventListener("click", clearSelection); heading.append(close); panel.append(heading);
    const card = element("div", undefined, "graph-selected-card");
    const cover = element("img"); cover.src = node.cover; cover.alt = `Cover art for ${node.title}`; cover.width = 60; cover.height = 107;
    const copy = element("div"); copy.append(element("h2", node.title));
    const link = element("a", "Read story ↗", "graph-read-link"); link.href = node.href; copy.append(link); card.append(cover, copy); panel.append(card);
    const dl = element("dl", undefined, "graph-classifications");
    for (const key of ["cycle", "era", "magic", "history", "evidence", "canon", "rating"]) {
      const row = element("div"); row.append(element("dt", data.classifications[key].label),
        element("dd", node.classes[key].length ? node.classes[key].map(id => labelFor(key, id)).join(" · ") : "Unclassified")); dl.append(row);
    }
    panel.append(dl);
    if (node.placementNote) {
      const note = element("details", undefined, "graph-placement"); note.append(element("summary", "About the proposed placement"), element("p", node.placementNote)); panel.append(note);
    }
    const related = shownEdges.filter(edge => edge.source === selected || edge.target === selected);
    panel.append(element("h3", `${related.length} connection${related.length === 1 ? "" : "s"} in this view`));
    if (!related.length) panel.append(element("p", "No connections in the current view. Try another connection lens or clear your filters.", "graph-detail-hint"));
    const list = element("ul", undefined, "graph-related");
    for (const edge of related) {
      const other = nodesById.get(edge.source === selected ? edge.target : edge.source);
      const li = element("li"), button = element("button", other.title); button.type = "button";
      button.addEventListener("click", () => selectStory(other.id, true));
      const kind = { direct: "Direct", historical: "Historical interpretation", echo: "Thematic echo", shared: "Shared classification" }[edge.kind];
      li.append(button, element("span", `${kind} · ${edge.label}`, "graph-relation-label"));
      const detail = element("details"); detail.append(element("summary", "Why these connect"), element("p", edge.note));
      if (edge.basis) detail.append(element("p", `Basis: ${edge.basis}.`));
      if (edge.ordering === "before") detail.append(element("p", `Relative order: ${nodesById.get(edge.source).title} → ${nodesById.get(edge.target).title}.`));
      li.append(detail); list.append(li);
    }
    panel.append(list);
  }
  function baseVisible() {
    const query = $("graph-search").value.trim().toLocaleLowerCase(), status = $("graph-status").value;
    return data.nodes.filter(node => (!query || node.title.toLocaleLowerCase().includes(query)) &&
      (status === "all" || node.canon === (status === "canon")));
  }
  function renderLegend(base) {
    const classification = data.classifications[colorMode];
    $("graph-key-title").textContent = `Color by ${classification.label.toLowerCase()}`;
    $("graph-key-description").textContent = `${classification.description} Select a color to filter; select it again to show all.`;
    $("graph-clear-category").hidden = category === null;
    const legend = $("graph-legend"); legend.replaceChildren();
    const values = [...classification.values, { id: UNCLASSIFIED, label: "Unclassified" }];
    for (const value of values) {
      const count = base.filter(node => valuesFor(node).includes(value.id)).length;
      if (!count && value.id !== category) continue;
      const button = element("button"); button.type = "button"; button.dataset.category = value.id; button.setAttribute("aria-pressed", String(category === value.id));
      const dot = element("i"); dot.style.backgroundColor = colorFor(value.id); dot.setAttribute("aria-hidden", "true");
      button.append(dot, element("span", value.label), element("span", String(count), "graph-legend-count"));
      button.addEventListener("click", () => {
        category = category === value.id ? null : value.id; update();
        [...legend.querySelectorAll("button")].find(item => item.dataset.category === value.id)?.focus({ preventScroll: true });
      }); legend.append(button);
    }
  }
  function renderList() {
    $("graph-list-summary").textContent = `Browse ${visible.length} ${visible.length === 1 ? "story" : "stories"}`;
    const list = $("graph-story-list"); list.replaceChildren();
    for (const node of [...visible].sort((a, b) => a.title.localeCompare(b.title))) {
      const button = element("button", node.title); button.type = "button"; button.dataset.story = node.id;
      button.setAttribute("aria-pressed", String(selected === node.id));
      const dot = element("i"); dot.style.backgroundColor = colorFor(valuesFor(node)[0]); dot.setAttribute("aria-hidden", "true"); button.prepend(dot);
      button.addEventListener("click", () => selectStory(node.id, true)); list.append(button);
    }
  }
  function update({ refit = true } = {}) {
    const base = baseVisible(); visible = base.filter(node => category === null || valuesFor(node).includes(category));
    visibleIds = new Set(visible.map(node => node.id));
    if (selected && !visibleIds.has(selected)) selected = null;
    shownEdges = edges.filter(edge => visibleIds.has(edge.source) && visibleIds.has(edge.target));
    $("graph-summary").textContent = `${visible.length} of ${data.nodes.length} stories · ${shownEdges.length} connections`;
    $("graph-empty").hidden = visible.length !== 0;
    $("graph-tooltip").hidden = true;
    renderLegend(base); paintNetwork(); renderDetail(); renderList();
    if (refit) fit();
    const explanations = {
      recorded: "Recorded links bring together direct connections, proposed historical interpretations, and thematic echoes. Select a story to read the reason and evidence behind each link.",
      direct: "Direct links retain a recorded relationship or supplied reading sequence. Read each link for its scope and basis; a connection does not necessarily mean shared characters or a sequel.",
      historical: "These links are proposed interpretations of the world's history. They are not established causal links or confirmed continuity.",
      echo: "Thematic echoes connect resonant ideas and situations. They do not imply common events, characters, or causes.",
      era: "Each line joins two stories in the same proposed era. This is a shared classification, not proof that their events overlap or their characters meet.",
      history: "Each line joins two cited anchors in a recurring history thread. Stories can share several threads; select a story to see which ones.",
      none: "Connections are hidden. Explore the color classifications, or choose a connection lens to bring the links back.",
    };
    $("graph-edge-explanation").textContent = explanations[connectionMode];
    document.querySelector(".graph-line-key").hidden = ["era", "history", "none"].includes(connectionMode);
  }
  $("graph-connections").addEventListener("change", event => {
    connectionMode = event.target.value; edges = connectionsFor(data, connectionMode); basePositions = layout(data.nodes, edges); scalePositions(); update();
  });
  $("graph-color").addEventListener("change", event => {
    const refit = category !== null; colorMode = event.target.value; category = null; update({ refit });
  });
  $("graph-status").addEventListener("change", () => update());
  $("graph-search").addEventListener("input", () => update());
  $("graph-labels").addEventListener("change", event => svg.classList.toggle("show-titles", event.target.checked));
  $("graph-clear-category").addEventListener("click", () => {
    category = null; update(); document.querySelector(".graph-floating-key > summary").focus();
  });
  $("graph-reset").addEventListener("click", () => {
    connectionMode = "recorded"; colorMode = "cycle"; category = null; selected = null;
    $("graph-connections").value = "recorded"; $("graph-color").value = "cycle"; $("graph-status").value = "all";
    $("graph-search").value = ""; $("graph-labels").checked = false; svg.classList.remove("show-titles");
    setExplorer(false); document.querySelector(".graph-floating-key").open = false;
    edges = connectionsFor(data, connectionMode); basePositions = layout(data.nodes, edges); scalePositions(); update();
  });
  $("graph-zoom-in").addEventListener("click", () => zoomAt(1.3));
  $("graph-zoom-out").addEventListener("click", () => zoomAt(1 / 1.3));
  $("graph-fit").addEventListener("click", fit);
  function svgPoint(event) {
    return new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse());
  }
  svg.addEventListener("wheel", event => {
    event.preventDefault(); const p = svgPoint(event); zoomAt(event.deltaY < 0 ? 1.12 : 1 / 1.12, p.x, p.y);
  }, { passive: false });
  let drag = null;
  svg.addEventListener("pointerdown", event => {
    if (event.button !== 0 || event.target.closest(".network-node")) return;
    const p = svgPoint(event); drag = { id: event.pointerId, x: p.x, y: p.y, panX, panY };
    svg.setPointerCapture(event.pointerId); svg.classList.add("is-dragging");
  });
  svg.addEventListener("pointermove", event => {
    if (!drag || drag.id !== event.pointerId) return;
    const p = svgPoint(event); panX = drag.panX + p.x - drag.x; panY = drag.panY + p.y - drag.y; applyCamera();
  });
  function endDrag() { drag = null; svg.classList.remove("is-dragging"); }
  svg.addEventListener("pointerup", endDrag); svg.addEventListener("pointercancel", endDrag);
  svg.addEventListener("lostpointercapture", endDrag);
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") clearSelection();
  });
  const missing = data.metadata.unclassifiedCount;
  $("graph-coverage").textContent = data.metadata.sourceAvailable
    ? `All ${data.nodes.length} published stories are here. The retained world model classifies ${data.metadata.classifiedCount}; ${missing} ${missing === 1 ? "story has" : "stories have"} no placement yet. Unclassified stories stay visible, even without recorded links.`
    : `All ${data.nodes.length} published stories are here. No world classifications are available in this snapshot yet. Canon status and content rating remain available.`;
  function scalePositions() {
    positions = new Map([...basePositions].map(([id, p]) => [id, { x: p.x, y: p.y / 720 * viewHeight }]));
  }
  const mobile = window.matchMedia("(max-width: 760px)");
  const compactControls = () => { document.querySelector(".graph-controls-toggle").open = !mobile.matches; };
  mobile.addEventListener("change", compactControls); compactControls();
  new ResizeObserver(() => {
    const bounds = svg.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return;
    const height = 1100 * bounds.height / bounds.width;
    if (Math.abs(height - viewHeight) < 0.1) return;
    viewHeight = height; svg.setAttribute("viewBox", `0 0 1100 ${viewHeight}`);
    scalePositions(); paintNetwork(); fit();
  }).observe(svg);
  update();
})();
