# Painted cover style study

## Scope and source

The source inventory is in [manifest.json](manifest.json). It records the 200 existing `title-image.jpg` covers, their story titles and authoritative canon markers, image dimensions and byte sizes, and proposed study candidate paths. All source covers are JPEG files measuring 864 × 1536 pixels. The existing covers total 106,657,984 bytes.

The 200 covers comprise 166 non-canon and 34 canon story packages. Canon packages remain locked. Candidate paths are under this study directory, outside every story package; creating a candidate there does not approve its use as a story cover.

## Style references

The current cover direction in [story-create](../../.agents/skills/story-create/SKILL.md) calls for a Group of Seven inspired oil painting. Pixel references inspected for this triage were `stories/the-fox-that-stood-up/title-image.jpg`, `stories/onyx-peace/title-image.jpg`, `stories/spirit-heart/title-image.jpg`, and `stories/the-sun-in-the-crowd/art/landscapes/night-market-portrait-stall.png`. The shared traits are conspicuous short brush or scraped strokes, broad color masses, dramatic light, and warm/cool contrast. Palettes and subject treatments vary.

## Study method

The triage inspected ten contact sheets covering all 200 source covers and opened borderline images individually at full cover size. Each manifest entry now has `style_status`, `style_reason`, `style_confidence`, and `detail_class`. `skip_already_painted` requires visible painted marks shaping the main forms; a textured background, recent date, or generally painterly mood alone is insufficient. `fine_detail` flags a restyle whose many small objects, intricate surfaces, crowd, or busy setting needs a composition review before heavy impasto. `broad_shape` means the main visual idea is already readable in larger forms. These are visual study labels, not approvals to replace covers.

Candidate production uses three non-overlapping slug batches in [batch_assignments.json](batch_assignments.json), with an exact prompt and inspection note for each image under `prompts/`. Each built-in image-generation call uses the source cover as its content guide and the recent art only for paint handling. Outputs are converted to 864 × 1536 JPEG and kept under this study directory. [style-brief.md](style-brief.md) records the visual rule established through user feedback. [gallery.html](gallery.html) compares each source with its selected candidate; run `python build_gallery.py` to refresh it as candidates arrive. Original covers remain unchanged.

## Findings

Visual triage marks **7 covers to skip** and **193 for restyling**. The skip list is `onyx-peace`, `spirit-heart`, `the-closed-day`, `the-first-winter`, `the-fox-that-stood-up`, `the-place-laid-for-her`, and `the-sun-in-the-crowd`. Of the restyles, 51 are flagged `fine_detail` (47 non-canon, 4 canon) and 142 `broad_shape`. All 34 canon packages are among the restyles; their study candidates can be kept outside the locked packages, but none may be installed there without the named-story unlock required by `AGENTS.md`.

The medium-confidence cases are `the-first-winter` (skip: blocky strokes and broad warm/cool masses, though the face is smooth) and these restyles: `a-busy-year-for-dying`, `a-place-for-sunday`, `after-the-party`, `every-flower-she-knew`, `no-need-to-worry`, `only-eighteen`, `the-credit-book`, `the-unfixed-song`, `the-unoffered-hand`, and `what-the-wind-wanted`. They have some painted or textured treatment, but their main forms read as smooth, finely rendered, or drawn compared with the references. Recheck them when representative candidates are compared.

The first `All Accounts Due` candidate retained too much miniature hardware under heavy brush texture; the second reduced it to nearly flat sectors. The user accepted [v3](candidates/all-accounts-due/painted-v3.jpg) as the detail benchmark: six differentiated chambers and a pointer remain legible against broad painted surroundings. This is the batch target, with subject-specific treatment rather than one fixed palette or composition. Fine-detail covers still need special scrutiny so they do not become texture passes over crowded scenes.

An independent visual audit compared 183 available selected candidates with their originals in 21 contact sheets and opened the densest examples at full size. It found no severe title, subject, or detail-balance error requiring regeneration. `The Rule Between Courses` and `The Thread That Held` remain visually busy because the dinner and tapestry carry story detail; they merit individual comparison even though their focal hierarchy reads. The remaining candidates were generated after this audit and receive their own saved-pixel check in the prompt logs.

The completed manifest selects **193 candidates**. Seven are marked for closer individual review: `apes-in-orbit`, `storm-warning`, `the-gentlest-terror`, `the-house-beneath-the-horns`, `the-rule-between-courses`, `the-weight-of-falling-up-rune-shoes`, and `what-she-remembered-of-peace`. These are usable study images, not automatic cover replacements. The late-batch thumbnail sheet was also reviewed after production.

The final file check found 200 sources, 7 skips, 193 present candidates, 0 missing, and 0 invalid. It verifies that each selected output is a readable 864 × 1536 JPEG within this study directory and differs byte-for-byte from its source. The selected candidates total 133,345,876 bytes. Prompt logs retain each built-in generation instruction and the per-cover inspection notes.

## Recommendation

Use the side-by-side gallery to choose covers individually. The approved `All Accounts Due` v3 gives a workable collection direction: recognizable focal detail, large painted light and color masses, and quieter secondary forms. It is a guide to judgment rather than a template to stamp across every story. The source identity, title, and anatomy still need a last cover-size read before any candidate replaces an existing cover.

The first pass should be a selection study, not a collection-wide swap. Keep the seven already painted covers. Give the `fine_detail` group priority in review, especially the covers marked `review_needed` or `candidate_review` in the manifest. `A Crown in the Bargain` and `Solstice Evening Bell` have second candidates because their first passes introduced an unrelated landscape and retained excessive small texture, respectively; the manifest selects their repaired versions. `The Apes Above` is a fresh composition, with somewhat fine foreground armor still worth comparing against the source. The title-specific choices belong to the user and the story editor.

All 34 canon story packages are locked. Their candidates may be compared here, but adopting one would require the explicit named-story unlock and separate commit described in `AGENTS.md`. Nothing in this study changes those packages or the original cover files.
