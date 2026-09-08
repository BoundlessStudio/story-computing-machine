"""A single worldline, with context and evidence opened on demand."""
from __future__ import annotations
import html

STATE_LABELS = {"old-magic": "Old magic", "long-dark": "The Long Dark", "new-magic": "New magic",
                "uncertain": "Unplaced in time", "off-axis": "Beyond the material clock"}
EVIDENCE = {"boundary": "Worldline boundary", "constrained": "Established constraint",
            "relative": "Relative sequence", "contextual": "Contextual evidence", "undated": "Date unresolved"}
LINK_LABELS = {"direct": "Direct connection", "historical": "Historical hypothesis", "echo": "Thematic echo"}
BASIS_LABELS = {"established": "Established chronology", "reading-sequence": "Supplied reading sequence",
                "proposed": "Proposed historical interpretation", "thematic": "A parallel, not a date"}
PHASE_COPY = {"old-magic": "Civilizations built upon civilizations.",
              "long-dark": "Magic is absent. The world keeps making history.",
              "new-magic": "New workings enter an already ancient world."}

def esc(value):
    return html.escape(str(value), quote=True)

def render(catalog, timeline):
    stories = {story.slug: story for story in catalog.stories}
    locations = {slug: (number, cycle, era) for number, cycle in enumerate(timeline.cycles, 1)
                 for era in cycle.eras for slug in era.stories}
    related = {slug: [] for slug in stories}
    for link in timeline.connections:
        related[link.source].append(link)
        related[link.target].append(link)

    phases, rows = [], []
    for number, cycle in enumerate(timeline.cycles, 1):
        if cycle.magic_state not in phases:
            phases.append(cycle.magic_state)
            hinge = ''
            if cycle.magic_state == 'long-dark' and 'all-accounts-due' in stories:
                hinge = '<a class="worldline-hinge" href="#story-all-accounts-due"><span>Magic ends</span><strong>All Accounts Due</strong><i aria-hidden="true">↗</i></a>'
            if cycle.magic_state == 'new-magic' and 'the-sky-remembers-us-return' in stories:
                hinge = '<a class="worldline-hinge" href="#story-the-sky-remembers-us-return"><span>Magic returns</span><strong>The Sky Remembers Us</strong><i aria-hidden="true">↗</i></a>'
            rows.append(
                f'<div class="history-phase state-{cycle.magic_state}" id="phase-{cycle.magic_state}" data-phase="{cycle.magic_state}">'
                f'{hinge}<div class="phase-heading"><span class="phase-dot" aria-hidden="true"></span>'
                f'<h2>{STATE_LABELS[cycle.magic_state]}</h2><p>{PHASE_COPY.get(cycle.magic_state, "A different relationship to time.")}</p></div></div>'
            )
        era_panels = []
        for era_number, era in enumerate(cycle.eras, 1):
            events = []
            for slug in era.stories:
                story = stories[slug]
                placement = timeline.story_placements[slug]
                evidence = timeline.story_evidence[slug]
                moments = timeline.story_moments.get(slug, ())
                span = timeline.story_spans.get(slug)
                history = ''
                if moments:
                    history = (f'<div class="story-history" id="depth-{esc(slug)}"><h5>Within this story</h5><ol>'
                               + ''.join(f'<li>{esc(moment)}</li>' for moment in moments) + '</ol></div>')
                if span:
                    history += f'<p class="story-span"><b>{esc(span.start)} → {esc(span.end)}</b>{esc(span.note)}</p>'
                links = ''.join(
                    f'<li class="{link.kind}"><span>{LINK_LABELS[link.kind]}</span>'
                    f'<a href="#thread-{esc(link.id)}">{esc(link.label)} <i aria-hidden="true">↗</i></a></li>'
                    for link in related[slug])
                connections = f'<ul class="event-connections">{links}</ul>' if links else ''
                search = " ".join((story.title, cycle.title, era.title, era.description, *era.context, placement.note, *moments))
                events.append(
                    f'<article class="worldline-event evidence-{evidence}" id="story-{esc(slug)}" '
                    f'data-story-slug="{esc(slug)}" data-story-evidence="{evidence}" data-search="{esc(search)}">'
                    '<div class="event-card">'
                    f'<a class="atlas-cover" href="stories/{esc(slug)}.html" aria-label="Read {esc(story.title)}">'
                    f'<img src="{esc(story.cover)}" alt="" width="864" height="1536" loading="lazy"></a>'
                    f'<div class="event-copy"><h4><a href="stories/{esc(slug)}.html">{esc(story.title)} <span aria-hidden="true">↗</span></a></h4>'
                    f'<span class="evidence">{EVIDENCE[evidence]}</span>'
                    '<details class="event-details" data-event-details><summary>Place in history</summary><div class="event-evidence">'
                    f'<p class="placement-status">Era placement proposed</p><p>{esc(placement.note)}</p>{history}{connections}'
                    '</div></details></div></div></article>')
            peers = [peer for peer in cycle.eras if peer.id != era.id
                     and max(peer.window.start, era.window.start) < min(peer.window.end, era.window.end)]
            peers_html = ('<div class="era-peers"><span>May share a horizon with</span>'
                          + ''.join(f'<a href="#era-{esc(peer.id)}">{esc(peer.title)} ↗</a>' for peer in peers)
                          + '</div>') if peers else ''
            local_links = [link for link in timeline.connections if link.ordering == 'before'
                           and link.source in era.stories and link.target in era.stories]
            local_order = ''.join(
                f'<li><span>{BASIS_LABELS[link.basis]}</span><a href="#story-{esc(link.source)}">{esc(stories[link.source].title)}</a>'
                f'<b aria-label="before">→</b><a href="#story-{esc(link.target)}">{esc(stories[link.target].title)}</a></li>'
                for link in local_links)
            local_order = f'<ul class="era-local-order">{local_order}</ul>' if local_order else ''
            previews = ''.join(
                f'<img src="{esc(stories[slug].cover)}" alt="" width="864" height="1536" loading="lazy">'
                for slug in era.stories[:3])
            context = ''.join(f'<li>{esc(item)}</li>' for item in era.context)
            era_panels.append(
                f'<details class="history-era" id="era-{esc(era.id)}" data-era-section="{esc(era.id)}">'
                '<summary class="era-stop">'
                f'<span class="era-stop-copy"><span class="era-stop-title">{esc(era.title)}</span>'
                f'<small><span data-era-count>{len(era.stories)}</span> <span data-era-noun>{"story" if len(era.stories) == 1 else "stories"}</span></small>'
                '<span class="era-matches" data-era-matches hidden></span></span>'
                f'<span class="era-covers" aria-hidden="true">{previews}</span><span class="era-open" aria-hidden="true">↗</span></summary>'
                f'<dialog class="era-dialog" aria-labelledby="era-title-{esc(era.id)}" data-era-dialog>'
                '<div class="dialog-bar"><button type="button" data-dialog-close>← Back to the timeline</button>'
                f'<span>Cycle {number:02d} · {esc(STATE_LABELS[cycle.magic_state])}</span></div>'
                '<div class="dialog-content"><header class="era-heading">'
                f'<p class="atlas-kicker">{esc(cycle.title)} · Era {era_number:02d}</p>'
                f'<h3 id="era-title-{esc(era.id)}">{esc(era.title)}</h3><p>{esc(era.description)}</p></header>'
                '<details class="era-context"><summary>About this era &amp; its placement</summary><div>'
                f'<h4>Life in this era</h4><ul>{context}</ul><p>{esc(era.sequence_note)}</p>{peers_html}'
                f'<h4>The wider cycle</h4><p>{esc(cycle.description)}</p><p>{esc(cycle.sequence_note)}</p></div></details>'
                f'{local_order}<div class="era-story-heading"><h4>Lives in this era</h4>'
                '<span>Proposed grouping · Dates may overlap</span></div>'
                f'<div class="era-lives">{"".join(events)}</div></div>'
                '<nav class="era-pagination" aria-label="Explore adjacent eras"><button type="button" data-era-prev>← Previous era</button>'
                '<button type="button" data-era-next>Next era →</button></nav></dialog></details>')
        rows.append(
            f'<section class="atlas-cycle state-{cycle.magic_state}" id="cycle-{esc(cycle.id)}" '
            f'data-cycle-section="{esc(cycle.id)}" data-magic-state="{cycle.magic_state}">'
            '<header class="cycle-heading">'
            f'<p class="atlas-kicker">Cycle {number:02d}</p><h3>{esc(cycle.title)}</h3>'
            f'<p class="cycle-context">{esc(cycle.eyebrow)}</p></header>'
            f'<span class="cycle-node" aria-hidden="true">{number:02d}</span>'
            f'<div class="cycle-eras">{"".join(era_panels)}</div></section>')

    thread_cards = []
    for link in timeline.connections:
        endpoints = ''.join(
            f'<a href="#story-{esc(slug)}"><small>Cycle {locations[slug][0]:02d} · {esc(locations[slug][2].title)}</small>'
            f'<span>{esc(stories[slug].title)}</span></a>' for slug in (link.source, link.target))
        thread_cards.append(
            f'<article class="thread-card {link.kind}" id="thread-{esc(link.id)}" data-thread-kind="{link.kind}">'
            f'<p class="atlas-kicker">{LINK_LABELS[link.kind]}</p><h3>{esc(link.label)}</h3>'
            f'<p class="thread-basis">{BASIS_LABELS[link.basis]}</p><div class="thread-endpoints">{endpoints}</div>'
            f'<p>{esc(link.note)}</p></article>')
    phase_links = ''.join(f'<a class="state-{state}" href="#phase-{state}" data-phase-link="{state}"><i aria-hidden="true"></i>{STATE_LABELS[state]}</a>' for state in phases)
    total_eras = sum(len(cycle.eras) for cycle in timeline.cycles)
    return (
        '<a class="atlas-skip" href="#atlas-explore">Skip to the timeline</a><div class="atlas" data-timeline>'
        '<header class="chronicle-intro"><div><p class="atlas-kicker">One world · Deep time</p>'
        '<h1>The Worldline</h1><p>Civilizations rise. The world remembers.</p></div>'
        f'<p class="chronicle-total"><b>{len(stories)}</b> stories woven through<br> <b>{len(timeline.cycles)}</b> cycles of one history.</p></header>'
        '<div class="chronicle-toolbar"><nav class="phase-nav" aria-label="The great ages">'
        f'{phase_links}</nav><label class="atlas-search" hidden><span class="sr-only">Search the whole chronology</span>'
        '<input type="search" data-atlas-search placeholder="Find a story, place, idea…" autocomplete="off"></label></div>'
        '<div class="chronicle-guide"><p>Follow time downward. Open an era.</p>'
        '<details class="reading-guide"><summary>How to read this history</summary><div>'
        '<p>A <b>Galactic Cycle</b> is an orbit of this world’s star system around the galaxy. '
        'These cycles and eras are a proposed reconstruction; spacing is schematic, not a measured duration.</p>'
        '<p>Magic’s extinction and return anchor the three great ages. Divine rule, technology and public powers '
        'have their own regional histories; they need not flourish, fade or return together.</p>'
        '<p>Technologies, institutions and inherited histories bring stories together. Within a cycle, '
        'regional stories may overlap in time; the order of era entries does not establish succession. '
        'Established sequences and local intervals take precedence.</p>'
        '<p>Open a story’s “Place in history” for its evidence and connections. Direct connections, historical hypotheses '
        'and thematic echoes are distinguished. A remembered event can reach beyond its story’s proposed era.</p></div></details></div>'
        '<div class="search-feedback" hidden data-search-feedback><p role="status" aria-live="polite" data-atlas-count></p>'
        '<button type="button" data-atlas-reset>Clear search ×</button></div>'
        f'<section class="worldline" id="atlas-explore" aria-label="{len(timeline.cycles)} cycles, {total_eras} eras"><span id="atlas-weave"></span><span id="atlas-depths"></span>{"".join(rows)}'
        '<p class="atlas-empty" data-atlas-empty hidden>No stories found. Try another title, place or idea.</p>'
        '<div class="worldline-end"><i aria-hidden="true"></i><p>History is still being written.</p></div></section>'
        '<footer class="chronicle-footer"><a href="index.html">← The story library</a>'
        '<details class="connections-library" id="atlas-threads"><summary>Explore the connections ↗</summary>'
        '<dialog class="connections-dialog" data-connections-dialog aria-label="Connections across history">'
        '<div class="dialog-bar"><button type="button" data-dialog-close>← Back to the timeline</button>'
        '<button type="button" data-all-connections>All connections</button></div><div class="dialog-content">'
        '<div class="thread-controls" role="group" aria-label="Connection type" hidden>'
        '<button type="button" data-thread-filter="all" aria-pressed="true">All</button>'
        '<button type="button" data-thread-filter="direct" aria-pressed="false">Direct</button>'
        '<button type="button" data-thread-filter="historical" aria-pressed="false">Historical</button>'
        '<button type="button" data-thread-filter="echo" aria-pressed="false">Echoes</button></div>'
        f'<div class="thread-grid">{"".join(thread_cards)}</div></div></dialog></details>'
        '<a href="#atlas-explore">Back to the beginning ↑</a></footer></div>')
