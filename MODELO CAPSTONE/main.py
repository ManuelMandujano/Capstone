# main.py
import yaml
import json
import pandas as pd
from utils.data_loader import DataLoader
from modelo.embalse_modelo import EmbalseModel
from modelo.montecarlo_simulacion import MonteCarloSimulator

def main():
    # Cargar configuración
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    params = config['parametros_embalse']
    
    # Cargar datos de caudales
    print("Cargando datos de caudales...")
    data_loader = DataLoader('data/caudales.xlsx')
    historical_scenarios = data_loader.get_historical_scenarios()
    average_scenario = data_loader.get_average_scenario()
    
    print(f"Cargados {len(historical_scenarios)} años históricos")
    
    # Demandas de ejemplo (deben calibrarse con datos reales)
    demandas_A = [15000000, 15000000, 18000000, 22000000, 25000000, 28000000, 
                  28000000, 26000000, 23000000, 20000000, 18000000, 16000000]
    demandas_B = [6000000, 6000000, 7000000, 9000000, 10000000, 11000000, 
                  11000000, 10000000, 9000000, 8000000, 7000000, 6000000]
    
    print("=== MODELO EMBALSE NUEVA PUNILLA - MINIMIZACIÓN DÉFICITS ===")
    
    # 1. Modelo con año promedio
    print("\n1. EJECUTANDO MODELO CON AÑO PROMEDIO...")
    modelo_promedio = EmbalseModel(params)
    
    solucion_promedio = modelo_promedio.solve(
        average_scenario['Q_nuble'],
        [8.0] * 12,  # Q_PD fijo
        demandas_A,
        demandas_B
    )
    
    if solucion_promedio:
        print(f"✓ Déficit total: {solucion_promedio['objetivo']:,.0f} m³")
        print(f"✓ Energía generada: {solucion_promedio['energia_total']:,.0f} MWh")
        print(f"✓ Déficit A: {sum(solucion_promedio['deficits_A']):,.0f} m³")
        print(f"✓ Déficit B: {sum(solucion_promedio['deficits_B']):,.0f} m³")
    
    # 2. Modelo con año histórico específico (1997/1998 - año húmedo)
    print("\n2. EJECUTANDO MODELO CON AÑO HÚMEDO (1997/1998)...")
    ano_humedo = historical_scenarios[8]  # 1997/1998
    modelo_humedo = EmbalseModel(params)
    
    solucion_humedo = modelo_humedo.solve(
        ano_humedo['Q_nuble'],
        [8.0] * 12,
        demandas_A,
        demandas_B
    )
    
    if solucion_humedo:
        print(f"✓ Déficit total: {solucion_humedo['objetivo']:,.0f} m³")
        print(f"✓ Energía generada: {solucion_humedo['energia_total']:,.0f} MWh")
    
    # 3. Simulación Monte Carlo
    print("\n3. EJECUTANDO SIMULACIÓN MONTE CARLO...")
    simulator = MonteCarloSimulator(params, n_simulations=config['montecarlo']['n_simulaciones'])
    resultados_mc = simulator.run_simulation(data_loader)
    
    if resultados_mc:
        print("\n=== RESULTADOS MONTE CARLO ===")
        print(f"✓ Déficit promedio: {resultados_mc['estadisticas_deficits']['deficit_total_promedio']:,.0f} m³")
        print(f"✓ Confiabilidad sin déficit: {resultados_mc['estadisticas_deficits']['confiabilidad_sin_deficit']:.1%}")
        print(f"✓ Energía promedio: {resultados_mc['estadisticas_energia']['energia_promedio']:,.0f} MWh")
        print(f"✓ Volumen final promedio: {resultados_mc['estadisticas_volumenes']['volumen_final_promedio']:,.0f} m³")
    
    # Guardar resultados
    with open('data/resultados/solucion_promedio.json', 'w') as f:
        json.dump(solucion_promedio, f, indent=2, default=convert_numpy)
    
    with open('data/resultados/resultados_montecarlo.json', 'w') as f:
        json.dump(resultados_mc, f, indent=2, default=convert_numpy)
    
    print("\n=== ANÁLISIS COMPLETADO ===")
    print("Resultados guardados en:/data/resultados/")

def convert_numpy(obj):
    """Convertir numpy types a Python native types para JSON"""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

if __name__ == "__main__":
    main()