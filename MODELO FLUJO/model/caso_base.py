# model/modelo_caso_base.py
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

class EmbalseCasoBase:
    """
    MODELO DE OPERACIÓN SIMPLIFICADO — Caso Base Embalse Nueva Punilla
    
    Características:
    - Solo volumen total del embalse (no separación A/B)
    - No hay prioridad de llenado 
    - Demanda humana fija = self.V_C_H (Hm³/año) repartida mes a mes (V_C_H/12)
    - Lógica FIFO simplificada
    """

    def __init__(self):
        self.model = gp.Model("Embalse_Caso_Base")

        # ============ CONJUNTOS ============
        self.anos = ['1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
                     '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
                     '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
                     '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
                     '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
                     '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019']
        self.months = list(range(1, 13))  # 1..12 = MAY..ABR

        # ============ CAPACIDAD TOTAL (Hm³) ============
        self.C_TOTAL = 540  # 175 + 260 + 105

        # ============ SEGUNDOS POR MES ============
        self.segundos_por_mes = {
            1: 31*24*3600,  # MAY
            2: 30*24*3600,  # JUN
            3: 31*24*3600,  # JUL
            4: 31*24*3600,  # AGO
            5: 30*24*3600,  # SEP
            6: 31*24*3600,  # OCT
            7: 30*24*3600,  # NOV
            8: 31*24*3600,  # DIC
            9: 31*24*3600,  # ENE
            10: 28*24*3600, # FEB
            11: 31*24*3600, # MAR
            12: 30*24*3600  # ABR
        }

        # ============ DATOS (m³/s) ============
        self.inflow  = {}
        self.Q_nuble = {}
        self.Q_hoya1 = {}
        self.Q_hoya2 = {}
        self.Q_hoya3 = {}

        # ============ DEMANDA TOTAL (parámetros) ============
        # Los parámetros mensuales por acción se mantienen tal cual (valores constantes)
        self.num_A = 21221
        self.num_B = 7100
        self.DA_a_m = {1:9503,2:6516,3:3452,4:776,5:0,6:0,7:0,8:0,9:0,10:2444,11:6516,12:9580}
        self.DB_a_b = {1:3361,2:2305,3:1221,4:274,5:0,6:0,7:0,8:0,9:0,10: 864,11:2305,12:3388}

        # Mapeo mes modelo (1..12=MAY..ABR) → mes civil (ene=1,...,dic=12)
        self.m_mayo_abril_to_civil = {1:5,2:6,3:7,4:8,5:9,6:10,7:11,8:12,9:1,10:2,11:3,12:4}

        # ============ SSR (Hm³/año) ============
        # Nota: según tu instrucción, usamos este valor (V_C_H) también como la
        # demanda humana fija anual que se repartirá en 12 meses.
        self.V_C_H = 3.9
        self.fix_ssr_monthly = False
        self.ssr_frac = {1:0.10,2:0.10,3:0.15,4:0.20,5:0.15,6:0.10,7:0.10,8:0.05,9:0.0,10:0.0,11:0.0,12:0.05}

        # atributo que guardará la DEMANDA HUMANA mensual fija (Hm³/mes)
        # se llenará en setup_constraints() como self.V_C_H / 12
        self.human_dem_monthly = None

    # ===================== Variables =====================
    def setup_variables(self):
        m = self.model
        
        # Stocks (Hm³)
        self.V_TOTAL = m.addVars(self.anos, self.months, name="V_TOTAL", lb=0, ub=self.C_TOTAL)

        # Llenados y rebalse (Hm³/mes)
        self.IN_TOTAL = m.addVars(self.anos, self.months, name="IN_TOTAL", lb=0)
        self.E_TOT = m.addVars(self.anos, self.months, name="E_TOT", lb=0)

        # Entregas (Hm³/mes)
        self.Q_ch = m.addVars(self.anos, self.months, name="Q_ch", lb=0)   # SSR
        self.Q_DEM = m.addVars(self.anos, self.months, name="Q_DEM", lb=0) # Servicio demanda total

        # Déficits
        self.d_TOTAL = m.addVars(self.anos, self.months, name="d_TOTAL", lb=0)

        # Turbinado
        self.Q_turb = m.addVars(self.anos, self.months, name="Q_turb", lb=0)

        # Para reporte
        self.Q_dis = m.addVars(self.anos, self.months, name="Q_dis", lb=0)

        # Auxiliares de llenado
        self.Rem = m.addVars(self.anos, self.months, name="Rem", lb=0)
        self.HeadT = m.addVars(self.anos, self.months, name="HeadT", lb=0)
        self.FillT = m.addVars(self.anos, self.months, name="FillT", lb=0)

    # ===================== Datos =====================
    def load_flow_data(self, file_path):
        xls = pd.ExcelFile(file_path)
        nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4,  nrows=31)
        hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=39, nrows=31)
        hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=75, nrows=31)
        hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=110,nrows=31)

        excel_col_names = ['MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC','ENE','FEB','MAR','ABR']
        model_month_order = [1,2,3,4,5,6,7,8,9,10,11,12]

        Q_nuble, Q_hoya1, Q_hoya2, Q_hoya3, Q_afl = {},{},{},{},{}

        for idx, row in nuble.iterrows():
            year_str = str(row.get('AÑO',''))
            if (pd.notna(row.get('AÑO')) and '/' in year_str
                and not any(w in year_str.upper() for w in ['PROMEDIO','TOTAL','MAX','MIN'])):
                try:
                    year = int(year_str.split('/')[0])
                    for col, mm in zip(excel_col_names, model_month_order):
                        n1 = nuble.loc[idx, col]; h1 = hoya1.loc[idx, col]
                        h2 = hoya2.loc[idx, col]; h3 = hoya3.loc[idx, col]
                        if pd.notna(n1): Q_nuble[year, mm] = float(n1); Q_afl[year, mm] = float(n1)
                        if pd.notna(h1): Q_hoya1[year, mm] = float(h1)
                        if pd.notna(h2): Q_hoya2[year, mm] = float(h2)
                        if pd.notna(h3): Q_hoya3[year, mm] = float(h3)
                except Exception:
                    pass
        return Q_afl, Q_nuble, Q_hoya1, Q_hoya2, Q_hoya3

    # ===================== Restricciones =====================
    def setup_constraints(self):
        m = self.model
        data_file = "data/caudales.xlsx"
        self.inflow, self.Q_nuble, self.Q_hoya1, self.Q_hoya2, self.Q_hoya3 = self.load_flow_data(data_file)

        # QPD efectivo (m³/s) en MAY..ABR
        derechos_MAY_ABR = [52.00,52.00,52.00,52.00,57.70,76.22,69.22,52.00,52.00,52.00,52.00,52.00]
        qeco_MAY_ABR = [10.00,10.35,14.48,15.23,15.23,15.23,15.23,15.23,12.80,15.20,16.40,17.60]
        self.QPD_eff = {}
        for año in self.anos:
            y = int(año.split('/')[0])
            for mes in self.months:
                H = self.Q_hoya1.get((y,mes),0.0) + self.Q_hoya2.get((y,mes),0.0) + self.Q_hoya3.get((y,mes),0.0)
                qpd_nom = max(derechos_MAY_ABR[mes-1], qeco_MAY_ABR[mes-1], max(0.0, 95.7 - H))
                self.QPD_eff[año, mes] = min(qpd_nom, self.Q_nuble.get((y,mes),0.0))

        # Iniciales (MAY del primer año)
        primer = self.anos[0]
        m.addConstr(self.V_TOTAL[primer,1] == 0, name="init_TOTAL")

        # -------------------------------------------------------------------
        # AQUÍ: usamos self.V_C_H (3.9 Hm³/año) como la demanda humana fija anual
        # y la repartimos uniformemente en 12 meses: human_dem_monthly = V_C_H / 12
        # -------------------------------------------------------------------
        self.human_dem_monthly = self.V_C_H / 12.0
        # -------------------------------------------------------------------

        for año in self.anos:
            y = int(año.split('/')[0])
            for i, mes in enumerate(self.months):
                seg = self.segundos_por_mes[mes]
                Qin_s = self.inflow.get((y,mes), 0.0)
                Qin = Qin_s * seg / 1_000_000.0
                UPREF = self.QPD_eff[año, mes] * seg / 1_000_000.0

                # Demanda TOTAL ahora: la DEMANDA HUMANA FIJA (V_C_H) repartida mes a mes
                demTOTAL = self.human_dem_monthly

                # Stock previo
                if i == 0:
                    prev_año = f"{y-1}/{y}"
                    V_prev = self.V_TOTAL[prev_año,12] if prev_año in self.anos else 0
                else:
                    V_prev = self.V_TOTAL[año, mes-1]

                # (1) Remanente y llenado simplificado
                m.addConstr(self.Rem[año,mes] == Qin - UPREF, name=f"rem_{año}_{mes}")
                m.addConstr(self.HeadT[año,mes] == self.C_TOTAL - V_prev, name=f"headT_{año}_{mes}")
                
                # Llenado: min(Rem, HeadT)
                m.addGenConstrMin(self.FillT[año,mes], [self.Rem[año,mes], self.HeadT[año,mes]], 
                                 name=f"fillT_min_{año}_{mes}")
                m.addConstr(self.IN_TOTAL[año,mes] == self.FillT[año,mes], name=f"in_total_{año}_{mes}")

                # (2) Rebalse (lo que no cabe)
                m.addConstr(self.E_TOT[año,mes] == self.Rem[año,mes] - self.IN_TOTAL[año,mes],
                           name=f"spill_{año}_{mes}")

                # Para reporte
                m.addConstr(self.Q_dis[año,mes] == Qin - UPREF, name=f"qdis_{año}_{mes}")

                # (3) Balance de stock
                m.addConstr(
                    self.V_TOTAL[año,mes] == V_prev + self.IN_TOTAL[año,mes] - self.Q_DEM[año,mes] - self.Q_ch[año,mes],
                    name=f"bal_total_{año}_{mes}"
                )
                m.addConstr(self.V_TOTAL[año,mes] <= self.C_TOTAL, name=f"cap_total_{año}_{mes}")

                # (4) Disponibilidad para servir
                m.addConstr(self.Q_DEM[año,mes] <= V_prev + self.IN_TOTAL[año,mes], name=f"disp_dem_{año}_{mes}")
                m.addConstr(self.Q_ch[año,mes] <= V_prev + self.IN_TOTAL[año,mes], name=f"disp_ch_{año}_{mes}")

                # (5) Servir hasta demanda disponible
                m.addConstr(self.Q_DEM[año,mes] <= demTOTAL + 1e-9, name=f"nosobre_dem_{año}_{mes}")

                # (6) Déficit
                m.addConstr(self.d_TOTAL[año,mes] == demTOTAL - self.Q_DEM[año,mes], name=f"def_total_{año}_{mes}")

                # (7) Turbinado (simplificado)
                m.addConstr(self.Q_turb[año,mes] == self.Q_DEM[año,mes] + self.E_TOT[año,mes],
                           name=f"turb_{año}_{mes}")

        # (8) SSR: anual o mensual fija
        if self.fix_ssr_monthly:
            for año in self.anos:
                for mes in self.months:
                    m.addConstr(self.Q_ch[año, mes] == self.V_C_H * float(self.ssr_frac.get(mes, 0.0)),
                               name=f"ssr_mes_{año}_{mes}")
        else:
            for año in self.anos:
                m.addConstr(gp.quicksum(self.Q_ch[año, mes] for mes in self.months) == self.V_C_H,
                           name=f"ssr_anual_{año}")

    # ===================== Objetivo =====================
    def set_objective(self):
        """ Minimiza déficit total """
        total_def = gp.quicksum(self.d_TOTAL[año,mes] for año in self.anos for mes in self.months)
        self.model.setObjective(total_def, GRB.MINIMIZE)

    # ===================== Exportar resultados a Excel =====================
    def export_to_excel(self, filename="resultados_caso_base.xlsx"):
        data = []
        # usar self.human_dem_monthly (demanda fija mensual) en los reportes para coherencia
        dem_month = self.human_dem_monthly if self.human_dem_monthly is not None else 0.0

        for año in self.anos:
            y = int(año.split('/')[0])
            for mes in self.months:
                seg = self.segundos_por_mes[mes]
                Qin_m3s = self.inflow.get((y,mes), 0.0)
                Qin = Qin_m3s * seg / 1_000_000.0
                QPD_eff_Hm3 = self.QPD_eff[año,mes] * seg / 1_000_000.0

                # demTOTAL en reportes = demanda humana mensual fija
                demTOTAL = dem_month

                fila = {
                    'Año': año, 'Mes': mes,
                    'V_TOTAL': self.V_TOTAL[año,mes].X,
                    'Q_dis': self.Q_dis[año,mes].X,
                    'Q_ch': self.Q_ch[año,mes].X,
                    'Q_DEM': self.Q_DEM[año,mes].X,
                    'Q_turb': self.Q_turb[año,mes].X,
                    'IN_TOTAL': self.IN_TOTAL[año,mes].X,
                    'E_TOT': self.E_TOT[año,mes].X,
                    'd_TOTAL': self.d_TOTAL[año,mes].X,
                    'QPD_eff_Hm3': QPD_eff_Hm3,
                    'Demanda_Total': demTOTAL,
                    'Q_afl_m3s': Qin_m3s,
                    'Q_afl_Hm3': Qin,
                    'Rem': self.Rem[año,mes].X,
                    'FillT': self.FillT[año,mes].X
                }
                
                servTOTAL = fila['Q_DEM']
                fila['Deficit_Total'] = fila['d_TOTAL']
                fila['Satisfaccion_Total'] = (servTOTAL/demTOTAL*100) if demTOTAL > 0 else 100
                data.append(fila)

        df_main = pd.DataFrame(data)
        resumen = []
        for año in self.anos:
            d = df_main[df_main['Año']==año]
            resumen.append({
                'Año': año,
                'Deficit_Total_Anual': d['Deficit_Total'].sum(),
                'Volumen_Turbinado_Anual': d['Q_turb'].sum(),
                'Demanda_Total_Anual': d['Demanda_Total'].sum(),
                'Satisfaccion_Promedio': d['Satisfaccion_Total'].mean(),
                'Mes_Mayor_Deficit': (d.loc[d['Deficit_Total'].idxmax(),'Mes'] 
                                    if d['Deficit_Total'].max()>0 else 'Ninguno')
            })
        df_res = pd.DataFrame(resumen)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as w:
            df_main.to_excel(w, sheet_name='Resultados_Detallados', index=False)
            df_res.to_excel(w, sheet_name='Resumen_Anual', index=False)
        
        print(f"✅ Resultados exportados a {filename}")
        print(f"📊 Déficit total: {df_main['Deficit_Total'].sum():.2f} Hm³")
        print(f"📈 Satisfacción promedio: {df_main['Satisfaccion_Total'].mean():.1f}%")
        return df_main, df_res

    # ===================== Exportar reporte TXT =====================
    def export_to_txt(self, filename="reporte_caso_base.txt"):
        def bar20(pct):
            n = int(round(min(max(pct,0),100) / 5.0))
            return "█"*n + "·"*(20-n)

        mes_tag = {1:'may',2:'jun',3:'jul',4:'ago',5:'sep',6:'oct',7:'nov',8:'dic',9:'ene',10:'feb',11:'mar',12:'abr'}
        lines = []
        
        # usar self.human_dem_monthly en el reporte
        dem_month = self.human_dem_monthly if self.human_dem_monthly is not None else 0.0

        for año in self.anos:
            y = int(año.split('/')[0])

            lines.append("="*50)
            lines.append(f"REPORTE CASO BASE: {año}")
            lines.append("="*50)
            lines.append("Tabla 1 — Física del sistema (Hm³)")
            header1 = ("Mes   Qin_m3s  Qin_Hm3  QPD_Hm3  IN_TOTAL  E_TOT    V_prev→V_fin   %lleno  |  Stock")
            lines.append(header1)
            lines.append("-"*100)

            for i, mes in enumerate(self.months):
                seg = self.segundos_por_mes[mes]
                Qin_m3s = self.inflow.get((y,mes), 0.0)
                Qin_Hm3 = Qin_m3s * seg / 1_000_000.0
                QPD_Hm3 = self.QPD_eff[año,mes] * seg / 1_000_000.0

                IN_TOTAL = self.IN_TOTAL[año, mes].X
                E_TOT = self.E_TOT[año, mes].X

                if i == 0:
                    prev_año = f"{y-1}/{y}"
                    V_prev = self.V_TOTAL[prev_año,12].X if prev_año in self.anos else 0.0
                else:
                    V_prev = self.V_TOTAL[año, mes-1].X

                V_fin = self.V_TOTAL[año, mes].X
                pct_lleno = (V_fin / self.C_TOTAL * 100) if self.C_TOTAL > 0 else 0
                bar = bar20(pct_lleno)

                row1 = (f"{mes_tag[mes]:<4} "
                        f"{Qin_m3s:8.2f}  {Qin_Hm3:7.1f}  {QPD_Hm3:7.1f}  "
                        f"{IN_TOTAL:8.1f}  {E_TOT:6.1f}  "
                        f"{V_prev:5.1f}→{V_fin:<5.1f}  {pct_lleno:5.1f}%  |  "
                        f"V[{V_fin:6.1f}] {bar}")
                lines.append(row1)

            # ================== TABLA 2 ==================
            lines.append("")
            lines.append("Tabla 2 — Servicio y SSR (Hm³)")
            header2 = ("Mes   Demanda_T  Servicio  Déficit   Q_SSR    Qturb")
            lines.append(header2)
            lines.append("-"*70)

            for i, mes in enumerate(self.months):
                demTOTAL = dem_month

                servicio = self.Q_DEM[año, mes].X
                deficit = self.d_TOTAL[año, mes].X
                Q_SSR = self.Q_ch[año, mes].X
                Qturb = self.Q_turb[año, mes].X

                row2 = (f"{mes_tag[mes]:<4} "
                        f"{demTOTAL:9.1f}  {servicio:8.1f}  {deficit:8.1f}  "
                        f"{Q_SSR:7.1f}  {Qturb:7.1f}")
                lines.append(row2)

            lines.append("")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"📝 Reporte TXT escrito en {filename}")
        return filename

    # ===================== Solve =====================
    def solve(self):
        try:
            data_file = "data/caudales.xlsx"
            self.inflow, self.Q_nuble, self.Q_hoya1, self.Q_hoya2, self.Q_hoya3 = self.load_flow_data(data_file)
            self.setup_variables()
            self.setup_constraints()
            self.set_objective()
            self.model.optimize()
            if self.model.status in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
                print(f"\n📊 MÉTRICAS DE OPTIMIZACIÓN:")
                print(f"   - Status: {self.model.status}")
                print(f"   - Valor objetivo: {self.model.objVal:.4f}")
                print(f"   - Tiempo de resolución: {self.model.Runtime:.2f} segundos")
                print(f"   - Gap de optimalidad: {self.model.MIPGap * 100:.6f}%")
                print(f"   - Nodos explorados: {self.model.NodeCount}")
                
                return self.get_solution()
            print(f"Modelo no resuelto optimalmente. Status: {self.model.status}")
            return None
        except Exception as e:
            print(f"Error al resolver el modelo: {e}")
            return None

    def get_solution(self):
        sol = {'status': self.model.status, 'obj_val': self.model.objVal}
        df_det, df_res = self.export_to_excel()
        sol['df_detalle'] = df_det
        sol['df_resumen'] = df_res
        txt_file = self.export_to_txt()
        sol['txt_file'] = txt_file
        return sol


# ===================== MAIN =====================
if __name__ == "__main__":
    print("🚀 Iniciando modelo de caso base...")
    modelo = EmbalseCasoBase()
    solucion = modelo.solve()
    
    if solucion:
        print("✅ Modelo resuelto exitosamente!")
        print(f"📊 Valor objetivo: {solucion['obj_val']:.4f}")
        print(f"📁 Archivos generados:")
        print(f"   - Excel: resultados_caso_base.xlsx")
        print(f"   - TXT: reporte_caso_base.txt")

    else:
        print("❌ Error al resolver el modelo")
