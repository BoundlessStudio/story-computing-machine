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
STAGE_LABELS = {"established": "Story anchor", "proposed": "Reconstruction",
                "recurrence": "A later recurrence", "absence": "An absence matters"}
SHORT_STATES = {**STATE_LABELS, "long-dark": "Zero"}

def esc(value):
    return html.escape(str(value), quote=True)


def render_braid(timeline, stories):
    """Recurring histories, not a quantified chart or a genealogy of powers."""
    cycle_headers = ''.join(
        f'<a class="braid-cycle state-{cycle.magic_state}" href="#cycle-{esc(cycle.id)}">'
        f'<span>{number:02d}</span><strong>{esc(cycle.title)}</strong>'
        '<span class="braid-phases">' + ' <i aria-hidden="true">→</i> '.join(
            f'<b class="state-{state}">{SHORT_STATES[state]}</b>'
            for state in cycle.magic_states) + '</span>'
        '<i aria-hidden="true">↓</i></a>' for number, cycle in enumerate(timeline.cycles, 1))
    strands = []
    for number, thread in enumerate(timeline.history_threads, 1):
        stages = {stage.cycle_id: stage for stage in thread.stages}
        cells = []
        for cycle in timeline.cycles:
            stage = stages.get(cycle.id)
            if not stage:
                cells.append('<div class="braid-gap"><span>No account selected</span></div>')
                continue
            anchors = ''.join(f'<a href="#story-{esc(slug)}">{esc(stories[slug].title)} ↗</a>' for slug in stage.anchors)
            cells.append(
                f'<details class="braid-stage kind-{stage.kind}" data-history-stage data-stage-cycle="{esc(cycle.id)}">'
                f'<summary><span class="braid-stitch" aria-hidden="true"></span><strong>{esc(stage.title)}</strong>'
                f'<small>{STAGE_LABELS[stage.kind]} <i aria-hidden="true">+</i></small></summary>'
                f'<div class="braid-account"><p>{esc(stage.note)}</p><div>{anchors}</div></div></details>')
        strands.append(
            f'<section class="braid-strand strand-{number}" id="current-{esc(thread.id)}" data-history-thread '
            f'aria-labelledby="current-title-{esc(thread.id)}">'
            f'<header><h3 id="current-title-{esc(thread.id)}">{esc(thread.title)}</h3>'
            f'<details class="strand-context"><summary>About this thread</summary><p>{esc(thread.description)}</p></details></header>'
            f'{"".join(cells)}</section>')
    return (
        '<section class="history-braid" id="atlas-currents" aria-labelledby="braid-title">'
        '<header class="braid-heading"><div><p class="atlas-kicker">The long view</p>'
        '<h2 id="braid-title">Four histories. One world.</h2></div>'
        '<p>Read across to follow a current. Read down to see what shares a world. '
        'Open a stitch for its stories.</p></header>'
        '<p class="braid-caption">Gods, machines and extraordinary bodies have different histories. '
        'A recurring form can be reinvented; the thread alone does not establish descent.</p>'
        '<p class="braid-mobile-hint">Swipe across the cycles →</p>'
        '<div class="braid-scroll" tabindex="0" role="region" aria-label="Historical currents across the cycles; scroll horizontally on small screens">'
        f'<div class="braid-cloth" style="--cycle-count:{len(timeline.cycles)}">'
        f'<nav class="braid-heading-row" aria-label="Jump to a cycle"><span class="braid-direction">Proposed cycles <b aria-hidden="true">→</b></span>{cycle_headers}</nav>'
        f'{"".join(strands)}</div></div>'
        '<div class="braid-boundaries"><a href="#story-all-accounts-due"><i class="cut" aria-hidden="true"></i>'
        '<span><b>The extinction</b>Old magic ends. Human history continues.</span></a>'
        '<a href="#story-the-sky-remembers-us-return"><i class="join" aria-hidden="true"></i>'
        '<span><b>The return</b>New magic enters an inhabited world.</span></a></div></section>')

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
        era_panels = []
        for era_number, era in enumerate(cycle.eras, 1):
            if era.magic_state not in phases:
                phases.append(era.magic_state)
                hinge = ''
                if era.magic_state == 'long-dark' and 'all-accounts-due' in stories:
                    hinge = '<a class="worldline-hinge" href="#story-all-accounts-due"><span>Magic ends</span><strong>All Accounts Due</strong><i aria-hidden="true">↗</i></a>'
                if era.magic_state == 'new-magic' and 'the-sky-remembers-us-return' in stories:
                    hinge = '<a class="worldline-hinge" href="#story-the-sky-remembers-us-return"><span>Magic returns</span><strong>The Sky Remembers Us</strong><i aria-hidden="true">↗</i></a>'
                era_panels.append(
                    f'<div class="history-phase state-{era.magic_state}" id="phase-{era.magic_state}" data-phase="{era.magic_state}">'
                    f'{hinge}<div class="phase-heading"><span class="phase-dot" aria-hidden="true"></span>'
                    f'<h2>{STATE_LABELS[era.magic_state]}</h2><p>{PHASE_COPY.get(era.magic_state, "A different relationship to time.")}</p></div></div>')
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
                span_text = (span.start, span.end, span.note) if span else ()
                search = " ".join((story.title, cycle.title, cycle.description, cycle.sequence_note,
                                   era.title, era.description, STATE_LABELS[era.magic_state], *era.context,
                                   placement.note, *moments, *span_text))
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
                f'<details class="history-era state-{era.magic_state}" id="era-{esc(era.id)}" data-era-section="{esc(era.id)}" data-magic-state="{era.magic_state}">'
                '<summary class="era-stop">'
                f'<span class="era-stop-copy"><span class="era-stop-title">{esc(era.title)}</span>'
                f'<span class="era-synopsis">{esc(era.description)}</span>'
                f'<small><span data-era-count>{len(era.stories)}</span> <span data-era-noun>{"story" if len(era.stories) == 1 else "stories"}</span></small>'
                '<span class="era-matches" data-era-matches hidden></span></span>'
                f'<span class="era-covers" aria-hidden="true">{previews}</span><span class="era-open" aria-hidden="true">↗</span></summary>'
                f'<dialog class="era-dialog" aria-labelledby="era-title-{esc(era.id)}" data-era-dialog>'
                '<div class="dialog-bar"><button type="button" data-dialog-close>← Back to the timeline</button>'
                f'<span>Cycle {number:02d} · {esc(STATE_LABELS[era.magic_state])}</span></div>'
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
            f'<p class="cycle-context">{esc(cycle.eyebrow)}</p>'
            f'<p class="cycle-history">{esc(cycle.description)}</p>'
            f'<p class="cycle-inheritance">{esc(cycle.sequence_note)}</p>'
            '<a class="cycle-to-braid" href="#atlas-currents">See the wider history ↑</a></header>'
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
    depth_cards = []
    for slug, (number, cycle, era) in locations.items():
        span = timeline.story_spans.get(slug)
        if not span:
            continue
        story = stories[slug]
        search = ' '.join((story.title, span.start, span.end, span.note, cycle.title, era.title))
        depth_cards.append(
            f'<article class="time-fold state-{era.magic_state}" data-time-fold data-search="{esc(search)}">'
            f'<p class="atlas-kicker">Placed frame · Cycle {number:02d} · {esc(STATE_LABELS[era.magic_state])}</p>'
            f'<h3><a href="#story-{esc(slug)}">{esc(story.title)} <span aria-hidden="true">↗</span></a></h3>'
            f'<div class="fold-path"><span>{esc(span.start)}</span><i aria-hidden="true">↝</i><span>{esc(span.end)}</span></div>'
            f'<p class="fold-note">{esc(span.note)}</p></article>')
    depths = (
        '<details class="depth-library" id="atlas-depths"><summary>Time within time '
        f'<span>{len(depth_cards)} histories</span> ↗</summary>'
        '<dialog class="depth-dialog" data-depth-dialog aria-labelledby="deep-history-title">'
        '<div class="dialog-bar"><button type="button" data-dialog-close>← Back to the timeline</button>'
        '<span>Local clocks · Buried civilizations · Living memory</span></div>'
        '<div class="dialog-content"><header class="depth-heading"><p class="atlas-kicker">The past inside the present</p>'
        '<h2 id="deep-history-title">Time within time</h2>'
        '<p>A life can cross centuries. A town can stand on several civilizations. A journey can return before its own history fits the clock.</p>'
        '<p class="depth-key">Each path follows a story’s experience, not the order of world eras. '
        'Lengths are not to scale; unresolved dates stay open. The cycle label locates the story’s placed frame.</p></header>'
        '<label class="depth-search" hidden><span>Find a history</span>'
        '<input type="search" data-history-search placeholder="Ravel, centuries, vanished cities…" autocomplete="off"></label>'
        f'<p class="depth-count" data-history-count role="status" aria-live="polite">{len(depth_cards)} histories</p>'
        f'<div class="time-folds">{"".join(depth_cards)}</div>'
        '<p data-history-empty hidden>No histories match. Try a place, title or interval.</p>'
        '</div></dialog></details>') if depth_cards else ''
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
        '<div class="chronicle-guide"><p>Follow the currents across. Explore the eras below.</p>'
        '<details class="reading-guide"><summary>How to read this history</summary><div>'
        '<p>A <b>Galactic Cycle</b> is an orbit of this world’s star system around the galaxy. '
        'The first orbit and absolute coordinates remain unknown. These cycle numbers locate this reconstruction, '
        'not a canonical calendar; spacing is schematic, not a measured duration.</p>'
        '<p>Magic’s extinction and return anchor the three great ages. Divine rule, technology and public powers '
        'have their own regional histories; they need not flourish, fade or return together. '
        'The extinction and return can fall inside an orbit, rather than at its edge.</p>'
        '<p>Technologies, institutions and inherited histories bring stories together. Within a cycle, '
        'regional stories may overlap in time; the order of era entries does not establish succession. '
        'Established sequences and local intervals take precedence.</p>'
        '<p>Open a story’s “Place in history” for its evidence and connections. Direct connections, historical hypotheses '
        'and thematic echoes are distinguished. A remembered event can reach beyond its story’s proposed era.</p></div></details></div>'
        f'{render_braid(timeline, stories)}'
        '<nav class="history-lenses" aria-label="Explore the layers of history">'
        f'{depths}<a href="#atlas-threads">Connections across history <span>{len(timeline.connections)} threads</span> ↗</a></nav>'
        '<div class="search-feedback" hidden data-search-feedback><p role="status" aria-live="polite" data-atlas-count></p>'
        '<button type="button" data-atlas-reset>Clear search ×</button></div>'
        f'<section class="worldline" id="atlas-explore" aria-label="{len(timeline.cycles)} cycles, {total_eras} eras"><span id="atlas-weave"></span>{"".join(rows)}'
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
