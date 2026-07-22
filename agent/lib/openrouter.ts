import { createOpenRouter } from '@openrouter/ai-sdk-provider';
import type { LanguageModel } from 'ai';

const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
  compatibility: 'strict',
  appName: 'Story Computing Machine',
  appUrl: 'https://github.com/BoundlessStudio/story-computing-machine',
});

export function rootModel(): LanguageModel {
  return openrouter(process.env.OPENROUTER_MODEL ?? 'openai/gpt-4.1-mini');
}

export function workerModel(): LanguageModel {
  return openrouter(process.env.OPENROUTER_WORKER_MODEL ?? 'openai/gpt-4.1-nano');
}

export function advisorModel(): LanguageModel {
  return openrouter(process.env.OPENROUTER_ADVISOR_MODEL ?? 'anthropic/claude-sonnet-4');
}
