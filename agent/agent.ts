import { defineAgent } from 'eve';
import { z } from 'zod';
import { StoryOperationResultSchema } from './lib/artifact-domain.js';
import { WorldSchema } from './lib/domain.js';
import { rootModel } from './lib/openrouter.js';

export default defineAgent({
  model: rootModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: z.union([WorldSchema, StoryOperationResultSchema]),
  limits: {
    maxInputTokensPerSession: 250_000,
    maxOutputTokensPerSession: 30_000,
  },
  compaction: { thresholdPercent: 0.75 },
});
