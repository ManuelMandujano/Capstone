# model/modelito2.py
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

class EmbalseNuevaPunilla:


    """
    MODELO DE OPERACIÓN SIMPLIFICADO — Embalse Nueva Punilla

    Unidades
    --------
    - Caudales base (Q_nuble, Q_hoya*) en m³/s → se convierten a Hm³/mes con `segundos_por_mes`.
    - Volúmenes (stocks V_*, llenados IN_*, rebalse E_TOT, entregas Q_*) en Hm³.
    - Demandas mensuales (DemA, DemB) en Hm³.

    Calendario
    ----------
    - Mes del modelo: m = 1..12 corresponde a MAY..ABR (año hidrológico).
    - Para leer demandas por mes civil (ene=1,...,dic=12) se usa un mapeo  (MAY..ABR → 5..4).

    === GLOSARIO DE VARIABLES (listo para LaTeX) ===
    Para cada año t y mes m:

    Stocks (Hm³)
    ------------
    - V_VRFI_{t,m}  : stock en VRFI al final de m, 0 ≤ V_VRFI ≤ C_VRFI.
    - V^A_{t,m}     : stock de A al final de m,     0 ≤ V^A ≤ C_A.
    - V^B_{t,m}     : stock de B al final de m,     0 ≤ V^B ≤ C_B.

    Llenados y rebalse (Hm³/mes)
    ----------------------------
    - IN_R_{t,m} (= IN_VRFI): llenado efectivo del VRFI en m.
    - IN_A_{t,m}, IN_B_{t,m}: llenados efectivos de A y B en m.
    - E_TOT_{t,m}           : rebalse total ex–post de remanente en m.

    Entregas (Hm³/mes)
    ------------------
    - Q_ch_{t,m}         : SSR (sale de VRFI); **no** turbina.
    - Q_A_{t,m}, Q_B_{t,m}: servicio propio de A y B (sale de sus stocks).
    - Q_A_ap_{t,m}, Q_B_ap_{t,m}: apoyo VRFI a A y B (safety-net hasta 50% de demanda).

    Déficits y turbinado
    --------------------
    - d_A_{t,m}, d_B_{t,m} : déficits del mes.
    - Q_turb_{t,m}         : volumen turbinado = (Q_A+Q_A_ap) + (Q_B+Q_B_ap) + E_TOT.

    Auxiliares de prioridad de llenado (Hm³)
    ----------------------------------------
    - Rem_{t,m}   : remanente del mes tras QPD (en Hm³/mes).
    - HeadR_{t,m} : espacio libre en VRFI al inicio del mes.
    - HeadA_{t,m}, HeadB_{t,m} : espacios libres en A y B.
    - FillR_{t,m} (= IN_R_{t,m}) = min(Rem, HeadR).
    - zR_{t,m} = Rem - IN_R.
    - ShareA_{t,m} = 0.71·zR,  ShareB_{t,m} = 0.29·zR.
    - IN_A = min(ShareA, HeadA),  IN_B = min(ShareB, HeadB).

    Auxiliares apoyo 50% y saturación VRFI
    --------------------------------------
    - needA_{t,m} ≥ max(0, 0.5·DemA_{t,m} − Q_A_{t,m}),  needB_{t,m} ≥ max(0, 0.5·DemB_{t,m} − Q_B_{t,m}).
    - VRFI_avail_{t,m} = V^R_{t,m-1} + IN_R_{t,m} − Q_ch_{t,m}.
    - needTot_{t,m} = needA_{t,m} + needB_{t,m}.
    - SupportTot_{t,m} = min(VRFI_avail_{t,m}, needTot_{t,m}).
    - Igualdad de saturación: Q_A_ap_{t,m} + Q_B_ap_{t,m} = SupportTot_{t,m}.

    *** Regla “Propio da TODO lo posible” (nueva, dura) ***
    ------------------------------------------------------
    - Q_A_{t,m} = min(DemA_{t,m}, V^A_{t,m-1} + IN_A_{t,m})
    - Q_B_{t,m} = min(DemB_{t,m}, V^B_{t,m-1} + IN_B_{t,m})

    Objetivo
    --------
    Minimizar déficit total con desempates suaves:
      min Σ(d_A + d_B) + 1e-3·Σ(Q_A_ap + Q_B_ap) − 1e-3·Σ(Q_A + Q_B) + 1e-6·Σ(V_A + V_B + V_VRFI)

    === BLOQUE DE RESTRICCIONES — Texto formal (listo para LaTeX) ===

    Para cada año t y mes m (Qin, QPD, DemA, DemB en Hm³/mes):

    1) Remanente y prioridades de llenado con el remanente del mes:
       Rem_{t,m} = Qin_{t,m} − QPD_{t,m}
       HeadR_{t,m} = C_VRFI − V^R_{t,m-1}
       IN_R_{t,m} = min(Rem_{t,m}, HeadR_{t,m})
       zR_{t,m} = Rem_{t,m} − IN_R_{t,m}
       HeadA_{t,m} = C_A − V^A_{t,m-1},   HeadB_{t,m} = C_B − V^B_{t,m-1}
       ShareA_{t,m} = 0.71·zR_{t,m},      ShareB_{t,m} = 0.29·zR_{t,m}
       IN_A_{t,m} = min(ShareA_{t,m}, HeadA_{t,m})
       IN_B_{t,m} = min(ShareB_{t,m}, HeadB_{t,m})

    2) Rebalse ex–post de remanente:
       E_TOT_{t,m} = Rem_{t,m} − IN_R_{t,m} − IN_A_{t,m} − IN_B_{t,m}

    3) Balances de stock (fin de mes):
       V^R_{t,m} = V^R_{t,m-1} + IN_R_{t,m} − Q_ch_{t,m} − Q_A_ap_{t,m} − Q_B_ap_{t,m}
       V^A_{t,m} = V^A_{t,m-1} + IN_A_{t,m} − Q_A_{t,m}
       V^B_{t,m} = V^B_{t,m-1} + IN_B_{t,m} − Q_B_{t,m}
       0 ≤ V^R_{t,m} ≤ C_VRFI, 0 ≤ V^A_{t,m} ≤ C_A, 0 ≤ V^B_{t,m} ≤ C_B

    4) Disponibilidades (cotas superiores):
       Q_A_{t,m} ≤ V^A_{t,m-1} + IN_A_{t,m}
       Q_B_{t,m} ≤ V^B_{t,m-1} + IN_B_{t,m}
       Q_ch_{t,m} ≤ V^R_{t,m-1} + IN_R_{t,m}

    4-bis) Propio “da TODO lo posible” (igualdad de mínimo):
       Q_A_{t,m} = min(DemA_{t,m}, V^A_{t,m-1} + IN_A_{t,m})
       Q_B_{t,m} = min(DemB_{t,m}, V^B_{t,m-1} + IN_B_{t,m})

    5) Apoyo VRFI solo para completar 50%:
       needA_{t,m} ≥ 0.5·DemA_{t,m} − Q_A_{t,m},   needA_{t,m} ≥ 0
       needB_{t,m} ≥ 0.5·DemB_{t,m} − Q_B_{t,m},   needB_{t,m} ≥ 0
       Q_A_ap_{t,m} ≤ needA_{t,m},  Q_B_ap_{t,m} ≤ needB_{t,m}

    5-bis) Usar TODO el VRFI disponible (saturación):
       VRFI_avail_{t,m} = V^R_{t,m-1} + IN_R_{t,m} − Q_ch_{t,m}
       needTot_{t,m} = needA_{t,m} + needB_{t,m}
       SupportTot_{t,m} = min(VRFI_avail_{t,m}, needTot_{t,m})
       Q_A_ap_{t,m} + Q_B_ap_{t,m} = SupportTot_{t,m}

    6) No sobre-servicio y déficit:
       Q_A_{t,m} + Q_A_ap_{t,m} ≤ DemA_{t,m}
       Q_B_{t,m} + Q_B_ap_{t,m} ≤ DemB_{t,m}
       d_A_{t,m} = DemA_{t,m} − (Q_A_{t,m} + Q_A_ap_{t,m}) ≥ 0
       d_B_{t,m} = DemB_{t,m} − (Q_B_{t,m} + Q_B_ap_{t,m}) ≥ 0

    7) Turbinado:
       Q_turb_{t,m} = (Q_A_{t,m} + Q_A_ap_{t,m}) + (Q_B_{t,m} + Q_B_ap_{t,m}) + E_TOT_{t,m}

    8) SSR (anual exacto o mensual fijo):
       Σ_m Q_ch_{t,m} = V_C_H    (ó bien Q_ch_{t,m} = V_C_H · frac_m si se fija mensual)
    """
    """
    MODELO DE OPERACIÓN SIMPLIFICADO — Embalse Nueva Punilla

    Reglas clave:
    - El remanente mensual (Qin - SSR) se usa para llenar: primero VRFI, luego A y B (71/29). Lo que sobre, rebalsa.
    - El servicio propio de A y B sale de sus stocks (previos + llenados de ese mes).
    - El VRFI solo apoya para completar HASTA el 50% de la demanda de cada grupo y SOLO si el propio queda < 50%.
      Si el propio alcanza ≥50%, el apoyo VRFI es 0.
    - El apoyo y el SSR salen del stock del VRFI (no del remanente directo).
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
        self.fix_ssr_monthly = False
        self.ssr_frac = {1:0.10,2:0.10,3:0.15,4:0.20,5:0.15,6:0.10,7:0.10,8:0.05,9:0.0,10:0.0,11:0.0,12:0.05}

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
        self.Q_ch = m.addVars(self.anos, self.months, name="Q_ch", lb=0)   # SSR
        self.Q_A  = m.addVars(self.anos, self.months, name="Q_A",  lb=0)   # Servicio propio A
        self.Q_B  = m.addVars(self.anos, self.months, name="Q_B",  lb=0)   # Servicio propio B

        # Apoyo VRFI (solo para completar 50%)
        self.Q_A_apoyo = m.addVars(self.anos, self.months, name="Q_A_apoyo", lb=0)
        self.Q_B_apoyo = m.addVars(self.anos, self.months, name="Q_B_apoyo", lb=0)

        # Déficits
        self.d_A = m.addVars(self.anos, self.months, name="d_A", lb=0)
        self.d_B = m.addVars(self.anos, self.months, name="d_B", lb=0)

        # Turbinado (SSR no turbina)
        self.Q_turb = m.addVars(self.anos, self.months, name="Q_turb", lb=0)

        # Para reporte
        self.Q_dis = m.addVars(self.anos, self.months, name="Q_dis", lb=0)

        # Auxiliares de llenado
        self.Rem    = m.addVars(self.anos, self.months, name="Rem",   lb=0)  # Qin-UPREF
        self.HeadR  = m.addVars(self.anos, self.months, name="HeadR", lb=0)  # espacio VRFI
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

        # ===== Auxiliares para “propio primero hasta 50%” =====
        self.A_avail   = m.addVars(self.anos, self.months, name="A_avail")
        self.A_dem50   = m.addVars(self.anos, self.months, name="A_dem50", lb=0.0)
        self.A_own_req = m.addVars(self.anos, self.months, name="A_own_req", lb=0.0)

        self.B_avail   = m.addVars(self.anos, self.months, name="B_avail")
        self.B_dem50   = m.addVars(self.anos, self.months, name="B_dem50", lb=0.0)
        self.B_own_req = m.addVars(self.anos, self.months, name="B_own_req", lb=0.0)

        # Faltante “teórico” para 50%
        self.tA = m.addVars(self.anos, self.months, name="tA")
        self.tB = m.addVars(self.anos, self.months, name="tB")

        # Constante cero (para GENCONSTR MAX)
        self.zeroVar = m.addVar(lb=0.0, ub=0.0, name="zeroConst")

        # ===== Slacks diagnósticos (ya no necesarios para forzar) =====
        self.rA = m.addVars(self.anos, self.months, name="rA", lb=0.0)
        self.rB = m.addVars(self.anos, self.months, name="rB", lb=0.0)

        # ===== NUEVOS auxiliares para “usar todo lo posible del VRFI” =====
        self.VRFI_avail  = m.addVars(self.anos, self.months, name="VRFI_avail")   # = V_R_prev + IN_VRFI - Q_ch
        self.needTot     = m.addVars(self.anos, self.months, name="needTot", lb=0)
        self.SupportTot  = m.addVars(self.anos, self.months, name="SupportTot", lb=0)  # = min(VRFI_avail, needTot)

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

    # ===================== Restricciones SOLO PARA EL MONTI CHARLI Q SINO NO FUNCA =====================
    def setup_constraints_montecarlo(self):
        """
        Versión de setup_constraints() para Monte Carlo.
        NO asume orden cronológico de años - cada año es independiente.
        """
        m = self.model
        data_file = "data/caudales.xlsx"
        self.inflow, self.Q_nuble, self.Q_hoya1, self.Q_hoya2, self.Q_hoya3 = self.load_flow_data(data_file)

        # QPD efectivo
        derechos_MAY_ABR = [52.00,52.00,52.00,52.00,57.70,76.22,69.22,52.00,52.00,52.00,52.00,52.00]
        qeco_MAY_ABR     = [10.00,10.35,14.48,15.23,15.23,15.23,15.23,15.23,12.80,15.20,16.40,17.60]
        self.QPD_eff = {}
        for año in self.anos:
            y = int(año.split('/')[0])
            for mes in self.months:
                H = self.Q_hoya1.get((y,mes),0.0) + self.Q_hoya2.get((y,mes),0.0) + self.Q_hoya3.get((y,mes),0.0)
                qpd_nom = max(derechos_MAY_ABR[mes-1], qeco_MAY_ABR[mes-1], max(0.0, 95.7 - H))
                self.QPD_eff[año, mes] = min(qpd_nom, self.Q_nuble.get((y,mes),0.0))

        # ========== CAMBIO CRÍTICO: Cada año empieza con stocks en 0 ==========
        for año in self.anos:
            m.addConstr(self.V_VRFI[año,1] == 0, name=f"init_VRFI_{año}")
            m.addConstr(self.V_A[año,1]    == 0, name=f"init_VA_{año}")
            m.addConstr(self.V_B[año,1]    == 0, name=f"init_VB_{año}")

        for año in self.anos:
            y = int(año.split('/')[0])
            for i, mes in enumerate(self.months):
                seg   = self.segundos_por_mes[mes]
                Qin_s = self.inflow.get((y,mes), 0.0)
                Qin   = Qin_s * seg / 1_000_000.0
                UPREF = self.QPD_eff[año, mes] * seg / 1_000_000.0

                key   = self.m_mayo_abril_to_civil[mes]
                demA  = (self.DA_a_m[key] * self.num_A * self.FEA) / 1_000_000.0
                demB  = (self.DB_a_b[key] * self.num_B * self.FEB) / 1_000_000.0

                # ========== CAMBIO CRÍTICO: Stocks previos solo del mes anterior DENTRO del mismo año ==========
                if i == 0:
                    # Primer mes del año: ya fijado en 0 arriba
                    V_R_prev = 0
                    V_A_prev = 0
                    V_B_prev = 0
                else:
                    V_R_prev = self.V_VRFI[año, mes-1]
                    V_A_prev = self.V_A[año,  mes-1]
                    V_B_prev = self.V_B[año,  mes-1]

                # El resto de las restricciones es IDÉNTICO a setup_constraints()
                # (copialo desde la línea "# (1) Remanente y prioridad..." hasta el final del loop)
                
                # (1) Remanente y prioridad de llenado
                m.addConstr(self.Rem[año,mes]    == Qin - UPREF,                 name=f"rem_{año}_{mes}")
                m.addConstr(self.HeadR[año,mes]  == self.C_VRFI  - V_R_prev,     name=f"headR_{año}_{mes}")
                m.addConstr(self.HeadA[año,mes]  == self.C_TIPO_A - V_A_prev,    name=f"headA_{año}_{mes}")
                m.addConstr(self.HeadB[año,mes]  == self.C_TIPO_B - V_B_prev,    name=f"headB_{año}_{mes}")

                m.addGenConstrMin(self.FillR[año,mes], [self.Rem[año,mes], self.HeadR[año,mes]], name=f"fillR_min_{año}_{mes}")
                m.addConstr(self.zR[año,mes]     == self.Rem[año,mes] - self.FillR[año,mes],     name=f"zR_{año}_{mes}")
                m.addConstr(self.ShareA[año,mes] == 0.71 * self.zR[año,mes],                      name=f"shareA_{año}_{mes}")
                m.addConstr(self.ShareB[año,mes] == 0.29 * self.zR[año,mes],                      name=f"shareB_{año}_{mes}")
                m.addGenConstrMin(self.FillA[año,mes], [self.ShareA[año,mes], self.HeadA[año,mes]], name=f"fillA_min_{año}_{mes}")
                m.addGenConstrMin(self.FillB[año,mes], [self.ShareB[año,mes], self.HeadB[año,mes]], name=f"fillB_min_{año}_{mes}")

                m.addConstr(self.IN_VRFI[año,mes] == self.FillR[año,mes], name=f"in_vrfi_{año}_{mes}")
                m.addConstr(self.IN_A[año,mes]    == self.FillA[año,mes], name=f"in_a_{año}_{mes}")
                m.addConstr(self.IN_B[año,mes]    == self.FillB[año,mes], name=f"in_b_{año}_{mes}")

                # (2) Rebalse
                m.addConstr(self.E_TOT[año,mes] == self.Rem[año,mes] - self.IN_VRFI[año,mes]
                                                - self.IN_A[año,mes] - self.IN_B[año,mes],
                            name=f"spill_{año}_{mes}")

                m.addConstr(self.Q_dis[año,mes] == Qin - UPREF, name=f"qdis_{año}_{mes}")

                # (3) Balances
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

                m.addConstr(self.V_VRFI[año,mes] <= self.C_VRFI,   name=f"cap_vrfi_{año}_{mes}")
                m.addConstr(self.V_A[año,mes]    <= self.C_TIPO_A, name=f"cap_va_{año}_{mes}")
                m.addConstr(self.V_B[año,mes]    <= self.C_TIPO_B, name=f"cap_vb_{año}_{mes}")

                # (4) Disponibilidades
                m.addConstr(self.Q_A[año,mes] <= V_A_prev + self.IN_A[año,mes],     name=f"disp_A_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] <= V_B_prev + self.IN_B[año,mes],     name=f"disp_B_{año}_{mes}")
                m.addConstr(self.Q_ch[año,mes] <= V_R_prev + self.IN_VRFI[año,mes], name=f"disp_ch_{año}_{mes}")

                # (4.5) Propio primero
                m.addConstr(self.A_avail[año,mes] == V_A_prev + self.IN_A[año,mes], name=f"A_avail_def_{año}_{mes}")
                m.addConstr(self.A_dem50[año,mes] == 0.5*demA,                      name=f"A_dem50_def_{año}_{mes}")
                m.addGenConstrMin(self.A_own_req[año,mes], [self.A_avail[año,mes], self.A_dem50[año,mes]],
                                name=f"A_own_req_min_{año}_{mes}")
                m.addConstr(self.Q_A[año,mes] >= self.A_own_req[año,mes],           name=f"A_use_own_first_{año}_{mes}")

                m.addConstr(self.B_avail[año,mes] == V_B_prev + self.IN_B[año,mes], name=f"B_avail_def_{año}_{mes}")
                m.addConstr(self.B_dem50[año,mes] == 0.5*demB,                      name=f"B_dem50_def_{año}_{mes}")
                m.addGenConstrMin(self.B_own_req[año,mes], [self.B_avail[año,mes], self.B_dem50[año,mes]],
                                name=f"B_own_req_min_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] >= self.B_own_req[año,mes],           name=f"B_use_own_first_{año}_{mes}")

                # (5) Apoyo VRFI
                m.addConstr(self.tA[año,mes] == 0.5*demA - self.Q_A[año,mes], name=f"tA_def_{año}_{mes}")
                m.addConstr(self.tB[año,mes] == 0.5*demB - self.Q_B[año,mes], name=f"tB_def_{año}_{mes}")

                m.addGenConstrMax(self.needA[año,mes], [self.tA[año,mes], self.zeroVar], name=f"needA_max_{año}_{mes}")
                m.addGenConstrMax(self.needB[año,mes], [self.tB[año,mes], self.zeroVar], name=f"needB_max_{año}_{mes}")

                m.addConstr(self.Q_A_apoyo[año,mes] <= self.needA[año,mes], name=f"apA_le_need_{año}_{mes}")
                m.addConstr(self.Q_B_apoyo[año,mes] <= self.needB[año,mes], name=f"apB_le_need_{año}_{mes}")

                # (5.1) Saturación VRFI
                m.addConstr(self.VRFI_avail[año,mes] == V_R_prev + self.IN_VRFI[año,mes] - self.Q_ch[año,mes],
                            name=f"vrfi_avail_{año}_{mes}")
                m.addConstr(self.needTot[año,mes] == self.needA[año,mes] + self.needB[año,mes],
                            name=f"needTot_{año}_{mes}")
                m.addGenConstrMin(self.SupportTot[año,mes], [self.VRFI_avail[año,mes], self.needTot[año,mes]],
                                name=f"supportTot_min_{año}_{mes}")
                m.addConstr(self.Q_A_apoyo[año,mes] + self.Q_B_apoyo[año,mes] == self.SupportTot[año,mes],
                            name=f"use_all_support_{año}_{mes}")

                # (5.5) Slacks
                m.addConstr(self.rA[año,mes] >= self.needA[año,mes] - self.Q_A_apoyo[año,mes],
                            name=f"slack_needA_{año}_{mes}")
                m.addConstr(self.rB[año,mes] >= self.needB[año,mes] - self.Q_B_apoyo[año,mes],
                            name=f"slack_needB_{año}_{mes}")

                # (6) Déficit
                m.addConstr(self.d_A[año,mes] == demA - (self.Q_A[año,mes] + self.Q_A_apoyo[año,mes]),
                            name=f"def_A_{año}_{mes}")
                m.addConstr(self.d_B[año,mes] == demB - (self.Q_B[año,mes] + self.Q_B_apoyo[año,mes]),
                            name=f"def_B_{año}_{mes}")

                m.addConstr(self.Q_A[año,mes] + self.Q_A_apoyo[año,mes] <= demA + 1e-9,
                            name=f"nosobre_A_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] + self.Q_B_apoyo[año,mes] <= demB + 1e-9,
                            name=f"nosobre_B_{año}_{mes}")

                # (7) Turbinado
                m.addConstr(self.Q_turb[año,mes] ==
                            (self.Q_A[año,mes] + self.Q_A_apoyo[año,mes]
                            + self.Q_B[año,mes] + self.Q_B_apoyo[año,mes]
                            + self.E_TOT[año,mes]),
                            name=f"turb_{año}_{mes}")

        # (8) SSR
        if self.fix_ssr_monthly:
            for año in self.anos:
                for mes in self.months:
                    self.model.addConstr(self.Q_ch[año, mes] == self.V_C_H * float(self.ssr_frac.get(mes, 0.0)),
                                        name=f"ssr_mes_{año}_{mes}")
        else:
            for año in self.anos:
                self.model.addConstr(gp.quicksum(self.Q_ch[año, mes] for mes in self.months) == self.V_C_H,
                                    name=f"ssr_anual_{año}")



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

        # Iniciales (MAY del primer año)
        primer = self.anos[0]
        m.addConstr(self.V_VRFI[primer,1] == 0, name="init_VRFI")
        m.addConstr(self.V_A[primer,1]    == 0, name="init_VA")
        m.addConstr(self.V_B[primer,1]    == 0, name="init_VB")

        for año in self.anos:
            y = int(año.split('/')[0])
            for i, mes in enumerate(self.months):
                seg   = self.segundos_por_mes[mes]
                Qin_s = self.inflow.get((y,mes), 0.0)
                Qin   = Qin_s * seg / 1_000_000.0
                UPREF = self.QPD_eff[año, mes] * seg / 1_000_000.0

                key   = self.m_mayo_abril_to_civil[mes]
                demA  = (self.DA_a_m[key] * self.num_A * self.FEA) / 1_000_000.0
                demB  = (self.DB_a_b[key] * self.num_B * self.FEB) / 1_000_000.0

                # Stocks previos
                if i == 0:
                    prev_año = f"{y-1}/{y}"
                    V_R_prev = self.V_VRFI[prev_año,12] if prev_año in self.anos else 0
                    V_A_prev = self.V_A[prev_año,12]    if prev_año in self.anos else 0
                    V_B_prev = self.V_B[prev_año,12]    if prev_año in self.anos else 0
                else:
                    V_R_prev = self.V_VRFI[año, mes-1]
                    V_A_prev = self.V_A[año,  mes-1]
                    V_B_prev = self.V_B[año,  mes-1]

                # (1) Remanente y prioridad de llenado
                m.addConstr(self.Rem[año,mes]    == Qin - UPREF,                 name=f"rem_{año}_{mes}")
                m.addConstr(self.HeadR[año,mes]  == self.C_VRFI  - V_R_prev,     name=f"headR_{año}_{mes}")
                m.addConstr(self.HeadA[año,mes]  == self.C_TIPO_A - V_A_prev,    name=f"headA_{año}_{mes}")
                m.addConstr(self.HeadB[año,mes]  == self.C_TIPO_B - V_B_prev,    name=f"headB_{año}_{mes}")

                m.addGenConstrMin(self.FillR[año,mes], [self.Rem[año,mes], self.HeadR[año,mes]], name=f"fillR_min_{año}_{mes}")
                m.addConstr(self.zR[año,mes]     == self.Rem[año,mes] - self.FillR[año,mes],     name=f"zR_{año}_{mes}")
                m.addConstr(self.ShareA[año,mes] == 0.71 * self.zR[año,mes],                      name=f"shareA_{año}_{mes}")
                m.addConstr(self.ShareB[año,mes] == 0.29 * self.zR[año,mes],                      name=f"shareB_{año}_{mes}")
                m.addGenConstrMin(self.FillA[año,mes], [self.ShareA[año,mes], self.HeadA[año,mes]], name=f"fillA_min_{año}_{mes}")
                m.addGenConstrMin(self.FillB[año,mes], [self.ShareB[año,mes], self.HeadB[año,mes]], name=f"fillB_min_{año}_{mes}")

                m.addConstr(self.IN_VRFI[año,mes] == self.FillR[año,mes], name=f"in_vrfi_{año}_{mes}")
                m.addConstr(self.IN_A[año,mes]    == self.FillA[año,mes], name=f"in_a_{año}_{mes}")
                m.addConstr(self.IN_B[año,mes]    == self.FillB[año,mes], name=f"in_b_{año}_{mes}")

                # (2) Rebalse (solo remanente)
                m.addConstr(self.E_TOT[año,mes] == self.Rem[año,mes] - self.IN_VRFI[año,mes]
                                                - self.IN_A[año,mes] - self.IN_B[año,mes],
                            name=f"spill_{año}_{mes}")

                # Para reporte
                m.addConstr(self.Q_dis[año,mes] == Qin - UPREF, name=f"qdis_{año}_{mes}")

                # (3) Balances de stock
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

                m.addConstr(self.V_VRFI[año,mes] <= self.C_VRFI,   name=f"cap_vrfi_{año}_{mes}")
                m.addConstr(self.V_A[año,mes]    <= self.C_TIPO_A, name=f"cap_va_{año}_{mes}")
                m.addConstr(self.V_B[año,mes]    <= self.C_TIPO_B, name=f"cap_vb_{año}_{mes}")

                # (4) Disponibilidades para servir
                m.addConstr(self.Q_A[año,mes] <= V_A_prev + self.IN_A[año,mes],     name=f"disp_A_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] <= V_B_prev + self.IN_B[año,mes],     name=f"disp_B_{año}_{mes}")
                m.addConstr(self.Q_ch[año,mes] <= V_R_prev + self.IN_VRFI[año,mes], name=f"disp_ch_{año}_{mes}")
                # (supervisor) ya no necesitamos esta cota suave; quedará implícita con VRFI_avail
                # m.addConstr(self.Q_A_apoyo[año,mes] + self.Q_B_apoyo[año,mes] + self.Q_ch[año,mes]
                #             <= V_R_prev + self.IN_VRFI[año,mes],                    name=f"disp_sup_vrfi_{año}_{mes}")

                # ========= (4.5) PROPIO PRIMERO hasta min(disponible, 50% demanda) =========
                m.addConstr(self.A_avail[año,mes] == V_A_prev + self.IN_A[año,mes], name=f"A_avail_def_{año}_{mes}")
                m.addConstr(self.A_dem50[año,mes] == 0.5*demA,                      name=f"A_dem50_def_{año}_{mes}")
                m.addGenConstrMin(self.A_own_req[año,mes], [self.A_avail[año,mes], self.A_dem50[año,mes]],
                                  name=f"A_own_req_min_{año}_{mes}")
                m.addConstr(self.Q_A[año,mes] >= self.A_own_req[año,mes],           name=f"A_use_own_first_{año}_{mes}")

                m.addConstr(self.B_avail[año,mes] == V_B_prev + self.IN_B[año,mes], name=f"B_avail_def_{año}_{mes}")
                m.addConstr(self.B_dem50[año,mes] == 0.5*demB,                      name=f"B_dem50_def_{año}_{mes}")
                m.addGenConstrMin(self.B_own_req[año,mes], [self.B_avail[año,mes], self.B_dem50[año,mes]],
                                  name=f"B_own_req_min_{año}_{mes}")
                m.addConstr(self.Q_B[año,mes] >= self.B_own_req[año,mes],           name=f"B_use_own_first_{año}_{mes}")

                # ========= (5) Apoyo VRFI: solo para completar 50% como máximo =========
                m.addConstr(self.tA[año,mes] == 0.5*demA - self.Q_A[año,mes], name=f"tA_def_{año}_{mes}")
                m.addConstr(self.tB[año,mes] == 0.5*demB - self.Q_B[año,mes], name=f"tB_def_{año}_{mes}")

                m.addGenConstrMax(self.needA[año,mes], [self.tA[año,mes], self.zeroVar], name=f"needA_max_{año}_{mes}")
                m.addGenConstrMax(self.needB[año,mes], [self.tB[año,mes], self.zeroVar], name=f"needB_max_{año}_{mes}")

                m.addConstr(self.Q_A_apoyo[año,mes] <= self.needA[año,mes], name=f"apA_le_need_{año}_{mes}")
                m.addConstr(self.Q_B_apoyo[año,mes] <= self.needB[año,mes], name=f"apB_le_need_{año}_{mes}")

                # ===== (5.1) “USAR TODO LO POSIBLE DEL VRFI”: saturación dura =====
                # VRFI disponible para apoyo (no incluye spill ni propio de A/B)
                m.addConstr(self.VRFI_avail[año,mes] == V_R_prev + self.IN_VRFI[año,mes] - self.Q_ch[año,mes],
                            name=f"vrfi_avail_{año}_{mes}")
                m.addConstr(self.needTot[año,mes] == self.needA[año,mes] + self.needB[año,mes],
                            name=f"needTot_{año}_{mes}")
                # SupportTot = min(VRFI_avail, needTot)
                m.addGenConstrMin(self.SupportTot[año,mes], [self.VRFI_avail[año,mes], self.needTot[año,mes]],
                                  name=f"supportTot_min_{año}_{mes}")
                # Obliga a usar todo lo posible: Q_A_apoyo + Q_B_apoyo == SupportTot
                m.addConstr(self.Q_A_apoyo[año,mes] + self.Q_B_apoyo[año,mes] == self.SupportTot[año,mes],
                            name=f"use_all_support_{año}_{mes}")

                # ===== (5.5) Slacks diagnósticos (no obligan nada) =====
                m.addConstr(self.rA[año,mes] >= self.needA[año,mes] - self.Q_A_apoyo[año,mes],
                            name=f"slack_needA_{año}_{mes}")
                m.addConstr(self.rB[año,mes] >= self.needB[año,mes] - self.Q_B_apoyo[año,mes],
                            name=f"slack_needB_{año}_{mes}")

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

        # (8) SSR: anual o mensual fija
        if self.fix_ssr_monthly:
            for año in self.anos:
                for mes in self.months:
                    self.model.addConstr(self.Q_ch[año, mes] == self.V_C_H * float(self.ssr_frac.get(mes, 0.0)),
                                         name=f"ssr_mes_{año}_{mes}")
        else:
            for año in self.anos:
                self.model.addConstr(gp.quicksum(self.Q_ch[año, mes] for mes in self.months) == self.V_C_H,
                                     name=f"ssr_anual_{año}")

    # ===================== Objetivo =====================
    def set_objective(self):
        """ Minimiza déficit; castigo leve al apoyo VRFI y premio leve al propio (solo desempate). """
        total_def = gp.quicksum(self.d_A[año,mes] + self.d_B[año,mes]
                                for año in self.anos for mes in self.months)
        pen_vrfi  = gp.quicksum(self.Q_A_apoyo[año,mes] + self.Q_B_apoyo[año,mes]
                                for año in self.anos for mes in self.months)
        inc_prop  = gp.quicksum(self.Q_A[año,mes] + self.Q_B[año,mes]
                                for año in self.anos for mes in self.months)
        tiny = 1e-6
        stock_pen = tiny * gp.quicksum(self.V_A[año,mes] + self.V_B[año,mes] + self.V_VRFI[año,mes]
                                       for año in self.anos for mes in self.months)
        self.model.setObjective(total_def + 1e-3*pen_vrfi - 1e-3*inc_prop + stock_pen, GRB.MINIMIZE)

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
                    'Q_A': self.Q_A[año,mes].X, 'Q_B': self.Q_B[año,mes].X, 'Q_turb': self.Q_turb[año,mes].X,
                    'IN_VRFI': self.IN_VRFI[año,mes].X, 'IN_A': self.IN_A[año,mes].X, 'IN_B': self.IN_B[año,mes].X,
                    'E_TOT': self.E_TOT[año,mes].X,
                    'Q_A_apoyo': self.Q_A_apoyo[año,mes].X, 'Q_B_apoyo': self.Q_B_apoyo[año,mes].X,
                    'VRFI_avail': self.VRFI_avail[año,mes].X, 'SupportTot': self.SupportTot[año,mes].X,
                    'needA': self.needA[año,mes].X, 'needB': self.needB[año,mes].X, 'needTot': self.needTot[año,mes].X,
                    'd_A': self.d_A[año,mes].X, 'd_B': self.d_B[año,mes].X,
                    'QPD_eff_Hm3': QPD_eff_Hm3,
                    'Demanda_A': DemA, 'Demanda_B': DemB,
                    'Q_afl_m3s': Qin_m3s, 'Q_afl_Hm3': Qin,
                    'Rem': self.Rem[año,mes].X, 'FillR': self.FillR[año,mes].X, 'zR': self.zR[año,mes].X,
                    'ShareA': self.ShareA[año,mes].X, 'ShareB': self.ShareB[año,mes].X,
                    'FillA': self.FillA[año,mes].X, 'FillB': self.FillB[año,mes].X,
                    'rA': self.rA[año,mes].X, 'rB': self.rB[año,mes].X
                }
                tot_dem = DemA + DemB
                servA = fila['Q_A'] + fila['Q_A_apoyo']; servB = fila['Q_B'] + fila['Q_B_apoyo']
                fila['Deficit_Total'] = fila['d_A'] + fila['d_B']
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

    # ===================== Exportar reporte TXT =====================
    def export_to_txt(self, filename="reporte_embalse.txt"):
        def bar20(pct):
            n = int(round(min(max(pct,0),100) / 5.0))
            return "█"*n + "·"*(20-n)

        mes_tag = {1:'may',2:'jun',3:'jul',4:'ago',5:'sep',6:'oct',7:'nov',8:'dic',9:'ene',10:'feb',11:'mar',12:'abr'}
        lines = []
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
                    V_R_prev = self.V_VRFI[prev_año,12].X if prev_año in self.anos else 0.0
                    V_A_prev = self.V_A[prev_año,12].X    if prev_año in self.anos else 0.0
                    V_B_prev = self.V_B[prev_año,12].X    if prev_año in self.anos else 0.0
                else:
                    V_R_prev = self.V_VRFI[año, mes-1].X
                    V_A_prev = self.V_A[año,  mes-1].X
                    V_B_prev = self.V_B[año,  mes-1].X

                V_R_fin = self.V_VRFI[año, mes].X
                V_A_fin = self.V_A[año, mes].X
                V_B_fin = self.V_B[año, mes].X

                pct_R_prev = (V_R_prev/self.C_VRFI*100) if self.C_VRFI>0 else 0
                pct_R_fin  = (V_R_fin /self.C_VRFI*100) if self.C_VRFI>0 else 0
                pct_A_prev = (V_A_prev/self.C_TIPO_A*100) if self.C_TIPO_A>0 else 0
                pct_A_fin  = (V_A_fin /self.C_TIPO_A*100) if self.C_TIPO_A>0 else 0
                pct_B_prev = (V_B_prev/self.C_TIPO_B*100) if self.C_TIPO_B>0 else 0
                pct_B_fin  = (V_B_fin /self.C_TIPO_B*100) if self.C_TIPO_B>0 else 0

                motivo  = "-" if EB <= 1e-9 else "Sobra tras llenado (ex-post)"

                barR = bar20(pct_R_fin); barA = bar20(pct_A_fin); barB = bar20(pct_B_fin)

                row1 = (f"{mes_tag[mes]:<4} "
                        f"{Qin_m3s:6.2f}  {Qin_Hm3:7.1f}  "
                        f"{QPD_m3s:6.2f}  {QPD_Hm3:7.1f}  "
                        f"{IN_R:7.1f}  {INA:7.1f}  {INB:7.1f}  {EB:7.1f}  "
                        f"{motivo:<24}  "
                        f"{V_R_prev:5.1f}→{V_R_fin:<5.1f}      "
                        f"{V_A_prev:5.1f}→{V_A_fin:<5.1f}    "
                        f"{V_B_prev:5.1f}→{V_B_fin:<5.1f}    "
                        f"{pct_R_prev:3.0f}→{pct_R_fin:<3.0f}%     "
                        f"{pct_A_prev:3.0f}→{pct_A_fin:<3.0f}%   "
                        f"{pct_B_prev:3.0f}→{pct_B_fin:<3.0f}%     "
                        f" |  VRFI[{V_R_fin:6.1f}] {barR}  "
                        f"A[{V_A_fin:6.1f}] {barA}  "
                        f"B[{V_B_fin:6.1f}] {barB}")
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
                VRFIa = self.VRFI_avail[año, mes].X
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
