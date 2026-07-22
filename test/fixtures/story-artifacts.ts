import { offlineWorld } from '../../agent/lib/deterministic.js';
import {
  artifactContentHash,
  createInitialCanonSnapshot,
  makeArtifactEnvelope,
  type ArtifactEnvelope,
  type CanonCommitReceipt,
} from '../../agent/lib/artifact-domain.js';
import type {
  CanonDelta,
  CharacterPlan,
  ContinuityReviewV2,
  NarrativeReview,
  PitchSlate,
  StoryBrief,
  StoryOutline,
  ThemePacingPlan,
  WorldIntegrationPlan,
} from '../../agent/lib/story-domain.js';

export const IDS = {
  snapshot: '00000000-0000-4000-8000-000000000001',
  run: '00000000-0000-4000-8000-000000000002',
  brief: '00000000-0000-4000-8000-000000000003',
  slate: '00000000-0000-4000-8000-000000000004',
  selection: '00000000-0000-4000-8000-000000000005',
  characterPlan: '00000000-0000-4000-8000-000000000006',
  worldPlan: '00000000-0000-4000-8000-000000000007',
  themePlan: '00000000-0000-4000-8000-000000000008',
  outline: '00000000-0000-4000-8000-000000000009',
  continuity: '00000000-0000-4000-8000-000000000010',
  narrative: '00000000-0000-4000-8000-000000000011',
  themeReview: '00000000-0000-4000-8000-000000000012',
  promotedSnapshot: '00000000-0000-4000-8000-000000000013',
  delta: '00000000-0000-4000-8000-000000000014',
  receipt: '00000000-0000-4000-8000-000000000015',
} as const;

const CREATED_AT = '2030-01-02T03:04:05.000Z';

function agent(name: string) {
  return {
    type: 'agent' as const,
    name,
    modelId: 'openrouter/test-model',
    gateway: 'openrouter' as const,
    eveSessionId: `eve-${name}`,
  };
}

export function createStoryArtifacts() {
  const world = offlineWorld('A city built inside a sleeping sky-whale', 42);
  const snapshot = createInitialCanonSnapshot(world);
  const snapshotArtifact = makeArtifactEnvelope({
    artifactId: IDS.snapshot,
    storyRunId: null,
    kind: 'canon.snapshot',
    logicalKey: 'canon/snapshot/1',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: snapshot,
    producer: { type: 'tool', name: 'bootstrap_canon' },
    createdAt: CREATED_AT,
  });

  const worldRef = 'world:foundation';
  const maraRef = 'entity:mara-venn';
  const placeRef = 'entity:aster-reach';
  const mara = snapshot.world.entities.find((entity) => entity.id === 'mara-venn')!;

  const brief: StoryBrief = {
    prompt: 'Write a mystery about a truthful map that erases its cartographer.',
    workingTitle: 'The Map That Forgot',
    genre: 'fantasy mystery',
    tone: 'wondrous and tense',
    themes: ['truth has a cost', 'memory and civic duty'],
    requiredElements: ['a disappearing district'],
    forbiddenElements: ['resurrection'],
    storyScale: 'short',
    sceneTarget: { min: 6, max: 8 },
    canonQuestions: [],
  };
  const briefArtifact = makeArtifactEnvelope({
    artifactId: IDS.brief,
    storyRunId: IDS.run,
    kind: 'story.brief',
    logicalKey: 'story/brief',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: brief,
    producer: agent('prompt_interpreter'),
    createdAt: CREATED_AT,
  });

  const pitchSlate: PitchSlate = {
    pitches: [
      {
        id: 'pitch-a',
        branchId: 'A',
        title: 'The Private Blank',
        logline: 'Mara risks her memories to restore one erased home.',
        protagonist: 'Mara Venn',
        centralConflict: 'Each truthful correction removes one of Mara’s memories.',
        stakes: 'One family and Mara’s identity.',
        endingDirection: 'Mara saves the home but forgets why it mattered.',
        characterPromise: 'An intimate sacrifice built from voluntary choices.',
        worldSpecificity: 'Truth-responsive maps make memory a civic resource.',
        canonRefs: [maraRef, placeRef],
        proposedSupportingEntities: [],
      },
      {
        id: 'pitch-b',
        branchId: 'B',
        title: 'The Map That Forgot',
        logline: 'Mara follows a truthful map into a district the city denies exists.',
        protagonist: 'Mara Venn',
        centralConflict: 'The map exposes a civic lie while erasing its own maker.',
        stakes: 'The lower wards will detach unless the lie is made public.',
        endingDirection: 'Mara publishes the truth and accepts a changed city.',
        characterPromise: 'Mara chooses public truth over control of the discovery.',
        worldSpecificity: 'Communal lies physically corrupt maps in Aster Reach.',
        canonRefs: [worldRef, maraRef],
        proposedSupportingEntities: [],
      },
      {
        id: 'pitch-c',
        branchId: 'C',
        title: 'The Surveyors’ Vote',
        logline: 'A public map audit forces Mara to choose which ward survives.',
        protagonist: 'Mara Venn',
        centralConflict: 'Competing truths pull gravity in incompatible directions.',
        stakes: 'The city’s shared map and political legitimacy.',
        endingDirection: 'The wards adopt a plural atlas at a permanent cost.',
        characterPromise: 'Mara shifts from lone investigator to reluctant institution builder.',
        worldSpecificity: 'Cartography is literal infrastructure in the sleeping host.',
        canonRefs: [worldRef, placeRef],
        proposedSupportingEntities: [],
      },
    ],
    editorialNote: 'Each branch is distinct; pitch B best satisfies the mystery prompt.',
  };
  const pitchSlateArtifact = makeArtifactEnvelope({
    artifactId: IDS.slate,
    storyRunId: IDS.run,
    kind: 'pitch.slate',
    logicalKey: 'pitch/slate',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: pitchSlate,
    producer: agent('story_editor'),
    createdAt: CREATED_AT,
  });

  const selectionArtifact = makeArtifactEnvelope({
    artifactId: IDS.selection,
    storyRunId: IDS.run,
    kind: 'decision.pitch-selection',
    logicalKey: 'decision/pitch-selection',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: {
      pitchSlateArtifactId: IDS.slate,
      pitchSlateHash: pitchSlateArtifact.contentHash,
      pitchId: 'pitch-b',
      selectedAt: CREATED_AT,
    },
    producer: { type: 'human', name: 'writer' },
    createdAt: CREATED_AT,
  });

  const characterPlan: CharacterPlan = {
    kind: 'plan.character',
    characters: [{
      entityId: 'mara-venn',
      role: 'protagonist',
      externalWant: 'Restore the erased district.',
      internalNeed: 'Trust the public with an unfinished truth.',
      dilemma: 'Control the map or preserve the city’s shared memory.',
      arcTurns: ['Hides the map', 'Shares the map', 'Publishes the correction'],
      canonRefs: [maraRef],
    }],
    relationshipDynamics: ['Mara’s distrust of the cartographers becomes reluctant cooperation.'],
    recommendations: [],
  };
  const characterPlanArtifact = makeArtifactEnvelope({
    artifactId: IDS.characterPlan,
    storyRunId: IDS.run,
    kind: 'plan.character',
    logicalKey: 'plan/character',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: characterPlan,
    producer: agent('character_architect'),
    createdAt: CREATED_AT,
  });

  const worldPlan: WorldIntegrationPlan = {
    kind: 'plan.world',
    verdict: 'safe',
    conflicts: [],
    causalUses: [
      { canonRef: worldRef, storyEffect: 'The world premise makes every map correction physically consequential.' },
      { canonRef: maraRef, storyEffect: 'Mara’s existing investigation makes her the necessary discoverer.' },
    ],
    proposedSupportingEntities: [],
    protectedFacts: [worldRef, maraRef],
    recommendations: [],
  };
  const worldPlanArtifact = makeArtifactEnvelope({
    artifactId: IDS.worldPlan,
    storyRunId: IDS.run,
    kind: 'plan.world',
    logicalKey: 'plan/world',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: worldPlan,
    producer: agent('world_integration_advisor'),
    createdAt: CREATED_AT,
  });

  const themePlan: ThemePacingPlan = {
    kind: 'plan.theme-pacing',
    mode: 'plan',
    centralTheme: 'Shared truth costs private certainty.',
    thematicProgression: ['Truth is guarded', 'Truth is tested', 'Truth is shared'],
    pacingShape: [
      { segment: 'opening', pressure: 'low', purpose: 'Establish the impossible absence.' },
      { segment: 'investigation', pressure: 'high', purpose: 'Make each discovery destabilize the city.' },
      { segment: 'choice', pressure: 'peak', purpose: 'Force publication of the truth.' },
    ],
    findings: [],
  };
  const themePlanArtifact = makeArtifactEnvelope({
    artifactId: IDS.themePlan,
    storyRunId: IDS.run,
    kind: 'plan.theme-pacing',
    logicalKey: 'plan/theme-pacing',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: themePlan,
    producer: agent('theme_pacing_critic'),
    createdAt: CREATED_AT,
  });

  const canonDelta: CanonDelta = {
    event: {
      id: 'the-public-correction',
      title: 'The Public Correction',
      summary: 'Mara publishes the suppressed district map and stabilizes the lower wards.',
      consequences: ['Aster Reach recognizes the erased district.', 'Mara becomes a public custodian of the atlas.'],
      participantEntityIds: ['mara-venn'],
      occursAfterEventId: null,
    },
    newEntities: [],
    newRelationships: [],
    entityStateChanges: [{
      entityId: 'mara-venn',
      before: mara.summary,
      after: 'Mara Venn publicly safeguards the corrected atlas.',
      basisSceneId: 'scene-06',
    }],
  };

  const outline: StoryOutline = {
    title: 'The Map That Forgot',
    logline: 'Mara follows a truthful map into a district the city denies exists.',
    synopsis: 'A disappearing district forces Mara to expose a communal lie before gravity tears the lower wards loose.',
    selectedPitchId: 'pitch-b',
    characters: characterPlan.characters,
    centralTheme: themePlan.centralTheme,
    scenes: Array.from({ length: 6 }, (_, index) => {
      const number = index + 1;
      const id = `scene-${String(number).padStart(2, '0')}`;
      return {
        id,
        title: ['The Blank Street', 'A Map Remembers', 'The Cartographers Refuse', 'The Ward Tilts', 'A Public Choice', 'The Correction'][index]!,
        beatIds: [`beat-${String(number).padStart(2, '0')}`],
        purpose: `Advance the investigation through turn ${number}.`,
        settingEntityId: 'aster-reach',
        participantEntityIds: ['mara-venn'],
        openingState: `Mara enters stage ${number} with incomplete evidence.`,
        conflict: 'The city’s official map contradicts lived reality.',
        turn: `Mara obtains consequence ${number} of the hidden truth.`,
        outcome: `The public correction becomes ${number === 6 ? 'unavoidable' : 'more costly'}.`,
        canonRefs: [worldRef, maraRef],
        setupIds: number === 1 ? ['forgotten-mark'] : [],
        payoffIds: number === 6 ? ['forgotten-mark'] : [],
      };
    }),
    canonRefs: [worldRef, maraRef],
    canonDelta,
  };
  const finalOutlineArtifact = makeArtifactEnvelope({
    artifactId: IDS.outline,
    storyRunId: IDS.run,
    kind: 'outline.final',
    logicalKey: 'outline/final',
    version: 2,
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: outline,
    producer: agent('story_editor'),
    createdAt: CREATED_AT,
  });

  const continuityReview: ContinuityReviewV2 = {
    kind: 'review.continuity',
    targetArtifactId: IDS.outline,
    targetContentHash: finalOutlineArtifact.contentHash,
    verdict: 'pass',
    findings: [],
    verifiedCanonRefs: [worldRef, maraRef],
  };
  const continuityReviewArtifact = makeArtifactEnvelope({
    artifactId: IDS.continuity,
    storyRunId: IDS.run,
    kind: 'review.continuity',
    logicalKey: 'review/continuity',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: continuityReview,
    producer: agent('continuity_critic'),
    createdAt: CREATED_AT,
  });

  const narrativeReview: NarrativeReview = {
    kind: 'review.narrative',
    targetArtifactId: IDS.outline,
    targetContentHash: finalOutlineArtifact.contentHash,
    verdict: 'pass',
    findings: [],
    strengths: ['Each discovery causes the next choice.'],
  };
  const narrativeReviewArtifact = makeArtifactEnvelope({
    artifactId: IDS.narrative,
    storyRunId: IDS.run,
    kind: 'review.narrative',
    logicalKey: 'review/narrative',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: narrativeReview,
    producer: agent('narrative_logic_critic'),
    createdAt: CREATED_AT,
  });

  const themeReview: ThemePacingPlan = {
    kind: 'review.theme-pacing',
    mode: 'review',
    targetArtifactId: IDS.outline,
    targetContentHash: finalOutlineArtifact.contentHash,
    centralTheme: themePlan.centralTheme,
    thematicProgression: themePlan.thematicProgression,
    pacingShape: themePlan.pacingShape,
    verdict: 'pass',
    findings: [],
  };
  const themeReviewArtifact = makeArtifactEnvelope({
    artifactId: IDS.themeReview,
    storyRunId: IDS.run,
    kind: 'review.theme-pacing',
    logicalKey: 'review/theme-pacing',
    canonRevision: 1,
    canonSnapshotArtifactId: IDS.snapshot,
    content: themeReview,
    producer: agent('theme_pacing_critic'),
    createdAt: CREATED_AT,
  });

  const receipt: CanonCommitReceipt = {
    worldId: 'shared-world',
    storyRunId: IDS.run,
    previousRevision: 1,
    revision: 2,
    snapshotArtifactId: IDS.promotedSnapshot,
    snapshotHash: artifactContentHash({ revision: 2, eventId: canonDelta.event.id }),
    deltaArtifactId: IDS.delta,
    finalOutlineArtifactId: IDS.outline,
    eventId: canonDelta.event.id,
    committedAt: CREATED_AT,
  };
  const commitReceiptArtifact = makeArtifactEnvelope({
    artifactId: IDS.receipt,
    storyRunId: IDS.run,
    kind: 'canon.commit-receipt',
    logicalKey: 'canon/commit-receipt',
    canonRevision: 2,
    canonSnapshotArtifactId: IDS.promotedSnapshot,
    content: receipt,
    producer: { type: 'tool', name: 'promote_outline' },
    createdAt: CREATED_AT,
  });

  return {
    world,
    snapshot,
    snapshotArtifact,
    brief,
    briefArtifact,
    pitchSlate,
    pitchSlateArtifact,
    selectionArtifact,
    characterPlanArtifact,
    worldPlanArtifact,
    themePlanArtifact,
    canonDelta,
    outline,
    finalOutlineArtifact,
    continuityReviewArtifact,
    narrativeReviewArtifact,
    themeReviewArtifact,
    commitReceiptArtifact,
  };
}

export function asHuman<T>(artifact: ArtifactEnvelope<T>): ArtifactEnvelope<T> {
  return {
    ...artifact,
    producer: { type: 'human', name: 'writer' },
  };
}
