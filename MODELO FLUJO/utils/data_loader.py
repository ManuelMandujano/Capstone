# utils/data_loader.py
import re
import pandas as pd
import numpy as np


class DataLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df_nuble = None
        self.df_hoya1 = None
        self.df_hoya2 = None
        self.df_hoya3 = None

        # ABR del primer año (promedio global que definiste)
        self.ABRIL_PRIMERO = 22.05

    # -------------------------
    # Lectura del Excel
    # -------------------------
    def load_caudales_data(self):
        """
        Carga el Excel con los cuatro bloques (Ñuble + 3 hoyas) desde 'Hoja1'
        con offsets fijos (como venían usando). Luego limpia filas vacías y
        la fila de PROMEDIO.
        """
        try:
            xls = pd.ExcelFile(self.file_path)

            # Río Ñuble (filas 4-34 aprox.)
            self.df_nuble = pd.read_excel(
                xls, sheet_name='Hoja1', skiprows=4, nrows=31
            )
            self.df_nuble.columns = [
                'AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT',
                'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL'
            ]

            # Hoya Intermedia 1 (filas 40-70)
            self.df_hoya1 = pd.read_excel(
                xls, sheet_name='Hoja1', skiprows=40, nrows=31
            )
            self.df_hoya1.columns = [
                'AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT',
                'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL'
            ]

            # Hoya Intermedia 2 (filas 76-106)
            self.df_hoya2 = pd.read_excel(
                xls, sheet_name='Hoja1', skiprows=76, nrows=31
            )
            self.df_hoya2.columns = [
                'AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT',
                'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL'
            ]

            # Hoya Intermedia 3 (filas 112-142)
            self.df_hoya3 = pd.read_excel(
                xls, sheet_name='Hoja1', skiprows=112, nrows=31
            )
            self.df_hoya3.columns = [
                'AÑO', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT',
                'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR', 'ANUAL'
            ]

            # Limpieza
            self._clean_dataframes()

            print("✓ Datos cargados correctamente:")
            print(f"  - Río Ñuble: {len(self.df_nuble)} años")
            print(f"  - Hoya 1: {len(self.df_hoya1)} años")
            print(f"  - Hoya 2: {len(self.df_hoya2)} años")
            print(f"  - Hoya 3: {len(self.df_hoya3)} años")

            return self.df_nuble, self.df_hoya1, self.df_hoya2, self.df_hoya3

        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return None, None, None, None

    def _clean_dataframes(self):
        """Elimina filas vacías y la fila 'PROMEDIO' en los 4 DataFrames."""
        for name in ['df_nuble', 'df_hoya1', 'df_hoya2', 'df_hoya3']:
            df = getattr(self, name)
            if df is None:
                continue
            df_clean = df[df['AÑO'].notna()]
            # quitar fila de promedio si aparece
            df_clean = df_clean[~df_clean['AÑO'].astype(str).str.contains('PROMEDIO', na=False)]
            setattr(self, name, df_clean.reset_index(drop=True))

    # -------------------------
    # Helpers de formato
    # -------------------------
    def _etiqueta_desde_anio(self, valor_anio):
        """
        Convierte '1989' → '1989/1990'
        Deja '1989/1990' o '1989-1990' como '1989/1990'
        Si viene un string raro, intenta extraer un año y arma 'Y/Y+1'.
        """
        s = str(valor_anio).strip()

        # Número puro: 1989
        if s.isdigit():
            y = int(s)
            return f"{y}/{y+1}"

        # Formato con separador: 1989/1990 o 1989-1990
        m = re.match(r'^\s*(\d{4})\s*[/\-]\s*(\d{4})\s*$', s)
        if m:
            return f"{m.group(1)}/{m.group(2)}"

        # Extraer primer año y armar Y/Y+1
        m = re.search(r'(\d{4})', s)
        if m:
            y = int(m.group(1))
            return f"{y}/{y+1}"

        # Último recurso: deja el texto
        return s

    def _fila_a_hidrologico(self, row: pd.Series, abr_prev: float):
        """
        Devuelve (serie_ABR_a_MAR, abr_siguiente).

        - serie_ABR_a_MAR = [ABR(prev), MAY, JUN, JUL, AGO, SEP, OCT, NOV, DIC, ENE, FEB, MAR]
          (en m³/s tal como vienen en el Excel)
        - abr_siguiente   = el ABR de la fila actual (si existe), para coser el próximo año.
        """
        meses_restantes = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR']

        vals = [float(abr_prev)]
        for m in meses_restantes:
            v = row[m]
            vals.append(float(v) if pd.notna(v) else 0.0)

        abr_next = float(row['ABR']) if pd.notna(row['ABR']) else float(abr_prev)
        return np.array(vals, dtype=float), abr_next

    # -------------------------
    # Escenarios
    # -------------------------
    def get_historical_scenarios(self):
        """
        Genera escenarios ABR→MAR “cosidos”:
          - Primer ABR = 22.05 (promedio).
          - Para el año i, ABR(i) = ABR de la fila (i-1) —es decir, el de la fila superior—.
          - Etiqueta de año robusta (ej. '1989' → '1989/1990').

        Retorna lista de dicts con:
          {
            'año': '1989/1990',
            'Q_nuble': np.array([ABR_prev, MAY..MAR], dtype=float),
            'Q_hoya1': ...,
            'Q_hoya2': ...,
            'Q_hoya3': ...
          }
        """
        df_nuble, df_hoya1, df_hoya2, df_hoya3 = self.load_caudales_data()
        if df_nuble is None:
            print("❌ No se pudieron cargar los datos")
            return []

        n = min(len(df_nuble), len(df_hoya1), len(df_hoya2), len(df_hoya3))
        print("📊 Procesando {} años históricos (ABR→MAR, con ABR cosido desde fila anterior)".format(n))

        scenarios = []

        # ABR inicial para cada bloque
        abr_prev_nuble = self.ABRIL_PRIMERO
        abr_prev_h1    = self.ABRIL_PRIMERO
        abr_prev_h2    = self.ABRIL_PRIMERO
        abr_prev_h3    = self.ABRIL_PRIMERO

        for i in range(n):
            rN = df_nuble.iloc[i]
            r1 = df_hoya1.iloc[i]
            r2 = df_hoya2.iloc[i]
            r3 = df_hoya3.iloc[i]

            Qn, abr_next_nuble = self._fila_a_hidrologico(rN, abr_prev_nuble)
            Q1, abr_next_h1    = self._fila_a_hidrologico(r1, abr_prev_h1)
            Q2, abr_next_h2    = self._fila_a_hidrologico(r2, abr_prev_h2)
            Q3, abr_next_h3    = self._fila_a_hidrologico(r3, abr_prev_h3)

            etiqueta = self._etiqueta_desde_anio(rN['AÑO'])

            scenarios.append({
                'año': etiqueta,
                'Q_nuble': Qn,
                'Q_hoya1': Q1,
                'Q_hoya2': Q2,
                'Q_hoya3': Q3
            })

            # Preparar ABR para el siguiente año
            abr_prev_nuble = abr_next_nuble
            abr_prev_h1    = abr_next_h1
            abr_prev_h2    = abr_next_h2
            abr_prev_h3    = abr_next_h3

        print(f"✅ {len(scenarios)} escenarios históricos cargados exitosamente")
        return scenarios

    # -------------------------
    # Utilidades (compat y escenarios derivados)
    # -------------------------
    def get_caudales_matrix(self, df: pd.DataFrame):
        """
        (Compatibilidad) Devuelve MAY..ABR en el orden clásico del Excel.
        Nota: No se usa en el método nuevo ABR→MAR, pero lo dejo por si
        algo externo lo llama.
        """
        try:
            meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR']
            return df[meses].values
        except Exception as e:
            print(f"Error obteniendo matriz de caudales: {e}")
            return np.zeros((len(df), 12))

    def get_average_scenario(self):
        """
        Promedio mensual (ABR→MAR) sobre todos los años disponibles.
        """
        scenarios = self.get_historical_scenarios()
        if not scenarios:
            print("❌ No hay escenarios para calcular promedio")
            # fallback razonable
            return {
                'Q_nuble': np.full(12, 50.0),
                'Q_hoya1': np.full(12, 10.0),
                'Q_hoya2': np.full(12, 8.0),
                'Q_hoya3': np.full(12, 8.0),
            }

        avg = {
            'Q_nuble': np.mean([s['Q_nuble'] for s in scenarios], axis=0),
            'Q_hoya1': np.mean([s['Q_hoya1'] for s in scenarios], axis=0),
            'Q_hoya2': np.mean([s['Q_hoya2'] for s in scenarios], axis=0),
            'Q_hoya3': np.mean([s['Q_hoya3'] for s in scenarios], axis=0),
        }
        return avg

    def get_dry_year_scenario(self):
        """
        Año más seco según promedio de Q_nuble (ABR→MAR).
        """
        scenarios = self.get_historical_scenarios()
        if not scenarios:
            return self.get_average_scenario()
        idx = int(np.argmin([np.mean(s['Q_nuble']) for s in scenarios]))
        return scenarios[idx]

    def get_wet_year_scenario(self):
        """
        Año más húmedo según promedio de Q_nuble (ABR→MAR).
        """
        scenarios = self.get_historical_scenarios()
        if not scenarios:
            return self.get_average_scenario()
        idx = int(np.argmax([np.mean(s['Q_nuble']) for s in scenarios]))
        return scenarios[idx]
