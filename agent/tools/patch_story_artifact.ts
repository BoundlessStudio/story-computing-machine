import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { EditReceiptResultSchema, JsonPatchOperationSchema } from '../lib/artifact-domain.js';
import { artifactStore } from '../lib/story-store.js';

export default defineTool({
  description: 'Apply an expected-hash RFC 6902 patch to /content of an editable story artifact. Creates a human-authored version and invalidates all descendants without calling a model.',
  inputSchema: z.object({
    artifactId: z.string().uuid(),
    expectedHash: z.string().regex(/^[a-f0-9]{64}$/),
    operations: z.array(JsonPatchOperationSchema).min(1),
    producerName: z.string().min(1).default('writer'),
  }),
  outputSchema: EditReceiptResultSchema,
  async execute(input) {
    const store = artifactStore();
    const previous = await store.getArtifact(input.artifactId);
    if (!previous?.storyRunId) throw new Error('Editable story artifact not found.');
    const result = await store.patchArtifact({
      artifactId: input.artifactId,
      expectedHash: input.expectedHash,
      operations: input.operations,
      producerName: input.producerName,
    });
    return {
      type: 'edit-receipt' as const,
      storyRunId: previous.storyRunId,
      previousArtifactId: previous.artifactId,
      artifactId: result.artifact.artifactId,
      contentHash: result.artifact.contentHash,
      invalidatedArtifactIds: result.invalidatedArtifactIds,
      status: result.invalidatedFromStatus,
    };
  },
});
