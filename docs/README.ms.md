<div align="center">

# Open Agent Memory Protocol

### Memori ejen AI anda sepatutnya menjadi milik anda.

[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue.svg)](../spec/v1/oamp-v1.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)
[![Rust Crate](https://img.shields.io/badge/crate-oamp--types-orange.svg)](../reference/rust/)
[![npm Package](https://img.shields.io/badge/npm-%40oamp%2Ftypes-red.svg)](../reference/typescript/)
[![PyPI Package](https://img.shields.io/pypi/v/oamp-types.svg)](https://pypi.org/project/oamp-types/)

[Spesifikasi](../spec/v1/oamp-v1.md) | [Rust Crate](../reference/rust/) | [Pakej TypeScript](../reference/typescript/) | [Pakej Python](../reference/python/) | [Panduan Keselamatan](security-guide.md)

---

[English](../README.md) | [中文](README.zh.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

</div>

## Masalahnya

Setiap ejen AI menyimpan memori dengan cara yang berbeza. Apabila anda bertukar ejen, anda bermula dari sifar.

```
Ejen A                              Ejen B
  mempelajari keutamaan anda   →     tidak tahu apa-apa
  menjejak kepakaran anda      →     bermula dari awal
  mengingat pembetulan         →     mengulangi kesilapan
  memahami aliran kerja anda   →     respons generik
```

Pembetulan, keutamaan, dan kepakaran anda terkunci dalam format proprietari. **Anda kehilangan konteks berminggu-minggu setiap kali bertukar.**

## Penyelesaiannya

OAMP ialah standard terbuka yang menjadikan memori ejen mudah alih, peribadi, dan boleh saling beroperasi.

```
Ejen A                              Ejen B
  eksport sebagai OAMP         →     import OAMP
  format JSON standard         →     konteks serta-merta
  data anda, kawalan anda      →     tiada penguncian vendor
```

---

## Kandungan Utama

<table>
<tr>
<td width="50%">

### Lapisan Pengetahuan

Fakta diskret yang dipelajari ejen anda:

```json
{
  "category": "correction",
  "content": "Jangan gunakan unwrap() — gunakan operator ?",
  "confidence": 0.98
}
```

Empat jenis: **fact** · **preference** · **pattern** · **correction**

</td>
<td width="50%">

### Lapisan Model Pengguna

Profil kaya tentang siapa anda:

```json
{
  "expertise": [
    { "domain": "rust", "level": "expert" },
    { "domain": "react", "level": "novice" }
  ],
  "communication": { "verbosity": -0.6 }
}
```

Menjejak: **kepakaran** · **gaya komunikasi** · **pembetulan** · **keutamaan**

</td>
</tr>
</table>

---

## Privasi Diutamakan

OAMP tidak menganggap privasi sebagai pilihan. Ini adalah **keperluan wajib** — bukan panduan:

| Keperluan | Perincian |
|:---|:---|
| **Penyulitan dalam simpanan** | Semua data yang disimpan MESTI disulitkan (AES-256-GCM disyorkan) |
| **Pemilikan data pengguna** | Eksport penuh MESTI disokong — pengguna memiliki memori mereka |
| **Hak pemadaman** | Pemadaman sebenar, bukan pemadaman lembut. Patuh GDPR Artikel 17 |
| **Tiada pengelogan kandungan** | Pelaksanaan TIDAK BOLEH merekod kandungan pengetahuan |
| **Penjejakan asal usul** | Setiap entri merekodkan di mana dan bila ia dipelajari |

---

## Mula Pantas

### Pengesahan

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
    content="Jangan gunakan unwrap() — gunakan operator ?",
    confidence=0.98,
    source=KnowledgeSource(session_id="session-42"),
)

# Pengesahan
errors = validate_knowledge_entry(entry)

# Serialisasikan kepada JSON (kecualikan medan null)
json_str = entry.model_dump_json(exclude_none=True)
```

---

## Struktur Repositori

```
spec/v1/
  oamp-v1.md              Spesifikasi berautoriti (RFC 2119)
  *.schema.json            Definisi JSON Schema (draft-2020-12)
  examples/                Dokumen contoh yang sah

proto/oamp/v1/             Definisi Protocol Buffer

reference/
  rust/                    Rust crate: oamp-types
  typescript/              Pakej npm: @oamp/types
  python/                  Pakej PyPI: oamp-types
  go/                      Modul Go: oamp-go
  elixir/                  Pakej Hex: oamp_types
  server/                  Backend rujukan FastAPI

validators/
  validate.sh              Pengesah dokumen CLI
  test-fixtures/            Dokumen ujian sah dan tidak sah

docs/
  guide-for-agents.md      Melaksanakan OAMP dalam ejen anda
  guide-for-backends.md    Membina backend patuh OAMP
  security-guide.md        Penyulitan, GDPR/CCPA, model ancaman
```

---

## Integrasi OAMP

<table>
<tr>
<td width="50%">

### Untuk Pembangun Ejen

Tambah kemudahalihan memori kepada ejen anda:

1. **Eksport** — petakan jenis dalaman kepada OAMP JSON
2. **Import** — hurai OAMP JSON kepada jenis dalaman
3. **Sahkan** — pastikan pematuhan dengan skema

[Baca Panduan Ejen →](guide-for-agents.md)

</td>
<td width="50%">

### Untuk Pembangun Backend

Bina stor memori patuh OAMP:

- 9 titik akhir REST (CRUD pengetahuan, model pengguna, eksport/import)
- Penyulitan dalam simpanan (wajib)
- Carian (FTS, vektor, atau hibrid — pilihan anda)

[Baca Panduan Backend →](guide-for-backends.md)

</td>
</tr>
</table>

---

## Spesifikasi

| | |
|:---|:---|
| **Versi semasa** | v1.0.0 |
| **Format skema** | JSON Schema (draft-2020-12) + Protocol Buffers |
| **Bahasa pematuhan** | RFC 2119 (MUST, SHOULD, MAY) |
| **Spesifikasi penuh** | [spec/v1/oamp-v1.md](../spec/v1/oamp-v1.md) |

### Dirancang untuk v2.0

Berdasarkan maklum balas komuniti:
- Hasil sesi (rekod tugasan berstruktur)
- Metrik kemahiran (statistik pelaksanaan)
- Corak kerja (masa aktiviti, keutamaan alat)
- API penstriman untuk penyegerakan memori masa nyata

---

## Menyumbang

Kami mengalu-alukan sumbangan:

1. Baca [spesifikasi](../spec/v1/oamp-v1.md) sebelum mencadangkan perubahan
2. Tambah fixture ujian untuk perubahan skema
3. Kemas kini semua tiga pelaksanaan rujukan: Rust, TypeScript, dan Python
4. Ikut gaya kod sedia ada

---

<div align="center">

### Hubungi

Untuk pertanyaan, perkongsian, atau maklum balas

**contact@dthink.ai**

---

**Lesen MIT** — [Deep Thinking LLC](https://dthink.ai)

</div>
