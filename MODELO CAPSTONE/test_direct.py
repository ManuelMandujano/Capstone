# test_direct.py
import numpy as np
from utils.data_loader import DataLoader

def main():
    print("=== PRUEBA DIRECTA DEL MODELO ===")
    
    # 1. Cargar datos primero
    print("1. Cargando datos...")
    data_loader = DataLoader('data/caudales.xlsx')
    scenarios = data_loader.get_historical_scenarios()
    
    if not scenarios:
        print("❌ Error cargando datos")
        return
    
    test_scenario = scenarios[0]
    print(f"✅ Año: {test_scenario['año']}")
    
    # 2. Parámetros básicos
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
    
    # 3. Importar directamente desde el archivo
    print("2. Importando modelo...")
    try:
        # Importación directa sin pasar por __init__.py
        import sys
        sys.path.append('.')  # Agregar directorio actual al path
        from model.embalse_model import EmbalseModel
        print("✅ Modelo importado correctamente")
    except Exception as e:
        print(f"❌ Error importando modelo: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Datos de prueba simplificados
    Q_afluente = test_scenario['Q_nuble']
    Q_PD = [8.0] * 12
    demandas_A = [1000000] * 12  # Valores pequeños para prueba
    demandas_B = [500000] * 12
    
    # 5. Crear y resolver modelo
    print("3. Creando modelo...")
    try:
        modelo = EmbalseModel(params)
        print("✅ Modelo creado correctamente")
    except Exception as e:
        print(f"❌ Error creando modelo: {e}")
        return
    
    print("4. Resolviendo modelo...")
    solucion = modelo.solve(Q_afluente, Q_PD, demandas_A, demandas_B)
    
    if solucion:
        print("\n🎉 MODELO RESUELTO EXITOSAMENTE!")
        print(f"📊 FUNCIÓN OBJETIVO (DÉFICIT TOTAL): {solucion['objetivo']:,.0f} m³")
        print(f"⚡ ENERGÍA GENERADA: {solucion['energia_total']:,.0f} MWh")
        
        # Verificar función objetivo
        deficit_A_total = sum(solucion['deficits_A'])
        deficit_B_total = sum(solucion['deficits_B'])
        suma_verificada = deficit_A_total + deficit_B_total
        
        print(f"📉 DÉFICIT A: {deficit_A_total:,.0f} m³")
        print(f"📉 DÉFICIT B: {deficit_B_total:,.0f} m³")
        print(f"✅ SUMA VERIFICADA: {suma_verificada:,.0f} m³ = {solucion['objetivo']:,.0f} m³")
        
        if abs(suma_verificada - solucion['objetivo']) < 1:
            print("🎯 FUNCIÓN OBJETIVO CORRECTA: min ∑(d_A + d_B)")
        else:
            print("❌ ERROR EN FUNCIÓN OBJETIVO")
            
    else:
        print("❌ No se pudo resolver el modelo")

if __name__ == "__main__":
    main()