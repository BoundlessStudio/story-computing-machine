import { defineAgent } from 'eve';
import { ConflictPlanSchema } from '../../lib/story-domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Design the central opposition, causal escalation, reversals, stakes, and resolution cost for exactly one supplied pitch or selected story.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: ConflictPlanSchema,
  limits: { maxInputTokensPerSession: 70_000, maxOutputTokensPerSession: 8_000 },
});
