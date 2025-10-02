# main.py - VERSIÓN FINAL
import yaml
import json
import numpy as np
from utils.data_loader import DataLoader
from model.embalse_model_advanced import EmbalseModelAdvanced

def main():
    print("=== MODELO EMBALSE NUEVA PUNILLA - VERSIÓN FINAL ===")
    
    # Cargar configuración
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        params = config['parametros_embalse']
        print("✅ Configuración cargada")
    except:
        # Configuración por defecto
        params = {
            'C_R': 175000000,
            'C_A': 260000000,  
            'C_B': 105000000,
            'V_R_inicial': 50000000,
            'V_A_inicial': 50000000,
            'V_B_inicial': 20000000,
            'consumo_humano_anual': 3900000,
            'eta': 0.85,
            'pronostico_deshielo_promedio': 200000000,
            'perdidas_mensuales': [1000000] * 12,
            'temporada_riego': [5, 6, 7, 8, 9, 10, 11],
            'segundos_mes': [2678400, 2592000, 2678400, 2592000, 2678400, 2592000, 
                            2678400, 2592000, 2678400, 2592000, 2678400, 2592000]
        }
    
    # Cargar datos
    print("📁 Cargando datos históricos...")
    data_loader = DataLoader('data/caudales.xlsx')
    scenarios = data_loader.get_historical_scenarios()
    
    if not scenarios:
        print("❌ Error cargando datos")
        return
    
    print(f"✅ {len(scenarios)} años históricos cargados")
    
    # Escenarios de prueba
    avg_scenario = data_loader.get_average_scenario()
    dry_scenario = data_loader.get_dry_year_scenario()
    wet_scenario = data_loader.get_wet_year_scenario()
    
    # Demandas realistas
    demandas_A = [15000000, 15000000, 20000000, 25000000, 30000000, 35000000, 
                  35000000, 30000000, 25000000, 20000000, 15000000, 15000000]
    demandas_B = [6000000, 6000000, 8000000, 10000000, 12000000, 14000000, 
                  14000000, 12000000, 10000000, 8000000, 6000000, 6000000]
    
    Q_PD = [8.0] * 12
    
    # Probar diferentes escenarios
    escenarios = [
        ("PROMEDIO", avg_scenario['Q_nuble']),
        ("AÑO SECO", dry_scenario['Q_nuble']),
        ("AÑO HÚMEDO", wet_scenario['Q_nuble'])
    ]
    
    resultados = {}
    
    for nombre, Q_afluente in escenarios:
        print(f"\n=== EJECUTANDO ESCENARIO: {nombre} ===")
        print(f"📊 Caudal promedio: {np.mean(Q_afluente):.2f} m³/s")
        
        modelo = EmbalseModelAdvanced(params)
        solucion = modelo.solve(Q_afluente, Q_PD, demandas_A, demandas_B)
        
        if solucion:
            resultados[nombre] = solucion
            print(f"✅ {nombre}: Déficit = {solucion['objetivo']:,.0f} m³")
        else:
            print(f"❌ {nombre}: No se pudo resolver")
    
    # Resumen final
    print("\n" + "="*50)
    print("📊 RESUMEN FINAL DE TODOS LOS ESCENARIOS")
    print("="*50)
    
    for nombre, solucion in resultados.items():
        print(f"\n{nombre}:")
        print(f"  Déficit total: {solucion['objetivo']:,.0f} m³")
        print(f"  Energía: {solucion['energia_total']:,.0f} MWh")
        print(f"  FE_A: {solucion['FE_A']:.3f}, FE_B: {solucion['FE_B']:.3f}")
        print(f"  V_sep-deshielo: {solucion['V_sep_deshielo']/1e6:.1f} Hm³")
    
    # Guardar todos los resultados
    import os
    os.makedirs('data/resultados', exist_ok=True)
    with open('data/resultados/resumen_final.json', 'w') as f:
        json.dump(resultados, f, indent=2, default=convert_numpy)
    
    print(f"\n💾 Todos los resultados guardados en: data/resultados/")

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