"use strict";

const assert = require("node:assert/strict");
const { test } = require("node:test");
const { connectionsFor, filterGraph, layout } = require("./world-graph.js");

function fixture() {
  return {
    nodes: [
      { id: "beta", classes: { era: ["earlier"], history: ["memory", "authority"] } },
      { id: "alpha", classes: { era: ["earlier"], history: ["memory", "authority"] } },
      { id: "gamma", classes: { era: ["later"], history: ["authority"] } },
      { id: "unplaced-one", classes: { era: [], history: [] } },
      { id: "unplaced-two", classes: { era: [], history: [] } },
    ],
    edges: [
      { id: "sequence", source: "beta", target: "alpha", kind: "direct", ordering: "before",
        basis: "reading-sequence", label: "A supplied sequence", note: "The interval is unknown." },
      { id: "interpretation", source: "alpha", target: "gamma", kind: "historical", ordering: "none",
        basis: "proposed", label: "A proposed relation", note: "No shared cause is established." },
      { id: "echo", source: "gamma", target: "beta", kind: "echo", ordering: "none",
        basis: "thematic", label: "A recurring idea", note: "This does not establish chronology." },
    ],
    classifications: {
      era: { values: [{ id: "earlier", label: "Earlier histories" }, { id: "later", label: "Later histories" }] },
      history: { values: [{ id: "memory", label: "Memory" }, { id: "authority", label: "Authority" }] },
    },
  };
}

function freezeDeep(value) {
  if (value && typeof value === "object") {
    Object.values(value).forEach(freezeDeep);
    Object.freeze(value);
  }
  return value;
}

function assertCompleteFiniteLayout(nodes, edges) {
  const first = layout(nodes, edges);
  const second = layout(nodes, edges);
  assert.ok(first instanceof Map);
  assert.deepEqual(first, second, "Identical inputs must produce stable positions");
  assert.equal(first.size, nodes.length);
  assert.deepEqual(new Set(first.keys()), new Set(nodes.map(node => node.id)));
  for (const [id, point] of first) {
    assert.ok(Number.isFinite(point.x), `${id} has a finite horizontal position`);
    assert.ok(Number.isFinite(point.y), `${id} has a finite vertical position`);
  }
}

test("recorded connections preserve every provenance field and source direction", () => {
  const data = fixture();
  const original = structuredClone(data.edges);
  const result = connectionsFor(data, "recorded");
  assert.deepEqual(result, original);
  assert.equal(result[0].source, "beta");
  assert.equal(result[0].target, "alpha");
  assert.equal(result[0].basis, "reading-sequence");
  assert.equal(result[0].ordering, "before");
});

test("direct, historical, and thematic filters return only their recorded edge kinds", () => {
  const data = fixture();
  for (const kind of ["direct", "historical", "echo"]) {
    const expected = data.edges.find(edge => edge.kind === kind);
    assert.deepEqual(connectionsFor(data, kind), [expected]);
  }
});

test("no-connections mode does not change recorded data", () => {
  const data = fixture();
  assert.deepEqual(connectionsFor(data, "none"), []);
  assert.equal(data.edges.length, 3);
});

test("shared era connects only explicit members, leaving missing classifications isolated", () => {
  const edges = connectionsFor(fixture(), "era");
  assert.equal(edges.length, 1);
  assert.equal(edges[0].source, "alpha");
  assert.equal(edges[0].target, "beta");
  assert.equal(edges[0].label, "Earlier histories");
  assert.equal(edges[0].kind, "shared");
  assert.equal(edges[0].basis, "editorial");
  assert.equal(edges[0].ordering, "none");
  assert.match(edges[0].note, /does not establish/);
});

test("shared histories deduplicate pairs while retaining every common membership", () => {
  const edges = connectionsFor(fixture(), "history");
  assert.equal(edges.length, 3);
  assert.equal(new Set(edges.map(edge => edge.id)).size, 3);
  const sharedTwice = edges.find(edge => edge.source === "alpha" && edge.target === "beta");
  assert.ok(sharedTwice);
  assert.deepEqual(sharedTwice.labels, ["Memory", "Authority"]);
  assert.equal(sharedTwice.label, "Memory · Authority");
  for (const edge of edges) {
    assert.ok(!edge.source.startsWith("unplaced") && !edge.target.startsWith("unplaced"));
    assert.notEqual(edge.source, edge.target);
    assert.equal(edge.kind, "shared");
    assert.equal(edge.basis, "editorial");
    assert.equal(edge.ordering, "none");
  }
  assert.deepEqual(edges.find(edge => edge.source === "alpha" && edge.target === "gamma").labels,
    ["Authority"]);
});

test("all connection lenses and layouts leave nested input snapshots unchanged", () => {
  const data = freezeDeep(fixture());
  const original = structuredClone(data);
  for (const mode of ["recorded", "direct", "historical", "echo", "era", "history", "none"]) {
    const edges = connectionsFor(data, mode);
    layout(data.nodes, edges);
  }
  assert.deepEqual(data, original);
});

test("layout includes isolated nodes and produces deterministic finite coordinates", () => {
  const data = fixture();
  assertCompleteFiniteLayout(data.nodes, data.edges);
  assertCompleteFiniteLayout(data.nodes, []);
});

test("empty and singleton layouts remain valid without requiring connections", () => {
  assertCompleteFiniteLayout([], []);
  assertCompleteFiniteLayout([{ id: "only-story" }], []);
});

test("dense shared-category layout remains deterministic and finite", () => {
  const nodes = Array.from({ length: 64 }, (_, i) => ({
    id: `story-${String(i).padStart(2, "0")}`, classes: { history: ["common"] },
  }));
  const data = freezeDeep({
    nodes, edges: [], classifications: { history: { values: [{ id: "common", label: "Common thread" }] } },
  });
  const edges = connectionsFor(data, "history");
  assert.equal(edges.length, nodes.length * (nodes.length - 1) / 2);
  assertCompleteFiniteLayout(nodes, freezeDeep(edges));
});

function filterFixture() {
  return {
    nodes: [
      { id: "alpha", title: "Anchor story", canon: true, classes: { cycle: ["north"] } },
      { id: "beta", title: "Bridge story", canon: true, classes: { cycle: ["north"] } },
      { id: "gamma", title: "Beyond story", canon: false, classes: { cycle: ["north"] } },
      { id: "delta", title: "Distant story", canon: false, classes: { cycle: ["south"] } },
      { id: "unplaced-one", title: "Unplaced harbor", canon: true, classes: { cycle: [] } },
      { id: "unplaced-two", title: "Unplaced island", canon: true, classes: { cycle: [] } },
      { id: "lonely", title: "Lonely story", canon: true, classes: { cycle: [] } },
    ],
    edges: [
      { id: "ab", source: "alpha", target: "beta", kind: "direct", basis: "established", ordering: "before" },
      { id: "bc", source: "beta", target: "gamma", kind: "echo", basis: "thematic", ordering: "none" },
      { id: "cd", source: "gamma", target: "delta", kind: "historical", basis: "proposed", ordering: "none" },
      { id: "au", source: "alpha", target: "unplaced-one", kind: "echo", basis: "thematic", ordering: "none" },
      { id: "uv", source: "unplaced-one", target: "unplaced-two", kind: "direct", basis: "reading-sequence", ordering: "before" },
    ],
  };
}

const nodeIds = result => result.nodes.map(node => node.id);
const edgeIds = result => result.edges.map(edge => edge.id);

test("graph defaults to linked stories and includes isolates only when requested", () => {
  const data = filterFixture();
  const linked = filterGraph(data.nodes, data.edges);
  assert.deepEqual(nodeIds(linked), ["alpha", "beta", "gamma", "delta", "unplaced-one", "unplaced-two"]);
  assert.deepEqual(linked.edges, data.edges);
  assert.equal(linked.matchCount, 6);
  const all = filterGraph(data.nodes, data.edges, { includeUnlinked: true });
  assert.deepEqual(all.nodes, data.nodes);
  assert.deepEqual(all.edges, data.edges);
  assert.equal(all.matchCount, 7);
});

test("a graph without links stays empty unless unlinked stories are enabled", () => {
  const { nodes } = filterFixture();
  assert.deepEqual(filterGraph(nodes, []), { nodes: [], edges: [], matchCount: 0 });
  assert.deepEqual(filterGraph(nodes, [], { includeUnlinked: true }), { nodes, edges: [], matchCount: nodes.length });
  assert.deepEqual(filterGraph([], []), { nodes: [], edges: [], matchCount: 0 });
});

test("search keeps one-hop neighbors and every induced link without expanding a second hop", () => {
  const data = filterFixture();
  const neighborsEdge = { id: "bu", source: "beta", target: "unplaced-one", kind: "echo" };
  const result = filterGraph(data.nodes, [...data.edges, neighborsEdge], { query: "  ANCHOR  " });
  assert.deepEqual(nodeIds(result), ["alpha", "beta", "unplaced-one"]);
  assert.deepEqual(edgeIds(result), ["ab", "au", "bu"]);
  assert.equal(result.matchCount, 1, "Neighbors must not inflate the title-match count");
  const bridge = filterGraph(data.nodes, data.edges, { query: "bridge" });
  assert.deepEqual(nodeIds(bridge), ["alpha", "beta", "gamma"]);
  assert.deepEqual(edgeIds(bridge), ["ab", "bc"]);
  assert.equal(bridge.matchCount, 1);
});

test("category and canon filters limit search neighbors before expansion", () => {
  const data = filterFixture();
  const north = filterGraph(data.nodes, data.edges, { category: "north", query: "anchor" });
  assert.deepEqual(nodeIds(north), ["alpha", "beta"]);
  assert.deepEqual(edgeIds(north), ["ab"]);
  const canon = filterGraph(data.nodes, data.edges, { status: "canon", query: "bridge" });
  assert.deepEqual(nodeIds(canon), ["alpha", "beta"]);
  assert.deepEqual(edgeIds(canon), ["ab"]);
  assert.deepEqual(filterGraph(data.nodes, data.edges, { status: "noncanon", query: "anchor" }),
    { nodes: [], edges: [], matchCount: 0 });
});

test("filters that remove all links also remove resulting isolates unless opted in", () => {
  const data = filterFixture();
  assert.deepEqual(filterGraph(data.nodes, data.edges, { category: "south" }),
    { nodes: [], edges: [], matchCount: 0 });
  const south = filterGraph(data.nodes, data.edges, { category: "south", includeUnlinked: true });
  assert.deepEqual(nodeIds(south), ["delta"]);
  assert.deepEqual(south.edges, []);
  assert.equal(south.matchCount, 1);

  const crossing = [{ id: "crossing", source: "alpha", target: "gamma" }];
  assert.deepEqual(filterGraph(data.nodes, crossing, { status: "noncanon" }),
    { nodes: [], edges: [], matchCount: 0 });
  const noncanon = filterGraph(data.nodes, crossing, { status: "noncanon", includeUnlinked: true });
  assert.deepEqual(nodeIds(noncanon), ["gamma", "delta"]);
  assert.deepEqual(noncanon.edges, []);
});

test("empty and unmatched searches report only visible matches", () => {
  const data = filterFixture();
  const empty = filterGraph(data.nodes, data.edges, { query: "   " });
  assert.equal(empty.matchCount, empty.nodes.length);
  assert.deepEqual(empty, filterGraph(data.nodes, data.edges));
  for (const includeUnlinked of [false, true]) {
    assert.deepEqual(filterGraph(data.nodes, data.edges, { query: "not-a-story-title", includeUnlinked }),
      { nodes: [], edges: [], matchCount: 0 });
  }
  assert.deepEqual(filterGraph(data.nodes, data.edges, { query: "lonely" }),
    { nodes: [], edges: [], matchCount: 0 });
  const isolatedMatch = filterGraph(data.nodes, data.edges, { query: "lonely", includeUnlinked: true });
  assert.deepEqual(nodeIds(isolatedMatch), ["lonely"]);
  assert.deepEqual(isolatedMatch.edges, []);
  assert.equal(isolatedMatch.matchCount, 1);
});

test("unclassified stories retain stored links and can be selected as a category", () => {
  const data = filterFixture();
  const result = filterGraph(data.nodes, data.edges, { category: "__unclassified__" });
  assert.deepEqual(nodeIds(result), ["unplaced-one", "unplaced-two"]);
  assert.deepEqual(edgeIds(result), ["uv"]);
  assert.equal(result.matchCount, 2);
  const all = filterGraph(data.nodes, data.edges, { category: "__unclassified__", includeUnlinked: true });
  assert.deepEqual(nodeIds(all), ["unplaced-one", "unplaced-two", "lonely"]);
  assert.deepEqual(edgeIds(all), ["uv"]);
});

test("graph filtering leaves frozen nodes, edges, classifications, and options unchanged", () => {
  const data = freezeDeep(filterFixture());
  const original = structuredClone(data);
  const options = freezeDeep({ query: "story", status: "canon", category: "north", color: "cycle", includeUnlinked: true });
  const originalOptions = structuredClone(options);
  filterGraph(data.nodes, data.edges, options);
  filterGraph(data.nodes, data.edges);
  assert.deepEqual(data, original);
  assert.deepEqual(options, originalOptions);
});
