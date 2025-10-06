# main.py — Runner multi-escenarios con guardado de resultados + TXT resumen
from pathlib import Path
import sys, json
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from model.modelo_flujo import EmbalseModel
from utils.data_loader import DataLoader

try:
    import yaml
except Exception:
    yaml = None


def load_params():
    # Defaults (se pueden sobre-escribir con config.yaml)
    params = {
        'C_R': 175_000_000, 'C_A': 260_000_000, 'C_B': 105_000_000,
        'V_R_inicial': 50_000_000, 'V_A_inicial': 50_000_000, 'V_B_inicial': 20_000_000,
        'consumo_humano_anual': 3_900_000,
        'eta': 0.85,
        'pronostico_deshielo_promedio': 200_000_000,
        'perdidas_mensuales': [1_000_000]*12,
        'temporada_riego': [6,7,8,9,10,11,0],  # oct–abr (abril=0)
        'segundos_mes': [2678400,2592000,2678400,2592000,2678400,2592000,
                         2678400,2592000,2678400,2592000,2678400,2592000],
        'lambda_R': 0.4, 'lambda_A': 0.4, 'lambda_B': 0.2,
        'TimeLimit': 300,

        # === controla el modelo ===
        'stage': 4,                         # 0..4 (4 = final)
        'force_upref_equals_min': True,     # UPREF = min(Qin, QPD)
        'force_FE_one': True,               # FE_A = FE_B = 1 (sin PWL)
    }
    cfg = ROOT / 'config' / 'config.yaml'
    if yaml and cfg.exists():
        with cfg.open('r', encoding='utf-8') as f:
            y = yaml.safe_load(f) or {}
        params.update(y.get('parametros_embalse', {}))
    return params


def convert_numpy(obj):
    if isinstance(obj, (np.integer, np.floating)): return obj.item()
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, (list, tuple)): return [convert_numpy(x) for x in obj]
    if isinstance(obj, dict): return {k: convert_numpy(v) for k,v in obj.items()}
    return obj


def escribir_resumen_hist(txt_path: Path, dl: DataLoader, params, demandas_A, demandas_B, Q_PD):
    """
    Recorre TODOS los años históricos y escribe un .txt con:
      - logística/explicación del modelo
      - resumen por año (independiente: cada año parte con V_*_inicial)
    """
    lineas = []
    lineas.append("=== LÓGICA (logística) DEL MODELO DE RED ===")
    lineas.append("• Horizonte mensual (abril–marzo). Cada mes entra Qin (m³/s) y se multiplica por los segundos del mes.")
    lineas.append("• Preferente: si force_upref_equals_min=True, UPREF = min(Qin, QPD).")
    lineas.append("• Conservación en la toma: Qin + SUP = UPREF + IN_VRFI + INA + INB + EB.")
    lineas.append("• Split 71/29 sobre el remanente a canales: rem = Qin - (UPREF - SUP) - IN_VRFI - EB;")
    lineas.append("  INA = 0.71·rem, INB = 0.29·rem.")
    lineas.append("• Capacidad de entrada: IN_* ≤ C_* - V_*prev (no puedes meter más de lo que cabe).")
    lineas.append("• Balance de stocks: V_*[m] = V_*[m-1] + IN_* - entregas - pérdidas")
    lineas.append("  (en VRFI además -R_H -SUP -apoyos UVRFI_A/B).")
    lineas.append("• Riego (temporada): R_A + UVRFI_A + d_A ≥ FE_A·dem_A; R_B + UVRFI_B + d_B ≥ FE_B·dem_B.")
    lineas.append("  Aquí FE_A=FE_B=1 (forzado con force_FE_one=True); la FO minimiza Σ(d_A + d_B).")
    lineas.append("• SSR anual (si activo): Σ_m R_H[m] = consumo_humano_anual.")
    lineas.append("• Turbinado (stage>=4): Q_turb·seg = UPREF + R_H + R_A + R_B (energía ~ η).")
    lineas.append("• Este resumen corre CADA AÑO EN FORMA INDEPENDIENTE (no concatena estados entre años).")
    lineas.append("  Para carry-over real (marzo→abril del año siguiente) usar un runner multi-año.")
    lineas.append("")

    from model.modelo_flujo import EmbalseModel
    historicos = dl.get_historical_scenarios()
    lineas.append("=== RESUMEN POR AÑO (independiente) ===")
    for s in historicos:
        nombre = s["año"]
        Q = s["Q_nuble"]
        modelo = EmbalseModel(params)
        sol = modelo.solve(Q, Q_PD, demandas_A, demandas_B)
        if not sol:
            lineas.append(f"{nombre}: INFACTIBLE")
            continue

        dA = sum(sol['deficits_A']); dB = sum(sol['deficits_B'])
        EB_total = sum(sol['EB'])
        VRf = sol['volumenes_R'][-1]/1e6
        VAf = sol['volumenes_A'][-1]/1e6
        VBf = sol['volumenes_B'][-1]/1e6
        energia = sol['energia_total']
        qbar = float(np.mean(Q))
        lineas.append(
            f"{nombre}: Q̄={qbar:.2f} m³/s | Déficit={dA+dB:,.0f} m³ (A={dA:,.0f}, B={dB:,.0f}) | "
            f"EB={EB_total:,.0f} m³ | Energía={energia:,.0f} MWh | "
            f"Stocks fin: VRFI={VRf:.1f} Hm³, A={VAf:.1f} Hm³, B={VBf:.1f} Hm³"
        )

    txt_path.write_text("\n".join(lineas), encoding="utf-8")
    print(f"📝 Resumen histórico guardado en: {txt_path}")


def main():
    params = load_params()
    STAGE = params.get('stage', 4)
    print(f"=== MODELO EMBALSE — RED DE FLUJO (stage={STAGE}) ===")

    xlsx = ROOT / 'data' / 'caudales.xlsx'
    dl = DataLoader(str(xlsx))
    scenarios = dl.get_historical_scenarios()
    if not scenarios:
        print("❌ No hay escenarios"); return
    print(f"✅ {len(scenarios)} escenarios históricos cargados")

    avg = dl.get_average_scenario()
    dry = dl.get_dry_year_scenario()
    wet = dl.get_wet_year_scenario()

    # Carpeta de salida (antes de usarla)
    outdir = ROOT / 'data' / 'resultados'
    outdir.mkdir(parents=True, exist_ok=True)

    # Demandas (m³/mes). Para stage 0 podrías poner [0]*12 para aislar.
    if STAGE == 0:
        demandas_A = [0.0]*12
        demandas_B = [0.0]*12
    else:
        demandas_A = [15_000_000,15_000_000,20_000_000,25_000_000,30_000_000,35_000_000,
                      35_000_000,30_000_000,25_000_000,20_000_000,15_000_000,15_000_000]
        demandas_B = [ 6_000_000, 6_000_000, 8_000_000,10_000_000,12_000_000,14_000_000,
                      14_000_000,12_000_000,10_000_000, 8_000_000, 6_000_000, 6_000_000]

    Q_PD = [8.0]*12

    escenarios = [
        ("PROMEDIO",  avg['Q_nuble']),
        ("AÑO SECO",  dry['Q_nuble']),
        ("AÑO HÚMEDO", wet['Q_nuble']),
    ]

    resultados = {}
    for nombre, Q in escenarios:
        print(f"\n=== {nombre} ===  Q̄={np.mean(Q):.2f} m³/s")
        modelo = EmbalseModel(params)
        sol = modelo.solve(Q, Q_PD, demandas_A, demandas_B)
        if not sol:
            print("❌ sin solución")
            continue

        resultados[nombre] = sol

        if STAGE == 0:
            EB_total = sum(sol['EB'])
            print(f"🎯 ΣEB (rebalse): {EB_total:,.0f} m³")
            print(f"   Stocks fin — VRFI={sol['volumenes_R'][-1]/1e6:.1f} Hm³ | "
                  f"A={sol['volumenes_A'][-1]/1e6:.1f} Hm³ | B={sol['volumenes_B'][-1]/1e6:.1f} Hm³")
        else:
            dA = sum(sol['deficits_A']); dB = sum(sol['deficits_B'])
            print(f"🎯 Déficit: {dA+dB:,.0f} m³ (A={dA:,.0f}, B={dB:,.0f}) | "
                  f"⚡ Energía: {sol['energia_total']:,.0f} MWh")
            print(f"   FE_A={sol['FE_A']:.3f}  FE_B={sol['FE_B']:.3f}  Vsep={sol['V_sep_deshielo']/1e6:.1f} Hm³")

    # Guardar JSON con todos los escenarios
    (outdir / 'resumen_final.json').write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False, default=convert_numpy),
        encoding='utf-8'
    )
    print(f"\n💾 Guardado en: {outdir}/resumen_final.json")

    # Guardar TXT con todos los AÑOS históricos (independientes)
    resumen_txt = outdir / "resumen_historico.txt"
    escribir_resumen_hist(resumen_txt, dl, params, demandas_A, demandas_B, Q_PD)


if __name__ == "__main__":
    main()
