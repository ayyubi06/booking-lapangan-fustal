"""Unit test + integration test Sistem Booking Lapangan Futsal.

Unit test: tiap fungsi logika diuji terpisah (black-box, berdasarkan spesifikasi).
Integration test: alur antar modul (logika bisnis x penyimpanan JSON) diuji
bekerjasama memakai direktori sementara (tmp_path).
"""

import json
from datetime import date, timedelta

import pytest

from booking import (
    batalkan_booking,
    buat_booking,
    cek_bentrok,
    hitung_total,
    jadwal_tanggal,
    ke_menit,
    muat_data,
    simpan_data,
    tambah_lapangan,
    validasi_tanggal,
)


def contoh_data():
    return {
        "lapangan": [{"id": "L1", "nama": "Lapangan A", "tarif": 50000}],
        "booking": [
            {"id": "B1", "id_lapangan": "L1", "nama": "Budi",
             "tanggal": "2026-10-20", "mulai": "16:00", "selesai": "18:00",
             "total": 100000, "status": "aktif"},
        ],
    }


BESOK = (date.today() + timedelta(days=1)).isoformat()
KEMARIN = (date.today() - timedelta(days=1)).isoformat()


# ------------------------------------------------------------- util & validasi

def test_ke_menit_valid():
    assert ke_menit("16:30") == 990


def test_ke_menit_format_salah():
    with pytest.raises(ValueError):
        ke_menit("16.30")
    with pytest.raises(ValueError):
        ke_menit("25:00")


def test_validasi_tanggal_format_salah():
    with pytest.raises(ValueError):
        validasi_tanggal("20-10-2026")


# ------------------------------------------------------------ deteksi bentrok

def test_tidak_bentrok_slot_berbeda():
    d = contoh_data()
    assert cek_bentrok(d["booking"], "L1", "2026-10-20", "18:00", "20:00") is False


def test_bentrok_overlap_parsial():
    d = contoh_data()
    assert cek_bentrok(d["booking"], "L1", "2026-10-20", "17:00", "19:00") is True


def test_batas_bersentuhan_tidak_bentrok():
    # 18:00 tepat saat booking lama selesai -> boleh
    d = contoh_data()
    assert cek_bentrok(d["booking"], "L1", "2026-10-20", "18:00", "20:00") is False
    assert cek_bentrok(d["booking"], "L1", "2026-10-20", "14:00", "16:00") is False


def test_booking_batal_diabaikan():
    d = contoh_data()
    d["booking"][0]["status"] = "batal"
    assert cek_bentrok(d["booking"], "L1", "2026-10-20", "17:00", "19:00") is False


def test_lapangan_atau_tanggal_beda_tidak_bentrok():
    d = contoh_data()
    assert cek_bentrok(d["booking"], "L2", "2026-10-20", "17:00", "19:00") is False
    assert cek_bentrok(d["booking"], "L1", "2026-10-21", "17:00", "19:00") is False


# -------------------------------------------------------------- hitung total

def test_hitung_total_2_jam():
    assert hitung_total(50000, "16:00", "18:00") == 100000


def test_hitung_total_90_menit_proporsional():
    assert hitung_total(60000, "16:00", "17:30") == 90000


def test_hitung_total_selesai_lebih_dulu():
    with pytest.raises(ValueError):
        hitung_total(50000, "18:00", "16:00")


# ----------------------------------------------------------- buat & batalkan

def test_buat_booking_valid():
    d = contoh_data()
    b = buat_booking(d, "L1", "Ani", BESOK, "19:00", "21:00")
    assert b["id"] == "B2"
    assert b["total"] == 100000
    assert len(d["booking"]) == 2


def test_buat_booking_bentrok_ditolak():
    d = contoh_data()
    with pytest.raises(ValueError, match="bentrok"):
        buat_booking(d, "L1", "Ani", "2026-10-20", "17:00", "19:00")


def test_buat_booking_tanggal_masa_lalu_ditolak():
    d = contoh_data()
    with pytest.raises(ValueError, match="masa lalu"):
        buat_booking(d, "L1", "Ani", KEMARIN, "19:00", "21:00")


def test_buat_booking_lapangan_tak_ada_ditolak():
    d = contoh_data()
    with pytest.raises(ValueError, match="tidak ditemukan"):
        buat_booking(d, "L99", "Ani", BESOK, "19:00", "21:00")


def test_batalkan_booking_ada():
    d = contoh_data()
    assert batalkan_booking(d, "B1") is True
    assert d["booking"][0]["status"] == "batal"


def test_batalkan_booking_tak_ada():
    d = contoh_data()
    assert batalkan_booking(d, "B99") is False


def test_tambah_lapangan_tarif_nol_ditolak():
    with pytest.raises(ValueError):
        tambah_lapangan(contoh_data(), "Lapangan B", 0)


def test_jadwal_tanggal_urut_jam_mulai():
    d = contoh_data()
    buat_booking(d, "L1", "Ani", "2026-10-20", "19:00", "20:00")
    jadwal = jadwal_tanggal(d, "2026-10-20")
    assert [b["id"] for b in jadwal] == ["B1", "B2"]


# ---------------------------------------------------------- integration test

def test_alur_penuh_booking(tmp_path):
    """Tambah lapangan -> booking -> bentrok ditolak -> batalkan ->
    slot bebas lagi -> data tersimpan & bisa dimuat ulang."""
    path = str(tmp_path / "data.json")

    data = muat_data(path)
    lap = tambah_lapangan(data, "Lapangan A", 50000)
    simpan_data(data, path)

    data = muat_data(path)  # modul penyimpanan bekerja sama dengan logika
    b1 = buat_booking(data, lap["id"], "Budi", BESOK, "16:00", "18:00")
    simpan_data(data, path)

    data = muat_data(path)
    with pytest.raises(ValueError, match="bentrok"):
        buat_booking(data, lap["id"], "Ani", BESOK, "17:00", "19:00")

    assert batalkan_booking(data, b1["id"]) is True
    b2 = buat_booking(data, lap["id"], "Ani", BESOK, "17:00", "19:00")
    simpan_data(data, path)

    with open(path) as f:
        mentah = json.load(f)
    assert len(mentah["booking"]) == 2
    assert b2["status"] == "aktif"
    assert mentah["booking"][0]["status"] == "batal"
