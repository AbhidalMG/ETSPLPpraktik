# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text

```

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1.
2.
3.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1.
2.
3.

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
