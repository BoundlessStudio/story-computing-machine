# Story Computing Machine

A durable shared-world story room built with [Vercel Eve](https://eve.dev/) and routed exclusively through [OpenRouter](https://openrouter.ai/docs/guides/community/vercel-ai-sdk). It creates foundation worlds and turns writing prompts into reviewed, canon-grounded story outlines using an immutable, versioned artifact graph.

## What the MVP does

The deployed story flow is:

```text
prompt → canon preflight → three independent pitch teams → writer selection
       → specialist plans → 6–8 scene outline → three critics
       → final revision → deterministic gates → explicit canon promotion
       → Markdown writer packet
```

Every prompt, plan, pitch, review, decision, outline, delta, snapshot, and export is a typed artifact. A local SQLite database is authoritative; Eve session state is not used as cross-session memory. Story runs store workflow status and exact artifact pointers, while lineage edges record `consumes`, `derives-from`, `reviews`, `supersedes`, `promotes`, and `renders` relationships.

Only an explicitly promoted outline changes the shared world. A provisional or stale run is invisible to future stories.

## Story room

The root agent coordinates and persists but does not creatively synthesize. The declared story specialists are:

1. `prompt_interpreter`
2. `canon_librarian`
3. `pitch_originator`, invoked once for each of three isolated branches
4. `character_architect`
5. `conflict_architect`
6. `world_integration_advisor`
7. `story_editor`, the sole synthesis role
8. `plot_architect`
9. `scene_architect`
10. `continuity_critic`
11. `narrative_logic_critic`
12. `theme_pacing_critic`

The existing `culture_architect`, `historian`, and `continuity_advisor` remain responsible for foundation-world generation. Eve discovers 15 declared subagents in total. Every declared specialist has a private prompt, task-mode Zod output, role-appropriate OpenRouter model, token budget, and disabled shell/filesystem/web tools.

## Artifact contract

Artifacts carry:

- UUID, kind, schema version, logical key, and logical version
- shared-world ID, story-run ID, branch ID, and pinned canon revision
- exact canon snapshot artifact ID
- canonical SHA-256 content hash
- human, agent, or tool provenance
- active, superseded, stale, or rejected lifecycle state
- immutable, validated JSON content stored as SQLite JSON text

Direct editing uses expected-hash [RFC 6902 JSON Patch](https://www.rfc-editor.org/rfc/rfc6902) paths under `/content`. An edit creates a human-authored version, supersedes the prior version, recursively invalidates descendants, and moves the run back to the earliest required stage. It never silently calls a model.

All story-room artifacts can be version-edited. Foundation and committed canon artifacts, envelopes, execution records, and rendered exports cannot. Editing a critic report makes it commentary; a fresh agent review of the exact final-outline hash is still required for promotion.

## Persistence

The migration creates:

- `worlds`: the singleton `shared-world` and canon head
- `story_runs`: workflow state and current artifact pointers
- `artifacts`: versioned JSON bodies and provenance
- `artifact_edges`: lineage DAG
- `agent_executions`: model/session/usage metadata without chain-of-thought
- `run_events`: append-only state-transition audit
- `canon_revisions`: materialized snapshots and promotion history

Promotion is an idempotent `BEGIN IMMEDIATE` transaction. It requires the current base revision, active final outline and delta, and three active agent-authored passing reviews whose target ID and hash exactly match that outline. SQLite serializes writers, while WAL mode permits concurrent reads; stale promotion attempts cannot rebase automatically.

## Setup

Requires Node.js 24+ and an OpenRouter key. Persistence uses Node's built-in `node:sqlite` module, so no database server or native third-party driver is required. The default database is `data/story-room.sqlite`.

```powershell
npm install
Copy-Item .env.example .env
# Set OPENROUTER_API_KEY in .env; SQLITE_PATH is optional
npm run db:migrate
npm run canon:bootstrap -- --file output/lumenwake-42.json
npm run dev
```

`db:migrate` creates the parent directory and applies migrations transactionally. `canon:bootstrap` is idempotent for the same foundation and refuses to replace an initialized shared world with a different one. Generate another candidate foundation with the existing world workflow or `npm run world:demo`, then bootstrap that file instead.

The SQLite design is intentionally local and single-host. Do not place the database on an ephemeral or multi-instance serverless filesystem; use a managed client/server database if the application later needs horizontally scaled writers.

Example prompts in Eve's terminal UI:

```text
Start a story about a Tidewright who discovers that the water ledgers predict Orra's dreams.

Select pitch-b from story run <run-id>.

Promote outline <artifact-id> from story run <run-id>.

Export the current writer packet for story run <run-id>.
```

For deterministic edits, provide the artifact ID, current hash, and patch explicitly:

```text
Patch artifact <artifact-id> at hash <sha256>:
[{"op":"replace","path":"/content/tone","value":"claustrophobic and humane"}]
```

## Configuration

`.env` accepts:

- `SQLITE_PATH` (defaults to `data/story-room.sqlite`; relative paths resolve from the project root)
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` and `OPENROUTER_MODEL_CONTEXT_TOKENS`
- `OPENROUTER_WORKER_MODEL` and `OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS`
- `OPENROUTER_ADVISOR_MODEL` and `OPENROUTER_ADVISOR_MODEL_CONTEXT_TOKENS`

The root, worker, and advisor model IDs remain configurable without changing orchestration. OpenRouter is the only model gateway.

## Important deterministic tools

- `begin_story`
- `clarify_story_prompt`
- `save_agent_artifact`
- `record_agent_execution` for started or failed child calls without output artifacts
- `get_artifact` (exact version plus immediate lineage) / `list_run_artifacts`
- `patch_story_artifact`
- `regenerate_from_artifact`
- `select_pitch`
- `finalize_outline`
- `promote_outline`
- `render_writer_packet`
- `finalize_world`

The Markdown writer packet is rendered from exact current artifacts. It includes the brief, selected pitch, cast, world grounding, theme, scene outline, canon impact, resolved review summary, and artifact provenance. Markdown is derived output and is never re-imported as canon.

## Project layout

```text
agent/
├── agent.ts                   # Eve root config and result union
├── instructions.md            # durable orchestration policy
├── lib/
│   ├── artifact-domain.ts     # envelopes, hashes, patching, canon rules
│   ├── artifact-store.ts      # repository contracts and JSON Patch engine
│   ├── sqlite-artifact-store.ts  # transactional local SQLite repository
│   ├── story-domain.ts        # story-room structured contracts
│   └── writer-packet.ts       # deterministic Markdown renderer
├── tools/                     # root-only deterministic operations
└── subagents/                 # 12 story + 3 foundation specialists
scripts/
├── migrate-database.ts
└── bootstrap-canon.ts
sql/
└── 001_artifact_graph.sql
test/
├── artifact-domain.test.ts
├── sqlite-artifact-store.test.ts
├── writer-packet.test.ts
└── world.test.ts
```

## Verification

```powershell
npm run info
npm run check
npm test
npm run build
```

The deterministic suite covers canonical hashing and references, delta application, schema validation, RFC 6902 editing, unsafe patch paths, SQLite migration/bootstrap, logical versioning, lineage, transitive invalidation, optimistic edit conflicts, exact review gates, atomic promotion, and deterministic Markdown provenance. Model-backed story generation additionally consumes OpenRouter credits.

`npm run smoke:live` remains the live foundation-world smoke test. `npm run world:demo` and `npm run world:offline` provide API-free foundation fixtures.
