# model/montecarlo_simulator.py
import numpy as np
import pandas as pd
from modelo.embalse_modelo import EmbalseModel

class MonteCarloSimulator:
    def __init__(self, params, n_simulations=1000):
        self.params = params
        self.n_simulations = n_simulations
        self.results = []
    
    def generate_scenarios(self, data_loader):
        """Generar escenarios basados en datos históricos"""
        historical_scenarios = data_loader.get_historical_scenarios()
        
        scenarios = []
        for _ in range(self.n_simulations):
            # Muestrear un año histórico aleatorio
            idx = np.random.randint(0, len(historical_scenarios))
            scenario_base = historical_scenarios[idx]
            
            # Agregar variabilidad aleatoria (±20%)
            variabilidad = np.random.normal(1.0, 0.1, 12)  # Media 1, desv 0.1
            variabilidad = np.clip(variabilidad, 0.8, 1.2)  # Limitar entre 0.8 y 1.2
            
            scenario = {
                'año': scenario_base['año'],
                'Q_afluente': scenario_base['Q_nuble'] * variabilidad,
                'Q_PD': np.full(12, 8.0),  # Caudal preferente fijo de 8 m³/s
                'demandas_A': self.generate_demandas_aleatorias(),
                'demandas_B': self.generate_demandas_aleatorias()
            }
            scenarios.append(scenario)
        
        return scenarios
    
    def generate_demandas_aleatorias(self):
        """Generar demandas de riego aleatorias con estacionalidad"""
        # Patrón estacional: más demanda en verano
        patron_estacional = [0.3, 0.3, 0.4, 0.6, 0.8, 1.0, 1.0, 0.9, 0.7, 0.5, 0.4, 0.3]
        demanda_base = 20000000  # 20 Hm³/mes máximo
        
        return [demanda_base * factor * np.random.uniform(0.9, 1.1) for factor in patron_estacional]
    
    def run_simulation(self, data_loader):
        """Ejecutar simulación Monte Carlo completa"""
        scenarios = self.generate_scenarios(data_loader)
        
        print(f"Iniciando simulación Monte Carlo con {len(scenarios)} escenarios...")
        
        for i, scenario in enumerate(scenarios):
            if (i + 1) % 10 == 0:
                print(f"Procesando escenario {i+1}/{len(scenarios)}")
            
            model = EmbalseModel(self.params)
            solution = model.solve(
                scenario['Q_afluente'],
                scenario['Q_PD'], 
                scenario['demandas_A'],
                scenario['demandas_B']
            )
            
            if solution:
                solution['scenario_id'] = i
                solution['año_hidrologico'] = scenario['año']
                solution['Q_afluente_promedio'] = np.mean(scenario['Q_afluente'])
                self.results.append(solution)
        
        return self.analyze_results()
    
    def analyze_results(self):
        """Analizar resultados de la simulación"""
        if not self.results:
            return None
        
        df = pd.DataFrame(self.results)
        
        analysis = {
            'estadisticas_deficits': {
                'deficit_A_promedio': df['deficits_A'].apply(lambda x: sum(x)).mean(),
                'deficit_B_promedio': df['deficits_B'].apply(lambda x: sum(x)).mean(),
                'deficit_total_promedio': df['objetivo'].mean(),
                'confiabilidad_sin_deficit': (df['objetivo'] == 0).mean()
            },
            'estadisticas_energia': {
                'energia_promedio': df['energia_total'].mean(),
                'energia_std': df['energia_total'].std(),
                'energia_min': df['energia_total'].min(),
                'energia_max': df['energia_total'].max()
            },
            'estadisticas_volumenes': {
                'volumen_final_promedio': df['volumenes_R'].apply(lambda x: x[-1]).mean() + 
                                         df['volumenes_A'].apply(lambda x: x[-1]).mean() + 
                                         df['volumenes_B'].apply(lambda x: x[-1]).mean()
            }
        }
        
        return analysis