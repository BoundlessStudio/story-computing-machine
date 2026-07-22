import { defineAgent } from 'eve';
import { CharacterPlanSchema } from '../../lib/story-domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Design a causally active protagonist, supporting cast, relationships, choices, and character arc for exactly one supplied pitch or selected story.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: CharacterPlanSchema,
  limits: { maxInputTokensPerSession: 70_000, maxOutputTokensPerSession: 8_000 },
});
