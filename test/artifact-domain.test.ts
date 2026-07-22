import { describe, expect, it } from 'vitest';
import {
  ArtifactEnvelopeSchema,
  NON_EDITABLE_ARTIFACT_KINDS,
  applyArtifactPatch,
  applyCanonDelta,
  artifactContentHash,
  assertPromotionReady,
  createInitialCanonSnapshot,
  makeArtifactEnvelope,
  statusAfterArtifactEdit,
  validateArtifactContent,
  validateStoryOutline,
  type ArtifactEnvelope,
  type ArtifactKind,
} from '../agent/lib/artifact-domain.js';
import { offlineWorld } from '../agent/lib/deterministic.js';
import { applyArtifactPatch as applyStoredContentPatch } from '../agent/lib/artifact-store.js';
import type { CanonDelta, StoryBrief, StoryOutline } from '../agent/lib/story-domain.js';
import { IDS, asHuman, createStoryArtifacts } from './fixtures/story-artifacts.js';

describe('canonical artifact hashing', () => {
  it('is independent of object key insertion order and has a pinned SHA-256 value', () => {
    const first = { b: 2, nested: { z: true, a: 'value' }, a: 1 };
    const second = { a: 1, nested: { a: 'value', z: true }, b: 2 };

    expect(artifactContentHash(first)).toBe(artifactContentHash(second));
    expect(artifactContentHash({ b: 2, a: 1 })).toBe(
      '43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777',
    );
  });

  it('normalizes undefined consistently and rejects non-JSON numeric values', () => {
    expect(artifactContentHash({ kept: 1, omitted: undefined })).toBe(artifactContentHash({ kept: 1 }));
    expect(artifactContentHash([1, undefined, 3])).toBe(artifactContentHash([1, null, 3]));
    expect(() => artifactContentHash({ value: Number.POSITIVE_INFINITY })).toThrow('non-finite');
  });
});

describe('canon snapshots and deltas', () => {
  it('creates a deterministic revision-one snapshot with stable, resolvable fact references', () => {
    const world = offlineWorld('A city built inside a sleeping sky-whale', 42);
    const first = createInitialCanonSnapshot(world);
    const second = createInitialCanonSnapshot(structuredClone(world));

    expect(first).toEqual(second);
    expect(first).toMatchObject({ worldId: 'shared-world', revision: 1, timeline: [] });
    expect(first.entityStates).toHaveLength(world.entities.length);
    expect(first.entityStates).toEqual(world.entities.map((entity) => ({
      entityId: entity.id,
      state: entity.summary,
      lastChangedEventId: null,
    })));

    const refs = first.facts.map((fact) => fact.ref);
    expect(new Set(refs).size).toBe(refs.length);
    expect(refs).toContain('world:foundation');
    for (const entity of world.entities) expect(refs).toContain(`entity:${entity.id}`);
    expect(first.facts.filter((fact) => fact.category === 'law')).toHaveLength(world.laws.length);
    expect(first.facts.filter((fact) => fact.category === 'history')).toHaveLength(world.history.length);
    expect(first.facts.filter((fact) => fact.category === 'relationship')).toHaveLength(world.relationships.length);
    expect(first.facts.filter((fact) => fact.category === 'state')).toHaveLength(world.entities.length);
  });

  it('applies an append-only event, supporting entity, relationship, and exact state transition', () => {
    const { snapshot } = createStoryArtifacts();
    const mara = snapshot.world.entities.find((entity) => entity.id === 'mara-venn')!;
    const delta: CanonDelta = {
      event: {
        id: 'the-public-correction',
        title: 'The Public Correction',
        summary: 'A suppressed district returns to the public atlas.',
        consequences: ['The lower wards stabilize.'],
        participantEntityIds: ['mara-venn', 'ila-reed'],
        occursAfterEventId: null,
      },
      newEntities: [{
        id: 'ila-reed',
        name: 'Ila Reed',
        kind: 'character',
        summary: 'A witness from the erased district.',
        wants: 'Public recognition of her home.',
        tags: ['witness'],
      }],
      newRelationships: [{
        from: 'ila-reed',
        to: 'mara-venn',
        type: 'protects',
        detail: 'Ila protects Mara while she corrects the atlas.',
      }],
      entityStateChanges: [{
        entityId: 'mara-venn',
        before: mara.summary,
        after: 'Mara publicly safeguards the corrected atlas.',
        basisSceneId: 'scene-06',
      }],
    };
    const original = structuredClone(snapshot);

    const next = applyCanonDelta(snapshot, delta);

    expect(snapshot).toEqual(original);
    expect(next.revision).toBe(2);
    expect(next.timeline).toEqual([delta.event]);
    expect(next.world.entities).toContainEqual(delta.newEntities[0]);
    expect(next.world.relationships).toContainEqual(delta.newRelationships[0]);
    expect(next.entityStates).toContainEqual({
      entityId: 'ila-reed',
      state: 'A witness from the erased district.',
      lastChangedEventId: 'the-public-correction',
    });
    expect(next.entityStates).toContainEqual({
      entityId: 'mara-venn',
      state: 'Mara publicly safeguards the corrected atlas.',
      lastChangedEventId: 'the-public-correction',
    });
    expect(next.facts.map((fact) => fact.ref)).toEqual(expect.arrayContaining([
      'entity:ila-reed',
      'event:the-public-correction',
    ]));
  });

  it.each([
    {
      name: 'a duplicate entity',
      mutate(delta: CanonDelta) {
        delta.newEntities.push({
          id: 'mara-venn', name: 'Duplicate Mara', kind: 'character', summary: 'Duplicate.', wants: 'Exist.', tags: [],
        });
      },
      message: 'Canon delta duplicates entity: mara-venn',
    },
    {
      name: 'a non-append-only event',
      mutate(delta: CanonDelta) { delta.event.occursAfterEventId = 'unknown-event'; },
      message: 'Canon event must occur after the foundation',
    },
    {
      name: 'an unknown event participant',
      mutate(delta: CanonDelta) { delta.event.participantEntityIds.push('missing-person'); },
      message: 'Unknown canon event participant: missing-person',
    },
    {
      name: 'a relationship with a missing endpoint',
      mutate(delta: CanonDelta) {
        delta.newRelationships.push({ from: 'mara-venn', to: 'missing-place', type: 'protects', detail: 'Impossible.' });
      },
      message: 'New relationship contains unknown endpoint',
    },
    {
      name: 'an inexact before-state',
      mutate(delta: CanonDelta) { delta.entityStateChanges[0]!.before = 'A stale description.'; },
      message: 'State mismatch for mara-venn',
    },
  ])('rejects $name', ({ mutate, message }) => {
    const { snapshot, canonDelta } = createStoryArtifacts();
    const invalid = structuredClone(canonDelta);
    mutate(invalid);
    expect(() => applyCanonDelta(snapshot, invalid)).toThrow(message);
  });

  it('rejects foundational entity kinds in a story canon delta', () => {
    const { snapshot, canonDelta } = createStoryArtifacts();
    const invalid = structuredClone(canonDelta) as unknown as { newEntities: Array<Record<string, unknown>> };
    invalid.newEntities.push({
      id: 'new-faction', name: 'New Faction', kind: 'faction', summary: 'Not supporting canon.', wants: 'Power.', tags: [],
    });
    expect(() => applyCanonDelta(snapshot, invalid)).toThrow();
  });
});

describe('artifact envelopes and editing', () => {
  it('constructs a validated envelope with canonical content hash and provenance', () => {
    const content = { text: 'A precise story prompt.' };
    const envelope = makeArtifactEnvelope({
      artifactId: IDS.brief,
      storyRunId: IDS.run,
      branchId: 'B',
      kind: 'prompt.original',
      logicalKey: 'prompt/original',
      version: 3,
      canonRevision: 1,
      canonSnapshotArtifactId: IDS.snapshot,
      content,
      producer: { type: 'human', name: 'writer' },
      createdAt: '2030-01-02T03:04:05.000Z',
    });

    expect(() => ArtifactEnvelopeSchema.parse(envelope)).not.toThrow();
    expect(envelope).toMatchObject({
      artifactId: IDS.brief,
      worldId: 'shared-world',
      storyRunId: IDS.run,
      branchId: 'B',
      kind: 'prompt.original',
      schemaVersion: 1,
      logicalKey: 'prompt/original',
      version: 3,
      canonRevision: 1,
      canonSnapshotArtifactId: IDS.snapshot,
      content,
      producer: { type: 'human', name: 'writer' },
    });
    expect(envelope.contentHash).toBe(artifactContentHash(content));
  });

  it('validates content against its artifact kind before constructing or accepting it', () => {
    expect(() => validateArtifactContent('story.brief', { prompt: 'Missing all required brief fields.' })).toThrow();
    expect(() => makeArtifactEnvelope({
      storyRunId: IDS.run,
      kind: 'prompt.original',
      logicalKey: 'prompt/original',
      canonRevision: 1,
      canonSnapshotArtifactId: IDS.snapshot,
      content: { text: '' },
      producer: { type: 'human', name: 'writer' },
    })).toThrow();
  });

  it('applies RFC 6902 operations only under content and leaves the source envelope immutable', () => {
    const { briefArtifact } = createStoryArtifacts();
    const original = structuredClone(briefArtifact);
    const patched = applyArtifactPatch<StoryBrief>(briefArtifact, [
      { op: 'test', path: '/content/prompt', value: briefArtifact.content.prompt },
      { op: 'replace', path: '/content/prompt', value: 'Write a mystery about a map that remembers every lie.' },
      { op: 'add', path: '/content/canonQuestions/-', value: 'Who is allowed to certify a public truth?' },
      { op: 'copy', from: '/content/themes/0', path: '/content/themes/-' },
    ]);

    expect(briefArtifact).toEqual(original);
    expect(patched.prompt).toContain('remembers every lie');
    expect(patched.canonQuestions).toContain('Who is allowed to certify a public truth?');
    expect(patched.themes.at(-1)).toBe(patched.themes[0]);
    expect(artifactContentHash(patched)).not.toBe(briefArtifact.contentHash);
  });

  it('enforces test/hash-style optimistic checks and rejects envelope or unsafe paths', () => {
    const { briefArtifact } = createStoryArtifacts();
    expect(() => applyArtifactPatch(briefArtifact, [
      { op: 'test', path: '/content/prompt', value: 'A stale prompt value.' },
      { op: 'replace', path: '/content/prompt', value: 'Should never apply.' },
    ])).toThrow('JSON Patch test failed');
    expect(() => applyArtifactPatch(briefArtifact, [
      { op: 'replace', path: '/producer/name', value: 'forged-producer' },
    ])).toThrow('only /content');
    expect(() => applyArtifactPatch(briefArtifact, [
      { op: 'copy', from: '/producer/name', path: '/content/prompt' },
    ])).toThrow('only /content');
    expect(() => applyArtifactPatch(briefArtifact, [
      { op: 'add', path: '/content/__proto__/polluted', value: true },
    ])).toThrow('Unsafe JSON Pointer');
  });

  it('rejects lookalike content roots in the persistence-layer patcher', () => {
    expect(() => applyStoredContentPatch({ prompt: 'Original' }, [
      { op: 'add', path: '/contents/prompt', value: 'Forged sibling root' },
    ])).toThrow('only modify /content');
    expect(() => applyStoredContentPatch({ prompt: 'Original' }, [
      { op: 'copy', from: '/contents/prompt', path: '/content/prompt' },
    ])).toThrow('only read /content');
  });

  it('validates patched content before returning it', () => {
    const { briefArtifact } = createStoryArtifacts();
    expect(() => applyArtifactPatch(briefArtifact, [
      { op: 'remove', path: '/content/genre' },
    ])).toThrow();
  });

  it('rejects edits for every immutable artifact kind', () => {
    const { snapshotArtifact } = createStoryArtifacts();
    for (const kind of NON_EDITABLE_ARTIFACT_KINDS) {
      const envelope = { ...snapshotArtifact, kind } as ArtifactEnvelope;
      expect(() => applyArtifactPatch(envelope, [
        { op: 'add', path: '/content/test', value: true },
      ]), kind).toThrow(`${kind} artifacts are immutable.`);
    }
  });
});

describe('outline validation, invalidation, and promotion gates', () => {
  it('accepts a grounded outline and reports all deterministic structural violations', () => {
    const { outline, snapshot } = createStoryArtifacts();
    expect(validateStoryOutline(outline, snapshot)).toEqual([]);

    const invalid: StoryOutline = structuredClone(outline);
    invalid.scenes[1]!.id = 'scene-01';
    invalid.scenes[2]!.settingEntityId = 'missing-place';
    invalid.scenes[3]!.participantEntityIds.push('missing-person');
    invalid.scenes[4]!.canonRefs.push('entity:missing');
    invalid.scenes[5]!.payoffIds.push('orphan-payoff');
    invalid.canonRefs.push('law:missing');
    invalid.characters[0]!.canonRefs.push('entity:missing-character-ref');
    invalid.canonDelta.entityStateChanges[0]!.basisSceneId = 'scene-99';
    invalid.canonDelta.entityStateChanges[0]!.before = 'A stale state.';

    expect(validateStoryOutline(invalid, snapshot)).toEqual(expect.arrayContaining([
      'duplicate scene id: scene-01',
      'unknown scene setting: missing-place',
      'unknown scene participant: missing-person',
      'unknown scene canon reference: entity:missing',
      'unknown outline canon reference: law:missing',
      'unknown character canon reference: entity:missing-character-ref',
      'payoff has no setup: orphan-payoff',
      'state change cites unknown scene: scene-99',
    ]));
    expect(validateStoryOutline(invalid, snapshot).some((issue) => issue.includes('State mismatch for mara-venn'))).toBe(true);
  });

  it.each([
    ['story.brief', 'building_pitches'],
    ['canon.dossier', 'building_pitches'],
    ['pitch.seed', 'building_pitches'],
    ['pitch.slate', 'building_pitches'],
    ['review.pitch-continuity', 'building_pitches'],
    ['decision.pitch-selection', 'planning'],
    ['plan.character', 'planning'],
    ['outline.blueprint', 'planning'],
    ['outline.scenes', 'needs_revision'],
    ['outline.final', 'needs_revision'],
    ['review.continuity', 'needs_revision'],
    ['prompt.original', 'analyzing'],
  ] as const)('maps an edit of %s to %s', (kind, status) => {
    expect(statusAfterArtifactEdit(kind as ArtifactKind)).toBe(status);
  });

  it('accepts three exact agent review certificates for the active outline hash', () => {
    const fixture = createStoryArtifacts();
    expect(assertPromotionReady({
      outline: fixture.outline,
      snapshot: fixture.snapshot,
      outlineArtifact: fixture.finalOutlineArtifact,
      continuityReview: fixture.continuityReviewArtifact,
      narrativeReview: fixture.narrativeReviewArtifact,
      themeReview: fixture.themeReviewArtifact,
    })).toEqual(fixture.outline);
  });

  it('rejects a human-edited review even when its content still says pass', () => {
    const fixture = createStoryArtifacts();
    expect(() => assertPromotionReady({
      outline: fixture.outline,
      snapshot: fixture.snapshot,
      outlineArtifact: fixture.finalOutlineArtifact,
      continuityReview: asHuman(fixture.continuityReviewArtifact),
      narrativeReview: fixture.narrativeReviewArtifact,
      themeReview: fixture.themeReviewArtifact,
    })).toThrow('Human-edited reviews cannot satisfy promotion gates.');
  });

  it('rejects a stale review hash and a blocker verdict', () => {
    const fixture = createStoryArtifacts();
    const staleNarrative = {
      ...fixture.narrativeReviewArtifact,
      content: { ...fixture.narrativeReviewArtifact.content, targetContentHash: artifactContentHash({ stale: true }) },
    };
    expect(() => assertPromotionReady({
      outline: fixture.outline,
      snapshot: fixture.snapshot,
      outlineArtifact: fixture.finalOutlineArtifact,
      continuityReview: fixture.continuityReviewArtifact,
      narrativeReview: staleNarrative,
      themeReview: fixture.themeReviewArtifact,
    })).toThrow('Review does not target the active final outline version.');

    const blockedTheme = {
      ...fixture.themeReviewArtifact,
      content: { ...fixture.themeReviewArtifact.content, verdict: 'block' as const },
    };
    expect(() => assertPromotionReady({
      outline: fixture.outline,
      snapshot: fixture.snapshot,
      outlineArtifact: fixture.finalOutlineArtifact,
      continuityReview: fixture.continuityReviewArtifact,
      narrativeReview: fixture.narrativeReviewArtifact,
      themeReview: blockedTheme,
    })).toThrow('All required reviews must pass before promotion.');
  });
});
