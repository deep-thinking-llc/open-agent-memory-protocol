import { z } from 'zod';

export const ExpertiseLevel = z.enum(['novice', 'intermediate', 'advanced', 'expert']);
export type ExpertiseLevel = z.infer<typeof ExpertiseLevel>;

export const CommunicationProfile = z.object({
  verbosity: z.number().min(-1).max(1),
  formality: z.number().min(-1).max(1),
  prefers_examples: z.boolean(),
  prefers_explanations: z.boolean(),
  languages: z.array(z.string()).default(['en']),
});
export type CommunicationProfile = z.infer<typeof CommunicationProfile>;

export const ExpertiseDomain = z.object({
  domain: z.string().min(1),
  level: ExpertiseLevel,
  confidence: z.number().min(0).max(1),
  evidence_sessions: z.array(z.string()).default([]),
  last_observed: z.string().datetime().optional(),
});

export const Correction = z.object({
  what_agent_did: z.string(),
  what_user_wanted: z.string(),
  context: z.string().optional(),
  session_id: z.string(),
  timestamp: z.string().datetime(),
});

export const StatedPreference = z.object({
  key: z.string(),
  value: z.string(),
  timestamp: z.string().datetime(),
});

export const UserModel = z.object({
  oamp_version: z.string().min(1),
  type: z.literal('user_model'),
  user_id: z.string().min(1),
  model_version: z.number().int().positive(),
  updated_at: z.string().datetime(),
  communication: CommunicationProfile.optional(),
  expertise: z.array(ExpertiseDomain).default([]),
  corrections: z.array(Correction).default([]),
  stated_preferences: z.array(StatedPreference).default([]),
  metadata: z.record(z.unknown()).default({}),
});
export type UserModel = z.infer<typeof UserModel>;
