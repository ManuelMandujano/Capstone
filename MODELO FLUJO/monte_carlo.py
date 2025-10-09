# monte_carlo.py
import numpy as np
import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from model.modelo_flujo_multi import EmbalseModelMulti

anos = ['1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
        '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
        '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
        '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
        '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
        '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019']

NUM_SIMULACIONES = 28
DURACION_ANOS = 1

ruta = "data/caudales.xlsx"
xls = pd.ExcelFile(ruta)
nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4, nrows=31)
hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=39, nrows=31)
hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=75, nrows=31)
hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=110, nrows=31)

def simular_escenario(anos_simulados):
    copia_anos = anos.copy()
    lista_resultados = []
    for ano in range(anos_simulados):
        ano_seleccionado = np.random.choice(copia_anos)
        lista_resultados.append(ano_seleccionado)
        copia_anos.remove(ano_seleccionado)
    return lista_resultados

def obtener_datos_simulacion(lista_anos, df):
    datos_simulados = []
    df['AÑO'] = df['AÑO'].astype(str)
    
    for ano in lista_anos:
        fila = df[df['AÑO'] == ano]
        if not fila.empty:
            datos_simulados.append(fila.iloc[0].tolist())
        else:
            datos_simulados.append([None] * len(df.columns))
    return datos_simulados

def preparar_datos_para_modelo(escenario_anos):
    datos_nuble = obtener_datos_simulacion(escenario_anos, nuble)
    datos_hoya1 = obtener_datos_simulacion(escenario_anos, hoya1)
    datos_hoya2 = obtener_datos_simulacion(escenario_anos, hoya2) 
    datos_hoya3 = obtener_datos_simulacion(escenario_anos, hoya3)
    
    escenario_data = []
    for i, ano in enumerate(escenario_anos):
        if datos_nuble[i][0] is not None:
            escenario_ano = {
                'año': ano,
                'Q_nuble': datos_nuble[i][1:13],
                'Q_hoya1': datos_hoya1[i][1:13],
                'Q_hoya2': datos_hoya2[i][1:13], 
                'Q_hoya3': datos_hoya3[i][1:13]
            }
            escenario_data.append(escenario_ano)
    return escenario_data

def ejecutar_modelo_con_escenario(escenario_anos):
    escenario_data = preparar_datos_para_modelo(escenario_anos)
    
    if not escenario_data:
        return None
    
    historicos = escenario_data
    
    params = {
        'C_R': 175_000_000, 'C_A': 260_000_000, 'C_B': 105_000_000,
        'V_R_inicial': 0, 'V_A_inicial': 0, 'V_B_inicial': 0,
        'consumo_humano_anual': 3_900_000,
        'perdidas_mensuales': [0]*12,
        'lambda_R': 0.4, 'lambda_A': 0.4, 'lambda_B': 0.2,
        'eta': 0.85,
        'temporada_riego': [6,7,8,9,10,11,0],
        'segundos_mes': [2678400,2592000,2678400,2592000,2678400,2592000,
                         2678400,2592000,2678400,2592000,2678400,2592000],
        'TimeLimit': 10_000_000,
        'FE_A': 1.0, 'FE_B': 1.0,
        'penaliza_EB': 1e-6, 'penaliza_SUP': 0.0,
    }
    
    Q_all = []
    H_all = []
    nombres = []
    for s in historicos:
        nombres.append(s['año'])
        Q_all.extend(list(s['Q_nuble']))
        H_sum = (np.array(s['Q_hoya1'], dtype=float) +
                 np.array(s['Q_hoya2'], dtype=float) + 
                 np.array(s['Q_hoya3'], dtype=float))
        H_all.extend(list(H_sum))
    
    Y = len(historicos)
    N = 12 * Y
    
    derechos_MAY_ABR = [52.00, 52.00, 52.00, 52.00, 57.70, 76.22, 69.22, 52.00, 52.00, 52.00, 52.00, 52.00]
    derechos_ABR_MAR = [derechos_MAY_ABR[11]] + derechos_MAY_ABR[:11]
    qeco_MAY_ABR = [10.00, 10.35, 14.48, 15.23, 15.23, 15.23, 15.23, 15.23, 12.80, 15.20, 16.40, 17.60]
    qeco_ABR_MAR = [qeco_MAY_ABR[11]] + qeco_MAY_ABR[:11]
    
    QPD_eff_all_m3s = []
    for k in range(N):
        mes = k % 12
        base95_menos_hoyas = max(0.0, 95.7 - H_all[k])
        qpd_nom_ajust = max(derechos_ABR_MAR[mes], qeco_ABR_MAR[mes], base95_menos_hoyas)
        QPD_eff_all_m3s.append(min(qpd_nom_ajust, Q_all[k]))
    
    num_A = 21221
    num_B = 7100
    demanda_A_mes = {1:0,2:0,3:0,4:500,5:2000,6:4000,7:6000,8:8000,9:6000,10:4000,11:2000,12:500}
    demanda_B_mes = {1:0,2:0,3:0,4:300,5:1500,6:3000,7:4500,8:6000,9:4500,10:3000,11:1500,12:300}
    orden_abr_mar = [4,5,6,7,8,9,10,11,12,1,2,3]
    demandas_A = [demanda_A_mes[m] * num_A for m in orden_abr_mar]
    demandas_B = [demanda_B_mes[m] * num_B for m in orden_abr_mar]
    
    # PRINT DE DEBUG - FLUJOS DE AGUA
    meses_nombres = ['ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR']
    print(f"\n{'='*100}")
    print(f" DEBUG COMPLETO - FLUJOS DE AGUA - AÑO: {escenario_anos[0]}")
    print(f"{'='*100}")
    
    for k in range(12):
        mes = k % 12
        seg = params['segundos_mes'][mes]
        Qin_m3 = Q_all[k] * seg
        QPD_m3 = QPD_eff_all_m3s[k] * seg
        
        print(f"\n MES {meses_nombres[mes]} (índice {mes}):")
        print(f"    ENTRADAS:")
        print(f"      Qin (río): {Q_all[k]:6.2f} m³/s = {Qin_m3:12,.0f} m³/mes")
        print(f"      QPD efectivo: {QPD_eff_all_m3s[k]:6.2f} m³/s = {QPD_m3:12,.0f} m³/mes")
        print(f"      Hoyas (1+2+3): {H_all[k]:6.2f} m³/s")
        
        print(f"   DEMANDAS:")
        print(f"      Demanda A: {demandas_A[mes]:12,.0f} m³/mes")
        print(f"      Demanda B: {demandas_B[mes]:12,.0f} m³/mes")
        print(f"      Consumo humano anual: {params['consumo_humano_anual']:12,.0f} m³/año")
    
    model = EmbalseModelMulti(params)
    sol = model.solve(Q_all, QPD_eff_all_m3s, demandas_A, demandas_B, n_years=Y)
    
    if sol:
        # PRINT DE RESULTADOS
        print(f"\n🎯 RESULTADOS DEL MODELO:")
        print(f"{'='*100}")
        
        for k in range(12):
            mes = k % 12
            seg = params['segundos_mes'][mes]
            
            print(f"\n MES {meses_nombres[mes]}:")
            print(f"    FLUJOS (m³/mes):")
            print(f"      UPREF (preferente): {sol['UPREF'][k]:12,.0f}")
            print(f"      IN_VRFI → Embalse R: {sol['IN_VRFI'][k]:12,.0f}")
            print(f"      INA → Embalse A: {sol['INA'][k]:12,.0f}")
            print(f"      INB → Embalse B: {sol['INB'][k]:12,.0f}")
            print(f"      EB (rebalse): {sol['EB'][k]:12,.0f}")
            print(f"      SUP (apoyo): {sol['SUP'][k]:12,.0f}")
            print(f"QIN (río): {Q_all[k]:6.2f} m³/s = {Q_all[k] * seg:12,.0f} m³/mes")

            print(f"    ENTREGAS (m³/mes):")
            print(f"      R_H (consumo humano): {sol['R_H'][k]:12,.0f}")
            print(f"      R_A (riego A): {sol['R_A'][k]:12,.0f}")
            print(f"      R_B (riego B): {sol['R_B'][k]:12,.0f}")
            print(f"      UVRFI_A (apoyo A): {sol['UVRFI_A'][k]:12,.0f}")
            print(f"      UVRFI_B (apoyo B): {sol['UVRFI_B'][k]:12,.0f}")
            
            print(f"    VOLÚMENES FINALES (m³):")
            print(f"      V_R: {sol['V_R'][k]:12,.0f}")
            print(f"      V_A: {sol['V_A'][k]:12,.0f}")
            print(f"      V_B: {sol['V_B'][k]:12,.0f}")
            
            print(f"    DÉFICITS (m³/mes):")
            print(f"      d_A: {sol['d_A'][k]:12,.0f}")
            print(f"      d_B: {sol['d_B'][k]:12,.0f}")
            
            print(f"    PÉRDIDAS (m³/mes):")
            print(f"      L_R: {sol['L_R'][k]:12,.0f}")
            print(f"      L_A: {sol['L_A'][k]:12,.0f}")
            print(f"      L_B: {sol['L_B'][k]:12,.0f}")
            
            print(f"   ⚡ TURBINADO:")
            print(f"      Q_turb: {sol['Q_turb'][k]:6.2f} m³/s = {sol['Q_turb'][k] * seg:12,.0f} m³/mes")
            
            print(f"    ESTADO EMBALSES:")
            print(f"      A_empty: {sol['A_empty'][k]}")
            print(f"      B_empty: {sol['B_empty'][k]}")
            print(f"      Qin (río): {Q_all[k]:6.2f} m³/s = {Q_all[k] * seg:12,.0f} m³/mes")
        
        print(f"\n RESUMEN ANUAL:")
        print(f"   Déficit total A: {sum(sol['d_A'][:12]):12,.0f} m³")
        print(f"   Déficit total B: {sum(sol['d_B'][:12]):12,.0f} m³")
        print(f"   Consumo humano total: {sum(sol['R_H'][:12]):12,.0f} m³")
        print(f"   Objetivo: {sol['objetivo']:12,.0f} m³")
        
        sol['escenario_anos'] = escenario_anos
        sol['dem_A_12'] = demandas_A * Y
        sol['dem_B_12'] = demandas_B * Y
        return sol
    else:
        return None

def ejecutar_simulacion_monte_carlo():
    todos_los_datos = []
    
    for i in range(NUM_SIMULACIONES):
        escenario_anos = simular_escenario(DURACION_ANOS)
        resultado = ejecutar_modelo_con_escenario(escenario_anos)
        if resultado:
            # Agregar datos de esta simulación
            for mes_idx in range(len(resultado['Q_turb'])):
                año_idx = mes_idx // 12
                mes = mes_idx % 12
                print("estoy en este mes:", mes) # Ejemplo de impresión de demanda
                print(f"demanda en este mes es {resultado['d_A'][0]}") 

                fila = {
                    'Simulacion': i + 1,
                    'Escenario': ', '.join(escenario_anos),
                    'Año_Hidrologico': escenario_anos[año_idx],
                    'Mes': mes,
                    'Q_turb': resultado['Q_turb'][mes_idx],
                    'V_R': resultado['V_R'][mes_idx],
                    'V_A': resultado['V_A'][mes_idx],
                    'V_B': resultado['V_B'][mes_idx],
                    'd_A': resultado['d_A'][mes_idx],
                    'd_B': resultado['d_B'][mes_idx],
                    'R_A': resultado['R_A'][mes_idx],
                    'R_B': resultado['R_B'][mes_idx],
                    'R_H': resultado['R_H'][mes_idx],
                    'UPREF': resultado['UPREF'][mes_idx],
                    'IN_VRFI': resultado['IN_VRFI'][mes_idx],
                    'INA': resultado['INA'][mes_idx],
                    'INB': resultado['INB'][mes_idx],
                    'EB': resultado['EB'][mes_idx],
                    'UVRFI_A': resultado['UVRFI_A'][mes_idx],
                    'UVRFI_B': resultado['UVRFI_B'][mes_idx],
                    'L_R': resultado['L_R'][mes_idx],
                    'L_A': resultado['L_A'][mes_idx],
                    'L_B': resultado['L_B'][mes_idx],
                    'demb': resultado['dem_B_12'][mes_idx],
                    'dema': resultado['dem_A_12'][mes_idx],}
                todos_los_datos.append(fila)
    
    # Crear un único DataFrame con todos los datos
    df_final = pd.DataFrame(todos_los_datos)
    
    # Guardar en un único Excel
    df_final.to_excel('resultados_monte_carlo.xlsx', index=False)
    
    return df_final

if __name__ == "__main__":
    df_resultados = ejecutar_simulacion_monte_carlo()
    print("Simulación Monte Carlo completada. Resultados guardados en 'resultados_monte_carlo.xlsx'")



        # Para printear Qpref (QPD_eff_all_m3s) de un año específico
   