# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

Ringkasan: 12 temuan (9 bug + 3 TODO). Pembagian: Zidane (lexer, resolver), Abhidal (parser, analyzer).

| ID | Modul | Spek | Ringkasan | Jenis |
| --- | --- | --- | --- | --- |
| L1 | lexer.py | 2.2 | Keyword huruf kecil tidak dikenali | bug |
| L2 | lexer.py | 2.5 | `<>` dipecah jadi `<` dan `>` | bug |
| L3 | lexer.py | 2.4 | `''` di dalam string tidak ditangani | bug |
| T3 | lexer.py | 2.3 | Komentar blok `/* */` | TODO |
| R1 | resolver.py | 4.3 | Pencarian scope terbalik (luar ke dalam) | bug |
| R2 | resolver.py | 4.5 | Scope DELETE tidak pernah di-pop | bug |
| T2 | resolver.py | 4.3 | Kolom tanpa qualifier | TODO |
| P1 | parser.py | 3.1 | AND dan OR sama kuat | bug |
| P2 | parser.py | 3 | `LEFT OUTER JOIN`: OUTER tidak dikonsumsi | bug |
| P3 | parser.py | 6 | Recovery membuang semua token sampai EOF | bug |
| T1 | parser.py | 3 dan 5 | `INSERT ... SELECT` | TODO |
| A1 | analyzer.py | 5 | Subquery di UPDATE ditandai `U`, harusnya `R` | bug |

---

## Bug 1 (L1): Keyword huruf kecil tidak dikenali

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Zidane

**Gejala.** `select id from t` menghasilkan semua token `IDENT`, lalu parser gagal di awal statement.
SPESIFIKASI 2.2: `select`, `Select`, `SELECT` sama-sama keyword dan nilai tokennya dinormalisasi
ke huruf besar. Terlihat pada `pemeliharaan.sql` yang semua keyword-nya huruf kecil.

**Reproduksi minimal.**

```sql
select a from t;
```

**Akar masalah.** (Bab 4, identifier vs reserved word) Lexer membaca satu kata utuh (maximal munch),
lalu menentukan jenisnya dengan mencocokkan ke tabel reserved words. Pencocokan memakai teks asli
sehingga peka huruf besar/kecil, padahal SQL tidak. `selection` dan `fromage` tetap `IDENT` karena
yang dicocokkan satu kata utuh, bukan awalannya.

**Perbaikan.** `lexer.py`, `_word`: cocokkan `text.upper()` ke `KEYWORDS`, simpan token bernilai
huruf besar. Alternatif: mengubah seluruh source ke huruf besar sebelum lexing. Tidak dipilih
karena ikut mengubah isi string literal.

**Test regresi.** `test_regresi_lexer_keyword_huruf_kecil_dinormalisasi`

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: [ISI: test gagal sebelum, lulus sesudah].

---

## Bug 2 (L2): Operator `<>` pecah menjadi dua token

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Zidane

**Gejala.** `o.catatan <> 'FROM rahasia'` gagal dengan `Baris 6, kolom 41: diharapkan ekspresi,
ditemukan '>'` (terlihat di `laporan_penjualan.sql`). SPESIFIKASI 2.5: `<>` adalah satu token `OP`.

**Reproduksi minimal.**

```sql
SELECT a FROM t WHERE a <> 1;
```

**Akar masalah.** (Bab 4, maximal munch) Lexer harus mengambil lexeme terpanjang yang cocok. Cabang `<`
hanya memeriksa `=` dan tidak memeriksa `>`, jadi `<>` terbaca sebagai `<` lalu `>`.

**Perbaikan.** `lexer.py`, cabang `<`: cek `=` (`<=`), lalu `>` (`<>`), selain itu `<`.
Alternatif: tabel operator dua karakter. Tidak dipilih karena perubahan satu cabang sudah cukup.

**Test regresi.** `test_regresi_lexer_operator_tidak_sama_satu_token`

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: [ISI].

---

## Bug 3 (L3): Kutip ganda `''` di dalam string

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Zidane

**Gejala.** `'O''Brien'` menjadi dua `STRING` (`O` dan `Brien`) yang bersebelahan, lalu parser gagal.
SPESIFIKASI 2.4: satu token `STRING` bernilai `O'Brien`. Terlihat di `pemeliharaan.sql`.

**Reproduksi minimal.**

```sql
SELECT a FROM t WHERE n = 'O''Brien';
```

**Akar masalah.** Kode lama memakai satu fungsi _logical dengan satu loop untuk AND maupun OR, sehingga kedua operator berada di tingkat yang sama dan digabung dari kiri ke kanan. Perbedaan tingkat yang tertulis di grammar hilang.

**Perbaikan.** parser.py:_logical dipecah menjadi _or (loop OR) dan _and(loop AND, operan dari _not); _expr memanggil _or

**Test regresi.** test_regresi_parser_and_lebih_kuat_dari_or

**Peran AI.** AI menemukan dan mengusulkan perbaikan bug. Kami memverivikasi dengan mencetak AST dengan --ast, kami juga melakukan cek ulang pada spesifikasi dan tabel presedensi.

---

## Bug 6 (R2): Scope DELETE tidak pernah di-pop

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di SPESIFIKASI.md disebutkan bahwa
join = ["INNER" | "LEFT"[ "OUTER" ]] "JOIN". parser menemukan OUTER padahal yang diharapkan adalah JOIN, ini merupakan error pada sintaks yang statement nya sudah valid

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```
SELECT a.id FROM a LEFT OUTER JOIN b ON b.id = a.id

```

**Akar masalah.** Fungsi parser harus menerima semua yang diterima grammar karena setiap aturan grammar seharusnya

**Perbaikan.**
```elif self._match_kw("LEFT"):
    self._match_kw("OUTER")
    kind = "LEFT"
```
**Test regresi.** test_regresi_parser_left_outer_join

**Peran AI.** AI menemukan BUG ini, cara kami memverifikasinya adalah dnegan membandingkan _join dengan baris join di grammar, menjalankan pemeliharaan.sql dan memeriksa crm.alamat masuk sebagai R
---

## Bug 9 (P2): `LEFT OUTER JOIN` gagal

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di SPESIFIKASI.md disebutkan bahwa panic mode itu membuang token sampai dan termasuk ; berikutnya, lanjutkan ke statement selanjutnya. error hanya ada di satu statement, statement valid sesudah error tetap di proses. di campuran_error.sql setelah error di baris 4, statement baris 6 (UPDATE) dan baris 8 (DELETE) hilang dari matrix jadi terlewat di evaluate.py

**Reproduksi minimal.**

```SELECT id nama, FROM a;
SELECT 1 FROM b;

```

**Akar masalah.** synchronization pada panic mode, seharusnya parser membuang token sampai titik sinkron dalam kasus ini adalah ; namun yang terjadi adalah kode terbuang sampai akhir input jadi tidak ada titik sinkron nya

**Perbaikan.**
```def _synchronize(self):
    while not self._at_end():
        if self._advance().type == T.SEMICOLON:
            return
```
**Test regresi.** 
test_regresi_parser_recovery_berhenti_setelah_titik_koma, test_tepi_recovery_statement_terakhir_tanpa_titik_koma

**Peran AI.** AI menemukan BUG ini, kami melakukan verifikasi dengan mengecek campuran_error.sql dan ternyata menghasilkan 1 error dan 3 statement (baris 2,6, dan 8) serta evaluate.py memberi parser recall 1.00 untuk file berlabel
---

## Bug 12 (A1): Subquery di UPDATE ditandai `U`, seharusnya `R`

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di spesifikasi membaca tabel lewat subquerry selalu R, apapun jenis statement luarnya. dalam audit.sql baris 20:UPDATE pesanan ... IN (SELECT id FROM pelanggan ...) menghasilkan pelanggan: U, seharusnya pelanggan: R (pesanan U). Begitu juga laporan_penjualan.sql baris 12.

**Reproduksi minimal.**

```
UPDATE t SET a = 1 WHERE id IN (SELECT id FROM u)

```

**Akar masalah.** Aturan CRUD menentukan operasi dari peran tabel (target statement atau sumber bacaan), bukan dari
jenis statement luar. Di analyze_statement, cabang UPDATE meneruskan "U" sebagai parameter op ke _collect,
sehingga setiap tabel di dalam subquery mewarisi U. Ini kesalahan semantik di tahap analisis yang berjalan di atas
AST (bukan kesalahan sintaks).

**Perbaikan.**
```_collect(assignment.value, usage, "R")
_collect(stmt.where, usage, "R")
```

**Test regresi.** test_regresi_analyzer_subquery_di_update_adalah_read

**Peran AI.** 
AI menemukan bug, diverifikasi dengan membaca ulang spek, menjalankan audit.sql dan laporan_penjualan.sql dan mencocokkan dengan label manual
---
