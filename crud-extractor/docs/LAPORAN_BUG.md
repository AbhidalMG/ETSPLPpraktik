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

## Tiga bagian TODO (bukan bug)

| Kode | Lokasi | Pendekatan | Dikerjakan oleh | Test |
| --- | --- | --- | --- | --- |
| T1 | `parser.py::_insert` | Parse `select_stmt` setelah daftar kolom, simpan di `Insert.query` dengan `values=[]` | Abhidal | `test_regresi_parser_insert_select` |
| T2 | `resolver.py::_column` | Kolom tanpa qualifier: lihat hanya scope terdalam; 1 tabel → resolve, >1 → warning ambigu, 0 → warning | Zidane | `test_regresi_resolver_kolom_tanpa_qualifier_ambigu` |
| T3 | `lexer.py::_scan_token` | Konsumsi `/* ... */` lintas baris; tidak tertutup → `LexError` | Zidane | `test_regresi_lexer_komentar_blok_dilewati_dan_posisi_benar` |

---

## Bug 1 (L1): Keyword huruf kecil tidak dikenali

**Ditemukan oleh:** audit dibantu AI, dikonfirmasi Zidane · **Diperbaiki oleh:** Zidane

**Gejala.** Menurut SPESIFIKASI.md bagian 2.2, `select`, `Select`, dan `SELECT` sama-sama keyword dan nilai
tokennya dinormalisasi ke huruf besar. Input `select id from t` menghasilkan token `IDENT 'select'`,
`IDENT 'id'`, `IDENT 'from'`, `IDENT 't'` (semuanya IDENT). Parser lalu gagal:
`Baris 1, kolom 1: diharapkan awal statement (SELECT, INSERT, UPDATE, DELETE), ditemukan 'select'`. Yang diharapkan:
`KEYWORD 'SELECT'`, `IDENT 'id'`, `KEYWORD 'FROM'`, `IDENT 't'`. Efek nyata terlihat pada `pemeliharaan.sql` yang
seluruh keyword-nya huruf kecil.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
select id from t
```

**Akar masalah.** Di lexer, sebuah kata dibaca utuh lebih dulu (maximal munch), lalu jenisnya ditentukan dengan
mencocokkannya ke tabel reserved words (*Crafting Interpreters* Bab 4, bagian identifier dan keyword). Kode lama
mencocokkan teks asli ke `KEYWORDS` yang berisi huruf besar, sehingga pencocokan bersifat peka huruf besar/kecil,
padahal SQL tidak membedakannya. Nilai token juga tidak dinormalisasi, jadi parser yang membandingkan `"SELECT"`
ikut gagal.

**Perbaikan.** `lexer.py`, method `_word`: pencocokan memakai `text.upper() in KEYWORDS` dan nilai token keyword
disimpan sebagai `text.upper()`. Identifier tetap memakai teks asli, sehingga `selection` dan `fromage` tetap
IDENT (yang dicocokkan satu kata utuh, bukan awalan). Alternatif yang dipertimbangkan: mengubah seluruh source ke
huruf besar sebelum lexing. Tidak dipilih karena ikut mengubah isi string literal.

**Test regresi.** `test_regresi_lexer_keyword_huruf_kecil_dinormalisasi` di `tests/test_tambahan.py` (gagal
sebelum, lulus sesudah). Test terlihat `test_keyword_huruf_kecil` ikut lulus.

**Peran AI.** AI menemukan bug saat mengaudit `lexer.py` terhadap spek 2.2 dan mengusulkan perbaikan. Kami
memverifikasi dengan menjalankan test `test_keyword_huruf_kecil` (gagal sebelum perbaikan), memeriksa token
`select`, `Select`, `selection`, `fromage` secara manual, dan menjalankan ulang `pemeliharaan.sql`.

---

## Bug 2 (L2): Operator `<>` pecah menjadi dua token

**Ditemukan oleh:** audit dibantu AI, dikonfirmasi Zidane · **Diperbaiki oleh:** Zidane

**Gejala.** SPESIFIKASI.md bagian 2.5 mewajibkan maximal munch: `<>` adalah satu token OP. Input `a <> b`
menghasilkan `IDENT a`, `OP <`, `OP >`, `IDENT b`. Pada `SELECT a FROM t WHERE a <> 1` parser gagal:
`Baris 1, kolom 26: diharapkan ekspresi, ditemukan '>'`. Yang diharapkan: `IDENT a`, `OP <>`, `IDENT b`. Efek nyata
terlihat di `laporan_penjualan.sql` baris 6 (`o.catatan <> 'FROM rahasia'`): seluruh statement SELECT hilang dari
matrix.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE a <> 1
```

**Akar masalah.** Aturan maximal munch (*Crafting Interpreters* Bab 4) menyatakan lexer harus mengambil lexeme
terpanjang yang cocok. Cabang `<` hanya memeriksa karakter `=` setelahnya (`<=`), tidak memeriksa `>`. Akibatnya
`<` dipotong lebih awal dan `>` menjadi token terpisah yang tidak punya tempat dalam grammar ekspresi.

**Perbaikan.** `lexer.py`, method `_scan_token`, cabang `ch == "<"`: urutan pengecekan `<=`, lalu `<>`, lalu `<`.
Alternatif: memakai tabel operator dua karakter lalu mencari yang terpanjang. Tidak dipilih karena perubahan
lebih besar daripada kebutuhan dan menambah tabel baru yang harus dijaga konsisten dengan spek.

**Test regresi.** `test_regresi_lexer_operator_tidak_sama_satu_token`.

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: menjalankan ulang `laporan_penjualan.sql` (error baris 6 hilang
dan statement SELECT masuk matrix), serta `evaluate.py` untuk file berlabel.

---

## Bug 3 (L3): Dua kutip tunggal `''` di dalam string

**Ditemukan oleh:** audit dibantu AI, dikonfirmasi Zidane · **Diperbaiki oleh:** Zidane

**Gejala.** SPESIFIKASI.md bagian 2.4: dua kutip berturut-turut di dalam string mewakili satu karakter kutip, jadi
`'O''Brien'` adalah satu token STRING bernilai `O'Brien`. Lexer lama menghasilkan dua token: `STRING 'O'` dan
`STRING 'Brien'`. Parser gagal: `Baris 1, kolom 30: diharapkan ';' di akhir statement, ditemukan 'Brien'`.
Efek nyata pada `pemeliharaan.sql` baris 6 dan 9 (`'O''Brien'`, `'O''Neil'`).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE n = 'O''Brien'
```

**Akar masalah.** Pemindaian literal string (*Crafting Interpreters* Bab 4) berhenti pada kutip penutup pertama
tanpa melihat karakter berikutnya. Aturan escape `''` membutuhkan lookahead satu karakter: jika kutip diikuti
kutip lagi, itu bagian dari isi string, bukan akhir string.

**Perbaikan.** `lexer.py`, method `_string`: saat menemukan `'`, periksa `_peek()`; jika juga `'`, konsumsi dan
tambahkan satu `'` ke isi, lalu lanjutkan loop. Alternatif: pasca-proses dua string bersebelahan di parser.
Tidak dipilih karena itu memindahkan tanggung jawab lexical ke parser dan salah menggabungkan dua literal
yang memang bersebelahan.

**Test regresi.** `test_regresi_lexer_kutip_ganda_dalam_string`; kasus tepi `test_tepi_string_kosong_dan_kutip_di_ujung`.

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: token `'O''Brien'` menjadi satu STRING `O'Brien`,
string kosong `''` tetap string kosong, dan `'a'''` bernilai `a'`; `pemeliharaan.sql` diproses tanpa error.

---

## Bug 5 (R1): Pencarian scope terbalik (luar ke dalam)

**Ditemukan oleh:** audit dibantu AI, dikonfirmasi Zidane · **Diperbaiki oleh:** Zidane

**Gejala.** SPESIFIKASI.md bagian 4.3: qualifier dicari dari scope terdalam ke luar, dan yang pertama ditemukan dipakai,
sehingga alias di subquery menutupi alias yang sama di luar (shadowing). Pada
`SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x)`, resolver lama menghubungkan
`x.pelanggan_id` ke `pelanggan` (scope luar). Yang diharapkan: `pesanan`. Efek nyata pada `audit.sql` baris 12-14.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x)
```

**Akar masalah.** Resolusi nama pada scope bersarang harus dimulai dari scope terdalam dan naik ke induknya
(*Crafting Interpreters* Bab 11, resolusi variabel dan shadowing). Kode lama membangun daftar rantai scope lalu
membaliknya dengan `reversed`, sehingga yang diperiksa pertama adalah scope terluar. Deklarasi lokal tidak lagi
menutupi deklarasi luar.

**Perbaikan.** `resolver.py`, method `_lookup`: telusuri dari `self.scope` ke `scope.parent` dalam satu loop dan
kembalikan entri pertama yang ditemukan. Alternatif: mempertahankan daftar rantai tetapi tidak membalikkannya. Tidak
dipilih karena menyimpan daftar sementara tidak diperlukan; menelusuri `parent` langsung lebih sederhana dan setara.

**Test regresi.** `test_regresi_resolver_alias_dalam_menutupi_alias_luar`.

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: `--ast` pada `audit.sql` menunjukkan `x.pelanggan_id`
menuju `pesanan`, dan correlated subquery (alias luar dipakai di subquery) tetap resolve ke tabel luar.

---

## Bug 6 (R2): Scope DELETE tidak pernah di-pop

**Ditemukan oleh:** audit dibantu AI, dikonfirmasi Zidane · **Diperbaiki oleh:** Zidane

**Gejala.** SPESIFIKASI.md bagian 4.5: setelah satu statement selesai di-resolve tidak boleh ada scope tersisa, dan alias
statement sebelumnya tidak boleh terlihat oleh statement berikutnya. Pada
`DELETE FROM sesi s WHERE s.k < 1; SELECT s.id FROM pengguna u`, resolver lama tidak melaporkan error apa pun
(`diag == []`) dan `Resolver.scope` tidak kembali `None`. Yang diharapkan: error `alias 's' tidak terdefinisi` untuk
statement kedua. Efek nyata pada `audit.sql` baris 16 lalu 18.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
DELETE FROM sesi s WHERE s.k < 1;
SELECT s.id FROM pengguna u;
```

**Akar masalah.** Setiap pembuatan scope harus berpasangan dengan penutupannya, seperti `beginScope` dan `endScope`
(*Crafting Interpreters* Bab 11, scope sebagai tumpukan). `_select` dan `_update` memanggil `_pop`, tetapi `_delete`
hanya memanggil `_push`. Scope DELETE tetap berada di tumpukan dan menjadi induk bagi semua statement berikutnya.

**Perbaikan.** `resolver.py`, method `_delete`: tambahkan `self._pop()` setelah resolusi klausa `WHERE`. Alternatif:
mereset `self.scope = None` di `resolve_statement` setelah tiap statement. Tidak dipilih karena itu menutupi
ketidakseimbangan push/pop alih-alih memperbaikinya dan akan menyembunyikan bug serupa di tempat lain.

**Test regresi.** `test_regresi_resolver_scope_delete_tidak_bocor`.

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: setelah memproses `DELETE` dan `UPDATE`,
`Resolver.scope` bernilai `None`, dan `audit.sql` baris 18 kini menghasilkan error alias `s`.

---

## Bug 8 (P1): AND dan OR sama kuat

**Ditemukan oleh:** audit dibantu AI, dikonfirmasi Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** SPESIFIKASI.md bagian 3.1: OR tingkat 1 (terendah), AND tingkat 2, sehingga `a = 1 OR b = 2 AND c = 3`
berarti `a = 1 OR (b = 2 AND c = 3)`. Parser lama menghasilkan `((a = 1 OR b = 2) AND c = 3)`: akar pohon bertipe AND
dengan anak kiri OR. Yang diharapkan: akar bertipe OR dengan anak kanan AND. Terlihat pada `audit.sql` baris 4-6 dan
`pemeliharaan.sql` baris 6. CRUD matrix sering tidak berubah, tetapi AST salah (bug tetap bug jika melanggar spek).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3
```

**Akar masalah.** Kode lama memakai satu fungsi _logical dengan satu loop untuk AND maupun OR, sehingga kedua operator berada di tingkat yang sama dan digabung dari kiri ke kanan. Perbedaan tingkat yang tertulis di grammar hilang.

**Perbaikan.** parser.py:_logical dipecah menjadi _or (loop OR) dan _and(loop AND, operan dari _not); _expr memanggil _or

**Test regresi.** test_regresi_parser_and_lebih_kuat_dari_or

**Peran AI.** AI menemukan dan mengusulkan perbaikan bug. Kami memverivikasi dengan mencetak AST dengan --ast, kami juga melakukan cek ulang pada spesifikasi dan tabel presedensi.

---

## Bug 9 (P2): `LEFT OUTER JOIN` gagal

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di SPESIFIKASI.md disebutkan bahwa
join = ["INNER" | "LEFT"[ "OUTER" ]] "JOIN". parser menemukan OUTER padahal yang diharapkan adalah JOIN, ini merupakan error pada sintaks yang statement nya sudah valid

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```
SELECT a.id FROM a LEFT OUTER JOIN b ON b.id = a.id

```

**Akar masalah.** Fungsi parser harus menerima semua yang diterima grammar karena setiap aturan grammar seharusnya

**Perbaikan.**

```
elif self._match_kw("LEFT"):
    self._match_kw("OUTER")
    kind = "LEFT"
```

**Test regresi.** test_regresi_parser_left_outer_join

**Peran AI.** AI menemukan BUG ini, cara kami memverifikasinya adalah dnegan membandingkan _join dengan baris join di grammar, menjalankan pemeliharaan.sql dan memeriksa crm.alamat masuk sebagai R

---

## Bug 10 (P3): Recovery membuang semua token sampai EOF

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di SPESIFIKASI.md disebutkan bahwa panic mode itu membuang token sampai dan termasuk ; berikutnya, lanjutkan ke statement selanjutnya. error hanya ada di satu statement, statement valid sesudah error tetap di proses. di campuran_error.sql setelah error di baris 4, statement baris 6 (UPDATE) dan baris 8 (DELETE) hilang dari matrix jadi terlewat di evaluate.py

**Reproduksi minimal.**

```
SELECT id nama, FROM a;
SELECT 1 FROM b;

```

**Akar masalah.** synchronization pada panic mode, seharusnya parser membuang token sampai titik sinkron dalam kasus ini adalah ; namun yang terjadi adalah kode terbuang sampai akhir input jadi tidak ada titik sinkron nya

**Perbaikan.**

```
def _synchronize(self):
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

```
_collect(assignment.value, usage, "R")
_collect(stmt.where, usage, "R")
```

**Test regresi.** test_regresi_analyzer_subquery_di_update_adalah_read

**Peran AI.**
AI menemukan bug, diverifikasi dengan membaca ulang spek, menjalankan audit.sql dan laporan_penjualan.sql dan mencocokkan dengan label manual

---
