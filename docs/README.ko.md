<div align="center">

# Open Agent Memory Protocol

### AI 에이전트의 메모리는 당신의 것이어야 합니다.

[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](../spec/v1/oamp-v1.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)
[![Rust Crate](https://img.shields.io/badge/crate-oamp--types-orange.svg)](../reference/rust/)
[![npm Package](https://img.shields.io/badge/npm-%40oamp%2Ftypes-red.svg)](../reference/typescript/)
[![PyPI Package](https://img.shields.io/pypi/v/oamp-types.svg)](https://pypi.org/project/oamp-types/)

[사양](../spec/v1/oamp-v1.md) | [Rust Crate](../reference/rust/) | [TypeScript 패키지](../reference/typescript/) | [Python 패키지](../reference/python/) | [보안 가이드](security-guide.md)

---

[English](../README.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Bahasa Melayu](README.ms.md)

</div>

## 문제점

모든 AI 에이전트는 메모리를 다른 방식으로 저장합니다. 에이전트를 전환하면 처음부터 다시 시작해야 합니다.

```
에이전트 A                          에이전트 B
  당신의 선호도를 학습       →     아무것도 모름
  당신의 전문 지식을 추적    →     처음부터 시작
  수정 사항을 기억           →     같은 실수를 반복
  당신의 워크플로우를 이해   →     일반적인 응답
```

당신의 수정 사항, 선호도, 전문 지식이 독점 형식에 갇혀 있습니다. **전환할 때마다 몇 주간의 컨텍스트를 잃게 됩니다.**

## 해결책

OAMP는 에이전트 메모리를 이식 가능하고, 프라이버시를 보장하며, 상호 운용 가능하게 만드는 개방형 표준입니다.

```
에이전트 A                          에이전트 B
  OAMP로 내보내기            →     OAMP 가져오기
  표준 JSON 형식             →     즉시 컨텍스트 확보
  당신의 데이터, 당신의 통제 →     벤더 종속 없음
```

---

## 핵심 내용

<table>
<tr>
<td width="50%">

### 지식 계층

에이전트가 학습하는 개별 사실:

```json
{
  "category": "correction",
  "content": "절대 unwrap()을 사용하지 마세요 — ? 연산자를 사용하세요",
  "confidence": 0.98
}
```

네 가지 유형: **fact** · **preference** · **pattern** · **correction**

</td>
<td width="50%">

### 사용자 모델 계층

당신이 누구인지에 대한 풍부한 프로필:

```json
{
  "expertise": [
    { "domain": "rust", "level": "expert" },
    { "domain": "react", "level": "novice" }
  ],
  "communication": { "verbosity": -0.6 }
}
```

추적 항목: **전문 지식** · **커뮤니케이션 스타일** · **수정 사항** · **선호도**

</td>
</tr>
</table>

---

## 프라이버시 우선

OAMP는 프라이버시를 선택 사항으로 취급하지 않습니다. 이것은 **필수 요구사항**이며 — 가이드라인이 아닙니다:

| 요구사항 | 상세 내용 |
|:---|:---|
| **저장 데이터 암호화** | 모든 저장 데이터는 반드시 암호화되어야 합니다 (AES-256-GCM 권장) |
| **사용자 데이터 소유권** | 전체 내보내기를 반드시 지원해야 합니다 — 사용자가 자신의 메모리를 소유합니다 |
| **삭제 권리** | 소프트 삭제가 아닌 실제 삭제. GDPR 제17조 준수 |
| **콘텐츠 로깅 금지** | 구현은 지식 콘텐츠를 로깅해서는 안 됩니다 |
| **출처 추적** | 모든 항목이 언제 어디서 학습되었는지 기록합니다 |

---

## 빠른 시작

### 검증

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
    content="절대 unwrap()을 사용하지 마세요 — ? 연산자를 사용하세요",
    confidence=0.98,
    source=KnowledgeSource(session_id="session-42"),
)

# 검증
errors = validate_knowledge_entry(entry)

# JSON으로 직렬화 (null 필드 제외)
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

// 검증
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

# 검증
errors = OampTypes.Validate.validate_knowledge_entry(entry)

# JSON 인코딩
json = Entry.to_json(entry)
```

### 참조 서버

```bash
cd reference/server
pip install -e ".[dev]"
python -m oamp_server
```

OpenAPI 문서: `http://localhost:8000/docs` — 지식 CRUD, 사용자 모델, 검색, 대량 내보내기/가져오기를 위한 12개 엔드포인트.

---

```
spec/v1/
  oamp-v1.md              권위 있는 사양 (RFC 2119)
  *.schema.json            JSON Schema 정의 (draft-2020-12)
  examples/                유효한 예제 문서

proto/oamp/v1/             Protocol Buffer 정의

reference/
  rust/                    Rust crate: oamp-types
  typescript/              npm 패키지: @oamp/types
  python/                  PyPI 패키지: oamp-types
  go/                      Go 모듈: oamp-go
  elixir/                  Hex 패키지: oamp_types
  server/                  FastAPI 참조 백엔드

scripts/
  protoc-gen.sh            protobuf 정의에서 코드 생성

validators/
  validate.sh              CLI 문서 검증기
  test-fixtures/            유효 및 무효 테스트 문서

docs/
  guide-for-agents.md      에이전트에 OAMP 구현하기
  guide-for-backends.md    OAMP 호환 백엔드 구축하기
  security-guide.md        암호화, GDPR/CCPA, 위협 모델
```

---

## OAMP 통합

<table>
<tr>
<td width="50%">

### 에이전트 개발자를 위한 안내

에이전트에 메모리 이식성을 추가하세요:

1. **내보내기** — 내부 타입을 OAMP JSON으로 매핑
2. **가져오기** — OAMP JSON을 내부 타입으로 파싱
3. **검증** — 스키마 준수 여부 확인

[에이전트 가이드 읽기 →](guide-for-agents.md)

</td>
<td width="50%">

### 백엔드 개발자를 위한 안내

OAMP 호환 메모리 저장소를 구축하세요:

- 9개의 REST 엔드포인트 (지식 CRUD, 사용자 모델, 내보내기/가져오기)
- 저장 시 암호화 (필수)
- 검색 (FTS, 벡터, 또는 하이브리드 — 선택 가능)

[백엔드 가이드 읽기 →](guide-for-backends.md)

</td>
</tr>
</table>

---

## 사양

| | |
|:---|:---|
| **현재 버전** | v1.0.0 |
| **스키마 형식** | JSON Schema (draft-2020-12) + Protocol Buffers |
| **준수 언어** | RFC 2119 (MUST, SHOULD, MAY) |
| **전체 사양** | [spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md) |

### v2.0 계획

커뮤니티 피드백을 기반으로:
- 세션 결과 (구조화된 작업 기록)
- 스킬 메트릭 (실행 통계)
- 작업 패턴 (활동 시간, 도구 선호도)
- 실시간 메모리 동기화를 위한 스트리밍 API

---

## 기여

기여를 환영합니다:

1. 변경 사항을 제안하기 전에 [사양](../spec/v1/oamp-v1.md)을 읽으세요
2. 스키마 변경에 대한 테스트 픽스처를 추가하세요
3. 모든 참조 구현 (Rust, TypeScript, Python, Go, Elixir)을 업데이트하세요
4. 기존 코드 스타일을 따르세요

---

<div align="center">

### 연락처

질문, 파트너십 또는 피드백

**contact@dthink.ai**

---

**MIT 라이선스** — [Deep Thinking LLC](https://dthink.ai)

</div>