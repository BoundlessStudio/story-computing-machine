# Graphic novels — draft v0.5

This is a draft agent workflow and house style for adapting finished stories
into PDF graphic novels. The agent entry points and production instructions are
supplied; this draft does not implement a comic CLI, automated lifecycle validator
or publication integration.

## Start from a finished story

```text
[GN] "Exact Story Title"
[GN] "story-slug" — use the existing illustrated edition as visual references
```

`[GN]` is the sole new trigger. It takes a repository story
title or slug, just like `[IL]`. It adapts that story into sequential panels
and dialogue. `[IL]` continues to preserve the complete prose in an illustrated
edition. `[Comic]` remains reserved and does not route here. Starting from a new
writing prompt is outside this first version. The `[IL]` contract, agents, tools,
artifacts and publication behavior are unchanged.

While this contract is marked **draft**, a trigger prepares the adaptation and
reference proposal for review; it does not start image generation. Approval of
that concrete plan may explicitly authorize trying this draft workflow for the
named edition. A general discussion of the workflow is not that authorization.

## Proposed experience

1. Read the story and inspect its cover, original references and any existing
   illustrated edition. Propose which actual images should guide the adaptation.
2. Write a page and panel script, reference plan and story-specific art direction.
   Show the exact page/reference counts and intended omissions or condensations.
   Obtain independent plan review, then the user's plan approval.
3. Reuse suitable references and create missing ones individually. Establish
   characters first, then places and objects using the written bold, flat-color
   comic style in STYLE.md. Existing IL art guides identity/content;
   create GN versions when its rendering differs. Keep IL originals unchanged.
4. Generate page 1, inspect it at reading size, correct it, and obtain independent
   page review. Only a passing page permits work on the next page.
5. Continue in order, with the same review loop for every complete page.
6. Use the PDF skill to assemble the selected cover followed by all comic-page
   images in order into edition.pdf, one image per PDF page. Preserve complete
   images and their aspect ratios without cropping or stretching; verify no
   image is omitted or duplicated. Render and inspect every PDF page at full
   and reading sizes. A fresh reviewer checks the entire PDF independently for
   story coverage, pacing, continuity, visual consistency and readable lettering.
   Repair and recheck.
7. Present the complete PDF for the user's final approval, bound to its actual hash.

Intermediate art and page reviews are assistant work. The default does not ask
the user to approve every image; an explicit request for additional checkpoints
takes precedence. PDF is the required final GN output. Reference sheets remain
production assets unless an appendix is expressly requested. Exact panel
transcripts stay in plan.md. An HTML preview is optional temporary production
material outside the package; it is not the final book. This workflow has no
website publication step and does not replace an existing reader.

## Draft choices to review

| Choice | Proposed default |
| --- | --- |
| Entry | `[GN] "Story Name"` only |
| Adaptation | Preserve events, character intent and ending; condense prose into panels and short dialogue |
| Art | STYLE.md: crisp black contours, flat saturated fills and hard-edged shadows |
| Visual anchors | Written house style plus accepted edition-specific sheets; compatible same-story art guides identity, costume and setting |
| Page | Portrait 2:3, left-to-right; no preferred panel count |
| Panel interaction | Clear borders/gutters and visual flow; purposeful insets, overlaps, frame breaks and transitions |
| Color | Strong flat color, near-white gutters/balloons and yellow narration; scene palette follows the story |
| Lettering | Bold condensed uppercase captions/dialogue, checked word-for-word against the script/transcript |
| Production | One complete page at a time; fix and pass before proceeding |
| Final output | edition.pdf: selected cover, then all ordered comic-page images, one image per PDF page |
| User checkpoints | Plan, then independently reviewed complete PDF bound to its hash |

Read the [written style draft](STYLE.md) or inspect the
[production contract](../.agents/skills/graphic-novel-create/SKILL.md).
There is no visual style preview. The supplied image is retained as provenance
for the text rules, not a compulsory generation input or fixed layout. Its
characters, objects and plot are not part of another story. Actual generated
references and pages still receive visual review. The style decision does not
approve generation or settle the still-proposed user review checkpoints.

Agent definitions: [creator](../.codex/agents/graphic-novel-creator.toml) and
[independent reviewer](../.codex/agents/graphic-novel-reviewer.toml).
