# model/modelito2.py
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

class EmbalseNuevaPunilla:
    """
    MODELO DE OPERACIÓN SIMPLIFICADO — Embalse Nueva Punilla

    Claves:
    - SSR mensual = 3.9/12 Hm³ con backlog y prioridad: Q_ch = min(SSR_due, V_R_prev + IN_VRFI).
    - Piso VRFI reservado (NO para A/B) = 1.5 Hm³: VRFI_avail_free = max(V_R_prev + IN - Q_ch - 1.5, 0).
    - Reparto de apoyo VRFI 71/29 con reasignación de excedentes.
    - FIX 1: cota dura Q_A_apoyo + Q_B_apoyo ≤ VRFI_avail_free (evita V_VRFI < 0).
    - FIX 2: sin igualdades de “stock MAY = 0”; uso parámetros de stock inicial si no hay año previo.
    - FIX 3: min() de SSR usa variable auxiliar (evita “Invalid data in vars array”).
    - FIX 4: escribir solo IIS en .ilp (Gurobi 12).
    """

    def __init__(self):
        self.model = gp.Model("Embalse_Nueva_Punilla")

        # ============ CONJUNTOS ============
        self.anos = ['1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
                     '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
                     '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
                     '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
                     '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
                     '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019']
        self.months = list(range(1, 13))  # 1..12 = MAY..ABR

        # ============ CAPACIDADES (Hm³) ============
        self.C_VRFI   = 175
        self.C_TIPO_A = 260
        self.C_TIPO_B = 105

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

        # ============ DEMANDAS (m³/mes por acción) ============
        self.num_A = 21221
        self.num_B = 7100
        self.DA_a_m = {1:9503,2:6516,3:3452,4:776,5:0,6:0,7:0,8:0,9:0,10:2444,11:6516,12:9580}
        self.DB_a_b = {1:3361,2:2305,3:1221,4:274,5:0,6:0,7:0,8:0,9:0,10: 864,11:2305,12:3388}

        # Mapeo mes modelo (1..12=MAY..ABR) → mes civil (ene=1,...,dic=12)
        self.m_mayo_abril_to_civil = {1:5,2:6,3:7,4:8,5:9,6:10,7:11,8:12,9:1,10:2,11:3,12:4}

        self.FEA = 1.0
        self.FEB = 1.0

        # ============ SSR (Hm³/año) ============
        self.V_C_H = 3.9
        self.ssr_carry_between_years = True  # arrastra backlog de abril a mayo

        # Piso de reserva VRFI (Hm³) protegido contra A/B
        self.RSV_FLOOR = 1.625

        # Stocks iniciales (si no hay año previo)
        self.VRFI_init = 0.0
        self.VA_init   = 0.0
        self.VB_init   = 0.0

        # Energía no usada
        self.MWh_per_Hm3 = 0.0

    # ===================== Variables =====================
    def setup_variables(self):
        m = self.model
        # Stocks (Hm³)
        self.V_VRFI = m.addVars(self.anos, self.months, name="V_VRFI", lb=0, ub=self.C_VRFI)
        self.V_A    = m.addVars(self.anos, self.months, name="V_A", lb=0, ub=self.C_TIPO_A)
        self.V_B    = m.addVars(self.anos, self.months, name="V_B", lb=0, ub=self.C_TIPO_B)

        # Llenados y rebalse (Hm³/mes)
        self.IN_VRFI = m.addVars(self.anos, self.months, name="IN_VRFI", lb=0)
        self.IN_A    = m.addVars(self.anos, self.months, name="IN_A", lb=0)
        self.IN_B    = m.addVars(self.anos, self.months, name="IN_B", lb=0)
        self.E_TOT   = m.addVars(self.anos, self.months, name="E_TOT", lb=0)

        # Entregas (Hm³/mes)
        self.Q_ch = m.addVars(self.anos, self.months, name="Q_ch", lb=0)   # SSR (consumo humano)
        self.Q_A  = m.addVars(self.anos, self.months, name="Q_A",  lb=0)   # Propio A
        self.Q_B  = m.addVars(self.anos, self.months, name="Q_B",  lb=0)   # Propio B

        # Apoyo VRFI (hasta 50%)
        self.Q_A_apoyo = m.addVars(self.anos, self.months, name="Q_A_apoyo", lb=0)
        self.Q_B_apoyo = m.addVars(self.anos, self.months, name="Q_B_apoyo", lb=0)

        # Déficits
        self.d_A = m.addVars(self.anos, self.months, name="d_A", lb=0)
        self.d_B = m.addVars(self.anos, self.months, name="d_B", lb=0)

        # Turbinado (SSR no turbina)
        self.Q_turb = m.addVars(self.anos, self.months, name="Q_turb", lb=0)

        # Para reporte
        self.Q_dis = m.addVars(self.anos, self.months, name="Q_dis", lb=-GRB.INFINITY)

        # Auxiliares de llenado
        self.Rem    = m.addVars(self.anos, self.months, name="Rem",   lb=0)
        self.HeadR  = m.addVars(self.anos, self.months, name="HeadR", lb=0)
        self.FillR  = m.addVars(self.anos, self.months, name="FillR", lb=0)
        self.zR     = m.addVars(self.anos, self.months, name="zR",    lb=0)
        self.HeadA  = m.addVars(self.anos, self.months, name="HeadA", lb=0)
        self.HeadB  = m.addVars(self.anos, self.months, name="HeadB", lb=0)
        self.ShareA = m.addVars(self.anos, self.months, name="ShareA",lb=0)
        self.ShareB = m.addVars(self.anos, self.months, name="ShareB",lb=0)
        self.FillA  = m.addVars(self.anos, self.months, name="FillA", lb=0)
        self.FillB  = m.addVars(self.anos, self.months, name="FillB", lb=0)

        # Auxiliares “faltante para 50%”
        self.needA  = m.addVars(self.anos, self.months, name="needA", lb=0)
        self.needB  = m.addVars(self.anos, self.months, name="needB", lb=0)

        # Totales de apoyo y disponibilidad post-SSR (libre para A/B)
        self.VRFI_avail_free = m.addVars(self.anos, self.months, name="VRFI_avail_free", lb=0)
        self.needTot     = m.addVars(self.anos, self.months, name="needTot", lb=0)
        self.SupportTot  = m.addVars(self.anos, self.months, name="SupportTot", lb=0)

        # Recorte Rem a ≥ 0
        self.RemRaw = m.addVars(self.anos, self.months, name="RemRaw", lb=-GRB.INFINITY)

        # Constante cero (para MAX)
        self.zeroVar = m.addVar(lb=0.0, ub=0.0, name="zeroConst")

        # (opcional debug)
        self.A_avail   = m.addVars(self.anos, self.months, name="A_avail")
        self.A_dem50   = m.addVars(self.anos, self.months, name="A_dem50", lb=0.0)
        self.A_own_req = m.addVars(self.anos, self.months, name="A_own_req", lb=0.0)
        self.B_avail   = m.addVars(self.anos, self.months, name="B_avail")
        self.B_dem50   = m.addVars(self.anos, self.months, name="B_dem50", lb=0.0)
        self.B_own_req = m.addVars(self.anos, self.months, name="B_own_req", lb=0.0)
        self.tA = m.addVars(self.anos, self.months, name="tA")
        self.tB = m.addVars(self.anos, self.months, name="tB")
        self.rA = m.addVars(self.anos, self.months, name="rA", lb=0.0)
        self.rB = m.addVars(self.anos, self.months, name="rB", lb=0.0)

        # Reparto proporcional 71/29 del apoyo VRFI
        self.pA = m.addVars(self.anos, self.months, name="pA")
        self.pB = m.addVars(self.anos, self.months, name="pB")
        self.allocA_base = m.addVars(self.anos, self.months, name="allocA_base", lb=0.0)
        self.allocB_base = m.addVars(self.anos, self.months, name="allocB_base", lb=0.0)
        self.surplusA = m.addVars(self.anos, self.months, name="surplusA", lb=0.0)
        self.surplusB = m.addVars(self.anos, self.months, name="surplusB", lb=0.0)
        self.gapA     = m.addVars(self.anos, self.months, name="gapA",     lb=0.0)
        self.gapB     = m.addVars(self.anos, self.months, name="gapB",     lb=0.0)
        self.extra_to_A = m.addVars(self.anos, self.months, name="extra_to_A", lb=0.0)
        self.extra_to_B = m.addVars(self.anos, self.months, name="extra_to_B", lb=0.0)

        # ===== SSR mensual con rezago y prioridad dura =====
        self.SSR_due     = m.addVars(self.anos, self.months, name="SSR_due", lb=0.0)
        self.SSR_backlog = m.addVars(self.anos, self.months, name="SSR_backlog", lb=0.0)
        # Capacidad (variable auxiliar) para usar en min()
        self.SSR_cap_var = m.addVars(self.anos, self.months, name="SSR_cap_var", lb=0.0)

    # ===================== Datos =====================
    def load_flow_data(self, file_path):
        xls = pd.ExcelFile(file_path)
        nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4,  nrows=31)
        hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=39, nrows=31)
        hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=75, nrows=31)
        hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=110,nrows=31)

        excel_col_names   = ['MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC','ENE','FEB','MAR','ABR']
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
        qeco_MAY_ABR     = [10.00,10.35,14.48,15.23,15.23,15.23,15.23,15.23,12.80,15.20,16.40,17.60]
        self.QPD_eff = {}
        for año in self.anos:
            y = int(año.split('/')[0])
            for mes in self.months:
                H = self.Q_hoya1.get((y,mes),0.0) + self.Q_hoya2.get((y,mes),0.0) + self.Q_hoya3.get((y,mes),0.0)
                qpd_nom = max(derechos_MAY_ABR[mes-1], qeco_MAY_ABR[mes-1], max(0.0, 95.7 - H))
                self.QPD_eff[año, mes] = min(qpd_nom, self.Q_nuble.get((y,mes),0.0))

        # SSR mensual (3.9/12) con backlog y prioridad dura
        ssr_month = self.V_C_H / 12.0

        for a_idx, año in enumerate(self.anos):
            y = int(año.split('/')[0])
            for i, mes in enumerate(self.months):
                seg   = self.segundos_por_mes[mes]
                Qin_s = self.inflow.get((y,mes), 0.0)
                Qin   = Qin_s * seg / 1_000_000.0
                UPREF = self.QPD_eff[año, mes] * seg / 1_000_000.0

                key   = self.m_mayo_abril_to_civil[mes]
                demA  = (self.DA_a_m[key] * self.num_A * self.FEA) / 1_000_000.0
                demB  = (self.DB_a_b[key] * self.num_B * self.FEB) / 1_000_000.0

                # Stocks previos (si no hay año previo, uso parámetros *_init)
                if i == 0:
                    if a_idx > 0:
                        prev_año = self.anos[a_idx-1]
                        V_R_prev = self.V_VRFI[prev_año,12]
                        V_A_prev = self.V_A[prev_año,12]
                        V_B_prev = self.V_B[prev_año,12]
                    else:
                        V_R_prev = self.model.addVar(lb=self.VRFI_init, ub=self.VRFI_init, name="VRFI_prev_init")
                        V_A_prev = self.model.addVar(lb=self.VA_init,   ub=self.VA_init,   name="VA_prev_init")
                        V_B_prev = self.model.addVar(lb=self.VB_init,   ub=self.VB_init,   name="VB_prev_init")
                else:
                    V_R_prev = self.V_VRFI[año, mes-1]
                    V_A_prev = self.V_A[año,  mes-1]
                    V_B_prev = self.V_B[año,  mes-1]

                # (1) Remanente con recorte a ≥ 0
                m.addConstr(self.RemRaw[año,mes] == Qin - UPREF, name=f"remraw_{año}_{mes}")
                m.addGenConstrMax(self.Rem[año,mes], [self.RemRaw[año,mes], self.zeroVar],
                                  name=f"rem_clip0_{año}_{mes}")

                # Prioridad de llenado con Rem
                m.addConstr(self.HeadR[año,mes]  == self.C_VRFI  - V_R_prev,  name=f"headR_{año}_{mes}")
                m.addConstr(self.HeadA[año,mes]  == self.C_TIPO_A - V_A_prev,  name=f"headA_{año}_{mes}")
                m.addConstr(self.HeadB[año,mes]  == self.C_TIPO_B - V_B_prev,  name=f"headB_{año}_{mes}")

                m.addGenConstrMin(self.FillR[año,mes], [self.Rem[año,mes], self.HeadR[año,mes]],
                                  name=f"fillR_min_{año}_{mes}")
                m.addConstr(self.zR[año,mes]     == self.Rem[año,mes] - self.FillR[año,mes], name=f"zR_{año}_{mes}")
                m.addConstr(self.ShareA[año,mes] == 0.71 * self.zR[año,mes],                 name=f"shareA_{año}_{mes}")
                m.addConstr(self.ShareB[año,mes] == 0.29 * self.zR[año,mes],                 name=f"shareB_{año}_{mes}")
                m.addGenConstrMin(self.FillA[año,mes], [self.ShareA[año,mes], self.HeadA[año,mes]],
                                  name=f"fillA_min_{año}_{mes}")
                m.addGenConstrMin(self.FillB[año,mes], [self.ShareB[año,mes], self.HeadB[año,mes]],
                                  name=f"fillB_min_{año}_{mes}")

                m.addConstr(self.IN_VRFI[año,mes] == self.FillR[año,mes], name=f"in_vrfi_{año}_{mes}")
                m.addConstr(self.IN_A[año,mes]    == self.FillA[año,mes], name=f"in_a_{año}_{mes}")
                m.addConstr(self.IN_B[año,mes]    == self.FillB[año,mes], name=f"in_b_{año}_{mes}")

                # (2) Rebalse (solo remanente)
                m.addConstr(self.E_TOT[año,mes] == self.Rem[año,mes] - self.IN_VRFI[año,mes]
                                                - self.IN_A[año,mes] - self.IN_B[año,mes],
                            name=f"spill_{año}_{mes}")

                # Para reporte
                m.addConstr(self.Q_dis[año,mes] == Qin - UPREF, name=f"qdis_{año}_{mes}")

                # ===== SSR mensual con prioridad dura (consumo humano) =====
                # backlog previo
                if i == 0:
                    if self.ssr_carry_between_years and a_idx > 0:
                        prev_a = self.anos[a_idx-1]
                        backlog_prev = self.SSR_backlog[prev_a, 12]
                    else:
                        backlog_prev = self.model.addVar(lb=0.0, ub=0.0, name=f"SSR_backlog_prev0_{año}")
                else:
                    backlog_prev = self.SSR_backlog[año, mes-1]

                # Deuda SSR del mes
                m.addConstr(self.SSR_due[año, mes] == ssr_month + backlog_prev,
                            name=f"SSR_due_{año}_{mes}")

                # Capacidad para SSR (= V_R_prev + IN_VRFI) como VARIABLE AUXILIAR
                m.addConstr(self.SSR_cap_var[año, mes] == V_R_prev + self.IN_VRFI[año,mes],
                            name=f"SSR_cap_var_def_{año}_{mes}")

                # PRIORIDAD: paga todo lo posible
                m.addGenConstrMin(
                    self.Q_ch[año, mes],
                    [ self.SSR_due[año, mes], self.SSR_cap_var[año, mes] ],
                    name=f"SSR_qch_equals_min_{año}_{mes}"
                )

                # backlog del mes
                m.addConstr(self.SSR_backlog[año, mes] == self.SSR_due[año, mes] - self.Q_ch[año, mes],
                            name=f"SSR_backlog_def_{año}_{mes}")

                # ===== Disponibilidad para apoyos A/B protegiendo 1.5 =====
                # VRFI_avail_free = max( V_R_prev + IN_VRFI - Q_ch - 1.5, 0 )
                temp_free = m.addVar(lb=-GRB.INFINITY, name=f"temp_free_{año}_{mes}")
                m.addConstr(temp_free == V_R_prev + self.IN_VRFI[año,mes] - self.Q_ch[año,mes] - self.RSV_FLOOR,
                            name=f"temp_free_def_{año}_{mes}")
                m.addGenConstrMax(self.VRFI_avail_free[año,mes], [temp_free, self.zeroVar],
                                  name=f"vrfi_avail_free_max_{año}_{mes}")

                # (4) Disponibilidades para propio A/B
                m.addConstr(self.Q_A[año,mes] <= V_A_prev + self.IN_A[año,mes],     name=f"disp_A_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] <= V_B_prev + self.IN_B[año,mes],     name=f"disp_B_{año}_{mes}")

                m.addConstr(self.A_avail[año,mes] == V_A_prev + self.IN_A[año,mes], name=f"A_avail_def_{año}_{mes}")
                m.addConstr(self.B_avail[año,mes] == V_B_prev + self.IN_B[año,mes], name=f"B_avail_def_{año}_{mes}")

                m.addConstr(self.Q_A[año,mes] <= demA, name=f"A_le_Dem_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] <= demB, name=f"B_le_Dem_{año}_{mes}")

                m.addConstr(self.A_dem50[año,mes] == 0.5*demA, name=f"A_dem50_def_{año}_{mes}")
                m.addConstr(self.B_dem50[año,mes] == 0.5*demB, name=f"B_dem50_def_{año}_{mes}")

                m.addGenConstrMin(self.A_own_req[año,mes], [self.A_avail[año,mes], self.A_dem50[año,mes]],
                                  name=f"A_own_req_min_{año}_{mes}")
                m.addGenConstrMin(self.B_own_req[año,mes], [self.B_avail[año,mes], self.B_dem50[año,mes]],
                                  name=f"B_own_req_min_{año}_{mes}")

                m.addConstr(self.Q_A[año,mes] >= self.A_own_req[año,mes], name=f"A_use_own_first_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] >= self.B_own_req[año,mes], name=f"B_use_own_first_{año}_{mes}")

                # ========= (5) Apoyo VRFI: reparto 71/29 con reasignación =========
                m.addConstr(self.tA[año,mes] == 0.5*demA - self.Q_A[año,mes], name=f"tA_def_{año}_{mes}")
                m.addConstr(self.tB[año,mes] == 0.5*demB - self.Q_B[año,mes], name=f"tB_def_{año}_{mes}")
                m.addGenConstrMax(self.needA[año,mes], [self.tA[año,mes], self.zeroVar], name=f"needA_max_{año}_{mes}")
                m.addGenConstrMax(self.needB[año,mes], [self.tB[año,mes], self.zeroVar], name=f"needB_max_{año}_{mes}")

                m.addConstr(self.needTot[año,mes] == self.needA[año,mes] + self.needB[año,mes],
                            name=f"needTot_{año}_{mes}")
                m.addGenConstrMin(self.SupportTot[año,mes],
                                  [self.VRFI_avail_free[año,mes], self.needTot[año,mes]],
                                  name=f"supportTot_min_{año}_{mes}")

                m.addConstr(self.pA[año,mes] == 0.71 * self.SupportTot[año,mes], name=f"pA_prop_{año}_{mes}")
                m.addConstr(self.pB[año,mes] == 0.29 * self.SupportTot[año,mes], name=f"pB_prop_{año}_{mes}")

                m.addGenConstrMin(self.allocA_base[año,mes],
                                  [self.needA[año,mes], self.pA[año,mes]],
                                  name=f"allocA_base_min_{año}_{mes}")
                m.addGenConstrMin(self.allocB_base[año,mes],
                                  [self.needB[año,mes], self.pB[año,mes]],
                                  name=f"allocB_base_min_{año}_{mes}")

                m.addConstr(self.surplusA[año,mes] == self.pA[año,mes] - self.allocA_base[año,mes],
                            name=f"surplusA_{año}_{mes}")
                m.addConstr(self.surplusB[año,mes] == self.pB[año,mes] - self.allocB_base[año,mes],
                            name=f"surplusB_{año}_{mes}")
                m.addConstr(self.gapA[año,mes]     == self.needA[año,mes] - self.allocA_base[año,mes],
                            name=f"gapA_{año}_{mes}")
                m.addConstr(self.gapB[año,mes]     == self.needB[año,mes] - self.allocB_base[año,mes],
                            name=f"gapB_{año}_{mes}")

                m.addGenConstrMin(self.extra_to_B[año,mes],
                                  [self.surplusA[año,mes], self.gapB[año,mes]],
                                  name=f"extra_to_B_min_{año}_{mes}")
                m.addGenConstrMin(self.extra_to_A[año,mes],
                                  [self.surplusB[año,mes], self.gapA[año,mes]],
                                  name=f"extra_to_A_min_{año}_{mes}")

                m.addConstr(self.Q_A_apoyo[año,mes] == self.allocA_base[año,mes] + self.extra_to_A[año,mes],
                            name=f"Q_A_apoyo_final_{año}_{mes}")
                m.addConstr(self.Q_B_apoyo[año,mes] == self.allocB_base[año,mes] + self.extra_to_B[año,mes],
                            name=f"Q_B_apoyo_final_{año}_{mes}")

                # *** FIX duro: no gastar más VRFI libre de lo que hay ***
                m.addConstr(self.Q_A_apoyo[año,mes] + self.Q_B_apoyo[año,mes] <= self.VRFI_avail_free[año,mes],
                            name=f"apoyo_sum_le_vrfi_free_{año}_{mes}")

                # (3) Balances de stock (VRFI descuenta SSR y apoyos)
                m.addConstr(
                    self.V_VRFI[año,mes] ==
                    V_R_prev + self.IN_VRFI[año,mes]
                    - self.Q_ch[año,mes] - self.Q_A_apoyo[año,mes] - self.Q_B_apoyo[año,mes],
                    name=f"bal_vrfi_{año}_{mes}"
                )
                m.addConstr(self.V_A[año,mes] == V_A_prev + self.IN_A[año,mes] - self.Q_A[año,mes],
                            name=f"bal_va_{año}_{mes}")
                m.addConstr(self.V_B[año,mes] == V_B_prev + self.IN_B[año,mes] - self.Q_B[año,mes],
                            name=f"bal_vb_{año}_{mes}")

                # Capacidad
                m.addConstr(self.V_VRFI[año,mes] <= self.C_VRFI,   name=f"cap_vrfi_{año}_{mes}")
                m.addConstr(self.V_A[año,mes]    <= self.C_TIPO_A, name=f"cap_va_{año}_{mes}")
                m.addConstr(self.V_B[año,mes]    <= self.C_TIPO_B, name=f"cap_vb_{año}_{mes}")

                # (6) Déficit y no-sobre-servicio
                m.addConstr(self.d_A[año,mes] == demA - (self.Q_A[año,mes] + self.Q_A_apoyo[año,mes]),
                            name=f"def_A_{año}_{mes}")
                m.addConstr(self.d_B[año,mes] == demB - (self.Q_B[año,mes] + self.Q_B_apoyo[año,mes]),
                            name=f"def_B_{año}_{mes}")

                m.addConstr(self.Q_A[año,mes] + self.Q_A_apoyo[año,mes] <= demA + 1e-9,
                            name=f"nosobre_A_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] + self.Q_B_apoyo[año,mes] <= demB + 1e-9,
                            name=f"nosobre_B_{año}_{mes}")

                # (7) Turbinado (SSR no turbina)
                m.addConstr(self.Q_turb[año,mes] ==
                            (self.Q_A[año,mes] + self.Q_A_apoyo[año,mes]
                             + self.Q_B[año,mes] + self.Q_B_apoyo[año,mes]
                             + self.E_TOT[año,mes]),
                            name=f"turb_{año}_{mes}")

    # ===================== Objetivo =====================
    def set_objective(self):
        total_def = gp.quicksum(self.d_A[a,m] + self.d_B[a,m] for a in self.anos for m in self.months)
        self.model.setObjective(total_def, GRB.MINIMIZE)

    # ===================== Exportar resultados a Excel =====================
    def export_to_excel(self, filename="resultados_embalse.xlsx"):
        data = []
        for año in self.anos:
            y = int(año.split('/')[0])
            for mes in self.months:
                seg = self.segundos_por_mes[mes]
                Qin_m3s = self.inflow.get((y,mes), 0.0); Qin = Qin_m3s*seg/1_000_000.0
                QPD_eff_Hm3 = self.QPD_eff[año,mes]*seg/1_000_000.0

                key = self.m_mayo_abril_to_civil[mes]
                DemA = (self.DA_a_m[key]*self.num_A*self.FEA)/1_000_000.0
                DemB = (self.DB_a_b[key]*self.num_B*self.FEB)/1_000_000.0

                fila = {
                    'Año': año, 'Mes': mes,
                    'V_VRFI': self.V_VRFI[año,mes].X, 'V_A': self.V_A[año,mes].X, 'V_B': self.V_B[año,mes].X,
                    'Q_dis': self.Q_dis[año,mes].X, 'Q_ch': self.Q_ch[año,mes].X,
                    'SSR_due': self.SSR_due[año,mes].X, 'SSR_backlog': self.SSR_backlog[año,mes].X,
                    'Q_A': self.Q_A[año,mes].X, 'Q_B': self.Q_B[año,mes].X, 'Q_turb': self.Q_turb[año,mes].X,
                    'IN_VRFI': self.IN_VRFI[año,mes].X, 'IN_A': self.IN_A[año,mes].X, 'IN_B': self.IN_B[año,mes].X,
                    'E_TOT': self.E_TOT[año,mes].X,
                    'VRFI_avail_free': self.VRFI_avail_free[año,mes].X,
                    'needA': self.needA[año,mes].X, 'needB': self.needB[año,mes].X, 'needTot': self.needTot[año,mes].X,
                    'd_A': self.d_A[año,mes].X, 'd_B': self.d_B[año,mes].X,
                    'QPD_eff_Hm3': QPD_eff_Hm3,
                    'Demanda_A': DemA, 'Demanda_B': DemB,
                    'Q_afl_m3s': Qin_m3s, 'Q_afl_Hm3': Qin,
                    'Rem': self.Rem[año,mes].X, 'FillR': self.FillR[año,mes].X, 'zR': self.zR[año,mes].X,
                    'ShareA': self.ShareA[año,mes].X, 'ShareB': self.ShareB[año,mes].X,
                    'FillA': self.FillA[año,mes].X, 'FillB': self.FillB[año,mes].X
                }
                # para Excel y TXT uso estas claves
                fila['Q_A_apoyo'] = self.Q_A_apoyo[año,mes].X
                fila['Q_B_apoyo'] = self.Q_B_apoyo[año,mes].X

                tot_dem = DemA + DemB
                servA = fila['Q_A'] + fila['Q_A_apoyo']
                servB = fila['Q_B'] + fila['Q_B_apoyo']
                fila['Deficit_Total'] = self.d_A[año,mes].X + self.d_B[año,mes].X
                fila['Satisfaccion_A'] = (servA/DemA*100) if (DemA>0) else 100
                fila['Satisfaccion_B'] = (servB/DemB*100) if (DemB>0) else 100
                fila['Satisfaccion_Total'] = ((servA+servB)/tot_dem*100) if tot_dem>0 else 100
                data.append(fila)

        df_main = pd.DataFrame(data)
        resumen = []
        for año in self.anos:
            d = df_main[df_main['Año']==año]
            resumen.append({
                'Año': año,
                'Deficit_Total_Anual': d['Deficit_Total'].sum(),
                'Deficit_A_Anual': d['d_A'].sum(),
                'Deficit_B_Anual': d['d_B'].sum(),
                'Volumen_Turbinado_Anual': d['Q_turb'].sum(),
                'Demanda_Total_Anual': d['Demanda_A'].sum()+d['Demanda_B'].sum(),
                'Satisfaccion_Promedio': d['Satisfaccion_Total'].mean(),
                'Mes_Mayor_Deficit': (d.loc[d['Deficit_Total'].idxmax(),'Mes'] if d['Deficit_Total'].max()>0 else 'Ninguno')
            })
        df_res = pd.DataFrame(resumen)
        with pd.ExcelWriter(filename, engine='openpyxl') as w:
            df_main.to_excel(w, sheet_name='Resultados_Detallados', index=False)
            df_res.to_excel(w,   sheet_name='Resumen_Anual', index=False)
        print(f"✅ Resultados exportados a {filename}")
        print(f"📊 Déficit total: {df_main['Deficit_Total'].sum():.2f} Hm³")
        print(f"📈 Satisfacción promedio: {df_main['Satisfaccion_Total'].mean():.1f}%")
        return df_main, df_res

    def export_to_txt(self, filename="reporte_embalse.txt"):
        def bar20(pct):
            n = int(round(min(max(pct,0),100) / 5.0))
            return "█"*n + "·"*(20-n)

        mes_tag = {1:'may',2:'jun',3:'jul',4:'ago',5:'sep',6:'oct',7:'nov',8:'dic',9:'ene',10:'feb',11:'mar',12:'abr'}
        lines = []

        N_Y = len(self.anos)
        N_M = 12
        TOT_PM = N_Y * N_M

        # Agregados 30 años
        Qturb_total_30y = 0.0
        spill_total_30y = 0.0
        qdis_total_30y  = 0.0
        serv_total_30y  = 0.0
        dem_total_30y   = 0.0

        spill_prom_mes = {m: 0.0 for m in self.months}
        qdis_prom_mes  = {m: 0.0 for m in self.months}
        sat_por_mes = {}

        for mes in self.months:
            serv_sum = 0.0
            dem_sum  = 0.0
            key_civil = self.m_mayo_abril_to_civil[mes]
            DemA_mes = (self.DA_a_m[key_civil] * self.num_A * self.FEA) / 1_000_000.0
            DemB_mes = (self.DB_a_b[key_civil] * self.num_B * self.FEB) / 1_000_000.0

            for año in self.anos:
                Qturb_total_30y += self.Q_turb[año, mes].X
                spill_total_30y += self.E_TOT[año, mes].X
                qdis_total_30y  += self.Q_dis[año, mes].X

                servA = self.Q_A[año, mes].X + self.Q_A_apoyo[año, mes].X
                servB = self.Q_B[año, mes].X + self.Q_B_apoyo[año, mes].X
                serv_sum += (servA + servB)
                dem_sum  += (DemA_mes + DemB_mes)

                spill_prom_mes[mes] += self.E_TOT[año, mes].X
                qdis_prom_mes[mes]  += self.Q_dis[año, mes].X

            spill_prom_mes[mes] /= N_Y
            qdis_prom_mes[mes]  /= N_Y
            sat_por_mes[mes] = (100.0 * serv_sum / dem_sum) if dem_sum > 0 else 100.0
            serv_total_30y += serv_sum
            dem_total_30y  += dem_sum

        spill_prom_mensual_30y = spill_total_30y / TOT_PM
        qdis_prom_mensual_30y  = qdis_total_30y  / TOT_PM
        qdis_prom_total_30y    = qdis_total_30y  / TOT_PM
        sat_global_30y         = (100.0 * serv_total_30y / dem_total_30y) if dem_total_30y > 0 else 100.0

        # Stocks finales
        ultimo_anio = self.anos[-1]
        V_R_fin = self.V_VRFI[ultimo_anio, 12].X
        V_A_fin = self.V_A[ultimo_anio, 12].X
        V_B_fin = self.V_B[ultimo_anio, 12].X
        V_total_fin_30y = V_R_fin + V_A_fin + V_B_fin

        # ======== RESUMEN 30 AÑOS ========
        lines.append("="*70)
        lines.append("RESUMEN 30 AÑOS — AGREGADOS")
        lines.append("="*70)
        lines.append(f"Volumen turbinado TOTAL (30 años): {Qturb_total_30y:,.1f} Hm³")
        lines.append(f"Rebalse TOTAL (30 años): {spill_total_30y:,.1f} Hm³")
        lines.append(f"Rebalse PROMEDIO mensual (30 años): {spill_prom_mensual_30y:,.2f} Hm³/mes")
        lines.append(f"Caudal disponible PROMEDIO mensual (30 años): {qdis_prom_mensual_30y:,.2f} Hm³/mes")
        lines.append(f"Caudal disponible PROMEDIO (30 años): {qdis_prom_total_30y:,.2f} Hm³/mes")
        lines.append(f"Satisfacción ponderada PROMEDIO (30 años): {sat_global_30y:6.2f}%")
        lines.append("")
        lines.append("Promedios mensuales sobre 30 años:")
        lines.append("Mes   Rebalse prom [Hm³/mes]   Q_dis prom [Hm³/mes]   %Satisfacción (ponderada)")
        lines.append("-"*70)
        for mes in self.months:
            lines.append(f"{mes_tag[mes]:<4}  {spill_prom_mes[mes]:10.2f}                {qdis_prom_mes[mes]:10.2f}                {sat_por_mes[mes]:6.2f}%")
        lines.append("")
        lines.append("Agua almacenada al final de los 30 años (fin del último periodo):")
        lines.append(f"  VRFI: {V_R_fin:.1f} Hm³   A: {V_A_fin:.1f} Hm³   B: {V_B_fin:.1f} Hm³   TOTAL: {V_total_fin_30y:.1f} Hm³")
        lines.append("")

        # ===================== DETALLE ANUAL =====================
        for año in self.anos:
            y = int(año.split('/')[0])

            lines.append("="*37)
            lines.append(f"REPORTE ANUAL: {año}  (mes a mes)")
            lines.append("="*37)
            lines.append("Tabla 1 — Física del sistema (volúmenes en Hm³; caudales en m³/s y Qin/QPD en Hm³/mes)")
            header1 = ("Mes   Qin     Qin_m    QPD     QPD_m    IN_R     INA      INB      EB       "
                    "Motivo_EB        VRFI prev→fin         A prev→fin        B prev→fin        "
                    "VRFI %p→f     A %p→f      B %p→f      CHEQ    |  Stocks fin  ")
            lines.append(header1)
            lines.append("-"*230)

            for i, mes in enumerate(self.months):
                seg = self.segundos_por_mes[mes]
                Qin_m3s = self.inflow.get((y,mes), 0.0)
                Qin_Hm3 = Qin_m3s * seg / 1_000_000.0
                QPD_m3s = self.QPD_eff[año, mes]
                QPD_Hm3 = QPD_m3s * seg / 1_000_000.0

                IN_R = self.IN_VRFI[año, mes].X
                INA  = self.IN_A[año, mes].X
                INB  = self.IN_B[año, mes].X
                EB   = self.E_TOT[año, mes].X

                if i == 0:
                    prev_año = f"{y-1}/{y}"
                    V_R_prev = self.V_VRFI[prev_año,12].X if prev_año in self.anos else self.VRFI_init
                    V_A_prev = self.V_A[prev_año,12].X    if prev_año in self.anos else self.VA_init
                    V_B_prev = self.V_B[prev_año,12].X    if prev_año in self.anos else self.VB_init
                else:
                    V_R_prev = self.V_VRFI[año, mes-1].X
                    V_A_prev = self.V_A[año,  mes-1].X
                    V_B_prev = self.V_B[año,  mes-1].X

                V_R_fin_m = self.V_VRFI[año, mes].X
                V_A_fin_m = self.V_A[año, mes].X
                V_B_fin_m = self.V_B[año, mes].X

                pct_R_prev = (V_R_prev/self.C_VRFI*100) if self.C_VRFI>0 else 0
                pct_R_fin  = (V_R_fin_m/self.C_VRFI*100) if self.C_VRFI>0 else 0
                pct_A_prev = (V_A_prev/self.C_TIPO_A*100) if self.C_TIPO_A>0 else 0
                pct_A_fin  = (V_A_fin_m/self.C_TIPO_A*100) if self.C_TIPO_A>0 else 0
                pct_B_prev = (V_B_prev/self.C_TIPO_B*100) if self.C_TIPO_B>0 else 0
                pct_B_fin  = (V_B_fin_m/self.C_TIPO_B*100) if self.C_TIPO_B>0 else 0

                motivo  = "-" if EB <= 1e-9 else "Sobra tras llenado (ex-post)"

                barR = bar20(pct_R_fin); barA = bar20(pct_A_fin); barB = bar20(pct_B_fin)

                row1 = (f"{mes_tag[mes]:<4} "
                        f"{Qin_m3s:6.2f}  {Qin_Hm3:7.1f}  "
                        f"{QPD_m3s:6.2f}  {QPD_Hm3:7.1f}  "
                        f"{IN_R:7.1f}  {INA:7.1f}  {INB:7.1f}  {EB:7.1f}  "
                        f"{motivo:<24}  "
                        f"{V_R_prev:5.1f}→{V_R_fin_m:<5.1f}      "
                        f"{V_A_prev:5.1f}→{V_A_fin_m:<5.1f}    "
                        f"{V_B_prev:5.1f}→{V_B_fin_m:<5.1f}    "
                        f"{pct_R_prev:3.0f}→{pct_R_fin:<3.0f}%     "
                        f"{pct_A_prev:3.0f}→{pct_A_fin:<3.0f}%   "
                        f"{pct_B_prev:3.0f}→{pct_B_fin:<3.0f}%     "
                        f" |  VRFI[{V_R_fin_m:6.1f}] {barR}  "
                        f"A[{V_A_fin_m:6.1f}] {barA}  "
                        f"B[{V_B_fin_m:6.1f}] {barB}")
                lines.append(row1)

            # ================== TABLA 2 ==================
            lines.append("")
            lines.append("Tabla 2 — Servicio (Hm³/mes) + SSR (Hm³) + Qturb (Hm³)")
            header2 = ("Mes   DemA*FE    ServA     dA      DemB*FE    ServB     dB      Q_SSR    "
                    "A_out    VRFI→A    B_out    VRFI→B   VRFI_avail  needTot  SupportTot   Qturb")
            lines.append(header2)
            lines.append("-"*160)

            for i, mes in enumerate(self.months):
                key = self.m_mayo_abril_to_civil[mes]
                DemA = (self.DA_a_m[key]*self.num_A*self.FEA)/1_000_000.0
                DemB = (self.DB_a_b[key]*self.num_B*self.FEB)/1_000_000.0

                ServA = self.Q_A[año, mes].X + self.Q_A_apoyo[año, mes].X
                ServB = self.Q_B[año, mes].X + self.Q_B_apoyo[año, mes].X
                dA    = self.d_A[año, mes].X
                dB    = self.d_B[año, mes].X
                Q_SSR = self.Q_ch[año, mes].X
                A_out = self.Q_A[año, mes].X
                B_out = self.Q_B[año, mes].X
                VA    = self.Q_A_apoyo[año, mes].X
                VB    = self.Q_B_apoyo[año, mes].X
                Qturb = self.Q_turb[año, mes].X
                VRFIa = self.VRFI_avail_free[año, mes].X
                needT = self.needTot[año, mes].X
                supT  = self.SupportTot[año, mes].X

                row2 = (f"{mes_tag[mes]:<4} "
                        f"{DemA:8.1f}   {ServA:6.1f}   {dA:6.1f}   "
                        f"{DemB:8.1f}   {ServB:6.1f}   {dB:6.1f}   "
                        f"{Q_SSR:6.1f}   "
                        f"{A_out:6.1f}    {VA:6.1f}     {B_out:6.1f}    {VB:6.1f}   "
                        f"{VRFIa:8.1f}   {needT:7.1f}    {supT:9.1f}   "
                        f"{Qturb:6.1f}")
                lines.append(row2)

            lines.append("")

        # ---- escribir archivo
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"📝 Reporte TXT escrito en {filename}")
        return filename

    # ===================== Solve =====================
    def solve(self):
        try:
            print("Iniciando optimización del Embalse Nueva Punilla...")
            data_file = "data/caudales.xlsx"
            self.inflow, self.Q_nuble, self.Q_hoya1, self.Q_hoya2, self.Q_hoya3 = self.load_flow_data(data_file)
            self.setup_variables()
            self.setup_constraints()
            self.set_objective()
            self.model.optimize()
            if self.model.status == GRB.INFEASIBLE:
                print("⚠️ Modelo infeasible. Calculando IIS...")
                self.model.computeIIS()
                # Escribir IIS en formato válido para Gurobi 12:
                self.model.write("modelo.ilp")   # IIS LP (contiene el subsistema conflictivo)
                print("IIS guardado en 'modelo.ilp'. Ábrelo para ver restricciones en conflicto.")
                return None

            if self.model.status in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
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
