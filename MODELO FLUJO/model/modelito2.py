#esto se llama modelito2.py
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

class EmbalseNuevaPunilla:
    def __init__(self):
        self.model = gp.Model("Embalse_Nueva_Punilla")
        
        # CONJUNTOS
        self.anos = ['1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
                    '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
                    '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
                    '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
                    '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
                    '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019']
        
        self.months = list(range(1, 13))  
        self.temporada_riego = [6,7,8,9,10,11,0]
        
        # PARAMETROS
        self.C_TOTAL = 540
        self.C_VRFI = 175
        self.C_TIPO_A = 260
        self.C_TIPO_B = 105
        
        self.segundos_por_mes = {
            1: 30*24*3600,  2: 31*24*3600,  3: 30*24*3600,
            4: 31*24*3600,  5: 31*24*3600,  6: 30*24*3600,
            7: 31*24*3600,  8: 30*24*3600,  9: 31*24*3600,
            10: 31*24*3600, 11: 28*24*3600, 12: 31*24*3600
        }
        
        # Variables para almacenar datos
        self.inflow = {}
        self.Q_nuble = {}
        self.Q_hoya1 = {}
        self.Q_hoya2 = {}
        self.Q_hoya3 = {}
        
        # Demandas
        self.num_A = 21221
        self.num_B = 7100
        self.DA_a_m = {1:0,2:0,3:0,4:500,5:2000,6:4000,7:6000,8:8000,9:6000,10:4000,11:2000,12:500} #revisar que estas sean las demandas correspondientes pq parece q están malas
        self.DB_a_b = {1:0,2:0,3:0,4:300,5:1500,6:3000,7:4500,8:6000,9:4500,10:3000,11:1500,12:300}  #revisar que estas sean las demandas correspondientes pq parece q están malas
        self.orden_mayo_a_abril = [5,6,7,8,9,10,11,12,1,2,3,4]
        
        self.demandas_A = [self.DA_a_m[m] * self.num_A for m in self.orden_mayo_a_abril]
        self.demandas_B = [self.DB_a_b[m] * self.num_B for m in self.orden_mayo_a_abril]
        
        # Factores de entrega
        self.FEA = 1
        self.FEB = 1
        
        # Demanda humana
        self.V_C_H = 3.9
        self.S_TOTAL_0 = 0

    def setup_variables(self):
        m = self.model
        # VOLUMENES 5.4.1. VOLÚMENES disponibles al final de cada mes (en Hm³)
        self.V_VRFI = m.addVars(self.anos, self.months, name="V_VRFI", lb=0, ub=self.C_VRFI)
        self.V_A = m.addVars(self.anos, self.months, name="V_A", lb=0, ub=self.C_TIPO_A)
        self.V_B = m.addVars(self.anos, self.months, name="V_B", lb=0, ub=self.C_TIPO_B)
    
        # 5.4.2 llenados            
        self.Q_alm = m.addVars(self.anos, self.months, name="Q_alm", lb=0)  # Caudal almacenable
        self.Q_dis = m.addVars(self.anos, self.months, name="Q_dis", lb=0)  # Caudal disponible
        self.IN_VRFI = m.addVars(self.anos, self.months, name="IN_VRFI", lb=0)  # Entrada a VRFI        
        self.IN_A = m.addVars(self.anos, self.months, name="IN_A", lb=0)  # Entrada a A
        self.IN_B = m.addVars(self.anos, self.months, name="IN_B", lb=0)  # entrada a b

        # 5.4.3. DESCARGAS a pie de presa (en Hm³/mes)
        #self.Q_pref = m.addVars(self.anos, self.months, name="Q_pref", lb=0)  # Caudal preferente
        self.Q_ch = m.addVars(self.anos, self.months, name="Q_ch", lb=0)  # Consumo humano
        self.Q_A = m.addVars(self.anos, self.months, name="Q_A", lb=0)  # Descarga A
        self.Q_B = m.addVars(self.anos, self.months, name="Q_B", lb=0)  # Descarga B

        # 5.4.5. REBALSES
        self.E_VRFI = m.addVars(self.anos, self.months, name="E_VRFI", lb=0)  # Rebalse VRFI a A y B
        self.E_A = m.addVars(self.anos, self.months, name="E_A", lb=0)  # Rebalse A a B
        self.E_B = m.addVars(self.anos, self.months, name="E_B", lb=0)  # Rebalse B a A
        self.E_TOT = m.addVars(self.anos, self.months, name="E_TOT", lb=0)
        
        # 5.4.4 Caudal de apoyo de VRFI a entregas
        self.Q_A_apoyo = m.addVars(self.anos, self.months, name="Q_A_apoyo", lb=0)  # Caudal de apoyo a A
        self.Q_B_apoyo = m.addVars(self.anos, self.months, name="Q_B_apoyo", lb=0)  # Caudal de apoyo a B

        # 5.4.6. DÉFICITS (en Hm³/mes)
        self.d_A = m.addVars(self.anos, self.months, name="d_A", lb=0)  # Déficit A
        self.d_B = m.addVars(self.anos, self.months, name="d_B", lb=0)  # Déficit B

        # Variable adicional para caudal turbinado, debo definir esto mejor en las restricciones
        
        
        self.Q_turb = m.addVars(self.anos, self.months, name="Q_turb", lb=0)
        
    def load_flow_data(self, file_path):# REVISAR
        """Cargar datos de caudales desde Excel"""
        xls = pd.ExcelFile(file_path)
        
        # Cargar datos
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
        
        # Process each year - FILTRANDO FILAS VÁLIDAS
        for idx, row in nuble.iterrows():
            year_str = str(row['AÑO'])
            
            # VERIFICAR SI ES UNA FILA VÁLIDA (no promedios, no NaN, tiene formato año)
            if (not pd.isna(row['AÑO']) and 
                isinstance(year_str, str) and 
                '/' in year_str and
                not any(word in year_str.upper() for word in ['PROMEDIO', 'TOTAL', 'MAX', 'MIN'])):
                
                try:
                    year = int(year_str.split('/')[0])  # Extract first year (e.g., 1989 from "1989/1990")
                    
                    # Map Excel columns to model months
                    for excel_col, model_month in zip(excel_col_names, model_month_order):
                        # Store individual flows - VERIFICAR QUE NO SEAN NaN
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
        
    def setup_constraints(self):#ACA HAY Q REVISAR BIEN LAS RESTRICCIONES PQ SON TODAS DE CHAT GPT, 
        m = self.model
        
        data_file = "data/caudales.xlsx"
        self.inflow, self.Q_nuble, self.Q_hoya1, self.Q_hoya2, self.Q_hoya3 = self.load_flow_data(data_file)
        
        
        derechos_MAY_ABR = [52.00, 52.00, 52.00, 52.00, 57.70, 76.22, 69.22, 52.00, 52.00, 52.00, 52.00, 52.00]
        qeco_MAY_ABR = [10.00, 10.35, 14.48, 15.23, 15.23, 15.23, 15.23, 15.23, 12.80, 15.20, 16.40, 17.60]
        
        self.QPD_eff = {}  # Diccionario para QPD efectivo en m³/s
        
        for año in self.anos:
            año_num = int(año.split('/')[0])
            for mes in self.months:

                Q_nuble_m3s = self.Q_nuble.get((año_num, mes), 0)
                
                H_m3s = (self.Q_hoya1.get((año_num, mes), 0) + 
                        self.Q_hoya2.get((año_num, mes), 0) + 
                        self.Q_hoya3.get((año_num, mes), 0))
                
                base95_menos_hoyas = max(0.0, 95.7 - H_m3s)
            
                qpd_nom_ajust = max(derechos_MAY_ABR[mes-1], qeco_MAY_ABR[mes-1], base95_menos_hoyas)
                #asi quedo definido el QPD_effectivo, cualdal preferente efectivo
                self.QPD_eff[año, mes] = min(qpd_nom_ajust, Q_nuble_m3s)
        primer_año = self.anos[0]
        m.addConstr(self.V_VRFI[primer_año, 1] == 0, "inicial_VRFI")#revisar estas restricciones iniciales
        m.addConstr(self.V_A[primer_año, 1] == 0, "inicial_A")  
        m.addConstr(self.V_B[primer_año, 1] == 0, "inicial_B")

        # RESTRICCIONES 
        
        for año in self.anos:
            año_num = int(año.split('/')[0])
            for i, mes in enumerate(self.months):
                seg = self.segundos_por_mes[mes]
                
                Qin_m3s = self.inflow.get((año_num, mes), 0)
                Qin = Qin_m3s * seg / 1_000_000  # Q_afl en Hm³/mes
                
    
                QPD_eff_m3s = self.QPD_eff[año, mes]
                QPD_eff_Hm3 = QPD_eff_m3s * seg / 1_000_000  # QPD_eff en Hm³/mes
                demA = self.demandas_A[i] / 1_000_000  # D_A en Hm³/mes#revisar coherencia en xlsx si correspinde
                demB = self.demandas_B[i] / 1_000_000  # D_B en Hm³/mes
                
                # Stocks previos (manejo de años)
                if i == 0:  # Primer mes del año (ABR)
                    año_anterior = str(año_num - 1) + '/' + str(año_num)
                    if año_anterior in self.anos:
                        V_VRFI_prev = self.V_VRFI[año_anterior, 12]
                        V_A_prev = self.V_A[año_anterior, 12]
                        V_B_prev = self.V_B[año_anterior, 12]
                    else:
                        V_VRFI_prev = 0
                        V_A_prev = 0
                        V_B_prev = 0
                else:
                    V_VRFI_prev = self.V_VRFI[año, mes-1]
                    V_A_prev = self.V_A[año, mes-1]
                    V_B_prev = self.V_B[año, mes-1]
                
                # RESTRICCIONES DE BALANCE DEL RÍO (PDF 1-3)
               
                ''''' ya no sirven pq qpref es parametro no. variable...
                # (1) Balance del río: Q_pref + Q_dis = Q_afl
                m.addConstr( self.Q_pref[año, mes] + self.Q_dis[año, mes] == Qin,
                    f"balance_rio_{año}_{mes}" )
                
                # (2) Q_pref ≤ Q_afl
                m.addConstr(
                    self.Q_pref[año, mes] <= Qin,
                    f"pref_leq_afl_{año}_{mes}")
                
                # (3) Q_pref ≤ QPD_eff  
                m.addConstr( self.Q_pref[año, mes] <= QPD_eff,
                    f"pref_leq_qpd_{año}_{mes}")
                '''

                # RESTRICCIONES DE BALANCE DE NODOS 
                
                # (4) Balance nodo almacenable: Q_dis = E_TOT + Q_alm
                m.addConstr(
                    self.Q_dis[año, mes] == self.E_TOT[año, mes] + self.Q_alm[año, mes],
                    f"balance_almacenable_{año}_{mes}")
                
                # (5) Balance nodo VRFI: Q_alm = IN_VRFI + E_VRFI
                m.addConstr(
                    self.Q_alm[año, mes] == self.IN_VRFI[año, mes] + self.E_VRFI[año, mes],
                    f"balance_vrfi_entrada_{año}_{mes}")
                
                # (6) Balance stock 
                m.addConstr(
                    self.V_VRFI[año, mes] == V_VRFI_prev + 
                    self.IN_VRFI[año, mes] - 
                    self.Q_ch[año, mes] - 
                    self.Q_A_apoyo[año, mes] - 
                    self.Q_B_apoyo[año, mes],
                    f"balance_vrfi_stock_{año}_{mes}"
                )
                
                # (7) Capacidad VRFI
                m.addConstr(
                    self.V_VRFI[año, mes] <= self.C_VRFI,
                    f"capacidad_vrfi_{año}_{mes}"
                )
                
                # (8) Entrada VRFI limitada por capacidad
                m.addConstr(
                    self.IN_VRFI[año, mes] <= self.C_VRFI - V_VRFI_prev + 
                    self.Q_ch[año, mes] + 
                    self.Q_A_apoyo[año, mes] + 
                    self.Q_B_apoyo[año, mes],
                    f"entrada_vrfi_capacidad_{año}_{mes}"
                )
                
                # (11) Distribución 71/29 a A y B desde VRFI
                m.addConstr(
                    self.IN_A[año, mes] == 0.71 * self.E_VRFI[año, mes],
                    f"distribucion_A_{año}_{mes}"
                )
                
                m.addConstr(
                    self.IN_B[año, mes] == 0.29 * self.E_VRFI[año, mes],
                    f"distribucion_B_{año}_{mes}"
                )
                
                # (15) Balance stock A
                m.addConstr(
                    self.V_A[año, mes] == V_A_prev + self.IN_A[año, mes] - self.Q_A[año, mes],
                    f"balance_A_{año}_{mes}"
                )
                
                # (16) Capacidad A
                m.addConstr(
                    self.V_A[año, mes] <= self.C_TIPO_A,
                    f"capacidad_A_{año}_{mes}"
                )
                
                # (18) Balance stock B
                m.addConstr(
                    self.V_B[año, mes] == V_B_prev + self.IN_B[año, mes] - self.Q_B[año, mes],
                    f"balance_B_{año}_{mes}"
                )
                
                # (20) Capacidad B
                m.addConstr(
                    self.V_B[año, mes] <= self.C_TIPO_B,
                    f"capacidad_B_{año}_{mes}"
                )
                
                # =============================================
                # RESTRICCIONES COMPLEMENTARIAS (PDF 22-38)
                # =============================================
                
                # (22) Caudal turbinado
                m.addConstr(
                    self.Q_turb[año, mes] == self.Q_ch[año, mes] + self.Q_A[año, mes] + self.Q_B[año, mes],
                    f"caudal_turbinado_{año}_{mes}"
                )
                
                # (23-24) Definición de déficits
                m.addConstr(
                    self.d_A[año, mes] == demA - self.Q_A[año, mes],
                    f"deficit_A_{año}_{mes}"
                )
                
                m.addConstr(
                    self.d_B[año, mes] == demB - self.Q_B[año, mes],
                    f"deficit_B_{año}_{mes}"
                )
                
                # (33-34) No sobre-servir demanda
                m.addConstr(self.Q_A[año, mes] <= demA, f"no_overserve_A_{año}_{mes}")
                m.addConstr(self.Q_B[año, mes] <= demB, f"no_overserve_B_{año}_{mes}")
                
                # (35-36) Mínimo 50% de demanda
                m.addConstr(self.Q_A[año, mes] >= 0.5 * demA, f"min_50_A_{año}_{mes}")
                m.addConstr(self.Q_B[año, mes] >= 0.5 * demB, f"min_50_B_{año}_{mes}")
                
                # Disponibilidad de entrega
                m.addConstr(self.Q_A[año, mes] <= V_A_prev + self.IN_A[año, mes], f"disp_A_{año}_{mes}")
                m.addConstr(self.Q_B[año, mes] <= V_B_prev + self.IN_B[año, mes], f"disp_B_{año}_{mes}")
                m.addConstr(self.Q_ch[año, mes] <= V_VRFI_prev + self.IN_VRFI[año, mes], f"disp_CH_{año}_{mes}")
            
        
    def set_objective(self):
        """Función objetivo - Minimizar déficit total"""
        total_deficit = gp.quicksum(self.d_A[año, mes] + self.d_B[año, mes] 
                                for año in self.anos for mes in self.months)
        self.model.setObjective(total_deficit, GRB.MINIMIZE)

    def export_to_excel(self, filename="resultados_embalse.xlsx"):
        """Exportar todos los resultados a Excel"""
        
        # Crear DataFrames para cada tipo de variable
        data = []
        
        for año in self.anos:
            año_num = int(año.split('/')[0])
            for mes in self.months:
                seg = self.segundos_por_mes[mes]
                
                # Obtener valores de las variables
                fila = {
                    'Año': año,
                    'Mes': mes,
                    
                    # Volúmenes almacenados
                    'V_VRFI': self.V_VRFI[año, mes].X,
                    'V_A': self.V_A[año, mes].X,
                    'V_B': self.V_B[año, mes].X,
                    
                    # Caudales
                    'Q_dis': self.Q_dis[año, mes].X,
                    'Q_alm': self.Q_alm[año, mes].X,
                    'Q_ch': self.Q_ch[año, mes].X,
                    'Q_A': self.Q_A[año, mes].X,
                    'Q_B': self.Q_B[año, mes].X,
                    'Q_turb': self.Q_turb[año, mes].X,
                    
                    # Entradas
                    'IN_VRFI': self.IN_VRFI[año, mes].X,
                    'IN_A': self.IN_A[año, mes].X,
                    'IN_B': self.IN_B[año, mes].X,
                    
                    # Rebalses
                    'E_VRFI': self.E_VRFI[año, mes].X,
                    'E_A': self.E_A[año, mes].X,
                    'E_B': self.E_B[año, mes].X,
                    'E_TOT': self.E_TOT[año, mes].X,
                    
                    # Déficits
                    'd_A': self.d_A[año, mes].X,
                    'd_B': self.d_B[año, mes].X,
                }
                
                # Agregar parámetros externos
                i = self.months.index(mes)
                QPD_eff_m3s = self.QPD_eff[año, mes]  # ← DEFINIR PRIMERO
                fila['QPD_eff_Hm3'] = QPD_eff_m3s * seg / 1_000_000

                fila['Demanda_A'] = self.demandas_A[i] / 1_000_000
                fila['Demanda_B'] = self.demandas_B[i] / 1_000_000
                
                # Caudales de entrada
                Qin_m3s = self.inflow.get((año_num, mes), 0)
                fila['Q_afl_m3s'] = Qin_m3s
                fila['Q_afl_Hm3'] = Qin_m3s * seg / 1_000_000
                
                # QPD efectivo
                QPD_eff_m3s = self.QPD_eff[año, mes]
                QPD_eff_m3s = self.QPD_eff[año, mes]  # Definir la variable local
                fila['QPD_eff_Hm3'] = QPD_eff_m3s * seg / 1_000_000
                # Indicadores de desempeño
                fila['Deficit_Total'] = fila['d_A'] + fila['d_B']
                fila['Satisfaccion_A'] = (fila['Q_A'] / fila['Demanda_A']) * 100 if fila['Demanda_A'] > 0 else 100
                fila['Satisfaccion_B'] = (fila['Q_B'] / fila['Demanda_B']) * 100 if fila['Demanda_B'] > 0 else 100
                fila['Satisfaccion_Total'] = ((fila['Q_A'] + fila['Q_B']) / (fila['Demanda_A'] + fila['Demanda_B'])) * 100 if (fila['Demanda_A'] + fila['Demanda_B']) > 0 else 100
                
                data.append(fila)
        
        # Crear DataFrame principal
        df_main = pd.DataFrame(data)
        
        # Crear resumen anual
        resumen_anual = []
        for año in self.anos:
            df_año = df_main[df_main['Año'] == año]
            resumen = {
                'Año': año,
                'Deficit_Total_Anual': df_año['Deficit_Total'].sum(),
                'Deficit_A_Anual': df_año['d_A'].sum(),
                'Deficit_B_Anual': df_año['d_B'].sum(),
                'Volumen_Turbinado_Anual': df_año['Q_turb'].sum(),
                'Demanda_Total_Anual': df_año['Demanda_A'].sum() + df_año['Demanda_B'].sum(),
                'Satisfaccion_Promedio': df_año['Satisfaccion_Total'].mean(),
                'Mes_Mayor_Deficit': df_año.loc[df_año['Deficit_Total'].idxmax(), 'Mes'] if df_año['Deficit_Total'].max() > 0 else 'Ninguno'
            }
            resumen_anual.append(resumen)
        
        df_resumen = pd.DataFrame(resumen_anual)
        
        # Crear Excel con múltiples hojas
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_main.to_excel(writer, sheet_name='Resultados_Detallados', index=False)
            df_resumen.to_excel(writer, sheet_name='Resumen_Anual', index=False)
            
            # Agregar hoja de estadísticas
            stats = {
                'Métrica': [
                    'Déficit Total (Hm³)',
                    'Déficit A (Hm³)',
                    'Déficit B (Hm³)',
                    'Satisfacción Promedio (%)',
                    'Volumen Turbinado Total (Hm³)'
                ],
                'Valor': [
                    df_main['Deficit_Total'].sum(),
                    df_main['d_A'].sum(),
                    df_main['d_B'].sum(),
                    df_main['Satisfaccion_Total'].mean(),
                    df_main['Q_turb'].sum()
                ]
            }
            df_stats = pd.DataFrame(stats)
            df_stats.to_excel(writer, sheet_name='Estadisticas_Globales', index=False)
        
        print(f"✅ Resultados exportados a {filename}")
        print(f"📊 Déficit total: {df_main['Deficit_Total'].sum():.2f} Hm³")
        print(f"📈 Satisfacción promedio: {df_main['Satisfaccion_Total'].mean():.1f}%")
        
        return df_main, df_resumen
    def solve(self):
        """Resolver el modelo"""            
        try:
                # Cargar datos
            data_file = "data/caudales.xlsx"
            self.inflow, self.Q_nuble, self.Q_hoya1, self.Q_hoya2, self.Q_hoya3 = self.load_flow_data(data_file)
                
                # Configurar modelo
            self.setup_variables()
            self.setup_constraints()
            self.set_objective()
                
                # Optimizar
            self.model.optimize()
                
            if self.model.status == GRB.OPTIMAL:
                    return self.get_solution()
            else:
                print(f"Modelo no resuelto optimalmente. Status: {self.model.status}")
                return None
                    
        except Exception as e:
            print(f"Error al resolver el modelo: {e}")
            return None

    def get_solution(self):
        """Extraer la solución del modelo"""
        solution = {
            'status': self.model.status,
            'obj_val': self.model.objVal,
        }
        
        # Exportar resultados a Excel
        df_detalle, df_resumen = self.export_to_excel()
        solution['df_detalle'] = df_detalle
        solution['df_resumen'] = df_resumen
        
        return solution


# main.py llamarlo #esto se llama main_modelito2.py
