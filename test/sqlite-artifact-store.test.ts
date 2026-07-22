import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { applyCanonDelta, createInitialCanonSnapshot } from '../agent/lib/artifact-domain.js';
import { ArtifactStore } from '../agent/lib/sqlite-artifact-store.js';
import { migrateDatabase } from '../scripts/migrate-database.js';
import { createStoryArtifacts } from './fixtures/story-artifacts.js';

describe('SQLite artifact repository', () => {
  let directory: string;
  let databasePath: string;
  let store: ArtifactStore;

  beforeEach(async () => {
    directory = mkdtempSync(join(tmpdir(), 'story-room-sqlite-'));
    databasePath = join(directory, 'story-room.sqlite');
    await migrateDatabase(databasePath);
    store = new ArtifactStore(databasePath);
  });

  afterEach(() => {
    store.close();
    rmSync(directory, { recursive: true, force: true });
  });

  async function bootstrapAndBegin() {
    const fixture = createStoryArtifacts();
    const snapshot = createInitialCanonSnapshot(fixture.world);
    const bootstrap = await store.bootstrapCanon({ world: fixture.world, normalizedSnapshot: snapshot });
    const begun = await store.beginStory('Write a mystery about a map that remembers every lie.');
    return { fixture, snapshot, bootstrap, begun };
  }

  it('migrates, bootstraps idempotently, and pins new runs to the local canon head', async () => {
    const { fixture, snapshot, bootstrap, begun } = await bootstrapAndBegin();

    expect(bootstrap).toMatchObject({ revision: 1, created: true });
    expect(begun.run.baseCanonRevision).toBe(1);
    expect(begun.run.baseCanonSnapshotArtifactId).toBe(bootstrap.snapshotArtifactId);
    expect(begun.prompt.content).toEqual({ text: 'Write a mystery about a map that remembers every lie.' });

    const editedPrompt = await store.patchArtifact({
      artifactId: begun.prompt.artifactId,
      expectedHash: begun.prompt.contentHash,
      operations: [{ op: 'replace', path: '/content/text', value: 'Write a mystery about a map that remembers every promise.' }],
    });
    expect((await store.getRun(begun.run.storyRunId))?.originalPromptArtifactId).toBe(editedPrompt.artifact.artifactId);

    const repeated = await store.bootstrapCanon({ world: fixture.world, normalizedSnapshot: snapshot });
    expect(repeated).toEqual({ ...bootstrap, created: false });
  });

  it('versions edits, records supersession lineage, and recursively invalidates descendants', async () => {
    const { fixture, begun } = await bootstrapAndBegin();
    const brief = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'story.brief',
      logicalKey: 'story/brief',
      content: fixture.brief,
      producer: { type: 'agent', name: 'prompt_interpreter', gateway: 'openrouter' },
      parents: [{ artifactId: begun.prompt.artifactId, relationship: 'consumes' }],
      nextStatus: 'building_pitches',
    });
    const characterPlan = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'plan.character',
      logicalKey: 'plan/character',
      content: fixture.characterPlanArtifact.content,
      producer: { type: 'agent', name: 'character_architect', gateway: 'openrouter' },
      parents: [{ artifactId: brief.artifactId, relationship: 'consumes' }],
    });

    const edited = await store.patchArtifact({
      artifactId: brief.artifactId,
      expectedHash: brief.contentHash,
      operations: [{ op: 'replace', path: '/content/tone', value: 'tense, intimate, and humane' }],
    });

    expect(edited.artifact.version).toBe(2);
    expect(edited.artifact.producer.type).toBe('human');
    expect(edited.invalidatedArtifactIds).toContain(characterPlan.artifactId);
    expect((await store.getArtifact(brief.artifactId))?.lifecycleStatus).toBe('superseded');
    expect((await store.getArtifact(characterPlan.artifactId))?.lifecycleStatus).toBe('stale');
    expect((await store.getRun(begun.run.storyRunId))?.status).toBe('building_pitches');
    expect(await store.getArtifactLineage(edited.artifact.artifactId)).toEqual(expect.arrayContaining([
      expect.objectContaining({
        direction: 'parent',
        relationship: 'supersedes',
        artifactId: brief.artifactId,
      }),
    ]));
  });

  it('preserves a writer clarification consumed by the brief that supersedes its resolved predecessor', async () => {
    const { fixture, begun } = await bootstrapAndBegin();
    const originalBrief = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'story.brief',
      logicalKey: 'story/brief',
      content: fixture.brief,
      producer: { type: 'agent', name: 'prompt_interpreter', gateway: 'openrouter' },
      parents: [{ artifactId: begun.prompt.artifactId, relationship: 'consumes' }],
      nextStatus: 'building_pitches',
    });
    const conflict = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'prompt.conflict-report',
      logicalKey: 'prompt/conflict-report',
      content: {
        kind: 'prompt.conflict-report',
        verdict: 'clarify',
        conflicts: [{
          issue: 'The prompt implies the erased district never existed.',
          promptClaim: 'The district was invented by the map.',
          canonRef: 'world:foundation',
          canonFact: 'Maps respond to truth but cannot invent matter.',
          resolutionQuestion: 'Should the district be real but suppressed from public maps?',
        }],
        causalUses: [],
        proposedSupportingEntities: [],
        protectedFacts: ['world:foundation'],
        recommendations: [],
      },
      producer: { type: 'agent', name: 'world_integration_advisor', gateway: 'openrouter' },
      parents: [{ artifactId: originalBrief.artifactId, relationship: 'consumes' }],
      expectedStatus: 'building_pitches',
      nextStatus: 'needs_clarification',
    });
    const clarification = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'prompt.clarification',
      logicalKey: 'prompt/clarification/writer-answer',
      content: {
        text: 'The district is real but was deliberately suppressed from public maps.',
        conflictArtifactId: conflict.artifactId,
      },
      producer: { type: 'human', name: 'writer' },
      parents: [{ artifactId: begun.prompt.artifactId, relationship: 'consumes' }],
      expectedStatus: 'needs_clarification',
      nextStatus: 'analyzing',
    });

    const regeneratedBrief = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'story.brief',
      logicalKey: 'story/brief',
      content: {
        ...fixture.brief,
        requiredElements: [...fixture.brief.requiredElements, 'the district is real but suppressed'],
      },
      producer: { type: 'agent', name: 'prompt_interpreter', gateway: 'openrouter' },
      parents: [
        { artifactId: begun.prompt.artifactId, relationship: 'consumes' },
        { artifactId: clarification.artifactId, relationship: 'consumes' },
      ],
      supersedesArtifactId: originalBrief.artifactId,
      expectedSupersededHash: originalBrief.contentHash,
      expectedStatus: 'analyzing',
      nextStatus: 'building_pitches',
    });

    expect((await store.getArtifact(originalBrief.artifactId))?.lifecycleStatus).toBe('superseded');
    expect((await store.getArtifact(conflict.artifactId))?.lifecycleStatus).toBe('stale');
    expect((await store.getArtifact(clarification.artifactId))?.lifecycleStatus).toBe('active');
    expect((await store.getArtifact(regeneratedBrief.artifactId))?.lifecycleStatus).toBe('active');
    expect((await store.getRun(begun.run.storyRunId))?.briefArtifactId).toBe(regeneratedBrief.artifactId);
    expect(await store.getArtifactLineage(regeneratedBrief.artifactId)).toEqual(expect.arrayContaining([
      expect.objectContaining({
        direction: 'parent',
        relationship: 'consumes',
        artifactId: clarification.artifactId,
        lifecycleStatus: 'active',
      }),
      expect.objectContaining({
        direction: 'parent',
        relationship: 'supersedes',
        artifactId: originalBrief.artifactId,
        lifecycleStatus: 'superseded',
      }),
    ]));
  });

  it('accepts only one of two edits racing on the same expected hash', async () => {
    const { fixture, begun } = await bootstrapAndBegin();
    const brief = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'story.brief',
      logicalKey: 'story/brief',
      content: fixture.brief,
      producer: { type: 'agent', name: 'prompt_interpreter', gateway: 'openrouter' },
      parents: [{ artifactId: begun.prompt.artifactId, relationship: 'consumes' }],
    });
    const secondConnection = new ArtifactStore(databasePath);
    try {
      const results = await Promise.allSettled([
        store.patchArtifact({
          artifactId: brief.artifactId,
          expectedHash: brief.contentHash,
          operations: [{ op: 'replace', path: '/content/tone', value: 'quietly ominous' }],
        }),
        secondConnection.patchArtifact({
          artifactId: brief.artifactId,
          expectedHash: brief.contentHash,
          operations: [{ op: 'replace', path: '/content/tone', value: 'openly confrontational' }],
        }),
      ]);
      expect(results.filter((result) => result.status === 'fulfilled')).toHaveLength(1);
      expect(results.filter((result) => result.status === 'rejected')).toHaveLength(1);
    } finally {
      secondConnection.close();
    }
  });

  it('atomically promotes a reviewed outline and pins the next story to revision two', async () => {
    const { fixture, begun } = await bootstrapAndBegin();
    const outline = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'outline.final',
      logicalKey: 'outline/final',
      content: fixture.outline,
      producer: { type: 'agent', name: 'story_editor', gateway: 'openrouter' },
      parents: [{ artifactId: begun.prompt.artifactId, relationship: 'derives-from' }],
      nextStatus: 'reviewing',
    });
    const reviewInputs = [
      ['review.continuity', 'review/final/continuity', fixture.continuityReviewArtifact.content, 'continuity_critic'],
      ['review.narrative', 'review/final/narrative', fixture.narrativeReviewArtifact.content, 'narrative_logic_critic'],
      ['review.theme-pacing', 'review/final/theme-pacing', fixture.themeReviewArtifact.content, 'theme_pacing_critic'],
    ] as const;
    const reviews = [];
    for (const [kind, logicalKey, reviewContent, agentName] of reviewInputs) {
      reviews.push(await store.saveArtifact({
        storyRunId: begun.run.storyRunId,
        kind,
        logicalKey,
        content: { ...reviewContent, targetArtifactId: outline.artifactId, targetContentHash: outline.contentHash },
        producer: { type: 'agent', name: agentName, gateway: 'openrouter' },
        parents: [{ artifactId: outline.artifactId, relationship: 'reviews' }],
      }));
    }
    const delta = await store.saveArtifact({
      storyRunId: begun.run.storyRunId,
      kind: 'canon.delta',
      logicalKey: 'canon/proposed-delta',
      content: fixture.outline.canonDelta,
      producer: { type: 'tool', name: 'finalize_outline' },
      parents: [
        { artifactId: outline.artifactId, relationship: 'derives-from' },
        ...reviews.map((review) => ({ artifactId: review.artifactId, relationship: 'consumes' as const })),
      ],
      expectedStatus: 'reviewing',
      nextStatus: 'ready_for_promotion',
    });
    const pinnedSnapshot = await store.getArtifact(begun.run.baseCanonSnapshotArtifactId);
    const nextSnapshot = applyCanonDelta(pinnedSnapshot!.content, delta.content);
    const receipt = await store.promoteOutline({
      storyRunId: begun.run.storyRunId,
      finalOutlineArtifactId: outline.artifactId,
      canonDeltaArtifactId: delta.artifactId,
      nextSnapshotContent: nextSnapshot,
    });

    expect(receipt.kind).toBe('canon.commit-receipt');
    expect((receipt.content as { revision: number }).revision).toBe(2);
    expect((await store.promoteOutline({
      storyRunId: begun.run.storyRunId,
      finalOutlineArtifactId: outline.artifactId,
      canonDeltaArtifactId: delta.artifactId,
      nextSnapshotContent: nextSnapshot,
    })).artifactId).toBe(receipt.artifactId);
    const nextRun = await store.beginStory('Tell the next story after the public correction.');
    expect(nextRun.run.baseCanonRevision).toBe(2);
    expect(nextRun.run.baseCanonSnapshotArtifactId).toBe((receipt.content as { snapshotArtifactId: string }).snapshotArtifactId);
  });
});
