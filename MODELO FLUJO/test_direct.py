# test_direct.py — Runner simple para probar una etapa específica
from pathlib import Path
import sys, numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from model.modelo_flujo import EmbalseModel
from utils.data_loader import DataLoader

# === CONFIG RÁPIDA DEL RUNNER ===
STAGE = 4  # 0..4  (0=red mínima, 4=final con FE PWL + turbinado)
FORCE_MIN_UPREF = True  # fuerza UPREF = min(Qin, QPD) (recomendado en stages >=1)

def main():
    print("=== PRUEBA DIRECTA — MODELO EN STAGE", STAGE, "===")
    xlsx = ROOT / 'data' / 'caudales.xlsx'
    dl = DataLoader(str(xlsx))
    scenarios = dl.get_historical_scenarios()
    if not scenarios:
        print("❌ Error cargando datos")
        return

    s0 = scenarios[0]  # primer año
    print(f"✅ Año: {s0['año']} — Q̄: {np.mean(s0['Q_nuble']):.2f} m³/s")

    params = {
        'C_R': 175_000_000, 'C_A': 260_000_000, 'C_B': 105_000_000,
        'V_R_inicial': 50_000_000, 'V_A_inicial': 50_000_000, 'V_B_inicial': 20_000_000,
        'consumo_humano_anual': 3_900_000,  # usado desde stage >=2
        'eta': 0.85,
        'pronostico_deshielo_promedio': 200_000_000,  # usado en stage >=4
        'perdidas_mensuales': [1_000_000]*12,         # usado desde stage >=2
        'temporada_riego': [6,7,8,9,10,11,0],         # oct–abr (abril=0)
        'segundos_mes': [2678400,2592000,2678400,2592000,2678400,2592000,
                         2678400,2592000,2678400,2592000,2678400,2592000],
        'lambda_R': 0.4, 'lambda_A': 0.4, 'lambda_B': 0.2,
        'TimeLimit': 300,
        'stage': STAGE,
        'force_upref_equals_min': FORCE_MIN_UPREF,
    }

    Q = s0['Q_nuble']           # m³/s por mes
    Q_PD = [8.0]*12             # preferente (m³/s)

    # Demandas (en m³/mes). En stage 0 puedes dejarlas en 0 si quieres aislar la red.
    if STAGE == 0:
        demandas_A = [0.0]*12
        demandas_B = [0.0]*12
    else:
        demandas_A = [15_000_000,15_000_000,20_000_000,25_000_000,30_000_000,35_000_000,
                      35_000_000,30_000_000,25_000_000,20_000_000,15_000_000,15_000_000]
        demandas_B = [ 6_000_000, 6_000_000, 8_000_000,10_000_000,12_000_000,14_000_000,
                      14_000_000,12_000_000,10_000_000, 8_000_000, 6_000_000, 6_000_000]

    modelo = EmbalseModel(params)
    sol = modelo.solve(Q, Q_PD, demandas_A, demandas_B)
    if not sol:
        print("❌ No se pudo resolver")
        return

    # Reporte según stage
    if STAGE == 0:
        EB_total = sum(sol['EB'])
        print("\n🎯 Objetivo ΣEB (rebalse): {:,.0f} m³".format(EB_total))
        print("Stocks fin — VRFI={:.1f} Hm³ | A={:.1f} Hm³ | B={:.1f} Hm³".format(
            sol['volumenes_R'][-1]/1e6, sol['volumenes_A'][-1]/1e6, sol['volumenes_B'][-1]/1e6
        ))
    else:
        dA = sum(sol['deficits_A']); dB = sum(sol['deficits_B'])
        print("\n🎯 Déficit total: {:,.0f} m³ (A={:,.0f}, B={:,.0f})".format(dA+dB, dA, dB))
        print("⚡ Energía: {:,.0f} MWh".format(sol['energia_total']))
        print("FE_A={:.3f}  FE_B={:.3f}  Vsep={:.1f} Hm³".format(sol['FE_A'], sol['FE_B'], sol['V_sep_deshielo']/1e6))

    # (opcional) dump mensual breve
    for i in range(12):
        print(f"Mes {i:02d}: VRFI={sol['volumenes_R'][i]/1e6:6.1f}  A={sol['volumenes_A'][i]/1e6:6.1f}  "
              f"B={sol['volumenes_B'][i]/1e6:6.1f}  EB={sol['EB'][i]/1e6:6.1f}  (Hm³)")

if __name__ == "__main__":
    main()
