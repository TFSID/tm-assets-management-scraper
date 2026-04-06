
## 🧭 **Panduan Singkat: Analisis & Pelaporan CVE**

Panduan ini membantu kamu mengubah daftar CVE mentah (dalam format CSV) menjadi **dasbor Excel** yang rapi, terstruktur, dan siap digunakan untuk analisis keamanan.

Ada dua langkah utama:

1. Mengolah dan mengategorikan data CVE.
2. Menganalisis hasilnya dan membuat dasbor.

---

### 🔹 **Langkah 1: Proses & Kategorikan Data CVE**

Script pertama — `1_cve-categorizer.py` — akan membaca file CSV mentah kamu, mengambil detail CVE (seperti skor CVSS dan deskripsinya), lalu membuat file hasil yang sudah diringkas dan dikategorikan.

#### Langkah-langkahnya:

1. **Siapkan file input.**
   Pastikan kamu sudah punya file CSV sumber, misalnya `sample.csv`, dengan kolom seperti:

   ```
   Device Name, IP Addresses, riskScore, operatingSystem, CVE ID
   ```

2. **Jalankan script-nya.**
   Buka terminal, masuk ke folder tempat script disimpan, lalu ketik:

   ```bash
   python .\1_cve-categorizer.py
   ```

3. **Ikuti petunjuk yang muncul.**
   Saat script dijalankan, kamu akan diminta mengisi beberapa hal:

   * **Enter choice (1-3):** ketik `1` (untuk memproses file CSV)

   * **Enter CSV file path:** masukkan `sample.csv` atau nama file kamu sendiri

   * **Enter output CSV filename:** beri nama hasilnya, misalnya `sample-categorized.csv`

   > 💡 **Tips:** Simpan hasilnya dalam format `.csv`, karena file ini akan dipakai di langkah berikutnya.

4. **Cek hasilnya.**
   Setelah selesai, script akan menampilkan ringkasan hasil di terminal dan membuat file baru bernama **`sample-categorized.csv`** di folder yang sama.
   File ini akan kamu pakai untuk tahap analisis selanjutnya.

---

### 🔹 **Langkah 2: Analisis Data & Buat Dasbor**

Script kedua — `2_data_analyzer.py` — akan membaca file hasil kategorisasi tadi, lalu membuat dasbor akhir dalam bentuk file Excel.

#### Langkah-langkahnya:

1. **Jalankan script analisis.**
   Di terminal yang sama, jalankan perintah berikut:

   ```bash
   python .\2_data_analyzer.py sample-categorized.csv analyzed_sample.xlsx
   ```

   Keterangan:

   * `sample-categorized.csv` → file hasil dari Langkah 1
   * `analyzed_sample.xlsx` → nama file untuk dasbor Excel yang akan dibuat

2. **Lihat hasilnya.**
   Setelah proses selesai, kamu akan melihat pesan:

   ```
   Berhasil membuat dasbor kerentanan...
   ```

   Artinya file **`analyzed_sample.xlsx`** sudah jadi dan siap dibuka.
   Di dalamnya, kamu bisa lihat hasil analisis CVE yang sudah disusun dengan jelas dan terkelompok.

---

### 🧩 **Ringkasan Alur Cepat**

Berikut gambaran singkat alurnya:

```
sample.csv
   ↓
1_cve-categorizer.py
   ↓
sample-categorized.csv
   ↓
2_data_analyzer.py
   ↓
analyzed_sample.xlsx
```

---