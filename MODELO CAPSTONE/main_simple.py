# main_simple.py
import yaml
import json
import numpy as np
from utils.data_loader import DataLoader
from model.embalse_model import EmbalseModel

def main_simple():
    """Versión simplificada para pruebas"""
    print("=== PRUEBA SIMPLIFICADA DEL MODELO ===")
    
    # Cargar configuración básica
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
    print("Cargando datos...")
    data_loader = DataLoader('data/caudales.xlsx')
    historical_scenarios = data_loader.get_historical_scenarios()
    
    if not historical_scenarios:
        print("Usando datos de ejemplo...")
        # Datos de ejemplo
        Q_afluente = [50.0, 45.0, 40.0, 35.0, 30.0, 25.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0]
    else:
        # Usar el primer escenario histórico
        Q_afluente = historical_scenarios[0]['Q_nuble']
        print(f"Usando datos del año: {historical_scenarios[0]['año']}")
    
    # Demandas de ejemplo
    demandas_A = [15000000, 15000000, 18000000, 22000000, 25000000, 28000000, 
                  28000000, 26000000, 23000000, 20000000, 18000000, 16000000]
    demandas_B = [6000000, 6000000, 7000000, 9000000, 10000000, 11000000, 
                  11000000, 10000000, 9000000, 8000000, 7000000, 6000000]
    
    Q_PD = [8.0] * 12  # Caudal preferente constante
    
    print("Ejecutando modelo...")
    modelo = EmbalseModel(params)
    solucion = modelo.solve(Q_afluente, Q_PD, demandas_A, demandas_B)
    
    if solucion:
        print("\n✅ MODELO RESUELTO EXITOSAMENTE")
        print(f"Déficit total: {solucion['objetivo']:,.0f} m³")
        print(f"Energía generada: {solucion['energia_total']:,.0f} MWh")
        print(f"Déficit A: {sum(solucion['deficits_A']):,.0f} m³")
        print(f"Déficit B: {sum(solucion['deficits_B']):,.0f} m³")
        
        # Guardar resultados
        import os
        os.makedirs('data/resultados', exist_ok=True)
        with open('data/resultados/solucion_simple.json', 'w') as f:
            json.dump(solucion, f, indent=2, default=convert_numpy)
        
        print("Resultados guardados en: data/resultados/solucion_simple.json")
        
        # Intentar graficar
        try:
            from utils.visualizacion import Visualizador
            viz = Visualizador()
            viz.plot_resultados_mensuales(solucion)
        except Exception as e:
            print(f"Nota: No se pudo generar gráfico: {e}")
            
    else:
        print("❌ No se pudo resolver el modelo")

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
    main_simple()