# Illustrated edition tooling

Start with `[Illustrate] "Story Name"` or `[IL] "Story Name"` in Codex. Both
route to the same [production contract](../.agents/skills/illustrated-create/SKILL.md).
Use `deluxe` or `cinematic` after the title to change presentation; otherwise
Classic applies. [House rules](STYLE.md) define the shared typography/layout.

Source stories remain unchanged. Editions are separate derivative packages,
including when their source is canon. Do not create a package until the source
and dedicated worktree are resolved. Generation and approval are agent-driven;
the website is the published reader, not an editor.

## Install

From the dedicated worktree, use an isolated Python environment and the pinned
browser dependency. Node.js and Python must be available on PATH.

```powershell
python -m venv --system-site-packages illustrated/.venv
illustrated/.venv/Scripts/python -m pip install -r illustrated/requirements.txt
npm ci --prefix illustrated
npm run install-browser --prefix illustrated
```

On macOS/Linux the Python executable is `illustrated/.venv/bin/python`.
Use that environment for the following Python commands (or activate it first).
The fonts are bundled locally with their licenses, so rendering works offline.
The exporter uses pinned Playwright Chromium; a system browser is not substituted.

Real image generation additionally requires `OPENAI_API_KEY` set locally, model
access, and the installed imagegen skill's unchanged `scripts/image_gen.py`.
The default model is `gpt-image-2.5-sunburst-2026-09-08`, quality high. Do not put
keys in the repository or chat. `generate --dry-run` validates without a paid
request. Installation makes no paid image requests.

## Lifecycle and layout

Run commands only inside the edition's worktree. Multiline requests, prompts,
evidence, and actual user approval responses go in temporary UTF-8 input files.

```powershell
python -m illustrated.edition new "Story Title" --request-file tmp/request.md
python -m illustrated.edition validate edition-slug --phase draft
python -m pages.illustrated_editions anchors edition-slug
python -m illustrated.edition --help
```

The planner fills plan.md and registers reference/scene assets using
`set-asset`. Each scene names an `after` anchor returned by `anchors`; IDs include
position and content so repeated paragraphs remain distinguishable and changed
source cannot silently reuse placements. Parse the complete Markdown; never
render individual prose fragments to insert images.

After plan approval and accepted reference sheets:

```powershell
python -m pages.illustrated_editions layout-sample edition-slug --output tmp/layout-sample
python -m illustrated.edition layout-preview edition-slug tmp/layout-sample/index.html --evidence-file tmp/layout-evidence.md
python -m illustrated.edition approve edition-slug visuals --decision-file tmp/user-approval.md
```

Show and inspect the reference sheets, reused/requested cover, and sample before
recording the actual user decision. Scene generation is blocked until that step.
The allowance is one initial call plus two automatic corrections per stable
asset ID. Renaming a file or restarting the agent does not reset it. Additional
attempts need explicit user direction, recorded with `extra-attempt`.

After every scene is accepted:

```powershell
python -m pages.illustrated_editions render edition-slug
python -m pages.illustrated_editions preview edition-slug --output tmp/edition-preview
python -m illustrated.edition record-review edition-slug --reviewer independent-agent-id --evidence-file tmp/review-evidence.md
python -m illustrated.edition approve edition-slug final --decision-file tmp/user-final.md
python pages/build.py capture-illustrated edition-slug
python pages/build.py check
python pages/build.py build --output _site
```

Rendering creates the digital 6×9-inch edition.pdf. Inspect the HTML at mobile
and desktop widths, render the PDF into page images with Poppler, and inspect
every page before independent review/final approval. Temporary previews are not
publication. The original must already be published, with reconciled canon
markers, before capturing its edition. Commit, push, and open a draft PR.

Source changes pause production. Explicit source repinning is a user version
decision and invalidates dependent approvals/assets while retaining attempts.
Existing published editions remain frozen until named recapture. A second
edition of a story needs another slug; no implicit overwrite is permitted.
