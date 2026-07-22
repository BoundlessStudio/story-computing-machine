import { defineAgent } from 'eve';
import { StoryEditorOutputSchema } from '../../lib/story-domain.js';
import { rootModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Synthesize explicitly supplied specialist artifacts into a pitch slate, outline blueprint, or revised final outline while preserving canon and branch provenance.',
  model: rootModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_MODEL_CONTEXT_TOKENS ?? 200_000),
  outputSchema: StoryEditorOutputSchema,
  reasoning: 'medium',
  limits: { maxInputTokensPerSession: 120_000, maxOutputTokensPerSession: 14_000 },
});
