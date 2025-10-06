# model/modelo_flujo.py
import gurobipy as gp
from gurobipy import GRB
from typing import List, Dict, Any


class EmbalseModel:
    """
    Modelo mensual (abril–marzo) como red de flujo tiempo-expandida con bolsillos VRFI, A y B.

    STAGE 0 (red mínima):
      - Balance río: Qpref + Qdis = Qin, con Qpref ≤ Qin y Qpref ≤ QPD·seg
      - Nodo almacenable: Qdis = EB + Qalm   (EB ≡ rebalse total a río)
      - Split almacenable: Qalm = IN_VRFI + EVRFI
      - Regla 71/29: INA = 0.71*EVRFI ; INB = 0.29*EVRFI
      - Capacidades de entrada: IN_* ≤ C_* − S_*_{prev}
      - Balances de stock: SVRFI = prev + IN_VRFI ; SA = prev + INA ; SB = prev + INB
      - Reporte: V_R=SVRFI, V_A=SA, V_B=SB
      - Objetivo: min Σ EB

    STAGES ≥ 1 (modelo completo):
      - Conservación en toma: Qin + SUP = UPREF + IN_VRFI + INA + INB + EB
      - UPREF ≥ QPD·seg (opcional forzar min(Qin, QPD·seg) con flag)
      - Regla 71/29 sobre saldo: INA=0.71*(Qin - (UPREF-SUP) - IN_VRFI), INB=0.29*(...)
      - Capacidades de entrada: IN_* ≤ C_* − V_*_{prev}
      - Balances con pérdidas y apoyos: V_R, V_A, V_B
      - SSR (Stage ≥ 2): ΣR_H = consumo_anual; R_H[m] ≤ V_R(prev)
      - Apoyos (Stage ≥ 3): UVRFI_A ≤ 0.71·V_R(prev), UVRFI_B ≤ 0.29·V_R(prev); ≤ R_A/R_B
      - Servicio riego (Stage ≥ 1): R_A + UVRFI_A + d_A ≥ FE_A·DemA, idem B (con caps por demanda)
      - FE (Stage ≥ 4): FE_A/FE_B por PWL en función de V_sep_deshielo = V_R[sep] + pronóstico
      - Turbinado (Stage ≥ 4): Q_turb*seg = UPREF + R_H + R_A + R_B
      - Objetivo: min Σ(d_A + d_B)

    Parámetros útiles en 'params':
      - stage: int (0..4). Si no viene, se asume 4.
      - force_upref_equals_min: bool (default False) → fuerza UPREF = min(Qin, QPD·seg) con GenConstrMin.
    """

    # -------------------------------
    # ctor y toggles
    # -------------------------------
    def __init__(self, params: Dict[str, Any]):
        self.p = params.copy()
        self.model = gp.Model("Embalse_Nueva_Punilla_Red")
        self.stage = int(self.p.get('stage', 4))  # por defecto: etapa final

        # Defaults de parámetros
        self.p.setdefault('segundos_mes', [2678400,2592000,2678400,2592000,2678400,2592000,
                                           2678400,2592000,2678400,2592000,2678400,2592000])
        self.p.setdefault('temporada_riego', [6,7,8,9,10,11,0])  # oct–abr (abril=0)
        self.p.setdefault('perdidas_mensuales', [0]*12)
        self.p.setdefault('eta', 0.85)
        self.p.setdefault('lambda_R', 0.4)
        self.p.setdefault('lambda_A', 0.4)
        self.p.setdefault('lambda_B', 0.2)
        # extras
        self.p.setdefault('consumo_humano_anual', 0.0)
        self.p.setdefault('pronostico_deshielo_promedio', 0.0)
        self.p.setdefault('TimeLimit', 300)
        self.p.setdefault('force_upref_equals_min', False)

    def _features(self):
        """Deriva toggles desde self.stage para activar bloques sin retocar constraints."""
        s = int(self.stage)
        return {
            'use_deliveries':   s >= 1,  # R_A/R_B + déficits
            'use_ssr_losses':   s >= 2,  # R_H anual + pérdidas
            'use_supports':     s >= 3,  # UVRFI_A / UVRFI_B
            'use_fe_pwl':       s >= 4,  # FE_A / FE_B por PWL
            'use_turbine':      s >= 4,  # Q_turb = salidas a pie de presa
        }

    # -------------------------------
    # variables
    # -------------------------------
    def setup_variables(self, n_meses: int = 12) -> None:
        m, p = self.model, self.p

        # Reporte (existirán siempre)
        self.V_R = m.addVars(n_meses, lb=0, ub=p['C_R'], name="V_R")
        self.V_A = m.addVars(n_meses, lb=0, ub=p['C_A'], name="V_A")
        self.V_B = m.addVars(n_meses, lb=0, ub=p['C_B'], name="V_B")

        # STAGE 0 (notación río/almacenable)
        self.SVRFI = m.addVars(n_meses, lb=0, ub=p['C_R'], name="SVRFI")
        self.SA    = m.addVars(n_meses, lb=0, ub=p['C_A'], name="SA")
        self.SB    = m.addVars(n_meses, lb=0, ub=p['C_B'], name="SB")

        self.Qpref = m.addVars(n_meses, lb=0, name="Qpref")  # m³/mes (preferente)
        self.Qdis  = m.addVars(n_meses, lb=0, name="Qdis")   # disponible tras preferente
        self.Qalm  = m.addVars(n_meses, lb=0, name="Qalm")   # parte almacenable
        self.EB    = m.addVars(n_meses, lb=0, name="EB")     # rebalse total a río (ETOT)

        self.IN_VRFI = m.addVars(n_meses, lb=0, name="IN_VRFI")
        self.EVRFI   = m.addVars(n_meses, lb=0, name="EVRFI")  # VRFI→(A,B) para 71/29
        self.INA     = m.addVars(n_meses, lb=0, name="INA")
        self.INB     = m.addVars(n_meses, lb=0, name="INB")

        # STAGES ≥ 1 (modelo completo)
        self.UPREF   = m.addVars(n_meses, lb=0, name="UPREF")
        self.SUP     = m.addVars(n_meses, lb=0, name="SUP")

        self.R_A  = m.addVars(n_meses, lb=0, name="R_A")
        self.R_B  = m.addVars(n_meses, lb=0, name="R_B")
        self.R_H  = m.addVars(n_meses, lb=0, name="R_H")
        self.UVRFI_A = m.addVars(n_meses, lb=0, name="UVRFI_A")
        self.UVRFI_B = m.addVars(n_meses, lb=0, name="UVRFI_B")

        self.d_A = m.addVars(n_meses, lb=0, name="d_A")
        self.d_B = m.addVars(n_meses, lb=0, name="d_B")

        self.Q_turb = m.addVars(n_meses, lb=0, name="Q_turb")

        self.FE_A = m.addVar(lb=0, ub=1, name="FE_A")
        self.FE_B = m.addVar(lb=0, ub=1, name="FE_B")
        self.V_sep_deshielo = m.addVar(lb=0, name="V_sep_deshielo")

    # -------------------------------
    # restricciones
    # -------------------------------
    def setup_constraints(self,
                          Q_afluente: List[float],
                          Q_PD: List[float],
                          demandas_A: List[float],
                          demandas_B: List[float]) -> None:
        m, p = self.model, self.p
        n = len(Q_afluente)

        # lambdas de pérdidas (inocuo en stage 0)
        m.addConstr(p['lambda_R'] + p['lambda_A'] + p['lambda_B'] == 1, name="lambda_sum")

        # --------- STAGE 0: red mínima ----------
        if self.stage == 0:
            # inits
            m.addConstr(self.SVRFI[0] == p['V_R_inicial'], name="init_SVRFI")
            m.addConstr(self.SA[0]    == p['V_A_inicial'], name="init_SA")
            m.addConstr(self.SB[0]    == p['V_B_inicial'], name="init_SB")

            for k in range(n):
                seg = p['segundos_mes'][k]
                Qin = Q_afluente[k] * seg
                Qpd = Q_PD[k] * seg

                # río
                m.addConstr(self.Qpref[k] + self.Qdis[k] == Qin, name=f"rio_bal_{k}")
                m.addConstr(self.Qpref[k] <= Qin,              name=f"rio_pref_leq_Qin_{k}")
                m.addConstr(self.Qpref[k] <= Qpd,              name=f"rio_pref_leq_Qpd_{k}")

                # almacenable
                m.addConstr(self.Qdis[k] == self.EB[k] + self.Qalm[k], name=f"alm_node_{k}")
                m.addConstr(self.Qalm[k] == self.IN_VRFI[k] + self.EVRFI[k], name=f"alm_split_{k}")
                m.addConstr(self.INA[k]  == 0.71 * self.EVRFI[k], name=f"inA_71_{k}")
                m.addConstr(self.INB[k]  == 0.29 * self.EVRFI[k], name=f"inB_29_{k}")

                # capacidades
                SV_prev = self.SVRFI[k-1] if k>0 else p['V_R_inicial']
                SA_prev = self.SA[k-1]    if k>0 else p['V_A_inicial']
                SB_prev = self.SB[k-1]    if k>0 else p['V_B_inicial']
                m.addConstr(self.IN_VRFI[k] <= p['C_R'] - SV_prev, name=f"cap_in_vrfi_{k}")
                m.addConstr(self.INA[k]     <= p['C_A'] - SA_prev, name=f"cap_in_A_{k}")
                m.addConstr(self.INB[k]     <= p['C_B'] - SB_prev, name=f"cap_in_B_{k}")

                # balances
                m.addConstr(self.SVRFI[k] == SV_prev + self.IN_VRFI[k], name=f"bal_SVRFI_{k}")
                m.addConstr(self.SA[k]    == SA_prev + self.INA[k],     name=f"bal_SA_{k}")
                m.addConstr(self.SB[k]    == SB_prev + self.INB[k],     name=f"bal_SB_{k}")

                # reporte
                m.addConstr(self.V_R[k] == self.SVRFI[k], name=f"Vreport_R_{k}")
                m.addConstr(self.V_A[k] == self.SA[k],    name=f"Vreport_A_{k}")
                m.addConstr(self.V_B[k] == self.SB[k],    name=f"Vreport_B_{k}")
            return  # no sigue a la rama completa

        # --------- STAGES ≥ 1: modelo completo con flags ----------
        feat = self._features()
        use_deliv   = feat['use_deliveries']
        use_ssr     = feat['use_ssr_losses']
        use_losses  = feat['use_ssr_losses']
        use_supp    = feat['use_supports']
        use_fe_pwl  = feat['use_fe_pwl']
        use_turbine = feat['use_turbine']

        # inits
        m.addConstr(self.V_R[0] == p['V_R_inicial'], name="init_R")
        m.addConstr(self.V_A[0] == p['V_A_inicial'], name="init_A")
        m.addConstr(self.V_B[0] == p['V_B_inicial'], name="init_B")

        for k in range(n):
            seg = p['segundos_mes'][k]
            Qin = Q_afluente[k] * seg
            Qpd = Q_PD[k] * seg

            # preferentes
            if p.get('force_upref_equals_min', False):
                # UPREF = min(Qin, Qpd) con GenConstrMin (introducimos vars fijas para Qin/Qpd)
                Qin_var = m.addVar(lb=Qin, ub=Qin, name=f"Qin_fix_{k}")
                Qpd_var = m.addVar(lb=Qpd, ub=Qpd, name=f"Qpd_fix_{k}")
                m.addGenConstrMin(self.UPREF[k], [Qin_var, Qpd_var], name=f"upref_min_{k}")
                # SUP libre para completar toma si quisieras, pero ya no necesario
            else:
                m.addConstr(self.UPREF[k] >= Qpd, name=f"upref_min_{k}")

            # toma: conservación general
            m.addConstr(
                Qin + self.SUP[k] == self.UPREF[k] + self.IN_VRFI[k] + self.INA[k] + self.INB[k] + self.EB[k],
                name=f"toma_conserv_{k}"
            )

            # 71/29 sobre saldo
            rem = (Qin - (self.UPREF[k] - self.SUP[k]) - self.IN_VRFI[k] - self.EB[k])
            m.addConstr(self.INA[k] == 0.71 * rem, name=f"inA_71_{k}")
            m.addConstr(self.INB[k] == 0.29 * rem, name=f"inB_29_{k}")

            # capacidades entrada
            V_R_prev = self.V_R[k-1] if k>0 else p['V_R_inicial']
            V_A_prev = self.V_A[k-1] if k>0 else p['V_A_inicial']
            V_B_prev = self.V_B[k-1] if k>0 else p['V_B_inicial']
            m.addConstr(self.IN_VRFI[k] <= p['C_R'] - V_R_prev, name=f"cap_in_R_{k}")
            m.addConstr(self.INA[k]     <= p['C_A'] - V_A_prev, name=f"cap_in_A_{k}")
            m.addConstr(self.INB[k]     <= p['C_B'] - V_B_prev, name=f"cap_in_B_{k}")

            # apoyos
            if use_supp:
                m.addConstr(self.UVRFI_A[k] <= 0.71 * V_R_prev, name=f"uvrfiA_cota_{k}")
                m.addConstr(self.UVRFI_B[k] <= 0.29 * V_R_prev, name=f"uvrfiB_cota_{k}")
                m.addConstr(self.UVRFI_A[k] <= self.R_A[k],     name=f"uvrfiA_leq_RA_{k}")
                m.addConstr(self.UVRFI_B[k] <= self.R_B[k],     name=f"uvrfiB_leq_RB_{k}")
            else:
                m.addConstr(self.UVRFI_A[k] == 0.0, name=f"uvrfiA_off_{k}")
                m.addConstr(self.UVRFI_B[k] == 0.0, name=f"uvrfiB_off_{k}")

        # balances con pérdidas y apoyos (flags)
        for k in range(n):
            seg_per = p['perdidas_mensuales'][k]
            V_R_prev = self.V_R[k-1] if k>0 else p['V_R_inicial']
            V_A_prev = self.V_A[k-1] if k>0 else p['V_A_inicial']
            V_B_prev = self.V_B[k-1] if k>0 else p['V_B_inicial']

            loss_R = p['lambda_R']*seg_per if use_losses else 0.0
            loss_A = p['lambda_A']*seg_per if use_losses else 0.0
            loss_B = p['lambda_B']*seg_per if use_losses else 0.0

            uA = self.UVRFI_A[k] if use_supp else 0.0
            uB = self.UVRFI_B[k] if use_supp else 0.0

            m.addConstr(
                self.V_R[k] == V_R_prev + self.IN_VRFI[k] - self.R_H[k] - uA - uB - loss_R - self.SUP[k],
                name=f"bal_R_{k}"
            )
            m.addConstr(
                self.V_A[k] == V_A_prev + self.INA[k] - self.R_A[k] - loss_A,
                name=f"bal_A_{k}"
            )
            m.addConstr(
                self.V_B[k] == V_B_prev + self.INB[k] - self.R_B[k] - loss_B,
                name=f"bal_B_{k}"
            )

        # SSR (anual y tope mensual) o apagado
        if use_ssr:
            m.addConstr(gp.quicksum(self.R_H[t] for t in range(n)) == p['consumo_humano_anual'], name="humano_anual")
        for k in range(n):
            V_R_prev = self.V_R[k-1] if k>0 else p['V_R_inicial']
            if use_ssr:
                m.addConstr(self.R_H[k] <= V_R_prev, name=f"humano_mensual_top_{k}")
            else:
                m.addConstr(self.R_H[k] == 0.0,      name=f"humano_off_{k}")

        # FE: PWL en stage 4, constante 1.0 en stages 1-3
        if use_fe_pwl:
            # septiembre: índice 5 si abril=0
            m.addConstr(self.V_sep_deshielo == self.V_R[5] + p['pronostico_deshielo_promedio'], name="def_Vsep")
            # A: 0.75 hasta 740 Hm³; 1.0 desde 1200 Hm³; lineal entre medio
            xA = [0.0, 740e6, 1200e6, 1e10]
            yA = [0.75, 0.75, 1.0,    1.0]
            m.addGenConstrPWL(self.V_sep_deshielo, self.FE_A, xA, yA, name="FEA_pwl")
            # B: 0.50 hasta 1000 Hm³; 1.0 desde 1100 Hm³
            xB = [0.0, 1000e6, 1100e6, 1e10]
            yB = [0.50, 0.50, 1.0,     1.0]
            m.addGenConstrPWL(self.V_sep_deshielo, self.FE_B, xB, yB, name="FEB_pwl")
        else:
            m.addConstr(self.FE_A == 1.0, name="FEA_const")
            m.addConstr(self.FE_B == 1.0, name="FEB_const")

        # Servicio riego (si hay entregas)
        temporada = set(self.p['temporada_riego'])
        for k in range(n):
            if k in temporada and use_deliv:
                m.addConstr(self.R_A[k] + self.UVRFI_A[k] + self.d_A[k] >= self.FE_A * demandas_A[k], name=f"servA_{k}")
                m.addConstr(self.R_B[k] + self.UVRFI_B[k] + self.d_B[k] >= self.FE_B * demandas_B[k], name=f"servB_{k}")
                m.addConstr(self.R_A[k] <= demandas_A[k], name=f"cap_dem_A_{k}")
                m.addConstr(self.R_B[k] <= demandas_B[k], name=f"cap_dem_B_{k}")

            # disponibilidad (siempre útil)
            V_A_prev = self.V_A[k-1] if k>0 else p['V_A_inicial']
            V_B_prev = self.V_B[k-1] if k>0 else p['V_B_inicial']
            m.addConstr(self.R_A[k] <= V_A_prev + self.INA[k], name=f"disp_A_{k}")
            m.addConstr(self.R_B[k] <= V_B_prev + self.INB[k], name=f"disp_B_{k}")

        # turbinado
        for k in range(n):
            seg = p['segundos_mes'][k]
            if use_turbine:
                m.addConstr(self.Q_turb[k] * seg == self.UPREF[k] + self.R_H[k] + self.R_A[k] + self.R_B[k],
                            name=f"qturb_{k}")
            else:
                m.addConstr(self.Q_turb[k] == 0.0, name=f"qturb_off_{k}")

    # -------------------------------
    # objetivo
    # -------------------------------
    def set_objective(self) -> None:
        if self.stage == 0:
            self.model.setObjective(gp.quicksum(self.EB[k] for k in range(len(self.EB))), GRB.MINIMIZE)
        else:
            self.model.setObjective(gp.quicksum(self.d_A[k] + self.d_B[k] for k in range(len(self.d_A))), GRB.MINIMIZE)

    # -------------------------------
    # solve & solución
    # -------------------------------
    def solve(self,
              Q_afluente: List[float],
              Q_PD: List[float],
              demandas_A: List[float],
              demandas_B: List[float]) -> Dict[str, Any]:
        try:
            n = len(Q_afluente)
            self.setup_variables(n)
            self.setup_constraints(Q_afluente, Q_PD, demandas_A, demandas_B)
            self.set_objective()

            # Parámetros Gurobi
            self.model.setParam('OutputFlag', 1)
            if 'TimeLimit' in self.p:
                self.model.setParam('TimeLimit', self.p['TimeLimit'])

            self.model.optimize()
            if self.model.status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
                return None
            return self.get_solution()
        except Exception as e:
            print(f"Error al resolver: {e}")
            return None

    def get_solution(self) -> Dict[str, Any]:
        n = len(self.V_R)
        seg = self.p['segundos_mes']

        sol = {
            # stocks
            'volumenes_R': [self.V_R[k].X for k in range(n)],
            'volumenes_A': [self.V_A[k].X for k in range(n)],
            'volumenes_B': [self.V_B[k].X for k in range(n)],
            # entregas y SSR
            'entregas_A':  [self.R_A[k].X for k in range(n)],
            'entregas_B':  [self.R_B[k].X for k in range(n)],
            'entregas_H':  [self.R_H[k].X for k in range(n)],
            # déficits
            'deficits_A':  [self.d_A[k].X for k in range(n)],
            'deficits_B':  [self.d_B[k].X for k in range(n)],
            # flujos toma / llenados
            'UPREF':       [self.UPREF[k].X for k in range(n)],
            'INA':         [self.INA[k].X for k in range(n)],
            'INB':         [self.INB[k].X for k in range(n)],
            'IN_VRFI':     [self.IN_VRFI[k].X for k in range(n)],
            'SUP':         [self.SUP[k].X for k in range(n)],
            'EB':          [self.EB[k].X for k in range(n)],  # rebalse total a río
            # turbinado / FE
            'Q_turb':      [self.Q_turb[k].X for k in range(n)],
            'FE_A':        self.FE_A.X,
            'FE_B':        self.FE_B.X,
            'V_sep_deshielo': self.V_sep_deshielo.X,
            # objetivo y status
            'objetivo':    self.model.objVal,
            'status':      self.model.status,
        }

        # Energía (MWh)
        energia = 0.0
        for k in range(n):
            energia += (self.p['eta'] * self.Q_turb[k].X * seg[k]) / 3_600_000.0
        sol['energia_total'] = energia

        # (Stage 0) valores de río/almacenable útiles para debug
        if self.stage == 0:
            sol['Qpref'] = [self.Qpref[k].X for k in range(n)]
            sol['Qdis']  = [self.Qdis[k].X  for k in range(n)]
            sol['Qalm']  = [self.Qalm[k].X  for k in range(n)]

        return sol
