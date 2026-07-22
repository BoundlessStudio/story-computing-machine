import { defineTool } from 'eve/tools';
import { z } from 'zod';
import { artifactStore } from '../lib/story-store.js';

const statusSchema = z.enum(['running', 'failed']);

export default defineTool({
  description: 'Start an agent execution audit record or close a failed child execution that produced no artifact. Successful executions are completed by save_agent_artifact.',
  inputSchema: z.object({
    executionId: z.string().uuid().optional(),
    storyRunId: z.string().uuid(),
    agentName: z.string().min(1),
    inputArtifactIds: z.array(z.string().uuid()).min(1),
    status: statusSchema,
    eveChildSessionId: z.string().min(1).optional(),
    modelId: z.string().min(1).optional(),
    promptRevision: z.string().min(1).optional(),
    skillRevision: z.string().min(1).optional(),
    startedAt: z.string().datetime(),
    completedAt: z.string().datetime().optional(),
    inputTokens: z.number().int().nonnegative().optional(),
    outputTokens: z.number().int().nonnegative().optional(),
    costUsd: z.number().nonnegative().optional(),
    errorSummary: z.string().min(1).optional(),
  }).superRefine((input, context) => {
    if (input.status === 'failed' && !input.completedAt) {
      context.addIssue({ code: 'custom', path: ['completedAt'], message: 'A failed execution requires completedAt.' });
    }
    if (input.status === 'failed' && !input.errorSummary) {
      context.addIssue({ code: 'custom', path: ['errorSummary'], message: 'A failed execution requires a sanitized diagnostic summary.' });
    }
  }),
  outputSchema: z.object({ executionId: z.string().uuid(), status: statusSchema }),
  async execute(input) {
    const store = artifactStore();
    const [run, artifacts] = await Promise.all([
      store.getRun(input.storyRunId),
      Promise.all(input.inputArtifactIds.map((artifactId) => store.getArtifact(artifactId))),
    ]);
    if (!run) throw new Error('Story run not found.');
    if (artifacts.some((artifact) => !artifact || (
      artifact.storyRunId !== input.storyRunId
      && artifact.artifactId !== run.baseCanonSnapshotArtifactId
    ))) {
      throw new Error('Every execution input must resolve to this run or its world-level canon snapshot.');
    }
    const executionId = await store.recordAgentExecution({
      executionId: input.executionId,
      storyRunId: input.storyRunId,
      agentName: input.agentName,
      eveChildSessionId: input.eveChildSessionId,
      modelId: input.modelId,
      gateway: 'openrouter',
      inputArtifactIds: input.inputArtifactIds,
      outputArtifactIds: [],
      promptRevision: input.promptRevision,
      skillRevision: input.skillRevision,
      startedAt: input.startedAt,
      completedAt: input.completedAt,
      inputTokens: input.inputTokens,
      outputTokens: input.outputTokens,
      costUsd: input.costUsd,
      status: input.status,
      errorSummary: input.errorSummary,
    });
    return { executionId, status: input.status };
  },
});
