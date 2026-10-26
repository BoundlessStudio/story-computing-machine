"""Derive the report dataset and text companion from recorded audit evidence."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import statistics
import sys

OUT = Path(__file__).resolve().parents[1]
APP = OUT / "report-app"
d = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
m = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
rows = d["rows"]
native = [r for r in rows if r.get("response", {}).get("answers")]
scored = [r for r in rows if r.get("score") is not None]
counts = Counter(r["status"] for r in rows)
summary = {
    "stories": len(m["packages"]), "stage_slots": len(rows), "available_artifacts": sum(r["status"] != "Unavailable" for r in rows),
    "api_results": len(native), "pending": counts["Pending"], "proceed": counts["Would proceed"], "restart": counts["Would restart"], "judgment": counts["Needs judgment"],
    "partial": counts["Partial evidence"], "unavailable": counts["Unavailable"], "errors": counts["API error"],
    "original_images": sum(p["reference_count"] for p in m["packages"]), "image_packages": sum(p["reference_count"] > 0 for p in m["packages"]),
    "image_evaluations": sum(r["reference_count"] for r in native), "canon_stories": sum(p["canon"] for p in m["packages"]),
    "raw_below_threshold": sum(r["score"] < 3 for r in scored), "confidence_below_threshold": sum(r["minimum_confidence"] < .8 for r in scored),
    "median_confidence": statistics.median(r["minimum_confidence"] for r in scored) if scored else None,
    "source_changes": len(d["manifest"].get("changed_source_files", [])),
    "input_tokens": sum(r["response"].get("usage", {}).get("input_tokens",0) for r in native),
    "cached_tokens": sum(r["response"].get("usage", {}).get("input_tokens_details", {}).get("cached_tokens",0) for r in native),
    "api_attempts": sum(len(r.get("attempts",[])) for r in rows),
}
stage_summary = []
for stage in ("outline", "final"):
    subset = [r for r in rows if r["stage"] == stage]
    c = Counter(r["status"] for r in subset)
    stage_summary.append({"stage": "Outline / plan" if stage == "outline" else "Final prose", "slots": len(subset), "scored": sum(r["score"] is not None for r in subset), "would_proceed": c["Would proceed"], "would_restart": c["Would restart"], "needs_judgment": c["Needs judgment"], "partial_evidence": c["Partial evidence"], "unavailable": c["Unavailable"], "api_error": c["API error"], "pending": c["Pending"]})
histogram = []
for lower in range(0,10):
    upper = lower + 1
    histogram.append({"confidence_band": f"{lower*10}–{upper*10}%", "artifacts": sum(lower/10 <= r["minimum_confidence"] < upper/10 or (upper == 10 and r["minimum_confidence"] == 1) for r in scored)})

definitions = [
    {"label":"Checkpoint score", "definition":"Minimum of the native prompt_fidelity, experience_fidelity, and (when originals exist) reference_fidelity scores. Each score is the probability-weighted index of the five rubric levels, from 0 to 4. Missing scores are null, never zero.", "componentIds":["audit-results","audit-detail","audit-summary"]},
    {"label":"Minimum confidence", "definition":"Minimum native Decisions confidence among applicable score questions. This is the model's returned statistic; it has not been calibrated as a probability that the judgment is correct.", "componentIds":["audit-results","audit-detail","confidence-distribution","audit-summary"]},
    {"label":"Gate outcome", "definition":"Uses the production assess_response with restarts=0. Uncertainty takes precedence: confidence <0.80, source_ambiguity >0.20, material_violation between 0.20 and 0.80, passing scores with violation >=0.80, or missing inputs require judgment. Only a reliable score <3 would restart; otherwise proceed. Historical restart counts are not inferred.", "componentIds":["audit-results","audit-detail","audit-summary","stage-coverage"]},
]
source = {"label":"Repository source snapshots and live OpenAI Decisions results", "tables":["reports/story-fidelity-audit-2026-10-25/results.json","reports/story-fidelity-audit-2026-10-25/manifest.json"], "filters":["268 current story packages; stories/_template and Git history excluded", "Full saved prompt and current outline/plan or prose; generated art and editorial reviews excluded", "91 saved originals supplied as actual image bytes at original detail; one missing original explicitly flagged"], "metricDefinitions": definitions,
 "evidenceFlow":[
  {"title":"Source inventory", "detail":f"Provider: local filesystem; tool: Python pathlib. Root: {m['source_root']}/stories. Source revision: {m['git_revision']}. Exact per-file paths, byte counts and SHA-256 digests are in manifest.json. Files were copied into tmp/fidelity-audit-2026-10-25/snapshots without altering story packages."},
  {"title":"API evaluation", "detail":f"Provider: OpenAI; tool: global Decisions skill create_decision; endpoint: {m['endpoint']}; model: {m['model']}; full non-secret requests under tmp/fidelity-audit-2026-10-25/bundles/<slug>/<stage>.json. Native responses and request digests are retained in results.json and tmp/.../responses. Four concurrent requests; at most one retry for a transient transport/API failure; no resampling on low scores or uncertainty."},
  {"title":"Gate classification", "detail":"Tool: .agents/skills/story-create/scripts/fidelity_checkpoint.py assess_response(bundle,response,restarts=0,conflict=missing_reference). Pure classification only; no production run, restart ledger, story revisions, or per-story halt. Report uncertainty is consolidated for user review."},
  {"title":"Version check", "detail":f"Sources hashed before evaluation; source changes detected at completion: {d['manifest'].get('changed_source_files', 'completion check pending')}. Results describe the captured source version and are not automatically refreshed."},
 ]}

def query(query_rows, methods, custom_source=None):
    return {"rows": query_rows, "source": custom_source or source, "methods":[{"language":"text","code":methods}]}

review_path=OUT / "review-notes.json"
review_notes=json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else []
preview_path=OUT / "image-previews.json"
previews=json.loads(preview_path.read_text(encoding="utf-8")) if preview_path.exists() else {}
for package in m["packages"]:
    package["external_text_references"] = sorted(set(re.findall(r"stories/[A-Za-z0-9_-]+/(?:story|05-story)\.md",package["prompt_text"])))
    for ref in package["reference_files"]:
        ref.update(previews.get(ref["sha256"],{}))
dataset = {"id":"story-fidelity-audit-2026-10-25-4a09", "surface":"report", "title":"Story fidelity audit", "generatedAt":datetime.now(timezone.utc).isoformat(), "buildStatus":"complete" if '--complete' in sys.argv else "creating", "status":"observed", "filters":[], "report":{"asOf":"2026-10-25"},
 "audit":{"sourceRevision":m["git_revision"],"capturedAt":m["created_at"],"completedAt":d["manifest"].get("completed_at"), "summary":summary, "reviewNotes":review_notes},
 "queries":{
  "artifacts":query(rows,"One row per story and stage; use results.json rows verbatim. Native probabilities/answers retained. No joins, sampling, imputation, score smoothing or rounding in source evidence."),
  "packages":query(m["packages"],"One row per package; prompt text and original file inventory read from saved sources. Current filenames or legacy numbered filenames are mapped to common stage names. No prompt edits sent to the API."),
  "summary":query([summary],"Count statuses across all 536 requested stage slots; native responses exclude unavailable/error inputs. Confidence median uses only non-null minimum_confidence. Token totals sum native usage.input_tokens; attempts include recorded transient retries. See scripts/prepare_report.py for exact executable calculations."),
  "stages":query(stage_summary,"Group artifacts by stage and count each exclusive outcome; scored counts rows with non-null score. Every stage has 268 requested slots."),
  "confidence":query(histogram,"Filter artifacts to non-null minimum_confidence. Count into [0,.1),[.1,.2),...,[.9,1] intervals; include 1 in final bucket. No missing values are filled."),
 }}
if (APP / "src/data.json").exists():
    dataset["id"] = json.loads((APP / "src/data.json").read_text(encoding="utf-8"))["id"]
(OUT / "report-data.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2),encoding="utf-8")
if APP.exists():
    (APP / "src/data.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2),encoding="utf-8")

lines=["# Story fidelity audit", "", f"Source snapshot: {m['created_at']} · repository commit `{m['git_revision']}`.", "", f"Evaluated {len(native)} of {summary['available_artifacts']} available artifacts across {summary['stories']} stories: 267 outlines/plans and 268 prose files. There are 536 requested stage slots, including one missing outline. The original-image inventory contains {summary['original_images']} images across {summary['image_packages']} packages.", "", "## Checkpoint outcomes", "", "| Stage | Scored | Would proceed | Would restart | Needs judgment | Partial evidence | Unavailable | API errors | Pending |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
for r in stage_summary:
    lines.append(f"| {r['stage']} | {r['scored']} | {r['would_proceed']} | {r['would_restart']} | {r['needs_judgment']} | {r['partial_evidence']} | {r['unavailable']} | {r['api_error']} | {r['pending']} |")
lines += ["", f"{summary['raw_below_threshold']} raw checkpoint scores are below 3/4; {summary['confidence_below_threshold']} assessments have minimum confidence below 0.80. Low scores with uncertainty are review findings, not reliable restart decisions. Native confidence is not measured judgment accuracy.", "", "## Evidence gaps", "", "- `after-the-party`: no saved outline or story plan; final prose evaluated.", "- `a-seat-for-the-sun`: the saved prompt names an original image that is absent. Both stages receive partial text-based evaluation and cannot receive a complete multimodal pass.", "- `the-first-year`: later requests to edit the generated table sheet are preserved as context. The sheet is explicitly an art-edit target; this audit covers outline and prose, not whether art edits were performed.", "", "## Method and limits", "", "The production checkpoint rubric and pure assessor were reused with restarts=0. Complete saved prompts, later directions, and each full current candidate were submitted. All saved original references were supplied as image bytes at original detail, respecting each prompt's intended use. A temporary filename/inventory adapter handled historical layouts; it did not change the prompt sent to the API. Generated covers, character sheets, location art, reviews, and notes were excluded as evaluation authority.", "", "This retrospective batch continues through uncertain findings so all packages can be reviewed together. No outlines, stories, prompts, notes, art, canon flags, or checkpoint restart ledgers were changed. Existing historical restart budgets were not inferred. A missing old outline cannot be reconstructed, and later prompt directions may postdate a saved outline. Score differences between stages are exploratory, not proof that the prose regressed.", "", "The Decisions API returns probabilities and confidence but no explanatory critique in these checkpoint answers. The report's reasons describe gate logic. They must not be treated as a diagnosis of which passage failed. No independent close reading of the entire corpus or empirical calibration was performed.", "", f"Source changes found after evaluation: {json.dumps(d['manifest'].get('changed_source_files','completion check pending'))}.", "", f"Recorded API usage: {summary['input_tokens']:,} input tokens, including {summary['cached_tokens']:,} cached tokens; {summary['api_attempts']} attempts. Usage is reported without estimating a billed monetary amount.", "", "## Files", "", "- `results.csv`: all artifact outcomes and numeric dimensions.", "- `results.json`: full source text, gate assessments, native answers, probabilities, timing, attempts and API usage.", "- `manifest.json`: full writing prompts, image inventory and source hashes.", "- `scripts/audit.py`: reproducible inventory/evaluation driver; uses the globally installed Decisions client.", "- `scripts/prepare_report.py`: exact report aggregation and export.", "", "The interactive report supports searching, stage/outcome/image/canon filters, and selecting any artifact to inspect its saved request, full text and probability distributions."]
if review_notes:
    lines += ["", "## Targeted reading notes", ""]
    for note in review_notes:
        lines += [f"### {note['title']}", "", note['text'], ""]
(OUT / "REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
with (OUT / "REPORT.md").open("a",encoding="utf-8") as stream:
    stream.write("\nAdditional scope limit: `the-old-percentage` requires continuity with `stories/empire-within/story.md` (*Nobody Spends Her Name*). The checkpoint received the saved prompt's continuity description, but did not expand that linked prior prose. Full continuity fidelity remains unverified; the raw score does not explain its cause.\n")
print(json.dumps(summary,indent=2))
