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
    "fixed": "Fixed anchor",
    "inferred": "Relative link",
    "speculative": "Proposed placement",
    "unresolved": "Date unresolved",
}


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


def period(position):
    return "Early" if position < 34 else "Middle" if position < 67 else "Late"


def render(catalog, timeline):
    stories = {story.slug: story for story in catalog.stories}
    locations = {slug: (number, cycle) for number, cycle in enumerate(timeline.cycles, 1) for slug in cycle.stories}
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
        previous_position = 0
        for local_index, slug in enumerate(cycle.stories):
            story = stories[slug]
            era = story_eras[slug]
            placement = timeline.story_placements[slug]
            confidence = timeline.story_confidence[slug]
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
                    f'<li class="event-connection {link.kind}"><span>{"Direct connection" if link.kind == "direct" else "Thematic echo"} · {crossing}</span>'
                    f'<a href="#story-{esc(other)}" data-locate-story="{esc(other)}">{esc(stories[other].title)} <i aria-hidden="true">↗</i></a>'
                    f'<small>{esc(link.label)}</small><a class="connection-evidence" href="#thread-{esc(link.id)}">Connection notes</a></li>'
                )
            connection_html = f'<ul class="event-connections">{"".join(connections)}</ul>' if connections else ''
            details = (
                f'<details class="event-details" data-event-details><summary>Local time &amp; connections <span aria-hidden="true">+</span></summary>'
                f'<div>{moment_html}{span_html}{connection_html}</div></details>'
                if moments or span or connections else ''
            )
            gap = 20 if slug == era.stories[0] else min(55, max(14, (placement.position - previous_position) * 4))
            events[slug] = (
                f'<article class="worldline-event event-{"left" if local_index % 2 == 0 else "right"}" id="story-{esc(slug)}" '
                f'data-story-slug="{esc(slug)}" data-position="{placement.position:g}" '
                f'data-search="{esc(" ".join((story.title, cycle.title, era.title, era.description, *era.context, placement.note, *moments)).lower())}" '
                f'data-placement-confidence="{confidence}" style="--event-gap:{gap:.1f}px">'
                f'<span class="event-coordinate">{period(placement.position)} in cycle {number:02d}</span>'
                f'<span class="event-node evidence-{confidence}" aria-hidden="true"></span>'
                '<div class="event-card">'
                f'<a class="atlas-cover" href="stories/{esc(slug)}.html" aria-label="Read {esc(story.title)}">'
                f'<img src="{esc(story.cover)}" alt="" width="864" height="1536" loading="lazy" decoding="async"></a>'
                '<div class="event-copy">'
                f'<span class="evidence evidence-{confidence}">{EVIDENCE[confidence]}</span>'
                f'<h4><a href="stories/{esc(slug)}.html">{esc(story.title)}</a></h4>'
                f'<p class="event-placement">{esc(placement.note)}</p>{details}</div></div></article>'
            )
            previous_position = placement.position
        era_panels = []
        for era_number, era in enumerate(cycle.eras, 1):
            context = ''.join(f'<li>{esc(observation)}</li>' for observation in era.context)
            era_panels.append(
                f'<section class="history-era" id="era-{esc(era.id)}" data-era-section="{esc(era.id)}" '
                f'aria-labelledby="era-title-{esc(era.id)}">'
                '<header class="era-heading"><div class="era-introduction">'
                f'<p class="atlas-kicker">Era {number:02d}.{era_number:02d} · {len(era.stories)} {"story" if len(era.stories) == 1 else "stories"}</p>'
                f'<h3 id="era-title-{esc(era.id)}">{esc(era.title)}</h3><p>{esc(era.description)}</p></div>'
                f'<div class="era-context"><span>Life in this era</span><ul>{context}</ul></div></header>'
                f'<p class="era-sequence-note"><span>Place in history</span>{esc(era.sequence_note)}</p>'
                f'<div class="cycle-events">{"".join(events[slug] for slug in era.stories)}</div></section>'
            )
        era_ranges = ''.join(
            f'<a class="cycle-era-range" href="#era-{esc(era.id)}" '
            f'style="--start:{timeline.story_placements[era.stories[0]].position:g}%;--range:{max(1, timeline.story_placements[era.stories[-1]].position - timeline.story_placements[era.stories[0]].position):g}%" '
            f'aria-label="Enter {esc(era.title)}" title="{esc(era.title)}"></a>'
            for era in cycle.eras
        )
        miniature = era_ranges + ''.join(
            f'<a href="#story-{esc(slug)}" data-locate-story="{esc(slug)}" '
            f'style="--position:{timeline.story_placements[slug].position:g}%" aria-label="Locate {esc(stories[slug].title)}" '
            f'title="{esc(stories[slug].title)}"><span></span></a>' for slug in cycle.stories
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
            f'<nav class="cycle-strip" aria-label="Story positions in cycle {number:02d}">{miniature}</nav>'
            '<div class="cycle-strip-labels" aria-hidden="true"><span>Earlier</span><span>Later →</span></div>'
            f'<nav class="cycle-era-index" aria-label="Eras in cycle {number:02d}">{era_index}</nav></div>'
            f'<span class="cycle-state">{STATE_LABELS[cycle.magic_state]}</span></header>'
            f'<div class="cycle-eras">{"".join(era_panels)}</div>'
            '<div class="cycle-passage" aria-hidden="true"><i></i><span>The world continues</span><i></i></div></section>'
        )

    thread_cards = []
    for link in timeline.connections:
        label = 'Direct connection' if link.kind == 'direct' else 'Thematic echo'
        endpoints = ''.join(
            f'<a href="#story-{esc(slug)}" data-locate-story="{esc(slug)}">'
            f'<small>Cycle {locations[slug][0]:02d} · {esc(story_eras[slug].title)}</small><span>{esc(stories[slug].title)}</span></a>'
            for slug in (link.source, link.target)
        )
        thread_cards.append(
            f'<article class="thread-card {link.kind}" id="thread-{esc(link.id)}" data-thread-kind="{link.kind}">'
            f'<span class="atlas-kicker">{label}</span><h3>{esc(link.label)}</h3>'
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
        '<h1>The Worldline<span>Civilizations rise.<br>The world remembers.</span></h1>'
        '<p class="atlas-lede">One world, inhabited again and again. Its people build cities, make ordinary lives, lose histories, and raise new civilizations among the traces of the old.</p>'
        '<a class="atlas-enter" href="#atlas-explore">Enter the timeline <span aria-hidden="true">↘</span></a>'
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
        '<p>The era groupings and broad succession are a proposed reconstruction of one history. Exact Galactic coordinates remain open; spacing is schematic. Within an era, regional stories may overlap in time. Established sequences and local intervals retain precedence.</p></section>'
        '<section class="atlas-directory" aria-labelledby="directory-title"><div class="atlas-section-label">'
        '<h2 id="directory-title">Travel through the cycles</h2><a href="#atlas-threads">Follow the connections ↗</a></div>'
        f'<nav class="cycle-directory" aria-label="Chronological cycles">{"".join(directory)}</nav></section>'
        '<nav class="atlas-wayfinder" aria-label="Atlas wayfinder"><span data-atlas-location>The timeline</span>'
        '<div><a href="#directory-title">Cycles ↑</a><a href="#atlas-explore">Find a story</a><a href="#atlas-threads">Threads ↗</a></div></nav>'
        '<div class="atlas-explore" id="atlas-explore"><div class="atlas-controls" hidden>'
        '<label class="atlas-search"><span>Find a story or historical context</span><input type="search" data-atlas-search placeholder="A title, an institution, a memory…" autocomplete="off"></label>'
        f'<label class="atlas-filter"><span>History category</span><select data-atlas-state><option value="all">All histories</option>{state_options}</select></label>'
        f'<label class="atlas-filter atlas-cycle-filter"><span>Cycle</span><select data-atlas-cycle><option value="all">All {len(timeline.cycles)} cycles</option>{cycle_options}</select></label>'
        '<button type="button" data-atlas-reset>Reset</button><button type="button" data-toggle-details>Expand story details</button>'
        '</div><div class="atlas-results"><p role="status" aria-live="polite" data-atlas-count>'
        f'{len(stories)} stories in {sum(len(cycle.eras) for cycle in timeline.cycles)} eras across {len(timeline.cycles)} cycles</p>'
        '<div class="atlas-evidence-legend" aria-label="Placement evidence"><span class="evidence evidence-fixed">Fixed anchor</span>'
        '<span class="evidence evidence-inferred">Relative link</span><span class="evidence evidence-speculative">Proposed</span>'
        '<span class="evidence evidence-unresolved">Unresolved</span></div></div>'
        '<p class="atlas-empty" data-atlas-empty hidden>No stories match this part of the timeline. Try another title or reset the filters.</p>'
        f'<div class="atlas-cycles">{"".join(sections)}</div></div>'
        '<section class="atlas-threads" id="atlas-threads"><header class="threads-heading"><p class="atlas-kicker">Across the distance</p>'
        '<h2>The past reaches<br><em>into another age.</em></h2>'
        '<p>Some connections follow the same people or events. Others echo across this world’s civilizations. Every endpoint leads back to its era and individual story. Notes may reveal story outcomes.</p></header>'
        '<div class="thread-controls" role="group" aria-label="Connection type" hidden><button type="button" data-thread-filter="all" aria-pressed="true">All threads</button>'
        '<button type="button" data-thread-filter="direct" aria-pressed="false">Direct connections</button>'
        '<button type="button" data-thread-filter="echo" aria-pressed="false">Thematic echoes</button></div>'
        f'<p class="thread-count" data-thread-count role="status">{len(timeline.connections)} threads</p>'
        f'<div class="thread-grid">{"".join(thread_cards)}</div></section>'
        '<footer class="atlas-footer"><span aria-hidden="true">✳</span><p class="atlas-kicker">Beyond the last plotted light</p>'
        '<h2>There is always<br>another beginning.</h2><p>The empty distance belongs to stories still to come.</p>'
        '<a href="index.html">Return to the library ↗</a><a href="#directory-title">Back to the cycles ↑</a></footer></div>'
    )
