import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { artifactStore, StoredArtifactEnvelopeSchema, StoryRunRecordSchema } from '../lib/story-store.js';

export default defineTool({
  description: 'List a story run and its exact artifact versions. Inactive history is excluded unless explicitly requested.',
  inputSchema: z.object({
    storyRunId: z.string().uuid(),
    includeInactive: z.boolean().default(false),
  }),
  outputSchema: z.object({ run: StoryRunRecordSchema, artifacts: z.array(StoredArtifactEnvelopeSchema) }),
  async execute({ storyRunId, includeInactive }) {
    const store = artifactStore();
    const [run, artifacts] = await Promise.all([
      store.getRun(storyRunId),
      store.listRunArtifacts(storyRunId, { includeInactive }),
    ]);
    if (!run) throw new Error(`Story run not found: ${storyRunId}`);
    return { run, artifacts };
  },
});
