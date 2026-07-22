import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { assertCanon, slugify, validateCanon, WorldDraftSchema, WorldSchema } from '../lib/domain.js';

const inputSchema = z.object({
  world: WorldDraftSchema,
  seed: z.number().int(),
  saveAs: z.string().regex(/^[a-zA-Z0-9][a-zA-Z0-9._-]*\.json$/).optional(),
});

const outputSchema = z.object({
  ok: z.literal(true),
  path: z.string(),
  world: WorldSchema,
});

export default defineTool({
  description: 'Deterministically validate canon references, stamp metadata, and save the final story world as JSON. Call only after advisory review.',
  inputSchema,
  outputSchema,
  async execute({ world: draft, seed, saveAs }) {
    const issues = validateCanon(draft);
    if (issues.length) throw new Error(`Canon validation failed:\n- ${issues.join('\n- ')}`);

    const world = assertCanon({
      ...draft,
      metadata: {
        seed,
        generatedAt: new Date().toISOString(),
        mode: 'online',
        framework: 'eve',
        gateway: 'openrouter',
      },
    });
    const outputDirectory = path.resolve('output');
    const filename = saveAs ?? `${slugify(world.title)}-${seed}.json`;
    const target = path.join(outputDirectory, filename);
    await mkdir(outputDirectory, { recursive: true });
    await writeFile(target, `${JSON.stringify(world, null, 2)}\n`, 'utf8');
    return { ok: true as const, path: target, world };
  },
});
