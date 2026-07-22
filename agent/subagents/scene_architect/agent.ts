import { defineAgent } from 'eve';
import { SceneOutlineSchema } from '../../lib/story-domain.js';
import { rootModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Expand one approved outline blueprint into a concrete 6–8-scene outline while preserving its causal structure and exact canon references.',
  model: rootModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_MODEL_CONTEXT_TOKENS ?? 200_000),
  outputSchema: SceneOutlineSchema,
  reasoning: 'medium',
  limits: { maxInputTokensPerSession: 100_000, maxOutputTokensPerSession: 14_000 },
});
