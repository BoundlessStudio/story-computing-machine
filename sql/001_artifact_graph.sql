CREATE TABLE IF NOT EXISTS worlds (
  world_id TEXT PRIMARY KEY,
  foundation_artifact_id TEXT NOT NULL,
  current_canon_revision INTEGER NOT NULL CHECK (current_canon_revision > 0),
  current_canon_snapshot_artifact_id TEXT NOT NULL,
  current_canon_hash TEXT NOT NULL CHECK (length(current_canon_hash) = 64 AND current_canon_hash NOT GLOB '*[^0-9a-f]*'),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (world_id = 'shared-world'),
  FOREIGN KEY (foundation_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (current_canon_snapshot_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS story_runs (
  story_run_id TEXT PRIMARY KEY,
  world_id TEXT NOT NULL REFERENCES worlds(world_id),
  base_canon_revision INTEGER NOT NULL CHECK (base_canon_revision > 0),
  base_canon_snapshot_artifact_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'analyzing', 'needs_clarification', 'building_pitches', 'awaiting_pitch',
    'planning', 'reviewing', 'needs_revision', 'ready_for_promotion',
    'promoted', 'stale', 'failed'
  )),
  original_prompt_artifact_id TEXT NOT NULL,
  brief_artifact_id TEXT,
  pitch_slate_artifact_id TEXT,
  pitch_selection_artifact_id TEXT,
  blueprint_artifact_id TEXT,
  final_outline_artifact_id TEXT,
  canon_delta_artifact_id TEXT,
  event_sequence INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (base_canon_snapshot_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (original_prompt_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (brief_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (pitch_slate_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (pitch_selection_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (blueprint_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (final_outline_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (canon_delta_artifact_id) REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS story_runs_world_status_idx
  ON story_runs (world_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  world_id TEXT NOT NULL REFERENCES worlds(world_id),
  story_run_id TEXT REFERENCES story_runs(story_run_id),
  branch_id TEXT CHECK (branch_id IS NULL OR branch_id IN ('A', 'B', 'C')),
  kind TEXT NOT NULL,
  schema_version INTEGER NOT NULL CHECK (schema_version > 0),
  logical_key TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  canon_revision INTEGER NOT NULL CHECK (canon_revision > 0),
  canon_snapshot_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  content TEXT NOT NULL CHECK (json_valid(content)),
  content_hash TEXT NOT NULL CHECK (length(content_hash) = 64 AND content_hash NOT GLOB '*[^0-9a-f]*'),
  producer_type TEXT NOT NULL CHECK (producer_type IN ('human', 'agent', 'tool')),
  producer_name TEXT NOT NULL,
  producer_model_id TEXT,
  producer_gateway TEXT CHECK (producer_gateway IS NULL OR producer_gateway = 'openrouter'),
  producer_eve_session_id TEXT,
  lifecycle_status TEXT NOT NULL DEFAULT 'active'
    CHECK (lifecycle_status IN ('active', 'superseded', 'stale', 'rejected')),
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS artifacts_logical_version_idx
  ON artifacts (world_id, COALESCE(story_run_id, ''), logical_key, version);
CREATE UNIQUE INDEX IF NOT EXISTS artifacts_active_logical_key_idx
  ON artifacts (world_id, COALESCE(story_run_id, ''), logical_key)
  WHERE lifecycle_status = 'active';
CREATE INDEX IF NOT EXISTS artifacts_run_kind_idx
  ON artifacts (story_run_id, kind, created_at);
CREATE INDEX IF NOT EXISTS artifacts_canon_revision_idx
  ON artifacts (world_id, canon_revision);
CREATE INDEX IF NOT EXISTS artifacts_content_hash_idx
  ON artifacts (content_hash);
CREATE INDEX IF NOT EXISTS artifacts_producer_idx
  ON artifacts (producer_type, producer_name);

CREATE TABLE IF NOT EXISTS artifact_edges (
  parent_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
  child_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
  relationship_type TEXT NOT NULL CHECK (relationship_type IN (
    'consumes', 'derives-from', 'reviews', 'supersedes', 'promotes', 'renders'
  )),
  created_at TEXT NOT NULL,
  PRIMARY KEY (parent_artifact_id, child_artifact_id, relationship_type),
  CHECK (parent_artifact_id <> child_artifact_id OR relationship_type <> 'supersedes')
);

CREATE INDEX IF NOT EXISTS artifact_edges_child_idx
  ON artifact_edges (child_artifact_id, relationship_type);

CREATE TABLE IF NOT EXISTS agent_executions (
  execution_id TEXT PRIMARY KEY,
  story_run_id TEXT NOT NULL REFERENCES story_runs(story_run_id),
  agent_name TEXT NOT NULL,
  eve_child_session_id TEXT,
  model_id TEXT,
  gateway TEXT CHECK (gateway IS NULL OR gateway = 'openrouter'),
  input_artifact_ids TEXT NOT NULL CHECK (json_valid(input_artifact_ids)),
  output_artifact_ids TEXT NOT NULL CHECK (json_valid(output_artifact_ids)),
  prompt_revision TEXT,
  skill_revision TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  input_tokens INTEGER CHECK (input_tokens IS NULL OR input_tokens >= 0),
  output_tokens INTEGER CHECK (output_tokens IS NULL OR output_tokens >= 0),
  cost_usd REAL CHECK (cost_usd IS NULL OR cost_usd >= 0),
  status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
  error_summary TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS agent_executions_run_idx
  ON agent_executions (story_run_id, started_at);

CREATE TABLE IF NOT EXISTS run_events (
  event_id TEXT PRIMARY KEY,
  story_run_id TEXT NOT NULL REFERENCES story_runs(story_run_id),
  run_sequence INTEGER NOT NULL CHECK (run_sequence > 0),
  previous_status TEXT,
  next_status TEXT NOT NULL,
  actor_type TEXT NOT NULL CHECK (actor_type IN ('human', 'agent', 'tool')),
  actor_name TEXT NOT NULL,
  triggering_artifact_id TEXT REFERENCES artifacts(artifact_id) DEFERRABLE INITIALLY DEFERRED,
  summary TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (story_run_id, run_sequence)
);

CREATE INDEX IF NOT EXISTS run_events_run_idx
  ON run_events (story_run_id, run_sequence);

CREATE TABLE IF NOT EXISTS canon_revisions (
  world_id TEXT NOT NULL REFERENCES worlds(world_id),
  revision INTEGER NOT NULL CHECK (revision > 0),
  parent_revision INTEGER,
  snapshot_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
  delta_artifact_id TEXT REFERENCES artifacts(artifact_id),
  source_story_run_id TEXT REFERENCES story_runs(story_run_id),
  final_outline_artifact_id TEXT REFERENCES artifacts(artifact_id),
  canon_hash TEXT NOT NULL CHECK (length(canon_hash) = 64 AND canon_hash NOT GLOB '*[^0-9a-f]*'),
  committed_at TEXT NOT NULL,
  PRIMARY KEY (world_id, revision),
  UNIQUE (snapshot_artifact_id)
);

CREATE INDEX IF NOT EXISTS canon_revisions_source_run_idx
  ON canon_revisions (source_story_run_id);
