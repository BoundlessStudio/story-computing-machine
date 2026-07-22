import { defineAgent } from 'eve';
import { WorldIntegrationPlanSchema } from '../../lib/story-domain.js';
import { advisorModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Advise on canon-safe world integration, identifying conflicts and making world laws, history, institutions, and entity states causally necessary without authoring the story.',
  model: advisorModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_ADVISOR_MODEL_CONTEXT_TOKENS ?? 200_000),
  outputSchema: WorldIntegrationPlanSchema,
  reasoning: 'medium',
  limits: { maxInputTokensPerSession: 100_000, maxOutputTokensPerSession: 10_000 },
});
