import pandas as pd
import argparse
import os

def parse_csv_to_excel(csv_file_path: str, excel_file_path: str):
    """
    Membaca data dari file CSV dan menyimpannya ke file Excel.

    Args:
        csv_file_path (str): Path ke file CSV input.
        excel_file_path (str): Path ke file Excel output.
    """
    if not os.path.exists(csv_file_path):
        print(f"Error: File input tidak ditemukan di {csv_file_path}")
        return

    try:
        # Membaca file CSV ke dalam pandas DataFrame
        df = pd.read_csv(csv_file_path)

        # Menulis DataFrame ke file Excel
        # index=False mencegah pandas menulis indeks baris ke dalam sheet Excel
        df.to_excel(excel_file_path, index=False, engine='openpyxl')

        print(f"Berhasil mengonversi {csv_file_path} ke {excel_file_path}")

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == '__main__':
    # Mengatur parser argumen untuk membuat skrip ramah pengguna dari baris perintah
    parser = argparse.ArgumentParser(description="Konversi file CSV ke file Excel.")
    parser.add_argument("csv_input", help="Path ke file CSV input.")
    parser.add_argument("excel_output", help="Path untuk file Excel output.")

    # Mem-parsing argumen baris perintah
    args = parser.parse_args()

    # Memanggil fungsi konversi
    parse_csv_to_excel(args.csv_input, args.excel_output)
