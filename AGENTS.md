# Story Computing Machine

This repository is a shared-universe fiction workspace. The prose and the
universe notes are the product; process records are not.

## Two story layouts

A completed current story has four authored Markdown files and one generated
title image:

- `prompt.md` — the verbatim original request, its few explicit constraints,
  and a display-name inventory of supplied reference images. An explicitly
  authorized rewrite adds the latest verbatim rewrite request, its reference
  display names, and cover policy to this same file.
- `outline.md` — the draftable narrative shape, proposed people and places, and
  relevant continuity boundaries.
- `story.md` — the reader-facing prose and its minimal metadata.
- `review.md` — the final people/place inventory and continuity verdict.
- `title-image.jpg` — the final-story 9:16 portrait visual; never canon authority.

The cover displays the exact reader-facing story title once. It has no author
name, caption, logo, border, watermark, or other text.

The scaffold contains only the four Markdown files until the story passes
review. No other files belong in a current story directory.

Reference images supplied with a prompt remain external workflow inputs; never
copy them into the story directory or treat them as canon. Record only their
display names in `prompt.md`, resolve and visually inspect every original, and
pass the originals to both the outliner and title-image illustrator. The written
prompt and universe authority control any conflict during outlining; the final
prose controls story facts during cover generation unless the prompt explicitly
makes an image detail binding.

Any existing story directory containing `05-story.md` is a locked legacy
bundle. Do not edit, migrate, validate, or regenerate its bundle files. Its
extra files are historical residue from the retired pipeline. The title-image
workflow may add or replace only `title-image.jpg` beside a legacy bundle;
that asset does not alter or reopen the bundle. Only the explicit Pages capture
command understands the legacy layout; normal story validation does not.

## Authority

- `universe/` is authoritative for shared facts. Read `universe/README.md`
  before interpreting canon.
- `universe/style-guide.md` is the binding narrative policy. Current scaffolds
  apply its prospective craft profile through the outline, writer, and reviewer
  skills; the profile alone never reopens a completed story. Only the explicit
  rewrite workflow may reopen a named non-canon current story. Locked legacy
  bundles remain closed.
- `stories/NAMES.md` is the frozen name baseline for legacy stories, not canon.
- Current `review.md` files extend production memory for new people and places.
- Plans, reviews, prompts, source notes, and non-canon stories never establish
  shared-universe facts.

## Branches

Before starting any new story or rewrite, make branch setup the first repository
action:

1. Switch to `main`.
2. Pull the latest changes from `origin/main` with a fast-forward-only pull.
3. Create a new `codex/story-<slug>` branch for a new story or
   `codex/rewrite-<slug>` for a rewrite from the updated `main`, without
   switching the primary checkout away from `main`.
4. Add a dedicated sibling Git worktree for that branch, then use the worktree
   as the working directory for the coordinator and every delegated agent for
   the rest of the story workflow.

Do not scaffold, prepare a rewrite, read for story production, or modify story
files until this sequence is complete. Resolve and retain the worktree's absolute path before
delegating, and include that path in every agent assignment so no story work
lands in the primary checkout. Run all validation, capture, Git, push, and pull
request commands from the worktree. If local changes prevent switching the
primary checkout to `main` safely, or if the intended worktree path is already
occupied, stop and ask the user how to preserve or reuse it. Never change
`stories/` or `universe/` in the primary `main` checkout; merge the story branch
through a pull request. Git is the history; do not create manifests, ledgers,
receipts, release certificates, or duplicate lifecycle records.

## `[WP]` workflow

Use the `story-room` skill for a prompt tagged `[WP]` unless the user requests
one named stage.

1. Before scaffolding, identify and visually inspect every reference image
   attached to the request. Scaffold the four files with `new-story.ps1`,
   preserve the prompt, and pass the reference image paths or attachment labels
   so `prompt.md` inventories their display names. If none were supplied,
   record that explicitly. Keep the original images outside the story directory.
2. Delegate `outline.md` to a fresh `story_outliner`. It reads the universe
   README and
   style guide, searches only relevant authority and noun history, skims the
   design sections of up to five recent passing current outlines, and proposes
   a story-specific generating force and narrative shape plus people and places
   as `new` or `recurring`. Recent outlines are comparison context only, never
   canon or models to imitate. For `prospective-2026-08-21`, target 700–1,000
   words and never exceed 1,200. It completes the required story-specific Voice
   capsule without opening prior Voice sections or prose. Record pressure and
   choices, not drafted
   confessions, reconciliations, speeches, or final thematic lines. Include
   every supplied reference image in the assignment with a resolvable path or
   unambiguous attachment identifier and its intended role when the prompt
   states one. The outliner must inspect all of them and use their relevant
   visual evidence without turning unrequested details into canon. If an image
   cannot be accessed, restore access or ask the user to attach it again rather
   than silently omitting it.
3. Delegate `story.md` to a fresh `story_writer`. It uses the project-owned
   `short-story-writing` production adapter. `creative-writing-craft` remains
   primary; `dialogue` and `prose-style` are diagnostic references only during
   in-place revision. It writes the complete story directly and revises it at
   whole-story, movement/information, dialogue-scene, and language/sound scales.
   Installed skills are internal references: their optional scripts, reports,
   and persistence files are forbidden. This remains one prose assignment;
   there is no separate draft, craft report, or final-edit artifact.
4. Run `Test-Stories.ps1 -Story <slug> -Phase PreReview` once. Pass its concise
   result to the reviewer without creating another file.
5. Delegate one fresh independent review to `story_reviewer`. It writes only
   `review.md`. It reads prompt and story first, forms a provisional
   reader-facing and dialogue judgment before opening the outline, inventories
   every story-facing person and place noun, and checks prompt fulfillment,
   universe continuity, chronology, causality, and internal facts. It uses
   `story-analysis` and `dialogue` as its default craft lenses, with
   `story-sense`, `prose-style`, and `sensitivity-check` only when their specific
   diagnostic scope is material. These skills create no separate artifacts.
   The prompt is authoritative; the outline is advisory.
6. If the verdict is `REVISE`, the story's writer may handle only blocking fixes,
   allowing the smallest necessary surrounding action or narration for a
   dialogue repair. Repeat the pre-review check and use a fresh reviewer agent
   for every subsequent review.
   Ask the user only when a canon ruling, retcon, or material prompt
   reinterpretation is required.
7. After `PASS`, delegate `title-image.jpg` to `story_title_illustrator`. It
   reads the complete final prose and writes only the spoiler-light 9:16 title
   visual. Unless the prompt says otherwise, use the repository's premium
   anime/light-novel key-visual default defined in that agent.
   Include every reference image supplied with the original prompt in the
   assignment and in the image-generation call. Use resolved local paths when
   all originals have them; otherwise include the smallest recent-attachment
   set that contains them all. The illustrator must inspect every reference
   before composing, use it for the visual role implied by the request, and
   preserve recognizable reference traits that do not conflict with the final
   prose. If not all references can be provided to image generation, ask the
   user to attach the missing images again rather than generating without them.
   After the JPEG is saved, both the illustrator and coordinator must open that
   exact file with the available image-viewing tool. Image-generation output,
   prompt text, file metadata, and the illustrator's written report are not
   substitutes for seeing the saved pixels. Inspect the whole composition at
   reduced cover size and inspect full-resolution details; when a hand, face,
   object connection, title letter, or spatial relation remains doubtful, use
   additional visual crops or views before deciding. Temporary review images
   must stay outside the story directory and must not be committed.
   The illustrator and coordinator must each judge the actual saved image at
   cover-card size and full resolution through six separate gates. A pass must
   name visible evidence for every gate; repeating the prompt or the
   illustrator's self-report is not review:
   - **Story promise** — the image foregrounds the story's distinctive emotional
     or narrative contradiction, could not be mistaken for a generic genre
     cover, preserves character roles and relationships, and does not imply a
      resolution the prose has not earned.
   - **Scene truth** — every depicted action, position, direction of travel,
     spatial constraint, possession, support, and cause-and-effect relation
     needed to read the chosen moment agrees with the prose. Openings, rooms,
     vehicles, restraints, tools, and other affordances have plausible scale
     and geometry. An attractive approximation fails when it changes how the
     scene works or makes the decisive action physically ambiguous.
   - **Role legibility** — story-important figures are distinguishable by
     silhouette, face, clothing, posture, and placement; the viewer can tell who
     is doing what, who holds power, and which objects belong to whom without a
     prose explanation. Near-duplicate faces, ambiguous grouping, or static
     poses that erase opposing choices fail.
   - **Cover read** — at thumbnail scale the exact title is readable once, the
     focal hierarchy is immediate, and the important figures, relationships,
     and story-specific objects remain legible rather than collapsing into a
     crowded tableau.
   - **Image integrity** — at full resolution anatomy and object counts are
     plausible, hands and faces withstand close inspection, perspective and
      physical connections are coherent, and there is no unintended text,
      pseudo-text, watermark, or visual artifact.
   - **Production finish** — the image has intentional lighting, color
     separation, edge treatment, and typography rather than muddy values,
     overprocessed texture, illegible letterforms, accidental tangencies,
     generic decoration, or inconsistent rendering. The exact title remains
     undamaged inside the safe crop and the JPEG shows no visible scaling or
     compression defects.
   The coordinator must compare the actual saved image against the prompt and
   final prose and make an independent decision; the illustrator's self-report
   and the technical validator are not acceptance. If a required action, role,
   object connection, or spatial fact is ambiguous, treat it as failed rather
   than resolving it charitably
   from the prose. Technical polish cannot compensate for a generic or
   off-promise concept. When a gate fails, delegate a concise regeneration brief
   that says what to preserve, names the blocking miss, directs the composition
   or focal change, and restates the invariants. Require a new composition for a
   story-promise failure and a targeted correction for a localized integrity
   failure. Repeat review until all six gates pass, and do not capture a
   rejected image.
8. Run `Test-Stories.ps1 -Phase Final` locally, capture the story with
   `python pages/build.py capture <slug>` once, and run
   `python pages/build.py check`. Stage the story's four Markdown files together
   with `title-image.jpg`, `pages/catalog.json`, and the captured
   `pages/covers/<slug>.jpg`; commit them, push the current story branch to
   `origin` with upstream tracking, and open a draft pull request against the
   repository's default branch. Capture is the final prose-and-cover handoff.

Do not create a canon brief, authority snapshot, draft copy, canon delta,
handoff guard, release record, promotion record, story README, or index row.

For `prospective-2026-08-21`, `outline.md` contains exactly one `## Voice`
section of at most 180 words with these completed fields:

- `Narrative texture` — how this story's narration moves, notices, selects, and
  sounds;
- `Conversational texture` — the range, rhythm, and ordinary texture of talk;
- `Rhetorical ownership` — which forms of thought, metaphor, precision, or
  argument belong to which speakers;
- `Pressure behavior` — what stress does to fluency, listening, evasion,
  repetition, silence, or directness; and
- `Anti-default` — the plausible default that would make this particular story
  sound interchangeable.

Every field must be actionable and story-specific. The three dialogue-specific
fields may be `N/A — no meaningful dialogue expected`; Narrative texture and
Anti-default remain required. Do not include sample lines, catchphrases,
phonetic accents, or
boilerplate such as merely `avoid house style`. The Voice section does not
increase the 1,200-word outline ceiling. Recent-outline comparison is limited
to each prior outline's `## Story` section; no prior Voice capsule or prose may
be exposed to the writer.

## Rewrite workflow

Use `story-room` REWRITE mode only when the user explicitly requests a rewrite
of one named completed current story. REWRITE means a new whole-story prose pass;
REVISE remains the narrow correction loop for blocking review findings. Reject
directories containing `05-story.md`. Reject `canon: true` unless the user first
requests and resolves a separate canon or retcon decision.

1. Complete the branch sequence above with `codex/rewrite-<slug>` and a sibling
   worktree. In the worktree, use only `prompt.md` and package metadata to
   prepare the reset; the preparation script may verify the prior PASS and
   frontmatter, but the prior outline, prose, and review are not creative
   inputs. Inspect the saved cover only when AUTO or KEEP makes it a candidate.
   Resolve and visually inspect every original and newly supplied reference
   image. Restore access or ask the user to attach it again if an original
   cannot be resolved.
2. Run
   `prepare-rewrite.ps1 -Story <slug> -Title <fresh-title> -Request <verbatim-request>`,
   passing each new image through `-ReferenceImage` and one cover policy:
   - `-Cover Auto` retains an unchanged-title cover for a fresh post-rewrite
     comparison, removes a changed-title cover, and generates a new one only
     when no valid reusable candidate remains;
   - `-Cover Keep` requires an unchanged title, forbids automatic generation,
      and can complete only if the retained image passes against the rewritten
      story;
   - `-Cover Regenerate` removes the retained image after the Markdown reset
     succeeds and requires a fresh one after prose review.
   The script preflights the linked worktree, target cleanliness, prior PASS,
   canon status, templates, title, cover policy, prompt structure, and every
   candidate file before changing tracked content. It rejects control characters
   in titles, stages candidates outside the repository, replaces the package in
   one guarded operation, and restores the original Markdown and cover bytes if
   any replacement fails.
   Preparation preserves the original prompt byte-for-byte outside the managed
   rewrite sections and preserves immutable package identity. It records the
   amended request, active `prospective-2026-08-21` profile, and cover choice in
   `prompt.md`, then resets
   `outline.md`, `story.md`, and `review.md` to clean scaffolds. It creates no
   rewrite brief, backup prose, alternate outline, or other artifact.
3. The original prompt plus the latest rewrite request form the acceptance
   authority. The latest request controls conflicts; unaffected original terms
   remain binding; the latest craft profile in Rewrite constraints controls
   production craft. Delegate fresh agents for the ordinary OUTLINE assignment,
   followed by the ordinary WRITE assignment. These are the same production
   stages and local adapter used by CREATE. Do not load the prior outline,
   prose, or review
   from Git. If the user explicitly asks to retain a named element, retrieve
   only the minimum old material required for that element and pass it to the
   relevant agent.
4. Run PreReview and request one fresh independent reviewer agent. The previous
   PASS is
   history, not evidence. Resolve a REVISE verdict through only its blocking
   findings, then rerun PreReview and request another fresh reviewer.
5. After PASS, apply the recorded cover policy. For AUTO or KEEP with a retained
   candidate, the coordinator
   must open the retained JPEG at cover-card size and full resolution and judge
   all six gates against the amended prompt and final rewrite. AUTO regenerates
   on any failure. KEEP stops for user direction on any failure. REGENERATE uses
   the normal illustrator workflow. Any generated replacement follows all
   reference-image, saved-pixel inspection, and six-gate requirements above.
   Cover generation is optional when a reusable candidate passes, but a valid
   final cover remains mandatory for completion.
6. Run final validation, recapture the story, and run the catalog check. Stage
   the four Markdown files, the title image only when changed, catalog, and
   captured cover; commit, push, and open the normal draft pull request. Git
   preserves the prior version, so do not add backup or rewrite-history files.

## People and places

The outline proposes nouns and labels them `new` or `recurring`. The pre-review
check catches exact declared collisions. The review inventories the final prose
and owns exhaustive extraction, aliases, close spellings, and semantic
confusion checks. For every story-facing proper noun that names a person,
person-like being, or place:

- label it `new` or `recurring` in the review;
- search `stories/NAMES.md`, current `review.md` files, and the relevant
  `universe/characters.md` or `universe/locations.md` entries;
- avoid accidental exact, alias, close-spelling, and easily confused reuse;
- explain intentional recurrence briefly; and
- use a single `None` row when the story has no named noun of that kind.

`PreReview` validates the scaffold, usable prompt/outline/story, exact outline
declarations, and the new profile's 1,200-word outline ceiling. Run final
validation locally with `-Phase Final` after review to validate the structure, exact
inventory, continuity verdict, and required dialogue verdict. Neither mode
substitutes for the reviewer's semantic judgment.

## Review and continuity

A `PASS` review requires all three continuity lines to pass:

- `Prompt` — the story fulfills the request and resolves its central promise.
- `Universe` — people, places, chronology, capabilities, and facts do not
  contradict current `LOCKED` or `CANON` notes.
- `Internal` — the story is causally coherent and keeps its own facts straight.

The prompt is the only acceptance authority. For a prepared rewrite, the
original prompt and latest `## Rewrite request` are one amended prompt: the
latest request controls conflicts and unaffected original terms remain binding.
The reviewer may use the outline to understand design intent, but deviation
from it is not blocking unless the result breaks the amended prompt, universe
continuity, or internal coherence.

For prompts carrying `Craft profile: prospective-2026-08-08`, the reviewer also
checks material compliance with the binding story craft defaults. Craft is
blocking only when it breaks the prompt's central promise, reader-facing
causality, or binding narrative policy. Do not copy the writer's in-place
revision criteria into `review.md`, and do not apply them retroactively to
existing stories.

For prompts carrying `Craft profile: prospective-2026-08-18`, the reviewer
applies those defaults and records exactly one dialogue line under `## Craft`:
`- Dialogue: PASS`, `- Dialogue: REVISE`, or `- Dialogue: N/A`. N/A means the
story has essentially no meaningful dialogue, not merely that it is
dialogue-light. The reviewer scans every dialogue scene and closely examines
the decisive and final meaningful exchanges, including their adjacent action
and narration. Outline compliance is not evidence that dialogue works. A
material reader-facing dialogue defect is independently blocking;
Dialogue REVISE requires an overall REVISE and one concise targeted finding
supported by no more than three short examples.

`Craft profile: prospective-2026-08-21` extends the 08-18 contract without
changing any completed 08-18 story. It keeps the same single Dialogue verdict.
The reviewer forms a provisional dialogue judgment before opening the outline,
then treats the Voice capsule as intent rather than evidence. In addition to
the 08-18 checks, examine context dependence and quote-card neatness,
rhetorical ownership, reasoning-shape diversity, secondary-character chorus,
unequal fluency under pressure, ordinary or single-purpose speech, and
over-explanation in the final exchange. One earned aphorism or articulate
exchange is acceptable. Only material scene-wide convergence is blocking, and
any such failure feeds `Dialogue: REVISE` rather than a new review field.

Review prose concisely. Record only blocking findings and short useful notes;
do not preserve reviewer chain-of-thought, repeated summaries, or audit logs.

## Canon

New stories begin with `canon: false`. Canon promotion requires explicit user
approval for one named story, a fresh passing review against current authority,
and direct edits to the smallest relevant `universe/*.md` entries. Then set
`canon: true` in `story.md`. A conflict with `LOCKED` canon stops for a user
ruling. Git records the transaction; no separate delta or promotion file is
needed.

## Pages

`pages/catalog.json` and `pages/covers/` form the stored publication snapshot.
GitHub Pages builds and publishes only that snapshot; it never traverses
`stories/` or runs story validation. The `capture` command requires a passing
review and copies one completed story and its title image into the snapshot
without rerunning full validation. Keep the catalog ordered by full creation
timestamp, newest to oldest, so the newest story is always the first card on the
GitHub Pages index. New scaffolds record `created-at`; when a source has only a
`created` date, capture combines that date with the story prose file's filesystem
modification time. `capture-all` exists only for an intentional full refresh,
not for CI.

## Completion

A new or rewritten current story is complete when its four Markdown files and 9:16 portrait
`title-image.jpg` exist, `review.md` says `PASS`, people and places are
inventoried, all three continuity lines pass, and the story plus image have
been completed in the story directory and captured into `pages/catalog.json`
and `pages/covers/`. Repository acceptance also requires the local final
validator and catalog check to pass, the completed changes to be committed and
pushed on its story or rewrite branch, and a draft pull request to be open against the
repository's default branch.
