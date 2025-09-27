import pandas as pd
from collections import Counter
import argparse
import os

def create_vulnerability_charts(csv_file_path: str, output_excel_path: str):
    """
    Membaca data kerentanan dari CSV, menganalisisnya, dan membuat dasbor
    berisi bagan dalam file Excel.
    """
    if not os.path.exists(csv_file_path):
        print(f"Error: File input tidak ditemukan di {csv_file_path}")
        return

    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error saat membaca file CSV: {e}")
        return

    # --- 1. Siapkan data untuk bagan ---

    # Analisis 1: Distribusi Tingkat Keparahan (Severity)
    severity_counts = df['Severity'].value_counts().reset_index()
    severity_counts.columns = ['Severity', 'Count']

    # Analisis 2: 10 Server Teratas yang Terpengaruh
    # Kolom 'Affected_Servers' berisi string yang dipisahkan koma.
    # Kita perlu memisahnya dan menghitung kemunculan setiap server.
    server_list = []
    for servers in df['Affected_Servers'].dropna():
        server_list.extend([server.strip() for server in servers.split(',')])
    
    server_counts = Counter(server_list)
    top_servers_df = pd.DataFrame(server_counts.most_common(10), columns=['Server', 'Count'])

    # Analisis 3: Distribusi Skor CVSS
    cvss_counts = df['Max_CVSS_Score'].value_counts().reset_index()
    cvss_counts.columns = ['CVSS_Score', 'Count']
    cvss_counts = cvss_counts.sort_values('CVSS_Score', ascending=False)

    # Analisis 4: Pemetaan CVE ke Aset (15 Teratas berdasarkan jumlah aset yang terpengaruh)
    # Hitung jumlah server untuk setiap CVE
    df['Asset_Count'] = df['Affected_Servers'].str.split(',').str.len()
    cve_asset_map_df = df[['CVE_ID', 'Asset_Count']].sort_values('Asset_Count', ascending=False).head(15)


    # --- 2. Buat file Excel dan bagan ---

    try:
        writer = pd.ExcelWriter(output_excel_path, engine='xlsxwriter')
        workbook = writer.book
        dashboard_sheet = workbook.add_worksheet('Vulnerability_Dashboard')
    except Exception as e:
        print(f"Error saat membuat Excel writer: {e}")
        return

    # --- Bagan 1: Distribusi Tingkat Keparahan (Bagan Pie) ---
    if not severity_counts.empty:
        # Tulis data ke sheet terpisah untuk bagan
        severity_counts.to_excel(writer, sheet_name='Severity_Data', index=False)
        
        chart1 = workbook.add_chart({'type': 'pie'})
        chart1.add_series({
            'name': 'Distribusi Severity',
            'categories': ['Severity_Data', 1, 0, len(severity_counts), 0],
            'values':     ['Severity_Data', 1, 1, len(severity_counts), 1],
            'data_labels': {'percentage': True, 'leader_lines': True},
        })
        chart1.set_title({'name': 'Distribusi Tingkat Keparahan Kerentanan'})
        chart1.set_style(10) # Gaya bisa 1-48
        dashboard_sheet.insert_chart('B2', chart1, {'x_scale': 1.2, 'y_scale': 1.2})

    # --- Bagan 2: 10 Server Teratas yang Terpengaruh (Bagan Batang) ---
    if not top_servers_df.empty:
        top_servers_df.to_excel(writer, sheet_name='Top_Servers_Data', index=False)
        
        chart2 = workbook.add_chart({'type': 'bar'})
        chart2.add_series({
            'name': 'Jumlah Kerentanan',
            'categories': ['Top_Servers_Data', 1, 0, len(top_servers_df), 0],
            'values':     ['Top_Servers_Data', 1, 1, len(top_servers_df), 1],
            'fill':   {'color': '#E74C3C'},
        })
        chart2.set_title({'name': '10 Server Teratas yang Paling Terpengaruh'})
        chart2.set_x_axis({'name': 'Jumlah Kerentanan'})
        chart2.set_y_axis({'name': 'Nama Server'})
        # chart2.get_y_axis()['reverse'] = True # Untuk menampilkan yang tertinggi di atas
        chart2.set_legend({'position': 'none'})
        dashboard_sheet.insert_chart('B20', chart2, {'x_scale': 1.5, 'y_scale': 1.5})

    # --- Bagan 3: Distribusi Skor CVSS (Bagan Kolom) ---
    if not cvss_counts.empty:
        cvss_counts.to_excel(writer, sheet_name='CVSS_Data', index=False)
        
        chart3 = workbook.add_chart({'type': 'column'})
        chart3.add_series({
            'name':       'Jumlah CVE',
            'categories': ['CVSS_Data', 1, 0, len(cvss_counts), 0],
            'values':     ['CVSS_Data', 1, 1, len(cvss_counts), 1],
            'fill':       {'color': '#3498DB'},
        })
        chart3.set_title({'name': 'Distribusi Skor CVSS Maksimal'})
        chart3.set_x_axis({'name': 'Skor CVSS'})
        chart3.set_y_axis({'name': 'Jumlah CVE'})
        chart3.set_legend({'position': 'none'})
        dashboard_sheet.insert_chart('K2', chart3, {'x_scale': 1.2, 'y_scale': 1.2})

    # --- Bagan 4: Pemetaan CVE ke Aset (Bagan Batang Horizontal) ---
    if not cve_asset_map_df.empty:
        cve_asset_map_df.to_excel(writer, sheet_name='CVE_Asset_Data', index=False)
        
        chart4 = workbook.add_chart({'type': 'bar'})
        chart4.add_series({
            'name': 'Jumlah Aset Terpengaruh',
            'categories': ['CVE_Asset_Data', 1, 0, len(cve_asset_map_df), 0],
            'values':     ['CVE_Asset_Data', 1, 1, len(cve_asset_map_df), 1],
            'fill':   {'color': '#F39C12'},
        })
        chart4.set_title({'name': '15 CVE Teratas berdasarkan Jumlah Aset'})
        chart4.set_x_axis({'name': 'Jumlah Aset'})
        chart4.set_y_axis({'name': 'CVE ID'})
        # chart4.get_y_axis()['reverse'] = True # Menampilkan yang tertinggi di atas
        chart4.set_legend({'position': 'none'})
        dashboard_sheet.insert_chart('K20', chart4, {'x_scale': 1.5, 'y_scale': 1.5})
        
    # Atur lebar kolom untuk dasbor agar presentasi lebih baik
    dashboard_sheet.set_column('A:A', 2)
    dashboard_sheet.set_column('B:Z', 12)

    # Tutup writer untuk menyimpan file
    writer.close()
    print(f"Berhasil membuat dasbor kerentanan di {output_excel_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Hasilkan dasbor kerentanan dari file CSV.")
    parser.add_argument("csv_input", help="Path ke file CSV input yang berisi data kerentanan.")
    parser.add_argument("excel_output", help="Path untuk file Excel output dasbor.")
    
    args = parser.parse_args()
    create_vulnerability_charts(args.csv_input, args.excel_output)

