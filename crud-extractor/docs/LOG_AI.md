# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

Keterangan kolom: **Pemberi prompt** = anggota yang meminta; **Pelaksana** = AI atau tool yang menjalankan;
**Hasil** = Diterima / Diterima dengan edit / Ditolak. Nomor bug mengikuti `docs/LAPORAN_BUG.md`.

## A. Temuan bug dari audit kode (tiap temuan diverifikasi oleh anggota)

| No | Pemberi prompt | Pelaksana | Prompt singkat | Hasil | Alasan dan verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Zidane | Claude | Audit `lexer.py` terhadap spek 2.2: apakah keyword huruf kecil dikenali? (Bug 1, L1) | Diterima | Spek mewajibkan keyword tidak peka kapitalisasi dan dinormalisasi. Verifikasi regresi: `test_regresi_lexer_keyword_huruf_kecil_dinormalisasi` dan `test_keyword_huruf_kecil`; `pemeliharaan.sql` terproses. |
| 2 | Zidane | Claude | Audit `lexer.py` terhadap spek 2.5: apakah `<>` menjadi satu token? (Bug 2, L2) | Diterima | `<>` harus menjadi satu token OP. Verifikasi regresi: `test_regresi_lexer_operator_tidak_sama_satu_token`; evaluasi seluruh data juga dijalankan. |
| 3 | Zidane | Claude | Audit `lexer.py` terhadap spek 2.4: apakah `''` di dalam string ditangani? (Bug 3, L3) | Diterima | `''` di dalam string menjadi satu kutip pada nilai token. Verifikasi regresi: `test_regresi_lexer_kutip_ganda_dalam_string`; `pemeliharaan.sql` terparse tanpa error. |
| 4 | Zidane | Claude | Audit `resolver.py` terhadap spek 4.3: apakah alias dalam menutupi alias luar? (Bug 4, R1) | Diterima | Lookup harus dimulai dari scope terdalam. Verifikasi regresi: `test_regresi_resolver_alias_dalam_menutupi_alias_luar`. |
| 5 | Zidane | Claude | Audit `resolver.py` terhadap spek 4.5: apakah scope bersih antar statement? (Bug 5, R2) | Diterima | Scope DELETE harus di-pop agar alias sebelumnya tidak bocor. Verifikasi regresi: `test_regresi_resolver_scope_delete_tidak_bocor`. |
| 6 | Abhidal | Claude | Audit `parser.py` terhadap presedensi spek 3.1: apakah AND lebih kuat dari OR? (Bug 6, P1) | Diterima | Presedensi diimplementasikan lewat fungsi bertingkat. Verifikasi regresi: `test_regresi_presedensi_and_lebih_tinggi_dari_or`. |
| 7 | Abhidal | Claude | Bandingkan `_join` dengan grammar: apakah `LEFT OUTER JOIN` diterima? (Bug 7, P2) | Diterima | Parser mengonsumsi `OUTER` opsional. Verifikasi regresi: `test_regresi_left_outer_join_diterima` dan pemrosesan `pemeliharaan.sql`. |
| 8 | Abhidal | Claude | Audit error recovery terhadap spek bagian 6 (Bug 8, P3) | Diterima | Panic mode berhenti di `;` dan meneruskan statement selanjutnya. Verifikasi regresi: `test_regresi_error_recovery_melanjutkan_setelah_semikolon`. |
| 9 | Abhidal | Claude | Audit operasi tabel di subquery UPDATE (Bug 9, A1) | Diterima | Tabel yang dibaca subquery harus `R`, terpisah dari target `U`. Verifikasi regresi: `test_regresi_subquery_di_update_dibaca_sebagai_read`; hasil sampel cocok dengan label evaluasi. |

## B. Dokumen dan evaluasi

| No | Pemberi prompt | Pelaksana | Prompt singkat | Hasil | Alasan dan verifikasi |
| --- | --- | --- | --- | --- | --- |
| 10 | Abhidal | Claude | Isi `KARTU_DESAIN.md` tanpa mengubah struktur, lalu ringkaskan | Diterima dengan edit | Kartu memuat lima keputusan desain. Dalam peninjauan dokumen ini, keputusan terkait token `STAR`, presedensi ekspresi, recovery, scope, dan kolom tanpa qualifier dicocokkan dengan implementasi yang ada. |
| 11 | Abhidal | Claude | Panduan melabeli `audit.sql` dan `pemeliharaan.sql` di `ground_truth.csv` | Diterima | Label mencakup kedua file. Verifikasi yang dapat diulang: `evaluate.py` membaca empat file dan 27 triple, dengan parser precision/recall/F1 1.00/1.00/1.00. |
| 12 | Abhidal | Claude | Tinjau hasil evaluasi setelah label dilengkapi | Diterima | Hasil `evaluate.py` saat ini: empat file dan 27 triple; parser 1.00/1.00/1.00, baseline regex 0.65/0.81/0.72. Output sama dengan bagian hasil evaluasi pada `LAPORAN_AKHIR.md`. |
| 13 | Abhidal | Claude | Periksa kelengkapan `LAPORAN_BUG`, `KARTU_DESAIN`, `LAPORAN_AKHIR`, `LOG_AI` | Diterima dengan edit | Peninjauan menemukan penomoran, nama tes, status TODO, dan placeholder yang tidak konsisten. Dokumen diperbarui; suite pengujian terakhir lulus 44 tes dan hasil evaluasi dicocokkan kembali. |
| 14 | Abhidal | Claude | Tinjau isi dan susunan `LAPORAN_BUG.md` | Diterima dengan edit | Laporan disusun menjadi Bug 1-9 dan TODO T1-T3. Referensi tes diganti agar sesuai nama fungsi tes yang tersedia di `tests/`. |
| 15 | Abhidal | Claude | Rapikan `LOG_AI.md` dan samakan penomoran bug | Diterima dengan edit | Nomor pada entri audit diselaraskan dengan Bug 1-9; placeholder diganti dengan hasil yang dapat diverifikasi. |
| 16 | Abhidal | Copilot SDK | Selaraskan `LAPORAN_BUG.md`, `LAPORAN_AKHIR.md`, dan `LOG_AI.md` dengan kode dan tes saat ini | Diterima dengan edit | Referensi tes dicek terhadap suite, TODO dipetakan ke implementasi serta tes yang tersedia, nomor bug diseragamkan, dan placeholder dihapus. Verifikasi: `pytest` terakhir 44 passed; evaluasi terakhir mencakup 27 triple dengan parser F1 1.00. |


**Refleksi (3-5 kalimat).** AI paling membantu saat membandingkan fungsi dengan aturan grammar atau spek, misalnya
`_join`, presedensi AND/OR, dan recovery, karena hal itu mengarahkan pemeriksaan ke kode yang relevan. Draf
Kartu Desain tetap perlu dicocokkan dengan implementasi sebelum dipakai sebagai dokumentasi. Satu koreksi konkret
adalah nama beberapa test regresi yang tercantum di draf laporan ternyata tidak ada di suite; pencarian nama test
menunjukkan perbedaan itu, lalu referensi dokumentasi diselaraskan dengan tes aktual. Hasil pengujian dan evaluasi
menjadi bukti yang dapat diulang untuk status kode saat ini.
