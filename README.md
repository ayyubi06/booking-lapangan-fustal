# Sistem Booking Lapangan Futsal

Final project mata kuliah **Analisis & Pengujian Sistem**
(Pertemuan 5: High Order Testing — demo pada Pertemuan 6).

Aplikasi CLI Python untuk memesan lapangan futsal: kelola lapangan,
buat booking dengan deteksi jadwal bentrok otomatis, hitung total bayar,
batalkan booking, dan lihat jadwal per tanggal.

## Persyaratan

- Python 3.x
- pytest (`pip install pytest`) — untuk menjalankan test

## Cara menjalankan

```bash
git clone https://github.com/ayyubi06/booking-lapangan-fustal.git
cd booking-lapangan-fustal
python3 booking.py
python3 -m pytest test_booking.py -v
```

## Desain

Arsitektur, use case, sequence diagram, dan activity diagram:

→ [**DESAIN.md**](DESAIN.md)

## Pengujian

- **Unit test** (20 test, pytest): tiap fungsi logika diuji terpisah —
  `cek_bentrok`, `hitung_total`, `buat_booking`, `batalkan_booking`,
  `tambah_lapangan`, `jadwal_tanggal`, util waktu/tanggal.
- **Integration test**: alur penuh antar modul (logika bisnis × penyimpanan
  JSON) — tambah lapangan → booking → bentrok ditolak → batalkan →
  slot bebas lagi → data tersimpan dan bisa dimuat ulang.

## Isi repo

| File | Keterangan |
|------|------------|
| `booking.py` | Program utama (logika + CLI) |
| `test_booking.py` | Unit test & integration test (pytest) |
| `DESAIN.md` | Arsitektur + diagram UML |
| `README.md` | Panduan ini |
