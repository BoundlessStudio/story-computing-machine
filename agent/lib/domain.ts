import { z } from 'zod';

export const EntitySchema = z.object({
  id: z.string().regex(/^[a-z0-9-]+$/),
  name: z.string().min(1),
  kind: z.enum(['place', 'faction', 'character', 'artifact', 'species']),
  summary: z.string().min(1),
  wants: z.string().min(1),
  tags: z.array(z.string()).default([]),
});

export const RelationshipSchema = z.object({
  from: z.string(),
  to: z.string(),
  type: z.enum(['controls', 'opposes', 'needs', 'protects', 'created', 'inhabits']),
  detail: z.string().min(1),
});

export const WorldDraftSchema = z.object({
  title: z.string().min(1),
  premise: z.string().min(1),
  tone: z.string().min(1),
  laws: z.array(z.string().min(1)).min(3),
  history: z.array(z.object({ era: z.string(), event: z.string(), consequence: z.string() })).min(3),
  entities: z.array(EntitySchema).min(5),
  relationships: z.array(RelationshipSchema).min(4),
  storyHooks: z.array(z.string().min(1)).min(3),
  openQuestions: z.array(z.string()).default([]),
});

export const WorldSchema = WorldDraftSchema.extend({
  metadata: z.object({
    seed: z.number().int(),
    generatedAt: z.string(),
    mode: z.enum(['online', 'offline']),
    framework: z.literal('eve'),
    gateway: z.literal('openrouter'),
  }),
});

export const CultureContributionSchema = z.object({
  institutions: z.array(z.object({ name: z.string(), role: z.string(), internalConflict: z.string() })).min(2),
  practices: z.array(z.object({ practice: z.string(), materialCause: z.string() })).min(2),
  tensions: z.array(z.string()).min(2),
});

export const HistoryContributionSchema = z.object({
  eras: z.array(z.object({ era: z.string(), event: z.string(), consequence: z.string() })).min(3),
  disputedMemory: z.string().min(1),
  presentPressure: z.string().min(1),
});

export const ContinuityReviewSchema = z.object({
  verdict: z.enum(['ready', 'revise']),
  contradictions: z.array(z.object({ issue: z.string(), repair: z.string() })),
  weakCausality: z.array(z.object({ issue: z.string(), repair: z.string() })),
  genericElements: z.array(z.object({ issue: z.string(), repair: z.string() })),
});

export type World = z.infer<typeof WorldSchema>;
export type WorldDraft = z.infer<typeof WorldDraftSchema>;

export function slugify(value: string): string {
  return value.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48) || 'entity';
}

export function validateCanon(world: Pick<WorldDraft, 'entities' | 'relationships'>): string[] {
  const issues: string[] = [];
  const ids = new Set<string>();
  for (const entity of world.entities) {
    if (ids.has(entity.id)) issues.push(`duplicate entity id: ${entity.id}`);
    ids.add(entity.id);
  }
  for (const relationship of world.relationships) {
    if (!ids.has(relationship.from)) issues.push(`unknown relationship source: ${relationship.from}`);
    if (!ids.has(relationship.to)) issues.push(`unknown relationship target: ${relationship.to}`);
    if (relationship.from === relationship.to) issues.push(`self relationship: ${relationship.from}`);
  }
  return issues;
}

export function assertCanon(world: World): World {
  const parsed = WorldSchema.parse(world);
  const issues = validateCanon(parsed);
  if (issues.length) throw new Error(`Canon validation failed:\n- ${issues.join('\n- ')}`);
  return parsed;
}
