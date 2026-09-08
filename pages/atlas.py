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


def chapter_slugs(chapter):
    return (*chapter.stories, *(slug for group in chapter.constellations for slug in group.stories))


def orbit_map(cycles):
    """A navigable reading map; ring radii deliberately encode no elapsed time."""
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


def render(catalog, timeline):
    stories = {story.slug: story for story in catalog.stories}
    chapters = {chapter.id: chapter for chapter in timeline.chapters}
    story_chapters = {slug: chapter for chapter in timeline.chapters for slug in chapter_slugs(chapter)}
    related = {slug: [] for slug in stories}
    for connection in timeline.connections:
        related[connection.source].append(connection)
        related[connection.target].append(connection)

    directory = []
    sections = []
    for number, cycle in enumerate(timeline.cycles, 1):
        slugs = [slug for chapter_id in cycle.chapters for slug in chapter_slugs(chapters[chapter_id])]
        directory.append(
            f'<a href="#cycle-{esc(cycle.id)}" class="cycle-entry state-{cycle.magic_state}" data-cycle-link="{esc(cycle.id)}">'
            f'<span>{number:02d}</span><strong>{esc(cycle.title)}</strong><small>{len(slugs)} stories</small></a>'
        )
        eras = []
        for chapter_id in cycle.chapters:
            chapter = chapters[chapter_id]
            entries = []
            for slug in chapter_slugs(chapter):
                story = stories[slug]
                moments = timeline.story_moments.get(slug, ())
                span = timeline.story_spans.get(slug)
                moment_html = f'<ol class="story-moments">{"".join(f"<li>{esc(moment)}</li>" for moment in moments)}</ol>' if moments else ''
                span_html = f'<p class="story-span"><b>{esc(span.start)} → {esc(span.end)}</b>{esc(span.note)}</p>' if span else ''
                routes = ''.join(
                    f'<a href="#thread-{esc(link.id)}" class="story-thread {link.kind}">{"↗" if link.kind == "direct" else "≈"} {esc(link.label)}</a>'
                    for link in related[slug]
                )
                entries.append(
                    f'<article class="atlas-story" id="story-{esc(slug)}" data-story-slug="{esc(slug)}" '
                    f'data-search="{esc(" ".join((story.title, chapter.title, cycle.title, *moments)).lower())}" '
                    f'data-placement-confidence="{timeline.story_confidence[slug]}">'
                    f'<a class="atlas-cover" href="stories/{esc(slug)}.html" aria-label="Read {esc(story.title)}">'
                    f'<img src="{esc(story.cover)}" alt="" width="864" height="1536" loading="lazy" decoding="async"></a>'
                    '<div class="atlas-story-copy">'
                    f'<span class="evidence evidence-{timeline.story_confidence[slug]}">{EVIDENCE[timeline.story_confidence[slug]]}</span>'
                    f'<h4><a href="stories/{esc(slug)}.html">{esc(story.title)}</a></h4>'
                    f'{moment_html}{span_html}'
                    f'<div class="story-threads">{routes}</div></div></article>'
                )
            group_notes = ''.join(
                f'<p><b>{esc(group.title)}.</b> {esc(group.sequence_note)}</p>' for group in chapter.constellations
            )
            eras.append(
                f'<details class="atlas-era" id="{esc(chapter.id)}" data-era-stop open>'
                '<summary><span class="era-cross" aria-hidden="true">+</span><span>'
                f'<small>{esc(chapter.eyebrow)}</small><h3>{esc(chapter.title)}</h3></span>'
                f'<span class="era-count">{len(entries):02d}<small>stories</small></span></summary>'
                f'<div class="era-body"><p class="era-description">{esc(chapter.description)}</p>'
                f'<p class="era-placement">{esc(chapter.sequence_note)}</p>{group_notes}'
                f'<div class="atlas-story-grid">{"".join(entries)}</div></div></details>'
            )
        sections.append(
            f'<section class="atlas-cycle state-{cycle.magic_state}" id="cycle-{esc(cycle.id)}" '
            f'data-cycle-section="{esc(cycle.id)}" data-magic-state="{cycle.magic_state}">'
            '<header class="cycle-heading"><div class="cycle-seal" aria-hidden="true">'
            f'<span>{number:02d}</span></div><div class="cycle-heading-copy">'
            f'<p class="atlas-kicker">{esc(cycle.eyebrow)} · {len(slugs)} stories</p>'
            f'<h2>{esc(cycle.title)}</h2><p>{esc(cycle.description)}</p>'
            f'<p class="cycle-placement">{esc(cycle.sequence_note)}</p></div>'
            f'<span class="cycle-state">{STATE_LABELS[cycle.magic_state]}</span></header>'
            f'<div class="cycle-eras">{"".join(eras)}</div></section>'
        )

    thread_cards = []
    for link in timeline.connections:
        label = 'Direct connection' if link.kind == 'direct' else 'Thematic echo'
        endpoints = ''.join(
            f'<a href="#story-{esc(slug)}" data-locate-story="{esc(slug)}">'
            f'<small>{esc(story_chapters[slug].title)}</small><span>{esc(stories[slug].title)}</span></a>'
            for slug in (link.source, link.target)
        )
        thread_cards.append(
            f'<article class="thread-card {link.kind}" id="thread-{esc(link.id)}" data-thread-kind="{link.kind}">'
            f'<span class="atlas-kicker">{label}</span><h3>{esc(link.label)}</h3>'
            f'<div class="thread-endpoints">{endpoints}</div><p>{esc(link.note)}</p></article>'
        )
    populated_states = {cycle.magic_state for cycle in timeline.cycles}
    state_options = ''.join(f'<option value="{key}">{label}</option>' for key, label in STATE_LABELS.items() if key in populated_states)
    return (
        '<a class="atlas-skip" href="#atlas-explore">Skip to stories</a><div class="atlas" data-timeline>'
        '<section class="atlas-hero"><div class="atlas-hero-copy">'
        '<p class="atlas-kicker">The chronology of a shared universe</p>'
        '<h1>The Worldline<span>An atlas of<br>countless beginnings.</span></h1>'
        '<p class="atlas-lede">Kingdoms become ruins. Machines become myths. Somewhere, in the deep history of the same world, someone is just getting home.</p>'
        '<a class="atlas-enter" href="#atlas-explore">Find your place in time <span aria-hidden="true">↘</span></a>'
        f'<div class="atlas-totals"><span><b>{len(stories)}</b> stories</span><span><b>{len(timeline.cycles)}</b> reading cycles</span>'
        f'<span><b>{len(timeline.connections)}</b> connections &amp; echoes</span></div>'
        f'</div><div class="atlas-orrery">{orbit_map(timeline.cycles)}'
        '<div class="orbit-readout"><b data-orbit-readout>Every light is a way in.</b>'
        '<span data-orbit-context>Choose a light or use the cycle index below.</span></div>'
        '<div class="orbit-key" aria-label="Orbit colors"><span>Old magic</span><span>The Long Dark</span><span>New magic</span><span>Unplaced</span></div>'
        '</div></section>'
        '<section class="atlas-backbone" aria-label="Established worldline backbone">'
        '<div><span>I · Before the zero</span><strong>Old magic</strong><p>Many systems. Many forgotten beginnings.</p></div>'
        '<a href="#story-all-accounts-due" data-locate-story="all-accounts-due" class="backbone-hinge"><span>Extinction</span><b>All Accounts Due</b><i aria-hidden="true">↓</i></a>'
        '<div><span>II · Material zero</span><strong>The Long Dark</strong><p>Magic is absent. History keeps happening.</p></div>'
        '<a href="#story-the-sky-remembers-us-return" data-locate-story="the-sky-remembers-us-return" class="backbone-hinge"><span>Reawakening</span><b>The Sky Remembers Us</b><i aria-hidden="true">↓</i></a>'
        '<div><span>III · After the return</span><strong>New magic</strong><p>Reciprocal links. A different beginning.</p></div></section>'
        '<section class="atlas-reading-note"><span class="atlas-kicker">How to read the map</span>'
        '<p>The two turning points fix the backbone. The reading cycles propose room for many histories around it; their numbers are navigation, not dates. A <b>Galactic Cycle</b> is one orbit of the star system around the galaxy. Its length and these stories’ coordinates remain unresolved.</p>'
        '<p>Solid threads follow shared people or events, or an intended reading sequence; each note explains the basis. Dotted echoes invite a comparison; they do not establish shared ancestry. Open placements remain open.</p></section>'
        '<section class="atlas-directory" aria-labelledby="directory-title"><div class="atlas-section-label">'
        '<h2 id="directory-title">Choose a cycle</h2><a href="#atlas-threads">Follow the connections ↗</a></div>'
        f'<nav class="cycle-directory" aria-label="Reading cycles">{"".join(directory)}</nav></section>'
        '<nav class="atlas-wayfinder" aria-label="Atlas wayfinder"><span data-atlas-location>The reading map</span>'
        '<div><a href="#directory-title">Cycles ↑</a><a href="#atlas-explore">Find a story</a><a href="#atlas-threads">Threads ↗</a></div></nav>'
        '<div class="atlas-explore" id="atlas-explore"><div class="atlas-controls" hidden>'
        '<label class="atlas-search"><span>Find a story or era</span><input type="search" data-atlas-search placeholder="A title, a world, a memory…" autocomplete="off"></label>'
        f'<label class="atlas-filter"><span>World history</span><select data-atlas-state><option value="all">All histories</option>{state_options}</select></label>'
        '<button type="button" data-atlas-reset>Reset</button><button type="button" data-collapse-eras>Fold all eras</button>'
        '</div><div class="atlas-results"><p role="status" aria-live="polite" data-atlas-count>'
        f'{len(stories)} stories across {len(timeline.cycles)} reading cycles</p>'
        '<div class="atlas-evidence-legend" aria-label="Placement evidence"><span class="evidence evidence-fixed">Fixed</span>'
        '<span class="evidence evidence-inferred">Relative</span><span class="evidence evidence-speculative">Proposed</span>'
        '<span class="evidence evidence-unresolved">Unresolved</span></div></div>'
        '<p class="atlas-empty" data-atlas-empty hidden>No stories match this part of the map. Try another title or reset the filters.</p>'
        f'<div class="atlas-cycles">{"".join(sections)}</div></div>'
        '<section class="atlas-threads" id="atlas-threads"><header class="threads-heading"><p class="atlas-kicker">Across the distance</p>'
        '<h2>Some threads survive.<br><em>Others only rhyme.</em></h2>'
        '<p>Follow a life across stories, watch an event become history, or find an unexpected echo in another age. Connection notes discuss story events and may reveal outcomes.</p></header>'
        '<div class="thread-controls" role="group" aria-label="Connection type" hidden><button type="button" data-thread-filter="all" aria-pressed="true">All threads</button>'
        '<button type="button" data-thread-filter="direct" aria-pressed="false">Direct connections</button>'
        '<button type="button" data-thread-filter="echo" aria-pressed="false">Thematic echoes</button></div>'
        f'<p class="thread-count" data-thread-count role="status">{len(timeline.connections)} threads</p>'
        f'<div class="thread-grid">{"".join(thread_cards)}</div></section>'
        '<footer class="atlas-footer"><span aria-hidden="true">✳</span><p class="atlas-kicker">Beyond the last plotted light</p>'
        '<h2>There is always<br>another beginning.</h2><p>The empty distance belongs to stories still to come.</p>'
        '<a href="index.html">Return to the library ↗</a><a href="#directory-title">Back to the cycles ↑</a></footer></div>'
    )
