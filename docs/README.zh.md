<div align="center">

# Open Agent Memory Protocol

### 你的 AI 智能体的记忆，应该属于你自己。

[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](../spec/v1/oamp-v1.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)
[![Rust Crate](https://img.shields.io/badge/crate-oamp--types-orange.svg)](../reference/rust/)
[![npm Package](https://img.shields.io/badge/npm-%40oamp%2Ftypes-red.svg)](../reference/typescript/)
[![PyPI Package](https://img.shields.io/pypi/v/oamp-types.svg)](https://pypi.org/project/oamp-types/)

[规范](../spec/v1/oamp-v1.md) | [Rust Crate](../reference/rust/) | [TypeScript 包](../reference/typescript/) | [Python 包](../reference/python/) | [安全指南](security-guide.md)

---

[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Bahasa Melayu](README.ms.md)

</div>

## 问题所在

每个 AI 智能体都以不同的方式存储记忆。当你切换智能体时，一切从零开始。

```
智能体 A                          智能体 B
  学习你的偏好               →     一无所知
  追踪你的专业知识           →     从头开始
  记住你的纠正               →     重复同样的错误
  理解你的工作流程           →     通用回答
```

你的纠正记录、偏好和专业知识被锁定在专有格式中。**每次切换，你都会失去数周的上下文。**

## 解决方案

OAMP 是一个开放标准，让智能体的记忆可移植、隐私安全且可互操作。

```
智能体 A                          智能体 B
  导出为 OAMP               →     导入 OAMP
  标准 JSON 格式             →     即时上下文
  你的数据，你做主           →     没有供应商锁定
```

---

## 核心内容

<table>
<tr>
<td width="50%">

### 知识层

智能体学到的离散事实：

```json
{
  "category": "correction",
  "content": "永远不要使用 unwrap()——使用 ? 运算符",
  "confidence": 0.98
}
```

四种类型：**fact** · **preference** · **pattern** · **correction**

</td>
<td width="50%">

### 用户模型层

关于你是谁的丰富画像：

```json
{
  "expertise": [
    { "domain": "rust", "level": "expert" },
    { "domain": "react", "level": "novice" }
  ],
  "communication": { "verbosity": -0.6 }
}
```

追踪：**专业知识** · **沟通风格** · **纠正记录** · **偏好**

</td>
</tr>
</table>

---

## 隐私优先

OAMP 不将隐私视为可选项。以下是**强制性要求**——而非指南：

| 要求 | 详情 |
|:---|:---|
| **静态数据加密** | 所有存储数据必须加密（推荐 AES-256-GCM） |
| **用户数据所有权** | 必须支持完整导出——用户拥有自己的记忆 |
| **删除权** | 真正的删除，而非软删除。符合 GDPR 第 17 条 |
| **禁止内容日志** | 实现不得记录知识内容 |
| **来源追踪** | 每条记录都记录其学习的时间和来源 |

---

## 快速入门

### 验证

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
    content="永远不要使用 unwrap()——使用 ? 运算符",
    confidence=0.98,
    source=KnowledgeSource(session_id="session-42"),
)

# 验证
errors = validate_knowledge_entry(entry)

# 序列化为 JSON（排除空值字段）
json_str = entry.model_dump_json(exclude_none=True)
```

### Go

```bash
go get github.com/deep-thinking-llc/oamp-go
```

```go
import oamp "github.com/deep-thinking-llc/oamp-go"

entry := oamp.NewKnowledgeEntry(
    "user-123",
    oamp.KnowledgeCategoryCorrection,
    "Never use unwrap() — use ? operator instead",
    0.98,
    "session-42",
)

// 验证
errors := oamp.ValidateKnowledgeEntry(entry)
```

### Elixir

```elixir
def deps do
  [{:oamp_types, "~> 1.0.0"}]
end
```

```elixir
alias OampTypes.Knowledge.Entry

entry = Entry.new(
  "user-123",
  :correction,
  "Never use unwrap() — use ? operator instead",
  0.98,
  "session-42"
)

# 验证
errors = OampTypes.Validate.validate_knowledge_entry(entry)

# JSON 编码
json = Entry.to_json(entry)
```

### 参考服务器

```bash
cd reference/server
pip install -e ".[dev]"
python -m oamp_server
```

OpenAPI 文档位于 `http://localhost:8000/docs` — 12 个端点，用于知识 CRUD、用户模型、搜索和批量导出/导入。

---

```
spec/v1/
  oamp-v1.md              权威规范（RFC 2119）
  *.schema.json            JSON Schema 定义（draft-2020-12）
  examples/                有效的示例文档

proto/oamp/v1/             Protocol Buffer 定义

reference/
  rust/                    Rust crate: oamp-types
  typescript/              npm 包: @oamp/types
  python/                  PyPI 包: oamp-types
  go/                      Go 模块: oamp-go
  elixir/                  Hex 包: oamp_types
  server/                  FastAPI 参考后端

scripts/
  protoc-gen.sh            从 protobuf 定义生成代码

validators/
  validate.sh              CLI 文档验证器
  test-fixtures/            有效和无效的测试文档

docs/
  guide-for-agents.md      为你的智能体实现 OAMP
  guide-for-backends.md    构建符合 OAMP 标准的后端
  security-guide.md        加密、GDPR/CCPA、威胁模型
```

---

## 集成 OAMP

<table>
<tr>
<td width="50%">

### 面向智能体开发者

为你的智能体添加记忆可移植性：

1. **导出** — 将内部类型映射为 OAMP JSON
2. **导入** — 将 OAMP JSON 解析为内部类型
3. **验证** — 确保符合 Schema

[阅读智能体指南 →](guide-for-agents.md)

</td>
<td width="50%">

### 面向后端开发者

构建符合 OAMP 标准的记忆存储：

- 9 个 REST 端点（知识增删改查、用户模型、导出/导入）
- 静态加密（强制性）
- 搜索（全文搜索、向量搜索或混合搜索——由你选择）

[阅读后端指南 →](guide-for-backends.md)

</td>
</tr>
</table>

---

## 规范

| | |
|:---|:---|
| **当前版本** | v1.0.0 |
| **Schema 格式** | JSON Schema (draft-2020-12) + Protocol Buffers |
| **合规语言** | RFC 2119 (MUST, SHOULD, MAY) |
| **完整规范** | [spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md) |

### v2.0 计划

基于社区反馈：
- 会话成果（结构化任务记录）
- 技能指标（执行统计数据）
- 工作模式（活动时间、工具偏好）
- 用于实时记忆同步的流式 API

---

## 贡献

我们欢迎贡献：

1. 在提出更改之前阅读[规范](../spec/v1/oamp-v1.md)
2. 为 Schema 更改添加测试夹具
3. 更新所有参考实现（Rust、TypeScript、Python、Go、Elixir）
4. 遵循现有的代码风格

---

<div align="center">

### 联系方式

如有问题、合作意向或反馈

**contact@dthink.ai**

---

**MIT 许可证** — [Deep Thinking](https://dthink.ai)

</div>