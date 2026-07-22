import { slugify } from './domain.js';
import {
  CanonSnapshotSchema,
  PitchSelectionSchema,
  WriterPacketSchema,
  type ArtifactEnvelope,
  type CanonCommitReceipt,
} from './artifact-domain.js';
import {
  CharacterPlanSchema,
  ContinuityReviewSchemaV2,
  NarrativeReviewSchema,
  PitchSlateSchema,
  StoryBriefSchema,
  StoryOutlineSchema,
  ThemePacingPlanSchema,
  WorldIntegrationPlanSchema,
} from './story-domain.js';

export type WriterPacketInput = {
  snapshot: ArtifactEnvelope;
  brief: ArtifactEnvelope;
  pitchSlate: ArtifactEnvelope;
  selection: ArtifactEnvelope;
  characterPlan?: ArtifactEnvelope;
  worldPlan?: ArtifactEnvelope;
  themePlan?: ArtifactEnvelope;
  finalOutline: ArtifactEnvelope;
  continuityReview: ArtifactEnvelope;
  narrativeReview: ArtifactEnvelope;
  themeReview: ArtifactEnvelope;
  commitReceipt?: ArtifactEnvelope<CanonCommitReceipt>;
  generatedAt?: string;
};

function bullets(values: string[], empty = '_None_'): string {
  return values.length ? values.map((value) => `- ${value}`).join('\n') : empty;
}

function artifactLine(artifact: ArtifactEnvelope): string {
  return `- \`${artifact.kind}\` — \`${artifact.artifactId}\` v${artifact.version} — \`${artifact.contentHash}\``;
}

export function renderWriterPacket(input: WriterPacketInput) {
  const snapshot = CanonSnapshotSchema.parse(input.snapshot.content);
  const brief = StoryBriefSchema.parse(input.brief.content);
  const slate = PitchSlateSchema.parse(input.pitchSlate.content);
  const selection = PitchSelectionSchema.parse(input.selection.content);
  const selectedPitch = slate.pitches.find((pitch) => pitch.id === selection.pitchId);
  if (!selectedPitch) throw new Error(`Selected pitch ${selection.pitchId} is absent from the supplied pitch slate.`);
  const outline = StoryOutlineSchema.parse(input.finalOutline.content);
  const continuity = ContinuityReviewSchemaV2.parse(input.continuityReview.content);
  const narrative = NarrativeReviewSchema.parse(input.narrativeReview.content);
  const themeReview = ThemePacingPlanSchema.parse(input.themeReview.content);
  const characterPlan = input.characterPlan ? CharacterPlanSchema.parse(input.characterPlan.content) : undefined;
  const worldPlan = input.worldPlan ? WorldIntegrationPlanSchema.parse(input.worldPlan.content) : undefined;
  const themePlan = input.themePlan ? ThemePacingPlanSchema.parse(input.themePlan.content) : undefined;
  const sourceArtifacts = [
    input.snapshot,
    input.brief,
    input.pitchSlate,
    input.selection,
    input.characterPlan,
    input.worldPlan,
    input.themePlan,
    input.finalOutline,
    input.continuityReview,
    input.narrativeReview,
    input.themeReview,
    input.commitReceipt,
  ].filter((artifact): artifact is ArtifactEnvelope => artifact !== undefined);
  const generatedAt = input.generatedAt ?? sourceArtifacts
    .map((artifact) => artifact.createdAt)
    .sort()
    .at(-1)!;
  const activeRevision = input.commitReceipt?.content.revision ?? snapshot.revision;
  const promotionState = input.commitReceipt ? `Promoted as canon revision ${activeRevision}` : `Provisional against canon revision ${activeRevision}`;

  const characterSections = outline.characters.map((character) => [
    `### ${character.entityId} — ${character.role}`,
    '',
    `- **External want:** ${character.externalWant}`,
    `- **Internal need:** ${character.internalNeed}`,
    `- **Dilemma:** ${character.dilemma}`,
    `- **Arc:** ${character.arcTurns.join(' → ')}`,
    `- **Canon:** ${character.canonRefs.map((ref) => `\`${ref}\``).join(', ')}`,
  ].join('\n')).join('\n\n');

  const sceneSections = outline.scenes.map((scene, index) => [
    `### ${index + 1}. ${scene.title} (\`${scene.id}\`)`,
    '',
    `**Purpose:** ${scene.purpose}`,
    '',
    `**Setting:** \`${scene.settingEntityId}\`  `,
    `**Participants:** ${scene.participantEntityIds.map((id) => `\`${id}\``).join(', ')}`,
    '',
    `- **Opening state:** ${scene.openingState}`,
    `- **Conflict:** ${scene.conflict}`,
    `- **Turn:** ${scene.turn}`,
    `- **Outcome:** ${scene.outcome}`,
    `- **Canon grounding:** ${scene.canonRefs.map((ref) => `\`${ref}\``).join(', ')}`,
    ...(scene.setupIds.length ? [`- **Setups:** ${scene.setupIds.join(', ')}`] : []),
    ...(scene.payoffIds.length ? [`- **Payoffs:** ${scene.payoffIds.join(', ')}`] : []),
  ].join('\n')).join('\n\n');

  const findings = [
    ...continuity.findings.map((finding) => `- **Continuity/${finding.severity}:** ${finding.issue} — ${finding.repair}`),
    ...narrative.findings.map((finding) => `- **Narrative/${finding.severity}:** ${finding.issue} — ${finding.repair}`),
    ...themeReview.findings.map((finding) => `- **Theme & pacing/${finding.severity}:** ${finding.issue} — ${finding.repair}`),
  ];

  const markdown = [
    '---',
    `world: "${snapshot.world.title.replaceAll('"', '\\"')}"`,
    `world_id: "${snapshot.worldId}"`,
    `canon_revision: ${activeRevision}`,
    `story_run_id: "${input.finalOutline.storyRunId ?? ''}"`,
    `outline_artifact_id: "${input.finalOutline.artifactId}"`,
    `outline_version: ${input.finalOutline.version}`,
    `generated_at: "${generatedAt}"`,
    '---',
    '',
    `# ${outline.title}`,
    '',
    `> ${outline.logline}`,
    '',
    `**Status:** ${promotionState}`,
    '',
    '## Story Brief',
    '',
    `- **Original prompt:** ${brief.prompt}`,
    `- **Genre:** ${brief.genre}`,
    `- **Tone:** ${brief.tone}`,
    `- **Themes:** ${brief.themes.join(', ')}`,
    `- **Required elements:** ${brief.requiredElements.join(', ') || 'None'}`,
    `- **Forbidden elements:** ${brief.forbiddenElements.join(', ') || 'None'}`,
    '',
    '## Chosen Pitch',
    '',
    `### ${selectedPitch.title}`,
    '',
    selectedPitch.logline,
    '',
    `- **Protagonist:** ${selectedPitch.protagonist}`,
    `- **Central conflict:** ${selectedPitch.centralConflict}`,
    `- **Stakes:** ${selectedPitch.stakes}`,
    `- **Ending direction:** ${selectedPitch.endingDirection}`,
    `- **World specificity:** ${selectedPitch.worldSpecificity}`,
    '',
    '## Synopsis',
    '',
    outline.synopsis,
    '',
    '## Cast and Arcs',
    '',
    characterSections,
    ...(characterPlan ? ['', '### Relationship Dynamics', '', bullets(characterPlan.relationshipDynamics)] : []),
    '',
    '## World Grounding',
    '',
    `- **Pinned world:** ${snapshot.world.title}, revision ${snapshot.revision}`,
    `- **Outline canon references:** ${outline.canonRefs.map((ref) => `\`${ref}\``).join(', ')}`,
    ...(worldPlan ? worldPlan.causalUses.map((use) => `- \`${use.canonRef}\` — ${use.storyEffect}`) : []),
    '',
    '## Theme and Pacing',
    '',
    `**Central theme:** ${outline.centralTheme}`,
    ...(themePlan ? ['', ...themePlan.thematicProgression.map((step, index) => `${index + 1}. ${step}`)] : []),
    '',
    '## Scene Outline',
    '',
    sceneSections,
    '',
    '## Canon Impact',
    '',
    `### ${outline.canonDelta.event.title}`,
    '',
    outline.canonDelta.event.summary,
    '',
    '**Consequences**',
    '',
    bullets(outline.canonDelta.event.consequences),
    '',
    '**Entity state changes**',
    '',
    bullets(outline.canonDelta.entityStateChanges.map((change) => `${change.entityId}: ${change.before} → ${change.after} (${change.basisSceneId})`)),
    '',
    '## Editorial Review',
    '',
    `- **Continuity:** ${continuity.verdict}`,
    `- **Narrative logic:** ${narrative.verdict}`,
    `- **Theme and pacing:** ${themeReview.verdict ?? 'advisory'}`,
    '',
    findings.length ? findings.join('\n') : '_No unresolved findings._',
    '',
    '## Artifact Provenance',
    '',
    ...sourceArtifacts.map(artifactLine),
    '',
  ].join('\n');

  return WriterPacketSchema.parse({
    filename: `${slugify(outline.title)}-writer-packet.md`,
    markdown,
    sourceArtifactIds: sourceArtifacts.map((artifact) => artifact.artifactId),
    rendererVersion: 1,
  });
}
