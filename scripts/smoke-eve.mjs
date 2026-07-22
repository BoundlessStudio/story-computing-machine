import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { Client } from 'eve/client';
import { WorldSchema } from '../agent/lib/domain.ts';

const port = Number(process.env.EVE_SMOKE_PORT ?? 2137);
const host = `http://127.0.0.1:${port}`;
const server = spawn(
  process.execPath,
  ['node_modules/eve/bin/eve.js', 'start', '--host', '127.0.0.1', '--port', String(port)],
  { cwd: process.cwd(), env: process.env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true },
);
let serverLog = '';
server.stdout.on('data', (chunk) => { serverLog += chunk; });
server.stderr.on('data', (chunk) => { serverLog += chunk; });

try {
  const client = new Client({ host });
  let ready = false;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`Eve exited before becoming ready.\n${serverLog}`);
    try {
      await client.health();
      ready = true;
      break;
    } catch {
      await delay(250);
    }
  }
  if (!ready) throw new Error(`Eve did not become ready at ${host}.\n${serverLog}`);
  process.stdout.write(`Eve ready at ${host}\n`);

  const session = client.session();
  const response = await session.send({
    message: 'Create a compact story world with seed 42 about a city built inside a sleeping sky-whale. Tone: wondrous, tense, humane. Follow the complete specialist and advisory workflow and persist the result.',
    outputSchema: WorldSchema,
  });
  const result = await response.result();
  if (result.status === 'failed') throw new Error(`Eve session failed: ${JSON.stringify(result.events.at(-1))}`);
  const world = WorldSchema.parse(result.data);
  const eventTypes = result.events.map((event) => event.type);
  const delegated = eventTypes.filter((type) => type === 'subagent.called').length;
  if (delegated < 3) throw new Error(`Expected at least three specialist calls, observed ${delegated}.`);
  if (!eventTypes.includes('action.result')) throw new Error('The finalization tool did not produce a result.');
  process.stdout.write(`${JSON.stringify({ status: result.status, title: world.title, delegated, framework: world.metadata.framework, gateway: world.metadata.gateway })}\n`);
} finally {
  if (server.exitCode === null) {
    server.kill('SIGTERM');
    await Promise.race([new Promise((resolve) => server.once('exit', resolve)), delay(5_000)]);
    if (server.exitCode === null) server.kill('SIGKILL');
  }
}
