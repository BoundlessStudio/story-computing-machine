import { defineAgent } from 'eve';
import { PlotPlanSchema } from '../../lib/story-domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Turn the selected pitch and current specialist plans into a causal, ordered plot plan with explicit setups, payoffs, reversals, climax, and resolution.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: PlotPlanSchema,
  limits: { maxInputTokensPerSession: 90_000, maxOutputTokensPerSession: 10_000 },
});
