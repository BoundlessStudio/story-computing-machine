import { defineAgent } from 'eve';
import { CultureContributionSchema } from '../../lib/domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Design cultures, institutions, and daily practices that emerge from a story world’s physical laws; use as an inventive specialist, not a final decision-maker.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: CultureContributionSchema,
  limits: { maxInputTokensPerSession: 40_000, maxOutputTokensPerSession: 5_000 },
});
