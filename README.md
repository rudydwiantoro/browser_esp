# BrowserESP Web Bluetooth Demo

Percobaan kontrol ESP32 TTGO dari browser menggunakan Web Bluetooth.

## File
- `espble.py`: firmware MicroPython BLE peripheral + output ke LCD
- `index.html`: UI browser untuk connect dan kirim command BLE

## UUID BLE
- Service UUID: `4fafc201-1fb5-459e-8fcc-c5c9c331914b`
- Characteristic UUID: `beb5483e-36e1-4688-b7f5-ea07361b26a8`

Keduanya harus sama antara `espble.py` dan `index.html`.

## Fitur yang sudah jalan
- Connect dari browser ke ESP32 BLE
- Tampilkan info `device.name` dan `device.id` di halaman
- Auto reconnect saat koneksi terputus
- Command byte:
  - `1` -> `ON`
  - `0` -> `OFF`
  - `2` -> `BLINK`
  - `3` -> `CLEAR`
- Command teks:
  - `TXT:<pesan>` -> tampilkan pesan di LCD

## Cara pakai
1. Upload/jalankan `espble.py` di ESP32 (MicroPython).
2. Buka `index.html` di Chrome/Edge.
3. Klik `Connect ke ESP32`.
4. Uji tombol `ON/OFF/BLINK/CLEAR` atau kirim teks custom.

## Catatan penting Web Bluetooth
- Disarankan akses via `https://` atau `http://localhost`.
- Browser yang direkomendasikan: Chrome/Edge desktop.
- Bluetooth komputer/laptop harus aktif dan permission situs diizinkan.

## Troubleshooting
- `OSError: -18` saat `gap_advertise`:
  - Penyebab: payload advertising > 31 byte.
  - Solusi: gunakan split `adv_data` (flags + service UUID) dan `resp_data` (nama device).
- Device tidak muncul di popup:
  - Pastikan `SERVICE_UUID` di browser dan firmware identik.
  - Restart BLE di board (soft reboot) lalu coba scan ulang.
