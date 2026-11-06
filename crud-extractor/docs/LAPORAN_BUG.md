# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: parser.py (tingkat prioritas OR dan AND yang tidak sesuai)

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di SPESIFIKAI.md OR adalah tingkat terendah dan AND tingkat 2 yaitu diatas OR, yang artinya jika terdapat contoh a=1 OR b=2 AND c=3 itu berarti a=1 OR (b=2 AND c=3). yang dihasilkan program parser adalah ((a=1 OR b=2) AND c=3)
yang diharapkan adalah akar yang bertipe OR dengan anak AND, CRUD matrix memang tidak berubah tapi bug tetap sebuah bug jika melanggar spek

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3

```

**Akar masalah.** Kode lama memakai satu fungsi _logical dengan satu loop untuk AND maupun OR, sehingga kedua operator berada di tingkat yang sama dan digabung dari kiri ke kanan. Perbedaan tingkat yang tertulis di grammar hilang.

**Perbaikan.** parser.py:_logical dipecah menjadi _or (loop OR) dan _and(loop AND, operan dari _not); _expr memanggil _or

**Test regresi.** test_regresi_parser_and_lebih_kuat_dari_or

**Peran AI.** AI menemukan dan mengusulkan perbaikan bug. Kami memverivikasi dengan mencetak AST dengan --ast, kami juga melakukan cek ulang pada spesifikasi dan tabel presedensi.

---
## Bug 2: LEFT OUTER JOIN

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di SPESIFIKASI.md disebutkan bahwa
join = ["INNER" | "LEFT"[ "OUTER" ]] "JOIN". parser menemukan OUTER padahal yang diharapkan adalah JOIN, ini merupakan error pada sintaks yang statement nya sudah valid

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```SELECT a.id FROM a LEFT OUTER JOIN b ON b.id = a.id

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

## Bug 3: Error recovery

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di SPESIFIKASI.md disebutkan bahwa panic mode itu membuang token sampai dan termasuk ; berikutnya, lanjutkan ke statement selanjutnya. error hanya ada di satu statement, statement valid sesudah error tetap di proses. di campuran_error.sql setelah error di baris 4, statement baris 6 (UPDATE) dan baris 8 (DELETE) hilang dari matrix jadi terlewat di evaluate.py

**Reproduksi minimal.** SQL terpendek yang memicu bug:

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

## Bug 4: analyzer.py - Subquerry di UPDATE

**Ditemukan oleh:** Abhidal · **Diperbaiki oleh:** Abhidal

**Gejala.** di spesifikasi membaca tabel lewat subquerry selalu R, apapun jenis statement luarnya. dalam audit.sql baris 20:UPDATE pesanan ... IN (SELECT id FROM pelanggan ...) menghasilkan pelanggan: U, seharusnya pelanggan: R (pesanan U). Begitu juga laporan_penjualan.sql baris 12.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```UPDATE t SET a = 1 WHERE id IN (SELECT id FROM u)

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

**Peran AI.** AI menemukan bug, diverifikasi dengan membaca ulang spek, menjalankan audit.sql dan laporan_penjualan.sql dan mencocokkan dengan label manual
---
