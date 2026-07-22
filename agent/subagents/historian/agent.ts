import { defineAgent } from 'eve';
import { HistoryContributionSchema } from '../../lib/domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Build causal histories, disputed memories, and present-day pressures for a proposed story world.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: HistoryContributionSchema,
  limits: { maxInputTokensPerSession: 40_000, maxOutputTokensPerSession: 5_000 },
});
