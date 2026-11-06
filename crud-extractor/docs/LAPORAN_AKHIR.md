# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

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

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1. **`FROM` di dalam string dianggap sebagai tabel oleh regex**

   ```sql
   SELECT nama FROM pelanggan WHERE catatan = 'FROM rahasia';
   ```

   Regex mencari pola `FROM <nama>` di teks tanpa membedakan sintaks SQL, sehingga
   menandai `pelanggan` dan `rahasia` sebagai tabel yang dibaca (R). Parser hanya
   menghasilkan `pelanggan: R`: pada tahap **lexing**, seluruh `'FROM rahasia'`
   menjadi satu token `STRING`, bukan token `FROM` diikuti nama tabel. Karena itu
   pola tersebut tidak menjadi sumber tabel saat **parsing**.

2. **`FROM` di dalam komentar dianggap sebagai tabel oleh regex**

   ```sql
   -- FROM pelanggan_lama
   SELECT nama FROM pelanggan;
   ```

   Regex tidak menghapus atau mengenali komentar, sehingga turut mengeluarkan
   `pelanggan_lama: R` selain `pelanggan: R`. Lexer mengabaikan komentar satu
   baris (`--` sampai akhir baris); parser hanya menerima `pelanggan` sebagai
   sumber `SELECT`. Ini menunjukkan pentingnya **lexing** sebelum mencari struktur
   sintaksis.

3. **Target `DELETE` juga keliru ditandai sebagai tabel yang dibaca**

   ```sql
   DELETE FROM keranjang WHERE dibuat < :batas;
   ```

   Pola regex `FROM <nama>` memberi `keranjang: R`, sementara pola
   `DELETE FROM <nama>` juga memberi `keranjang: D`; akibatnya satu target
   terhitung sebagai R dan D. Parser mengenali produksi **parsing** `DELETE`,
   membentuk node `Delete` dengan `keranjang` sebagai target, lalu analyzer
   menandai target itu hanya D. Kondisi `WHERE` tidak mengubah peran target
   menjadi tabel yang dibaca.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1. **SQL dinamis yang dibentuk saat aplikasi berjalan.** Misalnya aplikasi
   menggabungkan `"SELECT * FROM "` dengan nilai `nama_tabel` dari konfigurasi.
   Nama tabel tidak muncul sebagai identifier di SQL statis yang dianalisis,
   sehingga CRUD matrix tidak dapat mencantumkan tabel yang benar-benar dibaca
   (atau dapat tidak memprosesnya jika bentuk SQL yang dianalisis bukan subset
   yang didukung). Untuk menanganinya dibutuhkan nilai konfigurasi/runtime dan
   jalur kode yang membentuk atau mengeksekusi query.

2. **View tanpa informasi definisinya.**

   ```sql
   SELECT * FROM v_laporan;
   ```

   Matrix hanya dapat menandai `v_laporan: R`; tabel dasar yang dibaca oleh view
   tidak diketahui. Untuk menurunkan operasi sampai ke tabel dasar, tool
   membutuhkan definisi view dari database dan perlu menelusuri view bertingkat.

3. **Efek samping trigger dan foreign key cascade.**

   ```sql
   DELETE FROM pelanggan WHERE id = 7;
   ```

   Dari statement ini saja matrix menandai `pelanggan: D`. Jika database
   menghapus baris terkait di `pesanan` melalui `ON DELETE CASCADE`, atau trigger
   menulis ke `audit_log`, operasi pada tabel-tabel tersebut tidak tercatat.
   Untuk memasukkannya dibutuhkan skema foreign key, definisi trigger, serta
   informasi apakah aturan tersebut aktif pada database yang dianalisis.

## 4. Pembagian kerja

Pembagian kerja kami lakukan dengan membagikan masing-masing anggota modul untuk diperbaiki dengan pembagian sebagai berikut
Abhidal:
parser.py, ast_nodes.py dan analyzer.py

Zidane:
lexer.py, resolver.py, pipeline.py/cli.py, evaluate.py

Alasan pembagian: parser adalah file terbesar (±14 KB) ditambah analyzer, sedangkan lexer + resolver +
pipeline lebih kecil tetapi mencakup dua TODO. Lexer dikerjakan lebih dulu karena
parser bergantung pada token yang benar.

Modul dibagi dan dikerjakan secara pararel, untuk memastikan pemahaman antar anggota kami lakukan dengan:
1. Melakukan saling-ajar atau setiap anggota akan menjelaskan apa yang dikerjakan, apa yang salah dan apa yang diperbaiki kepada anggota yang lain.
2. Review ulang bersama sama: kedua anggota kelompok akan melakukan review dnegan mencocokan dengan spesifikasi dan saling mengkritisi
pekerjaan tiap anggota
3. Melakukan demo singkat untuk mengetahui pemahaman setiap anggota kelompok
