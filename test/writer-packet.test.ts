import { describe, expect, it } from 'vitest';
import { WriterPacketSchema } from '../agent/lib/artifact-domain.js';
import { renderWriterPacket, type WriterPacketInput } from '../agent/lib/writer-packet.js';
import { IDS, createStoryArtifacts } from './fixtures/story-artifacts.js';

const GENERATED_AT = '2031-02-03T04:05:06.000Z';

function writerPacketInput(): WriterPacketInput {
  const fixture = createStoryArtifacts();
  return {
    snapshot: fixture.snapshotArtifact,
    brief: fixture.briefArtifact,
    pitchSlate: fixture.pitchSlateArtifact,
    selection: fixture.selectionArtifact,
    characterPlan: fixture.characterPlanArtifact,
    worldPlan: fixture.worldPlanArtifact,
    themePlan: fixture.themePlanArtifact,
    finalOutline: fixture.finalOutlineArtifact,
    continuityReview: fixture.continuityReviewArtifact,
    narrativeReview: fixture.narrativeReviewArtifact,
    themeReview: fixture.themeReviewArtifact,
    generatedAt: GENERATED_AT,
  };
}

describe('deterministic Markdown writer packet', () => {
  it('renders byte-for-byte deterministically from exact artifact versions', () => {
    const input = writerPacketInput();
    const first = renderWriterPacket(input);
    const second = renderWriterPacket(structuredClone(input));

    expect(first).toEqual(second);
    expect(() => WriterPacketSchema.parse(first)).not.toThrow();
    expect(first.filename).toBe('the-map-that-forgot-writer-packet.md');
    expect(first.rendererVersion).toBe(1);
    expect(first.markdown).toContain(`generated_at: "${GENERATED_AT}"`);
  });

  it('derives a stable timestamp when the caller does not supply one', () => {
    const input = writerPacketInput();
    delete input.generatedAt;
    const first = renderWriterPacket(input);
    const second = renderWriterPacket(structuredClone(input));

    expect(first).toEqual(second);
    expect(first.markdown).toContain('generated_at: "2030-01-02T03:04:05.000Z"');
  });

  it('snapshots the writer-facing hierarchy and excludes rejected pitch bodies', () => {
    const packet = renderWriterPacket(writerPacketInput());
    const headings = packet.markdown.match(/^#{1,3} .+$/gm);

    expect(headings).toMatchInlineSnapshot(`
      [
        "# The Map That Forgot",
        "## Story Brief",
        "## Chosen Pitch",
        "### The Map That Forgot",
        "## Synopsis",
        "## Cast and Arcs",
        "### mara-venn — protagonist",
        "### Relationship Dynamics",
        "## World Grounding",
        "## Theme and Pacing",
        "## Scene Outline",
        "### 1. The Blank Street (\`scene-01\`)",
        "### 2. A Map Remembers (\`scene-02\`)",
        "### 3. The Cartographers Refuse (\`scene-03\`)",
        "### 4. The Ward Tilts (\`scene-04\`)",
        "### 5. A Public Choice (\`scene-05\`)",
        "### 6. The Correction (\`scene-06\`)",
        "## Canon Impact",
        "### The Public Correction",
        "## Editorial Review",
        "## Artifact Provenance",
      ]
    `);
    expect(packet.markdown).not.toContain('The Private Blank');
    expect(packet.markdown).not.toContain('The Surveyors’ Vote');
  });

  it('contains the complete writer packet while excluding operational internals', () => {
    const packet = renderWriterPacket(writerPacketInput());

    expect(packet.markdown).toContain('**Status:** Provisional against canon revision 1');
    expect(packet.markdown).toContain('**Original prompt:** Write a mystery about a truthful map that erases its cartographer.');
    expect(packet.markdown).toContain('**Protagonist:** Mara Venn');
    expect(packet.markdown).toContain('### mara-venn — protagonist');
    expect(packet.markdown).toContain('### Relationship Dynamics');
    expect(packet.markdown).toContain('The world premise makes every map correction physically consequential.');
    expect(packet.markdown).toContain('1. Truth is guarded');
    expect(packet.markdown).toContain('Mara Venn publicly safeguards the corrected atlas.');
    expect(packet.markdown).toContain('- **Continuity:** pass');
    expect(packet.markdown).toContain('- **Narrative logic:** pass');
    expect(packet.markdown).toContain('- **Theme and pacing:** pass');
    expect(packet.markdown).toContain('_No unresolved findings._');
    expect(packet.markdown.match(/^### [1-6]\. /gm)).toHaveLength(6);

    expect(packet.markdown).not.toContain('openrouter/test-model');
    expect(packet.markdown).not.toContain('eve-story_editor');
    expect(packet.markdown.toLowerCase()).not.toContain('chain-of-thought');
    expect(packet.markdown.toLowerCase()).not.toContain('token usage');
  });

  it('records exact source IDs, versions, and hashes in stable provenance order', () => {
    const input = writerPacketInput();
    const packet = renderWriterPacket(input);
    const sources = [
      input.snapshot,
      input.brief,
      input.pitchSlate,
      input.selection,
      input.characterPlan!,
      input.worldPlan!,
      input.themePlan!,
      input.finalOutline,
      input.continuityReview,
      input.narrativeReview,
      input.themeReview,
    ];

    expect(packet.sourceArtifactIds).toEqual(sources.map((artifact) => artifact.artifactId));
    expect(new Set(packet.sourceArtifactIds).size).toBe(packet.sourceArtifactIds.length);
    for (const artifact of sources) {
      expect(packet.markdown).toContain(
        `- \`${artifact.kind}\` — \`${artifact.artifactId}\` v${artifact.version} — \`${artifact.contentHash}\``,
      );
    }
    expect(packet.markdown).toContain(`outline_artifact_id: "${IDS.outline}"`);
    expect(packet.markdown).toContain('outline_version: 2');
  });

  it('renders a promotion receipt as revision two without changing the pinned grounding revision', () => {
    const fixture = createStoryArtifacts();
    const packet = renderWriterPacket({
      ...writerPacketInput(),
      commitReceipt: fixture.commitReceiptArtifact,
      generatedAt: GENERATED_AT,
    });

    expect(packet.markdown).toContain('canon_revision: 2');
    expect(packet.markdown).toContain('**Status:** Promoted as canon revision 2');
    expect(packet.markdown).toContain(`- **Pinned world:** ${fixture.world.title}, revision 1`);
    expect(packet.sourceArtifactIds.at(-1)).toBe(IDS.receipt);
    expect(packet.markdown).toContain(`\`canon.commit-receipt\` — \`${IDS.receipt}\``);
  });

  it('fails closed when the supplied slate duplicates a pitch branch', () => {
    const fixture = createStoryArtifacts();
    const input = writerPacketInput();
    const pitchA = fixture.pitchSlate.pitches[0]!;
    const withoutPitchB = {
      ...fixture.pitchSlateArtifact,
      content: {
        ...fixture.pitchSlate,
        pitches: [pitchA, { ...pitchA }, fixture.pitchSlate.pitches[2]!],
      },
    };

    expect(() => renderWriterPacket({ ...input, pitchSlate: withoutPitchB })).toThrow(
      'Pitch slate must contain pitch-a, pitch-b, and pitch-c exactly once.',
    );
  });
});
