<div align="center">

# Open Agent Memory Protocol

### AIエージェントの記憶は、あなたのものであるべきです。

[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](../spec/v1/oamp-v1.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)
[![Rust Crate](https://img.shields.io/badge/crate-oamp--types-orange.svg)](../reference/rust/)
[![npm Package](https://img.shields.io/badge/npm-%40oamp%2Ftypes-red.svg)](../reference/typescript/)
[![PyPI Package](https://img.shields.io/pypi/v/oamp-types.svg)](https://pypi.org/project/oamp-types/)

[仕様](../spec/v1/oamp-v1.md) | [Rust Crate](../reference/rust/) | [TypeScript パッケージ](../reference/typescript/) | [Python パッケージ](../reference/python/) | [セキュリティガイド](security-guide.md)

---

[English](../README.md) | [中文](README.zh.md) | [한국어](README.ko.md) | [Bahasa Melayu](README.ms.md)

</div>

## 問題点

すべてのAIエージェントはメモリを異なる方法で保存しています。エージェントを切り替えると、ゼロからのスタートです。

```
エージェント A                          エージェント B
  あなたの好みを学習           →     何も知らない
  あなたの専門知識を追跡       →     最初からやり直し
  修正を記憶                   →     同じミスを繰り返す
  あなたのワークフローを理解   →     汎用的な応答
```

あなたの修正履歴、好み、専門知識はプロプライエタリなフォーマットに閉じ込められています。**切り替えるたびに、数週間分のコンテキストを失います。**

## 解決策

OAMPは、エージェントメモリをポータブルで、プライバシーが守られ、相互運用可能にするオープンスタンダードです。

```
エージェント A                          エージェント B
  OAMPとしてエクスポート       →     OAMPをインポート
  標準JSONフォーマット         →     即座にコンテキスト取得
  あなたのデータ、あなたの管理 →     ベンダーロックインなし
```

---

## 核心コンテンツ

<table>
<tr>
<td width="50%">

### ナレッジ層

エージェントが学ぶ個別の事実：

```json
{
  "category": "correction",
  "content": "unwrap()は使用しないでください — ?演算子を使用してください",
  "confidence": 0.98
}
```

4つのタイプ：**fact** · **preference** · **pattern** · **correction**

</td>
<td width="50%">

### ユーザーモデル層

あなたが誰であるかの詳細なプロフィール：

```json
{
  "expertise": [
    { "domain": "rust", "level": "expert" },
    { "domain": "react", "level": "novice" }
  ],
  "communication": { "verbosity": -0.6 }
}
```

追跡項目：**専門知識** · **コミュニケーションスタイル** · **修正履歴** · **好み**

</td>
</tr>
</table>

---

## プライバシー最優先

OAMPはプライバシーをオプションとして扱いません。これらは**必須要件**であり、ガイドラインではありません：

| 要件 | 詳細 |
|:---|:---|
| **保存データの暗号化** | すべての保存データは暗号化されなければなりません（AES-256-GCM推奨） |
| **ユーザーデータの所有権** | 完全なエクスポートをサポートしなければなりません — ユーザーが自分のメモリを所有します |
| **削除の権利** | ソフトデリートではなく、本当の削除。GDPR第17条準拠 |
| **コンテンツログの禁止** | 実装はナレッジコンテンツをログに記録してはなりません |
| **出所の追跡** | すべてのエントリが、いつどこで学習されたかを記録します |

---

## クイックスタート

### 検証

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

let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "Never use unwrap() — use ? operator instead",
    0.98,
    "session-42",
);

// Validate against spec
oamp_types::validate::validate_knowledge_entry(&entry)?;
```

### TypeScript

```bash
npm install @oamp/types
```

```typescript
import { KnowledgeEntry } from '@oamp/types';

const entry = KnowledgeEntry.parse(jsonData);
console.log(entry.category);   // "correction"
console.log(entry.confidence);  // 0.98
```

### Python

```bash
pip install oamp-types
```

```python
from oamp_types import (
    KnowledgeEntry, KnowledgeCategory, KnowledgeSource,
    validate_knowledge_entry,
)

entry = KnowledgeEntry(
    user_id="user-123",
    category=KnowledgeCategory.correction,
    content="unwrap()は使用しないでください — ?演算子を使用してください",
    confidence=0.98,
    source=KnowledgeSource(session_id="session-42"),
)

# 検証
errors = validate_knowledge_entry(entry)

# JSONにシリアライズ（null フィールドを除外）
json_str = entry.model_dump_json(exclude_none=True)
```

---

## リポジトリ構造

```
spec/v1/
  oamp-v1.md              権威ある仕様（RFC 2119）
  *.schema.json            JSON Schema定義（draft-2020-12）
  examples/                有効なサンプルドキュメント

proto/oamp/v1/             Protocol Buffer定義

reference/
  rust/                    Rust crate: oamp-types
  typescript/              npmパッケージ: @oamp/types
  python/                  PyPIパッケージ: oamp-types
  go/                      Goモジュール: oamp-go
  elixir/                  Hexパッケージ: oamp_types
  server/                  FastAPIリファレンスバックエンド

validators/
  validate.sh              CLIドキュメントバリデータ
  test-fixtures/            有効および無効なテストドキュメント

docs/
  guide-for-agents.md      エージェントにOAMPを実装する
  guide-for-backends.md    OAMP準拠のバックエンドを構築する
  security-guide.md        暗号化、GDPR/CCPA、脅威モデル
```

---

## OAMPの統合

<table>
<tr>
<td width="50%">

### エージェント開発者向け

エージェントにメモリのポータビリティを追加：

1. **エクスポート** — 内部タイプをOAMP JSONにマッピング
2. **インポート** — OAMP JSONを内部タイプにパース
3. **検証** — スキーマへの準拠を確認

[エージェントガイドを読む →](guide-for-agents.md)

</td>
<td width="50%">

### バックエンド開発者向け

OAMP準拠のメモリストアを構築：

- 9つのRESTエンドポイント（ナレッジCRUD、ユーザーモデル、エクスポート/インポート）
- 保存時の暗号化（必須）
- 検索（FTS、ベクトル、またはハイブリッド — お好みで）

[バックエンドガイドを読む →](guide-for-backends.md)

</td>
</tr>
</table>

---

## 仕様

| | |
|:---|:---|
| **現在のバージョン** | v1.0.0 |
| **スキーマ形式** | JSON Schema (draft-2020-12) + Protocol Buffers |
| **準拠言語** | RFC 2119 (MUST, SHOULD, MAY) |
| **完全な仕様** | [spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md) |

### v2.0の計画

コミュニティのフィードバックに基づく：
- セッション成果（構造化されたタスク記録）
- スキルメトリクス（実行統計）
- 作業パターン（活動時間、ツールの好み）
- リアルタイムメモリ同期のためのストリーミングAPI

---

## コントリビュート

コントリビュートを歓迎します：

1. 変更を提案する前に[仕様](../spec/v1/oamp-v1.md)を読んでください
2. スキーマ変更にテストフィクスチャを追加してください
3. Rust、TypeScript、Pythonのすべてのリファレンス実装を更新してください
4. 既存のコードスタイルに従ってください

---

<div align="center">

### お問い合わせ

ご質問、パートナーシップ、フィードバック

**contact@dthink.ai**

---

**MITライセンス** — [Deep Thinking LLC](https://dthink.ai)

</div>
