"""
Sistem Booking Lapangan Futsal - Final Project
Mata kuliah: Analisis & Pengujian Sistem (Pertemuan 5: High Order Testing)

Fitur:
- Kelola lapangan (tambah, lihat) beserta tarif sewa per jam
- Buat booking dengan deteksi otomatis jadwal bentrok
- Hitung total bayar otomatis (durasi x tarif)
- Batalkan booking
- Lihat jadwal booking per tanggal
- Data tersimpan di data.json

Struktur 3 lapis:
  CLI (menu) -> logika bisnis (fungsi-fungsi di bawah) -> penyimpanan JSON
"""

import json
import os
from datetime import datetime, date

DATA_FILE = "data.json"


# ---------------------------------------------------------------- util waktu

def ke_menit(jam):
    """Ubah 'HH:MM' menjadi menit sejak 00:00. ValueError jika format salah."""
    try:
        h, m = jam.split(":")
        h, m = int(h), int(m)
    except (ValueError, AttributeError):
        raise ValueError("Format jam salah: %r (gunakan HH:MM)" % (jam,))
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("Jam tidak valid: %r" % (jam,))
    return h * 60 + m


def validasi_tanggal(tgl):
    """Pastikan format YYYY-MM-DD. ValueError jika salah."""
    try:
        datetime.strptime(tgl, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("Format tanggal salah: %r (gunakan YYYY-MM-DD)" % (tgl,))


# ------------------------------------------------------------ logika bisnis

def cek_bentrok(bookings, id_lapangan, tanggal, mulai, selesai):
    """True jika rentang [mulai, selesai) bentrok dengan booking AKTIF lain
    pada lapangan dan tanggal yang sama.

    Aturan batas: booking yang selesai tepat saat booking lain mulai
    (bersentuhan) TIDAK dianggap bentrok.
    """
    m1, s1 = ke_menit(mulai), ke_menit(selesai)
    for b in bookings:
        if b["id_lapangan"] != id_lapangan or b["tanggal"] != tanggal:
            continue
        if b.get("status") == "batal":
            continue
        m2, s2 = ke_menit(b["mulai"]), ke_menit(b["selesai"])
        if m1 < s2 and m2 < s1:
            return True
    return False


def hitung_total(tarif_per_jam, mulai, selesai):
    """Total = tarif/jam x durasi (proporsional per menit)."""
    menit = ke_menit(selesai) - ke_menit(mulai)
    if menit <= 0:
        raise ValueError("Jam selesai harus setelah jam mulai")
    return round(tarif_per_jam * menit / 60)


def cari_lapangan(data, id_lapangan):
    for l in data["lapangan"]:
        if l["id"] == id_lapangan:
            return l
    return None


def _id_berikutnya(items, prefix):
    angka = [int(x["id"][len(prefix):]) for x in items
             if x["id"].startswith(prefix) and x["id"][len(prefix):].isdigit()]
    return "%s%d" % (prefix, max(angka, default=0) + 1)


def tambah_lapangan(data, nama, tarif):
    """Tambah lapangan baru. ValueError jika nama kosong / tarif <= 0."""
    if not nama or not nama.strip():
        raise ValueError("Nama lapangan tidak boleh kosong")
    if tarif <= 0:
        raise ValueError("Tarif harus lebih dari 0")
    lap = {"id": _id_berikutnya(data["lapangan"], "L"),
           "nama": nama.strip(), "tarif": tarif}
    data["lapangan"].append(lap)
    return lap


def buat_booking(data, id_lapangan, nama, tanggal, mulai, selesai):
    """Buat booking baru. ValueError dengan pesan jelas jika tidak valid."""
    lap = cari_lapangan(data, id_lapangan)
    if lap is None:
        raise ValueError("Lapangan %r tidak ditemukan" % (id_lapangan,))
    if not nama or not nama.strip():
        raise ValueError("Nama pemesan tidak boleh kosong")
    validasi_tanggal(tanggal)
    if tanggal < date.today().isoformat():
        raise ValueError("Tanggal booking tidak boleh di masa lalu")
    ke_menit(mulai)
    ke_menit(selesai)
    if ke_menit(selesai) <= ke_menit(mulai):
        raise ValueError("Jam selesai harus setelah jam mulai")
    if cek_bentrok(data["booking"], id_lapangan, tanggal, mulai, selesai):
        raise ValueError("Jadwal bentrok dengan booking lain "
                         "di %s pada %s %s-%s"
                         % (lap["nama"], tanggal, mulai, selesai))
    booking = {
        "id": _id_berikutnya(data["booking"], "B"),
        "id_lapangan": id_lapangan,
        "nama": nama.strip(),
        "tanggal": tanggal,
        "mulai": mulai,
        "selesai": selesai,
        "total": hitung_total(lap["tarif"], mulai, selesai),
        "status": "aktif",
    }
    data["booking"].append(booking)
    return booking


def batalkan_booking(data, id_booking):
    """Batalkan booking aktif. True jika berhasil, False jika tidak ada."""
    for b in data["booking"]:
        if b["id"] == id_booking and b.get("status") == "aktif":
            b["status"] = "batal"
            return True
    return False


def jadwal_tanggal(data, tanggal):
    """Daftar booking AKTIF pada tanggal tertentu, urut jam mulai."""
    validasi_tanggal(tanggal)
    hasil = [b for b in data["booking"]
             if b["tanggal"] == tanggal and b.get("status") == "aktif"]
    return sorted(hasil, key=lambda b: ke_menit(b["mulai"]))


# --------------------------------------------------------------- penyimpanan

def muat_data(path=DATA_FILE):
    if not os.path.exists(path):
        return {"lapangan": [], "booking": []}
    with open(path) as f:
        return json.load(f)


def simpan_data(data, path=DATA_FILE):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------- CLI

def _tampil_lapangan(data):
    if not data["lapangan"]:
        print("Belum ada lapangan.")
        return
    print("\n--- DAFTAR LAPANGAN ---")
    for l in data["lapangan"]:
        print("%s | %s | Rp%s/jam" % (l["id"], l["nama"], f"{l['tarif']:,}"))


def _tampil_jadwal(data):
    tgl = input("Tanggal (YYYY-MM-DD): ").strip()
    try:
        jadwal = jadwal_tanggal(data, tgl)
    except ValueError as e:
        print("Error:", e)
        return
    if not jadwal:
        print("Tidak ada booking pada %s." % tgl)
        return
    print("\n--- JADWAL %s ---" % tgl)
    for b in jadwal:
        lap = cari_lapangan(data, b["id_lapangan"])
        nama_lap = lap["nama"] if lap else b["id_lapangan"]
        print("%s | %s | %s-%s | %s | Rp%s"
              % (b["id"], nama_lap, b["mulai"], b["selesai"],
                 b["nama"], f"{b['total']:,}"))


def main():
    data = muat_data()
    print("====== SISTEM BOOKING LAPANGAN FUTSAL ======")
    while True:
        print("\n1. Lihat lapangan")
        print("2. Tambah lapangan")
        print("3. Buat booking")
        print("4. Lihat jadwal per tanggal")
        print("5. Batalkan booking")
        print("0. Keluar")
        pilih = input("Pilih: ").strip()
        if pilih == "1":
            _tampil_lapangan(data)
        elif pilih == "2":
            nama = input("Nama lapangan: ")
            try:
                tarif = int(input("Tarif per jam (Rp): "))
                lap = tambah_lapangan(data, nama, tarif)
                simpan_data(data)
                print("Lapangan %s (%s) ditambahkan." % (lap["id"], lap["nama"]))
            except ValueError as e:
                print("Error:", e)
        elif pilih == "3":
            _tampil_lapangan(data)
            try:
                id_lap = input("ID lapangan: ").strip()
                nama = input("Nama pemesan: ")
                tgl = input("Tanggal (YYYY-MM-DD): ").strip()
                mulai = input("Jam mulai (HH:MM): ").strip()
                selesai = input("Jam selesai (HH:MM): ").strip()
                b = buat_booking(data, id_lap, nama, tgl, mulai, selesai)
                simpan_data(data)
                print("Booking %s berhasil. Total: Rp%s."
                      % (b["id"], f"{b['total']:,}"))
            except ValueError as e:
                print("Error:", e)
        elif pilih == "4":
            _tampil_jadwal(data)
        elif pilih == "5":
            id_b = input("ID booking: ").strip().upper()
            if batalkan_booking(data, id_b):
                simpan_data(data)
                print("Booking %s dibatalkan." % id_b)
            else:
                print("Booking %s tidak ditemukan / sudah batal." % id_b)
        elif pilih == "0":
            print("Sampai jumpa!")
            break
        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()
