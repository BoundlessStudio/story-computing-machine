"""The world graph's HTML shell; the network uses publication snapshots only."""

import html
import json


def render_graph(data: dict) -> str:
    # An HTML script element is raw text even when its type is application/json.
    payload = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c").replace("&", "\\u0026")
    links = "".join(
        f'<li><a href="{html.escape(node["href"], quote=True)}">{html.escape(node["title"])}</a></li>'
        for node in data["nodes"]
    )
    return '''
<details class="graph-controls-toggle" open><summary>Graph controls</summary>
<section class="graph-controls" aria-label="Graph controls">
  <label>Connect by<select id="graph-connections">
    <option value="recorded">All recorded connections</option>
    <option value="direct">Direct connections</option>
    <option value="historical">Historical interpretations</option>
    <option value="echo">Thematic echoes</option>
    <option value="era">Shared era</option>
    <option value="history">Shared history thread</option>
    <option value="none">No connections</option>
  </select></label>
  <label>Color by<select id="graph-color">
    <option value="cycle">World cycle</option><option value="magic">Magic phase</option>
    <option value="history">History threads</option><option value="evidence">Placement evidence</option>
    <option value="canon">Canon status</option><option value="rating">Content rating</option>
  </select></label>
  <label>Show<select id="graph-status"><option value="all">All stories</option>
    <option value="canon">Canon stories</option><option value="noncanon">Non-canon stories</option>
  </select></label>
  <label class="graph-search-label">Find a story<input id="graph-search" type="search" placeholder="Search titles…" autocomplete="off"></label>
  <button id="graph-reset" type="button">Reset view</button>
  <button id="graph-explorer" type="button" aria-expanded="false" aria-controls="graph-sidebar">Browse stories</button>
</section></details>
<div class="graph-workspace">
  <section class="graph-map" aria-label="Interactive story network">
    <div class="graph-map-bar"><div class="graph-map-title"><h1 id="world-title">World graph</h1><p id="graph-summary" role="status" aria-live="polite"></p></div>
      <div class="graph-zoom" role="group" aria-label="Map navigation">
        <button type="button" id="graph-zoom-out" aria-label="Zoom out">−</button>
        <button type="button" id="graph-fit">Fit all</button>
        <button type="button" id="graph-zoom-in" aria-label="Zoom in">+</button>
      </div>
    </div>
    <svg id="world-network" viewBox="0 0 1100 720" role="group" aria-labelledby="network-title network-description">
      <title id="network-title">Story world network</title>
      <desc id="network-description">Each circle is a story. Select a circle or use the story list to inspect its connections. Drag the background to pan; use the zoom buttons or scroll to zoom.</desc>
      <g id="network-camera"><g id="network-edges" aria-hidden="true"></g><g id="network-nodes"></g></g>
    </svg>
    <p class="graph-empty" id="graph-empty" hidden>No stories match. Clear the search or reset the view.</p>
    <details class="graph-floating-key"><summary>Color key</summary>
      <section class="graph-key" aria-label="Color legend">
        <div class="graph-key-heading"><h2 id="graph-key-title">Color key</h2><button type="button" id="graph-clear-category" hidden>Show every color</button></div>
        <p id="graph-key-description"></p><div id="graph-legend"></div>
      </section>
    </details>
    <div class="graph-map-footer"><span>Drag to pan · Scroll to zoom</span>
      <label><input type="checkbox" id="graph-labels"> Show titles</label></div>
    <div class="graph-tooltip" id="graph-tooltip" hidden></div>
  </section>
  <aside class="graph-sidebar" id="graph-sidebar" aria-label="Story explorer" hidden>
    <div class="graph-sidebar-heading"><span>Story explorer</span><button id="graph-close-explorer" type="button" aria-label="Close story explorer">×</button></div>
    <section class="graph-detail" id="graph-detail" aria-label="Selected story"></section>
    <details class="graph-story-list" open><summary id="graph-list-summary">Browse stories</summary>
      <div id="graph-story-list"></div>
    </details>
  </aside>
</div>
<details class="graph-about-toggle"><summary>How to read this graph</summary><section class="graph-about" aria-label="About this graph">
  <div><h2>Read the connections</h2><p id="graph-edge-explanation"></p>
    <p class="graph-line-key"><span><i class="key-direct"></i>Direct</span><span><i class="key-historical"></i>Historical interpretation</span><span><i class="key-echo"></i>Thematic echo</span></p></div>
  <div><h2>A map for exploration</h2><p id="graph-coverage"></p>
    <p>Grouping and history threads are editorial lenses. A shared color or thread does not establish a shared character, place, origin, or cause. Positions and distances are a reading aid, not dates or geography.</p></div>
</section></details>
<noscript><p>Enable JavaScript to explore the network. Every published story is also available below.</p><ul>''' + links + '''</ul></noscript>
<script type="application/json" id="world-graph-data">''' + payload + '''</script>
'''
