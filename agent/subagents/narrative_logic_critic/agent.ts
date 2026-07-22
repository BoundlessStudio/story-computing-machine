import { defineAgent } from 'eve';
import { NarrativeReviewSchema } from '../../lib/story-domain.js';
import { advisorModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Audit an exact story artifact version for motivation, causality, escalation, agency, setup and payoff, prompt alignment, and ending logic; advise but do not rewrite.',
  model: advisorModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_ADVISOR_MODEL_CONTEXT_TOKENS ?? 200_000),
  outputSchema: NarrativeReviewSchema,
  reasoning: 'medium',
  limits: { maxInputTokensPerSession: 100_000, maxOutputTokensPerSession: 10_000 },
});
