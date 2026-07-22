import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { statusAfterArtifactEdit } from '../lib/artifact-domain.js';
import { artifactStore, StoryRunRecordSchema } from '../lib/story-store.js';

export default defineTool({
  description: 'Mark a story run ready to regenerate downstream work from an exact active artifact. This changes workflow state but never calls a model itself.',
  inputSchema: z.object({ artifactId: z.string().uuid() }),
  outputSchema: StoryRunRecordSchema,
  async execute({ artifactId }) {
    const store = artifactStore();
    const artifact = await store.getArtifact(artifactId);
    if (!artifact?.storyRunId) throw new Error('Run-scoped artifact not found.');
    if (artifact.lifecycleStatus !== 'active') throw new Error('Regeneration must start from an active artifact version.');
    return store.transitionRun({
      storyRunId: artifact.storyRunId,
      nextStatus: statusAfterArtifactEdit(artifact.kind as never),
      actor: { type: 'human', name: 'writer' },
      triggeringArtifactId: artifact.artifactId,
      summary: `Regeneration requested from ${artifact.logicalKey}`,
    });
  },
});
