import { z } from 'zod';
import { EntitySchema, RelationshipSchema } from './domain.js';

export const BranchIdSchema = z.enum(['A', 'B', 'C']);

export const CanonRefSchema = z.string().min(3).regex(/^[a-z][a-z0-9-]*:[a-z0-9][a-z0-9:._/-]*$/);

export const StoryBriefSchema = z.object({
  prompt: z.string().min(1),
  workingTitle: z.string().min(1).optional(),
  genre: z.string().min(1),
  tone: z.string().min(1),
  themes: z.array(z.string().min(1)).min(1),
  requiredElements: z.array(z.string().min(1)).default([]),
  forbiddenElements: z.array(z.string().min(1)).default([]),
  storyScale: z.literal('short'),
  sceneTarget: z.object({ min: z.literal(6), max: z.literal(8) }),
  canonQuestions: z.array(z.string().min(1)).default([]),
});

export const PromptConflictSchema = z.object({
  issue: z.string().min(1),
  promptClaim: z.string().min(1),
  canonRef: CanonRefSchema,
  canonFact: z.string().min(1),
  resolutionQuestion: z.string().min(1),
});

export const PromptInterpreterOutputSchema = z.object({
  kind: z.literal('story.brief'),
  brief: StoryBriefSchema,
  conflicts: z.array(PromptConflictSchema).default([]),
});

export const CanonFactCategorySchema = z.enum([
  'world',
  'law',
  'history',
  'entity',
  'relationship',
  'event',
  'state',
]);

export const CanonFactSchema = z.object({
  ref: CanonRefSchema,
  category: CanonFactCategorySchema,
  text: z.string().min(1),
});

export const CanonDossierSchema = z.object({
  kind: z.literal('canon.dossier'),
  worldTitle: z.string().min(1),
  summary: z.string().min(1),
  relevantFacts: z.array(CanonFactSchema).min(3),
  currentPressures: z.array(z.string().min(1)).min(1),
  usableHooks: z.array(z.object({
    hook: z.string().min(1),
    canonRefs: z.array(CanonRefSchema).min(1),
  })).min(1),
  unresolvedQuestions: z.array(z.string().min(1)).default([]),
});

export const SupportingEntitySchema = EntitySchema.extend({
  kind: z.enum(['place', 'character', 'artifact']),
});

export const PitchSeedSchema = z.object({
  kind: z.literal('pitch.seed'),
  branchId: BranchIdSchema,
  lens: z.enum(['intimate', 'investigative', 'systemic']),
  title: z.string().min(1),
  logline: z.string().min(1),
  protagonist: z.string().min(1),
  centralConflict: z.string().min(1),
  stakes: z.string().min(1),
  endingDirection: z.string().min(1),
  canonRefs: z.array(CanonRefSchema).min(2),
  proposedSupportingEntities: z.array(SupportingEntitySchema).default([]),
});

export const CharacterPlanSchema = z.object({
  kind: z.enum(['pitch.character-plan', 'plan.character']),
  branchId: BranchIdSchema.optional(),
  characters: z.array(z.object({
    entityId: z.string().min(1),
    role: z.string().min(1),
    externalWant: z.string().min(1),
    internalNeed: z.string().min(1),
    dilemma: z.string().min(1),
    arcTurns: z.array(z.string().min(1)).min(2),
    canonRefs: z.array(CanonRefSchema).min(1),
  })).min(1),
  relationshipDynamics: z.array(z.string().min(1)).min(1),
  recommendations: z.array(z.string().min(1)).default([]),
});

export const ConflictPlanSchema = z.object({
  kind: z.enum(['pitch.conflict-plan', 'plan.conflict']),
  branchId: BranchIdSchema.optional(),
  incitingPressure: z.string().min(1),
  opposition: z.string().min(1),
  stakes: z.object({ personal: z.string(), communal: z.string(), irreversible: z.string() }),
  escalation: z.array(z.string().min(1)).min(3),
  reversals: z.array(z.string().min(1)).min(1),
  climaxChoice: z.string().min(1),
  resolutionCost: z.string().min(1),
  canonRefs: z.array(CanonRefSchema).min(2),
  genericityRisks: z.array(z.string().min(1)).default([]),
});

export const WorldIntegrationPlanSchema = z.object({
  kind: z.enum(['prompt.conflict-report', 'pitch.world-plan', 'plan.world']),
  branchId: BranchIdSchema.optional(),
  verdict: z.enum(['safe', 'clarify', 'revise']),
  conflicts: z.array(PromptConflictSchema).default([]),
  causalUses: z.array(z.object({
    canonRef: CanonRefSchema,
    storyEffect: z.string().min(1),
  })).default([]),
  proposedSupportingEntities: z.array(SupportingEntitySchema).default([]),
  protectedFacts: z.array(CanonRefSchema).default([]),
  recommendations: z.array(z.string().min(1)).default([]),
});

export const StoryPitchSchema = z.object({
  id: z.string().regex(/^pitch-[abc]$/),
  branchId: BranchIdSchema,
  title: z.string().min(1),
  logline: z.string().min(1),
  protagonist: z.string().min(1),
  centralConflict: z.string().min(1),
  stakes: z.string().min(1),
  endingDirection: z.string().min(1),
  characterPromise: z.string().min(1),
  worldSpecificity: z.string().min(1),
  canonRefs: z.array(CanonRefSchema).min(2),
  proposedSupportingEntities: z.array(SupportingEntitySchema).default([]),
});

export const PitchSlateSchema = z.object({
  pitches: z.array(StoryPitchSchema).length(3),
  editorialNote: z.string().min(1),
}).superRefine((slate, context) => {
  if (new Set(slate.pitches.map((pitch) => pitch.id)).size !== 3) {
    context.addIssue({ code: 'custom', path: ['pitches'], message: 'Pitch slate must contain pitch-a, pitch-b, and pitch-c exactly once.' });
  }
  if (new Set(slate.pitches.map((pitch) => pitch.branchId)).size !== 3) {
    context.addIssue({ code: 'custom', path: ['pitches'], message: 'Pitch slate must preserve exactly one pitch from each branch.' });
  }
  for (const [index, pitch] of slate.pitches.entries()) {
    if (pitch.id !== `pitch-${pitch.branchId.toLowerCase()}`) {
      context.addIssue({ code: 'custom', path: ['pitches', index, 'id'], message: 'Pitch ID must match its isolated branch.' });
    }
  }
});

export const PlotBeatSchema = z.object({
  id: z.string().regex(/^beat-[0-9]{2}$/),
  phase: z.enum(['setup', 'escalation', 'reversal', 'climax', 'resolution']),
  summary: z.string().min(1),
  cause: z.string().min(1),
  consequence: z.string().min(1),
  canonRefs: z.array(CanonRefSchema).min(1),
  setupIds: z.array(z.string()).default([]),
  payoffIds: z.array(z.string()).default([]),
});

export const PlotPlanSchema = z.object({
  kind: z.literal('plan.plot'),
  title: z.string().min(1),
  dramaticQuestion: z.string().min(1),
  beats: z.array(PlotBeatSchema).min(6).max(10),
  climax: z.string().min(1),
  resolution: z.string().min(1),
  timelinePlacement: z.object({
    occursAfterEventId: z.string().nullable(),
    rationale: z.string().min(1),
  }),
});

export const ThemePacingPlanSchema = z.object({
  kind: z.enum(['plan.theme-pacing', 'review.theme-pacing']),
  mode: z.enum(['plan', 'review']),
  targetArtifactId: z.string().uuid().optional(),
  targetContentHash: z.string().regex(/^[a-f0-9]{64}$/).optional(),
  centralTheme: z.string().min(1),
  thematicProgression: z.array(z.string().min(1)).min(3),
  pacingShape: z.array(z.object({
    segment: z.string().min(1),
    pressure: z.enum(['low', 'medium', 'high', 'peak']),
    purpose: z.string().min(1),
  })).min(3),
  verdict: z.enum(['pass', 'block']).optional(),
  findings: z.array(z.object({
    severity: z.enum(['advice', 'blocker']),
    issue: z.string().min(1),
    repair: z.string().min(1),
  })).default([]),
});

export const OutlineBlueprintSchema = z.object({
  title: z.string().min(1),
  logline: z.string().min(1),
  synopsis: z.string().min(1),
  selectedPitchId: z.string().regex(/^pitch-[abc]$/),
  characterArcSummary: z.string().min(1),
  thematicArgument: z.string().min(1),
  beats: z.array(PlotBeatSchema).min(6).max(10),
  canonRefs: z.array(CanonRefSchema).min(2),
});

export const SceneSchema = z.object({
  id: z.string().regex(/^scene-[0-9]{2}$/),
  title: z.string().min(1),
  beatIds: z.array(z.string().regex(/^beat-[0-9]{2}$/)).min(1),
  purpose: z.string().min(1),
  settingEntityId: z.string().min(1),
  participantEntityIds: z.array(z.string().min(1)).min(1),
  openingState: z.string().min(1),
  conflict: z.string().min(1),
  turn: z.string().min(1),
  outcome: z.string().min(1),
  canonRefs: z.array(CanonRefSchema).min(1),
  setupIds: z.array(z.string()).default([]),
  payoffIds: z.array(z.string()).default([]),
});

export const EntityStateChangeSchema = z.object({
  entityId: z.string().min(1),
  before: z.string(),
  after: z.string().min(1),
  basisSceneId: z.string().regex(/^scene-[0-9]{2}$/),
});

export const CanonEventSchema = z.object({
  id: z.string().regex(/^[a-z0-9-]+$/),
  title: z.string().min(1),
  summary: z.string().min(1),
  consequences: z.array(z.string().min(1)).min(1),
  participantEntityIds: z.array(z.string().min(1)).min(1),
  occursAfterEventId: z.string().nullable(),
});

export const CanonDeltaSchema = z.object({
  event: CanonEventSchema,
  newEntities: z.array(SupportingEntitySchema).default([]),
  newRelationships: z.array(RelationshipSchema).default([]),
  entityStateChanges: z.array(EntityStateChangeSchema).default([]),
});

export const StoryOutlineSchema = z.object({
  title: z.string().min(1),
  logline: z.string().min(1),
  synopsis: z.string().min(1),
  selectedPitchId: z.string().regex(/^pitch-[abc]$/),
  characters: CharacterPlanSchema.shape.characters,
  centralTheme: z.string().min(1),
  scenes: z.array(SceneSchema).min(6).max(8),
  canonRefs: z.array(CanonRefSchema).min(2),
  canonDelta: CanonDeltaSchema,
});

export const SceneOutlineSchema = z.object({
  kind: z.literal('outline.scenes'),
  outline: StoryOutlineSchema,
});

const ReviewFindingSchema = z.object({
  severity: z.enum(['advice', 'blocker']),
  issue: z.string().min(1),
  evidence: z.string().min(1),
  canonRef: CanonRefSchema.optional(),
  repair: z.string().min(1),
});

export const ContinuityReviewSchemaV2 = z.object({
  kind: z.enum(['review.pitch-continuity', 'review.continuity']),
  targetArtifactId: z.string().uuid(),
  targetContentHash: z.string().regex(/^[a-f0-9]{64}$/),
  verdict: z.enum(['pass', 'block']),
  findings: z.array(ReviewFindingSchema).default([]),
  verifiedCanonRefs: z.array(CanonRefSchema).default([]),
});

export const NarrativeReviewSchema = z.object({
  kind: z.literal('review.narrative'),
  targetArtifactId: z.string().uuid(),
  targetContentHash: z.string().regex(/^[a-f0-9]{64}$/),
  verdict: z.enum(['pass', 'block']),
  findings: z.array(ReviewFindingSchema.omit({ canonRef: true })).default([]),
  strengths: z.array(z.string().min(1)).default([]),
});

export const StoryEditorOutputSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('pitch-slate'), slate: PitchSlateSchema }),
  z.object({ type: z.literal('outline-blueprint'), blueprint: OutlineBlueprintSchema }),
  z.object({ type: z.literal('final-outline'), outline: StoryOutlineSchema }),
]);

export type StoryBrief = z.infer<typeof StoryBriefSchema>;
export type CanonFact = z.infer<typeof CanonFactSchema>;
export type CanonDossier = z.infer<typeof CanonDossierSchema>;
export type PitchSeed = z.infer<typeof PitchSeedSchema>;
export type CharacterPlan = z.infer<typeof CharacterPlanSchema>;
export type ConflictPlan = z.infer<typeof ConflictPlanSchema>;
export type WorldIntegrationPlan = z.infer<typeof WorldIntegrationPlanSchema>;
export type StoryPitch = z.infer<typeof StoryPitchSchema>;
export type PitchSlate = z.infer<typeof PitchSlateSchema>;
export type PlotPlan = z.infer<typeof PlotPlanSchema>;
export type ThemePacingPlan = z.infer<typeof ThemePacingPlanSchema>;
export type OutlineBlueprint = z.infer<typeof OutlineBlueprintSchema>;
export type StoryOutline = z.infer<typeof StoryOutlineSchema>;
export type CanonDelta = z.infer<typeof CanonDeltaSchema>;
export type ContinuityReviewV2 = z.infer<typeof ContinuityReviewSchemaV2>;
export type NarrativeReview = z.infer<typeof NarrativeReviewSchema>;
