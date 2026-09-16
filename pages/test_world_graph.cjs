"use strict";

const assert = require("node:assert/strict");
const { test } = require("node:test");
const { connectionsFor, layout } = require("./world-graph.js");

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
