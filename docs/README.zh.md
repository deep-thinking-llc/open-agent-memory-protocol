# Open Agent Memory Protocol (OAMP)

[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [Bahasa Melayu](README.ms.md)

**一种用于在 AI 智能体与记忆后端之间存储、交换和查询记忆数据的开放标准。**

OAMP 使 AI 智能体能够记住它们从用户那里学到的内容——并且可以在不同的智能体框架和存储后端之间可移植地共享这些记忆，同时从底层就内置了隐私和安全保护。

## 为什么需要 OAMP？

如今，每个 AI 智能体框架都以不同的方式存储用户记忆。当你切换智能体时，之前的智能体学到的关于你的一切都会丢失——你的偏好、专业知识、纠正记录、工作流模式。OAMP 通过定义以下内容来解决这个问题：

- **通用格式**——用于智能体记忆（JSON Schema + Protobuf）
- **REST API 契约**——用于记忆后端
- **隐私要求**——每个实现都必须满足
- **参考实现**——提供 Rust 和 TypeScript 版本

### 问题所在

- 智能体 A 学到了你偏好简洁的回答、你是 Rust 专家、你不希望代码示例中出现 `unwrap()`
- 你切换到了智能体 B
- 智能体 B 对你一无所知——你从零开始
- 你的纠正记录、偏好和专业知识被锁定在智能体 A 的专有格式中

### OAMP 的解决方案

- 智能体 A 将你的记忆导出为 OAMP 文档（标准 JSON）
- 智能体 B 导入该文档
- 智能体 B 立即了解你的偏好、专业知识和纠正记录
- 没有供应商锁定。你的记忆属于你自己。

## OAMP 定义了什么

### 知识层
智能体从你身上学到的离散事实：

```json
{
  "type": "knowledge_entry",
  "category": "correction",
  "content": "永远不要使用 unwrap()——始终使用 ? 运算符进行正确的错误处理",
  "confidence": 0.98,
  "source": { "session_id": "sess-003", "timestamp": "2026-03-12T16:45:00Z" }
}
```

四种类别：**fact**（客观信息）、**preference**（你喜欢的方式）、**pattern**（你倾向于做的事情）、**correction**（你告诉智能体不要再做的事情）。

### 用户模型层
关于你是谁的更丰富的画像：

```json
{
  "type": "user_model",
  "communication": { "verbosity": -0.6, "formality": 0.2 },
  "expertise": [
    { "domain": "rust", "level": "expert", "confidence": 0.95 },
    { "domain": "react", "level": "novice", "confidence": 0.60 }
  ],
  "corrections": [
    { "what_agent_did": "使用了 unwrap()", "what_user_wanted": "使用 ? 运算符" }
  ]
}
```

### 隐私要求（强制性）

OAMP 非常重视隐私。合规的实现**必须**：

- **对所有静态数据加密**（推荐 AES-256-GCM）
- **支持完整数据导出**——用户拥有自己的记忆
- **支持完整删除**——真正的删除，而非软删除
- **永远不记录内容**——仅记录 ID 和类别
- **追踪来源**——每条记录都记录其来源

## 仓库结构

```
open-agent-memory-protocol/
├── spec/v1/                    # 权威规范
│   ├── oamp-v1.md             # 人类可读规范（RFC 2119）
│   ├── *.schema.json          # JSON Schema (draft-2020-12)
│   └── examples/              # 有效的示例文档
├── proto/oamp/v1/             # Protocol Buffer 定义
├── reference/
│   ├── rust/                  # Rust crate: oamp-types
│   └── typescript/            # npm 包: @oamp/types
├── validators/
│   ├── validate.sh            # CLI 验证器
│   └── test-fixtures/         # 有效和无效的测试文档
└── docs/
    ├── guide-for-agents.md    # 如何为你的智能体添加 OAMP 支持
    ├── guide-for-backends.md  # 如何构建 OAMP 后端
    └── security-guide.md      # 加密、GDPR、威胁模型
```

## 快速入门

### 验证文档

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

// 创建一条知识条目
let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "永远不要使用 unwrap()——改用 ? 运算符",
    0.98,
    "session-42",
);

// 序列化为 OAMP JSON
let json = serde_json::to_string_pretty(&entry)?;

// 验证
oamp_types::validate::validate_knowledge_entry(&entry)?;
```

### TypeScript

```bash
npm install @oamp/types
```

```typescript
import { KnowledgeEntry } from '@oamp/types';

// 验证并解析 OAMP 文档
const entry = KnowledgeEntry.parse(jsonData);

// 类型安全的访问
console.log(entry.category); // "correction"
console.log(entry.confidence); // 0.98
```

## 面向智能体开发者

想为你的智能体添加 OAMP 支持？请参阅[智能体指南](guide-for-agents.md)。

简而言之：
1. **导出** — 将你的内部记忆类型映射为 OAMP JSON
2. **导入** — 将 OAMP JSON 解析为你的内部类型
3. **验证** — 使用 JSON Schema 或参考库确保合规

## 面向后端开发者

想构建一个符合 OAMP 标准的记忆后端？请参阅[后端指南](guide-for-backends.md)。

你的后端需要实现 9 个 REST 端点，涵盖知识的增删改查、用户模型存储以及批量导出/导入。

## 规范

完整规范位于 [spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md)。它使用 RFC 2119 语言（MUST、SHOULD、MAY）来定义合规级别。

### 版本

当前版本：**v1.0.0**

规范采用语义化版本控制。文档包含 `oamp_version` 字段以实现前向兼容性。

### 未来规划（v2.0）

v2.0 计划（基于社区反馈）：
- 会话成果（结构化任务记录）
- 技能指标（执行统计数据）
- 工作模式（活动时间、工具偏好）
- 用于实时记忆同步的流式 API

## 安全

请参阅[安全指南](security-guide.md)了解：
- 推荐的密码套件
- 密钥管理模式
- GDPR 第 17 条 / CCPA 合规映射
- 记忆交换的威胁模型

## 贡献

我们欢迎贡献。请：
1. 在提出更改之前阅读规范
2. 为任何 Schema 更改添加测试夹具
3. 同时更新 Rust 和 TypeScript 参考实现
4. 遵循现有的代码风格

## 联系方式

如有问题、合作意向或反馈：

**邮箱：** contact@dthink.ai

## 许可证

Apache 2.0 — 参见 [LICENSE](../LICENSE)
