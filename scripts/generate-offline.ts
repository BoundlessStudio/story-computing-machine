import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { offlineWorld } from '../agent/lib/deterministic.js';

function option(name: string, fallback?: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

const premise = option('--premise');
if (!premise) throw new Error('Usage: npm run world:offline -- --premise <text> [--seed 42] [--tone <text>] [--output output/world.json]');
const seed = Number.parseInt(option('--seed', '42')!, 10);
if (!Number.isSafeInteger(seed)) throw new Error('--seed must be an integer');
const world = offlineWorld(premise, seed, option('--tone', 'wondrous, tense, humane'));
const json = `${JSON.stringify(world, null, 2)}\n`;
const output = option('--output');
if (output) {
  const target = path.resolve(output);
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, json, 'utf8');
  console.error(`Wrote ${target}`);
} else {
  process.stdout.write(json);
}
