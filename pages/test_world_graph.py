"""The graph must reuse recorded relationships without inventing coverage."""
from copy import deepcopy
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from pages import build, graph_view, illustrated_editions
from pages.world_graph import graph_data


def story_fixture(slug, **changes):
    values = dict(
        slug=slug, title=slug.replace("-", " ").title(), created="2026-09-16",
        created_at="2026-09-16T12:00:00+00:00", edited="2026-09-16",
        rating="YA", canon=False, status="complete", prompt="A prompt.",
        cover=f"covers/{slug}.jpg", body="A story.\n",
    )
    values.update(changes)
    return build.Story(**values)


def timeline_fixture():
    return {
        "schemaVersion": 8,
        "cycles": [{
            "id": "early-cycle", "title": "An Earlier Cycle", "eyebrow": "An account.",
            "description": "An editorial grouping.", "sequenceNote": "Proposed order.",
            "eras": [{
                "id": "local-era", "title": "Local Histories", "magicState": "old-magic",
                "description": "A proposed context.", "context": ["One account.", "Another account."],
                "sequenceNote": "No shared cause established.",
                "stories": ["first-story", "second-story"], "window": {"start": 0, "end": 50},
            }],
        }],
        "storyPlacements": {
            "first-story": {"window": {"start": 1, "end": 10}, "note": "First proposed place."},
            "second-story": {"window": {"start": 20, "end": 30}, "note": "Second proposed place."},
        },
        "storyMoments": {}, "storySpans": {},
        "storyEvidence": {"first-story": "relative", "second-story": "undated"},
        "connections": [{
            "id": "first-to-second", "from": "first-story", "to": "second-story",
            "kind": "direct", "label": "A supplied sequence.", "note": "Its exact interval is unknown.",
            "ordering": "before", "basis": "reading-sequence",
        }, {
            "id": "first-echo-second", "from": "second-story", "to": "first-story",
            "kind": "echo", "label": "A recurring concern.", "note": "No common origin follows.",
            "ordering": "none", "basis": "thematic",
        }],
        "historyThreads": [{
            "id": "memory-history", "title": "Memory", "description": "Selected memory accounts.",
            "stages": [{"cycleId": "early-cycle", "title": "Earlier memory", "note": "A selected account.",
                        "anchors": ["first-story"], "kind": "proposed"}],
        }, {
            "id": "authority-history", "title": "Authority", "description": "Selected authority accounts.",
            "stages": [{"cycleId": "early-cycle", "title": "Earlier authority", "note": "A selected account.",
                        "anchors": ["first-story"], "kind": "proposed"}],
        }],
    }


class WorldGraphDataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="world-graph-test-")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "timeline.json"
        self.catalog = build.Catalog((
            story_fixture("new-story"), story_fixture("first-story", canon=True),
            story_fixture("second-story", rating="PG"),
        ))

    def write_model(self, model=None):
        self.path.write_text(json.dumps(model if model is not None else timeline_fixture()), encoding="utf-8")

    def test_all_publications_remain_nodes_when_classification_coverage_lags(self):
        self.write_model()
        result = graph_data(self.catalog, self.path)
        self.assertEqual([node["id"] for node in result["nodes"]],
                         [story.slug for story in self.catalog.stories])
        self.assertEqual(result["metadata"], {
            "classifiedCount": 2, "totalCount": 3, "unclassifiedCount": 1,
            "connectionCount": 2, "sourceAvailable": True,
        })
        new_story = result["nodes"][0]
        for key in ("cycle", "magic", "evidence", "history", "era"):
            self.assertEqual(new_story["classes"][key], [])
        self.assertEqual(new_story["classes"]["canon"], ["non-canon"])
        self.assertEqual(new_story["classes"]["rating"], ["YA"])
        self.assertEqual(new_story["placementNote"], "")
        json.dumps(result, allow_nan=False)

    def test_missing_optional_model_leaves_valid_graph_and_catalog_classifications(self):
        result = graph_data(self.catalog, self.path)
        self.assertEqual(len(result["nodes"]), 3)
        self.assertEqual(result["edges"], [])
        self.assertFalse(result["metadata"]["sourceAvailable"])
        self.assertEqual(result["metadata"]["unclassifiedCount"], 3)
        self.assertEqual(result["classifications"]["cycle"]["values"], [])
        self.assertEqual(result["nodes"][1]["classes"]["canon"], ["canon"])
        self.assertEqual(result["classifications"]["rating"]["values"],
                         [{"id": "PG", "label": "PG"}, {"id": "YA", "label": "YA"}])

    def test_empty_catalog_without_model_has_a_valid_empty_network(self):
        result = graph_data(build.Catalog(()), self.path)
        self.assertEqual(result["nodes"], [])
        self.assertEqual(result["edges"], [])
        self.assertEqual(result["metadata"], {
            "classifiedCount": 0, "totalCount": 0, "unclassifiedCount": 0,
            "connectionCount": 0, "sourceAvailable": False,
        })
        json.dumps(result, allow_nan=False)

    def test_malformed_existing_model_fails_instead_of_silently_dropping_relationships(self):
        for text in ("{broken", "[]", '{"schemaVersion": 8}'):
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Invalid world graph classification snapshot"):
                    graph_data(self.catalog, self.path)
        model = timeline_fixture()
        model["storyPlacements"]["first-story"]["window"]["end"] = 101
        self.write_model(model)
        with self.assertRaisesRegex(ValueError, "bounds|100|window"):
            graph_data(self.catalog, self.path)

    def test_orphan_classification_story_and_edge_fail(self):
        model = timeline_fixture()
        model["storyPlacements"]["unpublished-story"] = deepcopy(model["storyPlacements"]["first-story"])
        self.write_model(model)
        with self.assertRaisesRegex(ValueError, "absent from the publication catalog: unpublished-story"):
            graph_data(self.catalog, self.path)
        model = timeline_fixture()
        model["connections"][0]["to"] = "unpublished-story"
        self.write_model(model)
        with self.assertRaisesRegex(ValueError, "Connection endpoints must be different published stories"):
            graph_data(self.catalog, self.path)

    def test_only_explicit_history_anchors_receive_multiple_memberships(self):
        self.write_model()
        result = graph_data(self.catalog, self.path)
        first, second = result["nodes"][1:]
        self.assertEqual(first["classes"]["history"], ["memory-history", "authority-history"])
        self.assertEqual(second["classes"]["history"], [])
        self.assertEqual(first["classes"]["era"], second["classes"]["era"])
        self.assertEqual(first["placementNote"], "First proposed place.")

    def test_connection_provenance_and_direction_are_preserved_without_inferred_edges(self):
        model = timeline_fixture()
        self.write_model(model)
        edges = graph_data(self.catalog, self.path)["edges"]
        self.assertEqual(len(edges), len(model["connections"]))
        for actual, saved in zip(edges, model["connections"]):
            expected = {**saved, "source": saved["from"], "target": saved["to"]}
            del expected["from"], expected["to"]
            self.assertEqual(actual, expected)

    def test_illustrated_cover_overlay_preserves_source_identity_and_inputs(self):
        edition = {
            "source": {"slug": "first-story"}, "title": "Different Edition Title",
            "cover": {"path": "illustrated/first-story/cover.jpg"},
        }
        before = deepcopy((self.catalog, edition))
        result = graph_data(self.catalog, self.path, [edition])
        node = result["nodes"][1]
        self.assertEqual(node["title"], "First Story")
        self.assertEqual(node["href"], "stories/first-story.html")
        self.assertEqual(node["cover"], "illustrated/first-story/cover.jpg")
        self.assertEqual((self.catalog, edition), before)
        with self.assertRaisesRegex(ValueError, "Multiple illustrated"):
            graph_data(self.catalog, self.path, [edition, edition])

    def test_graph_reads_only_the_stored_classification_snapshot(self):
        self.write_model()
        read_text = Path.read_text
        allowed = self.path.resolve()

        def guarded_read(path, *args, **kwargs):
            self.assertEqual(path.resolve(), allowed, "Graph opened an unrelated or production file")
            return read_text(path, *args, **kwargs)

        with patch.object(Path, "read_text", guarded_read), patch.object(
            build, "load_story_source", side_effect=AssertionError("Production source read")
        ):
            result = graph_data(self.catalog, self.path)
        self.assertEqual(len(result["nodes"]), 3)

    def test_repository_model_reuses_validated_partial_coverage(self):
        catalog = build.load_catalog()
        result = graph_data(catalog, build.TIMELINE_PATH)
        self.assertEqual(len(result["nodes"]), len(catalog.stories))
        known = {node["id"] for node in result["nodes"]}
        for edge in result["edges"]:
            self.assertIn(edge["source"], known)
            self.assertIn(edge["target"], known)
        for node in result["nodes"]:
            for key, members in node["classes"].items():
                values = {value["id"] for value in result["classifications"][key]["values"]}
                self.assertTrue(set(members) <= values)


class GraphDocumentParser(HTMLParser):
    """Read actual HTML boundaries instead of trusting a script-shaped regex."""

    def __init__(self):
        super().__init__()
        self.scripts = []
        self.links = []
        self.graph_payload = ""
        self.in_graph_payload = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "a":
            self.links.append(attrs)
        if tag == "script":
            self.scripts.append(attrs)
            self.in_graph_payload = attrs.get("id") == "world-graph-data"

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_graph_payload = False

    def handle_data(self, data):
        if self.in_graph_payload:
            self.graph_payload += data


class WorldGraphPublicationTests(unittest.TestCase):
    def test_fixture_build_publishes_graph_and_shared_navigation_without_production_reads(self):
        with TemporaryDirectory(prefix="world-graph-build-test-") as temporary:
            root = Path(temporary)
            pages = root / "pages"
            (pages / "covers").mkdir(parents=True)
            plain = story_fixture("plain-story")
            illustrated = story_fixture("illustrated-source", canon=True)
            for story in (plain, illustrated):
                Image.new("RGB", (864, 1536), "navy").save(pages / story.cover)
            catalog_path = pages / "catalog.json"
            build.save_catalog([plain, illustrated], catalog_path)
            cover_path = pages / "illustrated/selected-edition/cover.png"
            cover_path.parent.mkdir(parents=True)
            Image.new("RGB", (32, 48), "ivory").save(cover_path)
            edition = {
                "slug": "selected-edition", "title": illustrated.title, "mode": "classic",
                "source": {"slug": illustrated.slug,
                           "bodySha256": hashlib.sha256(illustrated.body.encode()).hexdigest()},
                "body": illustrated.body,
                "cover": {"id": "cover", "path": "illustrated/selected-edition/cover.png",
                          "sha256": hashlib.sha256(cover_path.read_bytes()).hexdigest()},
                "illustrations": [],
            }
            edition_path = pages / "illustrated.json"
            edition_path.write_text(json.dumps({"schemaVersion": 1, "editions": [edition]}), encoding="utf-8")
            before = {path: path.read_bytes() for path in (catalog_path, edition_path, cover_path)}
            output = root / "site"

            with patch.object(build, "load_story_source", side_effect=AssertionError("Production source read")):
                catalog = build.build(output, catalog_path)

            self.assertEqual({story.slug for story in catalog.stories}, {plain.slug, illustrated.slug})
            for asset in ("world.html", "world-graph.js", "world-graph.css", "theme.js", "styles.css"):
                self.assertTrue((output / asset).is_file(), asset)
            self.assertFalse((output / "timeline.html").exists())
            self.assertFalse((pages / "timeline.json").exists())
            for route, href, active in (
                ("index.html", "world.html", False),
                ("world.html", "world.html", True),
                ("stories/plain-story.html", "../world.html", False),
                ("stories/illustrated-source.html", "../world.html", False),
            ):
                with self.subTest(route=route):
                    parser = GraphDocumentParser()
                    parser.feed((output / route).read_text(encoding="utf-8"))
                    links = [link for link in parser.links if link.get("href") == href]
                    self.assertEqual(len(links), 1)
                    self.assertEqual(links[0].get("aria-current") == "page", active)
            parser = GraphDocumentParser()
            parser.feed((output / "world.html").read_text(encoding="utf-8"))
            data = json.loads(parser.graph_payload)
            self.assertEqual(data["metadata"]["unclassifiedCount"], 2)
            self.assertFalse(data["metadata"]["sourceAvailable"])
            self.assertEqual(len(data["nodes"]), 2)
            node = next(node for node in data["nodes"] if node["id"] == illustrated.slug)
            self.assertEqual(node["cover"], "illustrated/selected-edition/cover.png")
            self.assertEqual(node["href"], "stories/illustrated-source.html")
            for path, original in before.items():
                self.assertEqual(path.read_bytes(), original)

    def test_hostile_title_cannot_close_inline_json_or_create_markup(self):
        title = '</script><script>alert("escaped")</script><img src=x onerror=alert(1)> & <b>story</b>'
        data = graph_data(build.Catalog((story_fixture("hostile-story", title=title),)), None)
        document = graph_view.render_graph(data)
        parser = GraphDocumentParser()
        parser.feed(document)
        self.assertEqual(parser.scripts, [{"type": "application/json", "id": "world-graph-data"}])
        self.assertEqual(json.loads(parser.graph_payload)["nodes"][0]["title"], title)
        self.assertNotIn("<", parser.graph_payload)
        self.assertNotIn('<img src=x', document)
        self.assertEqual(sum(link.get("href") == "stories/hostile-story.html" for link in parser.links), 1)

    def test_actual_catalog_is_complete_and_publication_inputs_remain_unchanged(self):
        paths = (build.SNAPSHOT_PATH, build.TIMELINE_PATH, build.SNAPSHOT_PATH.with_name("illustrated.json"))
        before = {path: hashlib.sha256(path.read_bytes()).digest() for path in paths}
        catalog = build.load_catalog()
        editions = illustrated_editions.load_snapshot(paths[2])
        with patch.object(build, "load_story_source", side_effect=AssertionError("Production source read")):
            document = graph_view.render_graph(graph_data(catalog, build.TIMELINE_PATH, editions))
        parser = GraphDocumentParser()
        parser.feed(document)
        data = json.loads(parser.graph_payload)
        expected = Counter({story.slug: 1 for story in catalog.stories})
        self.assertEqual(Counter(node["id"] for node in data["nodes"]), expected)
        self.assertEqual(Counter(link.get("href") for link in parser.links),
                         Counter({f"stories/{story.slug}.html": 1 for story in catalog.stories}))
        for path, original in before.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), original)


if __name__ == "__main__":
    unittest.main()
