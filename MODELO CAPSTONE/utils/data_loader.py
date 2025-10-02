# utils/data_loader.py
import pandas as pd
import numpy as np

class DataLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df_nuble = None
        self.df_hoya1 = None
        self.df_hoya2 = None
        self.df_hoya3 = None
        
    def load_caudales_data(self):
        """Cargar datos del archivo Excel de caudales de manera robusta"""
        try:
            xls = pd.ExcelFile(self.file_path)
            
            # Leer cada sección del archivo con manejo de errores
            # Río Ñuble (filas 4-34)
            self.df_nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4, nrows=31)  # nrows=31 para incluir promedios si es necesario
            self.df_nuble.columns = ['AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL']
            
            # Hoya Intermedia 1 (filas 40-70)
            self.df_hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=40, nrows=31)
            self.df_hoya1.columns = ['AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL']
            
            # Hoya Intermedia 2 (filas 76-106)
            self.df_hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=76, nrows=31)
            self.df_hoya2.columns = ['AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL']
            
            # Hoya Intermedia 3 (filas 112-142)
            self.df_hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=112, nrows=31)
            self.df_hoya3.columns = ['AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL']
            
            # Limpiar datos: eliminar filas con años NaN y la fila de promedios
            self._clean_dataframes()
            
            print(f"✓ Datos cargados correctamente:")
            print(f"  - Río Ñuble: {len(self.df_nuble)} años")
            print(f"  - Hoya 1: {len(self.df_hoya1)} años") 
            print(f"  - Hoya 2: {len(self.df_hoya2)} años")
            print(f"  - Hoya 3: {len(self.df_hoya3)} años")
            
            return self.df_nuble, self.df_hoya1, self.df_hoya2, self.df_hoya3
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return None, None, None, None
    
    def _clean_dataframes(self):
        """Limpiar DataFrames: eliminar NaN y filas de promedios"""
        for df_name in ['df_nuble', 'df_hoya1', 'df_hoya2', 'df_hoya3']:
            df = getattr(self, df_name)
            if df is not None:
                # Eliminar filas donde 'AÑO' es NaN
                df_clean = df[df['AÑO'].notna()]
                # Eliminar filas que contengan 'PROMEDIO' en la columna AÑO
                df_clean = df_clean[~df_clean['AÑO'].astype(str).str.contains('PROMEDIO', na=False)]
                setattr(self, df_name, df_clean.reset_index(drop=True))
    
    def get_caudales_matrix(self, df):
        """Convertir DataFrame a matriz de caudales mensuales de manera segura"""
        try:
            meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR']
            return df[meses].values
        except Exception as e:
            print(f"Error obteniendo matriz de caudales: {e}")
            return np.zeros((len(df), 12))
    
    def get_historical_scenarios(self):
        """Obtener todos los escenarios históricos de manera robusta"""
        df_nuble, df_hoya1, df_hoya2, df_hoya3 = self.load_caudales_data()
        
        if df_nuble is None:
            print("❌ No se pudieron cargar los datos")
            return []
        
        # Usar el mínimo número de filas disponibles
        n_filas = min(len(df_nuble), len(df_hoya1), len(df_hoya2), len(df_hoya3))
        print(f"📊 Procesando {n_filas} años históricos")
        
        scenarios = []
        for i in range(n_filas):
            try:
                scenario = {
                    'año': df_nuble.iloc[i]['AÑO'],
                    'Q_nuble': self.get_caudales_matrix(df_nuble)[i],
                    'Q_hoya1': self.get_caudales_matrix(df_hoya1)[i],
                    'Q_hoya2': self.get_caudales_matrix(df_hoya2)[i], 
                    'Q_hoya3': self.get_caudales_matrix(df_hoya3)[i]
                }
                scenarios.append(scenario)
            except Exception as e:
                print(f"❌ Error procesando año {i}: {e}")
                continue
        
        print(f"✅ {len(scenarios)} escenarios históricos cargados exitosamente")
        return scenarios
    
    def get_average_scenario(self):
        """Obtener escenario promedio de manera robusta"""
        scenarios = self.get_historical_scenarios()
        
        if not scenarios:
            print("❌ No hay escenarios para calcular promedio")
            return {
                'Q_nuble': np.full(12, 50.0),  # Valores por defecto
                'Q_hoya1': np.full(12, 10.0),
                'Q_hoya2': np.full(12, 8.0),
                'Q_hoya3': np.full(12, 8.0)
            }
        
        # Calcular promedios
        avg_scenario = {
            'Q_nuble': np.mean([s['Q_nuble'] for s in scenarios], axis=0),
            'Q_hoya1': np.mean([s['Q_hoya1'] for s in scenarios], axis=0),
            'Q_hoya2': np.mean([s['Q_hoya2'] for s in scenarios], axis=0),
            'Q_hoya3': np.mean([s['Q_hoya3'] for s in scenarios], axis=0)
        }
        
        return avg_scenario
    
    def get_dry_year_scenario(self):
        """Obtener escenario de año seco"""
        scenarios = self.get_historical_scenarios()
        
        if not scenarios:
            return self.get_average_scenario()
        
        # Encontrar el año con menor caudal anual promedio
        min_flow_idx = np.argmin([np.mean(s['Q_nuble']) for s in scenarios])
        return scenarios[min_flow_idx]
    
    def get_wet_year_scenario(self):
        """Obtener escenario de año húmedo"""
        scenarios = self.get_historical_scenarios()
        
        if not scenarios:
            return self.get_average_scenario()
        
        # Encontrar el año con mayor caudal anual promedio
        max_flow_idx = np.argmax([np.mean(s['Q_nuble']) for s in scenarios])
        return scenarios[max_flow_idx]