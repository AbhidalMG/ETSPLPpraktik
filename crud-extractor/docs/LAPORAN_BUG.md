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

**Akar masalah.** (Bab 4, literal string) Kutip penutup langsung mengakhiri string tanpa melihat
karakter berikutnya. Aturan escape `''` butuh lookahead satu karakter untuk membedakan "penutup"
dan "kutip di dalam string".

**Perbaikan.** `lexer.py`, `_string`: bila `'` diikuti `'`, konsumsi keduanya dan tambahkan satu `'`
ke isi string; selain itu string berakhir. Alternatif: regex `'(?:[^']|'')*'`. Tidak dipilih agar
lexer tetap konsisten ditulis tangan seperti di buku.

**Test regresi.** `test_regresi_lexer_kutip_ganda_dalam_string`, kasus tepi `test_tepi_string_kosong_dan_kutip_di_ujung`

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: [ISI].

---

## Bug 4 (T3): Komentar blok `/* ... */` belum didukung

**Ditemukan oleh:** AI (audit kode, TODO T3), diverifikasi [ISI] · **Diperbaiki oleh:** Zidane

**Gejala.** Setiap `/*` melempar `LexError("komentar blok belum didukung")`, sehingga
`pemeliharaan.sql` tidak bisa diproses. SPESIFIKASI 2.3: komentar blok boleh lintas baris, tidak
bersarang, boleh berisi `*`, tidak menghasilkan token; yang tidak ditutup adalah `LexError`.

**Reproduksi minimal.**

```sql
/* komentar */ SELECT a FROM t;
```

**Akar masalah.** (Bab 4, scanning) Komentar juga lexeme yang harus dikenali lalu dibuang. Komentar `--`
sudah punya cabang, tetapi `/*` hanya berisi `raise`. Mengenali penutup `*/` butuh lookahead dua
karakter (`_peek()` dan `_peek(1)`), dan input yang habis sebelum penutup harus menjadi error.
`/*/` bukan komentar tertutup, karena `*` pembuka sudah terpakai.

**Perbaikan.** `lexer.py`, `_scan_token`: setelah `/*`, maju sampai `*/`; bila `_at_end()` lebih dulu,
lempar `LexError("komentar blok tidak ditutup", line, col)` dengan posisi `/*` pembuka.
Alternatif: hapus komentar dengan regex sebelum lexing. Tidak dipilih karena merusak nomor
baris/kolom dan salah memotong bila `/*` ada di dalam string.

**Test regresi.** `test_regresi_lexer_komentar_blok_dilewati_dan_posisi_benar`, `test_regresi_lexer_komentar_blok_tertutup_ok_tak_tertutup_lexerror`, `test_tepi_komentar_blok_berisi_bintang_dan_garis_miring`

**Peran AI.** AI mengusulkan kode berdasarkan TODO dan spek. Verifikasi: [ISI].

---

## Bug 5 (R1): Pencarian scope terbalik

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Zidane

**Gejala.** Pada `audit.sql`, `x` di subquery (`FROM pesanan x`) justru di-resolve ke `pelanggan` milik
query luar, jadi `x.pelanggan_id -> pelanggan`, seharusnya `pesanan`. SPESIFIKASI 4.3: qualifier
dicari dari scope terdalam ke luar, yang pertama ditemukan dipakai (shadowing).

**Reproduksi minimal.**

```sql
SELECT x.id FROM pelanggan x
WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x);
```

**Akar masalah.** (Bab 11, resolusi variabel) Lookup harus berjalan dari scope terdalam ke luar agar
deklarasi lokal menutupi deklarasi luar. Kode membangun daftar rantai scope lalu memanggil
`reversed`, sehingga yang dicek pertama justru scope terluar.

**Perbaikan.** `resolver.py`, `_lookup`: telusuri `self.scope` lalu `parent` dengan loop `while`,
tanpa membalik. Alternatif: menyimpan scope sebagai stack dan menelusuri dari indeks terakhir
seperti di buku. Tidak dipilih karena rantai induk sudah ada.

**Test regresi.** `test_regresi_resolver_alias_dalam_menutupi_alias_luar`

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: [ISI: cek `--ast`, `resolved` harus `pesanan`].

---

## Bug 6 (R2): Scope DELETE tidak pernah di-pop

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Zidane

**Gejala.** `DELETE FROM sesi s ...; SELECT s.id FROM pengguna u` seharusnya error
`alias 's' tidak terdefinisi`, tetapi `s` bocor ke statement berikutnya dan dianggap valid.
Diagnostik hilang dan `Resolver.scope` tidak kembali `None`. Melanggar SPESIFIKASI 4.5.

**Reproduksi minimal.**

```sql
DELETE FROM sesi s WHERE s.a = 1;
SELECT s.id FROM pengguna u;
```

**Akar masalah.** (Bab 11, `beginScope`/`endScope`) Setiap `push` harus berpasangan dengan `pop`.
`_select` dan `_update` melakukannya, `_delete` lupa, sehingga scope-nya menjadi induk bagi
semua statement berikutnya.

**Perbaikan.** `resolver.py`, `_delete`: tambahkan `self._pop()` di akhir. Alternatif: `try/finally`
atau context manager. Tidak dipilih agar polanya sama dengan `_select` dan `_update`.

**Test regresi.** `test_regresi_resolver_scope_delete_tidak_bocor`

**Peran AI.** AI menemukan dengan membandingkan `_delete` dan `_update`. Verifikasi: [ISI].

---

## Bug 7 (T2): Kolom tanpa qualifier tidak di-resolve

**Ditemukan oleh:** AI (audit kode, TODO T2), diverifikasi [ISI] · **Diperbaiki oleh:** Zidane

**Gejala.** `ColumnRef.resolved` tetap `None` tanpa warning untuk kolom seperti `nama`.
SPESIFIKASI 4.3: tepat satu tabel di scope terdalam, di-resolve ke tabel itu; lebih dari satu,
warning `kolom 'nama' ambigu tanpa skema` dan `resolved` tetap `None`; tidak ada tabel, warning.

**Reproduksi minimal.**

```sql
SELECT nama FROM pelanggan;
SELECT nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id;
```

**Akar masalah.** (Bab 11) Cabang resolusi untuk nama tanpa qualifier belum ditulis. Berbeda dengan
qualifier, nama tanpa qualifier hanya melihat scope **terdalam**, karena tanpa skema database
resolver tidak bisa tahu apakah kolom itu milik tabel di scope luar. Kelemahannya:
`SELECT x FROM a WHERE EXISTS (SELECT 1 FROM b WHERE x = 1)` mengikat `x` ke `b`, padahal bisa
jadi milik `a`.

**Perbaikan.** `resolver.py`, `_column`: ambil `self.scope.entries`. Satu entri: isi `resolved` dengan
`_target_of`. Lebih dari satu: warning ambigu. Kosong: warning. Ada pengecekan `self.scope`
karena bisa `None` (kolom di `INSERT ... VALUES`, yang tidak membuat scope). Alternatif:
menelusuri scope luar untuk menebak tabel. Tidak dipilih karena spesifikasi melarangnya.

**Test regresi.** `test_regresi_resolver_kolom_tanpa_qualifier_ambigu`, `test_resolver.py::test_kolom_tanpa_qualifier_satu_tabel`

**Peran AI.** AI mengusulkan kode berdasarkan TODO dan spek. Verifikasi: [ISI].

---

## Bug 8 (P1): AND dan OR punya presedensi sama

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Abhidal

**Gejala.** `a = 1 OR b = 2 AND c = 3` di-parse sebagai `((a=1 OR b=2) AND c=3)`, seharusnya
`a = 1 OR (b = 2 AND c = 3)` (SPESIFIKASI 3.1). Terlihat pada `audit.sql` dan `pemeliharaan.sql`.
CRUD matrix sering tidak berubah, tetapi AST salah dan melanggar spek.

**Reproduksi minimal.**

```sql
SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** (Bab 6, presedensi) Presedensi diekspresikan dengan satu fungsi per tingkat
(OR memanggil AND, AND memanggil NOT, dan seterusnya). `_logical` menggabungkan dua tingkat
dalam satu loop asosiatif kiri, sehingga perbedaan tingkat hilang.

**Perbaikan.** `parser.py`: `_expr` memanggil `_or`; `_or` memanggil `_and` dengan loop `OR`;
`_and` memanggil `_not` dengan loop `AND`. Alternatif: Pratt parser dengan tabel binding power.
Tidak dipilih karena fungsi lain di file ini berbentuk satu fungsi per tingkat.

**Test regresi.** `test_regresi_parser_and_lebih_kuat_dari_or`, `test_tepi_not_dan_or_presedensi`

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: [ISI: cek bentuk AST dengan `--ast`].

---

## Bug 9 (P2): `LEFT OUTER JOIN` gagal

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Abhidal

**Gejala.** Parser menemukan `OUTER` padahal mengharapkan `JOIN`, jadi statement valid dianggap
error sintaks (terlihat di `pemeliharaan.sql`). Grammar 3: `"LEFT" [ "OUTER" ]`.

**Reproduksi minimal.**

```sql
SELECT a FROM t LEFT OUTER JOIN u ON t.id = u.id;
```

**Akar masalah.** (Bab 6, grammar) Fungsi parser harus menerima semua yang diterima grammar. Bagian
opsional `[ "OUTER" ]` tidak ada di kode, jadi setelah `LEFT` parser langsung menuntut `JOIN`.

**Perbaikan.** `parser.py`, `_join`: di cabang `LEFT`, tambahkan `self._match_kw("OUTER")`.

**Test regresi.** `test_regresi_parser_left_outer_join`

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: [ISI].

---

## Bug 10 (P3): Error recovery membuang semua token sampai EOF

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Abhidal

**Gejala.** Pada `campuran_error.sql`, setelah error di statement kedua, `UPDATE` dan `DELETE`
sesudahnya hilang dari matrix. SPESIFIKASI 6: buang token sampai dan termasuk `;`, lalu lanjut;
satu error per statement rusak; statement valid sesudahnya tetap diproses.

**Reproduksi minimal.**

```sql
SELECT a FROM ;
DELETE FROM t;
```

**Akar masalah.** (Bab 6, synchronization pada panic mode) Setelah error, parser membuang token sampai
titik sinkron yang aman, dalam SQL adalah `;`. `_synchronize` lama berjalan sampai akhir input,
jadi titik sinkron tidak pernah dipakai.

**Perbaikan.** `parser.py`, `_synchronize`: maju sampai token `;` dikonsumsi, lalu `return`. Bila
error terdeteksi tepat di `;`, token itu ikut dibuang sesuai "sampai dan termasuk".
Alternatif: berhenti di keyword awal statement. Tidak dipilih karena `SELECT` juga muncul di
dalam subquery.

**Test regresi.** `test_regresi_parser_recovery_berhenti_setelah_titik_koma`, `test_tepi_recovery_statement_terakhir_tanpa_titik_koma`

**Peran AI.** AI menemukan dan mengusulkan perbaikan. Verifikasi: [ISI].

---

## Bug 11 (T1): `INSERT ... SELECT` ditolak parser

**Ditemukan oleh:** AI (audit kode, TODO T1), diverifikasi [ISI] · **Diperbaiki oleh:** Abhidal

**Gejala.** Parser melempar `ParseError("INSERT ... SELECT belum didukung")`. SPESIFIKASI 3 dan 5:
`Insert` dengan `query` terisi, tabel target `C`, tabel sumber `R`.

**Reproduksi minimal.**

```sql
INSERT INTO arsip (id) SELECT id FROM pesanan;
```

**Akar masalah.** (Bab 5, grammar; Bab 6, recursive descent) `insert_stmt` punya dua alternatif:
`VALUES ...` atau `select_stmt`. Setiap alternatif grammar harus punya cabang kode, dan alternatif
kedua hanya berisi `raise`.

**Perbaikan.** `parser.py`, `_insert`: panggil `self._select()` dan kembalikan
`ast.Insert(table, columns, [], query, line=start.line)`. Nilai `values=[]` (bukan `None`)
karena analyzer dan resolver mengiterasi `ins.values`. Resolver dan analyzer sudah menangani
`ins.query`. `SELECT` di dalam INSERT mendapat scope sendiri (SPESIFIKASI 4.1).

**Test regresi.** `test_regresi_parser_insert_select`, `test_parser.py::test_insert_select`, `test_tepi_insert_select_tabel_sama_dan_urutan_operasi`

**Peran AI.** AI mengusulkan kode berdasarkan TODO dan spek. Verifikasi: [ISI].

---

## Bug 12 (A1): Subquery di UPDATE ditandai `U`, seharusnya `R`

**Ditemukan oleh:** AI (audit kode), diverifikasi [ISI] · **Diperbaiki oleh:** Abhidal

**Gejala.** `UPDATE pesanan ... IN (SELECT id FROM pelanggan ...)` menghasilkan `pelanggan: U`,
seharusnya `pelanggan: R` dan `pesanan: U` (SPESIFIKASI 5: membaca tabel lewat subquery selalu
`R`). Terlihat di `audit.sql` dan `laporan_penjualan.sql`.

**Reproduksi minimal.**

```sql
UPDATE a SET x = 1 WHERE y IN (SELECT y FROM b);
```

**Akar masalah.** Aturan analyzer bergantung pada peran tabel (target atau sumber), bukan jenis
statement luar. Parameter `op` diteruskan ke `_collect` sehingga seluruh subquery mewarisi `U`.
Terkait Bab 5: makna sebuah node ditentukan oleh posisinya di pohon AST.

**Perbaikan.** `analyzer.py`, cabang `Update`: ganti `"U"` menjadi `"R"` pada kedua pemanggilan
`_collect` (untuk `SET` dan `WHERE`). Alternatif: memisahkan fungsi "target" dan "sumber".
Tidak dipilih karena perubahan dua argumen sudah cukup.

**Test regresi.** `test_regresi_analyzer_subquery_di_update_adalah_read`

**Peran AI.** AI menemukan dengan membandingkan cabang `Update` dengan tabel SPESIFIKASI 5. Verifikasi: [ISI].

---
