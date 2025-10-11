# monte_carlo.py

'''''
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

NUM_SIMULACIONES = 1
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

'''''
# monte_carlo_simulation.py
# monte_carlo_simulation.py
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from datetime import datetime

class MonteCarloEmbalse:
    """
    Simulación de Monte Carlo para el Embalse Nueva Punilla.
    Simula 30 años consecutivos con stocks que se transfieren,
    pero con el orden de los años aleatorio.
    """
    
    def __init__(self, num_simulaciones=100, duracion_anos=30):
        self.num_simulaciones = num_simulaciones
        self.duracion_anos = duracion_anos
        
        self.anos_disponibles = [
            '1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
            '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
            '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
            '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
            '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
            '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019'
        ]
        
        self.resultados_simulaciones = []
        self._cargar_datos_base()
        
    def _cargar_datos_base(self):
        """Carga los datos de caudales base desde Excel."""
        data_file = "data/caudales.xlsx"
        xls = pd.ExcelFile(data_file)
        
        nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4, nrows=31)
        hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=39, nrows=31)
        hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=75, nrows=31)
        hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=110, nrows=31)
        
        excel_col_names = ['MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC','ENE','FEB','MAR','ABR']
        model_month_order = [1,2,3,4,5,6,7,8,9,10,11,12]
        
        self.Q_nuble_base = {}
        self.Q_hoya1_base = {}
        self.Q_hoya2_base = {}
        self.Q_hoya3_base = {}
        self.Q_afl_base = {}
        
        for idx, row in nuble.iterrows():
            year_str = str(row.get('AÑO',''))
            if (pd.notna(row.get('AÑO')) and '/' in year_str
                and not any(w in year_str.upper() for w in ['PROMEDIO','TOTAL','MAX','MIN'])):
                try:
                    year = int(year_str.split('/')[0])
                    for col, mm in zip(excel_col_names, model_month_order):
                        n1 = nuble.loc[idx, col]
                        h1 = hoya1.loc[idx, col]
                        h2 = hoya2.loc[idx, col]
                        h3 = hoya3.loc[idx, col]
                        if pd.notna(n1):
                            self.Q_nuble_base[year, mm] = float(n1)
                            self.Q_afl_base[year, mm] = float(n1)
                        if pd.notna(h1): self.Q_hoya1_base[year, mm] = float(h1)
                        if pd.notna(h2): self.Q_hoya2_base[year, mm] = float(h2)
                        if pd.notna(h3): self.Q_hoya3_base[year, mm] = float(h3)
                except Exception:
                    pass
    
    def generar_escenario(self):
        """Genera un escenario aleatorio seleccionando años sin reemplazo."""
        anos_disponibles = self.anos_disponibles.copy()
        escenario = []
        
        for _ in range(min(self.duracion_anos, len(anos_disponibles))):
            ano_seleccionado = np.random.choice(anos_disponibles)
            escenario.append(ano_seleccionado)
            anos_disponibles.remove(ano_seleccionado)
            
        return escenario
    
    def ejecutar_simulacion(self, num_sim, anos_escenario):
        """
        Ejecuta una simulación con años consecutivos.
        Los stocks se transfieren de un año al siguiente.
        """
        print(f"\n{'='*60}")
        print(f"Ejecutando Simulación #{num_sim + 1}/{self.num_simulaciones}")
        print(f"Primeros 5 años: {anos_escenario[:5]}")
        print(f"{'='*60}")
        
        try:
            resultado = self._resolver_modelo_montecarlo(anos_escenario)
            
            if resultado is not None:
                resultado['num_simulacion'] = num_sim + 1
                resultado['escenario_anos'] = ','.join(anos_escenario)
                print(f"✓ Simulación #{num_sim + 1} completada - Déficit: {resultado['deficit_total']:.2f} Hm³")
                return resultado
            else:
                print(f"❌ Simulación #{num_sim + 1} falló")
                return None
                
        except Exception as e:
            print(f"❌ Error en simulación #{num_sim + 1}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _resolver_modelo_montecarlo(self, anos_escenario):
        """
        Resuelve el modelo con años en secuencia.
        Los stocks finales de un año son los iniciales del siguiente.
        """
        model = gp.Model("MC_Embalse")
        model.setParam('OutputFlag', 0)
        
        # Parámetros
        C_VRFI = 175
        C_TIPO_A = 260
        C_TIPO_B = 105
        V_C_H = 3.9
        
        segundos_por_mes = {
            1: 31*24*3600, 2: 30*24*3600, 3: 31*24*3600, 4: 31*24*3600,
            5: 30*24*3600, 6: 31*24*3600, 7: 30*24*3600, 8: 31*24*3600,
            9: 31*24*3600, 10: 28*24*3600, 11: 31*24*3600, 12: 30*24*3600
        }
        
        num_A = 21221
        num_B = 7100
        DA_a_m = {1:9503,2:6516,3:3452,4:776,5:0,6:0,7:0,8:0,9:0,10:2444,11:6516,12:9580}
        DB_a_b = {1:3361,2:2305,3:1221,4:274,5:0,6:0,7:0,8:0,9:0,10:864,11:2305,12:3388}
        m_civil = {1:5,2:6,3:7,4:8,5:9,6:10,7:11,8:12,9:1,10:2,11:3,12:4}
        
        derechos = [52.00,52.00,52.00,52.00,57.70,76.22,69.22,52.00,52.00,52.00,52.00,52.00]
        qeco = [10.00,10.35,14.48,15.23,15.23,15.23,15.23,15.23,12.80,15.20,16.40,17.60]
        
        months = list(range(1, 13))
        
        # Variables
        V_VRFI = model.addVars(anos_escenario, months, name="V_VRFI", lb=0, ub=C_VRFI)
        V_A = model.addVars(anos_escenario, months, name="V_A", lb=0, ub=C_TIPO_A)
        V_B = model.addVars(anos_escenario, months, name="V_B", lb=0, ub=C_TIPO_B)
        
        IN_VRFI = model.addVars(anos_escenario, months, name="IN_VRFI", lb=0)
        IN_A = model.addVars(anos_escenario, months, name="IN_A", lb=0)
        IN_B = model.addVars(anos_escenario, months, name="IN_B", lb=0)
        E_TOT = model.addVars(anos_escenario, months, name="E_TOT", lb=0)
        
        Q_ch = model.addVars(anos_escenario, months, name="Q_ch", lb=0)
        Q_A = model.addVars(anos_escenario, months, name="Q_A", lb=0)
        Q_B = model.addVars(anos_escenario, months, name="Q_B", lb=0)
        Q_A_apoyo = model.addVars(anos_escenario, months, name="Q_A_apoyo", lb=0)
        Q_B_apoyo = model.addVars(anos_escenario, months, name="Q_B_apoyo", lb=0)
        
        d_A = model.addVars(anos_escenario, months, name="d_A", lb=0)
        d_B = model.addVars(anos_escenario, months, name="d_B", lb=0)
        Q_turb = model.addVars(anos_escenario, months, name="Q_turb", lb=0)
        
        # Auxiliares
        Rem = model.addVars(anos_escenario, months, name="Rem", lb=0)
        HeadR = model.addVars(anos_escenario, months, name="HeadR", lb=0)
        HeadA = model.addVars(anos_escenario, months, name="HeadA", lb=0)
        HeadB = model.addVars(anos_escenario, months, name="HeadB", lb=0)
        FillR = model.addVars(anos_escenario, months, name="FillR", lb=0)
        zR = model.addVars(anos_escenario, months, name="zR", lb=0)
        ShareA = model.addVars(anos_escenario, months, name="ShareA", lb=0)
        ShareB = model.addVars(anos_escenario, months, name="ShareB", lb=0)
        
        needA = model.addVars(anos_escenario, months, name="needA", lb=0)
        needB = model.addVars(anos_escenario, months, name="needB", lb=0)
        
        A_avail = model.addVars(anos_escenario, months, name="A_avail")
        A_dem50 = model.addVars(anos_escenario, months, name="A_dem50", lb=0)
        A_own_req = model.addVars(anos_escenario, months, name="A_own_req", lb=0)
        
        B_avail = model.addVars(anos_escenario, months, name="B_avail")
        B_dem50 = model.addVars(anos_escenario, months, name="B_dem50", lb=0)
        B_own_req = model.addVars(anos_escenario, months, name="B_own_req", lb=0)
        
        tA = model.addVars(anos_escenario, months, name="tA")
        tB = model.addVars(anos_escenario, months, name="tB")
        zeroVar = model.addVar(lb=0, ub=0, name="zero")
        
        VRFI_avail = model.addVars(anos_escenario, months, name="VRFI_avail")
        needTot = model.addVars(anos_escenario, months, name="needTot", lb=0)
        SupportTot = model.addVars(anos_escenario, months, name="SupportTot", lb=0)
        
        # Calcular QPD efectivo
        QPD_eff = {}
        for año in anos_escenario:
            y = int(año.split('/')[0])
            for mes in months:
                H = (self.Q_hoya1_base.get((y,mes),0) + 
                     self.Q_hoya2_base.get((y,mes),0) + 
                     self.Q_hoya3_base.get((y,mes),0))
                qpd_nom = max(derechos[mes-1], qeco[mes-1], max(0, 95.7 - H))
                QPD_eff[año, mes] = min(qpd_nom, self.Q_nuble_base.get((y,mes),0))
        
        # RESTRICCIONES
        # Primer año empieza con stocks en 0
        primer_ano = anos_escenario[0]
        model.addConstr(V_VRFI[primer_ano, 1] == 0, name="init_VRFI")
        model.addConstr(V_A[primer_ano, 1] == 0, name="init_VA")
        model.addConstr(V_B[primer_ano, 1] == 0, name="init_VB")
        
        for idx_ano, año in enumerate(anos_escenario):
            y = int(año.split('/')[0])
            
            for i, mes in enumerate(months):
                seg = segundos_por_mes[mes]
                Qin_s = self.Q_afl_base.get((y,mes), 0)
                Qin = Qin_s * seg / 1_000_000.0
                UPREF = QPD_eff[año, mes] * seg / 1_000_000.0
                
                key = m_civil[mes]
                demA = (DA_a_m[key] * num_A) / 1_000_000.0
                demB = (DB_a_b[key] * num_B) / 1_000_000.0
                
                # Stocks previos - CONSECUTIVOS entre años
                if i == 0:  # Primer mes del año
                    if idx_ano == 0:  # Primer año ya fijado arriba
                        V_R_prev = 0
                        V_A_prev = 0
                        V_B_prev = 0
                    else:  # Años siguientes: tomar del abril anterior
                        año_anterior = anos_escenario[idx_ano - 1]
                        V_R_prev = V_VRFI[año_anterior, 12]
                        V_A_prev = V_A[año_anterior, 12]
                        V_B_prev = V_B[año_anterior, 12]
                else:  # Dentro del mismo año
                    V_R_prev = V_VRFI[año, mes-1]
                    V_A_prev = V_A[año, mes-1]
                    V_B_prev = V_B[año, mes-1]
                
                # Remanente y llenado
                model.addConstr(Rem[año,mes] == Qin - UPREF)
                model.addConstr(HeadR[año,mes] == C_VRFI - V_R_prev)
                model.addConstr(HeadA[año,mes] == C_TIPO_A - V_A_prev)
                model.addConstr(HeadB[año,mes] == C_TIPO_B - V_B_prev)
                
                model.addGenConstrMin(FillR[año,mes], [Rem[año,mes], HeadR[año,mes]])
                model.addConstr(zR[año,mes] == Rem[año,mes] - FillR[año,mes])
                model.addConstr(ShareA[año,mes] == 0.71 * zR[año,mes])
                model.addConstr(ShareB[año,mes] == 0.29 * zR[año,mes])
                model.addGenConstrMin(IN_A[año,mes], [ShareA[año,mes], HeadA[año,mes]])
                model.addGenConstrMin(IN_B[año,mes], [ShareB[año,mes], HeadB[año,mes]])
                
                model.addConstr(IN_VRFI[año,mes] == FillR[año,mes])
                model.addConstr(E_TOT[año,mes] == Rem[año,mes] - IN_VRFI[año,mes] - IN_A[año,mes] - IN_B[año,mes])
                
                # Balances
                model.addConstr(V_VRFI[año,mes] == V_R_prev + IN_VRFI[año,mes] - Q_ch[año,mes] - Q_A_apoyo[año,mes] - Q_B_apoyo[año,mes])
                model.addConstr(V_A[año,mes] == V_A_prev + IN_A[año,mes] - Q_A[año,mes])
                model.addConstr(V_B[año,mes] == V_B_prev + IN_B[año,mes] - Q_B[año,mes])
                
                # Disponibilidades
                model.addConstr(Q_A[año,mes] <= V_A_prev + IN_A[año,mes])
                model.addConstr(Q_B[año,mes] <= V_B_prev + IN_B[año,mes])
                model.addConstr(Q_ch[año,mes] <= V_R_prev + IN_VRFI[año,mes])
                
                # Propio primero
                model.addConstr(A_avail[año,mes] == V_A_prev + IN_A[año,mes])
                model.addConstr(A_dem50[año,mes] == 0.5*demA)
                model.addGenConstrMin(A_own_req[año,mes], [A_avail[año,mes], A_dem50[año,mes]])
                model.addConstr(Q_A[año,mes] >= A_own_req[año,mes])
                
                model.addConstr(B_avail[año,mes] == V_B_prev + IN_B[año,mes])
                model.addConstr(B_dem50[año,mes] == 0.5*demB)
                model.addGenConstrMin(B_own_req[año,mes], [B_avail[año,mes], B_dem50[año,mes]])
                model.addConstr(Q_B[año,mes] >= B_own_req[año,mes])
                
                # Apoyo VRFI
                model.addConstr(tA[año,mes] == 0.5*demA - Q_A[año,mes])
                model.addConstr(tB[año,mes] == 0.5*demB - Q_B[año,mes])
                model.addGenConstrMax(needA[año,mes], [tA[año,mes], zeroVar])
                model.addGenConstrMax(needB[año,mes], [tB[año,mes], zeroVar])
                
                model.addConstr(Q_A_apoyo[año,mes] <= needA[año,mes])
                model.addConstr(Q_B_apoyo[año,mes] <= needB[año,mes])
                
                # Saturación VRFI
                model.addConstr(VRFI_avail[año,mes] == V_R_prev + IN_VRFI[año,mes] - Q_ch[año,mes])
                model.addConstr(needTot[año,mes] == needA[año,mes] + needB[año,mes])
                model.addGenConstrMin(SupportTot[año,mes], [VRFI_avail[año,mes], needTot[año,mes]])
                model.addConstr(Q_A_apoyo[año,mes] + Q_B_apoyo[año,mes] == SupportTot[año,mes])
                
                # Déficit
                model.addConstr(d_A[año,mes] == demA - (Q_A[año,mes] + Q_A_apoyo[año,mes]))
                model.addConstr(d_B[año,mes] == demB - (Q_B[año,mes] + Q_B_apoyo[año,mes]))
                
                model.addConstr(Q_A[año,mes] + Q_A_apoyo[año,mes] <= demA + 1e-9)
                model.addConstr(Q_B[año,mes] + Q_B_apoyo[año,mes] <= demB + 1e-9)
                
                # Turbinado
                model.addConstr(Q_turb[año,mes] == Q_A[año,mes] + Q_A_apoyo[año,mes] + Q_B[año,mes] + Q_B_apoyo[año,mes] + E_TOT[año,mes])
            
            # SSR anual
            model.addConstr(gp.quicksum(Q_ch[año, mes] for mes in months) == V_C_H)
        
        # Objetivo
        total_def = gp.quicksum(d_A[año,mes] + d_B[año,mes] for año in anos_escenario for mes in months)
        pen_vrfi = gp.quicksum(Q_A_apoyo[año,mes] + Q_B_apoyo[año,mes] for año in anos_escenario for mes in months)
        inc_prop = gp.quicksum(Q_A[año,mes] + Q_B[año,mes] for año in anos_escenario for mes in months)
        
        model.setObjective(total_def + 1e-3*pen_vrfi - 1e-3*inc_prop, GRB.MINIMIZE)
        
        # Resolver
        model.optimize()
        
        if model.status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            return None
        
        # Obtener tiempo de ejecución y gap
        tiempo_ejecucion = model.Runtime
        gap = model.MIPGap if hasattr(model, 'MIPGap') else 0.0
        
        # Calcular métricas
        deficit_total = model.objVal
        deficit_A = sum(d_A[año, mes].X for año in anos_escenario for mes in months)
        deficit_B = sum(d_B[año, mes].X for año in anos_escenario for mes in months)
        vol_turbinado = sum(Q_turb[año, mes].X for año in anos_escenario for mes in months)
        apoyo_vrfi_A = sum(Q_A_apoyo[año, mes].X for año in anos_escenario for mes in months)
        apoyo_vrfi_B = sum(Q_B_apoyo[año, mes].X for año in anos_escenario for mes in months)
        rebalse_total = sum(E_TOT[año, mes].X for año in anos_escenario for mes in months)
        
        # Volúmenes finales (último año, último mes = abril)
        ultimo_ano = anos_escenario[-1]
        vol_final_VRFI = V_VRFI[ultimo_ano, 12].X
        vol_final_A = V_A[ultimo_ano, 12].X
        vol_final_B = V_B[ultimo_ano, 12].X
        vol_final_total = vol_final_VRFI + vol_final_A + vol_final_B
        
        return {
            'deficit_total': deficit_total,
            'deficit_tipo_A': deficit_A,
            'deficit_tipo_B': deficit_B,
            'volumen_turbinado_total': vol_turbinado,
            'apoyo_vrfi_a': apoyo_vrfi_A,
            'apoyo_vrfi_b': apoyo_vrfi_B,
            'rebalse_total': rebalse_total,
            'gap': gap,
            'tiempo_ejecucion_seg': tiempo_ejecucion,
            'vol_final_VRFI': vol_final_VRFI,
            'vol_final_A': vol_final_A,
            'vol_final_B': vol_final_B,
            'vol_final_total': vol_final_total
        }
    
    def ejecutar_monte_carlo(self):
        """Ejecuta todas las simulaciones de Monte Carlo."""
        print(f"\n{'#'*60}")
        print(f"INICIANDO SIMULACIÓN DE MONTE CARLO")
        print(f"Número de simulaciones: {self.num_simulaciones}")
        print(f"Duración por simulación: {self.duracion_anos} años")
        print(f"{'#'*60}\n")
        
        for i in range(self.num_simulaciones):
            escenario = self.generar_escenario()
            resultado = self.ejecutar_simulacion(i, escenario)
            
            if resultado is not None:
                self.resultados_simulaciones.append(resultado)
        
        print(f"\n{'#'*60}")
        print(f"MONTE CARLO COMPLETADO")
        print(f"Simulaciones exitosas: {len(self.resultados_simulaciones)}/{self.num_simulaciones}")
        print(f"{'#'*60}\n")
    
    def exportar_resultados(self, archivo_salida=None):
        """Exporta los resultados a Excel."""
        if not self.resultados_simulaciones:
            print("⚠️  No hay resultados para exportar")
            return
        
        if archivo_salida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"monte_carlo_resultados_{timestamp}.xlsx"
        
        df_resultados = pd.DataFrame(self.resultados_simulaciones)
        
        columnas_numericas = df_resultados.select_dtypes(include=[np.number]).columns
        df_estadisticas = df_resultados[columnas_numericas].describe()
        
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        df_percentiles = df_resultados[columnas_numericas].quantile([p/100 for p in percentiles])
        df_percentiles.index = [f'percentil_{p}' for p in percentiles]
        
        idx_mejor = df_resultados['deficit_total'].idxmin()
        idx_peor = df_resultados['deficit_total'].idxmax()
        
        df_mejor_escenario = df_resultados.loc[[idx_mejor]].copy()
        df_mejor_escenario.insert(0, 'tipo', 'MEJOR ESCENARIO')
        
        df_peor_escenario = df_resultados.loc[[idx_peor]].copy()
        df_peor_escenario.insert(0, 'tipo', 'PEOR ESCENARIO')
        
        with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
            df_resultados.to_excel(writer, sheet_name='Resultados_Completos', index=False)
            df_estadisticas.to_excel(writer, sheet_name='Estadisticas')
            df_percentiles.to_excel(writer, sheet_name='Percentiles')
            
            df_escenarios = pd.concat([df_mejor_escenario, df_peor_escenario], ignore_index=True)
            df_escenarios.to_excel(writer, sheet_name='Escenarios_Extremos', index=False)
            
            resumen = {
                'Métrica': [
                    'Número de Simulaciones',
                    'Duración (años)',
                    'Déficit Total Promedio (Hm³)',
                    'Déficit Total Mínimo (Hm³)',
                    'Déficit Total Máximo (Hm³)',
                    'Desviación Estándar Déficit (Hm³)',
                    'Volumen Turbinado Promedio (Hm³)',
                    'Rebalse Promedio (Hm³)',
                    'Tiempo Ejecución Promedio (seg)',
                    'Tiempo Ejecución Total (seg)',
                    'Gap Promedio (%)',
                    'Vol Final Total Promedio (Hm³)',
                    'Vol Final VRFI Promedio (Hm³)',
                    'Vol Final A Promedio (Hm³)',
                    'Vol Final B Promedio (Hm³)'
                ],
                'Valor': [
                    len(self.resultados_simulaciones),
                    self.duracion_anos,
                    df_resultados['deficit_total'].mean(),
                    df_resultados['deficit_total'].min(),
                    df_resultados['deficit_total'].max(),
                    df_resultados['deficit_total'].std(),
                    df_resultados['volumen_turbinado_total'].mean(),
                    df_resultados['rebalse_total'].mean(),
                    df_resultados['tiempo_ejecucion_seg'].mean(),
                    df_resultados['tiempo_ejecucion_seg'].sum(),
                    df_resultados['gap'].mean() * 100,
                    df_resultados['vol_final_total'].mean(),
                    df_resultados['vol_final_VRFI'].mean(),
                    df_resultados['vol_final_A'].mean(),
                    df_resultados['vol_final_B'].mean()
                ]
            }
            df_resumen = pd.DataFrame(resumen)
            df_resumen.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
        
        print(f"✅ Resultados exportados a: {archivo_salida}")
        print(f"\n📊 RESUMEN:")
        print(f"   • Déficit promedio: {df_resultados['deficit_total'].mean():.2f} Hm³")
        print(f"   • Déficit mínimo: {df_resultados['deficit_total'].min():.2f} Hm³")
        print(f"   • Déficit máximo: {df_resultados['deficit_total'].max():.2f} Hm³")
        print(f"   • Tiempo total ejecución: {df_resultados['tiempo_ejecucion_seg'].sum():.1f} seg")
        print(f"   • Tiempo promedio por simulación: {df_resultados['tiempo_ejecucion_seg'].mean():.2f} seg")
        print(f"   • Gap promedio: {df_resultados['gap'].mean()*100:.4f}%")
        print(f"   • Vol final total promedio: {df_resultados['vol_final_total'].mean():.2f} Hm³")
        
        return archivo_salida


def main():
    """Función principal."""
    NUM_SIMULACIONES = 100
    DURACION_ANOS = 30
    
    mc = MonteCarloEmbalse(
        num_simulaciones=NUM_SIMULACIONES,
        duracion_anos=DURACION_ANOS
    )
    
    mc.ejecutar_monte_carlo()
    mc.exportar_resultados()


if __name__ == "__main__":
    np.random.seed(42)
    main()