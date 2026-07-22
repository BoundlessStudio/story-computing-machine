import { randomUUID } from 'node:crypto';
import { mkdirSync } from 'node:fs';
import { dirname, isAbsolute, resolve } from 'node:path';
import { DatabaseSync, type SQLInputValue } from 'node:sqlite';
import {
  NON_EDITABLE_ARTIFACT_KINDS,
  artifactContentHash,
  statusAfterArtifactEdit,
  validateArtifactContent,
  type ArtifactKind,
} from './artifact-domain.js';
import {
  SHARED_WORLD_ID,
  applyArtifactPatch,
  asJsonValue,
  type AgentExecutionInput,
  type ArtifactEnvelope,
  type ArtifactLifecycle,
  type ArtifactLineageLink,
  type ArtifactParent,
  type ArtifactProducer,
  type ArtifactRelationship,
  type ArtifactValidator,
  type CanonBootstrapInput,
  type JsonPatchOperation,
  type JsonValue,
  type PromotionInput,
  type SaveArtifactInput,
  type StoryRunRecord,
  type StoryRunStatus,
} from './artifact-store.js';

type DatabaseRow = Record<string, unknown>;

const BRANCH_ARTIFACT_KINDS = new Set<ArtifactKind>([
  'pitch.seed',
  'pitch.character-plan',
  'pitch.conflict-plan',
  'pitch.world-plan',
]);

function now(): string {
  return new Date().toISOString();
}

function assertUuid(value: string, label: string): void {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu.test(value)) {
    throw new Error(`${label} must be a UUID`);
  }
}

function parseContent(validator: ArtifactValidator | undefined, kind: ArtifactKind, schemaVersion: number, value: unknown): JsonValue {
  if (schemaVersion !== 1) throw new Error(`Unsupported ${kind} schema version: ${schemaVersion}`);
  const content = validator ? validator.parse(kind, schemaVersion, value) : validateArtifactContent(kind, value);
  return asJsonValue(content);
}

function parseStoredJson(value: unknown): JsonValue {
  if (typeof value !== 'string') throw new Error('Stored artifact content is not JSON text');
  return asJsonValue(JSON.parse(value));
}

function sanitizeErrorSummary(value: string | undefined): string | undefined {
  if (!value) return undefined;
  return value
    .replace(/\b(?:sk-or-v1-|sk-)[a-z0-9_-]{12,}\b/giu, '[redacted-api-key]')
    .replace(/\b(Bearer\s+)[a-z0-9._~-]+/giu, '$1[redacted]')
    .replace(/\b(SQLITE_PATH|OPENROUTER_API_KEY)\s*=\s*\S+/giu, '$1=[redacted]')
    .slice(0, 2_000);
}

function artifactFromRow(row: DatabaseRow): ArtifactEnvelope {
  return {
    artifactId: String(row.artifact_id),
    worldId: SHARED_WORLD_ID,
    storyRunId: row.story_run_id ? String(row.story_run_id) : null,
    branchId: row.branch_id ? String(row.branch_id) as 'A' | 'B' | 'C' : null,
    kind: String(row.kind) as ArtifactKind,
    schemaVersion: Number(row.schema_version),
    logicalKey: String(row.logical_key),
    version: Number(row.version),
    canonRevision: Number(row.canon_revision),
    canonSnapshotArtifactId: String(row.canon_snapshot_artifact_id),
    content: parseStoredJson(row.content),
    contentHash: String(row.content_hash),
    producer: {
      type: String(row.producer_type) as ArtifactProducer['type'],
      name: String(row.producer_name),
      ...(row.producer_model_id ? { modelId: String(row.producer_model_id) } : {}),
      ...(row.producer_gateway ? { gateway: String(row.producer_gateway) as 'openrouter' } : {}),
      ...(row.producer_eve_session_id ? { eveSessionId: String(row.producer_eve_session_id) } : {}),
    },
    lifecycleStatus: String(row.lifecycle_status) as ArtifactLifecycle,
    createdAt: String(row.created_at),
  };
}

function runFromRow(row: DatabaseRow): StoryRunRecord {
  return {
    storyRunId: String(row.story_run_id),
    worldId: SHARED_WORLD_ID,
    baseCanonRevision: Number(row.base_canon_revision),
    baseCanonSnapshotArtifactId: String(row.base_canon_snapshot_artifact_id),
    status: String(row.status) as StoryRunStatus,
    originalPromptArtifactId: String(row.original_prompt_artifact_id),
    briefArtifactId: row.brief_artifact_id ? String(row.brief_artifact_id) : null,
    pitchSlateArtifactId: row.pitch_slate_artifact_id ? String(row.pitch_slate_artifact_id) : null,
    pitchSelectionArtifactId: row.pitch_selection_artifact_id ? String(row.pitch_selection_artifact_id) : null,
    blueprintArtifactId: row.blueprint_artifact_id ? String(row.blueprint_artifact_id) : null,
    finalOutlineArtifactId: row.final_outline_artifact_id ? String(row.final_outline_artifact_id) : null,
    canonDeltaArtifactId: row.canon_delta_artifact_id ? String(row.canon_delta_artifact_id) : null,
    createdAt: String(row.created_at),
    updatedAt: String(row.updated_at),
  };
}

function resolveDatabasePath(value = process.env.SQLITE_PATH ?? 'data/story-room.sqlite'): string {
  if (value === ':memory:') return value;
  return isAbsolute(value) ? value : resolve(process.cwd(), value);
}

export class ArtifactStore {
  private readonly database: DatabaseSync;

  constructor(databasePath = resolveDatabasePath(), private readonly validator?: ArtifactValidator) {
    const resolvedPath = resolveDatabasePath(databasePath);
    if (resolvedPath !== ':memory:') mkdirSync(dirname(resolvedPath), { recursive: true });
    this.database = new DatabaseSync(resolvedPath);
    this.database.exec('PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL; PRAGMA busy_timeout = 5000;');
    const migrated = this.getRow("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'artifacts'");
    if (!migrated) {
      this.database.close();
      throw new Error('SQLite database is not migrated. Run npm run db:migrate first.');
    }
  }

  close(): void {
    this.database.close();
  }

  private getRow(statement: string, params: SQLInputValue[] = []): DatabaseRow | undefined {
    return this.database.prepare(statement).get(...params) as DatabaseRow | undefined;
  }

  private allRows(statement: string, params: SQLInputValue[] = []): DatabaseRow[] {
    return this.database.prepare(statement).all(...params) as DatabaseRow[];
  }

  private transaction<T>(operation: () => T): T {
    this.database.exec('BEGIN IMMEDIATE');
    try {
      this.database.exec('PRAGMA defer_foreign_keys = ON');
      const result = operation();
      this.database.exec('COMMIT');
      return result;
    } catch (error) {
      this.database.exec('ROLLBACK');
      throw error;
    }
  }

  private insertArtifact(input: {
    artifactId: string;
    storyRunId: string | null;
    branchId: 'A' | 'B' | 'C' | null;
    kind: ArtifactKind;
    schemaVersion: number;
    logicalKey: string;
    version: number;
    canonRevision: number;
    canonSnapshotArtifactId: string;
    content: JsonValue;
    contentHash: string;
    producer: ArtifactProducer;
    createdAt: string;
  }): void {
    this.database.prepare(`
      INSERT INTO artifacts (
        artifact_id, world_id, story_run_id, branch_id, kind, schema_version,
        logical_key, version, canon_revision, canon_snapshot_artifact_id,
        content, content_hash, producer_type, producer_name, producer_model_id,
        producer_gateway, producer_eve_session_id, lifecycle_status, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
    `).run(
      input.artifactId,
      SHARED_WORLD_ID,
      input.storyRunId,
      input.branchId,
      input.kind,
      input.schemaVersion,
      input.logicalKey,
      input.version,
      input.canonRevision,
      input.canonSnapshotArtifactId,
      JSON.stringify(input.content),
      input.contentHash,
      input.producer.type,
      input.producer.name,
      input.producer.modelId ?? null,
      input.producer.gateway ?? null,
      input.producer.eveSessionId ?? null,
      input.createdAt,
    );
  }

  private descendants(artifactId: string, lifecycleStatus?: ArtifactLifecycle): DatabaseRow[] {
    return this.allRows(`
      WITH RECURSIVE descendants(artifact_id) AS (
        SELECT child_artifact_id FROM artifact_edges WHERE parent_artifact_id = ?
        UNION
        SELECT e.child_artifact_id FROM artifact_edges e JOIN descendants d ON e.parent_artifact_id = d.artifact_id
      )
      SELECT a.artifact_id, a.lifecycle_status
      FROM artifacts a JOIN descendants d ON d.artifact_id = a.artifact_id
      WHERE (? IS NULL OR a.lifecycle_status = ?)
      ORDER BY a.created_at, a.artifact_id
    `, [artifactId, lifecycleStatus ?? null, lifecycleStatus ?? null]);
  }

  async beginStory(prompt: string, producerName = 'writer', runId = randomUUID()): Promise<{ run: StoryRunRecord; prompt: ArtifactEnvelope }> {
    if (!prompt.trim()) throw new Error('A non-empty writing prompt is required');
    assertUuid(runId, 'runId');
    const promptArtifactId = randomUUID();
    const content = parseContent(this.validator, 'prompt.original', 1, { text: prompt.trim() });
    const contentHash = artifactContentHash(content);
    return this.transaction(() => {
      const head = this.getRow('SELECT * FROM worlds WHERE world_id = ? AND current_canon_revision > 0', [SHARED_WORLD_ID]);
      if (!head) throw new Error('The shared world has not been bootstrapped');
      const timestamp = now();
      this.database.prepare(`
        INSERT INTO story_runs (
          story_run_id, world_id, base_canon_revision, base_canon_snapshot_artifact_id,
          status, original_prompt_artifact_id, event_sequence, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'analyzing', ?, 1, ?, ?)
      `).run(
        runId,
        SHARED_WORLD_ID,
        Number(head.current_canon_revision),
        String(head.current_canon_snapshot_artifact_id),
        promptArtifactId,
        timestamp,
        timestamp,
      );
      this.insertArtifact({
        artifactId: promptArtifactId,
        storyRunId: runId,
        branchId: null,
        kind: 'prompt.original',
        schemaVersion: 1,
        logicalKey: 'prompt/original',
        version: 1,
        canonRevision: Number(head.current_canon_revision),
        canonSnapshotArtifactId: String(head.current_canon_snapshot_artifact_id),
        content,
        contentHash,
        producer: { type: 'human', name: producerName },
        createdAt: timestamp,
      });
      this.database.prepare(`
        INSERT INTO run_events (
          event_id, story_run_id, run_sequence, previous_status, next_status,
          actor_type, actor_name, triggering_artifact_id, summary, created_at
        ) VALUES (?, ?, 1, NULL, 'analyzing', 'human', ?, ?, ?, ?)
      `).run(randomUUID(), runId, producerName, promptArtifactId, 'Story run created and pinned to canon', timestamp);
      return {
        run: runFromRow(this.getRow('SELECT * FROM story_runs WHERE story_run_id = ?', [runId])!),
        prompt: artifactFromRow(this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [promptArtifactId])!),
      };
    });
  }

  async saveArtifact(input: SaveArtifactInput): Promise<ArtifactEnvelope> {
    assertUuid(input.storyRunId, 'storyRunId');
    if (input.nextStatus === 'promoted' || input.nextStatus === 'stale') throw new Error(`${input.nextStatus} is reserved for the atomic promotion path`);
    if (input.nextStatus === 'ready_for_promotion' && (input.kind !== 'canon.delta' || input.producer.type !== 'tool')) {
      throw new Error('Only a deterministic canon.delta tool artifact may make a run promotable');
    }
    if (['canon.delta', 'export.writer-packet'].includes(input.kind) && input.producer.type !== 'tool') {
      throw new Error(`${input.kind} must be produced by a deterministic tool`);
    }
    if (input.kind === 'decision.pitch-selection' && input.producer.type !== 'human') throw new Error('Pitch selection must be a human decision');
    if (input.supersedesArtifactId) assertUuid(input.supersedesArtifactId, 'supersedesArtifactId');
    if (input.parents?.some((parent) => parent.artifactId === input.supersedesArtifactId)) {
      throw new Error('A superseded artifact must not also be supplied as a normal parent');
    }
    const schemaVersion = input.schemaVersion ?? 1;
    const content = parseContent(this.validator, input.kind, schemaVersion, input.content);
    const contentBranchId = content && typeof content === 'object' && !Array.isArray(content) ? content.branchId : undefined;
    if (BRANCH_ARTIFACT_KINDS.has(input.kind)) {
      if (!input.branchId || contentBranchId !== input.branchId) throw new Error(`${input.kind} requires matching envelope and content branch IDs`);
    } else if (input.branchId) throw new Error(`${input.kind} must not be stored in an isolated pitch branch`);

    const parents = input.parents ?? [];
    for (const parent of parents) {
      assertUuid(parent.artifactId, 'parent.artifactId');
      if (parent.relationship === 'supersedes') throw new Error('Use supersedesArtifactId to create supersession lineage');
      if (parent.relationship === 'promotes') throw new Error('Promotion lineage can only be created by promoteOutline');
      if (parent.relationship === 'renders' && input.kind !== 'export.writer-packet') throw new Error('Only writer packet exports may use renders lineage');
      if (parent.relationship === 'reviews' && !input.kind.startsWith('review.')) throw new Error('Only review artifacts may use reviews lineage');
    }
    if (new Set(parents.map((parent) => `${parent.artifactId}:${parent.relationship}`)).size !== parents.length) {
      throw new Error('Duplicate artifact lineage edge');
    }

    return this.transaction(() => {
      const runRow = this.getRow('SELECT * FROM story_runs WHERE story_run_id = ?', [input.storyRunId]);
      if (!runRow) throw new Error('Artifact save rejected: story run not found');
      const run = runFromRow(runRow);
      if (input.expectedStatus && run.status !== input.expectedStatus) throw new Error('Artifact save rejected: story run status changed');
      if (run.status === 'promoted' && input.kind !== 'export.writer-packet') throw new Error('Promoted story runs are immutable');

      for (const parent of parents) {
        const parentRow = this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [parent.artifactId]);
        if (!parentRow || parentRow.lifecycle_status !== 'active') throw new Error('Artifact save rejected: parent is missing or inactive');
        const sameRun = parentRow.story_run_id === input.storyRunId;
        const pinnedSnapshot = parentRow.artifact_id === run.baseCanonSnapshotArtifactId;
        if (!sameRun && !pinnedSnapshot) throw new Error('Artifact save rejected: parent belongs to another run');
        if (input.branchId && parentRow.branch_id && parentRow.branch_id !== input.branchId) {
          throw new Error('Artifact save rejected: isolated pitch branches cannot consume one another');
        }
      }

      let superseded: DatabaseRow | undefined;
      let invalidatedIds: string[] = [];
      if (input.supersedesArtifactId) {
        superseded = this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [input.supersedesArtifactId]);
        if (
          !superseded
          || superseded.story_run_id !== input.storyRunId
          || superseded.lifecycle_status !== 'active'
          || (input.expectedSupersededHash && superseded.content_hash !== input.expectedSupersededHash)
          || superseded.kind !== input.kind
          || superseded.logical_key !== input.logicalKey
        ) throw new Error('Artifact save rejected: superseded artifact is no longer valid');
        invalidatedIds = this.descendants(input.supersedesArtifactId, 'active').map((row) => String(row.artifact_id));
        const invalidatedSet = new Set(invalidatedIds);
        if (parents.some((parent) => invalidatedSet.has(parent.artifactId))) {
          throw new Error('Artifact save rejected: supersession would create a lineage cycle through a descendant parent');
        }
        this.database.prepare("UPDATE artifacts SET lifecycle_status = 'superseded' WHERE artifact_id = ?").run(input.supersedesArtifactId);
        const markStale = this.database.prepare("UPDATE artifacts SET lifecycle_status = 'stale' WHERE artifact_id = ? AND lifecycle_status = 'active'");
        for (const artifactId of invalidatedIds) markStale.run(artifactId);
      }

      const versionRow = this.getRow(
        'SELECT COALESCE(MAX(version), 0) + 1 AS next_version FROM artifacts WHERE story_run_id = ? AND logical_key = ?',
        [input.storyRunId, input.logicalKey],
      );
      const artifactId = randomUUID();
      const timestamp = now();
      this.insertArtifact({
        artifactId,
        storyRunId: input.storyRunId,
        branchId: input.branchId ?? null,
        kind: input.kind,
        schemaVersion,
        logicalKey: input.logicalKey,
        version: Number(versionRow?.next_version ?? 1),
        canonRevision: run.baseCanonRevision,
        canonSnapshotArtifactId: run.baseCanonSnapshotArtifactId,
        content,
        contentHash: artifactContentHash(content),
        producer: input.producer,
        createdAt: timestamp,
      });
      const insertEdge = this.database.prepare(`
        INSERT INTO artifact_edges (parent_artifact_id, child_artifact_id, relationship_type, created_at)
        VALUES (?, ?, ?, ?)
      `);
      for (const parent of parents) insertEdge.run(parent.artifactId, artifactId, parent.relationship, timestamp);
      if (input.supersedesArtifactId) insertEdge.run(input.supersedesArtifactId, artifactId, 'supersedes', timestamp);

      let briefId = run.briefArtifactId;
      let originalPromptId = run.originalPromptArtifactId;
      let slateId = run.pitchSlateArtifactId;
      let selectionId = run.pitchSelectionArtifactId;
      let blueprintId = run.blueprintArtifactId;
      let outlineId = run.finalOutlineArtifactId;
      let deltaId = run.canonDeltaArtifactId;
      if (input.kind === 'prompt.original') originalPromptId = artifactId;
      if (input.kind === 'story.brief') briefId = artifactId;
      else if (superseded && input.nextStatus === 'analyzing') briefId = null;
      if (input.kind === 'pitch.slate') slateId = artifactId;
      else if (superseded && ['analyzing', 'building_pitches'].includes(input.nextStatus ?? '')) slateId = null;
      if (input.kind === 'decision.pitch-selection') selectionId = artifactId;
      else if (superseded && ['analyzing', 'building_pitches'].includes(input.nextStatus ?? '')) selectionId = null;
      if (input.kind === 'outline.blueprint') blueprintId = artifactId;
      else if (superseded && ['analyzing', 'building_pitches', 'planning'].includes(input.nextStatus ?? '')) blueprintId = null;
      if (input.kind === 'outline.final') outlineId = artifactId;
      else if (superseded && !input.kind.startsWith('review.') && input.nextStatus && input.nextStatus !== 'ready_for_promotion') outlineId = null;
      if (input.kind === 'canon.delta') deltaId = artifactId;
      else if (superseded) deltaId = null;

      const nextStatus = input.nextStatus ?? run.status;
      const nextSequence = input.nextStatus ? Number(runRow.event_sequence) + 1 : Number(runRow.event_sequence);
      this.database.prepare(`
        UPDATE story_runs SET status = ?, original_prompt_artifact_id = ?, brief_artifact_id = ?, pitch_slate_artifact_id = ?,
          pitch_selection_artifact_id = ?, blueprint_artifact_id = ?, final_outline_artifact_id = ?,
          canon_delta_artifact_id = ?, event_sequence = ?, updated_at = ?
        WHERE story_run_id = ?
      `).run(nextStatus, originalPromptId, briefId, slateId, selectionId, blueprintId, outlineId, deltaId, nextSequence, timestamp, input.storyRunId);
      if (input.nextStatus) {
        this.database.prepare(`
          INSERT INTO run_events (
            event_id, story_run_id, run_sequence, previous_status, next_status,
            actor_type, actor_name, triggering_artifact_id, summary, created_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).run(
          randomUUID(), input.storyRunId, nextSequence, run.status, nextStatus,
          input.producer.type, input.producer.name, artifactId, input.eventSummary ?? 'Artifact saved', timestamp,
        );
      }
      return artifactFromRow(this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [artifactId])!);
    });
  }

  async getArtifact(artifactId: string): Promise<ArtifactEnvelope | null> {
    assertUuid(artifactId, 'artifactId');
    const row = this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [artifactId]);
    return row ? artifactFromRow(row) : null;
  }

  async getArtifactLineage(artifactId: string): Promise<ArtifactLineageLink[]> {
    assertUuid(artifactId, 'artifactId');
    const rows = this.allRows(`
      SELECT 'parent' AS direction, e.relationship_type, a.artifact_id, a.kind,
             a.logical_key, a.version, a.content_hash, a.lifecycle_status
      FROM artifact_edges e JOIN artifacts a ON a.artifact_id = e.parent_artifact_id
      WHERE e.child_artifact_id = ?
      UNION ALL
      SELECT 'child' AS direction, e.relationship_type, a.artifact_id, a.kind,
             a.logical_key, a.version, a.content_hash, a.lifecycle_status
      FROM artifact_edges e JOIN artifacts a ON a.artifact_id = e.child_artifact_id
      WHERE e.parent_artifact_id = ?
      ORDER BY direction, logical_key, version
    `, [artifactId, artifactId]);
    return rows.map((row) => ({
      direction: String(row.direction) as ArtifactLineageLink['direction'],
      relationship: String(row.relationship_type) as ArtifactRelationship,
      artifactId: String(row.artifact_id),
      kind: String(row.kind) as ArtifactKind,
      logicalKey: String(row.logical_key),
      version: Number(row.version),
      contentHash: String(row.content_hash),
      lifecycleStatus: String(row.lifecycle_status) as ArtifactLifecycle,
    }));
  }

  async listDescendantArtifactIds(artifactId: string, lifecycleStatus?: ArtifactLifecycle): Promise<string[]> {
    assertUuid(artifactId, 'artifactId');
    return this.descendants(artifactId, lifecycleStatus).map((row) => String(row.artifact_id));
  }

  async listRunArtifacts(storyRunId: string, options: { includeInactive?: boolean } = {}): Promise<ArtifactEnvelope[]> {
    assertUuid(storyRunId, 'storyRunId');
    const rows = options.includeInactive
      ? this.allRows('SELECT * FROM artifacts WHERE story_run_id = ? ORDER BY created_at, artifact_id', [storyRunId])
      : this.allRows("SELECT * FROM artifacts WHERE story_run_id = ? AND lifecycle_status = 'active' ORDER BY created_at, artifact_id", [storyRunId]);
    return rows.map(artifactFromRow);
  }

  async getRun(storyRunId: string): Promise<StoryRunRecord | null> {
    assertUuid(storyRunId, 'storyRunId');
    const row = this.getRow('SELECT * FROM story_runs WHERE story_run_id = ?', [storyRunId]);
    return row ? runFromRow(row) : null;
  }

  async patchArtifact(input: {
    artifactId: string;
    expectedHash: string;
    operations: JsonPatchOperation[];
    producerName?: string;
  }): Promise<{ artifact: ArtifactEnvelope; invalidatedFromStatus: StoryRunStatus; invalidatedArtifactIds: string[] }> {
    const current = await this.getArtifact(input.artifactId);
    if (!current) throw new Error('Artifact not found');
    if (!current.storyRunId) throw new Error('World-level artifacts cannot be edited');
    if (current.lifecycleStatus !== 'active' || current.contentHash !== input.expectedHash) throw new Error('Artifact edit conflict: expected hash is no longer active');
    if (NON_EDITABLE_ARTIFACT_KINDS.has(current.kind)) throw new Error(`${current.kind} artifacts are immutable`);
    if (input.operations.length === 0) throw new Error('At least one JSON Patch operation is required');
    const patched = applyArtifactPatch(current.content, input.operations);
    const validated = parseContent(this.validator, current.kind, current.schemaVersion, patched);
    const nextStatus = statusAfterArtifactEdit(current.kind);
    const activeDescendants = await this.listDescendantArtifactIds(current.artifactId, 'active');
    const artifact = await this.saveArtifact({
      storyRunId: current.storyRunId,
      branchId: current.branchId,
      kind: current.kind,
      schemaVersion: current.schemaVersion,
      logicalKey: current.logicalKey,
      content: validated,
      producer: { type: 'human', name: input.producerName ?? 'writer' },
      supersedesArtifactId: current.artifactId,
      expectedSupersededHash: input.expectedHash,
      nextStatus,
      eventSummary: `Writer edited ${current.logicalKey}; descendants invalidated`,
    });
    return { artifact, invalidatedFromStatus: nextStatus, invalidatedArtifactIds: activeDescendants };
  }

  async selectPitch(input: {
    storyRunId: string;
    pitchSlateArtifactId: string;
    expectedSlateHash: string;
    pitchId: string;
    producerName?: string;
  }): Promise<ArtifactEnvelope> {
    const slate = await this.getArtifact(input.pitchSlateArtifactId);
    if (!slate || slate.storyRunId !== input.storyRunId || slate.kind !== 'pitch.slate') throw new Error('Pitch slate does not belong to the story run');
    if (slate.lifecycleStatus !== 'active' || slate.contentHash !== input.expectedSlateHash) throw new Error('Pitch slate selection conflict');
    const activeArtifacts = await this.listRunArtifacts(input.storyRunId);
    const certification = activeArtifacts.find((artifact) => {
      if (artifact.kind !== 'review.pitch-continuity' || artifact.producer.type !== 'agent') return false;
      const content = artifact.content as { targetArtifactId?: JsonValue; targetContentHash?: JsonValue; verdict?: JsonValue };
      return content.targetArtifactId === slate.artifactId && content.targetContentHash === slate.contentHash && content.verdict === 'pass';
    });
    if (!certification) throw new Error('Pitch slate requires an exact passing agent continuity review before selection');
    const lineage = await this.getArtifactLineage(certification.artifactId);
    if (!lineage.some((link) => link.direction === 'parent' && link.relationship === 'reviews' && link.artifactId === slate.artifactId)) {
      throw new Error('Pitch continuity review is missing exact reviews lineage to the slate');
    }
    const pitches = (slate.content as { pitches?: JsonValue }).pitches;
    if (!Array.isArray(pitches) || !pitches.some((pitch) => pitch && typeof pitch === 'object' && !Array.isArray(pitch) && pitch.id === input.pitchId)) {
      throw new Error(`Pitch ${input.pitchId} is not present in the selected slate`);
    }
    return this.saveArtifact({
      storyRunId: input.storyRunId,
      kind: 'decision.pitch-selection',
      logicalKey: 'decision/pitch-selection',
      content: {
        pitchId: input.pitchId,
        pitchSlateArtifactId: slate.artifactId,
        pitchSlateHash: slate.contentHash,
        selectedAt: now(),
      },
      producer: { type: 'human', name: input.producerName ?? 'writer' },
      parents: [
        { artifactId: slate.artifactId, relationship: 'consumes' },
        { artifactId: certification.artifactId, relationship: 'consumes' },
      ],
      expectedStatus: 'awaiting_pitch',
      nextStatus: 'planning',
      eventSummary: `Writer selected pitch ${input.pitchId}`,
    });
  }

  async transitionRun(input: {
    storyRunId: string;
    expectedStatus?: StoryRunStatus;
    nextStatus: StoryRunStatus;
    actor: ArtifactProducer;
    triggeringArtifactId?: string;
    summary: string;
  }): Promise<StoryRunRecord> {
    if (['ready_for_promotion', 'promoted', 'stale'].includes(input.nextStatus)) throw new Error(`${input.nextStatus} is reserved for deterministic canon operations`);
    return this.transaction(() => {
      const row = this.getRow('SELECT * FROM story_runs WHERE story_run_id = ?', [input.storyRunId]);
      if (!row) throw new Error('Story run transition conflict');
      const run = runFromRow(row);
      if (input.expectedStatus && run.status !== input.expectedStatus) throw new Error('Story run transition conflict');
      if (['promoted', 'stale'].includes(run.status)) throw new Error('Story run transition conflict');
      const sequence = Number(row.event_sequence) + 1;
      const timestamp = now();
      this.database.prepare('UPDATE story_runs SET status = ?, event_sequence = ?, updated_at = ? WHERE story_run_id = ?')
        .run(input.nextStatus, sequence, timestamp, input.storyRunId);
      this.database.prepare(`
        INSERT INTO run_events (
          event_id, story_run_id, run_sequence, previous_status, next_status,
          actor_type, actor_name, triggering_artifact_id, summary, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        randomUUID(), input.storyRunId, sequence, run.status, input.nextStatus,
        input.actor.type, input.actor.name, input.triggeringArtifactId ?? null, input.summary, timestamp,
      );
      return runFromRow(this.getRow('SELECT * FROM story_runs WHERE story_run_id = ?', [input.storyRunId])!);
    });
  }

  async recordAgentExecution(input: AgentExecutionInput): Promise<string> {
    const executionId = input.executionId ?? randomUUID();
    this.database.prepare(`
      INSERT INTO agent_executions (
        execution_id, story_run_id, agent_name, eve_child_session_id, model_id, gateway,
        input_artifact_ids, output_artifact_ids, prompt_revision, skill_revision,
        started_at, completed_at, input_tokens, output_tokens, cost_usd, status, error_summary, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(execution_id) DO UPDATE SET
        eve_child_session_id = COALESCE(excluded.eve_child_session_id, agent_executions.eve_child_session_id),
        model_id = COALESCE(excluded.model_id, agent_executions.model_id),
        gateway = COALESCE(excluded.gateway, agent_executions.gateway),
        input_artifact_ids = excluded.input_artifact_ids,
        output_artifact_ids = excluded.output_artifact_ids,
        prompt_revision = COALESCE(excluded.prompt_revision, agent_executions.prompt_revision),
        skill_revision = COALESCE(excluded.skill_revision, agent_executions.skill_revision),
        completed_at = excluded.completed_at,
        input_tokens = excluded.input_tokens,
        output_tokens = excluded.output_tokens,
        cost_usd = excluded.cost_usd,
        status = excluded.status,
        error_summary = excluded.error_summary
    `).run(
      executionId,
      input.storyRunId,
      input.agentName,
      input.eveChildSessionId ?? null,
      input.modelId ?? null,
      input.gateway ?? null,
      JSON.stringify(input.inputArtifactIds),
      JSON.stringify(input.outputArtifactIds),
      input.promptRevision ?? null,
      input.skillRevision ?? null,
      input.startedAt,
      input.completedAt ?? null,
      input.inputTokens ?? null,
      input.outputTokens ?? null,
      input.costUsd ?? null,
      input.status,
      sanitizeErrorSummary(input.errorSummary) ?? null,
      now(),
    );
    return executionId;
  }

  async bootstrapCanon(input: CanonBootstrapInput): Promise<{ revision: number; snapshotArtifactId: string; canonHash: string; created: boolean }> {
    const foundation = parseContent(this.validator, 'world.foundation', 1, input.world);
    const snapshot = parseContent(this.validator, 'canon.snapshot', 1, input.normalizedSnapshot);
    const foundationHash = artifactContentHash(foundation);
    const snapshotHash = artifactContentHash(snapshot);
    return this.transaction(() => {
      const existing = this.getRow('SELECT * FROM worlds WHERE world_id = ?', [SHARED_WORLD_ID]);
      if (existing) {
        const storedFoundation = this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [String(existing.foundation_artifact_id)]);
        if (!storedFoundation || storedFoundation.content_hash !== foundationHash) {
          throw new Error('The shared world is already initialized from a different foundation');
        }
        return {
          revision: Number(existing.current_canon_revision),
          snapshotArtifactId: String(existing.current_canon_snapshot_artifact_id),
          canonHash: String(existing.current_canon_hash),
          created: false,
        };
      }
      const foundationId = randomUUID();
      const snapshotId = randomUUID();
      const producerName = input.producerName ?? 'bootstrap-canon';
      const timestamp = now();
      this.database.prepare(`
        INSERT INTO worlds (
          world_id, foundation_artifact_id, current_canon_revision,
          current_canon_snapshot_artifact_id, current_canon_hash, created_at, updated_at
        ) VALUES (?, ?, 1, ?, ?, ?, ?)
      `).run(SHARED_WORLD_ID, foundationId, snapshotId, snapshotHash, timestamp, timestamp);
      this.insertArtifact({
        artifactId: foundationId,
        storyRunId: null,
        branchId: null,
        kind: 'world.foundation',
        schemaVersion: 1,
        logicalKey: 'world/foundation',
        version: 1,
        canonRevision: 1,
        canonSnapshotArtifactId: snapshotId,
        content: foundation,
        contentHash: foundationHash,
        producer: { type: 'tool', name: producerName },
        createdAt: timestamp,
      });
      this.insertArtifact({
        artifactId: snapshotId,
        storyRunId: null,
        branchId: null,
        kind: 'canon.snapshot',
        schemaVersion: 1,
        logicalKey: 'canon/snapshot/1',
        version: 1,
        canonRevision: 1,
        canonSnapshotArtifactId: snapshotId,
        content: snapshot,
        contentHash: snapshotHash,
        producer: { type: 'tool', name: producerName },
        createdAt: timestamp,
      });
      this.database.prepare(`
        INSERT INTO artifact_edges (parent_artifact_id, child_artifact_id, relationship_type, created_at)
        VALUES (?, ?, 'derives-from', ?)
      `).run(foundationId, snapshotId, timestamp);
      this.database.prepare(`
        INSERT INTO canon_revisions (
          world_id, revision, parent_revision, snapshot_artifact_id, delta_artifact_id,
          source_story_run_id, final_outline_artifact_id, canon_hash, committed_at
        ) VALUES (?, 1, NULL, ?, NULL, NULL, NULL, ?, ?)
      `).run(SHARED_WORLD_ID, snapshotId, snapshotHash, timestamp);
      return { revision: 1, snapshotArtifactId: snapshotId, canonHash: snapshotHash, created: true };
    });
  }

  async promoteOutline(input: PromotionInput): Promise<ArtifactEnvelope> {
    assertUuid(input.storyRunId, 'storyRunId');
    assertUuid(input.finalOutlineArtifactId, 'finalOutlineArtifactId');
    assertUuid(input.canonDeltaArtifactId, 'canonDeltaArtifactId');
    const snapshotContent = parseContent(this.validator, 'canon.snapshot', 1, input.nextSnapshotContent);
    const result = this.transaction<{ receipt?: ArtifactEnvelope; stale?: true }>(() => {
      const prior = this.getRow(
        "SELECT * FROM artifacts WHERE story_run_id = ? AND kind = 'canon.commit-receipt' AND lifecycle_status = 'active' ORDER BY version DESC LIMIT 1",
        [input.storyRunId],
      );
      if (prior) return { receipt: artifactFromRow(prior) };

      const runRow = this.getRow('SELECT * FROM story_runs WHERE story_run_id = ?', [input.storyRunId]);
      if (!runRow) throw new Error('Story run not found');
      const world = this.getRow('SELECT * FROM worlds WHERE world_id = ?', [SHARED_WORLD_ID]);
      if (!world) throw new Error('Shared world not found');
      const run = runFromRow(runRow);
      if (run.status === 'ready_for_promotion' && run.baseCanonRevision !== Number(world.current_canon_revision)) {
        const sequence = Number(runRow.event_sequence) + 1;
        const timestamp = now();
        this.database.prepare("UPDATE story_runs SET status = 'stale', event_sequence = ?, updated_at = ? WHERE story_run_id = ?")
          .run(sequence, timestamp, input.storyRunId);
        this.database.prepare(`
          INSERT INTO run_events (
            event_id, story_run_id, run_sequence, previous_status, next_status,
            actor_type, actor_name, triggering_artifact_id, summary, created_at
          ) VALUES (?, ?, ?, 'ready_for_promotion', 'stale', 'tool', ?, ?, ?, ?)
        `).run(
          randomUUID(), input.storyRunId, sequence, input.producerName ?? 'promote-outline',
          input.finalOutlineArtifactId, 'Promotion rejected because canon head advanced', timestamp,
        );
        return { stale: true };
      }
      if (
        run.status !== 'ready_for_promotion'
        || run.finalOutlineArtifactId !== input.finalOutlineArtifactId
        || run.canonDeltaArtifactId !== input.canonDeltaArtifactId
      ) throw new Error('Promotion gates failed: run pointers are not ready');

      const outline = this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [input.finalOutlineArtifactId]);
      const delta = this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [input.canonDeltaArtifactId]);
      if (
        !outline || outline.story_run_id !== input.storyRunId || outline.kind !== 'outline.final' || outline.lifecycle_status !== 'active'
        || !delta || delta.story_run_id !== input.storyRunId || delta.kind !== 'canon.delta' || delta.lifecycle_status !== 'active'
      ) throw new Error('Promotion gates failed: outline or delta is missing or inactive');

      const reviews = this.allRows(`
        SELECT review.* FROM artifact_edges edge
        JOIN artifacts review ON review.artifact_id = edge.child_artifact_id
        WHERE edge.parent_artifact_id = ? AND edge.relationship_type = 'reviews'
          AND review.lifecycle_status = 'active' AND review.producer_type = 'agent'
          AND review.kind IN ('review.continuity', 'review.narrative', 'review.theme-pacing')
      `, [input.finalOutlineArtifactId]);
      const reviewKinds = new Set<string>();
      for (const review of reviews) {
        const content = parseStoredJson(review.content) as Record<string, JsonValue>;
        if (
          content.targetArtifactId === input.finalOutlineArtifactId
          && content.targetContentHash === outline.content_hash
          && content.verdict === 'pass'
        ) reviewKinds.add(String(review.kind));
      }
      if (!['review.continuity', 'review.narrative', 'review.theme-pacing'].every((kind) => reviewKinds.has(kind))) {
        throw new Error('Promotion gates failed: three exact passing agent reviews are required');
      }

      const candidateRevision = Number(world.current_canon_revision) + 1;
      if (
        !snapshotContent || typeof snapshotContent !== 'object' || Array.isArray(snapshotContent)
        || snapshotContent.revision !== candidateRevision
      ) throw new Error(`Next canon snapshot must be revision ${candidateRevision}`);
      const deltaContent = parseStoredJson(delta.content) as Record<string, JsonValue>;
      const deltaEvent = deltaContent.event;
      const canonEventId = deltaEvent && typeof deltaEvent === 'object' && !Array.isArray(deltaEvent) && typeof deltaEvent.id === 'string'
        ? deltaEvent.id
        : null;
      if (!canonEventId) throw new Error('Canon delta does not contain a valid event ID');

      const snapshotId = randomUUID();
      const receiptId = randomUUID();
      const timestamp = now();
      const snapshotHash = artifactContentHash(snapshotContent);
      const producerName = input.producerName ?? 'promote-outline';
      const receiptContent = parseContent(this.validator, 'canon.commit-receipt', 1, {
        worldId: SHARED_WORLD_ID,
        storyRunId: input.storyRunId,
        previousRevision: Number(world.current_canon_revision),
        revision: candidateRevision,
        snapshotArtifactId: snapshotId,
        snapshotHash,
        finalOutlineArtifactId: input.finalOutlineArtifactId,
        deltaArtifactId: input.canonDeltaArtifactId,
        eventId: canonEventId,
        committedAt: timestamp,
      });
      this.insertArtifact({
        artifactId: snapshotId,
        storyRunId: null,
        branchId: null,
        kind: 'canon.snapshot',
        schemaVersion: 1,
        logicalKey: `canon/snapshot/${candidateRevision}`,
        version: candidateRevision,
        canonRevision: candidateRevision,
        canonSnapshotArtifactId: snapshotId,
        content: snapshotContent,
        contentHash: snapshotHash,
        producer: { type: 'tool', name: producerName },
        createdAt: timestamp,
      });
      this.database.prepare(`
        INSERT INTO canon_revisions (
          world_id, revision, parent_revision, snapshot_artifact_id, delta_artifact_id,
          source_story_run_id, final_outline_artifact_id, canon_hash, committed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        SHARED_WORLD_ID, candidateRevision, Number(world.current_canon_revision), snapshotId,
        input.canonDeltaArtifactId, input.storyRunId, input.finalOutlineArtifactId, snapshotHash, timestamp,
      );
      const edge = this.database.prepare(`
        INSERT INTO artifact_edges (parent_artifact_id, child_artifact_id, relationship_type, created_at)
        VALUES (?, ?, ?, ?)
      `);
      edge.run(input.finalOutlineArtifactId, input.canonDeltaArtifactId, 'promotes', timestamp);
      edge.run(input.canonDeltaArtifactId, snapshotId, 'derives-from', timestamp);
      this.database.prepare(`
        UPDATE worlds SET current_canon_revision = ?, current_canon_snapshot_artifact_id = ?,
          current_canon_hash = ?, updated_at = ? WHERE world_id = ?
      `).run(candidateRevision, snapshotId, snapshotHash, timestamp, SHARED_WORLD_ID);
      const sequence = Number(runRow.event_sequence) + 1;
      this.database.prepare("UPDATE story_runs SET status = 'promoted', event_sequence = ?, updated_at = ? WHERE story_run_id = ?")
        .run(sequence, timestamp, input.storyRunId);
      this.insertArtifact({
        artifactId: receiptId,
        storyRunId: input.storyRunId,
        branchId: null,
        kind: 'canon.commit-receipt',
        schemaVersion: 1,
        logicalKey: 'canon/commit-receipt',
        version: 1,
        canonRevision: candidateRevision,
        canonSnapshotArtifactId: snapshotId,
        content: receiptContent,
        contentHash: artifactContentHash(receiptContent),
        producer: { type: 'tool', name: producerName },
        createdAt: timestamp,
      });
      edge.run(snapshotId, receiptId, 'derives-from', timestamp);
      this.database.prepare(`
        INSERT INTO run_events (
          event_id, story_run_id, run_sequence, previous_status, next_status,
          actor_type, actor_name, triggering_artifact_id, summary, created_at
        ) VALUES (?, ?, ?, 'ready_for_promotion', 'promoted', 'tool', ?, ?, ?, ?)
      `).run(
        randomUUID(), input.storyRunId, sequence, producerName, receiptId,
        `Outline promoted to canon revision ${candidateRevision}`, timestamp,
      );
      return { receipt: artifactFromRow(this.getRow('SELECT * FROM artifacts WHERE artifact_id = ?', [receiptId])!) };
    });
    if (result.stale) throw new Error('Promotion rejected because the story run is stale');
    if (!result.receipt) throw new Error('Promotion failed without a receipt');
    return result.receipt;
  }
}
