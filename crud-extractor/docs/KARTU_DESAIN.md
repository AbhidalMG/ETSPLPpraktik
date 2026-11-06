# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Lexer selalu memberi token `STAR`; parser menentukan artinya dari posisi: tepat setelah `SELECT`/`DISTINCT` = semua kolom, di `COUNT(*)` = argumen khusus, selain itu = perkalian di tingkat `multiplicative`. | Lexer membedakan dua token lewat lookbehind; regex pada teks mentah. | Lexer tidak punya konteks sintaks. Beda arti `*` adalah soal grammar, dan satu token lookahead di parser sudah cukup. |
| 2 | Presedensi dinyatakan lewat fungsi bertingkat, satu per aturan grammar: `or` → `and` → `not` → `comparison` → `additive` → `multiplicative` → `unary` → `primary`. `comparison` memakai `if` (tidak berantai); batas `BETWEEN` dibaca sebagai `additive`. | Pratt parser dengan tabel prioritas; satu fungsi ekspresi datar. | Padanan 1:1 dengan spek bagian 3, mudah diaudit. `AND` lebih kuat dari `OR` karena dipanggil lebih dalam. Versi datar tidak bisa mewakili tingkat dan asosiatif berbeda. |
| 3 | Panic mode: setelah `ParseError`, buang token sampai dan termasuk `;`, catat satu error, lanjut ke statement berikutnya. | Sinkronisasi di keyword `SELECT`/`INSERT` berikutnya; berhenti di error pertama. | `;` pembatas statement yang pasti. `SELECT` bisa muncul di subquery dan `INSERT ... SELECT`, sehingga memecah satu error jadi banyak. Berhenti di error pertama menghilangkan statement valid sesudahnya. |
| 4 | Scope chain: `SELECT`, `UPDATE`, `DELETE` membuat scope baru berinduk. Qualifier dicari dari scope terdalam ke luar, yang pertama ditemukan dipakai. Scope dibuang setelah tiap statement. | Tabel simbol datar global; pencarian dari scope terluar; larangan alias sama antar level. | Satu aturan menghasilkan shadowing dan correlated subquery sekaligus. Tabel datar membuat alias saling menimpa dan bocor antar statement (spek 4.5). |
| 5 | Kolom tanpa qualifier hanya dilihat di scope terdalam: satu tabel → di-resolve; lebih dari satu → warning ambigu, `resolved` = `None`; tidak ada tabel → warning. | Naik ke scope luar; menebak tabel pertama; memakai skema database. | Tanpa skema pemilik kolom tidak bisa dipastikan; menebak membuat hasil salah secara diam-diam. Kelemahan: join dua tabel tanpa qualifier selalu ambigu, dan kolom luar tanpa qualifier di correlated subquery tidak ter-resolve. |
