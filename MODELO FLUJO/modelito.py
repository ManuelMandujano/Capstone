import pandas as pd


def load_flow_data(file_path):
    """Cargar datos de caudales desde Excel"""
    xls = pd.ExcelFile(file_path)
        
    # Cargar datos
    nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4, nrows=31)
    hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=39, nrows=31)
    hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=75, nrows=31)
    hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=110, nrows=31)
        
    excel_col_names = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR']
    model_month_order = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # ABR=12, MAY=1, ..., MAR=11
        
    Q_nuble = {}
    Q_hoya1 = {}
    Q_hoya2 = {}
    Q_hoya3 = {}
    Q_afl = {}  
        
    for idx, row in nuble.iterrows():
        year_str = str(row['AÑO'])
            
        if (not pd.isna(row['AÑO']) and 
            isinstance(year_str, str) and 
            '/' in year_str and
            not any(word in year_str.upper() for word in ['PROMEDIO', 'TOTAL', 'MAX', 'MIN'])):
            
            try:
                year = int(year_str.split('/')[0])  

                for excel_col, model_month in zip(excel_col_names, model_month_order):
                    # VERIFICAR QUE NO SEAN NaN
                    nuble_val = nuble.loc[idx, excel_col]
                    hoya1_val = hoya1.loc[idx, excel_col]
                    hoya2_val = hoya2.loc[idx, excel_col]
                    hoya3_val = hoya3.loc[idx, excel_col]
                    
                    if not pd.isna(nuble_val):
                        Q_nuble[year, model_month] = nuble_val
                    if not pd.isna(hoya1_val):
                        Q_hoya1[year, model_month] = hoya1_val
                    if not pd.isna(hoya2_val):
                        Q_hoya2[year, model_month] = hoya2_val
                    if not pd.isna(hoya3_val):
                        Q_hoya3[year, model_month] = hoya3_val
                    
                        # alfuente es solo nuble
                    if not pd.isna(nuble_val):
                        Q_afl[year, model_month] = nuble_val
                            
            except (ValueError, KeyError) as e:
                print(f"Advertencia: Error procesando fila {idx}, año {year_str}: {e}")
                continue
        
    return Q_afl, Q_nuble, Q_hoya1, Q_hoya2, Q_hoya3

Q_afl, Q_nuble, Q_hoya1, Q_hoya2, Q_hoya3 = load_flow_data('data/caudales.xlsx')

print(f"Q_afl: {len(Q_afl)} valores")
print(f"Q_nuble: {len(Q_nuble)} valores")
print(f"Q_hoya1: {len(Q_hoya1)} valores")
print(f"Q_hoya2: {len(Q_hoya2)} valores")
print(f"Q_hoya3: {len(Q_hoya3)} valores")


def print_flows(Q_dict, name):
    print(f"\n=== {name} ===")
    for (year, month), value in sorted(Q_dict.items()):
        print(f"Año: {year}, Mes: {month:02d}, Caudal: {value}")

print_flows(Q_afl, "Q_afl")
print_flows(Q_nuble, "Q_nuble")
print_flows(Q_hoya1, "Q_hoya1")
print_flows(Q_hoya2, "Q_hoya2")
print_flows(Q_hoya3, "Q_hoya3")