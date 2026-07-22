import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { assertPromotionReady, ProvisionalOutlineResultSchema } from '../lib/artifact-domain.js';
import { artifactStore } from '../lib/story-store.js';

function latestMatching(artifacts: Awaited<ReturnType<ReturnType<typeof artifactStore>['listRunArtifacts']>>, kind: string, outlineId: string, outlineHash: string) {
  return artifacts
    .filter((artifact) => artifact.kind === kind && artifact.lifecycleStatus === 'active')
    .filter((artifact) => {
      const content = artifact.content as Record<string, unknown>;
      return content.targetArtifactId === outlineId && content.targetContentHash === outlineHash;
    })
    .at(-1);
}

export default defineTool({
  description: 'Deterministically validate the active final outline against pinned canon and three exact, passing agent-authored reviews, then save its immutable canon delta and mark it ready for explicit promotion.',
  inputSchema: z.object({
    storyRunId: z.string().uuid(),
    finalOutlineArtifactId: z.string().uuid(),
    expectedOutlineHash: z.string().regex(/^[a-f0-9]{64}$/),
  }),
  outputSchema: ProvisionalOutlineResultSchema,
  async execute(input) {
    const store = artifactStore();
    const [run, outline, artifacts] = await Promise.all([
      store.getRun(input.storyRunId),
      store.getArtifact(input.finalOutlineArtifactId),
      store.listRunArtifacts(input.storyRunId),
    ]);
    if (!run || !outline || outline.storyRunId !== input.storyRunId || outline.kind !== 'outline.final') {
      throw new Error('Active final outline does not belong to this run.');
    }
    if (run.status !== 'reviewing') throw new Error('Story run must be in reviewing status before finalization.');
    if (outline.lifecycleStatus !== 'active' || outline.contentHash !== input.expectedOutlineHash) {
      throw new Error('Final outline hash is no longer active.');
    }
    const snapshot = await store.getArtifact(run.baseCanonSnapshotArtifactId);
    if (!snapshot) throw new Error('Pinned canon snapshot is missing.');
    const continuity = latestMatching(artifacts, 'review.continuity', outline.artifactId, outline.contentHash);
    const narrative = latestMatching(artifacts, 'review.narrative', outline.artifactId, outline.contentHash);
    const theme = latestMatching(artifacts, 'review.theme-pacing', outline.artifactId, outline.contentHash);
    if (!continuity || !narrative || !theme) throw new Error('Three current reviews must target the exact final outline hash.');
    const validated = assertPromotionReady({
      outline: outline.content,
      snapshot: snapshot.content,
      outlineArtifact: outline as never,
      continuityReview: continuity as never,
      narrativeReview: narrative as never,
      themeReview: theme as never,
    });
    await store.saveArtifact({
      storyRunId: input.storyRunId,
      kind: 'canon.delta',
      logicalKey: 'canon/proposed-delta',
      content: validated.canonDelta,
      producer: { type: 'tool', name: 'finalize_outline' },
      parents: [
        { artifactId: outline.artifactId, relationship: 'derives-from' },
        { artifactId: continuity.artifactId, relationship: 'consumes' },
        { artifactId: narrative.artifactId, relationship: 'consumes' },
        { artifactId: theme.artifactId, relationship: 'consumes' },
      ],
      expectedStatus: 'reviewing',
      nextStatus: 'ready_for_promotion',
      eventSummary: 'Final outline and required reviews passed deterministic gates',
    });
    return {
      type: 'provisional-outline' as const,
      storyRunId: input.storyRunId,
      finalOutlineArtifactId: outline.artifactId,
      status: 'ready_for_promotion' as const,
    };
  },
});
