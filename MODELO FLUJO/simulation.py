# monte_carlo_simulator.py
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from model.modelo_flujo_multi import EmbalseModelMulti
from utils.data_loader import DataLoader

# Configuración Monte Carlo - REDUCIDO PARA DEBUG
NUM_SIMULACIONES = 5  # Reducido para pruebas
DURACION_ANOS = 5     # Reducido para pruebas

# Años disponibles
anos = ['1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
        '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
        '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
        '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
        '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
        '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019']

def simular_escenario(anos_simulados):
    """Selecciona años aleatorios sin reemplazo"""
    copia_anos = anos.copy()
    lista_resultados = []
    for _ in range(anos_simulados):
        ano_seleccionado = np.random.choice(copia_anos)
        lista_resultados.append(str(ano_seleccionado))  # Asegurar string
        copia_anos.remove(ano_seleccionado)
    return lista_resultados

def simular_varias_veces(anos_simulados, num_simulaciones=NUM_SIMULACIONES):
    """Genera múltiples secuencias de años aleatorios"""
    resultados = []
    for _ in range(num_simulaciones):
        resultado = simular_escenario(anos_simulados)
        resultados.append(resultado)
    return resultados

def cargar_y_limpiar_datos():
    """Carga y limpia todos los datos de caudales"""
    ruta = ROOT / "data" / "caudales.xlsx"
    print(f"📁 Cargando datos de: {ruta}")
    
    try:
        xls = pd.ExcelFile(ruta)
        
        # Cargar las diferentes hojas
        nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4, nrows=31)
        hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=38, nrows=31)
        hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=74, nrows=31)
        hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=111, nrows=31)
        
        # Limpiar datos - asegurar que AÑO sea string y limpiar valores
        for df in [nuble, hoya1, hoya2, hoya3]:
            df['AÑO'] = df['AÑO'].astype(str).str.strip()
            # Limpiar columnas numéricas
            columnas_numericas = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 
                                 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL']
            for col in columnas_numericas:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        print("✅ Datos cargados y limpiados correctamente")
        return nuble, hoya1, hoya2, hoya3
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return None, None, None, None

def obtener_caudales_anuales(ano, nuble_df):
    """Obtiene los caudales mensuales para un año específico"""
    try:
        # Buscar el año en el DataFrame
        fila = nuble_df[nuble_df['AÑO'] == str(ano)]
        
        if not fila.empty:
            # Extraer caudales mensuales en orden ABR-MAR
            caudales = fila.iloc[0][['ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 
                                   'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR']].values
            
            # Verificar que no haya valores None o NaN
            if np.any(pd.isna(caudales)):
                print(f"⚠️ Valores NaN encontrados para año {ano}, usando ceros")
                caudales = np.zeros(12)
            
            return caudales.tolist()
        else:
            print(f"⚠️ Año {ano} no encontrado, usando caudales promedio")
            # Usar promedio de todos los años como fallback
            columnas = ['ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR']
            promedios = [nuble_df[col].mean() for col in columnas]
            return promedios
            
    except Exception as e:
        print(f"❌ Error obteniendo caudales para {ano}: {e}")
        return [0] * 12  # Fallback a ceros

def preparar_datos_para_modelo(anos_seleccionados, nuble_df):
    """Prepara los datos en el formato que necesita el modelo"""
    datos_anuales = []
    
    for ano in anos_seleccionados:
        caudales = obtener_caudales_anuales(ano, nuble_df)
        
        datos_anuales.append({
            'año': str(ano),
            'Q_nuble': caudales
        })
        
        print(f"📊 Año {ano}: Caudales = {[f'{c:.1f}' for c in caudales]}")
    
    return datos_anuales

def verificar_datos(Q_all, QPD_eff_all_m3s, demandas_A, demandas_B):
    """Verifica que todos los datos sean válidos antes de ejecutar el modelo"""
    print("🔍 Verificando datos...")
    
    # Verificar que no haya None o NaN
    for i, q in enumerate(Q_all):
        if q is None or np.isnan(q):
            print(f"❌ Q_all[{i}] es inválido: {q}")
            return False
    
    for i, qpd in enumerate(QPD_eff_all_m3s):
        if qpd is None or np.isnan(qpd):
            print(f"❌ QPD_eff_all_m3s[{i}] es inválido: {qpd}")
            return False
    
    for i, dem in enumerate(demandas_A):
        if dem is None or np.isnan(dem):
            print(f"❌ demandas_A[{i}] es inválido: {dem}")
            return False
    
    for i, dem in enumerate(demandas_B):
        if dem is None or np.isnan(dem):
            print(f"❌ demandas_B[{i}] es inválido: {dem}")
            return False
    
    print("✅ Todos los datos son válidos")
    return True

def ejecutar_modelo_con_debug(params, Q_all, QPD_eff_all_m3s, demandas_A, demandas_B, n_years):
    """Ejecuta el modelo con verificación adicional"""
    try:
        print("🔧 Inicializando modelo...")
        model = EmbalseModelMulti(params)
        
        print("🔧 Resolviendo modelo...")
        sol = model.solve(Q_all, QPD_eff_all_m3s, demandas_A, demandas_B, n_years)
        
        return sol
        
    except Exception as e:
        print(f"❌ Error en ejecución del modelo: {e}")
        import traceback
        traceback.print_exc()
        return None

def ejecutar_simulacion_monte_carlo():
    """Ejecuta la simulación de Monte Carlo completa"""
    print("🚀 Iniciando simulación de Monte Carlo...")
    
    # Cargar datos
    nuble_df, hoya1_df, hoya2_df, hoya3_df = cargar_y_limpiar_datos()
    
    if nuble_df is None:
        print("❌ No se pudieron cargar los datos")
        return []
    
    # Parámetros base SIMPLIFICADOS para debug
    params_base = {
        'C_R': 175_000_000, 
        'C_A': 260_000_000, 
        'C_B': 105_000_000,
        'V_R_inicial': 50_000_000,  # Cambiado de 0 para evitar problemas
        'V_A_inicial': 50_000_000,
        'V_B_inicial': 50_000_000,
        'consumo_humano_anual': 3_900_000,
        'perdidas_mensuales': [0]*12,
        'lambda_R': 0.4, 
        'lambda_A': 0.4, 
        'lambda_B': 0.2,
        'eta': 0.85,
        'temporada_riego': [6,7,8,9,10,11,0],  # OCT–ABR
        'segundos_mes': [2678400,2592000,2678400,2592000,2678400,2592000,
                         2678400,2592000,2678400,2592000,2678400,2592000],
        'TimeLimit': 60,  # Reducido para debug
        'FE_A': 1.0,
        'FE_B': 1.0,
        'penaliza_EB': 1e-6,
        'penaliza_SUP': 0.0,
    }
    
    # Generar secuencias de años
    secuencias_anos = simular_varias_veces(DURACION_ANOS, NUM_SIMULACIONES)
    
    resultados_simulaciones = []
    
    for i, secuencia in enumerate(secuencias_anos):
        print(f"\n📊 Ejecutando simulación {i+1}/{NUM_SIMULACIONES}")
        print(f"Años seleccionados: {secuencia}")
        
        try:
            # Preparar datos para el modelo
            datos_historicos = preparar_datos_para_modelo(secuencia, nuble_df)
            
            if not datos_historicos:
                print(f"❌ No se pudieron preparar datos para la secuencia {secuencia}")
                continue
            
            # Construir series conectadas
            Q_all = []
            nombres_anos = []
            for escenario in datos_historicos:
                nombres_anos.append(escenario['año'])
                Q_all.extend(escenario['Q_nuble'])
            
            Y = len(datos_historicos)
            N = 12 * Y
            
            print(f"📏 Horizonte: {Y} años, {N} meses")
            print(f"📊 Q_all (primeros 5): {Q_all[:5]}")
            
            # Calcular QPD efectivo (simplificado)
            QPD_eff_all_m3s = [min(95.7, max(0, q)) for q in Q_all]  # Asegurar no negativos
            
            # Demandas (igual que en el main original)
            num_A = 21221
            num_B = 7100
            demanda_A_mes = {1:0,2:0,3:0,4:500,5:2000,6:4000,7:6000,8:8000,9:6000,10:4000,11:2000,12:500}
            demanda_B_mes = {1:0,2:0,3:0,4:300,5:1500,6:3000,7:4500,8:6000,9:4500,10:3000,11:1500,12:300}
            orden_abr_mar = [4,5,6,7,8,9,10,11,12,1,2,3]
            demandas_A = [demanda_A_mes[m] * num_A for m in orden_abr_mar]
            demandas_B = [demanda_B_mes[m] * num_B for m in orden_abr_mar]
            
            print(f"📊 Demandas A: {[f'{d/1e6:.1f}' for d in demandas_A]} Hm³")
            print(f"📊 Demandas B: {[f'{d/1e6:.1f}' for d in demandas_B]} Hm³")
            
            # Verificar datos antes de ejecutar
            if not verificar_datos(Q_all, QPD_eff_all_m3s, demandas_A, demandas_B):
                print("❌ Datos inválidos, saltando simulación")
                continue
            
            # Ejecutar modelo con debug
            sol = ejecutar_modelo_con_debug(params_base, Q_all, QPD_eff_all_m3s, demandas_A, demandas_B, Y)
            
            if sol and sol.get('status') in [2, 3]:  # OPTIMAL or SUBOPTIMAL
                # Almacenar resultados
                resultado = {
                    'simulacion_id': i + 1,
                    'anos_seleccionados': ', '.join(secuencia),
                    'FE_A': params_base['FE_A'],
                    'FE_B': params_base['FE_B'],
                    'lambda_R': params_base['lambda_R'],
                    'lambda_A': params_base['lambda_A'],
                    'lambda_B': params_base['lambda_B'],
                    'deficit_total_Hm3': (sum(sol['d_A']) + sum(sol['d_B'])) / 1e6,
                    'energia_total_MWh': sol['energia_total'],
                    'eb_total_Hm3': sum(sol['EB']) / 1e6,
                    'status': sol['status']
                }
                resultados_simulaciones.append(resultado)
                print(f"✅ Simulación {i+1} completada - Déficit: {resultado['deficit_total_Hm3']:.2f} Hm³")
            else:
                print(f"❌ Simulación {i+1} falló o no encontró solución óptima")
                if sol:
                    print(f"   Status: {sol.get('status')}")
                
        except Exception as e:
            print(f"❌ Error en simulación {i+1}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return resultados_simulaciones

def guardar_resultados_excel(resultados):
    """Guarda los resultados en un archivo Excel"""
    if not resultados:
        print("❌ No hay resultados para guardar")
        return None, None
    
    df_resultados = pd.DataFrame(resultados)
    
    # Crear directorio de resultados si no existe
    output_dir = ROOT / "data" / "resultados_monte_carlo"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Nombre del archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = output_dir / f"monte_carlo_resultados_{timestamp}.xlsx"
    
    # Guardar en Excel
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_resultados.to_excel(writer, sheet_name='Resultados', index=False)
            
            # Agregar resumen estadístico
            resumen = df_resultados.describe()
            resumen.to_excel(writer, sheet_name='Resumen_Estadistico')
        
        print(f"💾 Resultados guardados en: {excel_path}")
        return df_resultados, excel_path
    except Exception as e:
        print(f"❌ Error guardando Excel: {e}")
        return None, None

def main():
    """Función principal"""
    print("🎲 SIMULACIÓN DE MONTE CARLO - MODELO DE EMBALSE")
    print("=" * 50)
    
    # Ejecutar simulaciones
    resultados = ejecutar_simulacion_monte_carlo()
    
    if resultados:
        # Guardar resultados
        df, excel_path = guardar_resultados_excel(resultados)
        
        # Mostrar resumen
        print("\n" + "=" * 50)
        print("📈 RESUMEN FINAL")
        print("=" * 50)
        print(f"Simulaciones exitosas: {len(resultados)}/{NUM_SIMULACIONES}")
        if len(resultados) > 0:
            print(f"Déficit promedio: {df['deficit_total_Hm3'].mean():.2f} Hm³")
            print(f"Energía promedio: {df['energia_total_MWh'].mean():.0f} MWh")
            print(f"EB promedio: {df['eb_total_Hm3'].mean():.2f} Hm³")
        
    else:
        print("❌ No se completaron simulaciones exitosas")

if __name__ == "__main__":
    main()