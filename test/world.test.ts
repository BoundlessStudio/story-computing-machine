import { describe, expect, it } from 'vitest';
import { offlineWorld } from '../agent/lib/deterministic.js';
import { assertCanon, validateCanon } from '../agent/lib/domain.js';

describe('deterministic world pipeline', () => {
  it('produces the same creative content for the same seed', () => {
    const a = offlineWorld('A city inside a sleeping sky-whale', 42);
    const b = offlineWorld('A city inside a sleeping sky-whale', 42);
    expect({ ...a, metadata: undefined }).toEqual({ ...b, metadata: undefined });
  });

  it('creates a schema-valid canon with resolved references', () => {
    const world = offlineWorld('A city inside a sleeping sky-whale', 7);
    expect(() => assertCanon(world)).not.toThrow();
    expect(validateCanon(world)).toEqual([]);
    expect(world.metadata).toMatchObject({ framework: 'eve', gateway: 'openrouter' });
  });

  it('detects dangling references deterministically', () => {
    const world = offlineWorld('A city inside a sleeping sky-whale', 7);
    world.relationships[0]!.to = 'missing-place';
    expect(validateCanon(world)).toContain('unknown relationship target: missing-place');
  });
});
