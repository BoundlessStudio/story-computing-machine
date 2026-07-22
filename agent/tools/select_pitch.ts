import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { artifactStore, StoredArtifactEnvelopeSchema } from '../lib/story-store.js';

export default defineTool({
  description: 'Persist the writer choice of one pitch from an exact active pitch-slate version and move the run into planning.',
  inputSchema: z.object({
    storyRunId: z.string().uuid(),
    pitchSlateArtifactId: z.string().uuid(),
    expectedSlateHash: z.string().regex(/^[a-f0-9]{64}$/),
    pitchId: z.string().regex(/^pitch-[abc]$/),
    producerName: z.string().min(1).default('writer'),
  }),
  outputSchema: StoredArtifactEnvelopeSchema,
  async execute(input) {
    return artifactStore().selectPitch(input);
  },
});
