import { defineTool } from 'eve/tools';
import { z } from 'zod';
import {
  applyCanonDelta,
  CanonCommitReceiptSchema,
  PromotionReceiptResultSchema,
} from '../lib/artifact-domain.js';
import { StoryOutlineSchema } from '../lib/story-domain.js';
import { artifactStore } from '../lib/story-store.js';

export default defineTool({
  description: 'Atomically promote one ready final outline into the append-only shared canon. Call only after an explicit writer request; stale runs are rejected without rebasing.',
  inputSchema: z.object({
    storyRunId: z.string().uuid(),
    finalOutlineArtifactId: z.string().uuid(),
    expectedOutlineHash: z.string().regex(/^[a-f0-9]{64}$/),
  }),
  outputSchema: PromotionReceiptResultSchema,
  async execute(input) {
    const store = artifactStore();
    const [run, outline] = await Promise.all([
      store.getRun(input.storyRunId),
      store.getArtifact(input.finalOutlineArtifactId),
    ]);
    if (!run || run.status !== 'ready_for_promotion') throw new Error('Story run is not ready for promotion.');
    if (!outline || outline.kind !== 'outline.final' || outline.lifecycleStatus !== 'active' || outline.contentHash !== input.expectedOutlineHash) {
      throw new Error('Final outline is missing, inactive, or changed.');
    }
    if (run.finalOutlineArtifactId !== outline.artifactId || !run.canonDeltaArtifactId) {
      throw new Error('Run pointers do not identify the requested outline and delta.');
    }
    const [delta, snapshot] = await Promise.all([
      store.getArtifact(run.canonDeltaArtifactId),
      store.getArtifact(run.baseCanonSnapshotArtifactId),
    ]);
    if (!delta || !snapshot || delta.lifecycleStatus !== 'active') throw new Error('Promotion inputs are missing or stale.');
    const parsedOutline = StoryOutlineSchema.parse(outline.content);
    if (JSON.stringify(parsedOutline.canonDelta) !== JSON.stringify(delta.content)) {
      throw new Error('The active canon delta no longer matches the final outline.');
    }
    const nextSnapshot = applyCanonDelta(snapshot.content, delta.content);
    const receiptArtifact = await store.promoteOutline({
      storyRunId: input.storyRunId,
      finalOutlineArtifactId: outline.artifactId,
      canonDeltaArtifactId: delta.artifactId,
      nextSnapshotContent: nextSnapshot,
    });
    const receipt = CanonCommitReceiptSchema.parse(receiptArtifact.content);
    return { type: 'promotion-receipt' as const, receipt, status: 'promoted' as const };
  },
});
