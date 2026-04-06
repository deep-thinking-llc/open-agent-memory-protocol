# Open Agent Memory Protocol (OAMP)

[English](../README.md) | [中文](README.zh.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

**Satu standard untuk menyimpan, bertukar, dan membuat pertanyaan data memori antara ejen AI dan backend memori.**

OAMP membolehkan ejen AI mengingat apa yang mereka pelajari tentang pengguna — dan berkongsi memori tersebut secara mudah alih merentasi pelbagai rangka kerja ejen dan backend storan, dengan privasi dan keselamatan yang terbina dari asas.

## Mengapa OAMP?

Pada hari ini, setiap rangka kerja ejen AI menyimpan memori pengguna dengan cara yang berbeza. Apabila anda bertukar ejen, anda kehilangan semua yang dipelajari oleh ejen sebelumnya tentang anda — keutamaan anda, kepakaran, pembetulan, corak aliran kerja. OAMP menyelesaikan masalah ini dengan mentakrifkan:

- **Format bersama** — untuk memori ejen (JSON Schema + Protobuf)
- **Kontrak REST API** — untuk backend memori
- **Keperluan privasi** — yang mesti dipenuhi oleh setiap pelaksanaan
- **Pelaksanaan rujukan** — dalam Rust dan TypeScript

### Masalahnya

- Ejen A mempelajari bahawa anda lebih suka jawapan ringkas, anda pakar dalam Rust, dan anda tidak mahu `unwrap()` dalam contoh kod
- Anda bertukar kepada Ejen B
- Ejen B tidak tahu apa-apa tentang anda — anda bermula dari sifar
- Pembetulan, keutamaan, dan kepakaran anda terkunci dalam format proprietari Ejen A

### Penyelesaian OAMP

- Ejen A mengeksport memori anda sebagai dokumen OAMP (JSON standard)
- Ejen B mengimportnya
- Ejen B serta-merta mengetahui keutamaan, kepakaran, dan pembetulan anda
- Tiada penguncian vendor. Memori anda adalah milik anda.

## Apa yang Ditakrifkan oleh OAMP

### Lapisan Pengetahuan
Fakta diskret yang dipelajari ejen tentang anda:

```json
{
  "type": "knowledge_entry",
  "category": "correction",
  "content": "Jangan sekali-kali gunakan unwrap() — sentiasa gunakan pengendalian ralat yang betul dengan operator ?",
  "confidence": 0.98,
  "source": { "session_id": "sess-003", "timestamp": "2026-03-12T16:45:00Z" }
}
```

Empat kategori: **fact** (maklumat objektif), **preference** (cara anda suka sesuatu dilakukan), **pattern** (apa yang anda cenderung lakukan), **correction** (apa yang anda beritahu ejen supaya berhenti lakukan).

### Lapisan Model Pengguna
Profil yang lebih kaya tentang siapa anda:

```json
{
  "type": "user_model",
  "communication": { "verbosity": -0.6, "formality": 0.2 },
  "expertise": [
    { "domain": "rust", "level": "expert", "confidence": 0.95 },
    { "domain": "react", "level": "novice", "confidence": 0.60 }
  ],
  "corrections": [
    { "what_agent_did": "Menggunakan unwrap()", "what_user_wanted": "Gunakan operator ?" }
  ]
}
```

### Keperluan Privasi (Wajib)

OAMP mengambil privasi dengan serius. Pelaksanaan yang patuh **MESTI**:

- **Menyulitkan semua data dalam simpanan** (AES-256-GCM disyorkan)
- **Menyokong eksport data penuh** — pengguna memiliki memori mereka
- **Menyokong pemadaman penuh** — pemadaman sebenar, bukan pemadaman lembut
- **Tidak sekali-kali merekod kandungan** — hanya ID dan kategori
- **Menjejak asal usul** — setiap entri merekodkan dari mana ia datang

## Struktur Repositori

```
open-agent-memory-protocol/
├── spec/v1/                    # Spesifikasi berautoriti
│   ├── oamp-v1.md             # Spesifikasi yang boleh dibaca manusia (RFC 2119)
│   ├── *.schema.json          # JSON Schema (draft-2020-12)
│   └── examples/              # Dokumen contoh yang sah
├── proto/oamp/v1/             # Definisi Protocol Buffer
├── reference/
│   ├── rust/                  # Rust crate: oamp-types
│   └── typescript/            # Pakej npm: @oamp/types
├── validators/
│   ├── validate.sh            # Pengesah CLI
│   └── test-fixtures/         # Dokumen ujian sah dan tidak sah
└── docs/
    ├── guide-for-agents.md    # Cara menambah OAMP kepada ejen anda
    ├── guide-for-backends.md  # Cara membina backend OAMP
    └── security-guide.md      # Penyulitan, GDPR, model ancaman
```

## Mula Pantas

### Sahkan dokumen

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

// Cipta entri pengetahuan
let entry = KnowledgeEntry::new(
    "user-123",
    KnowledgeCategory::Correction,
    "Jangan sekali-kali gunakan unwrap() — gunakan operator ? sebagai ganti",
    0.98,
    "session-42",
);

// Serialkan ke OAMP JSON
let json = serde_json::to_string_pretty(&entry)?;

// Sahkan
oamp_types::validate::validate_knowledge_entry(&entry)?;
```

### TypeScript

```bash
npm install @oamp/types
```

```typescript
import { KnowledgeEntry } from '@oamp/types';

// Sahkan dan hurai dokumen OAMP
const entry = KnowledgeEntry.parse(jsonData);

// Akses selamat jenis
console.log(entry.category); // "correction"
console.log(entry.confidence); // 0.98
```

## Untuk Pembangun Ejen

Mahu menambah sokongan OAMP kepada ejen anda? Lihat [Panduan Ejen](guide-for-agents.md).

Ringkasnya:
1. **Eksport** — petakan jenis memori dalaman anda kepada OAMP JSON
2. **Import** — hurai OAMP JSON kepada jenis dalaman anda
3. **Sahkan** — gunakan JSON Schema atau pustaka rujukan untuk memastikan pematuhan

## Untuk Pembangun Backend

Mahu membina backend memori yang patuh OAMP? Lihat [Panduan Backend](guide-for-backends.md).

Backend anda perlu melaksanakan 9 titik akhir REST yang meliputi CRUD pengetahuan, penyimpanan model pengguna, dan eksport/import pukal.

## Spesifikasi

Spesifikasi penuh terdapat di [spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md). Ia menggunakan bahasa RFC 2119 (MUST, SHOULD, MAY) untuk mentakrifkan tahap pematuhan.

### Versi

Semasa: **v1.0.0**

Spesifikasi menggunakan pengurusan versi semantik. Dokumen menyertakan medan `oamp_version` untuk keserasian ke hadapan.

### Masa Hadapan (v2.0)

Dirancang untuk v2.0 (berdasarkan maklum balas komuniti):
- Hasil sesi (rekod tugasan berstruktur)
- Metrik kemahiran (statistik pelaksanaan)
- Corak kerja (masa aktiviti, keutamaan alat)
- API penstriman untuk penyegerakan memori masa nyata

## Keselamatan

Lihat [Panduan Keselamatan](security-guide.md) untuk:
- Suite sifer yang disyorkan
- Corak pengurusan kunci
- Pemetaan pematuhan GDPR Artikel 17 / CCPA
- Model ancaman untuk pertukaran memori

## Menyumbang

Kami mengalu-alukan sumbangan. Sila:
1. Baca spesifikasi sebelum mencadangkan perubahan
2. Tambah fixture ujian untuk sebarang perubahan Schema
3. Kemas kini kedua-dua pelaksanaan rujukan Rust dan TypeScript
4. Ikut gaya kod sedia ada

## Hubungi

Untuk pertanyaan, perkongsian, atau maklum balas:

**E-mel:** contact@dthink.ai

## Lesen

MIT — lihat [LICENSE](../LICENSE)
