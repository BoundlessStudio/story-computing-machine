"""Reader-facing orbital atlas, rendered entirely from the curated chronology."""

from __future__ import annotations

import html
import math


STATE_LABELS = {
    "old-magic": "Old magic",
    "long-dark": "The Long Dark",
    "new-magic": "New magic",
    "uncertain": "Unplaced in time",
    "off-axis": "Beyond the material clock",
}
EVIDENCE = {
    "boundary": "Worldline boundary",
    "constrained": "Established constraint",
    "relative": "Relative sequence",
    "contextual": "Contextual evidence",
    "undated": "Date unresolved",
}
LINK_LABELS = {"direct": "Direct connection", "historical": "Historical hypothesis", "echo": "Thematic echo"}
BASIS_LABELS = {"established": "Established chronology", "reading-sequence": "Supplied reading sequence",
                "proposed": "Proposed historical interpretation", "thematic": "A parallel, not a date"}


def esc(value):
    return html.escape(str(value), quote=True)


def orbit_map(cycles):
    """Navigate the proposed cycle sequence; orbital coordinates remain undated."""
    rings = []
    for index, cycle in enumerate(cycles):
        radius = 99 + index * (175 / max(1, len(cycles) - 1))
        angle = (-155 + index * 137.508) * math.pi / 180
        x = 340 + radius * math.cos(angle)
        y = 325 + radius * 0.79 * math.sin(angle)
        rings.append(
            f'<a href="#cycle-{esc(cycle.id)}" class="orbit-link state-{cycle.magic_state}" '
            f'data-orbit-title="{index + 1:02d} · {esc(cycle.title)}" data-orbit-state="{esc(STATE_LABELS[cycle.magic_state])}" '
            f'aria-label="Cycle {index + 1:02d}: {esc(cycle.title)}">'
            f'<title>{index + 1:02d} · {esc(cycle.title)}</title>'
            f'<ellipse cx="340" cy="325" rx="{radius:.2f}" ry="{radius * .79:.2f}" class="orbit-track"/>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="17" class="orbit-target"/>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" class="orbit-star"/>'
            f'<text x="{x + 8:.2f}" y="{y - 9:.2f}" class="orbit-number">{index + 1:02d}</text></a>'
        )
    ticks = []
    for index in range(120):
        angle = index * math.pi / 60
        outer, inner = 305, 292 if index % 5 == 0 else 300
        ticks.append(f'<path d="M{340 + inner * math.cos(angle):.2f},{325 + inner * math.sin(angle):.2f} L{340 + outer * math.cos(angle):.2f},{325 + outer * math.sin(angle):.2f}"/>')
    return (
        '<svg class="orbit-map" viewBox="0 0 680 660" role="group" aria-label="Orbital cycle navigator">'
        '<g class="orbit-instrument" aria-hidden="true">'
        f'{"".join(ticks)}<path d="M22 325H658 M340 10V640"/>'
        '<circle cx="340" cy="325" r="310"/><circle cx="340" cy="325" r="68"/>'
        '<ellipse cx="340" cy="325" rx="38" ry="68"/><path d="M274 307Q340 283 406 307 M274 343Q340 367 406 343"/></g>'
        f'{"".join(rings)}'
        '<g class="orbit-center" aria-hidden="true"><text x="340" y="318">ONE</text><text x="340" y="342">WORLD</text></g>'
        '<text class="orbit-caption" x="340" y="650" text-anchor="middle">CHOOSE A LIGHT. ENTER AN AGE.</text></svg>'
    )


def horizon(cycle, *, overview=False):
    """Pack possible era intervals in lanes; intersection never implies descent."""
    ends, bands = [], []
    for era in sorted(cycle.eras, key=lambda era: (era.window.start, era.window.end)):
        narrow = era.window.end - era.window.start < 15
        lane = len(ends) if narrow else next((index for index, end in enumerate(ends) if end <= era.window.start), len(ends))
        if lane == len(ends):
            ends.append(100 if narrow else era.window.end)
        else:
            ends[lane] = era.window.end
        bands.append(
            f'<a class="horizon-band{" narrow-horizon" if narrow else ""}{" end-horizon" if narrow and era.window.start > 50 else ""}" href="#era-{esc(era.id)}" '
            f'data-horizon-era="{esc(era.id)}" data-era-title="{esc(era.title)}" '
            f'data-era-description="{esc(era.description)}" '
            f'aria-label="{esc(era.title)}: {len(era.stories)} stories, proposed horizon" '
            f'title="{esc(era.title)} · {len(era.stories)} stories" '
            f'style="--start:{era.window.start:g}%;--range:{era.window.end-era.window.start:g}%;--lane:{lane}">'
            f'<span>{esc(era.title)}</span><small>{len(era.stories)} {"life" if len(era.stories) == 1 else "lives"}</small></a>'
        )
    return f'<div class="era-horizon{" overview-horizon" if overview else ""}" style="--lanes:{len(ends)}">{"".join(bands)}</div>'


def weave(cycles):
    rows = ''.join(
        f'<div class="weave-row state-{cycle.magic_state}"><a class="weave-cycle" href="#cycle-{esc(cycle.id)}">'
        f'<span>{index:02d}</span><strong>{esc(cycle.title)}</strong><small>{STATE_LABELS[cycle.magic_state]}</small></a>'
        f'{horizon(cycle, overview=True)}</div>' for index, cycle in enumerate(cycles, 1)
    )
    return (
        '<section class="atlas-weave" id="atlas-weave" aria-labelledby="weave-title">'
        '<header class="weave-heading"><div><p class="atlas-kicker">A palimpsest of civilizations</p>'
        '<h2 id="weave-title">Many lives.<br><em>One unfolding world.</em></h2></div>'
        '<p>Read the great turns downward. Within each turn, bands open from earlier to later. '
        'Overlapping bands leave room for societies living at the same time. Enter one to meet its people.</p></header>'
        '<div class="weave-key"><span class="band-swatch">Proposed era horizon</span>'
        '<span>Overlapping horizons ≠ a shared civilization</span><span>Distances are unmeasured</span></div>'
        '<div class="weave-tools"><div class="weave-toolbar"><div class="thread-controls" role="group" aria-label="Connections on the history map" hidden>'
        '<button type="button" data-thread-filter="direct" aria-pressed="true">Direct connections</button>'
        '<button type="button" data-thread-filter="historical" aria-pressed="false">Historical hypotheses</button>'
        '<button type="button" data-thread-filter="echo" aria-pressed="false">Thematic echoes</button>'
        '<button type="button" data-thread-filter="all" aria-pressed="false">All threads</button></div>'
        '<a href="#atlas-threads">Read the connection notes ↗</a></div><p class="weave-count" data-map-count aria-live="polite"></p>'
        '<p class="weave-readout" role="status" data-weave-readout>Follow a band to explore its era. Lines connect stories; they do not date the space between them.</p></div>'
        f'<div class="weave-surface" data-weave><svg class="weave-routes" aria-label="Connections between eras"></svg>{rows}</div>'
        '</section>'
    )


def depth_explorer(stories, timeline, locations):
    """Expose local historical layers without inventing Galactic coordinates."""
    panels, options = [], []
    for cycle in timeline.cycles:
        for slug in cycle.stories:
            span = timeline.story_spans.get(slug)
            moments = timeline.story_moments.get(slug, ())
            if not span or len(moments) < 3:
                continue
            story = stories[slug]
            options.append(f'<option value="depth-{esc(slug)}">{esc(story.title)}</option>')
            layers = ''.join(
                f'<li><span class="depth-number" aria-hidden="true">{index:02d}</span>'
                f'<p>{esc(moment)}</p></li>' for index, moment in enumerate(moments, 1)
            )
            panels.append(
                f'<details class="depth-history state-{cycle.magic_state}" id="depth-{esc(slug)}" '
                f'data-depth-history{" open" if not panels else ""}>'
                f'<summary>{esc(story.title)}</summary><div class="depth-cutaway">'
                '<div class="depth-art"><span class="depth-axis">Earlier traces ↓ Later lives</span>'
                f'<a href="stories/{esc(slug)}.html" aria-label="Read {esc(story.title)}">'
                f'<img src="{esc(story.cover)}" alt="" width="864" height="1536" loading="lazy"></a>'
                f'<span class="depth-cycle">Proposed cycle {locations[slug][0]:02d}</span></div>'
                f'<div class="depth-layers"><p class="atlas-kicker">The history carried inside this story</p>'
                f'<h3>{esc(story.title)}</h3><ol>{layers}</ol>'
                f'<p class="depth-scale">{esc(span.note)}</p>'
                f'<a class="depth-return" href="#story-{esc(slug)}" data-locate-story="{esc(slug)}">Find this life among its contemporaries ↗</a>'
                '</div></div></details>'
            )
    if not panels:
        return ''
    return (
        '<section class="atlas-depths" id="atlas-depths" aria-labelledby="depth-title">'
        '<header><div><p class="atlas-kicker">Beneath the present</p>'
        '<h2 id="depth-title">Every age has<br><em>older worlds inside it.</em></h2></div>'
        '<p>A forest grows over a vanished hall. A ruler inherits an ancient name. '
        'An ordinary evening carries centuries. Open a story and follow the layers it actually remembers.</p></header>'
        '<label class="depth-picker" hidden><span>Choose a history to unfold</span>'
        f'<select data-depth-picker>{"".join(options)}</select></label>'
        f'<div class="depth-histories">{"".join(panels)}</div>'
        '<p class="depth-footnote">These are intervals and sequences within individual stories. '
        'Layer thickness is symbolic; a remembered event can reach beyond its story’s proposed era.</p></section>'
    )


def render(catalog, timeline):
    stories = {story.slug: story for story in catalog.stories}
    locations = {slug: (number, cycle) for number, cycle in enumerate(timeline.cycles, 1) for slug in cycle.stories}
    depth_view = depth_explorer(stories, timeline, locations)
    depth_invitation = '<a class="atlas-deeper" href="#atlas-depths">Explore the histories within ↓</a>' if depth_view else ''
    story_eras = {slug: era for cycle in timeline.cycles for era in cycle.eras for slug in era.stories}
    related = {slug: [] for slug in stories}
    for connection in timeline.connections:
        related[connection.source].append(connection)
        related[connection.target].append(connection)

    directory, sections = [], []
    for number, cycle in enumerate(timeline.cycles, 1):
        directory.append(
            f'<a href="#cycle-{esc(cycle.id)}" class="cycle-entry state-{cycle.magic_state}" data-cycle-link="{esc(cycle.id)}">'
            f'<span>{number:02d}</span><strong>{esc(cycle.title)}</strong><small>{len(cycle.eras)} eras · {len(cycle.stories)} stories</small></a>'
        )
        events = {}
        for local_index, slug in enumerate(cycle.stories):
            story = stories[slug]
            era = story_eras[slug]
            placement = timeline.story_placements[slug]
            evidence = timeline.story_evidence[slug]
            moments = timeline.story_moments.get(slug, ())
            span = timeline.story_spans.get(slug)
            span_html = f'<p class="story-span"><b>{esc(span.start)} → {esc(span.end)}</b>{esc(span.note)}</p>' if span else ''
            moment_html = f'<ol class="story-moments">{"".join(f"<li>{esc(moment)}</li>" for moment in moments)}</ol>' if moments else ''
            connections = []
            for link in related[slug]:
                other = link.target if slug == link.source else link.source
                other_number, other_cycle = locations[other]
                crossing = f'Cycle {other_number:02d} · {story_eras[other].title}' if other_cycle.id != cycle.id else story_eras[other].title
                connections.append(
                    f'<li class="event-connection {link.kind}"><span>{LINK_LABELS[link.kind]} · {crossing}</span>'
                    f'<a href="#story-{esc(other)}" data-locate-story="{esc(other)}">{esc(stories[other].title)} <i aria-hidden="true">↗</i></a>'
                    f'<small>{esc(link.label)}</small><a class="connection-evidence" href="#thread-{esc(link.id)}">Connection notes</a></li>'
                )
            connection_html = f'<ul class="event-connections">{"".join(connections)}</ul>' if connections else ''
            details = (
                f'<details class="event-details" data-event-details><summary>Surviving evidence &amp; connections <span aria-hidden="true">+</span></summary>'
                f'<div>{moment_html}{span_html}{connection_html}</div></details>'
                if moments or span or connections else ''
            )
            events[slug] = (
                f'<article class="worldline-event evidence-{evidence}" id="story-{esc(slug)}" '
                f'data-story-slug="{esc(slug)}" '
                f'data-search="{esc(" ".join((story.title, cycle.title, era.title, era.description, *era.context, placement.note, *moments)).lower())}" '
                f'data-story-evidence="{evidence}">'
                '<div class="event-card">'
                f'<a class="atlas-cover" href="stories/{esc(slug)}.html" aria-label="Read {esc(story.title)}">'
                f'<img src="{esc(story.cover)}" alt="" width="864" height="1536" loading="lazy" decoding="async"></a>'
                '<div class="event-copy">'
                f'<span class="evidence evidence-{evidence}">{EVIDENCE[evidence]}</span>'
                f'<h4><a href="stories/{esc(slug)}.html">{esc(story.title)}</a></h4>'
                '<p class="placement-status">Era placement proposed</p>'
                f'<p class="event-placement">{esc(placement.note)}</p>{details}</div></div></article>'
            )
        era_panels = []
        for era_number, era in enumerate(cycle.eras, 1):
            context = ''.join(f'<li>{esc(observation)}</li>' for observation in era.context)
            peers = [peer for peer in cycle.eras if peer.id != era.id
                     and max(peer.window.start, era.window.start) < min(peer.window.end, era.window.end)]
            peers_html = ('<div class="era-peers"><span>May share a horizon with</span>'
                          + ''.join(f'<a href="#era-{esc(peer.id)}">{esc(peer.title)} ↗</a>' for peer in peers)
                          + '</div>') if peers else ''
            local_links = [link for link in timeline.connections if link.ordering == "before"
                           and link.source in era.stories and link.target in era.stories]
            paths = ''.join(
                f'<li><span>{BASIS_LABELS[link.basis]}</span><a href="#story-{esc(link.source)}">{esc(stories[link.source].title)}</a>'
                f'<b aria-label="before">→</b><a href="#story-{esc(link.target)}">{esc(stories[link.target].title)}</a></li>'
                for link in local_links
            )
            local_order = f'<ul class="era-local-order" aria-label="Known and proposed local sequences">{paths}</ul>' if paths else ''
            era_panels.append(
                f'<section class="history-era" id="era-{esc(era.id)}" data-era-section="{esc(era.id)}" '
                f'aria-labelledby="era-title-{esc(era.id)}">'
                '<header class="era-heading"><div class="era-introduction">'
                f'<p class="atlas-kicker">Cycle {number:02d} · A proposed era · {len(era.stories)} {"story" if len(era.stories) == 1 else "stories"}</p>'
                f'<h3 id="era-title-{esc(era.id)}">{esc(era.title)}</h3><p>{esc(era.description)}</p></div>'
                f'<div class="era-context"><span>Life in this era</span><ul>{context}</ul></div></header>'
                f'<p class="era-sequence-note"><span>Place in history</span>{esc(era.sequence_note)}</p>'
                f'{peers_html}{local_order}<p class="era-order-note">Lives within this horizon. Only the linked sequences establish an order.</p>'
                f'<div class="era-lives">{"".join(events[slug] for slug in era.stories)}</div></section>'
            )
        era_index = ''.join(f'<a href="#era-{esc(era.id)}">{esc(era.title)}</a>' for era in cycle.eras)
        sections.append(
            f'<section class="atlas-cycle state-{cycle.magic_state}" id="cycle-{esc(cycle.id)}" '
            f'data-cycle-section="{esc(cycle.id)}" data-magic-state="{cycle.magic_state}">'
            '<header class="cycle-heading"><div class="cycle-seal" aria-hidden="true">'
            f'<span>{number:02d}</span></div><div class="cycle-heading-copy">'
            f'<p class="atlas-kicker">{esc(cycle.eyebrow)} · {len(cycle.eras)} eras · {len(cycle.stories)} stories</p>'
            f'<h2>{esc(cycle.title)}</h2><p>{esc(cycle.description)}</p>'
            f'<p class="cycle-placement">{esc(cycle.sequence_note)}</p>'
            f'<nav class="cycle-horizons" aria-label="Proposed era horizons in cycle {number:02d}">{horizon(cycle)}</nav>'
            '<div class="cycle-strip-labels"><span>Earlier possible horizons</span><span>Later possible horizons →</span></div>'
            f'<nav class="cycle-era-index" aria-label="Eras in cycle {number:02d}">{era_index}</nav></div>'
            f'<span class="cycle-state">{STATE_LABELS[cycle.magic_state]}</span></header>'
            f'<div class="cycle-eras">{"".join(era_panels)}</div>'
            '<div class="cycle-passage" aria-hidden="true"><i></i><span>The world continues</span><i></i></div></section>'
        )

    thread_cards = []
    for link in timeline.connections:
        label = LINK_LABELS[link.kind]
        endpoints = ''.join(
            f'<a href="#story-{esc(slug)}" data-locate-story="{esc(slug)}">'
            f'<small>Cycle {locations[slug][0]:02d} · {esc(story_eras[slug].title)}</small><span>{esc(stories[slug].title)}</span></a>'
            for slug in (link.source, link.target)
        )
        thread_cards.append(
            f'<article class="thread-card {link.kind}" id="thread-{esc(link.id)}" data-thread-kind="{link.kind}" '
            f'data-from-era="{esc(story_eras[link.source].id)}" data-to-era="{esc(story_eras[link.target].id)}" '
            f'data-thread-label="{esc(link.label)}">'
            f'<span class="atlas-kicker">{label}</span><h3>{esc(link.label)}</h3>'
            f'<p class="thread-basis">{BASIS_LABELS[link.basis]}</p>'
            f'<div class="thread-endpoints">{endpoints}</div><p>{esc(link.note)}</p></article>'
        )
    populated_states = {cycle.magic_state for cycle in timeline.cycles}
    state_options = ''.join(f'<option value="{key}">{label}</option>' for key, label in STATE_LABELS.items() if key in populated_states)
    cycle_options = ''.join(
        f'<option value="{esc(cycle.id)}" data-magic-state="{cycle.magic_state}">{number:02d} · {esc(cycle.title)}</option>'
        for number, cycle in enumerate(timeline.cycles, 1)
    )
    return (
        '<a class="atlas-skip" href="#atlas-explore">Skip to the timeline</a><div class="atlas" data-timeline>'
        '<section class="atlas-hero"><div class="atlas-hero-copy">'
        '<p class="atlas-kicker">One world, across deep time</p>'
        '<h1>The Worldline<span>Civilizations rise.<br> The world remembers.</span></h1>'
        '<p class="atlas-lede">One world, inhabited again and again. Its people build cities, make ordinary lives, lose histories, and raise new civilizations among the traces of the old.</p>'
        '<a class="atlas-enter" href="#atlas-weave">Enter the timeline <span aria-hidden="true">↘</span></a>'
        f'{depth_invitation}'
        f'<div class="atlas-totals"><span><b>{len(stories)}</b> stories</span><span><b>{sum(len(cycle.eras) for cycle in timeline.cycles)}</b> historical eras</span>'
        f'<span><b>{len(timeline.cycles)}</b> proposed cycles</span></div>'
        f'</div><div class="atlas-orrery">{orbit_map(timeline.cycles)}'
        '<div class="orbit-readout"><b data-orbit-readout>Every light is a way in.</b>'
        '<span data-orbit-context>Enter a cycle. Meet the civilizations within it.</span></div>'
        '<div class="orbit-key" aria-label="Orbit colors"><span>Old magic</span><span>The Long Dark</span><span>New magic</span></div>'
        '</div></section>'
        '<section class="atlas-backbone" aria-label="Established worldline backbone">'
        '<div><span>I · Before the zero</span><strong>Old magic</strong><p>Many systems. Many forgotten beginnings.</p></div>'
        '<a href="#story-all-accounts-due" data-locate-story="all-accounts-due" class="backbone-hinge"><span>Extinction</span><b>All Accounts Due</b><i aria-hidden="true">↓</i></a>'
        '<div><span>II · Material zero</span><strong>The Long Dark</strong><p>Magic is absent. History keeps happening.</p></div>'
        '<a href="#story-the-sky-remembers-us-return" data-locate-story="the-sky-remembers-us-return" class="backbone-hinge"><span>Reawakening</span><b>The Sky Remembers Us</b><i aria-hidden="true">↓</i></a>'
        '<div><span>III · After the return</span><strong>New magic</strong><p>Reciprocal links. A different beginning.</p></div></section>'
        '<section class="atlas-reading-note"><span class="atlas-kicker">Reading the chronology</span>'
        '<p>A <b>Galactic Cycle</b> is an orbit of this world’s star system around the galaxy. Within the cycles, eras bring stories together through their technologies, institutions, magical conditions, and relationship to the past. Different societies can share a period.</p>'
        '<p>The era groupings and broad succession are a proposed reconstruction of one history. Exact Galactic coordinates remain open; spacing is schematic. Bands show possible placement, not a measured lifetime. Within and between overlapping eras, regional stories may overlap in time. Established sequences and local intervals retain precedence.</p></section>'
        f'{depth_view}{weave(timeline.cycles)}'
        '<section class="atlas-directory" aria-labelledby="directory-title"><div class="atlas-section-label">'
        '<h2 id="directory-title">Travel through the cycles</h2><a href="#atlas-threads">Follow the connections ↗</a></div>'
        f'<nav class="cycle-directory" aria-label="Chronological cycles">{"".join(directory)}</nav></section>'
        '<nav class="atlas-wayfinder" aria-label="Atlas wayfinder"><span data-atlas-location>The timeline</span>'
        '<div><a href="#atlas-weave">History map ↑</a><a href="#atlas-explore">Find a story</a><a href="#atlas-threads">Threads ↗</a></div></nav>'
        '<div class="atlas-explore" id="atlas-explore"><div class="atlas-controls" hidden>'
        '<label class="atlas-search"><span>Find a story or historical context</span><input type="search" data-atlas-search placeholder="A title, an institution, a memory…" autocomplete="off"></label>'
        f'<label class="atlas-filter"><span>History category</span><select data-atlas-state><option value="all">All histories</option>{state_options}</select></label>'
        f'<label class="atlas-filter atlas-cycle-filter"><span>Cycle</span><select data-atlas-cycle><option value="all">All {len(timeline.cycles)} cycles</option>{cycle_options}</select></label>'
        '<button type="button" data-atlas-reset>Reset</button><button type="button" data-toggle-details>Expand story details</button>'
        '</div><div class="atlas-results"><p role="status" aria-live="polite" data-atlas-count>'
        f'{len(stories)} stories in {sum(len(cycle.eras) for cycle in timeline.cycles)} eras across {len(timeline.cycles)} cycles</p>'
        '<div class="atlas-evidence-legend" aria-label="Surviving evidence"><span class="evidence evidence-boundary">Worldline boundary</span>'
        '<span class="evidence evidence-constrained">Established constraint</span><span class="evidence evidence-relative">Relative sequence</span>'
        '<span class="evidence evidence-contextual">Contextual evidence</span><span class="evidence evidence-undated">Date unresolved</span></div></div>'
        '<p class="evidence-reading-note">These marks describe what survives in the stories and established chronology. Every numbered cycle and era placement remains a proposal.</p>'
        '<p class="atlas-empty" data-atlas-empty hidden>No stories match this part of the timeline. Try another title or reset the filters.</p>'
        f'<div class="atlas-cycles">{"".join(sections)}</div></div>'
        '<section class="atlas-threads" id="atlas-threads"><header class="threads-heading"><p class="atlas-kicker">Across the distance</p>'
        '<h2>The past reaches<br><em>into another age.</em></h2>'
        '<p>Some connections follow the same people or events. Historical hypotheses explore how conditions might change across ages; thematic echoes connect questions that recur. Every endpoint leads back to its era and individual story. Notes may reveal story outcomes.</p></header>'
        '<div class="thread-controls" role="group" aria-label="Connection type" hidden><button type="button" data-thread-filter="all" aria-pressed="true">All threads</button>'
        '<button type="button" data-thread-filter="direct" aria-pressed="false">Direct connections</button>'
        '<button type="button" data-thread-filter="historical" aria-pressed="false">Historical hypotheses</button>'
        '<button type="button" data-thread-filter="echo" aria-pressed="false">Thematic echoes</button></div>'
        f'<p class="thread-count" data-thread-count role="status">{len(timeline.connections)} threads</p>'
        f'<div class="thread-grid">{"".join(thread_cards)}</div></section>'
        '<footer class="atlas-footer"><span aria-hidden="true">✳</span><p class="atlas-kicker">Beyond the last plotted light</p>'
        '<h2>There is always<br>another beginning.</h2><p>The empty distance belongs to stories still to come.</p>'
        '<a href="index.html">Return to the library ↗</a><a href="#directory-title">Back to the cycles ↑</a></footer></div>'
    )
