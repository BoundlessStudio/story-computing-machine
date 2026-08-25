# Story Computing Machine

This repository is a shared-universe fiction workspace. The prose and the
universe notes are the product; process records are not.

## Two story layouts

A completed current story has four authored Markdown files and one generated
title image:

- `prompt.md` — the verbatim request, its few explicit constraints, and a
  display-name inventory of supplied reference images. A replacement flattens
  every prior user-authored prompt or request block plus the new request
  verbatim into a clean Prompt section and inventories every associated
  reference display name; machine selection, cover-policy, and workflow
  metadata do not survive.
- `outline.md` — the draftable narrative shape, proposed people and places, and
  relevant continuity boundaries.
- `story.md` — the reader-facing prose and its minimal metadata.
- `review.md` — the final people/place inventory and continuity verdict.
- `title-image.jpg` — the final-story 9:16 portrait visual; never canon authority.

The cover displays the exact reader-facing story title once. It has no author
name, caption, logo, border, watermark, or other text. It is editorial packaging
for a work of fiction, not an interior illustration, film poster, ensemble key
visual, or visual synopsis. It should withhold most plot information and turn
one story-specific contradiction, motif, figure, object, or threshold into an
immediate invitation to read.

The scaffold contains only the four Markdown files until the story passes
review. No other files belong in a current story directory.

Reference images supplied with a prompt remain external workflow inputs; never
copy them into the story directory or treat them as canon. Record only their
display names in `prompt.md`, resolve and visually inspect every original, and
pass the originals to both the outliner and title-image illustrator. The written
prompt and universe authority control any conflict during outlining; the final
prose controls story facts during cover generation unless the prompt explicitly
makes an image detail binding.

An existing story directory containing `05-story.md` uses the supported bundle
format. Canon state alone controls editability in both layouts: `story.md`
frontmatter is authoritative for a current-format story, and `story.json` is
authoritative for a bundle-format story. A `canon: false` story may receive an
explicitly requested localized edit or named replacement, while `canon: true`
locks every file in the story package against direct human or AI edits. An
agent may unlock it only through the separate, explicit canon-state action
defined below. Extra bundle files are historical residue from the retired
pipeline, not lifecycle authority. The title-image workflow may add or replace
`title-image.jpg` beside a non-canon bundle without reopening the prose. Pages
capture supports both story layouts; current-format validation does not inspect
bundle-format prose.

## Authority

- `universe/` is authoritative for shared facts. Read `universe/README.md`
  before interpreting canon.
- `universe/style-guide.md` is the binding narrative policy. Current scaffolds
  apply its prospective craft profile through the outline, writer, and reviewer
  skills; the profile alone never reopens a completed story. A completed
  non-canon story changes only through an explicitly named localized edit or
  the remove-then-create replacement workflow. The authoritative canon flag,
  rather than age, layout, status, editor identity, or process metadata,
  controls whether work may begin.
- `stories/NAMES.md` is the frozen name baseline from earlier production, not canon.
- Current `review.md` files extend production memory for new people and places.
- Plans, reviews, prompts, source notes, and non-canon stories never establish
  shared-universe facts.

## Branches

Before starting any new story, replacement, or AI-performed story edit, make
branch setup the first repository action:

1. Switch to `main`.
2. Pull the latest changes from `origin/main` with a fast-forward-only pull.
3. Create a new `codex/story-<slug>` branch from the updated `main`, without
   switching the primary checkout away from `main`.
4. Add a dedicated sibling Git worktree for that branch, then use the worktree
   as the working directory for the coordinator and every delegated agent for
   the rest of the story workflow.

Do not scaffold, inspect a replacement or edit source for production, or modify
story files until this sequence is complete. Resolve and retain the worktree's absolute path before
delegating, and include that path in every agent assignment so no story work
lands in the primary checkout. Run all validation, capture, Git, push, and pull
request commands from the worktree. If local changes prevent switching the
primary checkout to `main` safely, or if the intended worktree path is already
occupied, stop and ask the user how to preserve or reuse it. Never change
`stories/` or `universe/` in the primary `main` checkout; merge the story branch
through a pull request. Git is the history; do not create manifests, ledgers,
receipts, release certificates, or duplicate lifecycle records.

## Canon lock and story editing

Humans and AI may directly patch or edit a story only while its authoritative
marker says `canon: false`. For AI work, inspect only the named story's canon
marker before reading it for production: `story.md` frontmatter for current
format or `story.json` for bundle format. When the marker is `false`, an
explicit request for a localized edit to that named story is sufficient AI
authorization; do not require a special waiver or an amendment to `AGENTS.md`.
Route a whole-story remake, rewrite, or overwrite through **Replacement
workflow**. When the marker is `true`, reject the edit request and do not edit,
overwrite, regenerate, or remove any file in the story package. An edit request
does not imply permission to unlock. The only allowed preparatory mutation is a
separately and explicitly requested unlock action that changes the
authoritative canon marker from `true` to `false`.

If a source marker already says `canon: false` while the publication catalog
says that story is canon, and no verified authorized unlock commit explains the
difference, treat the story as locked and stop for an explicit reconciliation
ruling. Never exploit an unexplained false marker or run capture in a way that
silently demotes the published canon state.

An explicit request to unlock a named story authorizes that action. A request
to edit or rewrite a named canon story does not; reject it and ask for a
separate unlock request if the user wants to make the story non-canon. The
unlock must be its own verified patch and commit, changing only the canon marker:
`story.json` for a bundle-format story or `story.md` frontmatter for a current-format story.
Do not combine the unlock with prose, cover, review, catalog, captured-page, or
universe edits. Once the unlock is complete, treat the story as non-canon and
begin any requested content work as a later action. That verified authorized
commit is the reconciliation ruling for editability even while the publication
snapshot still records the prior canon state. Capture remains blocked until the
named publication state is deliberately reconciled, and existing universe facts
still constrain the changed content. If the relevant state file is missing,
invalid, or has no unambiguous canon state, stop for user direction instead of
inferring it from the layout. A review request, critique, general approval to
improve stories, or an unnamed request authorizes neither an unlock nor an edit.

Unlocking a story does not demote or erase facts already recorded in
`universe/` as `LOCKED` or `CANON`. Those entries remain authoritative until a
separate user-approved retcon changes them.

For an AI-performed localized story edit:

1. Limit authority to the named story and the files or changes the user
   authorized. Complete the normal branch and dedicated worktree sequence
   before reading for production or modifying the story.
2. Edit the authorized prose directly and preserve its layout. For current
   format, patch `story.md`; for bundle format, patch the authorized prose file
   without migrating it to the current four-file format. Do not create process
   artifacts. Leave other story files and historical bundle files unchanged
   unless the user explicitly includes them or the current-format review loop
   requires a fresh `review.md` for the changed prose.
3. Use the smallest edit consistent with the request. Do not broaden a
   localized change into a general modernization pass; route whole-story work
   through **Replacement workflow**.
4. Check the resulting prose and diff directly. For current format, run
   `Test-Stories.ps1 -Story <slug> -Phase PreReview`, obtain a fresh independent
   review for changed prose, and run final validation after `PASS`; a targeted
   `REVISE` may be repaired through the ordinary writer/reviewer loop without a
   replacement. For bundle format, current-format validation and prior bundle
   review records do not certify changed prose, so run only compatible targeted
   checks. In either layout, state plainly when an old review, cover, or
   captured Pages snapshot may now be stale, and do not refresh publication
   artifacts until the changed story has the required passing review.
5. Even for a `canon: false` story, do not silently contradict shared authority.
   If the requested edit would change a fact represented in `LOCKED` or `CANON`
   universe notes, stop for the separate canon or retcon ruling. Prose-only
   changes that preserve established facts need no such ruling.

## `[WP]` workflow

Use the `story-create` skill for a new prompt tagged `[WP]`. Use `story-room`
only for its shared OUTLINE, REVIEW, and TITLE IMAGE stage contract or when the
user requests one named stage.

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
   canon or models to imitate. For `prospective-2026-08-21` or
   `prospective-2026-08-23`, target 700–1,000 words and never exceed 1,200. It
   completes the required story-specific Voice capsule without opening prior
   Voice sections or prose. Under 08-23 it also derives the dialogue promise
   from the prompt, deliberately chooses the dialogic medium, and states why
   communication itself moves this story. Record pressure and choices, not
   drafted confessions, reconciliations, speeches, or final thematic lines. Include
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
   `review.md`. For an 08-23 CREATE story, include the six most recent resolved
   passing current-story paths excluding the target for the collection
   comparison, or all available when fewer than six exist; these are
   comparison context only, never canon or models. The reviewer reads prompt
   and story first, forms a provisional
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
   illustrated-novel-cover default defined in that agent. Anime-influenced
   rendering remains available when it suits the story, but the composition
   must behave like a novel cover rather than franchise key art or a scene still.
   Include every reference image inventoried by the clean prompt, from all
   retained request blocks and the new request for a replacement, in the assignment and
   in the image-generation call. Use resolved local paths when all references
   have them; otherwise include the smallest recent-attachment
   set that contains them all. The illustrator must inspect every reference
   before composing, use it for the visual role implied by the request, and
   preserve recognizable reference traits that do not conflict with the final
   prose. If not all references can be provided to image generation, ask the
   user to attach the missing images again rather than generating without them.
   After the JPEG is saved, both the illustrator and coordinator must open that
   exact file with the available image-viewing tool. Image-generation output,
   prompt text, file metadata, and the illustrator's written report are not
   substitutes for seeing the saved pixels. Inspect the whole composition at
   reduced cover size and inspect full-resolution details; when a depicted hand,
   face, object connection, title letter, or spatial relation remains doubtful,
   use
   additional visual crops or views before deciding. Temporary review images
   must stay outside the story directory and must not be committed.
   The illustrator and coordinator must each judge the actual saved image at
   cover-card size and full resolution through seven separate gates. A pass must
   name visible evidence for every gate; repeating the prompt or the
   illustrator's self-report is not review:
   - **Cover identity** — the image reads first as a professionally art-directed
     novel cover, not an interior scene illustration, screenshot, film poster,
     character lineup, split-panel montage, or visual plot summary. One dominant
     image idea controls the composition and the typography belongs to the same
     design.
   - **Story promise** — the cover signals the story's genre, tone, and
     distinctive emotional or narrative contradiction through a charged partial
     image. It creates an unanswered question, remains recognizable as this
     story rather than merely its genre, and does not imply a resolution,
     romance, victory, scale, or stakes the prose has not earned.
   - **Editorial restraint** — the cover uses only the minimum cast, props,
     setting, and action needed for its hook. It does not inventory clues,
     reconstruct sequential beats, give equal weight to a roomful of figures,
     or explain who everyone is. Story specificity comes from selection and
     visual tension, not completeness.
   - **Depiction truth** — every person, role, relationship, object, action, and
     spatial connection the cover does choose to depict agrees with the prose.
     A symbolic image may compress reality but may not advertise a false event,
     allegiance, power relation, or outcome. A literal scene must preserve the
     geometry and cause-and-effect necessary for that chosen fragment to be
     true.
   - **Cover read** — at thumbnail scale the exact title is readable once, the
     focal hierarchy is immediate, and the dominant silhouette, emotional tone,
     and story-specific hook survive reduction. Intentional negative space and
     controlled detail beat crowded explanatory staging.
   - **Image integrity** — at full resolution anatomy and object counts are
     plausible, hands and faces withstand close inspection, perspective and
     depicted physical connections are coherent, and there is no unintended
     text, pseudo-text, watermark, or visual artifact.
   - **Production finish** — the image has intentional lighting, color
     separation, edge treatment, and typography rather than muddy values,
     overprocessed texture, illegible letterforms, accidental tangencies,
     generic decoration, or inconsistent rendering. The exact title remains
     undamaged inside the safe crop and the JPEG shows no visible scaling or
     compression defects.
   The coordinator must compare the actual saved image against the prompt and
   final prose and make an independent decision; the illustrator's self-report
   and the technical validator are not acceptance. If a depicted action, role,
   object connection, or spatial fact is ambiguous, treat it as failed rather
   than resolving it charitably
   from the prose. Technical polish cannot compensate for a generic or
   off-promise concept, and factual completeness cannot compensate for a cover
   that reads like an illustrated synopsis. When a gate fails, delegate a
   concise regeneration brief that says what to preserve, names the blocking
   miss, directs the concept, composition, or focal change, and restates the
   invariants. Require a new concept for a cover-identity, story-promise, or
   editorial-restraint failure, a new composition for a depiction-truth failure,
   and a targeted correction only for a localized integrity or finish failure.
   Repeat review until all seven gates pass, and do not capture a
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

Before delegating an 08-23 CREATE or replacement outline, count completed
passing current stories whose base `## Constraints` profile is 08-23 and whose
prompt has no historical `## Rewrite request`. When that count is a nonzero multiple of ten, the
coordinator performs a no-artifact rolling audit
of the ten most recent such stories. Check recurring dialogic media, articulate
competence structures, workplace triads, reasoning patterns, humor levels, and
ending gestures. Pass only a compact collection anti-default brief to the
outliner; do not expose prior prose or Voice capsules to the outliner or writer.

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

`Craft profile: prospective-2026-08-23` extends 08-21 for newly scaffolded
CREATE stories and replacements without changing completed stories that retain
an earlier profile. The
`## Story` section adds three completed fields:

- `Dialogue promise` — the relationship, tonal, and communication experience
  implied by this prompt rather than a dialogue quota;
- `Dialogic medium` — the deliberate use of speech, writing, internal voices,
  signs, interfaces, gesture, silence, failed contact, or a story-specific mix;
  and
- `Dialogue engine` — why these people must communicate and how communication
  itself creates movement.

The 08-23 `## Voice` section is capped at 220 words and adds
`Relationship movement` to the five 08-21 fields. It states what each major
participant wants from another, cannot comfortably request, and what an
exchange changes in knowledge, leverage, trust, commitment, risk, or the
relationship. `Rhetorical ownership` also assigns humor, evasion, affection,
misreading, social authority, and willingness to listen rather than relying
only on expertise, precision, or sentence length. The four dialogue-specific
Voice fields and the three Story dialogue fields may use
`N/A — no meaningful dialogue expected` only when the story truly contains no
meaningful dialogic action; non-spoken communication does not qualify for N/A.
Narrative texture and Anti-default remain required.

## Replacement workflow

Use `story-create` when the user explicitly requests a whole-story remake,
rewrite, overwrite, or replacement of one named completed story. Replacement
means removing the named package and then creating a clean current-format story;
it is not an in-place prose edit and has no preservation scopes. A localized
edit to a named non-canon story in either layout remains governed by **Canon
lock and story editing**.

1. Complete the normal `main` update, `codex/story-<slug>` branch, and sibling
   worktree sequence before inspecting story material for production. Read only
   the named story's authoritative canon marker first. If it is missing,
   invalid, or ambiguous, stop for user direction.
2. If the marker is `canon: true`, reject the replacement request and stop. The
   request does not authorize an unlock; the user must request the independent
   canon-marker-only unlock action separately before replacement work can begin.
3. Before removing the package, preserve every verbatim user-authored prompt or
   request block and every associated reference-image inventory, then preserve
   the new replacement request and its references. Discard only machine-owned
   selections, constraints, cover policy, and workflow metadata. Resolve every
   inventoried image from an accessible external path or attachment;
   display names are not paths. If an original cannot be recovered, ask the user
   to attach it again. Do not open the old outline, prose, review, or cover for
   creative reuse.
4. Remove only the explicitly named source package and its publication remnants:
   its catalog entry, captured cover, chronology placement, and bundle
   `stories/INDEX.md` row when present. Keep `stories/NAMES.md` as frozen
   production memory and do not remove or retcon `universe/` facts. Verify the
   exact paths before deletion. The target scaffold path must be absent.
5. Run `new-story.ps1` with all retained user-authored prompt/request text and
   the new request preserved verbatim under minimal labels. Pass every accessible image
   through `-ReferenceImage`, so the clean `prompt.md` records display names
   while the source images remain external. Use the active
   `prospective-2026-08-23` profile.
6. Run the ordinary CREATE outline, WRITE, PreReview, independent REVIEW, and
   REVISE loop with fresh agents. A replacement receives the same recent-story
   collection comparison as any other CREATE story. No prior outline, prose,
   review, title image, or historical process artifact may be carried forward.
7. Generate a fresh cover after PASS and apply all seven saved-pixel gates. A
   replacement never retains the removed cover as a candidate.
8. Add the final slug to the chronology, capture it into the publication
   snapshot, run final validation and `python pages/build.py check`, then commit
   the named removal and clean creation together, push, and open the normal draft
   pull request. Git preserves the removed version; create no backup or
   replacement-history artifact.

Completed packages may still contain historical `## Rewrite request`,
`## Rewrite selections`, or `## Rewrite constraints` sections. They are inert
production history, not an active workflow or permission to mutate the story.
When an old package is reviewed without replacement, its recorded prompt text
remains the acceptance authority and the last recorded craft profile remains
active. Do not generate new managed rewrite sections.

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

The prompt is the only acceptance authority. For a completed package carrying
historical rewrite sections, its recorded prompt text remains the amended
acceptance authority; those sections do not authorize new edits or revive the
retired in-place workflow.
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

`Craft profile: prospective-2026-08-23` extends that dialogue contract for new
CREATE stories and replacements. Treat speech, writing, internal voices, signs, interfaces,
gesture, silence, and failed contact as first-class dialogic media. Major
exchanges should materially change at least one of knowledge, leverage, trust,
commitment, risk, relationship, or action; adding more short exchanges is not
evidence of improvement. Check whether the cast has collapsed into articulate
professionals solving a material problem when the prompt supports play,
mistakes, pettiness, embarrassment, distraction, bad explanation, or social
unevenness instead. Check whether the ending uses practical instructions,
resumed maintenance, inventory, breakfast, or a return to work because the
story earned that gesture rather than because thematic contact was avoided.

For a CREATE story, including a replacement, after the target passes the standalone dialogue judgment, compare its
dialogic pattern, one representative major exchange, and final meaningful
exchange with the six most recent passing current stories, or all available
when fewer than six exist. Open only the bounded prior-prose passages and
adjacent action or narration needed for that purpose;
do not expose them to the outliner or writer. Repeated media or competence is
not automatically a defect, but block material collection-level convergence
when the exchanges, reasoning pattern, relationship action, or ending gesture
could be transplanted by changing job, system, or setting nouns. Record any
failure through the existing single `Dialogue: REVISE` line and one concise
blocking finding; create no comparison field or audit artifact.

Review prose concisely. Record only blocking findings and short useful notes;
do not preserve reviewer chain-of-thought, repeated summaries, or audit logs.

## Canon

New stories begin with `canon: false`. Canon promotion requires explicit user
approval for one named story and a fresh passing review against current
authority. Add or amend only the smallest relevant `universe/*.md` entries when
the approved story establishes facts not already present there, then set the
authoritative `canon` flag to `true` in `story.md` frontmatter or bundle-format
`story.json`. A conflict with `LOCKED` canon stops for a user ruling. Git records
the transaction; no separate delta or promotion file is needed.

`canon: true` is also the story-edit lock for humans and AI. Reject direct edit
requests while that state is true; they do not authorize an implicit unlock.
To make later revision possible, the user must separately request the
independent unlock action in **Canon lock and story editing**; the
canon-marker-only patch and commit must complete before any story change begins.
That unlock makes the story editable but does not itself alter authoritative
`universe/` entries.

## Pages

`pages/catalog.json` and `pages/covers/` form the stored publication snapshot.
GitHub Pages builds and publishes only that snapshot; it never traverses
`stories/` or runs story validation. The `capture` command requires a passing
review and copies one completed story and its title image into the snapshot
without rerunning full validation. Keep the catalog ordered by full creation
timestamp, newest to oldest, so the newest story is always the first card on the
GitHub Pages index. New scaffolds record `created-at`; when a source has only a
`created` date, capture combines that date with the story prose file's filesystem
modification time. `capture-all` refreshes only the stories already present in
the publication catalog; it never republishes an unpublished source package and
refuses any source/catalog canon demotion. It is not used by CI.
`python pages/build.py check` verifies source, bundle index, catalog, cover,
chronology, and source/catalog canon-flag parity, including byte-identical
captured covers. A mismatch is blocking and may be reconciled only through the
named canon process.

## Completion

A new or replacement current story is complete when its four Markdown files and 9:16 portrait
`title-image.jpg` exist, `review.md` says `PASS`, people and places are
inventoried, all three continuity lines pass, and the story plus image have
been completed in the story directory and captured into `pages/catalog.json`
and `pages/covers/`. Repository acceptance also requires the local final
validator and catalog check to pass, the completed changes to be committed and
pushed on its story branch, and a draft pull request to be open against the
repository's default branch.
