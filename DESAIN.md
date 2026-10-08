# Desain Sistem Booking Lapangan Futsal

## 1. Desain Arsitektur

Sistem memakai arsitektur 3 lapis sederhana:

```
┌─────────────────────────┐
│   CLI (menu interaktif) │  <- interaksi pengguna (main, _tampil_*)
├─────────────────────────┤
│     Logika bisnis       │  <- cek_bentrok, hitung_total, buat_booking,
│                         │     batalkan_booking, tambah_lapangan, jadwal_tanggal
├─────────────────────────┤
│   Penyimpanan (JSON)     │  <- muat_data / simpan_data ke data.json
└─────────────────────────┘
```

- **CLI** hanya mengurus input/output, tidak menyimpan state.
- **Logika bisnis** murni fungsi tanpa I/O — mudah di-unit-test.
- **Penyimpanan** satu file `data.json` berisi daftar lapangan & booking.

## 2. Use Case

Aktor: **Pengguna** (satu peran).

| ID | Use case | Deskripsi |
|----|----------|-----------|
| UC-01 | Lihat lapangan | Menampilkan daftar lapangan + tarif/jam |
| UC-02 | Tambah lapangan | Menambah lapangan baru (nama, tarif > 0) |
| UC-03 | Buat booking | Memesan slot: sistem menolak jika bentrok |
| UC-04 | Lihat jadwal | Menampilkan booking aktif per tanggal |
| UC-05 | Batalkan booking | Mengubah status booking menjadi "batal" |

Relasi: UC-03 membutuhkan UC-01 (memilih lapangan yang ada).

## 3. Sequence Diagram — Buat Booking

```mermaid
sequenceDiagram
    actor P as Pengguna
    participant UI as CLI
    participant LB as Logika Bisnis
    participant DB as data.json

    P->>UI: pilih "Buat booking" + data slot
    UI->>LB: buat_booking(...)
    LB->>LB: validasi lapangan, tanggal, jam
    LB->>LB: cek_bentrok(...)
    alt jadwal bentrok
        LB-->>UI: ValueError("Jadwal bentrok...")
        UI-->>P: tampilkan pesan error
    else slot tersedia
        LB->>LB: hitung_total(tarif, mulai, selesai)
        LB-->>UI: booking baru
        UI->>DB: simpan_data(...)
        UI-->>P: "Booking B2 berhasil. Total: Rp100.000"
    end
```

## 4. Activity Diagram — Buat Booking

```mermaid
flowchart TD
    A([Mulai]) --> B[Input: lapangan, nama, tanggal, jam]
    B --> C{Data valid?}
    C -- tidak --> Z[Tampilkan error]
    C -- ya --> D{Cek bentrok}
    D -- bentrok --> Z
    D -- tersedia --> E[Hitung total bayar]
    E --> F[Simpan booking]
    F --> G([Selesai])
    Z --> G
```

## 5. Keputusan desain penting

- **Aturan bentrok**: dua rentang `[mulai, selesai)` bentrok jika
  `mulai1 < selesai2 dan mulai2 < selesai1`. Booking yang selesai tepat
  saat booking lain mulai **diperbolehkan** (batas bersentuhan).
- **Booking yang dibatalkan** diabaikan saat cek bentrok — slotnya bebas lagi.
- **Total proporsional per menit**: 90 menit × Rp60.000/jam = Rp90.000.
