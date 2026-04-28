# Protokol Memori Ejen Terbuka -- Versi 1.0.0

**Status:** Draf  
**Tarikh:** 2026-04-06  
**Pengarang:** Deep Thinking LLC  
**Repositori:** `github.com/deep-thinking-llc/open-agent-memory-protocol`

---

## Abstrak

Protokol Memori Ejen Terbuka (OAMP) mendefinisikan format standard untuk menyimpan, menukar, dan menyoal data memori antara ejen AI dan backend memori. Ia membolehkan kebolehpindahan (pengguna boleh mengeksport memori dari satu ejen dan mengimportnya ke dalam ejen lain), interoperabiliti backend (mana-mana backend yang mematuhi OAMP berfungsi dengan mana-mana ejen yang mematuhi OAMP), dan privasi secara lalai (penyulitan semasa penyimpanan, pemilikan data pengguna, dan penjejakan asal adalah wajib).

Kata kunci "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", dan "OPTIONAL" dalam dokumen ini harus ditafsirkan seperti yang diterangkan dalam [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

---

## 1. Pengenalan dan Motivasi

Ejen AI semakin mengekalkan memori yang berterusan tentang pengguna: pilihan mereka, kepakaran, pembetulan, dan corak tingkah laku. Tanpa format pertukaran yang umum, memori ini terkurung kepada satu ejen atau backend, mencipta kunci vendor dan menghalang pengguna daripada memiliki data mereka sendiri.

OAMP menangani ini dengan mendefinisikan:

- **Skema JSON** untuk struktur dokumen memori ejen
- **Kontrak API REST** untuk backend memori
- **Keperluan privasi** yang mesti dipatuhi oleh pelaksanaan yang mematuhi
- **Pelaksanaan rujukan** dalam Rust dan TypeScript

### 1.1 Apa Itu OAMP

- Skema JSON yang mendefinisikan struktur dokumen memori ejen
- Kontrak API REST untuk backend memori
- Pelaksanaan rujukan dalam Rust dan TypeScript
- Keperluan privasi dan keselamatan yang mesti dipatuhi oleh pelaksanaan yang mematuhi

### 1.2 Apa Itu OAMP Bukan

- Pangkalan data atau enjin penyimpanan
- Rangka kerja ejen
- Model AI tertentu atau format embedding
- Protokol pengangkutan (OAMP menggunakan HTTP/JSON, dengan protobuf pilihan)

### 1.3 Prinsip Reka Bentuk

- **Kebolehpindahan pertama.** Memori yang dieksport dari satu ejen MUST boleh diimport oleh mana-mana ejen yang mematuhi tanpa transformasi.
- **Privasi secara lalai.** Penyulitan dan asal bukanlah tambahan pilihan; ia adalah keperluan normatif.
- **Adopsi lebih penting daripada kesempurnaan.** JSON lebih diutamakan berbanding protobuf sebagai format utama. Medan pilihan lebih diutamakan berbanding kompleksiti mandatori. Kurangkan spesifikasi carian untuk membolehkan pilihan backend.
- **Protokol dua hala.** OAMP berfungsi untuk kedua-dua rangka kerja ejen (pengeluar/pengguna) dan backend memori (penyimpanan/pengambilan). Kedua-dua pihak mempunyai keperluan normatif.

---

## 2. Terminologi

- **Ejen** -- sistem perisian yang berinteraksi dengan pengguna dan mengekalkan memori tentang mereka.
- **Backend** -- perkhidmatan penyimpanan yang mengekalkan dokumen OAMP dan mendedahkan API REST yang ditakrifkan dalam Seksyen 6.
- **Entiti Pengetahuan** -- sekeping maklumat yang berasingan yang telah dipelajari oleh ejen tentang pengguna, diwakili sebagai dokumen OAMP dengan `type: "knowledge_entry"`.
- **Penyimpanan Pengetahuan** -- koleksi Entiti Pengetahuan yang dibungkus untuk eksport atau import secara pukal, diwakili sebagai dokumen OAMP dengan `type: "knowledge_store"`.
- **Model Pengguna** -- pemahaman terstruktur yang berkembang tentang pengguna oleh ejen, diwakili sebagai dokumen OAMP dengan `type: "user_model"`.
- **Keyakinan** -- nombor titik terapung dalam [0.0, 1.0] yang mewakili kepastian ejen dalam sekeping pengetahuan. 0.0 bermaksud tiada keyakinan; 1.0 bermaksud pasti.
- **Asal** -- rekod tentang bila dan bagaimana sekeping pengetahuan diperoleh (sesi, ejen, cap waktu).
- **Pengurangan** -- pengurangan keyakinan dari semasa ke semasa apabila pengetahuan menjadi lapuk.

---

## 3. Entiti Pengetahuan

Entiti Pengetahuan mewakili sekeping maklumat yang berasingan yang telah dipelajari oleh ejen tentang pengguna.

### 3.1 Struktur Dokumen

```json
{
  "oamp_version": "1.0.0",
  "type": "knowledge_entry",
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "user-123",
  "category": "preference",
  "content": "Pengguna lebih suka Rust berbanding Python untuk pengaturcaraan sistem",
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

### 3.2 Definisi Medan

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | Versi spesifikasi sebagai semver. Untuk versi ini: `"1.0.0"`. |
| `type` | string | MUST | MUST be `"knowledge_entry"`. |
| `id` | string | MUST | Pengenalan unik UUID v4. MUST be globally unique. |
| `user_id` | string | MUST | Pengenalan pengguna yang pengetahuan ini milik. |
| `category` | string | MUST | Salah satu: `"fact"`, `"preference"`, `"pattern"`, `"correction"`. Lihat 3.4. |
| `content` | string | MUST | Pengetahuan itu sendiri dalam bahasa semula jadi. MUST NOT be empty. |
| `confidence` | number | MUST | Float dalam [0.0, 1.0]. Lihat 3.5. |
| `source` | object | MUST | Maklumat asal. Lihat 3.3. |
| `decay` | object | MAY | Parameter pengurangan temporal. Lihat 3.6. |
| `tags` | array of string | MAY | Tag bebas untuk penapisan dan pengelompokan. |
| `metadata` | object | MAY | Sambungan khusus vendor. Pelaksanaan yang mematuhi MUST NOT menolak dokumen dengan medan metadata yang tidak diketahui. |

### 3.3 Objek Sumber

Objek `source` merekod asal Entiti Pengetahuan. Pelaksanaan MUST NOT mencipta Entiti Pengetahuan tanpa `source`.

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `session_id` | string | MUST | Pengenalan sesi di mana ini dipelajari. |
| `timestamp` | string | MUST | Tarikh dan masa ISO 8601 apabila ini dipelajari. |
| `agent_id` | string | MAY | Pengenalan ejen yang menghasilkan pengetahuan ini. |

### 3.4 Definisi Kategori

Medan `category` mengklasifikasikan jenis pengetahuan. Pelaksanaan yang mematuhi MUST menggunakan salah satu daripada empat nilai yang ditakrifkan dan MUST NOT mendefinisikan kategori tambahan dalam v1.0 (gunakan `tags` atau `metadata` untuk sambungan vendor).

- **`fact`** -- Maklumat objektif tentang persekitaran atau konteks pengguna. Fakta tidak bersifat evaluatif. Contoh: "Pengguna bekerja di Acme Corp", "Projek menggunakan PostgreSQL 15", "Pengguna terletak di Berlin".

- **`preference`** -- Pilihan pengguna yang dinyatakan atau disimpulkan tentang bagaimana ejen harus berkelakuan atau bertindak balas. Contoh: "Lebih suka jawapan ringkas", "Suka mod gelap", "Lebih suka Rust berbanding Python".

- **`pattern`** -- Corak tingkah laku berulang yang telah diperhatikan oleh ejen. Corak disimpulkan dari beberapa pemerhatian, bukan satu peristiwa. Contoh: "Menghantar ke staging sebelum pengeluaran", "Mengulas PR pada waktu pagi", "Meminta semakan kod sebelum menggabungkan".

- **`correction`** -- Pengguna membetulkan tingkah laku ejen. Kategori ini adalah data kelas pertama, bukan kesan sampingan. Pembetulan adalah isyarat pembelajaran utama. Contoh: "Jangan gunakan `unwrap()`, gunakan pengendalian ralat yang betul", "Jangan ulang konteks yang sudah saya berikan".

### 3.5 Keyakinan

Medan `confidence` adalah float dalam [0.0, 1.0]:

- `0.0` -- tiada keyakinan; pengetahuan ini mungkin salah
- `0.5` -- tidak pasti; kebarangkalian yang lebih kurang sama untuk betul atau salah
- `1.0` -- pasti; ejen mempunyai bukti yang kuat bahawa ini adalah betul

Ejen SHOULD mengkalibrasi skor keyakinan berdasarkan bukti. Fakta yang dinyatakan oleh pengguna SHOULD mempunyai keyakinan awal yang lebih tinggi berbanding corak yang disimpulkan.

Pembetulan daripada pengguna SHOULD diberikan keyakinan >= 0.9, kerana ia mewakili niat pengguna yang jelas.

### 3.6 Pengurangan Keyakinan

Pengetahuan menjadi lapuk dari semasa ke semasa. Pelaksanaan SHOULD menerapkan pengurangan temporal:

```
confidence_t = confidence_0 * e^(-ln(2) / half_life_days * age_days)
```

Di mana:
- `confidence_0` adalah keyakinan pada masa pengesahan terakhir
- `half_life_days` adalah `decay.half_life_days`
- `age_days` adalah bilangan hari sejak `decay.last_confirmed`
  (atau `source.timestamp` jika `last_confirmed` tidak ada)

Jika `decay` tidak ada atau `half_life_days` adalah `null`, tiada pengurangan yang diterapkan.

Separuh hayat yang disyorkan mengikut kategori:
- `fact`: 365 hari (fakta berubah dengan jarang)
- `preference`: 70 hari (pilihan berkembang)
- `pattern`: 90 hari (corak mungkin berubah dengan perubahan peranan/konteks)
- `correction`: tiada pengurangan (pembetulan adalah kekal kecuali digantikan)

---

## 4. Penyimpanan Pengetahuan

Penyimpanan Pengetahuan adalah dokumen koleksi untuk eksport dan import secara pukal. Ia membolehkan snapshot memori lengkap dipindahkan antara ejen atau backend.

### 4.1 Struktur Dokumen

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

### 4.2 Definisi Medan

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | Versi spesifikasi. |
| `type` | string | MUST | MUST be `"knowledge_store"`. |
| `user_id` | string | MUST | Pengguna semua entri milik. |
| `entries` | array | MUST | Array objek Entiti Pengetahuan. MAY be empty. |
| `exported_at` | string | MUST | Cap waktu ISO 8601 eksport. |
| `agent_id` | string | MAY | Pengenalan ejen yang mengeksport. |

### 4.3 Warisan Entri

Setiap entri dalam `entries` MUST merupakan objek Entiti Pengetahuan yang sah. Entri dalam Penyimpanan Pengetahuan MAY mengabaikan `oamp_version` (mereka mewarisi dari penyimpanan); walau bagaimanapun, pengimport yang mematuhi MUST menerima entri dengan atau tanpa `oamp_version`.

### 4.4 Semantik Penggabungan

Apabila mengimport Penyimpanan Pengetahuan ke dalam backend yang sedia ada:

- Entri dengan ID yang tidak wujud MUST dimasukkan.
- Entri dengan ID yang sudah wujud: spesifikasi RECOMMENDS penyelesaian berdasarkan keyakinan (keyakinan yang lebih tinggi menang). Pelaksanaan MAY mendefinisikan strategi penggabungan lain tetapi MUST mendokumentasikannya.
- Pelaksanaan MUST NOT membuang entri secara senyap; sebarang entri yang ditolak SHOULD dilaporkan dalam respons import.

---

## 5. Model Pengguna

Model Pengguna mewakili pemahaman terstruktur yang berkembang tentang pengguna oleh ejen. Semua seksyen di luar sampul adalah secara bebas pilihan -- ejen yang hanya menjejaki kepakaran MAY mengabaikan komunikasi dan pembetulan.

### 5.1 Medan Sampul

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `oamp_version` | string | MUST | Versi spesifikasi. |
| `type` | string | MUST | MUST be `"user_model"`. |
| `user_id` | string | MUST | Pengenalan pengguna. |
| `model_version` | integer | MUST | Nombor versi yang meningkat monoton. MUST be >= 1. |
| `updated_at` | string | MUST | Cap waktu ISO 8601 kemas kini terakhir. |
| `metadata` | object | MAY | Sambungan khusus vendor. |

Apabila menyimpan Model Pengguna, backend MUST menolak kemas kini di mana `model_version` adalah kurang daripada atau sama dengan versi yang disimpan (pengawalan kebolehan optimistik).

### 5.2 Seksyen Komunikasi

Objek `communication` memodelkan bagaimana pengguna lebih suka berinteraksi dengan ejen. Skala adalah berterusan dan bukan kategori untuk membolehkan pemodelan yang halus.

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `verbosity` | number | MAY | -1.0 (ringkas) hingga 1.0 (terperinci). 0.0 = lalai. |
| `formality` | number | MAY | -1.0 (kasual) hingga 1.0 (formal). 0.0 = lalai. |
| `prefers_examples` | boolean | MAY | Pengguna lebih suka contoh kod atau yang telah berfungsi. |
| `prefers_explanations` | boolean | MAY | Pengguna lebih suka penjelasan tentang pemikiran. |
| `languages` | array of string | MAY | Kod bahasa ISO 639-1 (contohnya, `["en", "de"]`). |

### 5.3 Seksyen Kepakaran

Array `expertise` memodelkan pengetahuan yang ditunjukkan oleh pengguna di pelbagai domain. Setiap entri mewakili satu domain.

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `domain` | string | MUST | Nama domain kepakaran (contohnya, `"rust"`, `"kubernetes"`). |
| `level` | string | MUST | Salah satu: `"novice"`, `"intermediate"`, `"advanced"`, `"expert"`. |
| `confidence` | number | MUST | Keyakinan ejen dalam penilaian ini, 0.0-1.0. |
| `evidence_sessions` | array of string | MAY | ID sesi di mana kepakaran ini diperhatikan. |
| `last_observed` | string | MAY | Tarikh dan masa ISO 8601 pemerhatian yang paling terkini. |

### 5.4 Seksyen Pembetulan

Array `corrections` adalah rekod kelas pertama tentang instances di mana pengguna membetulkan ejen. Ini adalah isyarat pembelajaran utama dan SHOULD dipelihara tanpa had.

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `what_agent_did` | string | MUST | Apa yang dilakukan ejen yang tidak betul. |
| `what_user_wanted` | string | MUST | Apa yang diinginkan pengguna sebagai ganti. |
| `context` | string | MAY | Bila pembetulan ini berlaku (contohnya, "hanya untuk perbincangan seni bina"). |
| `session_id` | string | MUST | Sesi di mana pembetulan berlaku. |
| `timestamp` | string | MUST | Tarikh dan masa ISO 8601. |

### 5.5 Seksyen Pilihan yang Dinyatakan

Array `stated_preferences` merekod pilihan yang telah dinyatakan secara eksplisit oleh pengguna. Ini membawa berat yang lebih tinggi berbanding pengetahuan yang disimpulkan kerana pengguna secara aktif menyatakannya.

| Medan | Jenis | Keperluan | Penerangan |
|-------|------|-------------|-------------|
| `key` | string | MUST | Kunci pilihan (contohnya, `"code_style"`, `"response_length"`). |
| `value` | string | MUST | Nilai pilihan. |
| `timestamp` | string | MUST | Tarikh dan masa ISO 8601 apabila dinyatakan. |

---

## 6. API REST Backend

### 6.1 URL Asas

Semua titik akhir berada di bawah `/v1/`. Backend MAY hos di mana-mana URL asas tetapi MUST mengekalkan awalan laluan `/v1/` untuk membolehkan versi masa depan.

### 6.2 Titik Akhir Pengetahuan

```
POST   /v1/knowledge             -- simpan Entiti Pengetahuan
GET    /v1/knowledge?query=      -- cari pengetahuan (pertanyaan teks)
GET    /v1/knowledge/:id         -- ambil berdasarkan ID
DELETE /v1/knowledge/:id         -- padam
PATCH  /v1/knowledge/:id         -- kemas kini keyakinan, sahkan
```

**POST /v1/knowledge**

Badan permintaan: dokumen Entiti Pengetahuan yang sah.  
Respons kejayaan: `201 Created` dengan dokumen yang disimpan (termasuk sebarang medan yang ditetapkan oleh backend).  
Pada kegagalan pengesahan: `400 Bad Request` dengan badan ralat JSON.

**GET /v1/knowledge/:id**

Respons kejayaan: `200 OK` dengan dokumen Entiti Pengetahuan.  
Jika tidak dijumpai: `404 Not Found`.  
Backend MUST mengesahkan bahawa pengguna yang disahkan memiliki entri ini. Jika pengguna yang meminta tidak memiliki entri, backend MUST mengembalikan `403 Forbidden`. Parameter pertanyaan pilihan `?user_id=` adalah RECOMMENDED untuk pengesahan autorisasi pertahanan dalam.

**DELETE /v1/knowledge/:id**

Respons kejayaan: `204 No Content`.  
Backend MUST memadam entri secara kekal (bukan padam lembut).  
Medan yang disulitkan SHOULD dihapuskan sebelum penghapusan (spesifikasi §8.2.7).  
Backend MUST mengesahkan bahawa pengguna yang disahkan memiliki entri ini.

**PATCH /v1/knowledge/:id**

Membolehkan kemas kini separa `confidence`, `decay.last_confirmed`, dan `tags`.  
Pelaksanaan MUST NOT membenarkan pengubahsuaian `id`, `user_id`, `category`, atau `source`.  
Backend MUST mengesahkan bahawa pengguna yang disahkan memiliki entri ini.

**GET /v1/knowledge?query=**

Lihat Seksyen 6.6 (Carian).

### 6.3 Titik Akhir Model Pengguna

```
POST   /v1/user-model            -- simpan/kemas kini Model Pengguna
GET    /v1/user-model/:user_id   -- ambil
DELETE /v1/user-model/:user_id   -- padam (reset penuh)
```

**POST /v1/user-model**

Badan permintaan: dokumen Model Pengguna yang sah.  
Respons kejayaan: `200 OK` (kemas kini) atau `201 Created` (baru).  
Backend MUST menguatkuasakan monotoniti `model_version` (menolak jika versi baru <= versi yang disimpan dengan `409 Conflict`).

**DELETE /v1/user-model/:user_id**

MUST memadam Model Pengguna lengkap dan semua Entiti Pengetahuan yang berkaitan untuk pengguna. MUST NOT boleh dibalikkan (tiada padam lembut). Respons kejayaan: `204 No Content`.

### 6.4 Titik Akhir Pukal

```
POST   /v1/export                -- eksport semua data untuk pengguna sebagai dokumen OAMP
POST   /v1/import                -- import dokumen OAMP
```

**POST /v1/export**

Badan permintaan: `{ "user_id": "string" }`.  
Respons: dokumen Penyimpanan Pengetahuan yang mengandungi semua entri untuk pengguna, ditambah Model Pengguna dalam medan `metadata` (jika ada).

**POST /v1/import**

Badan permintaan: dokumen Penyimpanan Pengetahuan.  
Respons: `200 OK` dengan ringkasan entri yang diimport, diabaikan, dan ditolak.

### 6.5 Negosiasi Kandungan

Backend MUST menyokong `application/json`. Sokongan untuk format lain adalah OPTIONAL.

| Header Terima | Format Respons |
|--------------|----------------|
| `application/json` (lalai) | JSON mengikut skema |
| `application/protobuf` | Protobuf binari (OPTIONAL) |
| `application/json+oamp` | JSON dengan metadata sampul OAMP (OPTIONAL) |

### 6.6 Carian

Titik akhir `GET /v1/knowledge?query=` menerima parameter pertanyaan teks.

- Spesifikasi TIDAK mewajibkan pelaksanaan carian tertentu (FTS, vektor, hibrid). Backend memilih pelaksanaan mereka.
- Hasil MUST diatur mengikut relevansi (ditakrifkan oleh backend).
- Hasil MUST dikembalikan sebagai array JSON objek Entiti Pengetahuan.
- Titik akhir senarai SHOULD menyokong parameter `?limit=` dan `?offset=`, atau penggilan berasaskan kursor. Spesifikasi tidak mewajibkan gaya penggilan tertentu.
- Backend SHOULD menyokong `?user_id=` untuk mengehadkan hasil kepada satu pengguna.

### 6.7 Pengesahan

Spesifikasi TIDAK mendefinisikan mekanisme pengesahan tertentu. Pengesahan adalah spesifik kepada penyebaran. Panduan keselamatan RECOMMENDS mTLS atau token Pembawa. Backend MUST mendokumentasikan keperluan pengesahan mereka.

Tanpa mengira mekanisme pengesahan, backend MUST menguatkuasakan pengesahan tahap pengguna: setiap titik akhir API yang mengembalikan atau mengubah data pengetahuan MUST terhad kepada pengguna yang disahkan. Akses silang pengguna MUST ditolak dengan `403 Forbidden`.

### 6.8 Respons Ralat

Semua respons ralat MUST adalah objek JSON dengan sekurang-kurangnya:

```json
{
  "error": "string describing the error",
  "code": "machine-readable error code"
}
```

Kod ralat yang disyorkan:

| Kod | Status HTTP | Apabila |
|------|-----------|------|
| `NOT_FOUND` | 404 | Sumber tidak wujud |
| `VERSION_CONFLICT` | 409 | model_version tidak meningkat monoton |
| `VALIDATION_ERROR` | 400 | Kegagalan pengesahan medan |
| `DUPLICATE_ID` | 409 | Entri dengan ID yang sama sudah wujud |
| `UNAUTHORIZED` | 401 | Pengesahan diperlukan |
| `FORBIDDEN` | 403 | Pengguna tidak memiliki sumber ini |
| `RATE_LIMITED` | 429 | Terlalu banyak permintaan |

---

## 7. Negosiasi Kandungan

Apabila ejen menghantar permintaan dengan `Accept: application/protobuf`, backend MAY menjawab dengan mesej binari yang dikodkan protobuf. Definisi protobuf disediakan dalam `proto/oamp/v1/` dalam repositori OAMP. Representasi protobuf dan JSON MUST adalah setara secara semantik.

Jika backend tidak menyokong protobuf, ia MUST menjawab dengan `406 Not Acceptable` daripada mengembalikan JSON dengan Content-Type yang salah.

---

## 8. Keperluan Privasi dan Keselamatan

### 8.1 Keperluan MUST (Normatif)

Pelaksanaan yang melanggar keperluan ini MUST NOT mendakwa pematuhan OAMP.

1. **Penyulitan semasa penyimpanan.** Semua pengetahuan yang disimpan dan data model pengguna MUST disulitkan semasa penyimpanan. AES-256-GCM adalah RECOMMENDED. Penyimpanan teks biasa semasa penyimpanan adalah pelanggaran pematuhan.

2. **Pemilikan data pengguna.** Titik akhir `/v1/export` MUST mengembalikan semua data untuk pengguna tanpa pengecualian. Titik akhir DELETE MUST menghapuskan semua data pengguna secara kekal. Penghapusan lembut (menandakan sebagai dipadam sambil mengekalkan data) TIDAK mematuhi.

3. **Tiada kandungan dalam log.** Pelaksanaan MUST NOT mencatat kandungan pengetahuan, nilai medan model pengguna, atau teks pembetulan. Mencatat ID entri, kategori, cap waktu, dan kunci metadata adalah dibenarkan.

4. **Penjejakan asal.** Setiap Entiti Pengetahuan MUST mempunyai objek `source` dengan `session_id` dan `timestamp`. Ejen MUST NOT mencipta entri pengetahuan tanpa asal.

### 8.2 Keperluan SHOULD (Disyorkan)

5. **Pengurangan keyakinan.** Pelaksanaan SHOULD menerapkan pengurangan temporal kepada skor keyakinan menggunakan formula dalam Seksyen 3.6.

6. **Log audit.** Operasi pada data pengguna SHOULD dicatat dalam log audit, merekod siapa yang mengakses apa dan bila. Log audit MUST NOT mengandungi kandungan pengetahuan (lihat keperluan 3).

7. **Penghapusan yang selamat.** Operasi penghapusan SHOULD menghapuskan penampan memori yang mengandungi kandungan pengetahuan sebelum membebaskannya.

### 8.3 Panduan Pendamping (Tidak Normatif)

Dokumen `docs/security-guide.md` menyediakan:

- Suite cipher dan saiz kunci yang disyorkan
- Corak pengurusan kunci (kunci per pengguna, penggiliran kunci)
- Pemetaan pematuhan Artikel 17 GDPR (hak untuk dihapuskan)
- Pertimbangan pematuhan CCPA
- Model ancaman: pengintipan fail eksport, pencemaran import, pengulangan sesi

---

## 9. Antara Muka Ejen

Ejen yang menghasilkan atau menggunakan dokumen OAMP MUST melaksanakan:

- **Eksport** -- Serialize memori dalaman kepada dokumen OAMP yang sah. Semua dokumen yang dieksport MUST lulus pengesahan terhadap Skema JSON dalam `spec/v1/`.

- **Import** -- Deserialize dokumen OAMP ke dalam format dalaman. Ejen MUST menerima dokumen yang sah mengikut Skema JSON dan MUST NOT menolak dokumen yang sah kerana medan `metadata` yang tidak diketahui.

- **Gabung** -- Mengendalikan konflik apabila mengimport pengetahuan yang bertindih dengan pengetahuan sedia ada. Spesifikasi RECOMMENDS penyelesaian berdasarkan keyakinan (keyakinan yang lebih tinggi menang). Ejen MAY melaksanakan strategi lain tetapi MUST mendokumentasikannya.

---

## 10. Dasar Versi

### 10.1 Medan Versi

Medan `oamp_version` menggunakan penandaan versi semantik (semver). Versi semasa adalah `"1.0.0"`.

### 10.2 Peraturan Keserasian

- Pelaksanaan MUST menolak dokumen dengan versi utama yang tidak disokong (contohnya, pelaksanaan v1.0 menerima dokumen `"2.0.0"` MUST menolaknya dengan ralat yang jelas).
- Pelaksanaan SHOULD menerima dokumen dengan versi kecil yang lebih tinggi, mengabaikan medan pilihan yang tidak diketahui (keserasian ke hadapan).
- Pelaksanaan MUST menerima dokumen dengan sebarang versi patch dalam versi kecil yang sama.

### 10.3 Evolusi Medan

- Medan REQUIRED baru MAY hanya ditambah dalam versi utama.
- Medan OPTIONAL baru MAY ditambah dalam versi kecil.
- Medan TIDAK BOLEH dibuang dalam versi kecil atau patch.

---

## 11. Pertimbangan Masa Depan (Skop v2.0)

Yang berikut secara sengaja dikecualikan daripada v1.0 kerana terlalu spesifik kepada pelaksanaan atau memerlukan lebih banyak input komuniti. Mereka MAY ditambah dalam v2.0 atau diteroka melalui medan `metadata` dalam v1.0:

- **Corak kerja** -- jam aktif, jenis tugas biasa, pilihan alat. Ejen v1.0 MAY menyimpan ini dalam `metadata`.

- **Masa aktiviti** -- corak tingkah laku jam-hari dan hari-minggu. Relevan untuk ejen yang peka terhadap jadual.

- **Hasil sesi** -- rekod terstruktur tentang apa yang dicapai dalam setiap sesi. Berguna untuk ejen yang menguruskan projek jangka panjang.

- **Metrik kemahiran** -- statistik pelaksanaan untuk kemahiran atau aliran kerja yang boleh digunakan semula. Terlalu spesifik kepada pelaksanaan tanpa input komuniti yang lebih luas.

Maklum balas komuniti tentang kawasan ini harus diarahkan kepada papan perbincangan repositori GitHub OAMP.

---

## Lampiran A: Senarai Semak Pematuhan

### Pematuhan Ejen

- [ ] Eksport menghasilkan dokumen OAMP yang sah (disahkan terhadap Skema JSON)
- [ ] Semua Entiti Pengetahuan yang dieksport mempunyai `source.session_id` dan `source.timestamp`
- [ ] Import menerima semua dokumen OAMP yang sah (termasuk `metadata` yang tidak diketahui)
- [ ] Strategi penggabungan didokumentasikan
- [ ] Tiada kandungan pengetahuan dicatat

### Pematuhan Backend

- [ ] Semua sepuluh titik akhir REST dilaksanakan
- [ ] Data disulitkan semasa penyimpanan
- [ ] `/v1/export` mengembalikan semua data pengguna
- [ ] Titik akhir DELETE melakukan penghapusan kekal
- [ ] Monotoniti `model_version` dikuatkuasakan
- [ ] Tiada kandungan pengetahuan dalam log
- [ ] Pengesahan tahap pengguna dikuatkuasakan pada semua titik akhir
- [ ] Respons ralat mengikuti format Seksyen 6.8

---

## Lampiran B: Lokasi Skema JSON

| Jenis Dokumen | Skema |
|--------------|--------|
| Entiti Pengetahuan | `spec/v1/knowledge-entry.schema.json` |
| Penyimpanan Pengetahuan | `spec/v1/knowledge-store.schema.json` |
| Model Pengguna | `spec/v1/user-model.schema.json` |

Semua skema menggunakan Draf Skema JSON 2020-12.