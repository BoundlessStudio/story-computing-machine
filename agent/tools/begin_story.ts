import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { CanonSnapshotSchema } from '../lib/artifact-domain.js';
import { artifactStore, StoredArtifactEnvelopeSchema, StoryRunRecordSchema } from '../lib/story-store.js';

const outputSchema = z.object({
  run: StoryRunRecordSchema,
  promptArtifact: StoredArtifactEnvelopeSchema,
  canonSnapshot: StoredArtifactEnvelopeSchema.extend({ content: CanonSnapshotSchema }),
});

export default defineTool({
  description: 'Create a durable story run from a writer prompt and pin it to the current shared canon snapshot. This is the only valid way to start story planning.',
  inputSchema: z.object({
    prompt: z.string().min(1),
    producerName: z.string().min(1).default('writer'),
  }),
  outputSchema,
  async execute({ prompt, producerName }) {
    const store = artifactStore();
    const created = await store.beginStory(prompt, producerName);
    const snapshot = await store.getArtifact(created.run.baseCanonSnapshotArtifactId);
    if (!snapshot) throw new Error('Pinned canon snapshot artifact is missing.');
    CanonSnapshotSchema.parse(snapshot.content);
    return outputSchema.parse({ run: created.run, promptArtifact: created.prompt, canonSnapshot: snapshot });
  },
});
