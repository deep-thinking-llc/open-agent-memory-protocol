import { z } from 'zod';

export const KnowledgeCategory = z.enum(['fact', 'preference', 'pattern', 'correction']);
export type KnowledgeCategory = z.infer<typeof KnowledgeCategory>;

export const KnowledgeSource = z.object({
  session_id: z.string().min(1),
  agent_id: z.string().optional(),
  timestamp: z.string().datetime(),
});

export const KnowledgeDecay = z.object({
  half_life_days: z.number().positive().nullable().optional(),
  last_confirmed: z.string().datetime().optional(),
});

export const KnowledgeEntry = z.object({
  oamp_version: z.string().min(1),
  type: z.literal('knowledge_entry'),
  id: z.string().uuid(),
  user_id: z.string().min(1),
  category: KnowledgeCategory,
  content: z.string().min(1),
  confidence: z.number().min(0).max(1),
  source: KnowledgeSource,
  decay: KnowledgeDecay.optional(),
  tags: z.array(z.string()).default([]),
  metadata: z.record(z.unknown()).default({}),
});
export type KnowledgeEntry = z.infer<typeof KnowledgeEntry>;

export const KnowledgeStore = z.object({
  oamp_version: z.string().min(1),
  type: z.literal('knowledge_store'),
  user_id: z.string().min(1),
  entries: z.array(KnowledgeEntry),
  exported_at: z.string().datetime(),
  agent_id: z.string().optional(),
});
export type KnowledgeStore = z.infer<typeof KnowledgeStore>;
