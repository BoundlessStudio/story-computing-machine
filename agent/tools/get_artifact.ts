import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { artifactStore, ArtifactWithLineageSchema } from '../lib/story-store.js';

export default defineTool({
  description: 'Load one exact immutable artifact version by ID plus its immediate parent and child lineage links.',
  inputSchema: z.object({ artifactId: z.string().uuid() }),
  outputSchema: ArtifactWithLineageSchema,
  async execute({ artifactId }) {
    const store = artifactStore();
    const [artifact, lineage] = await Promise.all([
      store.getArtifact(artifactId),
      store.getArtifactLineage(artifactId),
    ]);
    if (!artifact) throw new Error(`Artifact not found: ${artifactId}`);
    return { artifact, lineage };
  },
});
