import { defineAgent } from 'eve';
import { ContinuityReviewSchemaV2 } from '../../lib/story-domain.js';
import { advisorModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Audit an exact story artifact version for contradictions in canon, chronology, world laws, entity state, relationships, and cited references; advise but do not rewrite.',
  model: advisorModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_ADVISOR_MODEL_CONTEXT_TOKENS ?? 200_000),
  outputSchema: ContinuityReviewSchemaV2,
  reasoning: 'medium',
  limits: { maxInputTokensPerSession: 120_000, maxOutputTokensPerSession: 10_000 },
});
