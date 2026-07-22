import { defineAgent } from 'eve';
import { PromptInterpreterOutputSchema } from '../../lib/story-domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Translate a writer prompt into a precise story brief, identifying explicit requirements, ambiguities, and possible canon conflicts without inventing story solutions.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: PromptInterpreterOutputSchema,
  limits: { maxInputTokensPerSession: 60_000, maxOutputTokensPerSession: 6_000 },
});
