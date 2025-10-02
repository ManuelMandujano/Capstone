# main.py
import yaml
import json
import numpy as np
from utils.data_loader import DataLoader
from model.embalse_model import EmbalseModel
from model.montecarlo_simulator import MonteCarloSimulator

def main():
    # Cargar configuración
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        params = config[ 'parametros_embalse']
        print("✅ Configuración cargada correctamente")
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return

    # Cargar datos de caudales
    print("\n📁 Cargando datos de caudales...")
    data_loader = DataLoader('data/caudales.xlsx')
    historical_scenarios = data_loader.get_historical_scenarios()
    
    if not historical_scenarios:
        print("❌ No se pudieron cargar escenarios históricos. Usando datos de ejemplo.")
        # Crear datos de ejemplo para continuar
        historical_scenarios = [{
            'año': '1990/1991',
            'Q_nuble': np.array([50.0, 45.0, 40.0, 35.0, 30.0, 25.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]),
            'Q_hoya1': np.array([10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]),
            'Q_hoya2': np.array([8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]),
            'Q_hoya3': np.array([8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        }]
    
    average_scenario = data_loader.get_average_scenario()
    dry_year_scenario = data_loader.get_dry_year_scenario()
    wet_year_scenario = data_loader.get_wet_year_scenario()

    print(f"✅ Datos procesados: {len(historical_scenarios)} años históricos")

    # Demandas de ejemplo (deben calibrarse con datos reales)
    demandas_A = [15000000, 15000000, 18000000, 22000000, 25000000, 28000000, 
                  28000000, 26000000, 23000000, 20000000, 18000000, 16000000]
    demandas_B = [6000000, 6000000, 7000000, 9000000, 10000000, 11000000, 
                  11000000, 10000000, 9000000, 8000000, 7000000, 6000000]
    
    print("\n=== MODELO EMBALSE NUEVA PUNILLA - MINIMIZACIÓN DÉFICITS ===")
    
    # 1. Modelo con año promedio
    print("\n1. 📈 EJECUTANDO MODELO CON AÑO PROMEDIO...")
    try:
        modelo_promedio = EmbalseModel(params)
        solucion_promedio = modelo_promedio.solve(
            average_scenario['Q_nuble'],
            [8.0] * 12,  # Q_PD fijo
            demandas_A,
            demandas_B
        )
        
        if solucion_promedio:
            print(f"✅ Déficit total: {solucion_promedio['objetivo']:,.0f} m³")
            print(f"✅ Energía generada: {solucion_promedio['energia_total']:,.0f} MWh")
            print(f"✅ Déficit A: {sum(solucion_promedio['deficits_A']):,.0f} m³")
            print(f"✅ Déficit B: {sum(solucion_promedio['deficits_B']):,.0f} m³")
        else:
            print("❌ No se pudo resolver el modelo con año promedio")
    except Exception as e:
        print(f"❌ Error en modelo promedio: {e}")

    # 2. Modelo con año húmedo
    print("\n2. 🌊 EJECUTANDO MODELO CON AÑO HÚMEDO...")
    try:
        modelo_humedo = EmbalseModel(params)
        solucion_humedo = modelo_humedo.solve(
            wet_year_scenario['Q_nuble'],
            [8.0] * 12,
            demandas_A,
            demandas_B
        )
        
        if solucion_humedo:
            print(f"✅ Déficit total: {solucion_humedo['objetivo']:,.0f} m³")
            print(f"✅ Energía generada: {solucion_humedo['energia_total']:,.0f} MWh")
        else:
            print("❌ No se pudo resolver el modelo con año húmedo")
    except Exception as e:
        print(f"❌ Error en modelo húmedo: {e}")

    # 3. Modelo con año seco
    print("\n3. 🏜️ EJECUTANDO MODELO CON AÑO SECO...")
    try:
        modelo_seco = EmbalseModel(params)
        solucion_seco = modelo_seco.solve(
            dry_year_scenario['Q_nuble'],
            [8.0] * 12,
            demandas_A,
            demandas_B
        )
        
        if solucion_seco:
            print(f"✅ Déficit total: {solucion_seco['objetivo']:,.0f} m³")
            print(f"✅ Energía generada: {solucion_seco['energia_total']:,.0f} MWh")
        else:
            print("❌ No se pudo resolver el modelo con año seco")
    except Exception as e:
        print(f"❌ Error en modelo seco: {e}")

    # 4. Simulación Monte Carlo (solo si hay suficientes datos)
    if len(historical_scenarios) >= 10:
        print("\n4. 🎲 EJECUTANDO SIMULACIÓN MONTE CARLO...")
        try:
            n_simulaciones = min(config['montecarlo']['n_simulaciones'], 50)  # Limitar para prueba
            simulator = MonteCarloSimulator(params, n_simulations=n_simulaciones)
            resultados_mc = simulator.run_simulation(data_loader)
            
            if resultados_mc:
                print("\n=== RESULTADOS MONTE CARLO ===")
                print(f"✅ Déficit promedio: {resultados_mc['estadisticas_deficits']['deficit_total_promedio']:,.0f} m³")
                print(f"✅ Confiabilidad sin déficit: {resultados_mc['estadisticas_deficits']['confiabilidad_sin_deficit']:.1%}")
                print(f"✅ Energía promedio: {resultados_mc['estadisticas_energia']['energia_promedio']:,.0f} MWh")
                print(f"✅ Volumen final promedio: {resultados_mc['estadisticas_volumenes']['volumen_final_promedio']:,.0f} m³")
            else:
                print("❌ No se pudieron obtener resultados de Monte Carlo")
        except Exception as e:
            print(f"❌ Error en simulación Monte Carlo: {e}")
    else:
        print("\n4. ⚠️ OMITIENDO MONTE CARLO: Se necesitan más datos históricos")

    # Guardar resultados
    try:
        import os
        os.makedirs('data/resultados', exist_ok=True)
        
        if solucion_promedio:
            with open('data/resultados/solucion_promedio.json', 'w') as f:
                json.dump(solucion_promedio, f, indent=2, default=convert_numpy)
        
        print("\n✅ ANÁLISIS COMPLETADO")
        print("📊 Resultados guardados en: /data/resultados/")
        
    except Exception as e:
        print(f"❌ Error guardando resultados: {e}")

def convert_numpy(obj):
    """Convertir numpy types a Python native types para JSON"""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_numpy(value) for key, value in obj.items()}
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

if __name__ == "__main__":
    main()