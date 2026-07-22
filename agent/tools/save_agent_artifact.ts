import { defineTool } from 'eve/tools';
import { randomUUID } from 'node:crypto';
import { z } from 'zod';
import { ArtifactKindSchema, StoryRunStatusSchema } from '../lib/artifact-domain.js';
import {
  AgentExecutionMetadataSchema,
  AgentProducerInputSchema,
  ArtifactParentInputSchema,
  artifactStore,
  StoredArtifactEnvelopeSchema,
} from '../lib/story-store.js';

const forbiddenKinds = new Set([
  'world.foundation',
  'prompt.original',
  'prompt.clarification',
  'decision.pitch-selection',
  'canon.delta',
  'canon.snapshot',
  'canon.commit-receipt',
  'export.writer-packet',
]);

export default defineTool({
  description: 'Validate and persist one declared subagent structured output with exact artifact lineage. This tool always records the producer as an agent.',
  inputSchema: z.object({
    storyRunId: z.string().uuid(),
    branchId: z.enum(['A', 'B', 'C']).nullable().optional(),
    kind: ArtifactKindSchema,
    logicalKey: z.string().min(1).regex(/^[a-z0-9][a-z0-9/_-]*$/),
    content: z.unknown(),
    producer: AgentProducerInputSchema,
    parents: z.array(ArtifactParentInputSchema).min(1),
    supersedesArtifactId: z.string().uuid().optional(),
    expectedSupersededHash: z.string().regex(/^[a-f0-9]{64}$/).optional(),
    expectedStatus: StoryRunStatusSchema.optional(),
    nextStatus: StoryRunStatusSchema.optional(),
    eventSummary: z.string().min(1).optional(),
    execution: AgentExecutionMetadataSchema.optional(),
  }),
  outputSchema: z.object({ artifact: StoredArtifactEnvelopeSchema, executionId: z.string().uuid().optional() }),
  async execute(input) {
    if (forbiddenKinds.has(input.kind)) throw new Error(`${input.kind} cannot be authored by an agent.`);
    if (input.nextStatus && ['ready_for_promotion', 'promoted', 'stale'].includes(input.nextStatus)) {
      throw new Error(`${input.nextStatus} is reserved for deterministic canon tools.`);
    }
    if (input.supersedesArtifactId && !input.expectedSupersededHash) {
      throw new Error('Regeneration requires the exact superseded artifact hash.');
    }
    const store = artifactStore();
    const executionId = input.execution?.executionId ?? randomUUID();
    try {
      const artifact = await store.saveArtifact({
        storyRunId: input.storyRunId,
        branchId: input.branchId,
        kind: input.kind,
        logicalKey: input.logicalKey,
        content: input.content,
        producer: { type: 'agent', ...input.producer, gateway: 'openrouter' },
        parents: input.parents,
        supersedesArtifactId: input.supersedesArtifactId,
        expectedSupersededHash: input.expectedSupersededHash,
        expectedStatus: input.expectedStatus,
        nextStatus: input.nextStatus,
        eventSummary: input.eventSummary,
      });
      await store.recordAgentExecution({
          executionId,
          storyRunId: input.storyRunId,
          agentName: input.producer.name,
          eveChildSessionId: input.execution?.eveChildSessionId,
          modelId: input.execution?.modelId ?? input.producer.modelId,
          gateway: 'openrouter',
          inputArtifactIds: input.parents.map((parent) => parent.artifactId),
          outputArtifactIds: [artifact.artifactId],
          promptRevision: input.execution?.promptRevision,
          skillRevision: input.execution?.skillRevision,
          startedAt: input.execution?.startedAt ?? artifact.createdAt,
          completedAt: input.execution?.completedAt ?? new Date().toISOString(),
          inputTokens: input.execution?.inputTokens,
          outputTokens: input.execution?.outputTokens,
          costUsd: input.execution?.costUsd,
          status: 'succeeded',
        });
      return { artifact, executionId };
    } catch (error) {
      try {
        await store.recordAgentExecution({
          executionId,
          storyRunId: input.storyRunId,
          agentName: input.producer.name,
          eveChildSessionId: input.execution?.eveChildSessionId,
          modelId: input.execution?.modelId ?? input.producer.modelId,
          gateway: 'openrouter',
          inputArtifactIds: input.parents.map((parent) => parent.artifactId),
          outputArtifactIds: [],
          promptRevision: input.execution?.promptRevision,
          skillRevision: input.execution?.skillRevision,
          startedAt: input.execution?.startedAt ?? new Date().toISOString(),
          completedAt: new Date().toISOString(),
          inputTokens: input.execution?.inputTokens,
          outputTokens: input.execution?.outputTokens,
          costUsd: input.execution?.costUsd,
          status: 'failed',
          errorSummary: error instanceof Error ? error.message : String(error),
        });
      } catch {
        // Preserve the original validation/storage error if the audit row cannot be written.
      }
      throw error;
    }
  },
});
