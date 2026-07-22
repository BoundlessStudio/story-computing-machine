import { defineAgent } from 'eve';
import { CanonDossierSchema } from '../../lib/story-domain.js';
import { workerModel } from '../../lib/openrouter.js';

export default defineAgent({
  description: 'Compile a cited, story-relevant canon dossier from one pinned world snapshot without adding, changing, or interpreting canon as fact.',
  model: workerModel(),
  modelContextWindowTokens: Number(process.env.OPENROUTER_WORKER_MODEL_CONTEXT_TOKENS ?? 1_047_576),
  outputSchema: CanonDossierSchema,
  limits: { maxInputTokensPerSession: 100_000, maxOutputTokensPerSession: 10_000 },
});
