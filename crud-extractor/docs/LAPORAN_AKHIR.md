# Laporan Akhir

## 1. Hasil evaluasi

Keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi (27 triple, 4 berkas):

```
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```

**Interpretasi.** Parser tepat pada seluruh 27 triple (precision, recall, dan F1 sama-sama 1,00).
Regex benar pada 22 triple, sehingga precision-nya 0,65 (22 dari 34 prediksi) dan recall-nya 0,81
(22 dari 27 label). Precision lebih rendah daripada recall karena regex lebih sering melaporkan
terlalu banyak daripada terlewat: dari 12 prediksi salah, 4 adalah target `DELETE` yang ikut
ditandai `R`, 4 adalah tabel yang benar tetapi bernomor baris keliru, 2 berasal dari isi
komentar, 1 dari isi string, dan 1 dari statement yang gagal di-parse. Dari 5 triple yang
terlewat, 4 adalah pasangan dari kesalahan nomor baris tadi, dan 1 adalah tabel `pesanan` pada
`FROM pelanggan p, pesanan o` di `audit.sql` baris 2.

## 2. Tiga kasus di mana regex salah

1. **`FROM` di dalam string dianggap sebagai tabel**

   `laporan_penjualan.sql`, baris 3-7:

   ```sql
   SELECT p.nama, SUM(o.total) AS omzet
   FROM pelanggan p
   JOIN pesanan o ON o.pelanggan_id = p.id
   WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
   GROUP BY p.nama;
   ```

   Regex mencari pola `FROM <nama>` di seluruh teks tanpa membedakan string dari sintaks, sehingga
   menghasilkan FP `('laporan_penjualan.sql', 2, 'rahasia', 'R')`. Tabel `pelanggan` dan `pesanan`
   memang dibaca, jadi keduanya bukan kesalahan di kasus ini. Pada tahap **lexing** (Bab 4),
   lexer membaca literal dari kutip pembuka sampai kutip penutup sebagai satu token `STRING`
   bernilai `FROM rahasia`; token itu tidak pernah menjadi keyword `FROM`. Saat **parsing**
   (Bab 6), aturan `FROM table_ref` hanya menerima identifier atau subquery, sehingga `rahasia`
   tidak mungkin menjadi tabel.

2. **Perintah di dalam komentar, beserta pergeseran nomor baris**

   `laporan_penjualan.sql`, baris 2-3:

   ```sql
   -- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
   SELECT p.nama, SUM(o.total) AS omzet
   ```

   `pemeliharaan.sql`, baris 1-3:

   ```sql
   /* Skrip pemeliharaan data pelanggan.
      Catatan lama: UPDATE pelanggan_lama sudah tidak dipakai. */
   select c.id, c.nama, a.kota
   ```

   Regex membuat dua kesalahan. Pertama, isi komentar dianggap perintah: muncul FP
   `pelanggan: D` (laporan_penjualan.sql baris 2) dan `pelanggan_lama: U` (pemeliharaan.sql
   baris 2), padahal tidak ada statement seperti itu. Kedua, tabel dari `SELECT` yang asli
   dilaporkan di baris 2 (baris komentar), bukan baris 3 tempat `SELECT` dimulai. Karena evaluasi
   membandingkan `(file, baris, tabel, operasi)`, satu kesalahan nomor baris dihitung dua kali:
   FP `(2, pelanggan, R)` dan `(2, pesanan, R)` berpasangan dengan FN `(3, pelanggan, R)` dan
   `(3, pesanan, R)`; hal yang sama terjadi pada `crm.alamat` dan `crm.pelanggan` di
   `pemeliharaan.sql`. Lexer melewati komentar sebagai trivia (Bab 4): `--` sampai akhir
   baris dan `/* ... */` lintas baris tidak menghasilkan token, tetapi penghitung baris tetap maju
   pada setiap karakter. Token `SELECT` karena itu berposisi baris 3, dan statement mencatat baris
   dari token tersebut.

3. **Target `DELETE` ikut ditandai sebagai tabel yang dibaca**

   `campuran_error.sql`, baris 8:

   ```sql
   DELETE FROM keranjang WHERE dibuat < :batas;
   ```

   Pola `FROM <nama>` pada regex memberi `keranjang: R`, di samping `keranjang: D` yang benar,
   sehingga satu target terhitung sebagai R dan D. Pola yang sama muncul empat kali:
   `audit.sql` baris 16 (`sesi`), `campuran_error.sql` baris 8 (`keranjang`),
   `laporan_penjualan.sql` baris 15 (`pesanan`), dan `pemeliharaan.sql` baris 15 (`crm.alamat`).
   Parser mengenali `DELETE FROM` sebagai satu produksi `delete_stmt` (Bab 5 dan 6) dan
   membentuk node `Delete` dengan `keranjang` sebagai `table`. Analyzer menandai target itu hanya
   `D`; `FROM` di sini bagian dari aturan `DELETE`, bukan awal sebuah `SELECT`.

## 3. Batas pendekatan kami

Tiga hal yang tidak bisa ditangani dengan benar oleh tool ini meskipun semua bug sudah
diperbaiki:

1. **SQL dinamis yang dirakit saat aplikasi berjalan.** Tool membaca file SQL, bukan kode
   aplikasi. Bila aplikasi menggabungkan `"SELECT * FROM "` dengan nama tabel dari konfigurasi,
   nama tabel itu baru ada saat program berjalan dan tidak pernah muncul sebagai identifier pada
   SQL yang dianalisis. Akibatnya tabel tersebut tidak tercatat di CRUD matrix. Untuk
   menanganinya dibutuhkan nilai konfigurasi saat runtime dan analisis jalur kode yang
   merakit atau mengeksekusi query.

2. **View tanpa informasi definisinya.**

   ```sql
   SELECT * FROM v_laporan;
   ```

   Matrix hanya dapat menandai `v_laporan: R`; tabel dasar yang dibaca oleh view tidak
   diketahui. Untuk menurunkan operasi sampai ke tabel dasar, tool membutuhkan definisi view
   dari database dan perlu menelusuri view bertingkat.

3. **Efek samping trigger dan foreign key cascade.**

   ```sql
   DELETE FROM pelanggan WHERE id = 7;
   ```

   Dari statement ini saja matrix menandai `pelanggan: D`. Jika database menghapus baris terkait
   di `pesanan` melalui `ON DELETE CASCADE`, atau trigger menulis ke `audit_log`, operasi pada
   tabel-tabel tersebut tidak tercatat. Untuk memasukkannya dibutuhkan skema foreign key,
   definisi trigger, serta informasi apakah aturan tersebut aktif pada database yang dianalisis.

## 4. Pembagian kerja

Pembagian kerja yang dicatat kelompok:

- **Abhidal:** `parser.py`, `ast_nodes.py`, dan `analyzer.py`; menangani Bug 6-9
  (presedensi `AND`/`OR`, `LEFT OUTER JOIN`, error recovery, dan pembacaan subquery pada
  `UPDATE`) serta TODO T1 (`INSERT ... SELECT`).
- **Zidane:** `lexer.py`, `resolver.py`, `pipeline.py`, `cli.py`, dan `evaluate.py`;
  menangani Bug 1-5 (keyword tidak peka kapitalisasi, operator `<>`, escape string `''`,
  urutan lookup scope, dan scope `DELETE`) serta TODO T2 (resolusi kolom tanpa qualifier)
  dan T3 (komentar blok).

Pembagian ini mengikuti ukuran dan tanggung jawab modul: parser merupakan modul terbesar,
sementara lexer perlu diselesaikan lebih dulu karena parser bergantung pada token yang benar.
Ketiga TODO yang tercatat pada `LAPORAN_BUG.md` kini sudah diimplementasikan.

Untuk memastikan kedua anggota memahami seluruh pekerjaan, kami melakukan:

1. **Saling-ajar:** tiap anggota menjelaskan kepada anggota lain apa yang dikerjakan, apa yang
   salah, dan apa yang diperbaiki.
2. **Review bersama:** kedua anggota mencocokkan hasil dengan spesifikasi dan saling mengkritisi
   pekerjaan masing-masing.
3. **Demo singkat:** untuk memeriksa pemahaman setiap anggota.

Penggunaan AI dicatat di `docs/LOG_AI.md` dan pada bagian "Peran AI" di setiap entri
LAPORAN_BUG.md.

## 5. Status verifikasi

Suite pengujian saat ini lulus **44 tes** (`python -m pytest -q`). Evaluasi terhadap
27 triple di empat berkas berlabel menghasilkan parser precision/recall/F1 **1.00/1.00/1.00**
dan baseline regex **0.65/0.81/0.72** (`python evaluate.py`). Hasil evaluasi lengkap tercantum
di bagian 1.

## 6. Rujukan

Nystrom, Robert. *Crafting Interpreters*. Genever Benning, 2021.
https://craftinginterpreters.com

Konsep dan istilah yang dipakai dalam laporan ini diambil dari bab berikut:

- Bab 4 (*Scanning*): lexeme, maximal munch, lookahead, dan komentar sebagai trivia.
- Bab 5 (*Representing Code*): grammar dan AST.
- Bab 6 (*Parsing Expressions*): recursive descent, presedensi, dan error recovery (panic mode).
- Bab 11 (*Resolving and Binding*): scope dan resolusi nama.

Buku tersebut membahas bahasa Lox; kami menerapkan konsepnya pada subset SQL.