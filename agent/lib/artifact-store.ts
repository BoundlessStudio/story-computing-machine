import {
  artifactContentHash,
  type ArtifactKind,
} from './artifact-domain.js';

export const SHARED_WORLD_ID = 'shared-world' as const;

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type ArtifactLifecycle = 'active' | 'superseded' | 'stale' | 'rejected';
export type ArtifactRelationship =
  | 'consumes'
  | 'derives-from'
  | 'reviews'
  | 'supersedes'
  | 'promotes'
  | 'renders';
export type StoryRunStatus =
  | 'analyzing'
  | 'needs_clarification'
  | 'building_pitches'
  | 'awaiting_pitch'
  | 'planning'
  | 'reviewing'
  | 'needs_revision'
  | 'ready_for_promotion'
  | 'promoted'
  | 'stale'
  | 'failed';

export interface ArtifactProducer {
  type: 'human' | 'agent' | 'tool';
  name: string;
  modelId?: string;
  gateway?: 'openrouter';
  eveSessionId?: string;
}

export interface ArtifactEnvelope<T extends JsonValue = JsonValue> {
  artifactId: string;
  worldId: typeof SHARED_WORLD_ID;
  storyRunId: string | null;
  branchId: 'A' | 'B' | 'C' | null;
  kind: ArtifactKind;
  schemaVersion: number;
  logicalKey: string;
  version: number;
  canonRevision: number;
  canonSnapshotArtifactId: string;
  content: T;
  contentHash: string;
  producer: ArtifactProducer;
  lifecycleStatus: ArtifactLifecycle;
  createdAt: string;
}

export interface StoryRunRecord {
  storyRunId: string;
  worldId: typeof SHARED_WORLD_ID;
  baseCanonRevision: number;
  baseCanonSnapshotArtifactId: string;
  status: StoryRunStatus;
  originalPromptArtifactId: string;
  briefArtifactId: string | null;
  pitchSlateArtifactId: string | null;
  pitchSelectionArtifactId: string | null;
  blueprintArtifactId: string | null;
  finalOutlineArtifactId: string | null;
  canonDeltaArtifactId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ArtifactParent {
  artifactId: string;
  relationship: ArtifactRelationship;
}

export interface ArtifactLineageLink {
  direction: 'parent' | 'child';
  relationship: ArtifactRelationship;
  artifactId: string;
  kind: ArtifactKind;
  logicalKey: string;
  version: number;
  contentHash: string;
  lifecycleStatus: ArtifactLifecycle;
}

export interface ArtifactValidator {
  parse(kind: ArtifactKind, schemaVersion: number, content: unknown): unknown;
}

export interface SaveArtifactInput {
  storyRunId: string;
  branchId?: 'A' | 'B' | 'C' | null;
  kind: ArtifactKind;
  schemaVersion?: number;
  logicalKey: string;
  content: unknown;
  producer: ArtifactProducer;
  parents?: ArtifactParent[];
  supersedesArtifactId?: string;
  expectedSupersededHash?: string;
  expectedStatus?: StoryRunStatus;
  nextStatus?: StoryRunStatus;
  eventSummary?: string;
}

export interface JsonPatchOperation {
  op: 'add' | 'remove' | 'replace' | 'move' | 'copy' | 'test';
  path: string;
  from?: string;
  value?: unknown;
}

export interface AgentExecutionInput {
  executionId?: string;
  storyRunId: string;
  agentName: string;
  eveChildSessionId?: string;
  modelId?: string;
  gateway?: 'openrouter';
  inputArtifactIds: string[];
  outputArtifactIds: string[];
  promptRevision?: string;
  skillRevision?: string;
  startedAt: string;
  completedAt?: string;
  inputTokens?: number;
  outputTokens?: number;
  costUsd?: number;
  status: 'running' | 'succeeded' | 'failed';
  errorSummary?: string;
}

export interface CanonBootstrapInput {
  world: unknown;
  normalizedSnapshot: unknown;
  producerName?: string;
}

export interface PromotionInput {
  storyRunId: string;
  finalOutlineArtifactId: string;
  canonDeltaArtifactId: string;
  nextSnapshotContent: unknown;
  producerName?: string;
}

export function asJsonValue(value: unknown, path = '$'): JsonValue {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return value;
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (Array.isArray(value)) return value.map((item, index) => asJsonValue(item, `${path}[${index}]`));
  if (typeof value === 'object') {
    const result: Record<string, JsonValue> = {};
    for (const [key, child] of Object.entries(value)) {
      if (child === undefined) throw new Error(`Undefined JSON value at ${path}.${key}`);
      result[key] = asJsonValue(child, `${path}.${key}`);
    }
    return result;
  }
  throw new Error(`Unsupported JSON value at ${path}`);
}

export function canonicalJson(value: JsonValue): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key]!)}`).join(',')}}`;
}

export function hashArtifactContent(content: JsonValue): string {
  return artifactContentHash(content);
}

function decodePointer(token: string): string {
  return token.replace(/~1/gu, '/').replace(/~0/gu, '~');
}

function pointerParts(path: string): string[] {
  if (path === '') return [];
  if (!path.startsWith('/')) throw new Error(`Invalid JSON Pointer: ${path}`);
  return path.slice(1).split('/').map(decodePointer);
}

function cloneJson<T extends JsonValue>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function getPointer(document: JsonValue, path: string): JsonValue {
  let current: JsonValue = document;
  for (const token of pointerParts(path)) {
    if (Array.isArray(current)) {
      if (!/^\d+$/u.test(token) || Number(token) >= current.length) throw new Error(`JSON Pointer not found: ${path}`);
      current = current[Number(token)]!;
    } else if (current && typeof current === 'object') {
      if (['__proto__', 'prototype', 'constructor'].includes(token)) throw new Error('Unsafe JSON Pointer');
      if (!(token in current)) throw new Error(`JSON Pointer not found: ${path}`);
      current = current[token]!;
    } else throw new Error(`JSON Pointer not found: ${path}`);
  }
  return current;
}

function mutatePointer(document: JsonValue, operation: 'add' | 'remove' | 'replace', path: string, value?: JsonValue): JsonValue {
  const parts = pointerParts(path);
  if (parts.length === 0) {
    if (operation === 'remove') throw new Error('Cannot remove the artifact document root');
    if (value === undefined) throw new Error(`${operation} requires a value`);
    return cloneJson(value);
  }
  const token = parts.pop()!;
  const parentPath = `/${parts.map((part) => part.replace(/~/gu, '~0').replace(/\//gu, '~1')).join('/')}`;
  const parent = getPointer(document, parts.length ? parentPath : '');
  if (Array.isArray(parent)) {
    if (token === '-' && operation === 'add') {
      if (value === undefined) throw new Error('add requires a value');
      parent.push(cloneJson(value));
      return document;
    }
    if (!/^\d+$/u.test(token)) throw new Error(`Invalid array index: ${token}`);
    const index = Number(token);
    if (operation === 'add') {
      if (index > parent.length || value === undefined) throw new Error(`Invalid array add at ${path}`);
      parent.splice(index, 0, cloneJson(value));
    } else {
      if (index >= parent.length) throw new Error(`JSON Pointer not found: ${path}`);
      if (operation === 'remove') parent.splice(index, 1);
      else {
        if (value === undefined) throw new Error('replace requires a value');
        parent[index] = cloneJson(value);
      }
    }
  } else if (parent && typeof parent === 'object') {
    if (['__proto__', 'prototype', 'constructor'].includes(token)) throw new Error('Unsafe JSON Pointer');
    if (operation !== 'add' && !(token in parent)) throw new Error(`JSON Pointer not found: ${path}`);
    if (operation === 'remove') delete parent[token];
    else {
      if (value === undefined) throw new Error(`${operation} requires a value`);
      parent[token] = cloneJson(value);
    }
  } else throw new Error(`JSON Pointer parent not found: ${path}`);
  return document;
}

export function applyArtifactPatch(content: JsonValue, operations: JsonPatchOperation[]): JsonValue {
  let document: JsonValue = { content: cloneJson(content) };
  for (const operation of operations) {
    if (operation.path !== '/content' && !operation.path.startsWith('/content/')) throw new Error('JSON Patch may only modify /content');
    if (operation.from && operation.from !== '/content' && !operation.from.startsWith('/content/')) throw new Error('JSON Patch may only read /content');
    if (operation.op === 'test') {
      if (operation.value === undefined || canonicalJson(getPointer(document, operation.path)) !== canonicalJson(asJsonValue(operation.value))) {
        throw new Error(`JSON Patch test failed at ${operation.path}`);
      }
      continue;
    }
    if (operation.op === 'copy' || operation.op === 'move') {
      if (!operation.from) throw new Error(`${operation.op} requires from`);
      const copied = cloneJson(getPointer(document, operation.from));
      if (operation.op === 'move') document = mutatePointer(document, 'remove', operation.from);
      document = mutatePointer(document, 'add', operation.path, copied);
      continue;
    }
    document = mutatePointer(document, operation.op, operation.path, operation.value === undefined ? undefined : asJsonValue(operation.value));
  }
  if (!document || typeof document !== 'object' || Array.isArray(document) || !('content' in document)) {
    throw new Error('Patch removed the artifact content root');
  }
  return document.content!;
}
