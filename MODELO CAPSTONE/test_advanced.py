# test_advanced.py
import numpy as np
from utils.data_loader import DataLoader
from model.embalse_model_advanced import EmbalseModelAdvanced

def main():
    print("=== PRUEBA DEL MODELO AVANZADO ===")
    
    # Cargar datos
    data_loader = DataLoader('data/caudales.xlsx')
    scenarios = data_loader.get_historical_scenarios()
    test_scenario = scenarios[0]
    
    print(f"📊 Año: {test_scenario['año']}")
    
    # Parámetros mejorados
    params = {
        'C_R': 175000000,
        'C_A': 260000000,  
        'C_B': 105000000,
        'V_R_inicial': 50000000,
        'V_A_inicial': 50000000,
        'V_B_inicial': 20000000,
        'consumo_humano_anual': 3900000,
        'eta': 0.85,
        'pronostico_deshielo_promedio': 200000000,  # 200 Hm³
        'perdidas_mensuales': [1000000] * 12,
        'temporada_riego': [5, 6, 7, 8, 9, 10, 11],  # OCT-ABR
        'segundos_mes': [2678400, 2592000, 2678400, 2592000, 2678400, 2592000, 
                        2678400, 2592000, 2678400, 2592000, 2678400, 2592000]
    }
    
    # Demandas realistas según capacidad del embalse
    demandas_A = [15000000, 15000000, 20000000, 25000000, 30000000, 35000000, 
                  35000000, 30000000, 25000000, 20000000, 15000000, 15000000]
    demandas_B = [6000000, 6000000, 8000000, 10000000, 12000000, 14000000, 
                  14000000, 12000000, 10000000, 8000000, 6000000, 6000000]
    
    Q_afluente = test_scenario['Q_nuble']
    Q_PD = [8.0] * 12
    
    print(f"💧 Demandas anuales:")
    print(f"   - Tipo A: {sum(demandas_A)/1e6:.1f} Hm³")
    print(f"   - Tipo B: {sum(demandas_B)/1e6:.1f} Hm³")
    
    # Crear y resolver modelo avanzado
    modelo = EmbalseModelAdvanced(params)
    solucion = modelo.solve(Q_afluente, Q_PD, demandas_A, demandas_B)
    
    if solucion:
        print(f"\n🎯 RESULTADOS MODELO AVANZADO:")
        print(f"📊 Déficit total: {solucion['objetivo']:,.0f} m³")
        print(f"⚡ Energía generada: {solucion['energia_total']:,.0f} MWh")
        print(f"🎯 Factores de entrega:")
        print(f"   - FE_A: {solucion['FE_A']:.3f}")
        print(f"   - FE_B: {solucion['FE_B']:.3f}")
        print(f"💧 V_sep-deshielo: {solucion['V_sep_deshielo']/1e6:.1f} Hm³")
        
        # Análisis detallado
        deficit_A_total = sum(solucion['deficits_A'])
        deficit_B_total = sum(solucion['deficits_B'])
        
        print(f"📉 Déficit A: {deficit_A_total:,.0f} m³")
        print(f"📉 Déficit B: {deficit_B_total:,.0f} m³")
        
        # Volúmenes finales
        V_final_total = solucion['volumenes_R'][-1] + solucion['volumenes_A'][-1] + solucion['volumenes_B'][-1]
        print(f"💧 Volumen final total: {V_final_total/1e6:.1f} Hm³")
        
        # Guardar resultados
        import json
        import os
        os.makedirs('data/resultados', exist_ok=True)
        with open('data/resultados/solucion_avanzada.json', 'w') as f:
            json.dump(solucion, f, indent=2, default=convert_numpy)
        print("💾 Resultados guardados en: data/resultados/solucion_avanzada.json")
        
    else:
        print("❌ No se pudo resolver el modelo avanzado")

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