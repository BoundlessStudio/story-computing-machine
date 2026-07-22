import { z } from 'zod';
import {
  ArtifactEnvelopeSchema,
  ArtifactKindSchema,
  ArtifactLifecycleSchema,
  ArtifactProducerSchema,
  StoryRunStatusSchema,
  validateArtifactContent,
  type ArtifactKind,
} from './artifact-domain.js';
import type { ArtifactValidator, JsonValue } from './artifact-store.js';
import { ArtifactStore } from './sqlite-artifact-store.js';

export const StoredArtifactEnvelopeSchema = ArtifactEnvelopeSchema.extend({
  lifecycleStatus: ArtifactLifecycleSchema,
});

export const ArtifactLineageLinkSchema = z.object({
  direction: z.enum(['parent', 'child']),
  relationship: z.enum(['consumes', 'derives-from', 'reviews', 'supersedes', 'promotes', 'renders']),
  artifactId: z.string().uuid(),
  kind: ArtifactKindSchema,
  logicalKey: z.string().min(1),
  version: z.number().int().positive(),
  contentHash: z.string().regex(/^[a-f0-9]{64}$/),
  lifecycleStatus: ArtifactLifecycleSchema,
});

export const ArtifactWithLineageSchema = z.object({
  artifact: StoredArtifactEnvelopeSchema,
  lineage: z.array(ArtifactLineageLinkSchema),
});

export const StoryRunRecordSchema = z.object({
  storyRunId: z.string().uuid(),
  worldId: z.literal('shared-world'),
  baseCanonRevision: z.number().int().positive(),
  baseCanonSnapshotArtifactId: z.string().uuid(),
  status: StoryRunStatusSchema,
  originalPromptArtifactId: z.string().uuid(),
  briefArtifactId: z.string().uuid().nullable(),
  pitchSlateArtifactId: z.string().uuid().nullable(),
  pitchSelectionArtifactId: z.string().uuid().nullable(),
  blueprintArtifactId: z.string().uuid().nullable(),
  finalOutlineArtifactId: z.string().uuid().nullable(),
  canonDeltaArtifactId: z.string().uuid().nullable(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const ArtifactParentInputSchema = z.object({
  artifactId: z.string().uuid(),
  relationship: z.enum(['consumes', 'derives-from', 'reviews', 'supersedes', 'promotes', 'renders']),
});

export const AgentProducerInputSchema = ArtifactProducerSchema.omit({ type: true }).extend({
  name: z.string().min(1),
});

export const AgentExecutionMetadataSchema = z.object({
  executionId: z.string().uuid().optional(),
  eveChildSessionId: z.string().min(1).optional(),
  modelId: z.string().min(1).optional(),
  promptRevision: z.string().min(1).optional(),
  skillRevision: z.string().min(1).optional(),
  startedAt: z.string().datetime().optional(),
  completedAt: z.string().datetime().optional(),
  inputTokens: z.number().int().nonnegative().optional(),
  outputTokens: z.number().int().nonnegative().optional(),
  costUsd: z.number().nonnegative().optional(),
});

const validator: ArtifactValidator = {
  parse(kind, schemaVersion, content) {
    if (schemaVersion !== 1) throw new Error(`Unsupported artifact schema version: ${kind}@${schemaVersion}`);
    const parsedKind = ArtifactKindSchema.parse(kind) as ArtifactKind;
    return validateArtifactContent(parsedKind, content) as JsonValue;
  },
};

let sharedStore: ArtifactStore | undefined;
let sharedPath: string | undefined;

export function artifactStore(): ArtifactStore {
  const databasePath = process.env.SQLITE_PATH ?? 'data/story-room.sqlite';
  if (!sharedStore || sharedPath !== databasePath) {
    sharedStore?.close();
    sharedStore = new ArtifactStore(databasePath, validator);
    sharedPath = databasePath;
  }
  return sharedStore;
}
