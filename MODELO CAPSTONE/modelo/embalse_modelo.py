# model/embalse_model.py
import gurobipy as gp
from gurobipy import GRB
import numpy as np

class EmbalseModel:
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Embalse_Nueva_Punilla")
        
    def setup_variables(self, n_meses=12):
        """Configurar variables según el modelo actualizado"""
        # Volúmenes almacenados
        self.V_R = self.model.addVars(n_meses, lb=0, name="V_R")  # Reserva fija
        self.V_A = self.model.addVars(n_meses, lb=0, name="V_A")  # Acciones A
        self.V_B = self.model.addVars(n_meses, lb=0, name="V_B")  # Acciones B
        
        # Entregas
        self.R_H = self.model.addVars(n_meses, lb=0, name="R_H")  # Consumo humano
        self.R_A = self.model.addVars(n_meses, lb=0, name="R_A")  # Entrega A
        self.R_B = self.model.addVars(n_meses, lb=0, name="R_B")  # Entrega B
        
        # Déficits (nuevas variables según modelo actualizado)
        self.d_A = self.model.addVars(n_meses, lb=0, name="d_A")  # Déficit A
        self.d_B = self.model.addVars(n_meses, lb=0, name="d_B")  # Déficit B
        
        # Caudal turbinado
        self.Q_turb = self.model.addVars(n_meses, lb=0, name="Q_turb")
        
        # Variables auxiliares para lógica de llenado
        self.u_R = self.model.addVars(n_meses, vtype=GRB.BINARY, name="u_R")
        self.u_A = self.model.addVars(n_meses, vtype=GRB.BINARY, name="u_A")
        self.u_B = self.model.addVars(n_meses, vtype=GRB.BINARY, name="u_B")
    
    def calculate_factores_entrega(self, V_sep_deshielo):
        """Calcular factores de entrega según V_sep_deshielo (reglas oficiales)"""
        # Para Acciones Tipo A
        if V_sep_deshielo >= 1200:  # Hm³
            FE_A = 1.0
        elif V_sep_deshielo <= 740:  # Hm³
            FE_A = 0.75
        else:
            FE_A = 0.0005435 * V_sep_deshielo + 0.3478
        
        # Para Acciones Tipo B
        if V_sep_deshielo >= 1100:  # Hm³
            FE_B = 1.0
        elif V_sep_deshielo <= 1000:  # Hm³
            FE_B = 0.5
        else:
            FE_B = 0.00505 * V_sep_deshielo - 4.555
        
        return min(FE_A, 1.0), min(FE_B, 1.0)
    
    def setup_constraints(self, Q_afluente, Q_PD, demandas_A, demandas_B):
        """Configurar restricciones según el modelo actualizado"""
        n_meses = len(Q_afluente)
        
        # 1. Balance hídrico para cada volumen
        for m in range(n_meses):
            if m == 0:
                # Condiciones iniciales
                V_R_prev = self.params['V_R_inicial']
                V_A_prev = self.params['V_A_inicial']
                V_B_prev = self.params['V_B_inicial']
            else:
                V_R_prev = self.V_R[m-1]
                V_A_prev = self.V_A[m-1]
                V_B_prev = self.V_B[m-1]
            
            # Agua disponible para almacenamiento (convertir m³/s a volumen mensual)
            segundos_mes = self.params['segundos_mes'][m]
            Q_almacenable = max(0, Q_afluente[m] - Q_PD[m]) * segundos_mes
            
            # Lógica de llenado secuencial (simplificada)
            # Primero se llena V_R, luego V_A y V_B en proporción 71%/29%
            exceso_despues_R = Q_almacenable - max(0, self.params['C_R'] - V_R_prev)
            
            if exceso_despues_R > 0:
                # Distribuir exceso entre V_A y V_B
                entrada_A = exceso_despues_R * 0.71
                entrada_B = exceso_despues_R * 0.29
            else:
                entrada_A = 0
                entrada_B = 0
            
            # Balance con pérdidas distribuidas proporcionalmente
            perdidas_mes = self.params['perdidas_mensuales'][m]
            
            self.model.addConstr(
                self.V_R[m] == V_R_prev + min(Q_almacenable, self.params['C_R'] - V_R_prev) 
                - self.R_H[m] - perdidas_mes * (V_R_prev / (V_R_prev + V_A_prev + V_B_prev + 1e-6)),
                name=f"balance_R_{m}"
            )
            
            self.model.addConstr(
                self.V_A[m] == V_A_prev + entrada_A - self.R_A[m] 
                - perdidas_mes * (V_A_prev / (V_R_prev + V_A_prev + V_B_prev + 1e-6)),
                name=f"balance_A_{m}"
            )
            
            self.model.addConstr(
                self.V_B[m] == V_B_prev + entrada_B - self.R_B[m] 
                - perdidas_mes * (V_B_prev / (V_R_prev + V_A_prev + V_B_prev + 1e-6)),
                name=f"balance_B_{m}"
            )
        
        # 2. Restricciones de capacidad
        for m in range(n_meses):
            self.model.addConstr(self.V_R[m] <= self.params['C_R'], name=f"cap_R_{m}")
            self.model.addConstr(self.V_A[m] <= self.params['C_A'], name=f"cap_A_{m}")
            self.model.addConstr(self.V_B[m] <= self.params['C_B'], name=f"cap_B_{m}")
        
        # 3. Consumo humano anual
        self.model.addConstr(
            sum(self.R_H[m] for m in range(n_meses)) >= self.params['consumo_humano_anual'],
            name="consumo_humano_total"
        )
        
        # 4. Restricciones de entrega mínima con déficits
        temporada_riego = self.params['temporada_riego']  # [5,6,7,8,9,10,11] = OCT-ABR
        
        # Calcular V_sep_deshielo para factores de entrega
        V_sep = self.V_R[4] + self.V_A[4] + self.V_B[4]  # SEPTIEMBRE (índice 4)
        pronostico_deshielo = self.params['pronostico_deshielo_promedio']  # Hm³
        V_sep_deshielo = V_sep + pronostico_deshielo
        
        FE_A, FE_B = self.calculate_factores_entrega(V_sep_deshielo)
        
        for m in temporada_riego:
            # R_A + d_A >= FE_A * demanda_A
            self.model.addConstr(
                self.R_A[m] + self.d_A[m] >= FE_A * demandas_A[m],
                name=f"min_entrega_A_{m}"
            )
            
            # R_B + d_B >= FE_B * demanda_B  
            self.model.addConstr(
                self.R_B[m] + self.d_B[m] >= FE_B * demandas_B[m],
                name=f"min_entrega_B_{m}"
            )
        
        # 5. Relación caudal turbinado - entregas
        for m in range(n_meses):
            self.model.addConstr(
                self.Q_turb[m] * self.params['segundos_mes'][m] == 
                self.R_H[m] + self.R_A[m] + self.R_B[m],
                name=f"turbinado_{m}"
            )
    
    def set_objective(self):
        """Función objetivo: MINIMIZAR suma de déficits (modelo actualizado)"""
        objetivo = sum(self.d_A[m] + self.d_B[m] for m in range(len(self.d_A)))
        self.model.setObjective(objetivo, GRB.MINIMIZE)
    
    def solve(self, Q_afluente, Q_PD, demandas_A, demandas_B):
        """Resolver el modelo actualizado"""
        n_meses = len(Q_afluente)
        self.setup_variables(n_meses)
        self.setup_constraints(Q_afluente, Q_PD, demandas_A, demandas_B)
        self.set_objective()
        
        # Configurar parámetros del solver
        self.model.setParam('OutputFlag', 1)
        self.model.setParam('TimeLimit', 300)  # 5 minutos
        
        self.model.optimize()
        
        if self.model.status == GRB.OPTIMAL:
            return self.get_solution()
        else:
            print(f"No se encontró solución óptima. Status: {self.model.status}")
            return None
    
    def get_solution(self):
        """Extraer solución completa"""
        n_meses = len(self.V_R)
        
        solution = {
            'volumenes_R': [self.V_R[m].X for m in range(n_meses)],
            'volumenes_A': [self.V_A[m].X for m in range(n_meses)],
            'volumenes_B': [self.V_B[m].X for m in range(n_meses)],
            'entregas_A': [self.R_A[m].X for m in range(n_meses)],
            'entregas_B': [self.R_B[m].X for m in range(n_meses)],
            'entregas_H': [self.R_H[m].X for m in range(n_meses)],
            'deficits_A': [self.d_A[m].X for m in range(n_meses)],
            'deficits_B': [self.d_B[m].X for m in range(n_meses)],
            'turbinado': [self.Q_turb[m].X for m in range(n_meses)],
            'objetivo': self.model.objVal,
            'energia_total': sum(
                self.params['eta'] * self.Q_turb[m].X * self.params['segundos_mes'][m] 
                for m in range(n_meses)
            ) / 3600000  # Convertir a MWh
        }
        return solution