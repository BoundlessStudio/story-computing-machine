import { defineAgent } from 'eve';
import { PitchSeedSchema } from '../../lib/story-domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Create one world-specific pitch seed for an assigned creative lens and isolated pitch branch; never compare or merge competing branches.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: PitchSeedSchema,
  limits: { maxInputTokensPerSession: 70_000, maxOutputTokensPerSession: 7_000 },
});
