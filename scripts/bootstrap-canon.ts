import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createInitialCanonSnapshot } from '../agent/lib/artifact-domain.js';
import { ArtifactStore } from '../agent/lib/sqlite-artifact-store.js';
import { WorldSchema } from '../agent/lib/domain.js';
import { migrateDatabase } from './migrate-database.js';

function inputPath(): string {
  const fileFlag = process.argv.indexOf('--file');
  const value = fileFlag >= 0 ? process.argv[fileFlag + 1] : process.argv[2];
  if (fileFlag >= 0 && !value) throw new Error('--file requires a path');
  return resolve(value ?? 'output/lumenwake-42.json');
}

const path = inputPath();
await migrateDatabase();
const world = WorldSchema.parse(JSON.parse(await readFile(path, 'utf8')));
const normalizedSnapshot = createInitialCanonSnapshot(world);
const store = new ArtifactStore();
const result = await store.bootstrapCanon({ world, normalizedSnapshot });
store.close();

console.log(JSON.stringify({
  worldId: 'shared-world',
  source: path,
  revision: result.revision,
  snapshotArtifactId: result.snapshotArtifactId,
  snapshotHash: result.canonHash,
  created: result.created,
}, null, 2));
