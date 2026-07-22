import { createHash, randomUUID } from 'node:crypto';
import { z } from 'zod';
import { assertCanon, slugify, WorldSchema, type World } from './domain.js';
import {
  CanonDeltaSchema,
  CanonDossierSchema,
  CanonFactSchema,
  CharacterPlanSchema,
  ConflictPlanSchema,
  ContinuityReviewSchemaV2,
  NarrativeReviewSchema,
  OutlineBlueprintSchema,
  PitchSeedSchema,
  PitchSlateSchema,
  PlotPlanSchema,
  SceneOutlineSchema,
  StoryBriefSchema,
  StoryOutlineSchema,
  ThemePacingPlanSchema,
  WorldIntegrationPlanSchema,
  type CanonDelta,
  type CanonFact,
  type StoryOutline,
} from './story-domain.js';

export const SHARED_WORLD_ID = 'shared-world' as const;

export const ArtifactKindSchema = z.enum([
  'world.foundation',
  'prompt.original',
  'prompt.clarification',
  'story.brief',
  'canon.dossier',
  'prompt.conflict-report',
  'pitch.seed',
  'pitch.character-plan',
  'pitch.conflict-plan',
  'pitch.world-plan',
  'pitch.slate',
  'review.pitch-continuity',
  'decision.pitch-selection',
  'plan.character',
  'plan.conflict',
  'plan.world',
  'plan.theme-pacing',
  'plan.plot',
  'outline.blueprint',
  'outline.scenes',
  'outline.final',
  'review.continuity',
  'review.narrative',
  'review.theme-pacing',
  'canon.delta',
  'canon.snapshot',
  'canon.commit-receipt',
  'export.writer-packet',
]);

export const ArtifactLifecycleSchema = z.enum(['active', 'superseded', 'stale', 'rejected']);
export const ArtifactEdgeTypeSchema = z.enum(['consumes', 'derives-from', 'reviews', 'supersedes', 'promotes', 'renders']);
export const ProducerTypeSchema = z.enum(['human', 'agent', 'tool']);
export const StoryRunStatusSchema = z.enum([
  'analyzing',
  'needs_clarification',
  'building_pitches',
  'awaiting_pitch',
  'planning',
  'reviewing',
  'needs_revision',
  'ready_for_promotion',
  'promoted',
  'stale',
  'failed',
]);

export const ArtifactProducerSchema = z.object({
  type: ProducerTypeSchema,
  name: z.string().min(1),
  modelId: z.string().min(1).optional(),
  gateway: z.literal('openrouter').optional(),
  eveSessionId: z.string().min(1).optional(),
});

export const ArtifactEnvelopeSchema = z.object({
  artifactId: z.string().uuid(),
  worldId: z.literal(SHARED_WORLD_ID),
  storyRunId: z.string().uuid().nullable(),
  branchId: z.enum(['A', 'B', 'C']).nullable(),
  kind: ArtifactKindSchema,
  schemaVersion: z.number().int().positive(),
  logicalKey: z.string().min(1),
  version: z.number().int().positive(),
  canonRevision: z.number().int().positive(),
  canonSnapshotArtifactId: z.string().uuid(),
  content: z.unknown(),
  contentHash: z.string().regex(/^[a-f0-9]{64}$/),
  producer: ArtifactProducerSchema,
  createdAt: z.string().datetime(),
});

export const EntityStateSchema = z.object({
  entityId: z.string().min(1),
  state: z.string(),
  lastChangedEventId: z.string().nullable(),
});

export const CanonSnapshotSchema = z.object({
  worldId: z.literal(SHARED_WORLD_ID),
  revision: z.number().int().positive(),
  world: WorldSchema,
  facts: z.array(CanonFactSchema),
  timeline: z.array(CanonDeltaSchema.shape.event),
  entityStates: z.array(EntityStateSchema),
});

export const CanonCommitReceiptSchema = z.object({
  worldId: z.literal(SHARED_WORLD_ID),
  storyRunId: z.string().uuid(),
  previousRevision: z.number().int().positive(),
  revision: z.number().int().positive(),
  snapshotArtifactId: z.string().uuid(),
  snapshotHash: z.string().regex(/^[a-f0-9]{64}$/),
  deltaArtifactId: z.string().uuid(),
  finalOutlineArtifactId: z.string().uuid(),
  eventId: z.string().min(1),
  committedAt: z.string().datetime(),
});

export const PitchSelectionSchema = z.object({
  pitchSlateArtifactId: z.string().uuid(),
  pitchSlateHash: z.string().regex(/^[a-f0-9]{64}$/),
  pitchId: z.string().regex(/^pitch-[abc]$/),
  selectedAt: z.string().datetime().optional(),
});

export const WriterPacketSchema = z.object({
  filename: z.string().regex(/^[a-zA-Z0-9][a-zA-Z0-9._-]*\.md$/),
  markdown: z.string().min(1),
  sourceArtifactIds: z.array(z.string().uuid()).min(1),
  rendererVersion: z.literal(1),
});

export const PromptOriginalSchema = z.object({ text: z.string().min(1) });
export const PromptClarificationSchema = z.object({
  text: z.string().min(1),
  conflictArtifactId: z.string().uuid().optional(),
});

export const ClarificationRequiredResultSchema = z.object({
    type: z.literal('clarification-required'),
    storyRunId: z.string().uuid(),
    conflictArtifactId: z.string().uuid(),
    status: z.literal('needs_clarification'),
  });
export const PitchSlateReadyResultSchema = z.object({
    type: z.literal('pitch-slate-ready'),
    storyRunId: z.string().uuid(),
    pitchSlateArtifactId: z.string().uuid(),
    status: z.literal('awaiting_pitch'),
  });
export const EditReceiptResultSchema = z.object({
    type: z.literal('edit-receipt'),
    storyRunId: z.string().uuid(),
    previousArtifactId: z.string().uuid(),
    artifactId: z.string().uuid(),
    contentHash: z.string().regex(/^[a-f0-9]{64}$/),
    invalidatedArtifactIds: z.array(z.string().uuid()),
    status: StoryRunStatusSchema,
  });
export const ProvisionalOutlineResultSchema = z.object({
    type: z.literal('provisional-outline'),
    storyRunId: z.string().uuid(),
    finalOutlineArtifactId: z.string().uuid(),
    status: z.literal('ready_for_promotion'),
  });
export const PromotionReceiptResultSchema = z.object({
    type: z.literal('promotion-receipt'),
    receipt: CanonCommitReceiptSchema,
    status: z.literal('promoted'),
  });
export const MarkdownExportResultSchema = z.object({
    type: z.literal('markdown-export'),
    storyRunId: z.string().uuid(),
    exportArtifactId: z.string().uuid(),
    filename: z.string().endsWith('.md'),
    markdown: z.string().min(1),
  });

export const StoryOperationResultSchema = z.discriminatedUnion('type', [
  ClarificationRequiredResultSchema,
  PitchSlateReadyResultSchema,
  EditReceiptResultSchema,
  ProvisionalOutlineResultSchema,
  PromotionReceiptResultSchema,
  MarkdownExportResultSchema,
]);

export type ArtifactKind = z.infer<typeof ArtifactKindSchema>;
export type ArtifactLifecycle = z.infer<typeof ArtifactLifecycleSchema>;
export type ArtifactEdgeType = z.infer<typeof ArtifactEdgeTypeSchema>;
export type StoryRunStatus = z.infer<typeof StoryRunStatusSchema>;
export type ArtifactProducer = z.infer<typeof ArtifactProducerSchema>;
export type ArtifactEnvelope<T = unknown> = Omit<z.infer<typeof ArtifactEnvelopeSchema>, 'content'> & { content: T };
export type CanonSnapshot = z.infer<typeof CanonSnapshotSchema>;
export type CanonCommitReceipt = z.infer<typeof CanonCommitReceiptSchema>;

type AnySchema = z.ZodType;

export const ARTIFACT_SCHEMAS: Record<ArtifactKind, AnySchema> = {
  'world.foundation': WorldSchema,
  'prompt.original': PromptOriginalSchema,
  'prompt.clarification': PromptClarificationSchema,
  'story.brief': StoryBriefSchema,
  'canon.dossier': CanonDossierSchema,
  'prompt.conflict-report': WorldIntegrationPlanSchema.extend({ kind: z.literal('prompt.conflict-report') }),
  'pitch.seed': PitchSeedSchema,
  'pitch.character-plan': CharacterPlanSchema.extend({
    kind: z.literal('pitch.character-plan'),
    branchId: z.enum(['A', 'B', 'C']),
  }),
  'pitch.conflict-plan': ConflictPlanSchema.extend({
    kind: z.literal('pitch.conflict-plan'),
    branchId: z.enum(['A', 'B', 'C']),
  }),
  'pitch.world-plan': WorldIntegrationPlanSchema.extend({
    kind: z.literal('pitch.world-plan'),
    branchId: z.enum(['A', 'B', 'C']),
  }),
  'pitch.slate': PitchSlateSchema,
  'review.pitch-continuity': ContinuityReviewSchemaV2.extend({ kind: z.literal('review.pitch-continuity') }),
  'decision.pitch-selection': PitchSelectionSchema,
  'plan.character': CharacterPlanSchema.extend({ kind: z.literal('plan.character') }),
  'plan.conflict': ConflictPlanSchema.extend({ kind: z.literal('plan.conflict') }),
  'plan.world': WorldIntegrationPlanSchema.extend({ kind: z.literal('plan.world') }),
  'plan.theme-pacing': ThemePacingPlanSchema.extend({
    kind: z.literal('plan.theme-pacing'),
    mode: z.literal('plan'),
  }),
  'plan.plot': PlotPlanSchema,
  'outline.blueprint': OutlineBlueprintSchema,
  'outline.scenes': SceneOutlineSchema,
  'outline.final': StoryOutlineSchema,
  'review.continuity': ContinuityReviewSchemaV2.extend({ kind: z.literal('review.continuity') }),
  'review.narrative': NarrativeReviewSchema,
  'review.theme-pacing': ThemePacingPlanSchema.extend({
    kind: z.literal('review.theme-pacing'),
    mode: z.literal('review'),
    targetArtifactId: z.string().uuid(),
    targetContentHash: z.string().regex(/^[a-f0-9]{64}$/),
    verdict: z.enum(['pass', 'block']),
  }),
  'canon.delta': CanonDeltaSchema,
  'canon.snapshot': CanonSnapshotSchema,
  'canon.commit-receipt': CanonCommitReceiptSchema,
  'export.writer-packet': WriterPacketSchema,
};

export const NON_EDITABLE_ARTIFACT_KINDS = new Set<ArtifactKind>([
  'world.foundation',
  'canon.delta',
  'canon.snapshot',
  'canon.commit-receipt',
  'export.writer-packet',
]);

export function validateArtifactContent<T = unknown>(kind: ArtifactKind, content: unknown): T {
  return ARTIFACT_SCHEMAS[kind].parse(content) as T;
}

function canonicalJson(value: unknown): string {
  if (value === null) return 'null';
  if (typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new TypeError('Artifact content cannot contain non-finite numbers.');
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item === undefined ? null : item)).join(',')}]`;
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const entries = Object.keys(record)
      .filter((key) => record[key] !== undefined)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(record[key])}`);
    return `{${entries.join(',')}}`;
  }
  throw new TypeError(`Unsupported artifact content value: ${typeof value}`);
}

export function artifactContentHash(content: unknown): string {
  return createHash('sha256').update(canonicalJson(content)).digest('hex');
}

function shortHash(value: unknown): string {
  return artifactContentHash(value).slice(0, 12);
}

export function normalizeCanonFacts(world: World, timeline: CanonSnapshot['timeline'], entityStates: CanonSnapshot['entityStates']): CanonFact[] {
  const facts: CanonFact[] = [{ ref: 'world:foundation', category: 'world', text: `${world.title}: ${world.premise}` }];
  for (const law of world.laws) facts.push({ ref: `law:${shortHash(law)}`, category: 'law', text: law });
  for (const item of world.history) {
    facts.push({
      ref: `history:${slugify(item.era)}:${shortHash(item)}`,
      category: 'history',
      text: `${item.era}: ${item.event} Consequence: ${item.consequence}`,
    });
  }
  for (const entity of world.entities) {
    facts.push({ ref: `entity:${entity.id}`, category: 'entity', text: `${entity.name}: ${entity.summary} Wants: ${entity.wants}` });
  }
  for (const relationship of world.relationships) {
    facts.push({
      ref: `relationship:${relationship.from}:${relationship.type}:${relationship.to}:${shortHash(relationship.detail)}`,
      category: 'relationship',
      text: `${relationship.from} ${relationship.type} ${relationship.to}: ${relationship.detail}`,
    });
  }
  for (const event of timeline) {
    facts.push({ ref: `event:${event.id}`, category: 'event', text: `${event.title}: ${event.summary}` });
  }
  for (const state of entityStates) {
    facts.push({ ref: `state:${state.entityId}:${shortHash(state.state)}`, category: 'state', text: `${state.entityId}: ${state.state}` });
  }
  return facts;
}

export function createInitialCanonSnapshot(worldInput: unknown): CanonSnapshot {
  const world = assertCanon(WorldSchema.parse(worldInput));
  const entityStates = world.entities.map((entity) => ({
    entityId: entity.id,
    state: entity.summary,
    lastChangedEventId: null,
  }));
  const timeline: CanonSnapshot['timeline'] = [];
  return CanonSnapshotSchema.parse({
    worldId: SHARED_WORLD_ID,
    revision: 1,
    world,
    timeline,
    entityStates,
    facts: normalizeCanonFacts(world, timeline, entityStates),
  });
}

export function applyCanonDelta(snapshotInput: unknown, deltaInput: unknown): CanonSnapshot {
  const snapshot = CanonSnapshotSchema.parse(snapshotInput);
  const delta = CanonDeltaSchema.parse(deltaInput);
  const existingEntities = new Map(snapshot.world.entities.map((entity) => [entity.id, entity]));

  for (const entity of delta.newEntities) {
    if (existingEntities.has(entity.id)) throw new Error(`Canon delta duplicates entity: ${entity.id}`);
    existingEntities.set(entity.id, entity);
  }

  const lastEventId = snapshot.timeline.at(-1)?.id ?? null;
  if (delta.event.occursAfterEventId !== lastEventId) {
    throw new Error(`Canon event must occur after ${lastEventId ?? 'the foundation'}, received ${delta.event.occursAfterEventId ?? 'null'}.`);
  }
  if (snapshot.timeline.some((event) => event.id === delta.event.id)) throw new Error(`Duplicate canon event: ${delta.event.id}`);

  for (const participantId of delta.event.participantEntityIds) {
    if (!existingEntities.has(participantId)) throw new Error(`Unknown canon event participant: ${participantId}`);
  }

  const relationships = [...snapshot.world.relationships];
  for (const relationship of delta.newRelationships) {
    if (!existingEntities.has(relationship.from) || !existingEntities.has(relationship.to)) {
      throw new Error(`New relationship contains unknown endpoint: ${relationship.from} -> ${relationship.to}`);
    }
    if (relationships.some((item) => item.from === relationship.from && item.to === relationship.to && item.type === relationship.type)) {
      throw new Error(`Duplicate relationship: ${relationship.from} ${relationship.type} ${relationship.to}`);
    }
    relationships.push(relationship);
  }

  const states = new Map(snapshot.entityStates.map((state) => [state.entityId, { ...state }]));
  for (const entity of delta.newEntities) {
    states.set(entity.id, { entityId: entity.id, state: entity.summary, lastChangedEventId: delta.event.id });
  }
  for (const change of delta.entityStateChanges) {
    const current = states.get(change.entityId);
    if (!current) throw new Error(`Unknown entity state target: ${change.entityId}`);
    if (current.state !== change.before) throw new Error(`State mismatch for ${change.entityId}; expected exactly "${current.state}".`);
    states.set(change.entityId, { entityId: change.entityId, state: change.after, lastChangedEventId: delta.event.id });
  }

  const world = assertCanon({
    ...snapshot.world,
    entities: [...existingEntities.values()],
    relationships,
  });
  const timeline = [...snapshot.timeline, delta.event];
  const entityStates = [...states.values()];
  return CanonSnapshotSchema.parse({
    worldId: SHARED_WORLD_ID,
    revision: snapshot.revision + 1,
    world,
    timeline,
    entityStates,
    facts: normalizeCanonFacts(world, timeline, entityStates),
  });
}

export function validateStoryOutline(outlineInput: unknown, snapshotInput: unknown): string[] {
  const outline = StoryOutlineSchema.parse(outlineInput);
  const snapshot = CanonSnapshotSchema.parse(snapshotInput);
  const issues: string[] = [];
  const canonRefs = new Set(snapshot.facts.map((fact) => fact.ref));
  const existingEntities = new Set(snapshot.world.entities.map((entity) => entity.id));
  for (const entity of outline.canonDelta.newEntities) existingEntities.add(entity.id);

  const sceneIds = new Set<string>();
  const setupIds = new Set<string>();
  const payoffIds = new Set<string>();
  for (const scene of outline.scenes) {
    if (sceneIds.has(scene.id)) issues.push(`duplicate scene id: ${scene.id}`);
    sceneIds.add(scene.id);
    if (!existingEntities.has(scene.settingEntityId)) issues.push(`unknown scene setting: ${scene.settingEntityId}`);
    for (const participantId of scene.participantEntityIds) {
      if (!existingEntities.has(participantId)) issues.push(`unknown scene participant: ${participantId}`);
    }
    for (const ref of scene.canonRefs) if (!canonRefs.has(ref)) issues.push(`unknown scene canon reference: ${ref}`);
    for (const id of scene.setupIds) setupIds.add(id);
    for (const id of scene.payoffIds) payoffIds.add(id);
  }
  for (const ref of outline.canonRefs) if (!canonRefs.has(ref)) issues.push(`unknown outline canon reference: ${ref}`);
  for (const character of outline.characters) {
    for (const ref of character.canonRefs) if (!canonRefs.has(ref)) issues.push(`unknown character canon reference: ${ref}`);
  }
  for (const payoffId of payoffIds) if (!setupIds.has(payoffId)) issues.push(`payoff has no setup: ${payoffId}`);
  for (const change of outline.canonDelta.entityStateChanges) {
    if (!sceneIds.has(change.basisSceneId)) issues.push(`state change cites unknown scene: ${change.basisSceneId}`);
  }
  try {
    applyCanonDelta(snapshot, outline.canonDelta);
  } catch (error) {
    issues.push(error instanceof Error ? error.message : String(error));
  }
  return [...new Set(issues)];
}

export const JsonPatchOperationSchema = z.discriminatedUnion('op', [
  z.object({ op: z.literal('add'), path: z.string(), value: z.unknown() }),
  z.object({ op: z.literal('remove'), path: z.string() }),
  z.object({ op: z.literal('replace'), path: z.string(), value: z.unknown() }),
  z.object({ op: z.literal('move'), from: z.string(), path: z.string() }),
  z.object({ op: z.literal('copy'), from: z.string(), path: z.string() }),
  z.object({ op: z.literal('test'), path: z.string(), value: z.unknown() }),
]);

export type JsonPatchOperation = z.infer<typeof JsonPatchOperationSchema>;

function pointerSegments(pointer: string): string[] {
  if (pointer === '') return [];
  if (!pointer.startsWith('/')) throw new Error(`Invalid JSON Pointer: ${pointer}`);
  const segments = pointer.slice(1).split('/').map((part) => part.replace(/~1/g, '/').replace(/~0/g, '~'));
  if (segments.some((part) => ['__proto__', 'prototype', 'constructor'].includes(part))) throw new Error('Unsafe JSON Pointer segment.');
  return segments;
}

function assertContentPath(pointer: string): void {
  const [root] = pointerSegments(pointer);
  if (root !== 'content') throw new Error('Artifact patches may modify only /content.');
}

function readPointer(document: unknown, pointer: string): unknown {
  let current = document;
  for (const segment of pointerSegments(pointer)) {
    if (Array.isArray(current)) {
      if (!/^\d+$/.test(segment)) throw new Error(`Invalid array index: ${segment}`);
      current = current[Number(segment)];
    } else if (current !== null && typeof current === 'object') {
      current = (current as Record<string, unknown>)[segment];
    } else {
      throw new Error(`JSON Pointer does not resolve: ${pointer}`);
    }
  }
  return current;
}

function resolveParent(document: unknown, pointer: string): { parent: Record<string, unknown> | unknown[]; key: string } {
  const segments = pointerSegments(pointer);
  const key = segments.pop();
  if (key === undefined) throw new Error('Cannot patch the artifact root.');
  let current = document;
  for (const segment of segments) {
    if (Array.isArray(current)) current = current[Number(segment)];
    else if (current !== null && typeof current === 'object') current = (current as Record<string, unknown>)[segment];
    else throw new Error(`JSON Pointer does not resolve: ${pointer}`);
  }
  if (current === null || typeof current !== 'object') throw new Error(`JSON Pointer parent does not resolve: ${pointer}`);
  return { parent: current as Record<string, unknown> | unknown[], key };
}

function removePointer(document: unknown, pointer: string): unknown {
  const { parent, key } = resolveParent(document, pointer);
  if (Array.isArray(parent)) {
    if (!/^\d+$/.test(key) || Number(key) >= parent.length) throw new Error(`Invalid array index: ${key}`);
    return parent.splice(Number(key), 1)[0];
  }
  if (!(key in parent)) throw new Error(`JSON Pointer does not resolve: ${pointer}`);
  const value = parent[key];
  delete parent[key];
  return value;
}

function addPointer(document: unknown, pointer: string, value: unknown, replace = false): void {
  const { parent, key } = resolveParent(document, pointer);
  if (Array.isArray(parent)) {
    if (key === '-' && !replace) {
      parent.push(value);
      return;
    }
    if (!/^\d+$/.test(key)) throw new Error(`Invalid array index: ${key}`);
    const index = Number(key);
    if (replace) {
      if (index >= parent.length) throw new Error(`Invalid array index: ${key}`);
      parent[index] = value;
    } else {
      if (index > parent.length) throw new Error(`Invalid array index: ${key}`);
      parent.splice(index, 0, value);
    }
    return;
  }
  if (replace && !(key in parent)) throw new Error(`JSON Pointer does not resolve: ${pointer}`);
  parent[key] = value;
}

export function applyArtifactPatch<T>(artifactInput: ArtifactEnvelope<T>, operationsInput: unknown): T {
  const artifact = ArtifactEnvelopeSchema.parse(artifactInput) as ArtifactEnvelope<T>;
  if (NON_EDITABLE_ARTIFACT_KINDS.has(artifact.kind)) throw new Error(`${artifact.kind} artifacts are immutable.`);
  const operations = z.array(JsonPatchOperationSchema).min(1).parse(operationsInput);
  const document = structuredClone(artifact) as ArtifactEnvelope<T>;
  for (const operation of operations) {
    assertContentPath(operation.path);
    if ('from' in operation) assertContentPath(operation.from);
    switch (operation.op) {
      case 'add': addPointer(document, operation.path, structuredClone(operation.value)); break;
      case 'remove': removePointer(document, operation.path); break;
      case 'replace': addPointer(document, operation.path, structuredClone(operation.value), true); break;
      case 'move': addPointer(document, operation.path, removePointer(document, operation.from)); break;
      case 'copy': addPointer(document, operation.path, structuredClone(readPointer(document, operation.from))); break;
      case 'test': {
        const actual = readPointer(document, operation.path);
        if (canonicalJson(actual) !== canonicalJson(operation.value)) throw new Error(`JSON Patch test failed at ${operation.path}.`);
        break;
      }
    }
  }
  return validateArtifactContent<T>(artifact.kind, document.content);
}

export function makeArtifactEnvelope<T>(input: {
  artifactId?: string;
  storyRunId: string | null;
  branchId?: 'A' | 'B' | 'C' | null;
  kind: ArtifactKind;
  logicalKey: string;
  version?: number;
  canonRevision: number;
  canonSnapshotArtifactId: string;
  content: T;
  producer: ArtifactProducer;
  createdAt?: string;
}): ArtifactEnvelope<T> {
  const content = validateArtifactContent<T>(input.kind, input.content);
  return ArtifactEnvelopeSchema.parse({
    artifactId: input.artifactId ?? randomUUID(),
    worldId: SHARED_WORLD_ID,
    storyRunId: input.storyRunId,
    branchId: input.branchId ?? null,
    kind: input.kind,
    schemaVersion: 1,
    logicalKey: input.logicalKey,
    version: input.version ?? 1,
    canonRevision: input.canonRevision,
    canonSnapshotArtifactId: input.canonSnapshotArtifactId,
    content,
    contentHash: artifactContentHash(content),
    producer: input.producer,
    createdAt: input.createdAt ?? new Date().toISOString(),
  }) as ArtifactEnvelope<T>;
}

export function statusAfterArtifactEdit(kind: ArtifactKind): StoryRunStatus {
  if (['story.brief', 'canon.dossier', 'prompt.conflict-report'].includes(kind)) return 'building_pitches';
  if (kind.startsWith('pitch.') || kind === 'review.pitch-continuity') return 'building_pitches';
  if (kind === 'decision.pitch-selection') return 'planning';
  if (kind.startsWith('plan.') || kind === 'outline.blueprint') return 'planning';
  if (kind.startsWith('outline.') || kind.startsWith('review.')) return 'needs_revision';
  return 'analyzing';
}

export function assertPromotionReady(input: {
  outline: unknown;
  snapshot: unknown;
  outlineArtifact: ArtifactEnvelope;
  continuityReview: ArtifactEnvelope;
  narrativeReview: ArtifactEnvelope;
  themeReview: ArtifactEnvelope;
}): StoryOutline {
  const outline = StoryOutlineSchema.parse(input.outline);
  const issues = validateStoryOutline(outline, input.snapshot);
  if (issues.length) throw new Error(`Outline validation failed:\n- ${issues.join('\n- ')}`);
  const reviews = [
    ContinuityReviewSchemaV2.parse(input.continuityReview.content),
    NarrativeReviewSchema.parse(input.narrativeReview.content),
    ThemePacingPlanSchema.parse(input.themeReview.content),
  ];
  for (const [index, review] of reviews.entries()) {
    if (input[index === 0 ? 'continuityReview' : index === 1 ? 'narrativeReview' : 'themeReview'].producer.type !== 'agent') {
      throw new Error('Human-edited reviews cannot satisfy promotion gates.');
    }
    if (review.targetArtifactId !== input.outlineArtifact.artifactId || review.targetContentHash !== input.outlineArtifact.contentHash) {
      throw new Error('Review does not target the active final outline version.');
    }
    if (review.verdict !== 'pass') throw new Error('All required reviews must pass before promotion.');
  }
  return outline;
}

export type ArtifactContent =
  | World
  | StoryOutline
  | CanonDelta
  | CanonSnapshot
  | CanonCommitReceipt
  | Record<string, unknown>;
