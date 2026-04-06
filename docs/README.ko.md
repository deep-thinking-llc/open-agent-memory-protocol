# Open Agent Memory Protocol (OAMP)

[English](../README.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Bahasa Melayu](README.ms.md)

**AI 에이전트와 메모리 백엔드 간에 메모리 데이터를 저장, 교환 및 쿼리하기 위한 표준입니다.**

OAMP는 AI 에이전트가 사용자에 대해 학습한 내용을 기억하고, 프라이버시와 보안을 기본으로 내장하면서 다양한 에이전트 프레임워크와 스토리지 백엔드 간에 이식 가능하게 메모리를 공유할 수 있도록 합니다.

## 왜 OAMP인가?

현재 모든 AI 에이전트 프레임워크는 사용자 메모리를 서로 다른 방식으로 저장합니다. 에이전트를 전환하면 이전 에이전트가 당신에 대해 학습한 모든 것을 잃게 됩니다 — 선호도, 전문 지식, 수정 사항, 워크플로우 패턴. OAMP는 다음을 정의하여 이 문제를 해결합니다:

- **공통 포맷** — 에이전트 메모리용 (JSON Schema + Protobuf)
- **REST API 계약** — 메모리 백엔드용
- **프라이버시 요구사항** — 모든 구현이 충족해야 하는
- **참조 구현** — Rust와 TypeScript로 제공

### 문제점

- 에이전트 A가 당신이 간결한 답변을 선호하고, Rust 전문가이며, 코드 예제에 `unwrap()`을 원하지 않는다는 것을 학습합니다
- 에이전트 B로 전환합니다
- 에이전트 B는 당신에 대해 아무것도 모릅니다 — 처음부터 다시 시작합니다
- 당신의 수정 사항, 선호도, 전문 지식이 에이전트 A의 독점 형식에 갇혀 있습니다

### OAMP의 해결책

- 에이전트 A가 당신의 메모리를 OAMP 문서(표준 JSON)로 내보냅니다
- 에이전트 B가 이를 가져옵니다
- 에이전트 B가 즉시 당신의 선호도, 전문 지식, 수정 사항을 파악합니다
- 벤더 종속 없음. 당신의 메모리는 당신의 것입니다.

## OAMP가 정의하는 것

### 지식 계층
에이전트가 당신에 대해 학습하는 개별 사실:

```json
{
  "type": "knowledge_entry",
  "category": "correction",
  "content": "절대 unwrap()을 사용하지 마세요 — 항상 ? 연산자로 적절한 에러 처리를 하세요",
  "confidence": 0.98,
  "source": { "session_id": "sess-003", "timestamp": "2026-03-12T16:45:00Z" }
}
```

네 가지 카테고리: **fact**(객관적 정보), **preference**(선호하는 방식), **pattern**(주로 하는 행동), **correction**(에이전트에게 하지 말라고 지시한 것).

### 사용자 모델 계층
당신이 누구인지에 대한 더 풍부한 프로필:

```json
{
  "type": "user_model",
  "communication": { "verbosity": -0.6, "formality": 0.2 },
  "expertise": [
    { "domain": "rust", "level": "expert", "confidence": 0.95 },
    { "domain": "react", "level": "novice", "confidence": 0.60 }
  ],
  "corrections": [
    { "what_agent_did": "unwrap()을 사용함", "what_user_wanted": "? 연산자 사용" }
  ]
}
```

### 프라이버시 요구사항 (필수)

OAMP는 프라이버시를 중요하게 생각합니다. 준수하는 구현은 **반드시** 다음을 충족해야 합니다:

- **모든 저장 데이터 암호화** (AES-256-GCM 권장)
- **전체 데이터 내보내기 지원** — 사용자가 자신의 메모리를 소유합니다
- **완전한 삭제 지원** — 소프트 삭제가 아닌 실제 삭제
- **콘텐츠를 절대 로깅하지 않음** — ID와 카테고리만 기록
- **출처 추적** — 모든 항목이 어디서 왔는지 기록

## 저장소 구조

```
open-agent-memory-protocol/
├── spec/v1/                    # 권위 있는 사양
│   ├── oamp-v1.md             # 사람이 읽을 수 있는 사양 (RFC 2119)
│   ├── *.schema.json          # JSON Schema (draft-2020-12)
│   └── examples/              # 유효한 예제 문서
├── proto/oamp/v1/             # Protocol Buffer 정의
├── reference/
│   ├── rust/                  # Rust crate: oamp-types
│   └── typescript/            # npm 패키지: @oamp/types
├── validators/
│   ├── validate.sh            # CLI 검증기
│   └── test-fixtures/         # 유효 및 무효 테스트 문서
└── docs/
    ├── guide-for-agents.md    # 에이전트에 OAMP를 추가하는 방법
    ├── guide-for-backends.md  # OAMP 백엔드를 구축하는 방법
    └── security-guide.md      # 암호화, GDPR, 위협 모델
```

## 빠른 시작

### 문서 검증

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

// 지식 항목 생성
let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "절대 unwrap()을 사용하지 마세요 — 대신 ? 연산자를 사용하세요",
    0.98,
    "session-42",
);

// OAMP JSON으로 직렬화
let json = serde_json::to_string_pretty(&entry)?;

// 검증
oamp_types::validate::validate_knowledge_entry(&entry)?;
```

### TypeScript

```bash
npm install @oamp/types
```

```typescript
import { KnowledgeEntry } from '@oamp/types';

// OAMP 문서 검증 및 파싱
const entry = KnowledgeEntry.parse(jsonData);

// 타입 안전한 접근
console.log(entry.category); // "correction"
console.log(entry.confidence); // 0.98
```

## 에이전트 개발자를 위한 안내

에이전트에 OAMP 지원을 추가하고 싶으신가요? [에이전트 가이드](guide-for-agents.md)를 참조하세요.

요약:
1. **내보내기** — 내부 메모리 타입을 OAMP JSON으로 매핑
2. **가져오기** — OAMP JSON을 내부 타입으로 파싱
3. **검증** — JSON Schema 또는 참조 라이브러리를 사용하여 준수 여부 확인

## 백엔드 개발자를 위한 안내

OAMP 호환 메모리 백엔드를 구축하고 싶으신가요? [백엔드 가이드](guide-for-backends.md)를 참조하세요.

백엔드는 지식 CRUD, 사용자 모델 저장, 대량 내보내기/가져오기를 포함하는 9개의 REST 엔드포인트를 구현해야 합니다.

## 사양

전체 사양은 [spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md)에 있습니다. 준수 수준을 정의하기 위해 RFC 2119 언어(MUST, SHOULD, MAY)를 사용합니다.

### 버전

현재: **v1.0.0**

사양은 시맨틱 버전 관리를 따릅니다. 문서에는 전방 호환성을 위한 `oamp_version` 필드가 포함됩니다.

### 향후 계획 (v2.0)

v2.0 계획 (커뮤니티 피드백 기반):
- 세션 결과 (구조화된 작업 기록)
- 스킬 메트릭 (실행 통계)
- 작업 패턴 (활동 시간, 도구 선호도)
- 실시간 메모리 동기화를 위한 스트리밍 API

## 보안

[보안 가이드](security-guide.md)에서 다음을 확인하세요:
- 권장 암호 스위트
- 키 관리 패턴
- GDPR 제17조 / CCPA 준수 매핑
- 메모리 교환을 위한 위협 모델

## 기여

기여를 환영합니다. 다음을 준수해 주세요:
1. 변경 사항을 제안하기 전에 사양을 읽으세요
2. 모든 Schema 변경에 대해 테스트 픽스처를 추가하세요
3. Rust와 TypeScript 참조 구현을 모두 업데이트하세요
4. 기존 코드 스타일을 따르세요

## 연락처

질문, 파트너십 또는 피드백:

**이메일:** contact@dthink.ai

## 라이선스

Apache 2.0 — [LICENSE](../LICENSE) 참조
