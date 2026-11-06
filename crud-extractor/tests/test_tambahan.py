"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

from crud import ast_nodes as ast
from crud.analyzer import analyze_statement
from crud.parser import parse_sql


def one(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    assert len(script.statements) == 1
    return script.statements[0]


# Tes regresi: setiap tes menangkap salah satu bug yang tercatat di LAPORAN_BUG.md.
def test_regresi_presedensi_and_lebih_tinggi_dari_or():
    stmt = one("SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3")

    assert isinstance(stmt.where, ast.BinaryOp)
    assert stmt.where.op == "OR"
    assert isinstance(stmt.where.right, ast.BinaryOp)
    assert stmt.where.right.op == "AND"


def test_regresi_left_outer_join_diterima():
    stmt = one("SELECT a.id FROM a LEFT OUTER JOIN b ON b.id = a.id")

    assert len(stmt.joins) == 1
    assert stmt.joins[0].kind == "LEFT"
    assert stmt.joins[0].source.name == "b"


def test_regresi_error_recovery_melanjutkan_setelah_semikolon():
    script = parse_sql("SELECT id nama, FROM a;\nUPDATE t SET nilai = 1;")

    assert len(script.errors) == 1
    assert len(script.statements) == 1
    assert isinstance(script.statements[0], ast.Update)
    assert script.statements[0].table.name == "t"


def test_regresi_subquery_di_update_dibaca_sebagai_read():
    stmt = one("UPDATE t SET a = 1 WHERE id IN (SELECT id FROM u)")

    assert analyze_statement(stmt) == {"t": {"U"}, "u": {"R"}}


# Lima kasus tepi: masing-masing menguji batas token atau struktur yang rawan.
def test_tepi_statement_boleh_berakhir_di_eof():
    # Statement terakhir tanpa titik koma rawan terbuang di batas akhir input.
    stmt = one("SELECT id FROM pelanggan")

    assert isinstance(stmt, ast.Select)
    assert stmt.sources[0].name == "pelanggan"


def test_tepi_titik_koma_kosong_diabaikan():
    # Separator berulang rawan dianggap sebagai statement kosong yang invalid.
    script = parse_sql(";;; SELECT id FROM pelanggan;;;")

    assert script.errors == []
    assert len(script.statements) == 1


def test_tepi_nama_tabel_dengan_skema_dinormalisasi():
    # Kapitalisasi dan titik skema rawan membuat identitas tabel tidak konsisten.
    stmt = one("UPDATE CRM.Pelanggan SET aktif = 1")

    assert analyze_statement(stmt) == {"crm.pelanggan": {"U"}}


def test_tepi_parameter_named_dan_posisional_dikenali():
    # Parameter tanpa nama dan bernama rawan keliru diparse sebagai operator/kolom.
    stmt = one("UPDATE produk SET stok = :stok WHERE id = ?")

    assert isinstance(stmt.assignments[0].value, ast.Param)
    assert isinstance(stmt.where.right, ast.Param)


def test_tepi_keyword_di_dalam_string_bukan_tabel():
    # Kata mirip sintaks SQL dalam literal rawan disalahartikan sebagai sumber tabel.
    stmt = one("SELECT catatan FROM log WHERE catatan = 'JOIN pelanggan'")

    assert analyze_statement(stmt) == {"log": {"R"}}
