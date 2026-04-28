# 开放代理内存协议 -- 版本 1.0.0

**状态：** 草案  
**日期：** 2026-04-06  
**作者：** Deep Thinking LLC  
**仓库：** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## 摘要

开放代理内存协议 (OAMP) 定义了一个标准格式，用于在 AI 代理和内存后端之间存储、交换和查询内存数据。它实现了可移植性（用户可以从一个代理导出内存并导入到另一个代理中）、后端互操作性（任何符合 OAMP 的后端都可以与任何符合 OAMP 的代理一起工作）和默认隐私（静态加密、用户数据所有权和来源追踪是强制性的）。

文档中的关键字 "MUST"、"MUST NOT"、"REQUIRED"、"SHALL"、"SHALL NOT"、"SHOULD"、"SHOULD NOT"、"RECOMMENDED"、"MAY" 和 "OPTIONAL" 应按照 [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) 中的描述进行解释。

---

## 1. 引言与动机

AI 代理越来越多地维护关于用户的持久内存：他们的偏好、专业知识、纠正和行为模式。如果没有一个共同的交换格式，这些内存就会被锁定在单个代理或后端中，造成供应商锁定，并阻止用户拥有自己的数据。

OAMP 通过定义以下内容来解决这个问题：

- **JSON Schema** 用于代理内存文档的结构
- **REST API 合同** 用于内存后端
- **隐私要求** 合规实现必须满足
- **参考实现** 使用 Rust 和 TypeScript

### 1.1 OAMP 是什么

- 定义代理内存文档结构的 JSON schema
- 用于内存后端的 REST API 合同
- 使用 Rust 和 TypeScript 的参考实现
- 合规实现必须满足的隐私和安全要求

### 1.2 OAMP 不是

- 数据库或存储引擎
- 代理框架
- 特定的 AI 模型或嵌入格式
- 传输协议（OAMP 使用 HTTP/JSON，支持可选的 protobuf）

### 1.3 设计原则

- **优先考虑可移植性。** 从一个代理导出的内存 MUST 能够被任何其他合规代理导入，而无需转换。
- **默认隐私。** 加密和来源追踪不是可选附加项；它们是规范要求。
- **优先考虑采用而非完整性。** JSON 优于 protobuf 作为主要格式。可选字段优于强制复杂性。对搜索的规范应低于以允许后端选择。
- **双向协议。** OAMP 同时服务于代理框架（生产者/消费者）和内存后端（存储/检索）。双方都有规范要求。

---

## 2. 术语

- **代理** -- 与用户交互并维护关于他们的内存的软件系统。
- **后端** -- 持久化 OAMP 文档并暴露第 6 节定义的 REST API 的存储服务。
- **知识条目** -- 代理关于用户学习到的离散信息，表示为 `type: "knowledge_entry"` 的 OAMP 文档。
- **知识库** -- 为批量导出或导入打包的知识条目集合，表示为 `type: "knowledge_store"` 的 OAMP 文档。
- **用户模型** -- 代理对用户不断演变的结构化理解，表示为 `type: "user_model"` 的 OAMP 文档。
- **置信度** -- 在 [0.0, 1.0] 范围内的浮点数，表示代理对一条知识的确定性。0.0 表示没有信心；1.0 表示确定。
- **来源** -- 记录知识获取的时间和方式（会话、代理、时间戳）。
- **衰减** -- 随着时间推移，知识变得陈旧而导致的置信度降低。

---

## 3. 知识条目

知识条目表示代理关于用户学习到的离散信息。

### 3.1 文档结构

```json
{
  "oamp_version": "1.0.0",
  "type": "knowledge_entry",
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "user-123",
  "category": "preference",
  "content": "用户更喜欢使用 Rust 而不是 Python 进行系统编程",
  "confidence": 0.85,
  "source": {
    "session_id": "sess-2026-04-01-001",
    "agent_id": "my-agent-v1",
    "timestamp": "2026-04-01T14:30:00Z"
  },
  "decay": {
    "half_life_days": 70.0,
    "last_confirmed": "2026-04-01T14:30:00Z"
  },
  "tags": ["language", "preference"],
  "metadata": {}
}
```

### 3.2 字段定义

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | 规范版本，采用语义版本控制。对于此版本：`"1.0.0"`。 |
| `type` | string | MUST | MUST 为 `"knowledge_entry"`。 |
| `id` | string | MUST | UUID v4 唯一标识符。MUST 全局唯一。 |
| `user_id` | string | MUST | 此知识所属用户的标识符。 |
| `category` | string | MUST | 取值之一：`"fact"`、`"preference"`、`"pattern"`、`"correction"`。见 3.4。 |
| `content` | string | MUST | 知识本身的自然语言描述。MUST NOT 为空。 |
| `confidence` | number | MUST | 在 [0.0, 1.0] 范围内的浮点数。见 3.5。 |
| `source` | object | MUST | 来源信息。见 3.3。 |
| `decay` | object | MAY | 时间衰减参数。见 3.6。 |
| `tags` | array of string | MAY | 用于过滤和分组的自由格式标签。 |
| `metadata` | object | MAY | 供应商特定扩展。合规实现 MUST NOT 拒绝具有未知元数据字段的文档。 |

### 3.3 来源对象

`source` 对象记录知识条目的来源。实现 MUST NOT 在没有 `source` 的情况下创建知识条目。

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `session_id` | string | MUST | 学习此知识的会话标识符。 |
| `timestamp` | string | MUST | 学习此知识的 ISO 8601 日期时间。 |
| `agent_id` | string | MAY | 生成此知识的代理标识符。 |

### 3.4 类别定义

`category` 字段对知识的种类进行分类。合规实现 MUST 使用四个定义值之一，并且 MUST NOT 在 v1.0 中定义其他类别（使用 `tags` 或 `metadata` 进行供应商扩展）。

- **`fact`** -- 关于用户环境或上下文的客观信息。事实不是评估性的。示例：“用户在 Acme Corp 工作”，“项目使用 PostgreSQL 15”，“用户位于柏林”。

- **`preference`** -- 用户对代理应如何行为或响应的明确或推断的偏好。示例：“更喜欢简洁的回答”，“喜欢黑暗模式”，“更喜欢 Rust 而不是 Python”。

- **`pattern`** -- 代理观察到的重复行为模式。模式是从多个观察中推断的，而不是单一事件。示例：“在生产之前部署到暂存环境”，“早上审核 PR”，“在合并之前请求代码审查”。

- **`correction`** -- 用户纠正了代理的行为。此类别是第一类数据，而不是副作用。纠正是主要学习信号。示例：“不要使用 `unwrap()`，使用适当的错误处理”，“不要重复我已经提供的上下文”。

### 3.5 置信度

`confidence` 字段是一个在 [0.0, 1.0] 范围内的浮点数：

- `0.0` -- 没有信心；这条知识可能是错误的
- `0.5` -- 不确定；正确或错误的概率大致相等
- `1.0` -- 确定；代理有强有力的证据表明这是正确的

代理 SHOULD 根据证据校准置信度分数。用户提供的陈述事实 SHOULD 具有比推断模式更高的初始置信度。

来自用户的纠正 SHOULD 被赋予置信度 >= 0.9，因为它们代表明确的用户意图。

### 3.6 置信度衰减

知识随着时间的推移而变得陈旧。实现 SHOULD 应用时间衰减：

```
confidence_t = confidence_0 * e^(-ln(2) / half_life_days * age_days)
```

其中：
- `confidence_0` 是最后确认时的置信度
- `half_life_days` 是 `decay.half_life_days`
- `age_days` 是自 `decay.last_confirmed` 以来的天数
  （如果 `last_confirmed` 缺失，则为 `source.timestamp`）

如果 `decay` 缺失或 `half_life_days` 为 `null`，则不应用衰减。

按类别推荐的默认半衰期：
- `fact`：365 天（事实变化不频繁）
- `preference`：70 天（偏好会演变）
- `pattern`：90 天（模式可能会随着角色/上下文变化而变化）
- `correction`：无衰减（纠正是持久的，除非被取代）

---

## 4. 知识库

知识库是一个用于批量导出和导入的集合文档。它允许在代理或后端之间移动完整的内存快照。

### 4.1 文档结构

```json
{
  "oamp_version": "1.0.0",
  "type": "knowledge_store",
  "user_id": "user-123",
  "entries": [...],
  "exported_at": "2026-04-06T10:00:00Z",
  "agent_id": "my-agent-v1"
}
```

### 4.2 字段定义

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | 规范版本。 |
| `type` | string | MUST | MUST 为 `"knowledge_store"`。 |
| `user_id` | string | MUST | 所有条目所属的用户。 |
| `entries` | array | MUST | 知识条目对象的数组。MAY 为空。 |
| `exported_at` | string | MUST | 导出的 ISO 8601 时间戳。 |
| `agent_id` | string | MAY | 导出代理标识符。 |

### 4.3 条目继承

`entries` 中的每个条目 MUST 是有效的知识条目对象。知识库中的条目 MAY 省略 `oamp_version`（它们从知识库继承）；但是，合规的导入者 MUST 接受具有或不具有 `oamp_version` 的条目。

### 4.4 合并语义

将知识库导入现有后端时：

- ID 不存在的条目 MUST 被插入。
- ID 已存在的条目：规范 RECOMMENDS 基于置信度的解决方案（更高的置信度优先）。实现 MAY 定义其他合并策略，但 MUST 记录它们。
- 实现 MUST NOT 默默丢弃条目；任何被拒绝的条目 SHOULD 在导入响应中报告。

---

## 5. 用户模型

用户模型表示代理对用户不断演变的结构化理解。信封之外的所有部分都是独立可选的 -- 仅跟踪专业知识的代理 MAY 省略通信和纠正。

### 5.1 信封字段

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | 规范版本。 |
| `type` | string | MUST | MUST 为 `"user_model"`。 |
| `user_id` | string | MUST | 用户标识符。 |
| `model_version` | integer | MUST | 单调递增的版本号。MUST >= 1。 |
| `updated_at` | string | MUST | 最后更新的 ISO 8601 时间戳。 |
| `metadata` | object | MAY | 供应商特定扩展。 |

在存储用户模型时，后端 MUST 拒绝 `model_version` 小于或等于存储版本的更新（乐观并发控制）。

### 5.2 通信部分

`communication` 对象建模用户偏好的与代理交互的方式。尺度是连续的，而不是分类的，以允许细粒度建模。

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `verbosity` | number | MAY | -1.0（简洁）到 1.0（冗长）。0.0 = 默认。 |
| `formality` | number | MAY | -1.0（随意）到 1.0（正式）。0.0 = 默认。 |
| `prefers_examples` | boolean | MAY | 用户更喜欢代码或实例。 |
| `prefers_explanations` | boolean | MAY | 用户更喜欢推理的解释。 |
| `languages` | array of string | MAY | ISO 639-1 语言代码（例如，`["en", "de"]`）。 |

### 5.3 专业知识部分

`expertise` 数组建模用户在各个领域的表现知识。每个条目代表一个单一领域。

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `domain` | string | MUST | 专业知识领域名称（例如，`"rust"`、`"kubernetes"`）。 |
| `level` | string | MUST | 取值之一：`"novice"`、`"intermediate"`、`"advanced"`、`"expert"`。 |
| `confidence` | number | MUST | 代理对该评估的置信度，0.0-1.0。 |
| `evidence_sessions` | array of string | MAY | 观察到该专业知识的会话 ID。 |
| `last_observed` | string | MAY | 最近观察的 ISO 8601 日期时间。 |

### 5.4 纠正部分

`corrections` 数组是用户纠正代理的实例的第一类记录。这是主要学习信号，应该被永久保存。

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `what_agent_did` | string | MUST | 代理做错了什么。 |
| `what_user_wanted` | string | MUST | 用户想要的是什么。 |
| `context` | string | MAY | 此纠正适用的情况（例如，“仅适用于架构讨论”）。 |
| `session_id` | string | MUST | 发生纠正的会话。 |
| `timestamp` | string | MUST | ISO 8601 日期时间。 |

### 5.5 陈述偏好部分

`stated_preferences` 数组记录用户明确声明的偏好。这些比推断知识更具权重，因为用户主动声明了它们。

| 字段 | 类型 | 要求 | 描述 |
|-------|------|-------------|-------------|
| `key` | string | MUST | 偏好键（例如，`"code_style"`、`"response_length"`）。 |
| `value` | string | MUST | 偏好值。 |
| `timestamp` | string | MUST | 陈述的 ISO 8601 日期时间。 |

---

## 6. 后端 REST API

### 6.1 基础 URL

所有端点都在 `/v1/` 下。后端 MAY 在任何基础 URL 上托管，但 MUST 保留 `/v1/` 路径前缀以允许未来版本控制。

### 6.2 知识端点

```
POST   /v1/knowledge             -- 存储一个 KnowledgeEntry
GET    /v1/knowledge?query=      -- 搜索知识（文本查询）
GET    /v1/knowledge/:id         -- 按 ID 检索
DELETE /v1/knowledge/:id         -- 删除
PATCH  /v1/knowledge/:id         -- 更新置信度，确认
```

**POST /v1/knowledge**

请求体：一个有效的 KnowledgeEntry 文档。  
成功响应：`201 Created`，包含存储的文档（包括任何后端分配的字段）。  
验证失败时：`400 Bad Request`，带有 JSON 错误体。

**GET /v1/knowledge/:id**

成功响应：`200 OK`，包含 KnowledgeEntry 文档。  
如果未找到：`404 Not Found`。  
后端 MUST 验证经过身份验证的用户是否拥有此条目。如果请求用户不拥有该条目，后端 MUST 返回 `403 Forbidden`。建议使用可选的 `?user_id=` 查询参数进行深度防御授权验证。

**DELETE /v1/knowledge/:id**

成功响应：`204 No Content`。  
后端 MUST 永久删除该条目（不进行软删除）。  
加密列在删除之前 SHOULD 被清零（见 §8.2.7）。  
后端 MUST 验证经过身份验证的用户是否拥有此条目。

**PATCH /v1/knowledge/:id**

允许部分更新 `confidence`、`decay.last_confirmed` 和 `tags`。  
实现 MUST NOT 允许修补 `id`、`user_id`、`category` 或 `source`。  
后端 MUST 验证经过身份验证的用户是否拥有此条目。

**GET /v1/knowledge?query=**

见第 6.6 节（搜索）。

### 6.3 用户模型端点

```
POST   /v1/user-model            -- 存储/更新一个 UserModel
GET    /v1/user-model/:user_id   -- 检索
DELETE /v1/user-model/:user_id   -- 删除（完全重置）
```

**POST /v1/user-model**

请求体：一个有效的 UserModel 文档。  
成功响应：`200 OK`（更新）或 `201 Created`（新）。  
后端 MUST 强制执行 `model_version` 的单调性（如果新版本 <= 存储版本，则拒绝，返回 `409 Conflict`）。

**DELETE /v1/user-model/:user_id**

MUST 删除该用户的完整用户模型和所有相关知识条目。MUST NOT 可逆（无软删除）。成功响应：`204 No Content`。

### 6.4 批量端点

```
POST   /v1/export                -- 将所有用户数据导出为 OAMP 文档
POST   /v1/import                -- 导入一个 OAMP 文档
```

**POST /v1/export**

请求体：`{ "user_id": "string" }`。  
响应：一个包含该用户所有条目的 KnowledgeStore 文档，以及 `metadata` 字段中的用户模型（如果存在）。

**POST /v1/import**

请求体：一个 KnowledgeStore 文档。  
响应：`200 OK`，包含导入、跳过和拒绝条目的摘要。

### 6.5 内容协商

后端 MUST 支持 `application/json`。对其他格式的支持是 OPTIONAL。

| Accept Header | Response Format |
|--------------|----------------|
| `application/json` (默认) | 按 schema 返回 JSON |
| `application/protobuf` | Protobuf 二进制（OPTIONAL） |
| `application/json+oamp` | 带有 OAMP 信封元数据的 JSON（OPTIONAL） |

### 6.6 搜索

`GET /v1/knowledge?query=` 端点接受文本查询参数。

- 规范不强制要求特定的搜索实现（FTS、向量、混合）。后端选择其实现。
- 结果 MUST 按相关性排名（后端定义）。
- 结果 MUST 作为 KnowledgeEntry 对象的 JSON 数组返回。
- 列表端点 SHOULD 支持 `?limit=` 和 `?offset=` 参数，或基于游标的分页。规范不强制要求特定的分页样式。
- 后端 SHOULD 支持 `?user_id=` 以将结果范围限制为单个用户。

### 6.7 身份验证

规范不定义特定的身份验证机制。身份验证是特定于部署的。安全指南 RECOMMENDS 使用 mTLS 或 Bearer 令牌。后端 MUST 记录其身份验证要求。

无论身份验证机制如何，后端 MUST 强制执行用户级授权：每个返回或修改知识数据的 API 端点 MUST 限定为经过身份验证的用户。跨用户访问 MUST 被拒绝，并返回 `403 Forbidden`。

### 6.8 错误响应

所有错误响应 MUST 是 JSON 对象，至少包含：

```json
{
  "error": "描述错误的字符串",
  "code": "机器可读的错误代码"
}
```

推荐的错误代码：

| 代码 | HTTP 状态 | 何时 |
|------|-----------|------|
| `NOT_FOUND` | 404 | 资源不存在 |
| `VERSION_CONFLICT` | 409 | model_version 未单调递增 |
| `VALIDATION_ERROR` | 400 | 字段验证失败 |
| `DUPLICATE_ID` | 409 | 已存在相同 ID 的条目 |
| `UNAUTHORIZED` | 401 | 需要身份验证 |
| `FORBIDDEN` | 403 | 用户不拥有此资源 |
| `RATE_LIMITED` | 429 | 请求过多 |

---

## 7. 内容协商

当代理发送带有 `Accept: application/protobuf` 的请求时，后端 MAY 以 protobuf 编码的二进制消息响应。protobuf 定义在 OAMP 仓库的 `proto/oamp/v1/` 中提供。protobuf 和 JSON 表示 MUST 在语义上等效。

如果后端不支持 protobuf，则 MUST 响应 `406 Not Acceptable`，而不是返回具有错误 Content-Type 的 JSON。

---

## 8. 隐私和安全要求

### 8.1 MUST 要求（规范性）

违反这些要求的实现 MUST NOT 声称符合 OAMP。

1. **静态加密。** 所有存储的知识和用户模型数据 MUST 在静态时加密。推荐使用 AES-256-GCM。静态存储明文是合规性违规。

2. **用户数据所有权。** `/v1/export` 端点 MUST 返回用户的所有数据而不遗漏。DELETE 端点 MUST 永久删除所有用户数据。软删除（标记为删除同时保留数据）不符合规范。

3. **日志中无内容。** 实现 MUST NOT 记录知识内容、用户模型字段值或纠正文本。记录条目 ID、类别、时间戳和元数据键是允许的。

4. **来源追踪。** 每个 KnowledgeEntry MUST 有一个包含 `session_id` 和 `timestamp` 的 `source` 对象。代理 MUST NOT 创建匿名知识条目（没有来源的条目）。

### 8.2 SHOULD 要求（推荐）

5. **置信度衰减。** 实现 SHOULD 根据第 3.6 节中的公式对置信度分数应用时间衰减。

6. **审计日志。** 对用户数据的操作 SHOULD 进行审计日志记录，记录谁在何时访问了什么。审计日志 MUST NOT 包含知识内容（见要求 3）。

7. **安全删除。** 删除操作 SHOULD 在释放之前清零包含知识内容的内存缓冲区。

### 8.3 附加指导（非规范性）

`docs/security-guide.md` 提供：

- 推荐的密码套件和密钥大小
- 密钥管理模式（每用户密钥、密钥轮换）
- GDPR 第 17 条（删除权）合规映射
- CCPA 合规考虑
- 威胁模型：导出文件拦截、导入中毒、会话重放

---

## 9. 代理接口

生成或消费 OAMP 文档的代理 MUST 实现：

- **导出** -- 将内部内存序列化为有效的 OAMP 文档。所有导出的文档 MUST 通过 `spec/v1/` 中的 JSON Schema 验证。

- **导入** -- 将 OAMP 文档反序列化为内部格式。代理 MUST 接受符合 JSON Schema 的有效文档，并且 MUST NOT 因未知的 `metadata` 字段而拒绝有效文档。

- **合并** -- 在导入与现有知识重叠的知识时处理冲突。规范 RECOMMENDS 基于置信度的解决方案（更高的置信度优先）。代理 MAY 实现其他策略，但 MUST 记录它们。

---

## 10. 版本控制政策

### 10.1 版本字段

`oamp_version` 字段使用语义版本控制（semver）。当前版本为 `"1.0.0"`。

### 10.2 兼容性规则

- 实现 MUST 拒绝具有不支持的主要版本的文档（例如，v1.0 实现接收 `"2.0.0"` 文档时 MUST 拒绝，并给出明确错误）。
- 实现 SHOULD 接受具有更高次要版本的文档，忽略未知的可选字段（向前兼容）。
- 实现 MUST 接受同一次要版本内的任何补丁版本的文档。

### 10.3 字段演变

- 新的 REQUIRED 字段 MAY 仅在主要版本中添加。
- 新的 OPTIONAL 字段 MAY 在次要版本中添加。
- 字段 MAY NOT 在次要或补丁版本中删除。

---

## 11. 未来考虑（v2.0 范围）

以下内容故意从 v1.0 中排除，因为它们过于特定于实现或需要更多社区输入。它们 MAY 在 v2.0 中添加或通过 v1.0 中的 `metadata` 字段进行探索：

- **工作模式** -- 活动时间、常见任务类型、工具偏好。v1.0 代理 MAY 将这些存储在 `metadata` 中。

- **活动时间** -- 每日和每周的行为模式。与调度感知代理相关。

- **会话结果** -- 每个会话中完成的结构化记录。对管理长期项目的代理有用。

- **技能指标** -- 可重用技能或工作流的执行统计。没有更广泛的社区输入，这太特定于实现。

对这些领域的社区反馈应指向 OAMP GitHub 仓库的讨论板。

---

## 附录 A：合规检查表

### 代理合规

- [ ] 导出生成有效的 OAMP 文档（经过 JSON Schema 验证）
- [ ] 所有导出的 KnowledgeEntries 具有 `source.session_id` 和 `source.timestamp`
- [ ] 导入接受所有有效的 OAMP 文档（包括未知的 `metadata`）
- [ ] 合并策略已记录
- [ ] 没有记录知识内容

### 后端合规

- [ ] 实现所有十个 REST 端点
- [ ] 数据在静态时加密
- [ ] `/v1/export` 返回所有用户数据
- [ ] DELETE 端点执行永久删除
- [ ] 强制执行 `model_version` 的单调性
- [ ] 日志中没有知识内容
- [ ] 所有端点都强制执行用户级授权
- [ ] 错误响应遵循第 6.8 节格式

---

## 附录 B：JSON Schema 位置

| 文档类型 | Schema |
|--------------|--------|
| KnowledgeEntry | `spec/v1/knowledge-entry.schema.json` |
| KnowledgeStore | `spec/v1/knowledge-store.schema.json` |
| UserModel | `spec/v1/user-model.schema.json` |

所有模式使用 JSON Schema draft-2020-12。