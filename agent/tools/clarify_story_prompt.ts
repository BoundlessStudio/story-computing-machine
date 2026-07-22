import { defineTool } from 'eve/tools';
import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import { artifactStore, StoredArtifactEnvelopeSchema } from '../lib/story-store.js';

export default defineTool({
  description: 'Persist a writer clarification for a prompt conflict and return the run to analysis. This records the clarification without rewriting the original prompt.',
  inputSchema: z.object({
    storyRunId: z.string().uuid(),
    text: z.string().min(1),
    conflictArtifactId: z.string().uuid(),
    producerName: z.string().min(1).default('writer'),
  }),
  outputSchema: StoredArtifactEnvelopeSchema,
  async execute(input) {
    const store = artifactStore();
    const conflict = await store.getArtifact(input.conflictArtifactId);
    const run = await store.getRun(input.storyRunId);
    if (
      !conflict
      || !run
      || conflict.storyRunId !== input.storyRunId
      || conflict.kind !== 'prompt.conflict-report'
      || conflict.lifecycleStatus !== 'active'
    ) {
      throw new Error('Clarification must target the active prompt conflict report for this story run.');
    }
    const originalPrompt = await store.getArtifact(run.originalPromptArtifactId);
    if (!originalPrompt || originalPrompt.kind !== 'prompt.original' || originalPrompt.lifecycleStatus !== 'active') {
      throw new Error('Clarification requires the active immutable original prompt for this story run.');
    }
    return store.saveArtifact({
      storyRunId: input.storyRunId,
      kind: 'prompt.clarification',
      logicalKey: `prompt/clarification/${randomUUID()}`,
      content: { text: input.text, conflictArtifactId: input.conflictArtifactId },
      producer: { type: 'human', name: input.producerName },
      // The exact conflict remains in structured content for audit, but the
      // clarification is rooted in immutable writer input. Making the conflict
      // its graph parent would cause brief regeneration to invalidate the
      // clarification that triggered it and can form a supersession cycle.
      parents: [{ artifactId: originalPrompt.artifactId, relationship: 'consumes' }],
      expectedStatus: 'needs_clarification',
      nextStatus: 'analyzing',
      eventSummary: 'Writer clarified a canon conflict',
    });
  },
});
