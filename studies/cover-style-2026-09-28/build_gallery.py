"""Build a local, self-contained source/candidate comparison gallery."""

from __future__ import annotations

import html
import json
from pathlib import Path


STUDY_DIR = Path(__file__).resolve().parent
MANIFEST = STUDY_DIR / "manifest.json"
OUTPUT = STUDY_DIR / "gallery.html"
STUDY_PREFIX = "studies/cover-style-2026-09-28/"


def card(entry: dict) -> str:
    title = html.escape(entry["title"])
    slug = html.escape(entry["slug"])
    status = entry["style_status"]
    tags = [status.replace("_", " ")]
    if entry.get("detail_class"):
        tags.append(entry["detail_class"])
    if entry["canon"]:
        tags.append("canon locked")
    if entry.get("candidate_status"):
        tags.append(entry["candidate_status"].replace("_", " "))
    source = "../../" + entry["source_cover_path"]
    candidate = entry["candidate_path"].removeprefix(STUDY_PREFIX)
    has_candidate = (STUDY_DIR / candidate).exists()
    candidate_html = (
        f'<a href="{html.escape(candidate)}" target="_blank" rel="noopener"><img loading="lazy" src="{html.escape(candidate)}" alt="Painted candidate for {title}"></a>'
        if has_candidate else ('<div class="missing">Already painted — no candidate needed</div>' if status == "skip_already_painted" else '<div class="missing">Candidate pending</div>')
    )
    tags_html = "".join(f"<span>{html.escape(tag)}</span>" for tag in tags)
    return f"""<article class="card" data-status="{html.escape(status)}" data-detail="{html.escape(entry.get("detail_class") or "")}" data-canon="{str(entry["canon"]).lower()}" data-search="{html.escape((entry["title"] + " " + entry["slug"]).lower())}">
      <header><h2>{title}</h2><small>{slug}</small><div class="tags">{tags_html}</div></header>
      <div class="images">
        <figure><a href="{html.escape(source)}" target="_blank" rel="noopener"><img loading="lazy" src="{html.escape(source)}" alt="Original cover for {title}"></a><figcaption>Original</figcaption></figure>
        <figure>{candidate_html}<figcaption>Painted study</figcaption></figure>
      </div>
    </article>"""


def main() -> None:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]
    cards = "\n".join(card(entry) for entry in entries)
    document = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painted cover study — comparison gallery</title>
<style>
:root { color-scheme: dark; font: 15px/1.45 system-ui, sans-serif; background:#151b24; color:#f4eee2 }
body { margin:0; }
.top { position:sticky; top:0; z-index:10; background:#151b24ef; backdrop-filter:blur(12px); border-bottom:1px solid #38414b; padding:12px clamp(16px,3vw,40px) }
h1 { margin:0 0 8px; font-size:1.35rem }
.controls { display:flex; gap:10px; align-items:center; flex-wrap:wrap }
input, select { background:#27313d; border:1px solid #6d7886; border-radius:6px; color:#fff; padding:8px; font:inherit }
input { min-width:230px; flex:1; max-width:500px }
main { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:18px; padding:20px clamp(16px,3vw,40px) }
.card { background:#202834; border:1px solid #455161; border-radius:10px; overflow:hidden }
.card header { padding:12px 14px }
h2 { margin:0; font-size:1.08rem }
small { color:#b7c1ca }
.tags { display:flex; flex-wrap:wrap; gap:5px; margin-top:8px }
.tags span { font-size:.72rem; background:#3b4856; border-radius:4px; padding:2px 6px }
.images { display:grid; grid-template-columns:1fr 1fr; gap:3px; background:#111821 }
figure { margin:0; min-width:0; position:relative; aspect-ratio:9/16; background:#111821 }
figure a { display:block; width:100%; height:100% }
figure img { width:100%; height:100%; object-fit:contain; display:block }
figcaption { position:absolute; left:0; bottom:0; background:#111b; padding:3px 8px; font-size:.75rem }
.missing { height:100%; display:grid; place-items:center; color:#9babb9; text-align:center; padding:10px; box-sizing:border-box }
.card[hidden] { display:none }
</style>
</head>
<body>
<div class="top"><h1>Painted cover study</h1><div class="controls">
<input id="search" type="search" placeholder="Search title or slug" aria-label="Search title or slug">
<select id="status" aria-label="Filter by status"><option value="all">All covers</option><option value="restyle">Restyle</option><option value="skip_already_painted">Already painted</option></select>
<select id="detail" aria-label="Filter by detail"><option value="all">All detail levels</option><option value="fine_detail">Fine-detail source</option><option value="broad_shape">Broad-shape source</option></select>
<select id="canon" aria-label="Filter by canon"><option value="all">All canon states</option><option value="true">Canon locked</option><option value="false">Non-canon</option></select>
<span id="count"></span></div></div>
<main>
""" + cards + """
</main>
<script>
const cards=[...document.querySelectorAll('.card')];
const search=document.getElementById('search'),status=document.getElementById('status'),detail=document.getElementById('detail'),canon=document.getElementById('canon'),count=document.getElementById('count');
function filter(){const q=search.value.toLowerCase().trim(); let n=0; for(const card of cards){const show=(status.value==='all'||card.dataset.status===status.value)&&(detail.value==='all'||card.dataset.detail===detail.value)&&(canon.value==='all'||card.dataset.canon===canon.value)&&card.dataset.search.includes(q);card.hidden=!show;if(show)n++;}count.textContent=n+' shown';}
search.addEventListener('input',filter);status.addEventListener('change',filter);detail.addEventListener('change',filter);canon.addEventListener('change',filter);filter();
</script>
</body></html>
"""
    OUTPUT.write_text(document, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
