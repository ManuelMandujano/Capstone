import pandas as pd


def load_flow_data(file_path):
    """Cargar datos de caudales desde Excel"""
    xls = pd.ExcelFile(file_path)
        
    nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4, nrows=31)
    hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=39, nrows=31)
    hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=75, nrows=31)
    hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=110, nrows=31)
        
    # Month mapping: Excel columns are MAY-ABR, we need to map to months 1-12 (APR-MAR)
    excel_col_names = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR']
    model_month_order = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # ABR=12, MAY=1, ..., MAR=11
        
        # Initialize dictionaries
    Q_nuble = {}
    Q_hoya1 = {}
    Q_hoya2 = {}
    Q_hoya3 = {}
    Q_afl = {}  
        
        # Process each year
    for idx, row in nuble.iterrows():
        year_str = str(row['AÑO'])
        year = int(year_str.split('/')[0])  # Extract first year (e.g., 1989 from "1989/1990")
            
        # Map Excel columns to model months
        for excel_col, model_month in zip(excel_col_names, model_month_order):
            # Store individual flows
            Q_nuble[year, model_month] = nuble.loc[idx, excel_col]
            Q_hoya1[year, model_month] = hoya1.loc[idx, excel_col]
            Q_hoya2[year, model_month] = hoya2.loc[idx, excel_col]
            Q_hoya3[year, model_month] = hoya3.loc[idx, excel_col]
                
            # alfuente es solo nuble
            Q_afl[year, model_month] = (Q_nuble[year, model_month] )

        
    return Q_afl, Q_nuble, Q_hoya1, Q_hoya2, Q_hoya3


print(load_flow_data('data/caudales.xlsx'))