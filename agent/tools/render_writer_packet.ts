import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { MarkdownExportResultSchema } from '../lib/artifact-domain.js';
import { renderWriterPacket } from '../lib/writer-packet.js';
import { artifactStore } from '../lib/story-store.js';

export default defineTool({
  description: 'Deterministically render and persist a Markdown writer packet from the current active story artifacts. The export is derived and never becomes canon.',
  inputSchema: z.object({ storyRunId: z.string().uuid() }),
  outputSchema: MarkdownExportResultSchema,
  async execute({ storyRunId }) {
    const store = artifactStore();
    const [run, artifacts] = await Promise.all([
      store.getRun(storyRunId),
      store.listRunArtifacts(storyRunId),
    ]);
    if (!run) throw new Error(`Story run not found: ${storyRunId}`);
    const byId = new Map(artifacts.map((artifact) => [artifact.artifactId, artifact]));
    const required = (artifactId: string | null, label: string) => {
      const artifact = artifactId ? byId.get(artifactId) : undefined;
      if (!artifact) throw new Error(`Active ${label} artifact is missing.`);
      return artifact;
    };
    const brief = required(run.briefArtifactId, 'brief');
    const pitchSlate = required(run.pitchSlateArtifactId, 'pitch slate');
    const selection = required(run.pitchSelectionArtifactId, 'pitch selection');
    const finalOutline = required(run.finalOutlineArtifactId, 'final outline');
    const snapshot = await store.getArtifact(run.baseCanonSnapshotArtifactId);
    if (!snapshot) throw new Error('Pinned canon snapshot is missing.');
    const findReview = (kind: string) => artifacts.find((artifact) => {
      const content = artifact.content as Record<string, unknown>;
      return artifact.kind === kind && content.targetArtifactId === finalOutline.artifactId && content.targetContentHash === finalOutline.contentHash;
    });
    const continuityReview = findReview('review.continuity');
    const narrativeReview = findReview('review.narrative');
    const themeReview = findReview('review.theme-pacing');
    if (!continuityReview || !narrativeReview || !themeReview) throw new Error('Current final-outline reviews are incomplete.');
    const findKind = (kind: string) => [...artifacts].reverse().find((artifact) => artifact.kind === kind);
    const commitReceipt = findKind('canon.commit-receipt');
    const packet = renderWriterPacket({
      snapshot: snapshot as never,
      brief: brief as never,
      pitchSlate: pitchSlate as never,
      selection: selection as never,
      characterPlan: findKind('plan.character') as never,
      worldPlan: findKind('plan.world') as never,
      themePlan: findKind('plan.theme-pacing') as never,
      finalOutline: finalOutline as never,
      continuityReview: continuityReview as never,
      narrativeReview: narrativeReview as never,
      themeReview: themeReview as never,
      commitReceipt: commitReceipt as never,
    });
    const previousExport = findKind('export.writer-packet');
    const sourceArtifacts = packet.sourceArtifactIds.map((artifactId) => ({ artifactId, relationship: 'renders' as const }));
    const exportArtifact = await store.saveArtifact({
      storyRunId,
      kind: 'export.writer-packet',
      logicalKey: 'export/writer-packet',
      content: packet,
      producer: { type: 'tool', name: 'render_writer_packet' },
      parents: sourceArtifacts,
      supersedesArtifactId: previousExport?.artifactId,
      expectedSupersededHash: previousExport?.contentHash,
      eventSummary: 'Rendered Markdown writer packet',
    });
    return {
      type: 'markdown-export' as const,
      storyRunId,
      exportArtifactId: exportArtifact.artifactId,
      filename: packet.filename,
      markdown: packet.markdown,
    };
  },
});
