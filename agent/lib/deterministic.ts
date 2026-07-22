import type { World } from './domain.js';
import { assertCanon, slugify, WorldSchema } from './domain.js';

function rng(seed: number): () => number {
  let state = seed >>> 0;
  return () => ((state = (state * 1664525 + 1013904223) >>> 0) / 0x100000000);
}

function pick<T>(random: () => number, values: readonly T[]): T {
  return values[Math.floor(random() * values.length)]!;
}

export function offlineWorld(premise: string, seed: number, tone = 'wondrous, tense, humane'): World {
  const random = rng(seed);
  const title = pick(random, ['The Hollow Meridian', 'Atlas of the Sleeping Vast', 'The Lantern Dominion']);
  const names = ['Aster Reach', 'The Quiet Cartographers', 'Mara Venn', 'The Breathglass Key', 'Cloudkin'];
  const kinds = ['place', 'faction', 'character', 'artifact', 'species'] as const;
  const entities = names.map((name, index) => ({
    id: slugify(name),
    name,
    kind: kinds[index]!,
    summary: `${name} embodies a different consequence of the world's central premise.`,
    wants: pick(random, ['stability at any cost', 'the truth made public', 'freedom from an inherited duty', 'control of the next awakening']),
    tags: [kinds[index]!, index % 2 ? 'volatile' : 'ancient'],
  }));
  return assertCanon(WorldSchema.parse({
    title,
    premise,
    tone,
    laws: ['The sky-whale’s dreams alter gravity but cannot create matter.', 'Every use of breathglass wakes the host a little.', 'Maps become inaccurate after each communal lie.'],
    history: [
      { era: 'The Landing', event: 'Refugees mistook the sleeping creature for an island.', consequence: 'The first districts were anchored to living bone.' },
      { era: 'The Cartographic Schism', event: 'Rival maps described incompatible cities.', consequence: 'Truth became civic infrastructure.' },
      { era: 'The First Stirring', event: 'The host rolled in its sleep.', consequence: 'The lower wards became a vertical frontier.' },
    ],
    entities,
    relationships: [
      { from: entities[1]!.id, to: entities[0]!.id, type: 'protects', detail: 'They maintain the only maps that respond to truth.' },
      { from: entities[2]!.id, to: entities[3]!.id, type: 'needs', detail: 'The key may prove whether the awakening can be delayed.' },
      { from: entities[4]!.id, to: entities[0]!.id, type: 'inhabits', detail: 'They migrate through the city as gravity changes.' },
      { from: entities[1]!.id, to: entities[2]!.id, type: 'opposes', detail: 'Her investigation threatens their monopoly on stable maps.' },
    ],
    storyHooks: ['A district disappears from every honest map.', 'The sky-whale speaks through the city bells.', 'A child is born immune to dream-gravity.'],
    openQuestions: ['Is the host truly asleep, or pretending?'],
    metadata: {
      seed,
      generatedAt: new Date(0).toISOString(),
      mode: 'offline',
      framework: 'eve',
      gateway: 'openrouter',
    },
  }));
}
