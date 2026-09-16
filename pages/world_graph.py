"""Build a story network from stored publication and classification snapshots.

The retained chronology is an optional source of editorial classifications and
explicit connections. It is not a source of new canon, nor must newly published
stories acquire a chronological placement before they appear in the network.
"""
from __future__ import annotations

from pathlib import Path


MAGIC_LABELS = {
    "old-magic": "Old magic",
    "long-dark": "The Long Dark",
    "new-magic": "New magic",
    "uncertain": "Unplaced in time",
    "off-axis": "Beyond the material clock",
}
EVIDENCE_LABELS = {
    "boundary": "Worldline boundary",
    "constrained": "Established constraint",
    "relative": "Relative sequence",
    "contextual": "Contextual evidence",
    "undated": "Date unresolved",
}


def graph_data(catalog, timeline_path, editions=()):
    """Return JSON-ready nodes, explicit edges, and independent classifications.

    All catalog stories become nodes in catalog order. Empty classification
    arrays mean no membership was recorded; they do not assert an absence in
    the story. Edges retain their original provenance and direction semantics.
    No source packages, universe files, or story prose are inspected.
    """
    # A local import supports both `python pages/build.py` and package imports
    # without making the build renderer and its data module import each other.
    if __package__:
        from . import build
    else:
        import build

    known = {story.slug for story in catalog.stories}
    if len(known) != len(catalog.stories):
        raise ValueError("World graph requires unique publication catalog story slugs")
    selected = build._editions_by_source(editions, known)
    path = Path(timeline_path) if timeline_path is not None else None
    timeline = None
    if path is not None and path.exists():
        try:
            raw = build.read_json_object(path)
            placements = raw.get("storyPlacements")
            if not isinstance(placements, dict):
                raise ValueError("storyPlacements must be an object")
            orphaned = sorted(set(placements) - known)
            if orphaned:
                raise ValueError(
                    "Classification stories are absent from the publication catalog: "
                    + ", ".join(orphaned)
                )
            # The original model validator intentionally requires exact coverage
            # of its selected catalog. New publications remain unclassified.
            covered = build.Catalog(tuple(story for story in catalog.stories
                                          if story.slug in placements))
            timeline = build.load_timeline(covered, path)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise ValueError(f"Invalid world graph classification snapshot {path}: {exc}") from exc

    classifications = {
        "cycle": {
            "label": "Historical cycle",
            "description": "Retained editorial groupings of the world's history; placements remain proposed.",
            "values": [],
        },
        "magic": {
            "label": "Magic phase",
            "description": "The proposed material conditions of a story's era, not a claim that every story shows magic.",
            "values": [],
        },
        "evidence": {
            "label": "Placement evidence",
            "description": "The evidence supporting historical placement, independently of the proposed cycle.",
            "values": [],
        },
        "history": {
            "label": "Shared histories",
            "description": "Selected editorial anchors for recurring histories. Stories can belong to several; membership establishes no shared origin or descent.",
            "values": [],
        },
        "canon": {
            "label": "Canon status",
            "description": "The story's recorded publication status. Shared-universe authority remains in the universe notes.",
            "values": [
                {"id": "canon", "label": "Canon"},
                {"id": "non-canon", "label": "Non-canon"},
            ],
        },
        "rating": {
            "label": "Reading rating",
            "description": "The content rating recorded in the publication catalog.",
            "values": [
                {"id": rating, "label": rating} for rating in ("PG", "YA", "R+")
                if any(story.rating == rating for story in catalog.stories)
            ],
        },
        "era": {
            "label": "Historical era",
            "description": "Finer editorial groupings of compatible local histories. Sharing an era does not establish contact or an order between stories.",
            "values": [],
        },
    }
    nodes = []
    by_id = {}
    for story in catalog.stories:
        edition = selected.get(story.slug)
        classes = {key: [] for key in classifications}
        classes["canon"] = ["canon" if story.canon else "non-canon"]
        classes["rating"] = [story.rating]
        node = {
            "id": story.slug,
            "title": story.title,
            "href": f"stories/{story.slug}.html",
            "cover": edition["cover"]["path"] if edition else story.cover,
            "canon": story.canon,
            "rating": story.rating,
            "classes": classes,
            "placementNote": "",
        }
        nodes.append(node)
        by_id[story.slug] = node

    edges = []
    if timeline is not None:
        used_magic = set()
        used_evidence = set()
        for cycle in timeline.cycles:
            classifications["cycle"]["values"].append({
                "id": cycle.id, "label": cycle.title,
                "description": cycle.description,
            })
            for era in cycle.eras:
                classifications["era"]["values"].append({
                    "id": era.id, "label": era.title,
                    "description": era.description,
                })
                used_magic.add(era.magic_state)
                for slug in era.stories:
                    node = by_id[slug]
                    evidence = timeline.story_evidence[slug]
                    node["classes"]["cycle"] = [cycle.id]
                    node["classes"]["era"] = [era.id]
                    node["classes"]["magic"] = [era.magic_state]
                    node["classes"]["evidence"] = [evidence]
                    node["placementNote"] = timeline.story_placements[slug].note
                    used_evidence.add(evidence)
        for key, labels, used in (
            ("magic", MAGIC_LABELS, used_magic),
            ("evidence", EVIDENCE_LABELS, used_evidence),
        ):
            classifications[key]["values"] = [
                {"id": value, "label": label}
                for value, label in labels.items() if value in used
            ]
        for thread in timeline.history_threads:
            classifications["history"]["values"].append({
                "id": thread.id, "label": thread.title,
                "description": thread.description,
            })
            for stage in thread.stages:
                for slug in stage.anchors:
                    by_id[slug]["classes"]["history"].append(thread.id)
        edges = [{
            "id": link.id, "source": link.source, "target": link.target,
            "kind": link.kind, "label": link.label, "note": link.note,
            "basis": link.basis, "ordering": link.ordering,
        } for link in timeline.connections]

    classified_count = len(timeline.story_placements) if timeline is not None else 0
    return {
        "nodes": nodes,
        "edges": edges,
        "classifications": classifications,
        "metadata": {
            "classifiedCount": classified_count,
            "totalCount": len(nodes),
            "unclassifiedCount": len(nodes) - classified_count,
            "connectionCount": len(edges),
            "sourceAvailable": timeline is not None,
        },
    }
