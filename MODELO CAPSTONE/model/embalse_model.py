# model/embalse_model.py
import gurobipy as gp
from gurobipy import GRB
import numpy as np

class EmbalseModel:
    def __init__(self, params):
        self.params = params
        self.model = gp.Model("Embalse_Nueva_Punilla")
        
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
        
        # DÉFICITS - Variables clave para la función objetivo
        self.d_A = self.model.addVars(n_meses, lb=0, name="d_A")
        self.d_B = self.model.addVars(n_meses, lb=0, name="d_B")
        
        # Caudal turbinado
        self.Q_turb = self.model.addVars(n_meses, lb=0, name="Q_turb")
        
        print("✅ Variables creadas correctamente")
        
    def setup_constraints(self, Q_afluente, Q_PD, demandas_A, demandas_B):
        """Configurar restricciones del modelo"""
        n_meses = len(Q_afluente)
        print("🔧 Configurando restricciones...")
        
        # 1. Condiciones iniciales
        self.model.addConstr(self.V_R[0] == self.params['V_R_inicial'], "init_R")
        self.model.addConstr(self.V_A[0] == self.params['V_A_inicial'], "init_A")
        self.model.addConstr(self.V_B[0] == self.params['V_B_inicial'], "init_B")
        
        # 2. Balances hídricos mensuales
        for m in range(n_meses):
            if m > 0:
                V_R_prev = self.V_R[m-1]
                V_A_prev = self.V_A[m-1]
                V_B_prev = self.V_B[m-1]
            else:
                V_R_prev = self.params['V_R_inicial']
                V_A_prev = self.params['V_A_inicial']
                V_B_prev = self.params['V_B_inicial']
            
            # Convertir caudal a volumen (m³/s * s = m³)
            segundos = self.params['segundos_mes'][m]
            volumen_entrante = max(0, Q_afluente[m] - Q_PD[m]) * segundos
            
            # Distribución simplificada
            entrada_R = volumen_entrante * 0.4
            entrada_A = volumen_entrante * 0.42
            entrada_B = volumen_entrante * 0.18
            
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
        
        # 3. Consumo humano anual
        consumo_total = sum(self.R_H[m] for m in range(n_meses))
        self.model.addConstr(consumo_total >= self.params['consumo_humano_anual'], "consumo_humano")
        
        # 4. RESTRICCIONES DE DÉFICIT - CLAVE PARA LA FUNCIÓN OBJETIVO
        temporada_riego = self.params['temporada_riego']
        FE_A = 0.85  # Factor de entrega A
        FE_B = 0.85  # Factor de entrega B
        
        for m in temporada_riego:
            if m < n_meses:  # Asegurar que el índice esté en rango
                # La entrega más el déficit debe ser al menos la demanda mínima
                self.model.addConstr(
                    self.R_A[m] + self.d_A[m] >= FE_A * demandas_A[m],
                    f"deficit_A_{m}"
                )
                self.model.addConstr(
                    self.R_B[m] + self.d_B[m] >= FE_B * demandas_B[m],
                    f"deficit_B_{m}"
                )
        
        # 5. Relación caudal turbinado
        for m in range(n_meses):
            total_entregas = self.R_H[m] + self.R_A[m] + self.R_B[m]
            self.model.addConstr(
                self.Q_turb[m] * self.params['segundos_mes'][m] == total_entregas,
                f"turbinado_{m}"
            )
        
        print("✅ Restricciones configuradas correctamente")
    
    def set_objective(self):
        """FUNCIÓN OBJETIVO: min ∑(d_A[m] + d_B[m]) para todos los meses m"""
        print("🎯 Configurando función objetivo: min ∑(d_A + d_B)")
        
        # Sumar todos los déficits de tipo A y tipo B
        total_deficit = sum(self.d_A[m] + self.d_B[m] for m in range(len(self.d_A)))
        
        # Minimizar la suma de déficits
        self.model.setObjective(total_deficit, GRB.MINIMIZE)
        
        print("✅ Función objetivo configurada")
    
    def solve(self, Q_afluente, Q_PD, demandas_A, demandas_B):
        """Resolver el modelo"""
        n_meses = len(Q_afluente)
        
        try:
            print("\n=== INICIANDO RESOLUCIÓN DEL MODELO ===")
            self.setup_variables(n_meses)
            self.setup_constraints(Q_afluente, Q_PD, demandas_A, demandas_B)
            self.set_objective()
            
            # Configurar parámetros
            self.model.setParam('OutputFlag', 1)
            self.model.setParam('TimeLimit', 300)
            
            print("🚀 Optimizando...")
            self.model.optimize()
            
            if self.model.status == GRB.OPTIMAL:
                print("✅ SOLUCIÓN ÓPTIMA ENCONTRADA")
                return self.get_solution()
            else:
                print(f"❌ No se encontró solución óptima. Status: {self.model.status}")
                return None
                
        except Exception as e:
            print(f"❌ Error durante la resolución: {e}")
            return None
    
    def get_solution(self):
        """Extraer solución del modelo"""
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
            'status': self.model.status
        }
        
        # Calcular energía generada
        energia_total = 0
        for m in range(n_meses):
            energia_mes = (self.params['eta'] * self.Q_turb[m].X * 
                          self.params['segundos_mes'][m] / 3600000)  # MWh
            energia_total += energia_mes
        
        solution['energia_total'] = energia_total
        
        return solution