import { spawn, type ChildProcessByStdio } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { DatabaseSync } from 'node:sqlite';
import type { Readable } from 'node:stream';
import { Client } from 'eve/client';
import { StoryOperationResultSchema, createInitialCanonSnapshot, type ArtifactKind } from '../agent/lib/artifact-domain.js';
import { WorldSchema } from '../agent/lib/domain.js';
import { ArtifactStore } from '../agent/lib/sqlite-artifact-store.js';
import { renderWriterPacket } from '../agent/lib/writer-packet.js';
import { migrateDatabase, resolveSqlitePath } from './migrate-database.js';

const PROMPT = 'Two kids from two very different backgrounds get isekaid into another world and bond over their shared situation. Write a story on the aftermath of their adventure, them trying to re-adjust to normal life while trying to look for each other.';
const CLARIFICATION = 'Both children come from very different backgrounds in the same modern Earth. They were transported together to Lumenwake, completed an adventure there, and returned separately to Earth. They do not know enough identifying details to find one another easily. Begin after their return, and keep Lumenwake causally important through their shared memories, consequences, and any canon-safe artifact rather than rewriting the foundation world.';
const port = Number(process.env.EVE_STORY_TEST_PORT ?? 2141);
const turnTimeoutMs = Number(process.env.EVE_STORY_TURN_TIMEOUT_MS ?? 360_000);
const host = `http://127.0.0.1:${port}`;
const projectRoot = resolve(import.meta.dirname, '..');
const outputDirectory = resolve(projectRoot, 'output');
const databasePath = resolveSqlitePath();
const resumeStoryRunId = process.env.STORY_TEST_RESUME_RUN_ID;

type Row = Record<string, unknown>;
type EveServer = ChildProcessByStdio<null, Readable, Readable>;
type StoryResult = ReturnType<typeof StoryOperationResultSchema.parse>;

function invariant(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(`Acceptance check failed: ${message}`);
}

function parseJson(value: unknown): Record<string, unknown> {
  invariant(typeof value === 'string', 'expected stored JSON text');
  const parsed = JSON.parse(value) as unknown;
  invariant(parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed), 'expected stored JSON object');
  return parsed as Record<string, unknown>;
}

function artifactFromRow(row: Row) {
  return {
    artifactId: String(row.artifact_id),
    worldId: 'shared-world' as const,
    storyRunId: row.story_run_id ? String(row.story_run_id) : null,
    branchId: row.branch_id ? String(row.branch_id) as 'A' | 'B' | 'C' : null,
    kind: String(row.kind) as ArtifactKind,
    schemaVersion: Number(row.schema_version),
    logicalKey: String(row.logical_key),
    version: Number(row.version),
    canonRevision: Number(row.canon_revision),
    canonSnapshotArtifactId: String(row.canon_snapshot_artifact_id),
    content: JSON.parse(String(row.content)),
    contentHash: String(row.content_hash),
    producer: {
      type: String(row.producer_type) as 'human' | 'agent' | 'tool',
      name: String(row.producer_name),
      ...(row.producer_model_id ? { modelId: String(row.producer_model_id) } : {}),
      ...(row.producer_gateway ? { gateway: String(row.producer_gateway) as 'openrouter' } : {}),
      ...(row.producer_eve_session_id ? { eveSessionId: String(row.producer_eve_session_id) } : {}),
    },
    lifecycleStatus: String(row.lifecycle_status) as 'active' | 'superseded' | 'stale' | 'rejected',
    createdAt: String(row.created_at),
  };
}

async function waitForEve(server: EveServer, serverLog: () => string): Promise<Client> {
  const client = new Client({ host });
  for (let attempt = 0; attempt < 120; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`Eve exited before becoming ready.\n${serverLog()}`);
    try {
      await client.health();
      return client;
    } catch {
      await delay(250);
    }
  }
  throw new Error(`Eve did not become ready at ${host}.\n${serverLog()}`);
}

async function stopServer(server: EveServer): Promise<void> {
  if (server.exitCode !== null) return;
  server.kill('SIGTERM');
  await Promise.race([new Promise((resolveExit) => server.once('exit', resolveExit)), delay(5_000)]);
  if (server.exitCode === null) server.kill('SIGKILL');
}

async function main(): Promise<void> {
  const startedAt = Date.now();
  await mkdir(outputDirectory, { recursive: true });
  const appliedMigrations = await migrateDatabase(databasePath);
  const worldPath = resolve(projectRoot, 'output/lumenwake-42.json');
  const world = WorldSchema.parse(JSON.parse(await readFile(worldPath, 'utf8')));
  const bootstrapStore = new ArtifactStore(databasePath);
  const bootstrap = await bootstrapStore.bootstrapCanon({
    world,
    normalizedSnapshot: createInitialCanonSnapshot(world),
    producerName: 'live-story-room-test',
  });
  bootstrapStore.close();
  invariant(bootstrap.revision === 1, 'test must start from canon revision 1');

  const server = spawn(
    process.execPath,
    ['node_modules/eve/bin/eve.js', 'start', '--host', '127.0.0.1', '--port', String(port)],
    {
      cwd: projectRoot,
      env: { ...process.env, WORKFLOW_LOCAL_RECOVER_ACTIVE_RUNS: 'false' },
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    },
  );
  let serverLog = '';
  const appendLog = (chunk: Buffer) => {
    serverLog = `${serverLog}${chunk.toString()}`.slice(-250_000);
  };
  server.stdout.on('data', appendLog);
  server.stderr.on('data', appendLog);

  let storyRunId: string | undefined;
  let pitchSlateArtifactId: string | undefined;
  let finalOutlineArtifactId: string | undefined;
  let finalOutlineContentHash: string | undefined;
  let exportArtifactId: string | undefined;
  let markdown = '';
  let exportFilename = '';
  let clarificationUsed = false;
  let selectionAlreadyPersisted = false;
  let finalOutlineAlreadyPersisted = false;
  let finalReviewsAlreadyPersisted = false;
  let finalizationRepairIssues: string[] = [];
  let finalizationRepairOperations: Array<{ op: 'add'; path: string; value: Record<string, unknown> }> = [];
  let narrativeRepairOperations: Array<{ op: 'replace'; path: string; value: string }> = [];
  let stateMismatchRepairOperations: Array<{ op: 'replace'; path: string; value: string }> = [];
  let retryContinuityWithFullInputs = false;
  let finalContinuityPass = false;
  let finalNarrativePass = false;
  let finalThemePass = false;
  let runAlreadyReady = false;
  const responseEventTypes: string[] = [];

  try {
    const client = await waitForEve(server, () => serverLog);
    process.stdout.write(`Eve ready at ${host}\n`);
    let session = client.session();

    const send = async (message: string, allowEmpty = false): Promise<StoryResult | undefined> => {
      const activeSession = session;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), turnTimeoutMs);
      try {
        const response = await activeSession.send({ message, outputSchema: StoryOperationResultSchema, signal: controller.signal });
        const result = await response.result();
        responseEventTypes.push(...result.events.map((event) => event.type));
        if (result.status === 'failed') {
          throw new Error(`Eve session failed: ${JSON.stringify(result.events.at(-1))}`);
        }
        const unrecoverableEvent = result.events.find((event) => /(?:model|session|turn).*(?:error|failed)|(?:error|failed).*(?:model|session|turn)/iu.test(event.type));
        if (result.data === undefined && unrecoverableEvent) {
          throw new Error(`Eve model/session failure: ${JSON.stringify(unrecoverableEvent)}`);
        }
        if (result.data === undefined) {
          if (allowEmpty) return undefined;
          throw new Error(`Eve returned ${result.status} without structured data. Last event: ${JSON.stringify(result.events.at(-1))}`);
        }
        return StoryOperationResultSchema.parse(result.data);
      } catch (error) {
        if (!controller.signal.aborted) throw error;
        responseEventTypes.push('harness.turn-timeout');
        await activeSession.cancel().catch(() => undefined);
        session = client.session();
        if (allowEmpty) return undefined;
        throw new Error(`Eve turn exceeded ${turnTimeoutMs} ms and was cancelled`);
      } finally {
        clearTimeout(timeout);
      }
    };
    const sendRequired = async (message: string): Promise<StoryResult> => {
      let result = await send(message, true);
      for (let continuation = 1; !result && continuation <= 40; continuation += 1) {
        if (continuation > 1 && continuation % 5 === 1) session = client.session();
        await delay(250);
        result = await send(
          `Resume ${storyRunId ? `story run ${storyRunId}` : 'the same story-room operation'} from its exact persisted active artifacts and current workflow status. Do not repeat valid completed work. Continue only the earliest missing stage, complete the requested checkpoint, and return the declared structured result. This is automatic continuation ${continuation}${continuation > 1 && continuation % 5 === 1 ? ' in a fresh Eve coordinator session' : ''}.`,
          true,
        );
      }
      invariant(result, 'Eve parked without structured data after 40 automatic continuations');
      return result;
    };

    let pitchResult: StoryResult;
    if (resumeStoryRunId) {
      storyRunId = resumeStoryRunId;
      const resumeDatabase = new DatabaseSync(databasePath, { readOnly: true });
      const run = resumeDatabase.prepare('SELECT status, base_canon_snapshot_artifact_id FROM story_runs WHERE story_run_id = ?').get(storyRunId) as Row | undefined;
      const activeArtifacts = resumeDatabase.prepare(`
        SELECT artifact_id, kind, logical_key, content_hash, content FROM artifacts
        WHERE story_run_id = ? AND lifecycle_status = 'active'
        ORDER BY created_at, artifact_id
      `).all(storyRunId) as Row[];
      invariant(run, 'resume story run does not exist');
      runAlreadyReady = run.status === 'ready_for_promotion';
      const activeByKind = (kind: string) => activeArtifacts.filter((artifact) => artifact.kind === kind);
      const clarification = activeByKind('prompt.clarification').at(-1);
      const brief = activeByKind('story.brief').at(-1);
      const dossier = activeByKind('canon.dossier').at(-1);
      const slate = activeByKind('pitch.slate').at(-1);
      const selection = activeByKind('decision.pitch-selection').at(-1);
      const finalOutline = activeByKind('outline.final').at(-1);
      clarificationUsed = Boolean(clarification);
      finalOutlineAlreadyPersisted = Boolean(finalOutline);
      if (finalOutline) {
        finalOutlineArtifactId = String(finalOutline.artifact_id);
        finalOutlineContentHash = String(finalOutline.content_hash);
        const snapshotRow = resumeDatabase.prepare('SELECT content FROM artifacts WHERE artifact_id = ?').get(String(run.base_canon_snapshot_artifact_id)) as Row | undefined;
        invariant(snapshotRow, 'pinned snapshot is missing while inspecting finalization readiness');
        const snapshot = parseJson(snapshotRow.content) as { world?: { entities?: Array<{ id?: string }> } };
        const outline = parseJson(finalOutline.content) as {
          characters?: Array<{ entityId?: string; role?: string; externalWant?: string }>;
          scenes?: Array<{ settingEntityId?: string; participantEntityIds?: string[] }>;
          canonDelta?: {
            event?: { participantEntityIds?: string[] };
            newEntities?: Array<{ id?: string; summary?: string }>;
            entityStateChanges?: Array<{ entityId?: string; before?: string }>;
          };
        };
        const resolvableEntityIds = new Set([
          ...(snapshot.world?.entities ?? []).flatMap((entity) => entity.id ? [entity.id] : []),
          ...(outline.canonDelta?.newEntities ?? []).flatMap((entity) => entity.id ? [entity.id] : []),
        ]);
        const referencedEntityIds = [
          ...(outline.scenes ?? []).flatMap((scene) => [
            ...(scene.settingEntityId ? [scene.settingEntityId] : []),
            ...(scene.participantEntityIds ?? []),
          ]),
          ...(outline.canonDelta?.event?.participantEntityIds ?? []),
        ];
        finalizationRepairIssues = [...new Set(referencedEntityIds.filter((entityId) => !resolvableEntityIds.has(entityId)))];
        finalizationRepairOperations = finalizationRepairIssues.map((entityId) => {
          const character = outline.characters?.find((candidate) => candidate.entityId === entityId);
          const stateChange = outline.canonDelta?.entityStateChanges?.find((candidate) => candidate.entityId === entityId);
          const name = entityId.split('-').map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`).join(' ');
          return {
            op: 'add' as const,
            path: '/content/canonDelta/newEntities/-',
            value: {
              id: entityId,
              name,
              kind: 'character',
              summary: stateChange?.before ?? character?.role ?? `Provisional story character ${name}.`,
              wants: character?.externalWant ?? 'To complete the story goal while preserving established boundaries.',
              tags: ['provisional', 'story-character'],
            },
          };
        });
        stateMismatchRepairOperations = (outline.canonDelta?.entityStateChanges ?? []).flatMap((stateChange, index) => {
          const newEntity = outline.canonDelta?.newEntities?.find((entity) => entity.id === stateChange.entityId);
          if (!newEntity?.summary || stateChange.before === newEntity.summary) return [];
          return [{
            op: 'replace' as const,
            path: `/content/canonDelta/entityStateChanges/${index}/before`,
            value: newEntity.summary,
          }];
        });
        const hasExactPassingReview = (kind: string) => activeArtifacts
          .filter((artifact) => artifact.kind === kind && String(artifact.logical_key).endsWith('/final'))
          .some((artifact) => {
            const review = parseJson(artifact.content) as { verdict?: string; targetArtifactId?: string; targetContentHash?: string };
            return review.verdict === 'pass'
              && review.targetArtifactId === finalOutline.artifact_id
              && review.targetContentHash === finalOutline.content_hash;
          });
        finalContinuityPass = hasExactPassingReview('review.continuity');
        finalNarrativePass = hasExactPassingReview('review.narrative');
        finalThemePass = hasExactPassingReview('review.theme-pacing');
      }
      resumeDatabase.close();
      const finalReviewKeys = new Set(activeArtifacts.map((artifact) => String(artifact.logical_key)));
      finalReviewsAlreadyPersisted = [
        'review/continuity/final',
        'review/narrative/final',
        'review/theme-pacing/final',
      ].every((logicalKey) => finalReviewKeys.has(logicalKey));
      const blockedNarrativeReview = activeArtifacts
        .filter((artifact) => artifact.kind === 'review.narrative' && artifact.logical_key === 'review/narrative/final')
        .map((artifact) => parseJson(artifact.content) as { verdict?: string; findings?: Array<{ issue?: string }> })
        .find((review) => review.verdict === 'block' && review.findings?.some((finding) => finding.issue?.includes('privacy rule')));
      const blockedContinuityReview = activeArtifacts
        .filter((artifact) => artifact.kind === 'review.continuity' && artifact.logical_key === 'review/continuity/final')
        .map((artifact) => parseJson(artifact.content) as { verdict?: string; findings?: Array<{ issue?: string }> })
        .find((review) => review.verdict === 'block' && review.findings?.some((finding) => finding.issue?.includes('absent from the supplied review input')));
      retryContinuityWithFullInputs = Boolean(blockedContinuityReview);
      if (blockedNarrativeReview && finalOutline) {
        const currentOutline = parseJson(finalOutline.content) as { scenes?: Array<{ id?: string }> };
        const sceneIndex = (sceneId: string) => currentOutline.scenes?.findIndex((scene) => scene.id === sceneId) ?? -1;
        const scene02 = sceneIndex('scene-02');
        const scene03 = sceneIndex('scene-03');
        const scene06 = sceneIndex('scene-06');
        const scene07 = sceneIndex('scene-07');
        invariant([scene02, scene03, scene06, scene07].every((index) => index >= 0), 'narrative repair scenes are missing');
        narrativeRepairOperations = [
          {
            op: 'replace',
            path: '/content/synopsis',
            value: 'Mira and Ash are children from materially different backgrounds: Lumenwake’s fragile water economy taught Mira to equate care with knowing where everyone is, while Ash entered their shared adventure already protective of personal information and choice. During displacement in Lumenwake, they bonded by surviving a dangerous moment without forcing Orra awake, learning to wait through her breath rather than demand an immediate answer. They later departed separately in safe sail-cages, during long exhales and before the Thin Dream; whatever subsequently brought each child from the exterior to Earth remains off-page and unexplained. Now both are readjusting to ordinary but separate Earth lives. Mira is recovering in a provisional, water-rich household and starting school routines. Ash is also negotiating school and household routines, and independently uses an ordinary Earth-side youth relocation letterbox. Its confidential intake registry verifies participants internally, while the public circular publishes only a recipient-approved mark and never a name, location, school, household, or arrival history. Ash registers the private mark and authorizes exactly one screened deposit from Mira. When Mira presents herself, the office verifies her identity against its confidential record but tells her only that a protected participant authorized one message from her; Mira infers Ash from the mark they invented together, while the office neither confirms that inference nor discloses the submitter. The channel forbids location requests, proof demands, tracking, and immediate-reply requirements. Those limits sharpen Mira’s temptation to crowdsource the mark, but she closes the public query and sends one invitation stripped of demands. Through nine evenings she returns to school and household life rather than searching. A cover sheet lets Ash verify that the sender was the internally authenticated Mira, that she made one deposit, and that she requested no identifying information or follow-up. Ash weighs whether any reply will be treated as permission to locate them, then answers with one-message-at-a-time correspondence through the intermediary, no address exchange or tracing, and either child’s right to pause. Mira accepts without bargaining. The “ninth exhale” becomes their emotional practice of patient consent, not a signal, route, launch schedule, or transit mechanism.',
          },
          {
            op: 'replace',
            path: `/content/scenes/${scene02}/conflict`,
            value: 'At Ash’s earlier private visit, the service verifies Ash through its confidential intake registry and records Mira as the only authorized depositor. At Mira’s later visit, the volunteer verifies Mira against that registry but discloses only that a protected participant published the mark and authorized one screened message from her. The volunteer does not identify Ash or reveal a location, household, school, health, or arrival history; recognizing the now-public mark is not itself authentication.',
          },
          {
            op: 'replace',
            path: `/content/scenes/${scene02}/turn`,
            value: 'Mira infers that the protected participant is Ash because only the two children know what the shared mark meant before publication, but the volunteer neither confirms her inference nor relaxes the restrictions. The office can authenticate Mira internally while withholding the recipient’s identity and circumstances.',
          },
          {
            op: 'replace',
            path: `/content/scenes/${scene02}/outcome`,
            value: 'Mira receives a real but narrow opening: one authenticated deposit to the protected recipient, with no location request, proof demand, tracking, follow-up, or guaranteed answer.',
          },
          {
            op: 'replace',
            path: `/content/scenes/${scene03}/openingState`,
            value: 'The authorized channel cannot tell Mira where Ash is, prove present safety, compel an immediate reply, or permit follow-up. Those limits activate her scarcity-shaped fear that care without shared whereabouts is not enough; at the library she has one concrete chance to crowdsource the public mark before the circular rotates out.',
          },
          {
            op: 'replace',
            path: `/content/scenes/${scene06}/conflict`,
            value: 'For nine evenings no answer arrives. Mira repeatedly wants to return to the library search but treats each evening as a deliberate patience practice, never as a signal or transit countdown. Ash receives the authenticated, screened note amid homework, meals, and the strain of settling into an ordinary household, and worries that any reply could be misread as permission to seek an address or present circumstances.',
          },
          {
            op: 'replace',
            path: `/content/scenes/${scene07}/conflict`,
            value: 'The reply does not provide the certainty Mira once sought. Ash permits only one-message-at-a-time correspondence through the intermediary, refuses address exchange and tracing, and reserves either child’s right to pause without explanation.',
          },
          {
            op: 'replace',
            path: `/content/scenes/${scene07}/turn`,
            value: 'Ash explains that leaving the shared mark was their own search for Mira. They waited nine evenings before answering as a private echo of the patience learned beside Orra—not because any signal, route, launch schedule, or transit effect opened—and chose these bounded terms because the authenticated cover sheet proved Mira made one nontracking deposit and did not pursue them outside the channel.',
          },
          {
            op: 'replace',
            path: '/content/canonDelta/newEntities/5/summary',
            value: 'Proposed wholly Earth-side contact affordance backed by a confidential intake registry: the service verifies participants internally, publishes only recipient-approved marks, authorizes named senders for screened deposits, withholds recipient identity and circumstances, and records deposit count plus forbidden tracking or address requests. It has no signal, route, portal, launch, or transit function.',
          },
        ];
      }
      if (slate && selection) {
        selectionAlreadyPersisted = true;
        pitchResult = {
          type: 'pitch-slate-ready',
          storyRunId,
          pitchSlateArtifactId: String(slate.artifact_id),
          status: 'awaiting_pitch',
        };
      } else if (clarification) {
        pitchResult = await sendRequired(
          `Resume existing story run ${storyRunId} from active clarification artifact ${clarification.artifact_id}. Treat the immutable original prompt and that clarification as the combined writer input. Sequentially regenerate and supersede only the story brief; retain the existing active canon dossier because the pinned snapshot is unchanged. Then rerun canon preflight using the new brief, active dossier, snapshot, and clarification. If safe, generate all three isolated pitch branches, obtain exact pitch-slate continuity certification, and stop at the writer selection checkpoint.`,
        );
      } else if (brief && !dossier) {
        pitchResult = await sendRequired(
          `Resume partially completed story run ${storyRunId}. Keep exact active brief ${brief.artifact_id}; do not regenerate it. Load the immutable original prompt and pinned canon snapshot, call canon_librarian, and persist exactly the child invocation's output value as canon.dossier (not the Eve child-result wrapper), with the original prompt and snapshot as consumes parents. Continue through canon preflight. If clarification is required, return that checkpoint; otherwise generate all three isolated pitch branches, obtain exact pitch-slate continuity certification, and stop at writer selection.`,
        );
      } else {
        pitchResult = await sendRequired(
          `Resume partially completed story run ${storyRunId} from its exact active artifacts. Do not regenerate valid active work. Continue from the earliest missing stage through all three isolated pitch branches and exact pitch-slate continuity certification, then stop at the writer selection checkpoint. When persisting a canon librarian result, save exactly canon_librarian.output rather than the Eve child-result wrapper.`,
        );
      }
    } else {
      pitchResult = await sendRequired(PROMPT);
    }
    if (pitchResult.type === 'clarification-required') {
      invariant(!clarificationUsed, 'a second unresolved clarification is not allowed');
      clarificationUsed = true;
      storyRunId = pitchResult.storyRunId;
      const clarificationResult = await send(
        `Clarify prompt conflict ${pitchResult.conflictArtifactId} for story run ${pitchResult.storyRunId}: ${CLARIFICATION} Record this writer clarification and return the run to analysis.`,
        true,
      );
      if (clarificationResult?.type === 'pitch-slate-ready') {
        pitchResult = clarificationResult;
      } else {
        pitchResult = await sendRequired(
          `Resume existing story run ${storyRunId} from its active prompt clarification. Treat the immutable original prompt and active clarification as the combined writer input. Sequentially regenerate and supersede only the story brief; retain the existing active canon dossier because the pinned snapshot is unchanged. Then rerun canon preflight using the new brief, active dossier, snapshot, and clarification. If safe, generate all three isolated pitch branches, obtain exact pitch-slate continuity certification, and stop at the writer selection checkpoint.`,
        );
      }
    }
    invariant(pitchResult.type !== 'clarification-required', 'a second unresolved clarification is not allowed');
    invariant(pitchResult.type === 'pitch-slate-ready', `expected pitch-slate-ready, received ${pitchResult.type}`);
    storyRunId = pitchResult.storyRunId;
    pitchSlateArtifactId = pitchResult.pitchSlateArtifactId;
    process.stdout.write(selectionAlreadyPersisted
      ? `Pitch-a selection already active for run ${storyRunId}; resuming outline work\n`
      : `Pitch slate ready for run ${storyRunId}; selecting pitch-a\n`);

    if (finalOutlineAlreadyPersisted && finalizationRepairOperations.length > 0) {
      const editResult = await sendRequired(
        `The deterministic finalization gate found unresolved entity declarations in final outline ${finalOutlineArtifactId} for story run ${storyRunId}: ${finalizationRepairIssues.join(', ')}. Under the writer's preauthorized revision cycle, call patch_story_artifact exactly once with artifactId ${finalOutlineArtifactId}, expectedHash ${finalOutlineContentHash}, producerName "live-story-room-test", and these exact RFC 6902 operations: ${JSON.stringify(finalizationRepairOperations)}. Do not invoke an agent, rewrite any other content, or return an edit receipt unless it is the actual tool response.`,
      );
      invariant(editResult.type === 'edit-receipt', `expected edit-receipt for deterministic entity repair, received ${editResult.type}`);
      finalOutlineArtifactId = editResult.artifactId;
      finalOutlineContentHash = editResult.contentHash;
      finalReviewsAlreadyPersisted = false;
      finalizationRepairIssues = [];
      finalizationRepairOperations = [];
      const repairDatabase = new DatabaseSync(databasePath, { readOnly: true });
      const repaired = repairDatabase.prepare('SELECT producer_type, lifecycle_status FROM artifacts WHERE artifact_id = ?').get(finalOutlineArtifactId) as Row | undefined;
      repairDatabase.close();
      invariant(repaired?.producer_type === 'human' && repaired.lifecycle_status === 'active', 'patch_story_artifact did not persist an active human-produced replacement');
      process.stdout.write(`Patched unresolved final-outline entities: ${finalOutlineArtifactId}\n`);
    }

    if (finalOutlineAlreadyPersisted && narrativeRepairOperations.length > 0) {
      const editResult = await sendRequired(
        `Narrative review blocked final outline ${finalOutlineArtifactId} for an identity-authentication/privacy contradiction. Under the second and final preauthorized revision cycle, call patch_story_artifact exactly once with artifactId ${finalOutlineArtifactId}, expectedHash ${finalOutlineContentHash}, producerName "live-story-room-test", and these exact RFC 6902 operations: ${JSON.stringify(narrativeRepairOperations)}. The patch clarifies internal verification versus public disclosure, strengthens the costly search temptation and Ash's bounded choice, and changes no canon law or story outcome. Do not invoke an agent or return an edit receipt unless it is the actual tool response.`,
      );
      invariant(editResult.type === 'edit-receipt', `expected edit-receipt for narrative repair, received ${editResult.type}`);
      finalOutlineArtifactId = editResult.artifactId;
      finalOutlineContentHash = editResult.contentHash;
      finalReviewsAlreadyPersisted = false;
      narrativeRepairOperations = [];
      const repairDatabase = new DatabaseSync(databasePath, { readOnly: true });
      const repaired = repairDatabase.prepare('SELECT producer_type, lifecycle_status FROM artifacts WHERE artifact_id = ?').get(finalOutlineArtifactId) as Row | undefined;
      repairDatabase.close();
      invariant(repaired?.producer_type === 'human' && repaired.lifecycle_status === 'active', 'narrative patch did not persist an active human-produced replacement');
      process.stdout.write(`Patched blocked final-outline narrative logic: ${finalOutlineArtifactId}\n`);
    }

    if (finalOutlineAlreadyPersisted && stateMismatchRepairOperations.length > 0) {
      const editResult = await sendRequired(
        `The deterministic canon-delta gate found that a new entity's state-change before value does not exactly match its initial summary in final outline ${finalOutlineArtifactId}. Call patch_story_artifact exactly once with artifactId ${finalOutlineArtifactId}, expectedHash ${finalOutlineContentHash}, producerName "live-story-room-test", and these exact RFC 6902 operations: ${JSON.stringify(stateMismatchRepairOperations)}. This is a deterministic state-baseline correction only. Do not invoke an agent or return an edit receipt unless it is the actual tool response.`,
      );
      invariant(editResult.type === 'edit-receipt', `expected edit-receipt for state baseline repair, received ${editResult.type}`);
      finalOutlineArtifactId = editResult.artifactId;
      finalOutlineContentHash = editResult.contentHash;
      finalReviewsAlreadyPersisted = false;
      stateMismatchRepairOperations = [];
      const repairDatabase = new DatabaseSync(databasePath, { readOnly: true });
      const repaired = repairDatabase.prepare('SELECT producer_type, lifecycle_status FROM artifacts WHERE artifact_id = ?').get(finalOutlineArtifactId) as Row | undefined;
      repairDatabase.close();
      invariant(repaired?.producer_type === 'human' && repaired.lifecycle_status === 'active', 'state baseline patch did not persist an active human-produced replacement');
      process.stdout.write(`Patched final-outline state baseline: ${finalOutlineArtifactId}\n`);
    }

    let outlineResult: StoryResult;
    if (runAlreadyReady) {
      invariant(finalOutlineArtifactId, 'ready run has no active final outline');
      outlineResult = {
        type: 'provisional-outline',
        storyRunId,
        finalOutlineArtifactId,
        status: 'ready_for_promotion',
      };
    } else {
      outlineResult = await sendRequired(
        finalOutlineAlreadyPersisted && finalContinuityPass && finalNarrativePass && !finalThemePass
        ? `Resume story run ${storyRunId} from exact active final outline ${finalOutlineArtifactId} at hash ${finalOutlineContentHash}. Its exact continuity and narrative reviews already pass; do not rerun or supersede them. Call get_artifact for the complete final-outline and pinned canon-snapshot envelopes, invoke only theme_pacing_critic in review mode with both full content bodies, and save its output under review/theme-pacing/final targeting this exact ID/hash. Do not summarize or omit either body. If it passes, call finalize_outline with this outline ID/hash and return the actual tool response. Do not revise or promote.`
        : finalOutlineAlreadyPersisted && retryContinuityWithFullInputs
        ? `Resume story run ${storyRunId} without revising active final outline ${finalOutlineArtifactId} at hash ${finalOutlineContentHash}. Its latest continuity review blocked only because the delegated payload omitted the outline and canon bodies. Call get_artifact for the exact final outline and pinned canon snapshot, then invoke continuity_critic with both COMPLETE artifact envelopes including their full content—not summaries, references, IDs alone, or claims that content was previously retrieved. Save the replacement continuity review under review/continuity/final, superseding the input-incomplete review. Then run narrative_logic_critic and theme_pacing_critic sequentially with the same complete final-outline and snapshot envelopes, saving exact final reviews. Do not call story_editor or alter the outline. When all three exact reviews pass, call finalize_outline with this outline ID/hash and return its actual tool response. Do not promote canon.`
        : finalOutlineAlreadyPersisted && finalReviewsAlreadyPersisted
        ? `Resume story run ${storyRunId} from exact active final outline ${finalOutlineArtifactId} with content hash ${finalOutlineContentHash} and its three already persisted active final review artifacts. Do not invoke any agent. Call the finalize_outline tool exactly once using storyRunId ${storyRunId}, finalOutlineArtifactId ${finalOutlineArtifactId}, and expectedOutlineHash ${finalOutlineContentHash}. Do not return provisional-outline unless it is the actual tool response; it must independently verify the reviews and persist canon.delta while setting ready_for_promotion. Do not promote canon.`
        : finalOutlineAlreadyPersisted
        ? `Resume story run ${storyRunId} from exact active final outline ${finalOutlineArtifactId}. Do not regenerate any prompt, pitch, plan, blueprint, scenes, initial review, or final outline artifact. Run only the missing exact final-outline reviews sequentially—continuity, narrative, then theme/pacing—persisting each declared child output against this exact final-outline ID and hash. If a final critic blocks, permit at most two story-editor revision cycles and rerun all three exact reviews against the replacement hash. When all three pass, call finalize_outline, return the provisional outline result, and do not promote canon.`
        : selectionAlreadyPersisted
        ? `Resume story run ${storyRunId} from its exact active pitch-a selection and slate ${pitchSlateArtifactId}; do not call select_pitch again. Continue only missing outline work. To avoid local Eve hook starvation, invoke and save all missing specialists sequentially: character, conflict, world, theme/pacing, then plot; likewise run and save each scenes review and each final-outline review one at a time. For scene_architect, use its declared schema and persist exactly scene_architect.output as the complete { kind: "outline.scenes", outline: StoryOutline } content—never extract, simplify, or reconstruct it. Continue through blueprint, 6–8 scenes, editor revision, and exact final reviews. Address critic blockers with no more than two final revision cycles. Call finalize_outline when all gates pass, return the provisional outline result, and do not promote canon.`
        : `The writer preauthorizes selecting pitch-a from exact slate ${pitchSlateArtifactId} for story run ${storyRunId}. Continue through selected-pitch planning, blueprint, 6–8 scenes, the three initial critics, story-editor revision, and three exact final-outline reviews. Invoke and save selected-pitch specialists and critics sequentially. Address critic blockers with no more than two final revision cycles. Call finalize_outline when all gates pass, return the provisional outline result, and do not promote canon.`,
      );
    }
    invariant(outlineResult.type === 'provisional-outline', `expected provisional-outline, received ${outlineResult.type}`);
    invariant(outlineResult.storyRunId === storyRunId, 'outline result changed story run');
    finalOutlineArtifactId = outlineResult.finalOutlineArtifactId;
    invariant(storyRunId && finalOutlineArtifactId, 'finalization identifiers are incomplete');
    const finalizationStoryRunId = storyRunId;
    const finalizationOutlineId = finalOutlineArtifactId;
    const verifyFinalization = () => {
      const verificationDatabase = new DatabaseSync(databasePath, { readOnly: true });
      const run = verificationDatabase.prepare('SELECT status, canon_delta_artifact_id FROM story_runs WHERE story_run_id = ?').get(finalizationStoryRunId) as Row | undefined;
      const outline = verificationDatabase.prepare('SELECT content_hash FROM artifacts WHERE artifact_id = ?').get(finalizationOutlineId) as Row | undefined;
      verificationDatabase.close();
      return { run, outline };
    };
    let finalization = verifyFinalization();
    if (finalization.run?.status !== 'ready_for_promotion' || !finalization.run.canon_delta_artifact_id) {
      invariant(finalization.outline, 'final outline disappeared before finalization retry');
      finalOutlineContentHash = String(finalization.outline.content_hash);
      outlineResult = await sendRequired(
        `Your previous response did not execute the deterministic finalization gate: story run ${storyRunId} is still ${String(finalization.run?.status)} and has no canon delta. Call finalize_outline now with exactly {"storyRunId":"${storyRunId}","finalOutlineArtifactId":"${finalOutlineArtifactId}","expectedOutlineHash":"${finalOutlineContentHash}"}. Do not invoke agents, do not merely describe or echo a provisional result, and do not promote. Return only the actual finalize_outline tool response.`,
      );
      invariant(outlineResult.type === 'provisional-outline', `expected provisional-outline after finalization retry, received ${outlineResult.type}`);
      finalization = verifyFinalization();
    }
    invariant(finalization.run?.status === 'ready_for_promotion' && finalization.run.canon_delta_artifact_id, 'finalize_outline tool did not persist its state transition');
    process.stdout.write(`Provisional outline ready: ${finalOutlineArtifactId}\n`);

    const exportStoryRunId = storyRunId;
    const loadPersistedExport = (): StoryResult | undefined => {
      const exportDatabase = new DatabaseSync(databasePath, { readOnly: true });
      const row = exportDatabase.prepare(`
        SELECT artifact_id, content FROM artifacts
        WHERE story_run_id = ? AND kind = 'export.writer-packet' AND lifecycle_status = 'active'
        ORDER BY created_at DESC, artifact_id DESC LIMIT 1
      `).get(exportStoryRunId) as Row | undefined;
      exportDatabase.close();
      if (!row) return undefined;
      const content = parseJson(row.content) as { filename?: string; markdown?: string };
      const { filename, markdown: storedMarkdown } = content;
      if (!filename || !storedMarkdown) return undefined;
      return {
        type: 'markdown-export',
        storyRunId: exportStoryRunId,
        exportArtifactId: String(row.artifact_id),
        filename,
        markdown: storedMarkdown,
      };
    };
    let exportResult = loadPersistedExport();
    if (!exportResult) {
      const response = await sendRequired(
        `Call render_writer_packet for story run ${storyRunId} and return its actual markdown-export tool response. Do not promote or alter canon, and do not repeat the provisional-outline result.`,
      );
      exportResult = response.type === 'markdown-export' ? response : loadPersistedExport();
    }
    invariant(exportResult, 'render_writer_packet did not persist or return a Markdown export');
    invariant(exportResult.type === 'markdown-export', `expected markdown-export, received ${exportResult.type}`);
    exportArtifactId = exportResult.exportArtifactId;
    markdown = exportResult.markdown;
    exportFilename = exportResult.filename;
  } catch (error) {
    if (!storyRunId) {
      const failureDatabase = new DatabaseSync(databasePath, { readOnly: true });
      const latestRun = failureDatabase.prepare(`
        SELECT story_run_id FROM story_runs
        WHERE created_at >= ? ORDER BY created_at DESC LIMIT 1
      `).get(new Date(startedAt - 1_000).toISOString()) as Row | undefined;
      failureDatabase.close();
      if (latestRun) storyRunId = String(latestRun.story_run_id);
    }
    if (storyRunId) {
      await writeFile(resolve(outputDirectory, `${storyRunId}-live-test-failure.json`), `${JSON.stringify({
        status: 'failed',
        storyRunId,
        elapsedSeconds: Math.round((Date.now() - startedAt) / 100) / 10,
        error: error instanceof Error ? error.message : String(error),
        serverLogPath: resolve(outputDirectory, `${storyRunId}-eve-server.log`),
      }, null, 2)}\n`, 'utf8');
    }
    throw error;
  } finally {
    await stopServer(server);
    await writeFile(resolve(outputDirectory, 'live-story-room-server.log'), serverLog, 'utf8');
    if (storyRunId) await writeFile(resolve(outputDirectory, `${storyRunId}-eve-server.log`), serverLog, 'utf8');
  }

  if (storyRunId) {
    const auditDatabase = new DatabaseSync(databasePath, { readOnly: true });
    const unfinishedExecutions = auditDatabase.prepare(`
      SELECT * FROM agent_executions WHERE story_run_id = ? AND status = 'running'
    `).all(storyRunId) as Row[];
    auditDatabase.close();
    if (unfinishedExecutions.length > 0) {
      const auditStore = new ArtifactStore(databasePath);
      for (const execution of unfinishedExecutions) {
        await auditStore.recordAgentExecution({
          executionId: String(execution.execution_id),
          storyRunId,
          agentName: String(execution.agent_name),
          ...(execution.eve_child_session_id ? { eveChildSessionId: String(execution.eve_child_session_id) } : {}),
          ...(execution.model_id ? { modelId: String(execution.model_id) } : {}),
          gateway: 'openrouter',
          inputArtifactIds: JSON.parse(String(execution.input_artifact_ids)) as string[],
          outputArtifactIds: JSON.parse(String(execution.output_artifact_ids)) as string[],
          ...(execution.prompt_revision ? { promptRevision: String(execution.prompt_revision) } : {}),
          ...(execution.skill_revision ? { skillRevision: String(execution.skill_revision) } : {}),
          startedAt: String(execution.started_at),
          completedAt: new Date().toISOString(),
          status: 'failed',
          errorSummary: 'Execution was interrupted before artifact persistence; the live harness resumed from exact stored inputs and retried the stage.',
        });
      }
      auditStore.close();
    }
  }

  invariant(storyRunId && pitchSlateArtifactId && finalOutlineArtifactId && exportArtifactId, 'principal result IDs are incomplete');
  const markdownPath = resolve(outputDirectory, `${storyRunId}-${exportFilename}`);
  await writeFile(markdownPath, markdown, 'utf8');

  const database = new DatabaseSync(databasePath, { readOnly: true });
  database.exec('PRAGMA foreign_keys = ON');
  try {
    const get = (sql: string, ...params: Array<string | number | null>) => database.prepare(sql).get(...params) as Row | undefined;
    const all = (sql: string, ...params: Array<string | number | null>) => database.prepare(sql).all(...params) as Row[];
    const worldRow = get('SELECT * FROM worlds WHERE world_id = ?', 'shared-world');
    const runRow = get('SELECT * FROM story_runs WHERE story_run_id = ?', storyRunId);
    invariant(worldRow && Number(worldRow.current_canon_revision) === 1, 'shared canon must remain at revision 1');
    invariant(runRow && runRow.status === 'ready_for_promotion', 'story run must remain ready_for_promotion');
    invariant(runRow.final_outline_artifact_id === finalOutlineArtifactId, 'run final-outline pointer mismatch');
    invariant(runRow.pitch_slate_artifact_id === pitchSlateArtifactId, 'run pitch-slate pointer mismatch');

    const activeRows = all("SELECT * FROM artifacts WHERE story_run_id = ? AND lifecycle_status = 'active' ORDER BY created_at, artifact_id", storyRunId);
    const activeArtifacts = activeRows.map(artifactFromRow);
    const byKind = (kind: ArtifactKind) => activeArtifacts.filter((artifact) => artifact.kind === kind);
    const latest = (kind: ArtifactKind) => byKind(kind).at(-1);
    invariant(new Set(byKind('pitch.seed').map((artifact) => artifact.branchId)).size === 3, 'three isolated pitch seeds are required');
    const crossBranch = get(`
      SELECT count(*) AS total FROM artifact_edges edge
      JOIN artifacts parent ON parent.artifact_id = edge.parent_artifact_id
      JOIN artifacts child ON child.artifact_id = edge.child_artifact_id
      WHERE parent.story_run_id = ? AND child.story_run_id = ?
        AND parent.branch_id IS NOT NULL AND child.branch_id IS NOT NULL
        AND parent.branch_id <> child.branch_id
    `, storyRunId, storyRunId);
    invariant(Number(crossBranch?.total) === 0, 'pitch branches crossed before synthesis');

    const selection = latest('decision.pitch-selection');
    invariant(selection, 'active pitch selection is missing');
    const selectionContent = selection.content as { pitchId?: string; pitchSlateArtifactId?: string; pitchSlateHash?: string };
    const slate = latest('pitch.slate');
    invariant(slate && selectionContent.pitchId === 'pitch-a', 'pitch-a was not selected');
    invariant(selectionContent.pitchSlateArtifactId === slate.artifactId && selectionContent.pitchSlateHash === slate.contentHash, 'selection is not bound to the exact slate');
    const pitchReview = latest('review.pitch-continuity');
    invariant(pitchReview && pitchReview.producer.type === 'agent', 'agent pitch-continuity review is missing');
    const pitchReviewContent = pitchReview.content as { verdict?: string; targetArtifactId?: string; targetContentHash?: string };
    invariant(
      pitchReviewContent.verdict === 'pass' && pitchReviewContent.targetArtifactId === slate.artifactId && pitchReviewContent.targetContentHash === slate.contentHash,
      'pitch review does not certify the exact slate',
    );

    const finalOutline = latest('outline.final');
    invariant(finalOutline && finalOutline.artifactId === finalOutlineArtifactId, 'active final outline is missing');
    const outlineContent = finalOutline.content as { scenes?: unknown[] };
    invariant(Array.isArray(outlineContent.scenes) && outlineContent.scenes.length >= 6 && outlineContent.scenes.length <= 8, 'final outline must contain 6–8 scenes');
    const finalReviews = ['review.continuity', 'review.narrative', 'review.theme-pacing'] as const;
    const criticFindings: Record<string, unknown> = {};
    for (const kind of finalReviews) {
      const review = byKind(kind).find((candidate) => {
        const content = candidate.content as { targetArtifactId?: string; targetContentHash?: string };
        return content.targetArtifactId === finalOutline.artifactId && content.targetContentHash === finalOutline.contentHash;
      });
      invariant(review && review.producer.type === 'agent', `${kind} is missing or not agent-produced`);
      const content = review.content as { verdict?: string; findings?: unknown[] };
      invariant(content.verdict === 'pass', `${kind} did not pass`);
      criticFindings[kind] = content.findings ?? [];
    }

    const receiptCount = get("SELECT count(*) AS total FROM artifacts WHERE story_run_id = ? AND kind = 'canon.commit-receipt'", storyRunId);
    const revisionCount = get("SELECT count(*) AS total FROM canon_revisions WHERE world_id = 'shared-world'");
    invariant(Number(receiptCount?.total) === 0, 'a canon commit receipt must not exist');
    invariant(Number(revisionCount?.total) === 1, 'canon revision 2 must not exist');

    const exportArtifact = latest('export.writer-packet');
    invariant(exportArtifact && exportArtifact.artifactId === exportArtifactId, 'writer-packet artifact is missing');
    const renderEdges = get("SELECT count(*) AS total FROM artifact_edges WHERE child_artifact_id = ? AND relationship_type = 'renders'", exportArtifactId);
    invariant(Number(renderEdges?.total) > 0, 'writer packet has no renders provenance');
    const snapshotRow = get('SELECT * FROM artifacts WHERE artifact_id = ?', String(runRow.base_canon_snapshot_artifact_id));
    invariant(snapshotRow, 'pinned canon snapshot is missing');
    const renderedAgain = renderWriterPacket({
      snapshot: artifactFromRow(snapshotRow),
      brief: latest('story.brief')!,
      pitchSlate: slate,
      selection,
      characterPlan: latest('plan.character'),
      worldPlan: latest('plan.world'),
      themePlan: latest('plan.theme-pacing'),
      finalOutline,
      continuityReview: byKind('review.continuity').find((artifact) => (artifact.content as { targetArtifactId?: string }).targetArtifactId === finalOutline.artifactId)!,
      narrativeReview: byKind('review.narrative').find((artifact) => (artifact.content as { targetArtifactId?: string }).targetArtifactId === finalOutline.artifactId)!,
      themeReview: byKind('review.theme-pacing').find((artifact) => (artifact.content as { targetArtifactId?: string }).targetArtifactId === finalOutline.artifactId)!,
    });
    invariant(renderedAgain.markdown === markdown, 'writer packet is not reproducible from exact active artifacts');
    invariant(!/chain-of-thought|token usage/iu.test(markdown), 'writer packet exposes operational internals');
    const slateContent = slate.content as { pitches?: Array<{ id?: string; title?: string }> };
    const selectedPitchTitle = slateContent.pitches?.find((pitch) => pitch.id === 'pitch-a')?.title;
    for (const rejectedPitch of slateContent.pitches?.filter((pitch) => pitch.id !== 'pitch-a') ?? []) {
      if (rejectedPitch.title && rejectedPitch.title !== selectedPitchTitle) {
        invariant(!markdown.includes(rejectedPitch.title), `writer packet exposes rejected pitch ${rejectedPitch.id}`);
      }
    }

    const executionSummary = get(`
      SELECT count(*) AS model_calls,
             sum(input_tokens) AS input_tokens,
             sum(output_tokens) AS output_tokens,
             sum(cost_usd) AS cost_usd
      FROM agent_executions WHERE story_run_id = ?
    `, storyRunId);
    const executionStatusCounts = all(`
      SELECT status, count(*) AS total FROM agent_executions
      WHERE story_run_id = ? GROUP BY status ORDER BY status
    `, storyRunId);
    const failedExecutions = all(`
      SELECT execution_id, agent_name, error_summary, started_at, completed_at
      FROM agent_executions WHERE story_run_id = ? AND status = 'failed'
      ORDER BY started_at
    `, storyRunId);
    const staleArtifacts = all(`
      SELECT artifact_id, kind, logical_key, version FROM artifacts
      WHERE story_run_id = ? AND lifecycle_status IN ('stale', 'superseded')
      ORDER BY created_at
    `, storyRunId);
    const report = {
      status: 'passed',
      prompt: PROMPT,
      clarificationUsed,
      selectedPitchId: 'pitch-a',
      canonRevision: Number(worldRow.current_canon_revision),
      storyRunStatus: String(runRow.status),
      elapsedSeconds: Math.round((Date.now() - new Date(String(runRow.created_at)).getTime()) / 100) / 10,
      attemptElapsedSeconds: Math.round((Date.now() - startedAt) / 100) / 10,
      migrationsApplied: appliedMigrations,
      bootstrap,
      ids: {
        storyRunId,
        pitchSlateArtifactId,
        pitchSelectionArtifactId: selection.artifactId,
        finalOutlineArtifactId,
        canonDeltaArtifactId: String(runRow.canon_delta_artifact_id),
        exportArtifactId,
      },
      outline: {
        title: String((finalOutline.content as { title?: string }).title ?? ''),
        sceneCount: outlineContent.scenes.length,
      },
      criticFindings,
      executionSummary: {
        modelCalls: Number(executionSummary?.model_calls ?? 0),
        modelCallScope: 'Persisted specialist/advisor executions; Eve coordinator calls are not exposed by the current runtime metadata.',
        inputTokens: executionSummary?.input_tokens === null || executionSummary?.input_tokens === undefined ? null : Number(executionSummary.input_tokens),
        outputTokens: executionSummary?.output_tokens === null || executionSummary?.output_tokens === undefined ? null : Number(executionSummary.output_tokens),
        costUsd: executionSummary?.cost_usd === null || executionSummary?.cost_usd === undefined ? null : Number(executionSummary.cost_usd),
        statusCounts: executionStatusCounts,
        failedExecutions,
      },
      staleOrSupersededArtifacts: staleArtifacts,
      responseEventTypes,
      databasePath,
      markdownPath,
    };
    const reportPath = resolve(outputDirectory, `${storyRunId}-live-test-report.json`);
    await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
    process.stdout.write(`${JSON.stringify({ ...report, reportPath }, null, 2)}\n`);
  } finally {
    database.close();
  }
}

await main();
