# model/embalse_model_advanced.py
import gurobipy as gp
from gurobipy import GRB
import numpy as np

class EmbalseModelAdvanced:
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Embalse_Nueva_Punilla_Avanzado")
        
    def calculate_factores_entrega(self, V_sep_deshielo):
        """Calcular factores de entrega según V_sep-deshielo (reglas oficiales)"""
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
        
        return min(FE_A, 1.0), min(max(FE_B, 0.0), 1.0)  # Asegurar valores entre 0 y 1
    
    def setup_variables(self, n_meses=12):
        """Configurar variables de decisión"""
        print(f"🔧 Creando variables para {n_meses} meses...")
        
        # Volúmenes almacenados
        self.V_R = self.model.addVars(n_meses, lb=0, ub=self.params['C_R'], name="V_R")
        self.V_A = self.model.addVars(n_meses, lb=0, ub=self.params['C_A'], name="V_A") 
        self.V_B = self.model.addVars(n_meses, lb=0, ub=self.params['C_B'], name="V_B")
        
        # Entregas
        self.R_H = self.model.addVars(n_meses, lb=0, name="R_H")
        self.R_A = self.model.addVars(n_meses, lb=0, name="R_A")
        self.R_B = self.model.addVars(n_meses, lb=0, name="R_B")
        
        # DÉFICITS
        self.d_A = self.model.addVars(n_meses, lb=0, name="d_A")
        self.d_B = self.model.addVars(n_meses, lb=0, name="d_B")
        
        # Caudal turbinado
        self.Q_turb = self.model.addVars(n_meses, lb=0, name="Q_turb")
        
        # Variables para factores de entrega (septiembre)
        self.FE_A = self.model.addVar(lb=0, ub=1, name="FE_A")
        self.FE_B = self.model.addVar(lb=0, ub=1, name="FE_B")
        
        print("✅ Variables creadas correctamente")
        
    def setup_constraints_advanced(self, Q_afluente, Q_PD, demandas_A, demandas_B):
        """Configurar restricciones con factores de entrega dinámicos"""
        n_meses = len(Q_afluente)
        print("🔧 Configurando restricciones avanzadas...")
        
        # 1. Condiciones iniciales
        self.model.addConstr(self.V_R[0] == self.params['V_R_inicial'], "init_R")
        self.model.addConstr(self.V_A[0] == self.params['V_A_inicial'], "init_A")
        self.model.addConstr(self.V_B[0] == self.params['V_B_inicial'], "init_B")
        
        # 2. Calcular V_sep-deshielo (volumen en septiembre + pronóstico deshielo)
        # Septiembre es el mes 4 en nuestro calendario (MAY=0, JUN=1, JUL=2, AGO=3, SEP=4)
        V_sep = self.V_R[4] + self.V_A[4] + self.V_B[4]
        V_sep_deshielo = V_sep + self.params['pronostico_deshielo_promedio']
        
        # 3. Factores de entrega como variables (aproximación lineal)
        # Para FE_A
        self.model.addConstr(self.FE_A <= 1.0, "FE_A_max")
        self.model.addConstr(self.FE_A >= 0.75, "FE_A_min")
        
        # Para FE_B  
        self.model.addConstr(self.FE_B <= 1.0, "FE_B_max")
        self.model.addConstr(self.FE_B >= 0.5, "FE_B_min")
        
        # 4. Balances hídricos mensuales
        for m in range(n_meses):
            if m > 0:
                V_R_prev = self.V_R[m-1]
                V_A_prev = self.V_A[m-1]
                V_B_prev = self.V_B[m-1]
            else:
                V_R_prev = self.params['V_R_inicial']
                V_A_prev = self.params['V_A_inicial']
                V_B_prev = self.params['V_B_inicial']
            
            # Convertir caudal a volumen
            segundos = self.params['segundos_mes'][m]
            volumen_disponible = max(0, Q_afluente[m] - Q_PD[m]) * segundos
            
            # Distribución simplificada
            entrada_R = volumen_disponible * 0.4
            entrada_A = volumen_disponible * 0.42
            entrada_B = volumen_disponible * 0.18
            
            # Pérdidas proporcionales
            perdidas_totales = self.params['perdidas_mensuales'][m]
            perdidas_R = perdidas_totales * 0.4
            perdidas_A = perdidas_totales * 0.4
            perdidas_B = perdidas_totales * 0.2
            
            # Ecuaciones de balance
            self.model.addConstr(
                self.V_R[m] == V_R_prev + entrada_R - self.R_H[m] - perdidas_R,
                f"balance_R_{m}"
            )
            self.model.addConstr(
                self.V_A[m] == V_A_prev + entrada_A - self.R_A[m] - perdidas_A,
                f"balance_A_{m}"
            )
            self.model.addConstr(
                self.V_B[m] == V_B_prev + entrada_B - self.R_B[m] - perdidas_B,
                f"balance_B_{m}"
            )
        
        # 5. Consumo humano anual
        consumo_total = sum(self.R_H[m] for m in range(n_meses))
        self.model.addConstr(consumo_total >= self.params['consumo_humano_anual'], "consumo_humano")
        
        # 6. Restricciones de déficit con factores dinámicos
        temporada_riego = self.params['temporada_riego']
        
        for m in temporada_riego:
            if m < n_meses:
                self.model.addConstr(
                    self.R_A[m] + self.d_A[m] >= self.FE_A * demandas_A[m],
                    f"deficit_A_{m}"
                )
                self.model.addConstr(
                    self.R_B[m] + self.d_B[m] >= self.FE_B * demandas_B[m],
                    f"deficit_B_{m}"
                )
        
        # 7. Relación caudal turbinado
        for m in range(n_meses):
            total_entregas = self.R_H[m] + self.R_A[m] + self.R_B[m]
            self.model.addConstr(
                self.Q_turb[m] * self.params['segundos_mes'][m] == total_entregas,
                f"turbinado_{m}"
            )
        
        print("✅ Restricciones avanzadas configuradas")
    
    def set_objective(self):
        """FUNCIÓN OBJETIVO: min ∑(d_A[m] + d_B[m])"""
        print("🎯 Configurando función objetivo: min ∑(d_A + d_B)")
        
        total_deficit = sum(self.d_A[m] + self.d_B[m] for m in range(len(self.d_A)))
        self.model.setObjective(total_deficit, GRB.MINIMIZE)
        
        print("✅ Función objetivo configurada")
    
    def solve(self, Q_afluente, Q_PD, demandas_A, demandas_B):
        """Resolver el modelo avanzado"""
        n_meses = len(Q_afluente)
        
        try:
            print("\n=== INICIANDO RESOLUCIÓN AVANZADA ===")
            self.setup_variables(n_meses)
            self.setup_constraints_advanced(Q_afluente, Q_PD, demandas_A, demandas_B)
            self.set_objective()
            
            self.model.setParam('OutputFlag', 1)
            self.model.setParam('TimeLimit', 300)
            
            print("🚀 Optimizando...")
            self.model.optimize()
            
            if self.model.status == GRB.OPTIMAL:
                print("✅ SOLUCIÓN ÓPTIMA ENCONTRADA")
                return self.get_solution()
            else:
                print(f"❌ Status: {self.model.status}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_solution(self):
        """Extraer solución del modelo avanzado"""
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
            'FE_A': self.FE_A.X,
            'FE_B': self.FE_B.X,
            'objetivo': self.model.objVal,
            'status': self.model.status
        }
        
        # Calcular V_sep-deshielo real
        V_sep = solution['volumenes_R'][4] + solution['volumenes_A'][4] + solution['volumenes_B'][4]
        solution['V_sep_deshielo'] = V_sep + self.params['pronostico_deshielo_promedio']
        
        # Calcular energía
        energia_total = 0
        for m in range(n_meses):
            energia_mes = (self.params['eta'] * self.Q_turb[m].X * 
                          self.params['segundos_mes'][m] / 3600000)
            energia_total += energia_mes
        
        solution['energia_total'] = energia_total
        
        return solution