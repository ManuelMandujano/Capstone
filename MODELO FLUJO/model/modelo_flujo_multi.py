# model/modelo_flujo_multi.py
import gurobipy as gp
from gurobipy import GRB
from typing import List, Dict, Any


class EmbalseModelMulti:
    """
    Red de flujo tiempo-expandida para Y años concatenados (abril–marzo * Y).

    Cambios clave:
      • Preferente mensual: UPREF[k] = min(QPD_nominal_mes, Qin_k)  (todo en m³/s ← convertido a m³/mes).
        => SUP (apoyo VRFI a preferente) no se usa: SUP[k] = 0.
        => SL_PREF[k] = 0 (sin holgura de preferente).
      • Llenado del remanente: VRFI primero, luego A/B en 0.71/0.29 con reasignación.
      • EB sólo si el remanente no cabe en VRFI + A + B.
      • Objetivo: min sum(d_A + d_B).

    Pérdidas: L_R, L_A, L_B (m³/mes):
      L_* ≤ lambda_* * perdidas_mensuales[mes]  y  L_* ≤ V_*_prev.

    NOTA: Este archivo mantiene genConstr MIN/MAX/INDICATOR que ya tenías;
          sólo se cambia la definición de preferente (UPREF) y se fuerza SUP=0 y SL_PREF=0.
    """

    def __init__(self, params: Dict[str, Any]):
        self.p = params.copy()
        self.m = gp.Model("Embalse_Nueva_Punilla_Multi")

        # defaults
        self.p.setdefault('segundos_mes', [2678400,2592000,2678400,2592000,2678400,2592000,
                                           2678400,2592000,2678400,2592000,2678400,2592000])
        self.p.setdefault('temporada_riego', [6,7,8,9,10,11,0])  # OCT–ABR (abril=0)
        self.p.setdefault('perdidas_mensuales', [0]*12)
        self.p.setdefault('eta', 0.85)
        self.p.setdefault('lambda_R', 0.4)
        self.p.setdefault('lambda_A', 0.4)
        self.p.setdefault('lambda_B', 0.2)
        self.p.setdefault('force_FE_one', True)

    # -------------------------
    # Variables
    # -------------------------
    def setup_variables(self, N: int) -> None:
        m = self.m
        p = self.p
        # stocks
        self.V_R = m.addVars(N, lb=0, ub=p['C_R'], name="V_R")
        self.V_A = m.addVars(N, lb=0, ub=p['C_A'], name="V_A")
        self.V_B = m.addVars(N, lb=0, ub=p['C_B'], name="V_B")
        # flujos toma / llenado / rebalse
        self.UPREF   = m.addVars(N, lb=0, name="UPREF")
        self.SUP     = m.addVars(N, lb=0, name="SUP")         # forzado a 0 (no se usa para preferente)
        self.IN_VRFI = m.addVars(N, lb=0, name="IN_VRFI")
        self.INA     = m.addVars(N, lb=0, name="INA")
        self.INB     = m.addVars(N, lb=0, name="INB")
        self.EB      = m.addVars(N, lb=0, name="EB")
        # entregas y apoyos
        self.R_A     = m.addVars(N, lb=0, name="R_A")
        self.R_B     = m.addVars(N, lb=0, name="R_B")
        self.R_H     = m.addVars(N, lb=0, name="R_H")
        self.UVRFI_A = m.addVars(N, lb=0, name="UVRFI_A")
        self.UVRFI_B = m.addVars(N, lb=0, name="UVRFI_B")
        # déficits, caudal turbinado
        self.d_A     = m.addVars(N, lb=0, name="d_A")
        self.d_B     = m.addVars(N, lb=0, name="d_B")
        self.Q_turb  = m.addVars(N, lb=0, name="Q_turb")

        # pérdidas efectivas (m3/mes) – "sin agua → sin pérdidas"
        self.L_R = m.addVars(N, lb=0, name="L_R")
        self.L_A = m.addVars(N, lb=0, name="L_A")
        self.L_B = m.addVars(N, lb=0, name="L_B")

        # detectores “parte vacío” (para el tope/piso del 50% de la demanda)
        self.A_empty = m.addVars(N, vtype=GRB.BINARY, name="A_empty")
        self.B_empty = m.addVars(N, vtype=GRB.BINARY, name="B_empty")

        # (queda, pero lo forzaremos a 0)
        self.SL_PREF = m.addVars(N, lb=0, name="SL_PREF")

    # -------------------------
    # Restricciones
    # -------------------------
    def setup_constraints(self,
                          Q_afluente_all: List[float],      # m3/s por mes (horizonte completo)
                          QPD_eff_all_m3s: List[float],      # m3/s por mes (ya min(QPD_nom, Qin))
                          dem_A_12: List[float],             # m3/mes por mes (12)
                          dem_B_12: List[float],             # m3/mes por mes (12)
                          n_years: int) -> None:
        m, p = self.m, self.p
        N = len(Q_afluente_all)
        assert N == 12 * n_years, "El largo de Q_afluente_all debe ser 12*n_years"
        assert len(QPD_eff_all_m3s) == N, "QPD_eff_all_m3s debe tener largo N (=12*n_years)"

        # lambdas de pérdidas
        m.addConstr(p['lambda_R'] + p['lambda_A'] + p['lambda_B'] == 1, "lambda_sum")

        EPS0 = 1.0  # m3 para “parte vacío” (evita problemas numéricos)

        for k in range(N):
            mes = k % 12
            seg = p['segundos_mes'][mes]
            Qin = Q_afluente_all[k] * seg          # m³/mes disponibles
            Qpd_eff = QPD_eff_all_m3s[k] * seg     # m³/mes de preferente efectivo (min(QPD_nom, Qin_m3s))
            demA = dem_A_12[mes]
            demB = dem_B_12[mes]

            # stocks previos
            V_R_prev = self.V_R[k-1] if k > 0 else p['V_R_inicial']
            V_A_prev = self.V_A[k-1] if k > 0 else p['V_A_inicial']
            V_B_prev = self.V_B[k-1] if k > 0 else p['V_B_inicial']

            # === PREFERENTE: UPREF = min(QPD_nom, Qin) y no hay SUP ni SL_PREF ===
            m.addConstr(self.UPREF[k] == Qpd_eff, f"pref_eq_{k}")
            m.addConstr(self.SUP[k] == 0,        f"sup_zero_{k}")
            m.addConstr(self.SL_PREF[k] == 0,    f"slpref_zero_{k}")
            # (opcional, refuerzo): UPREF ≤ Qin
            m.addConstr(self.UPREF[k] <= Qin,    f"pref_leq_Qin_{k}")

            # === REMANENTE DEL RÍO DESPUÉS DE ENTREGAR UPREF ===
            rem = m.addVar(lb=0, name=f"rem[{k}]")
            m.addConstr(rem == Qin - self.UPREF[k], f"rem_def_{k}")  # (SUP=0)

            # Capacidades disponibles al inicio del mes (headrooms)
            capR = m.addVar(lb=0, name=f"capR[{k}]"); m.addConstr(capR == p['C_R'] - V_R_prev, f"capR_def_{k}")
            capA = m.addVar(lb=0, name=f"capA[{k}]"); m.addConstr(capA == p['C_A'] - V_A_prev, f"capA_def_{k}")
            capB = m.addVar(lb=0, name=f"capB[{k}]"); m.addConstr(capB == p['C_B'] - V_B_prev, f"capB_def_{k}")

            # === PRIORIDAD DE LLENADO: VRFI → A/B → EB ===
            tR = m.addVar(lb=-GRB.INFINITY, name=f"tR[{k}]")
            m.addConstr(tR == rem - capR, f"tR_def_{k}")
            zR = m.addVar(lb=0, name=f"zR[{k}]")
            m.addGenConstrMax(zR, [tR, 0.0], name=f"zR_max_{k}")

            fillR = m.addVar(lb=0, name=f"fillR[{k}]")
            m.addConstr(fillR == rem - zR, f"fillR_def_{k}")
            m.addConstr(self.IN_VRFI[k] == fillR, f"invrfi_fillfirst_{k}")

            tAB = m.addVar(lb=-GRB.INFINITY, name=f"tAB[{k}]")
            m.addConstr(tAB == zR - capA - capB, f"tAB_def_{k}")
            EB_cap = m.addVar(lb=0, name=f"EB_cap[{k}]")
            m.addGenConstrMax(EB_cap, [tAB, 0.0], name=f"EB_cap_max_{k}")
            m.addConstr(self.EB[k] == EB_cap, f"EB_eq_{k}")

            # === Distribución 71/29 con reasignación ===
            shareA = m.addVar(lb=0, name=f"shareA[{k}]")
            shareB = m.addVar(lb=0, name=f"shareB[{k}]")
            m.addConstr(shareA == 0.71 * zR, f"shareA_def_{k}")
            m.addConstr(shareB == 0.29 * zR, f"shareB_def_{k}")

            yA = m.addVar(lb=0, name=f"yA[{k}]")
            yB = m.addVar(lb=0, name=f"yB[{k}]")
            m.addGenConstrMin(yA, [shareA, capA], name=f"yA_min_{k}")
            m.addGenConstrMin(yB, [shareB, capB], name=f"yB_min_{k}")

            overflowA = m.addVar(lb=0, name=f"overflowA[{k}]")
            overflowB = m.addVar(lb=0, name=f"overflowB[{k}]")
            extraA    = m.addVar(lb=0, name=f"extraA[{k}]")
            extraB    = m.addVar(lb=0, name=f"extraB[{k}]")
            m.addConstr(overflowA == shareA - yA, f"overflowA_def_{k}")
            m.addConstr(overflowB == shareB - yB, f"overflowB_def_{k}")
            m.addConstr(extraA    == capA   - yA, f"extraA_def_{k}")
            m.addConstr(extraB    == capB   - yB, f"extraB_def_{k}")

            tA = m.addVar(lb=0, name=f"tA[{k}]")  # B→A
            tB = m.addVar(lb=0, name=f"tB[{k}]")  # A→B
            m.addConstr(tA <= overflowB, f"tA_leq_overflowB_{k}")
            m.addConstr(tA <= extraA,    f"tA_leq_extraA_{k}")
            m.addConstr(tB <= overflowA, f"tB_leq_overflowA_{k}")
            m.addConstr(tB <= extraB,    f"tB_leq_extraB_{k}")

            m.addConstr(self.INA[k] == yA + tA, f"INA_final_{k}")
            m.addConstr(self.INB[k] == yB + tB, f"INB_final_{k}")
            m.addConstr(self.INA[k] + self.INB[k] == zR - self.EB[k], f"fill_AB_{k}")
            m.addConstr(tA + tB == zR - self.EB[k] - (yA + yB), f"tA_tB_balance_{k}")

            # --- PÉRDIDAS EFECTIVAS ---
            seg_per = p['perdidas_mensuales'][mes]
            loss_cap_R = p['lambda_R'] * seg_per
            loss_cap_A = p['lambda_A'] * seg_per
            loss_cap_B = p['lambda_B'] * seg_per

            m.addConstr(self.L_R[k] <= loss_cap_R, f"L_R_cap_{k}")
            m.addConstr(self.L_A[k] <= loss_cap_A, f"L_A_cap_{k}")
            m.addConstr(self.L_B[k] <= loss_cap_B, f"L_B_cap_{k}")

            m.addConstr(self.L_R[k] <= V_R_prev,   f"L_R_stockprev_{k}")
            m.addConstr(self.L_A[k] <= V_A_prev,   f"L_A_stockprev_{k}")
            m.addConstr(self.L_B[k] <= V_B_prev,   f"L_B_stockprev_{k}")

            # --- Servicio de riego (con FE) ---
            feA = (self.p['FE_A_12'][mes] if 'FE_A_12' in self.p else float(self.p.get('FE_A', 1.0)))
            feB = (self.p['FE_B_12'][mes] if 'FE_B_12' in self.p else float(self.p.get('FE_B', 1.0)))
            DemA_eff = feA * demA
            DemB_eff = feB * demB

            m.addConstr(self.d_A[k] == DemA_eff - (self.R_A[k] + self.UVRFI_A[k]), f"def_deficit_A_{k}")
            m.addConstr(self.d_B[k] == DemB_eff - (self.R_B[k] + self.UVRFI_B[k]), f"def_deficit_B_{k}")

            m.addConstr(self.R_A[k] + self.UVRFI_A[k] <= DemA_eff, f"no_overserve_A_{k}")
            m.addConstr(self.R_B[k] + self.UVRFI_B[k] <= DemB_eff, f"no_overserve_B_{k}")

            # --- Detectores “parte vacío” y topes 50% (indicadores como tenías) ---
            if k == 0:
                m.addConstr(self.A_empty[k] == (1 if p['V_A_inicial'] <= EPS0 else 0), name=f"Aempty_fix_{k}")
                m.addConstr(self.B_empty[k] == (1 if p['V_B_inicial'] <= EPS0 else 0), name=f"Bempty_fix_{k}")
            else:
                m.addGenConstrIndicator(self.A_empty[k], 1, self.V_A[k-1], GRB.LESS_EQUAL,  EPS0, name=f"Aempty1_{k}")
                m.addGenConstrIndicator(self.A_empty[k], 0, self.V_A[k-1], GRB.GREATER_EQUAL, EPS0, name=f"Aempty0_{k}")
                m.addGenConstrIndicator(self.B_empty[k], 1, self.V_B[k-1], GRB.LESS_EQUAL,  EPS0, name=f"Bempty1_{k}")
                m.addGenConstrIndicator(self.B_empty[k], 0, self.V_B[k-1], GRB.GREATER_EQUAL, EPS0, name=f"Bempty0_{k}")

            m.addGenConstrIndicator(self.A_empty[k], 1, self.UVRFI_A[k], GRB.LESS_EQUAL, 0.5 * DemA_eff,
                                    name=f"uvrfiA_half_dem_if_empty_{k}")
            m.addGenConstrIndicator(self.B_empty[k], 1, self.UVRFI_B[k], GRB.LESS_EQUAL, 0.5 * DemB_eff,
                                    name=f"uvrfiB_half_dem_if_empty_{k}")

            # --- VRFI NETO DISPONIBLE (tras SUP=0 y R_H) ---
            tmp_vrfi = m.addVar(lb=-GRB.INFINITY, name=f"tmp_vrfi[{k}]")
            m.addConstr(tmp_vrfi == V_R_prev + self.IN_VRFI[k] - self.R_H[k], f"tmp_vrfi_def_{k}")
            VRFI_net = m.addVar(lb=0, name=f"VRFI_net[{k}]")
            m.addGenConstrMax(VRFI_net, [tmp_vrfi, 0.0], name=f"VRFI_net_max_{k}")

            # Piso activable: min(0.5*Dem, cuota*VRFI_net)
            Mbig = float(self.p.get('C_R', 1e9))
            auxA1 = m.addVar(lb=0, name=f"auxA1[{k}]"); m.addConstr(auxA1 == 0.5 * DemA_eff, name=f"auxA1_def_{k}")
            auxA2 = m.addVar(lb=0, name=f"auxA2[{k}]"); m.addConstr(auxA2 == 0.71 * VRFI_net, name=f"auxA2_def_{k}")
            auxB1 = m.addVar(lb=0, name=f"auxB1[{k}]"); m.addConstr(auxB1 == 0.5 * DemB_eff, name=f"auxB1_def_{k}")
            auxB2 = m.addVar(lb=0, name=f"auxB2[{k}]"); m.addConstr(auxB2 == 0.29 * VRFI_net, name=f"auxB2_def_{k}")
            minA_req = m.addVar(lb=0, name=f"minA_req[{k}]"); m.addGenConstrMin(minA_req, [auxA1, auxA2], name=f"minA_min_{k}")
            minB_req = m.addVar(lb=0, name=f"minB_req[{k}]"); m.addGenConstrMin(minB_req, [auxB1, auxB2], name=f"minB_min_{k}")
            m.addConstr(self.UVRFI_A[k] >= minA_req - Mbig * (1 - self.A_empty[k]), f"uvrfiA_min_lb_{k}")
            m.addConstr(self.UVRFI_B[k] >= minB_req - Mbig * (1 - self.B_empty[k]), f"uvrfiB_min_lb_{k}")

            # Topes 71/29 contra VRFI_net
            m.addConstr(self.UVRFI_A[k] <= 0.71 * VRFI_net, f"uvrfiA_cota_{k}")
            m.addConstr(self.UVRFI_B[k] <= 0.29 * VRFI_net, f"uvrfiB_cota_{k}")

            # Disponibilidad total (sin sobregiro bruto) — SUP=0
            m.addConstr(
                self.UVRFI_A[k] + self.UVRFI_B[k] + self.R_H[k]
                <= V_R_prev + self.IN_VRFI[k],
                f"vrfi_avail_{k}"
            )

            # disponibilidad de entrega desde A y B
            m.addConstr(self.R_A[k] <= V_A_prev + self.INA[k], f"disp_A_{k}")
            m.addConstr(self.R_B[k] <= V_B_prev + self.INB[k], f"disp_B_{k}")

            # balances de stocks
            m.addConstr(
                self.V_R[k] == V_R_prev + self.IN_VRFI[k] - self.R_H[k] - self.UVRFI_A[k] - self.UVRFI_B[k]
                               - self.L_R[k],
                f"bal_R_{k}"
            )
            m.addConstr(self.V_A[k] == V_A_prev + self.INA[k] - self.R_A[k] - self.L_A[k], f"bal_A_{k}")
            m.addConstr(self.V_B[k] == V_B_prev + self.INB[k] - self.R_B[k] - self.L_B[k], f"bal_B_{k}")

            # turbinado (el apoyo VRFI va por canales, no turbinado)
            m.addConstr(self.Q_turb[k] * seg == self.UPREF[k] + self.R_H[k] + self.R_A[k] + self.R_B[k],
                        f"qturb_{k}")

        # SSR anual por año
        for y in range(n_years):
            idx0, idx1 = 12*y, 12*(y+1)
            m.addConstr(gp.quicksum(self.R_H[k] for k in range(idx0, idx1)) == self.p['consumo_humano_anual'],
                        f"humano_anual_y{y}")

    # -------------------------
    # Objetivo
    # -------------------------
    def set_objective(self, N: int) -> None:
        self.m.setObjective(gp.quicksum(self.d_A[k] + self.d_B[k] for k in range(N)), GRB.MINIMIZE)

    # -------------------------
    # Solve
    # -------------------------
    def solve(self,
              Q_afluente_all: List[float],      # m3/s por mes (horizonte)
              QPD_eff_all_m3s: List[float],     # m3/s por mes (min(QPD_nom, Qin))
              dem_A_12: List[float],            # m3/mes (12)
              dem_B_12: List[float],            # m3/mes (12)
              n_years: int):
        try:
            N = 12 * n_years
            self.setup_variables(N)
            self.setup_constraints(Q_afluente_all, QPD_eff_all_m3s, dem_A_12, dem_B_12, n_years)
            self.set_objective(N)

            if 'TimeLimit' in self.p:
                self.m.setParam('TimeLimit', self.p['TimeLimit'])
            self.m.setParam('OutputFlag', 1)
            self.m.optimize()

            if self.m.status == GRB.INFEASIBLE:
                print("⚠️ Modelo inviable; generando IIS…")
                self.m.setParam(GRB.Param.IISMethod, 1)
                self.m.computeIIS()
                self.m.write("infeasible.ilp")
                self.m.write("model.lp")
                return None

            if self.m.status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
                return None

            sol = {
                'V_R':  [self.V_R[k].X for k in range(N)],
                'V_A':  [self.V_A[k].X for k in range(N)],
                'V_B':  [self.V_B[k].X for k in range(N)],
                'R_A':  [self.R_A[k].X for k in range(N)],
                'R_B':  [self.R_B[k].X for k in range(N)],
                'R_H':  [self.R_H[k].X for k in range(N)],
                'd_A':  [self.d_A[k].X for k in range(N)],
                'd_B':  [self.d_B[k].X for k in range(N)],
                'UPREF':[self.UPREF[k].X for k in range(N)],
                'IN_VRFI':[self.IN_VRFI[k].X for k in range(N)],
                'INA':  [self.INA[k].X for k in range(N)],
                'INB':  [self.INB[k].X for k in range(N)],
                'SUP':  [self.SUP[k].X for k in range(N)],
                'EB':   [self.EB[k].X for k in range(N)],
                'UVRFI_A': [self.UVRFI_A[k].X for k in range(N)],
                'UVRFI_B': [self.UVRFI_B[k].X for k in range(N)],
                'Q_turb':[self.Q_turb[k].X for k in range(N)],
                'L_R':  [self.L_R[k].X for k in range(N)],
                'L_A':  [self.L_A[k].X for k in range(N)],
                'L_B':  [self.L_B[k].X for k in range(N)],
                'A_empty': [self.A_empty[k].X for k in range(N)],
                'B_empty': [self.B_empty[k].X for k in range(N)],
                'objetivo': self.m.objVal,
                'status':   self.m.status,
            }
            # energía total
            energia = 0.0
            seg = self.p['segundos_mes']
            for k in range(N):
                energia += (self.p['eta'] * sol['Q_turb'][k] * seg[k % 12]) / 3_600_000.0
            sol['energia_total'] = energia
            return sol
        except Exception as e:
            print(f"Error solve multi: {e}")
            return None
