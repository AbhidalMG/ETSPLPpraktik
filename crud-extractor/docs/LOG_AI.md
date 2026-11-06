# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

Keterangan kolom: **Pemberi prompt** = anggota yang meminta; **Pelaksana** = AI atau tool yang menjalankan;
**Hasil** = Diterima / Diterima dengan edit / Ditolak. Nomor bug mengikuti `docs/LAPORAN_BUG.md`.

## A. Temuan bug dari audit kode (tiap temuan diverifikasi oleh anggota)

| No | Pemberi prompt | Pelaksana | Prompt singkat | Hasil | Alasan dan verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Zidane | AI | Audit `lexer.py` terhadap spek 2.2: apakah keyword huruf kecil dikenali? (Bug 1, L1) | Diterima | Spek 2.2 mewajibkan keyword tidak peka huruf besar/kecil. Verifikasi: test terlihat `test_keyword_huruf_kecil` gagal sebelum perbaikan, token `select`, `Select`, `selection`, `fromage` diperiksa manual, `pemeliharaan.sql` dijalankan ulang. |
| 2 | Zidane | AI | Audit `lexer.py` terhadap spek 2.5: apakah `<>` menjadi satu token? (Bug 2, L2) | Diterima | Spek 2.5 (maximal munch). Verifikasi: `laporan_penjualan.sql` dijalankan ulang (error baris 6 hilang, statement SELECT masuk matrix) dan `evaluate.py` untuk file berlabel. |
| 3 | Zidane | AI | Audit `lexer.py` terhadap spek 2.4: apakah `''` di dalam string ditangani? (Bug 3, L3) | Diterima | Spek 2.4 (satu token `STRING` bernilai `O'Brien`). Verifikasi: `'O''Brien'` menjadi satu STRING, `''` tetap string kosong, `'a'''` bernilai `a'`, `pemeliharaan.sql` diproses tanpa error. |
| 4 | Zidane | AI | Audit `resolver.py` terhadap spek 4.3: apakah alias dalam menutupi alias luar? (Bug 5, R1) | Diterima | Pencarian scope dimulai dari yang terluar sehingga shadowing hilang. Verifikasi: `--ast` pada `audit.sql` menunjukkan `x.pelanggan_id` menuju `pesanan`, dan correlated subquery tetap resolve ke tabel luar. |
| 5 | Zidane | AI | Audit `resolver.py` terhadap spek 4.5: apakah tidak ada scope tersisa antar statement? (Bug 6, R2) | Diterima | `_delete` memanggil `_push` tanpa `_pop`. Verifikasi: setelah `DELETE` dan `UPDATE`, `Resolver.scope` bernilai `None`, dan `audit.sql` baris 18 menghasilkan error alias `s`. |
| 6 | Abhidal | AI | Audit `parser.py` terhadap tabel presedensi spek 3.1: apakah AND lebih kuat dari OR? (Bug 8, P1) | Diterima | Satu fungsi `_logical` menyamakan tingkat AND dan OR, melanggar grammar. Verifikasi: cetak AST dengan `--ast`, cek ulang spek dan tabel presedensi, test `test_regresi_parser_and_lebih_kuat_dari_or`. |
| 7 | Abhidal | AI | Bandingkan `_join` dengan aturan `join` di grammar: apakah `LEFT OUTER JOIN` diterima? (Bug 9, P2) | Diterima | `OUTER` tidak dikonsumsi sehingga statement valid ditolak. Verifikasi: membandingkan `_join` dengan baris `join` di grammar, menjalankan `pemeliharaan.sql` dan memeriksa `crm.alamat` masuk sebagai R. |
| 8 | Abhidal | AI | Audit error recovery `parser.py` terhadap spek bagian 6 (Bug 10, P3) | Diterima | Recovery membuang token sampai EOF, padahal harus berhenti setelah `;`. Verifikasi: `campuran_error.sql` kini menghasilkan 1 error dan 3 statement (baris 2, 6, 8), `evaluate.py` memberi recall parser 1.00 untuk file berlabel. |
| 9 | Abhidal | AI | Audit `analyzer.py` terhadap spek bagian 5: operasi tabel di subquery UPDATE (Bug 12, A1) | Diterima | Cabang UPDATE meneruskan `U` ke subquery, padahal subquery selalu R. Verifikasi: baca ulang spek, jalankan `audit.sql` dan `laporan_penjualan.sql`, cocokkan dengan label manual di `ground_truth.csv`. |

Catatan: ganti "AI" dengan nama tool yang benar-benar dipakai. Tambahkan baris untuk T1, T2, dan T3 bila AI
dipakai pada bagian itu; jika tidak, tidak perlu dicatat.

## B. Dokumen dan evaluasi

| No | Pemberi prompt | Pelaksana | Prompt singkat | Hasil | Alasan dan verifikasi |
| --- | --- | --- | --- | --- | --- |
| 10 | Abhidal | Claude | Isi `KARTU_DESAIN.md` tanpa mengubah struktur, lalu ringkaskan | Diterima dengan edit | Draf ditulis dari spesifikasi, bukan dari kode kami. Verifikasi: dicocokkan dengan implementasi `parser.py` dan `resolver.py` (nama fungsi, `if` pada `comparison`, penanganan `COUNT(*)`) dan disesuaikan: [ISI perubahan yang dibuat]. |
| 11 | Abhidal | Claude | Cara melabeli `audit.sql` dan `pemeliharaan.sql` di `ground_truth.csv` | Diterima | Hanya panduan langkah dan jebakan (alias, subquery R, komentar/string). Label tetap ditulis manual dari spek 5, bukan dari output tool. Verifikasi: saling periksa label antar anggota, lalu `evaluate.py`: [ISI]. |
| 12 | Abhidal | Claude | Apakah output `evaluate.py` sudah sesuai setelah debugging dan TODO? | Diterima | AI menilai arah sudah benar tetapi belum selesai (dua file belum berlabel, saat itu). Verifikasi: setelah label lengkap, `evaluate.py` mencakup 4 file (27 triple), parser 1.00/1.00/1.00, regex 0.65/0.81/0.72, sama dengan yang ditempel di `LAPORAN_AKHIR.md` bagian 1. |
| 13 | Abhidal | Claude | Periksa kelengkapan `LAPORAN_BUG`, `KARTU_DESAIN`, `LAPORAN_AKHIR`, `LOG_AI` | Diterima dengan edit | AI menemukan entri `LAPORAN_BUG` tertukar (isi tidak sesuai judul/ID), placeholder `[ISI]`, dan contoh `LAPORAN_AKHIR` bagian 2 yang tidak cocok dengan FP/FN. Verifikasi: kami membandingkan judul tiap entri dengan tabel ringkasan dan contoh SQL dengan output `evaluate.py`, lalu memperbaikinya sendiri: [ISI]. |
| 14 | Abhidal | Claude | Tinjau draf `LAPORAN_BUG`, lalu gabungkan ke struktur sebelumnya tanpa mengubah entri tulisan Abhidal | Diterima dengan edit | AI hanya memindahkan entri ke judul yang benar, memperbaiki format Markdown, dan menyelaraskan istilah. Verifikasi: kami membaca ulang tiap entri terhadap spek dan kode, dan akar masalah ditulis ulang dengan kata sendiri: [ISI]. |
| 15 | Abhidal | Claude | Rapikan `LOG_AI.md` menjadi tabel bertahap, lalu sesuaikan penomoran bug | Diterima dengan edit | Struktur tabel dari AI. Isi kolom verifikasi hanya yang benar-benar kami lakukan; sisanya kami lengkapi sendiri. |


**Refleksi (3-5 kalimat).** AI paling membantu saat membandingkan satu fungsi dengan satu aturan grammar atau spek
(misalnya `_join`, presedensi AND/OR, recovery), karena menunjuk ke kode yang harus diperiksa. Namun AI tidak
melihat kode kami saat membuat draf Kartu Desain, sehingga isinya baru bisa dipercaya setelah kami cocokkan dengan
implementasi. AI juga tidak menjamin dokumen konsisten: entri `LAPORAN_BUG` ternyata tertukar dan baru terlihat saat
judulnya dibandingkan dengan isinya. Karena itu akar masalah kami tulis ulang dengan kata sendiri dan setiap
perbaikan diverifikasi dengan test yang gagal dulu, lalu lulus. [ISI: satu kasus di mana saran AI keliru atau
ditolak, dan bagaimana kami mengetahuinya.]
