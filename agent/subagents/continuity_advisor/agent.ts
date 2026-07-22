import { defineAgent } from 'eve';
import { ContinuityReviewSchema } from '../../lib/domain.js';
import { advisorModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Advise the lead architect by finding contradictions, weak causality, and generic elements in a complete world draft and proposing exact repairs.',
  model: advisorModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_ADVISOR_MODEL_CONTEXT_TOKENS ?? 200_000),
  outputSchema: ContinuityReviewSchema,
  reasoning: 'medium',
  limits: { maxInputTokensPerSession: 80_000, maxOutputTokensPerSession: 8_000 },
});
