import { z } from 'zod';

export const KnowledgeCategory = z.enum(['fact', 'preference', 'pattern', 'correction']);
export type KnowledgeCategory = z.infer<typeof KnowledgeCategory>;

export const KnowledgeSource = z.object({
  session_id: z.string().min(1),
  agent_id: z.string().optional(),
  timestamp: z.string().datetime(),
});

export const ProvenanceSource = z.object({
  session_id: z.string().min(1),
  agent_id: z.string().optional(),
  timestamp: z.string().datetime(),
  turn_id: z.string().optional(),
});
export type ProvenanceSource = z.infer<typeof ProvenanceSource>;

export const Provenance = z.object({
  sources: z.array(ProvenanceSource).min(1),
  derived: z.boolean().optional(),
});
export type Provenance = z.infer<typeof Provenance>;

export const GovernanceHandling = z.object({
  retrieval: z.enum(['governed', 'ungoverned']).optional(),
  export: z.enum(['governed', 'ungoverned']).optional(),
  stream: z.enum(['governed', 'ungoverned']).optional(),
});
export type GovernanceHandling = z.infer<typeof GovernanceHandling>;

export const Governance = z.object({
  sensitivity_class: z.enum(['public', 'internal', 'confidential', 'restricted']),
  labels: z.array(z.string().min(1)).default([]),
  handling: GovernanceHandling.optional(),
});
export type Governance = z.infer<typeof Governance>;

export const KnowledgeDecay = z.object({
  half_life_days: z.number().positive().nullable().optional(),
  last_confirmed: z.string().datetime().optional(),
});

export const KnowledgeEntry = z.object({
  oamp_version: z.enum(['1.0.0', '1.1.0', '1.2.0', '1.3.0']),
  type: z.literal('knowledge_entry'),
  id: z.string().uuid(),
  user_id: z.string().min(1),
  category: KnowledgeCategory,
  content: z.string().min(1),
  confidence: z.number().min(0).max(1),
  source: KnowledgeSource,
  provenance: Provenance.optional(),
  governance: Governance.optional(),
  decay: KnowledgeDecay.optional(),
  tags: z.array(z.string()).default([]),
  metadata: z.record(z.unknown()).default({}),
});
export type KnowledgeEntry = z.infer<typeof KnowledgeEntry>;

export const KnowledgeStore = z.object({
  oamp_version: z.enum(['1.0.0', '1.1.0', '1.2.0', '1.3.0']),
  type: z.literal('knowledge_store'),
  user_id: z.string().min(1),
  entries: z.array(KnowledgeEntry),
  exported_at: z.string().datetime(),
  agent_id: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
});
export type KnowledgeStore = z.infer<typeof KnowledgeStore>;
