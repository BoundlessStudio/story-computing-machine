"""A layered atlas of one world, with its chronology and evidence intact."""
from __future__ import annotations
import html

STATE_LABELS = {"old-magic": "Old magic", "long-dark": "The Long Dark", "new-magic": "New magic",
                "uncertain": "Unplaced in time", "off-axis": "Beyond the material clock"}
EVIDENCE = {"boundary": "Worldline boundary", "constrained": "Established constraint",
            "relative": "Relative sequence", "contextual": "Contextual evidence", "undated": "Date unresolved"}
LINK_LABELS = {"direct": "Direct connection", "historical": "Historical hypothesis", "echo": "Thematic echo"}
BASIS_LABELS = {"established": "Established chronology", "reading-sequence": "Supplied reading sequence",
                "proposed": "Proposed historical interpretation", "thematic": "A parallel, not a date"}
STAGE_LABELS = {"established": "Story anchor", "proposed": "Reconstruction",
                "recurrence": "A later recurrence", "absence": "An absence matters"}

def esc(value):
    return html.escape(str(value), quote=True)


def render_cartography(timeline, stories):
    """A changeable atlas of selected accounts over one shared chronology."""
    lenses = [('all', 'Whole history',
               'Many civilizations. Overlapping lives. Begin with the whole world, or follow one of its histories.', None)]
    lenses += [(thread.id, thread.title, thread.description, thread) for thread in timeline.history_threads]
    buttons, descriptions, views, accounts = [], [], [], []
    first_cycle = timeline.cycles[0].id
    for lens_number, (lens, title, description, thread) in enumerate(lenses):
        buttons.append(f'<button type="button" data-history-lens="{esc(lens)}" '
                       f'aria-pressed="{str(lens_number == 0).lower()}">{esc(title)}</button>')
        descriptions.append(f'<p data-lens-description="{esc(lens)}"'
                            f'{" hidden" if lens_number else ""}>{esc(description)}</p>')
        stages = {stage.cycle_id: stage for stage in thread.stages} if thread else {}
        columns = []
        for number, cycle in enumerate(timeline.cycles, 1):
            stage = stages.get(cycle.id)
            # Overview illustrations are entry points, not membership or chronology claims.
            overview_anchors = list(dict.fromkeys(slug for current in timeline.history_threads
                for item in current.stages if item.cycle_id == cycle.id for slug in item.anchors))[:3]
            anchors = list(stage.anchors) if stage else ([] if thread else overview_anchors)
            cycle_icon = f"cycle-icons/{cycle.id}.png"
            heading = stage.title if stage else ('No account selected' if thread else cycle.eyebrow)
            note = stage.note if stage else ('No account has been selected for this history in this cycle. Explore its stories below.' if thread else cycle.description)
            selected = stage.anchors if stage else (() if thread else cycle.stories)
            marks = []
            for index, slug in enumerate(selected):
                window = timeline.story_placements[slug].window
                x = 18 + (index % 5) * 21
                y1, y2 = 18 + window.start * 1.6, 18 + window.end * 1.6
                marks.append(f'<g data-map-story="{esc(slug)}"><line x1="{x}" x2="{x}" '
                             f'y1="{y1:.2f}" y2="{y2:.2f}"/><circle cx="{x}" cy="{(y1+y2)/2:.2f}" r="2"/></g>')
            columns.append(
                f'<a class="map-cycle" href="#cycle-{esc(cycle.id)}" data-map-cycle="{esc(cycle.id)}" '
                f'aria-current="{str(cycle.id == first_cycle).lower()}">'
                f'<span class="map-number"><b>{number:02d}</b><span>Cycle</span></span>'
                f'<span class="map-window"><img src="{esc(cycle_icon)}" alt="" '
                f'width="1280" height="1280" loading="lazy"><svg class="map-constellation" '
                f'viewBox="0 0 120 200" aria-hidden="true">{"".join(marks)}</svg></span>'
                f'<strong class="map-cycle-title">{esc(cycle.title)}</strong>'
                f'<span class="map-stage-title">{esc(heading)}</span>'
                f'<span class="map-count">{len(cycle.stories)} stories in cycle <i aria-hidden="true">↗</i></span></a>')
            anchor_links = ''.join(f'<a href="#story-{esc(slug)}"><span>{esc(stories[slug].title)}</span> '
                                   '<i aria-hidden="true">↗</i></a>' for slug in anchors)
            stage_kind = STAGE_LABELS[stage.kind] if stage else ('An open account' if thread else 'Proposed historical horizon')
            stage_attrs = f' data-history-stage data-stage-cycle="{esc(cycle.id)}"' if stage else ''
            account_id = f' id="current-{esc(lens)}" data-history-thread ' if thread and number == 1 else ''
            accounts.append(
                f'<article class="desk-account"{account_id} data-account-lens="{esc(lens)}" '
                f'data-account-cycle="{esc(cycle.id)}"{stage_attrs}'
                f'{" hidden" if lens_number or number != 1 else ""}>'
                f'<div class="desk-illustration"><img src="{esc(cycle_icon)}" alt="" '
                'width="1280" height="1280" loading="lazy"></div>'
                f'<div class="desk-copy"><p class="atlas-kicker">Cycle {number:02d} · {esc(stage_kind)}</p>'
                f'<h3>{esc(stage.title if stage else ("No account selected" if thread else cycle.title))}</h3><p>{esc(note)}</p>'
                f'<div class="desk-anchors"><span>{"Stories to enter through" if anchors else "This account remains open"}</span>'
                f'{anchor_links}</div><div class="desk-actions"><a href="#cycle-{esc(cycle.id)}">'
                f'Explore all {len(cycle.stories)} stories in this cycle <span aria-hidden="true">→</span></a>'
                '</div></div></article>')
        views.append(f'<div class="map-view lens-{lens_number}" data-lens-view="{esc(lens)}" '
                     f'style="--cycle-count:{len(timeline.cycles)}"'
                     f'{" hidden" if lens_number else ""}>{"".join(columns)}</div>')
    return (
        '<section class="atlas-cartography" id="atlas-currents" aria-labelledby="cartography-title">'
        '<header class="cartography-heading"><div><p class="atlas-kicker">Choose a way through time</p>'
        '<h2 id="cartography-title">A world, lived many ways.</h2></div>'
        '<p>Follow a history. Find a civilization. Step into a life.</p></header>'
        f'<nav class="lens-nav" aria-label="Historical lens" hidden>{"".join(buttons)}</nav>'
        f'<div class="lens-introduction">{"".join(descriptions)}</div>'
        '<p class="map-mobile-hint">Explore across the cycles →</p>'
        f'<div class="atlas-panorama" tabindex="0" role="region" aria-label="{len(timeline.cycles)} cycles of one world; scroll horizontally on small screens">'
        f'{"".join(views)}</div>'
        '<p class="map-legend"><span>Earlier <i aria-hidden="true">⟶</i> Later</span>'
        '<span>Story marks trace proposed placement windows. Spacing is schematic, not a measured duration.</span></p>'
        f'<div class="atlas-desk" aria-live="polite" aria-atomic="false">{"".join(accounts)}</div>'
        '<p class="atlas-account-note">These lenses offer selected accounts, not exhaustive categories. '
        'A recurring form can be reinvented; the thread alone does not establish descent. '
        'Explore a cycle to find every story placed there.</p>'
        '<noscript><p>Follow a cycle above to browse its eras. Enable JavaScript to switch historical lenses.</p></noscript></section>')

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
                era_panels.append(f'<span class="phase-anchor" id="phase-{era.magic_state}" data-phase="{era.magic_state}" aria-hidden="true"></span>')
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
            '<details class="cycle-background"><summary>Read this cycle’s history and placement</summary><div>'
            f'<p class="cycle-history">{esc(cycle.description)}</p>'
            f'<p class="cycle-inheritance">{esc(cycle.sequence_note)}</p></div></details>'
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
    cycle_options = ''.join(f'<option value="{esc(cycle.id)}">{number:02d} · {esc(cycle.title)}</option>' for number, cycle in enumerate(timeline.cycles, 1))
    total_eras = sum(len(cycle.eras) for cycle in timeline.cycles)
    return (
        '<a class="atlas-skip" href="#atlas-explore">Skip to the timeline</a><div class="atlas" data-timeline>'
        '<header class="chronicle-intro"><div><p class="atlas-kicker">One world · Deep time</p>'
        '<h1>An atlas of lives.</h1><p>Civilizations rise. Lives intertwine. The past remains.</p></div>'
        f'<p class="chronicle-total"><b>{len(stories)}</b> stories woven through<br> <b>{len(timeline.cycles)}</b> cycles of one history.</p></header>'
        '<div class="chronicle-guide"><p>One world. No single path through its history.</p>'
        '<details class="reading-guide"><summary>How to read this history</summary><div>'
        '<p>A <b>Galactic Cycle</b> is an orbit of this world’s star system around the galaxy. '
        'The first orbit and absolute coordinates remain unknown. These cycle numbers locate this reconstruction, '
        'not a canonical calendar; spacing is schematic, not a measured duration.</p>'
        '<p>Magic’s extinction and return are two major events. Divine rule, technology and public powers '
        'have their own regional histories; they need not flourish, fade or return together. '
        'The extinction and return can fall inside an orbit, rather than at its edge.</p>'
        '<p>Technologies, institutions and inherited histories bring stories together. Within a cycle, '
        'regional stories may overlap in time; the order of era entries does not establish succession. '
        'Established sequences and local intervals take precedence.</p>'
        '<p>Open a story’s “Place in history” for its evidence and connections. Direct connections, historical hypotheses '
        'and thematic echoes are distinguished. A remembered event can reach beyond its story’s proposed era.</p></div></details></div>'
        f'{render_cartography(timeline, stories)}'
        '<nav class="history-lenses" aria-label="Explore the layers of history">'
        f'{depths}<a href="#atlas-threads">Connections across history <span>{len(timeline.connections)} threads</span> ↗</a></nav>'
        '<header class="archive-heading" id="atlas-archive"><p class="atlas-kicker">The inhabited world</p>'
        '<h2>Find your place in history.</h2><p>Browse the societies within a cycle. Their horizons can overlap.</p></header>'
        '<div class="chronicle-toolbar"><label class="cycle-picker" hidden><span>Explore a cycle</span>'
        f'<select data-cycle-picker><option value="all">All cycles · The whole chronology</option>{cycle_options}</select></label>'
        '<label class="atlas-search" hidden><span>Search every cycle</span>'
        '<input type="search" data-atlas-search placeholder="Story, place, person, idea…" autocomplete="off"></label></div>'
        '<div class="search-feedback" data-search-feedback><p role="status" aria-live="polite" data-atlas-count></p>'
        '<button type="button" data-atlas-reset hidden>Clear search ×</button></div>'
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
