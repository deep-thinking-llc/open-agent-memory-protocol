import { describe, it, expect } from 'vitest';
import { KnowledgeEntry, KnowledgeStore, UserModel, OAMP_VERSION } from '../index';
import * as fs from 'fs';
import * as path from 'path';

describe('KnowledgeEntry validation', () => {
  it('validates a correct entry', () => {
    const entry = {
      oamp_version: '1.0.0',
      type: 'knowledge_entry' as const,
      id: '550e8400-e29b-41d4-a716-446655440000',
      user_id: 'user-1',
      category: 'fact' as const,
      content: 'User knows Rust',
      confidence: 0.85,
      source: { session_id: 'sess-1', timestamp: '2026-03-15T14:32:00Z' },
    };
    expect(KnowledgeEntry.parse(entry)).toBeTruthy();
  });

  it('rejects confidence > 1.0', () => {
    const entry = {
      oamp_version: '1.0.0', type: 'knowledge_entry' as const,
      id: '550e8400-e29b-41d4-a716-446655440000', user_id: 'user-1',
      category: 'fact' as const, content: 'test', confidence: 1.5,
      source: { session_id: 's', timestamp: '2026-01-01T00:00:00Z' },
    };
    expect(() => KnowledgeEntry.parse(entry)).toThrow();
  });

  it('rejects invalid category', () => {
    const entry = {
      oamp_version: '1.0.0', type: 'knowledge_entry' as const,
      id: '550e8400-e29b-41d4-a716-446655440000', user_id: 'user-1',
      category: 'opinion', content: 'test', confidence: 0.5,
      source: { session_id: 's', timestamp: '2026-01-01T00:00:00Z' },
    };
    expect(() => KnowledgeEntry.parse(entry)).toThrow();
  });

  it('parses example file', () => {
    const json = fs.readFileSync(path.join(__dirname, '../../../../spec/v1/examples/knowledge-entry.json'), 'utf-8');
    const entry = KnowledgeEntry.parse(JSON.parse(json));
    expect(entry.category).toBe('preference');
    expect(entry.confidence).toBeGreaterThan(0);
  });
});

describe('UserModel validation', () => {
  it('validates a correct model', () => {
    const model = {
      oamp_version: '1.0.0', type: 'user_model' as const,
      user_id: 'user-1', model_version: 1,
      updated_at: '2026-03-28T12:00:00Z',
    };
    expect(UserModel.parse(model)).toBeTruthy();
  });

  it('rejects verbosity out of range', () => {
    const model = {
      oamp_version: '1.0.0', type: 'user_model' as const,
      user_id: 'user-1', model_version: 1,
      updated_at: '2026-03-28T12:00:00Z',
      communication: { verbosity: 2.0, formality: 0, prefers_examples: true, prefers_explanations: true },
    };
    expect(() => UserModel.parse(model)).toThrow();
  });

  it('parses example file', () => {
    const json = fs.readFileSync(path.join(__dirname, '../../../../spec/v1/examples/user-model.json'), 'utf-8');
    const model = UserModel.parse(JSON.parse(json));
    expect(model.expertise.length).toBeGreaterThan(0);
    expect(model.expertise[0].level).toBe('expert');
  });
});
