# Open Agent Memory Protocol (OAMP)

[English](../README.md) | [中文](README.zh.md) | [한국어](README.ko.md) | [Bahasa Melayu](README.ms.md)

**AIエージェントとメモリバックエンド間でメモリデータを保存、交換、クエリするための標準規格です。**

OAMPは、AIエージェントがユーザーについて学んだことを記憶し、プライバシーとセキュリティを基盤から組み込みながら、異なるエージェントフレームワークやストレージバックエンド間でポータブルにメモリを共有することを可能にします。

## なぜOAMPが必要なのか？

現在、すべてのAIエージェントフレームワークはユーザーメモリを異なる方法で保存しています。エージェントを切り替えると、以前のエージェントがあなたについて学んだすべてのこと——好み、専門知識、修正履歴、ワークフローパターン——を失います。OAMPは以下を定義することでこの問題を解決します：

- **共通フォーマット** — エージェントメモリ用（JSON Schema + Protobuf）
- **REST API契約** — メモリバックエンド用
- **プライバシー要件** — すべての実装が満たすべきもの
- **リファレンス実装** — RustおよびTypeScriptで提供

### 問題点

- エージェントAが、あなたが簡潔な回答を好み、Rustの専門家であり、コード例で`unwrap()`を使ってほしくないことを学習します
- エージェントBに切り替えます
- エージェントBはあなたについて何も知りません——ゼロからのスタートです
- あなたの修正履歴、好み、専門知識はエージェントAの独自フォーマットに閉じ込められています

### OAMPの解決策

- エージェントAがあなたのメモリをOAMPドキュメント（標準JSON）としてエクスポートします
- エージェントBがそれをインポートします
- エージェントBがあなたの好み、専門知識、修正履歴を即座に把握します
- ベンダーロックインなし。あなたのメモリはあなたのものです。

## OAMPが定義するもの

### ナレッジ層
エージェントがあなたについて学ぶ個別の事実：

```json
{
  "type": "knowledge_entry",
  "category": "correction",
  "content": "unwrap()は絶対に使用しないでください——常に?演算子で適切なエラー処理を行ってください",
  "confidence": 0.98,
  "source": { "session_id": "sess-003", "timestamp": "2026-03-12T16:45:00Z" }
}
```

4つのカテゴリ：**fact**（客観的情報）、**preference**（好みの方法）、**pattern**（よく行う行動）、**correction**（エージェントにやめるよう指示したこと）。

### ユーザーモデル層
あなたが誰であるかのより詳細なプロフィール：

```json
{
  "type": "user_model",
  "communication": { "verbosity": -0.6, "formality": 0.2 },
  "expertise": [
    { "domain": "rust", "level": "expert", "confidence": 0.95 },
    { "domain": "react", "level": "novice", "confidence": 0.60 }
  ],
  "corrections": [
    { "what_agent_did": "unwrap()を使用した", "what_user_wanted": "?演算子を使用する" }
  ]
}
```

### プライバシー要件（必須）

OAMPはプライバシーを重視しています。準拠する実装は**必ず**以下を満たさなければなりません：

- **保存データをすべて暗号化**（AES-256-GCM推奨）
- **完全なデータエクスポートをサポート** — ユーザーが自分のメモリを所有します
- **完全な削除をサポート** — ソフトデリートではなく、本当の削除
- **コンテンツを絶対にログに記録しない** — IDとカテゴリのみ
- **出所を追跡** — すべてのエントリがどこから来たかを記録

## リポジトリ構造

```
open-agent-memory-protocol/
├── spec/v1/                    # 権威ある仕様
│   ├── oamp-v1.md             # 人間が読める仕様（RFC 2119）
│   ├── *.schema.json          # JSON Schema (draft-2020-12)
│   └── examples/              # 有効なサンプルドキュメント
├── proto/oamp/v1/             # Protocol Buffer定義
├── reference/
│   ├── rust/                  # Rust crate: oamp-types
│   └── typescript/            # npmパッケージ: @oamp/types
├── validators/
│   ├── validate.sh            # CLIバリデータ
│   └── test-fixtures/         # 有効および無効なテストドキュメント
└── docs/
    ├── guide-for-agents.md    # エージェントにOAMPを追加する方法
    ├── guide-for-backends.md  # OAMPバックエンドを構築する方法
    └── security-guide.md      # 暗号化、GDPR、脅威モデル
```

## クイックスタート

### ドキュメントの検証

```bash
./validators/validate.sh my-export.json
```

### Rust

```toml
[dependencies]
oamp-types = "1.0"
```

```rust
use oamp_types::{KnowledgeEntry, KnowledgeCategory};

// ナレッジエントリを作成
let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "unwrap()は絶対に使用しないでください——代わりに?演算子を使用してください",
    0.98,
    "session-42",
);

// OAMP JSONにシリアライズ
let json = serde_json::to_string_pretty(&entry)?;

// 検証
oamp_types::validate::validate_knowledge_entry(&entry)?;
```

### TypeScript

```bash
npm install @oamp/types
```

```typescript
import { KnowledgeEntry } from '@oamp/types';

// OAMPドキュメントを検証してパース
const entry = KnowledgeEntry.parse(jsonData);

// 型安全なアクセス
console.log(entry.category); // "correction"
console.log(entry.confidence); // 0.98
```

## エージェント開発者向け

エージェントにOAMPサポートを追加したいですか？[エージェントガイド](guide-for-agents.md)をご覧ください。

要約：
1. **エクスポート** — 内部メモリタイプをOAMP JSONにマッピング
2. **インポート** — OAMP JSONを内部タイプにパース
3. **検証** — JSON Schemaまたはリファレンスライブラリを使用して準拠を確認

## バックエンド開発者向け

OAMP準拠のメモリバックエンドを構築したいですか？[バックエンドガイド](guide-for-backends.md)をご覧ください。

バックエンドは、ナレッジのCRUD、ユーザーモデルの保存、一括エクスポート/インポートをカバーする9つのRESTエンドポイントを実装する必要があります。

## 仕様

完全な仕様は[spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md)にあります。準拠レベルを定義するためにRFC 2119の用語（MUST、SHOULD、MAY）を使用しています。

### バージョン

現在：**v1.0.0**

仕様はセマンティックバージョニングに従います。ドキュメントには前方互換性のための`oamp_version`フィールドが含まれます。

### 将来の計画（v2.0）

v2.0の計画（コミュニティのフィードバックに基づく）：
- セッション成果（構造化されたタスク記録）
- スキルメトリクス（実行統計）
- 作業パターン（活動時間、ツールの好み）
- リアルタイムメモリ同期のためのストリーミングAPI

## セキュリティ

[セキュリティガイド](security-guide.md)で以下を確認してください：
- 推奨暗号スイート
- 鍵管理パターン
- GDPR第17条 / CCPA準拠マッピング
- メモリ交換の脅威モデル

## コントリビュート

コントリビュートを歓迎します。以下をお願いします：
1. 変更を提案する前に仕様を読んでください
2. すべてのSchema変更にテストフィクスチャを追加してください
3. RustとTypeScriptの両方のリファレンス実装を更新してください
4. 既存のコードスタイルに従ってください

## お問い合わせ

ご質問、パートナーシップ、フィードバック：

**メール：** contact@dthink.ai

## ライセンス

MIT — [LICENSE](../LICENSE)を参照
