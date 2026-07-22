import { defineAgent } from 'eve';
import { ThemePacingPlanSchema } from '../../lib/story-domain.js';
import { advisorModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Advise on thematic progression, tonal consistency, pacing, dramatic pressure, scene function, and repetition for one exact pitch branch or outline version.',
  model: advisorModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_ADVISOR_MODEL_CONTEXT_TOKENS ?? 200_000),
  outputSchema: ThemePacingPlanSchema,
  reasoning: 'medium',
  limits: { maxInputTokensPerSession: 100_000, maxOutputTokensPerSession: 10_000 },
});
