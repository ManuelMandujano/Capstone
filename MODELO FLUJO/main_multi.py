# main_multi.py — Run CONECTADO (años enlazados) y guarda un informe TXT legible
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from utils.data_loader import DataLoader
from model.modelo_flujo_multi import EmbalseModelMulti

try:
    import yaml
except Exception:
    yaml = None

MESES = ["abr","may","jun","jul","ago","sep","oct","nov","dic","ene","feb","mar"]

def hm3(x):      # m3 -> Hm3
    return float(x) / 1e6

def f(x, nd=1):  # float corto
    return f"{x:.{nd}f}"

def fsci(x):
    return f"{x:.2f}"

def pad(s, w):
    s = str(s)
    if len(s) >= w: return s[:w]
    return s + " " * (w - len(s))

def row_line(cols, widths):
    return "  ".join(pad(c, w) for c, w in zip(cols, widths))

def header(title, char="="):
    line = char * max(len(title), 3)
    return f"{line}\n{title}\n{line}\n"

def check_tol(val, tol=1e-6):
    return abs(val) <= tol

def pct_pair(prev, fin, cap):
    if cap <= 0:
        return "0→0%"
    p = 100.0 * (prev / cap)
    q = 100.0 * (fin  / cap)
    return f"{p:.0f}→{q:.0f}%"


def load_params():
    params = {
        'C_R': 175_000_000, 'C_A': 260_000_000, 'C_B': 105_000_000,
        'V_R_inicial': 0, 'V_A_inicial': 0, 'V_B_inicial': 0,
        'consumo_humano_anual': 3_900_000,  # m3/año
        'perdidas_mensuales': [0]*12,
        'lambda_R': 0.4, 'lambda_A': 0.4, 'lambda_B': 0.2,
        'eta': 0.85,
        'temporada_riego': [6,7,8,9,10,11,0],
        'segundos_mes': [2678400,2592000,2678400,2592000,2678400,2592000,
                         2678400,2592000,2678400,2592000,2678400,2592000],
        'TimeLimit': 10_000_000,  # deja tu valor largo si quieres
        'FE_A': 1.0,
        'FE_B': 1.0,
        'penaliza_EB': 1e-6,
        'penaliza_SUP': 0.0,
    }
    cfg = ROOT / 'config' / 'config.yaml'
    if yaml and cfg.exists():
        with cfg.open('r', encoding='utf-8') as f:
            y = yaml.safe_load(f) or {}
        params.update(y.get('parametros_embalse', {}))
    return params


def main():
    out = []
    out.append(header("MODELO EMBALSE — RUN CONECTADO MULTI-AÑO"))

    params = load_params()

    # Entrada (Excel)
    xlsx = ROOT / 'data' / 'caudales.xlsx'
    dl = DataLoader(str(xlsx))
    historicos = dl.get_historical_scenarios()
    if not historicos:
        print("❌ No hay escenarios en el Excel")
        return

    out.append(f"✓ Escenarios cargados: {len(historicos)} años (serie abril→marzo)\n")

    # Serie conectada (m3/s)
    Q_all = []
    nombres = []
    for s in historicos:
        nombres.append(s['año'])
        Q_all.extend(list(s['Q_nuble']))  # m3/s por mes

    Y = len(nombres)
    N = 12 * Y
    out.append(f"→ Horizonte conectado: {Y} años = {N} meses\n\n")

    # Demandas (m3/mes)
    num_A = 21221
    num_B = 7100
    demanda_A_mes = {1:0,2:0,3:0,4:500,5:2000,6:4000,7:6000,8:8000,9:6000,10:4000,11:2000,12:500}
    demanda_B_mes = {1:0,2:0,3:0,4:300,5:1500,6:3000,7:4500,8:6000,9:4500,10:3000,11:1500,12:300}
    orden_abr_mar = [4,5,6,7,8,9,10,11,12,1,2,3]
    demandas_A = [demanda_A_mes[m] * num_A for m in orden_abr_mar]
    demandas_B = [demanda_B_mes[m] * num_B for m in orden_abr_mar]
    temporada_idx = [i for i,m in enumerate(orden_abr_mar) if (demanda_A_mes[m] > 0 or demanda_B_mes[m] > 0)]
    params['temporada_riego'] = temporada_idx

    # QPD nominal (m3/s) por mes (si viene de config/Excel, úsalo; aquí fijo a 95.7)
    QPD_nominal_12 = [95.7]*12

    # === NUEVO: QPD efectivo por mes del horizonte: min(QPD_nominal_mes, Qin_mes)
    QPD_eff_all_m3s = []
    for k in range(N):
        mes = k % 12
        QPD_eff_all_m3s.append(min(QPD_nominal_12[mes], Q_all[k]))

    # Traza rápida
    out.append("Perfiles de demanda (m3/mes):\n")
    out.append(f"  ΣA = {hm3(sum(demandas_A)):.1f} Hm³/año  (por acción: {sum(demanda_A_mes.values()):,.0f} m³/acc/año)\n")
    out.append(f"  ΣB = {hm3(sum(demandas_B)):.1f} Hm³/año  (por acción: {sum(demanda_B_mes.values()):,.0f} m³/acc/año)\n\n")

    # Resolver (pasa QPD efectivo por k)
    model = EmbalseModelMulti(params)
    sol = model.solve(Q_all, QPD_eff_all_m3s, demandas_A, demandas_B, n_years=Y)
    if not sol:
        print("❌ Multi-año sin solución")
        return

    seg = params['segundos_mes']
    FE_A_12 = params.get('FE_A_12', None)
    FE_B_12 = params.get('FE_B_12', None)
    FE_A = params.get('FE_A', 1.0)
    FE_B = params.get('FE_B', 1.0)
    temporada = set(params['temporada_riego'])

    # ==========
    # Resumen global
    # ==========
    energia_total = sol['energia_total']
    deficit_total = sol.get('objetivo', None)
    out.append(header("RESUMEN GLOBAL", "-"))
    if deficit_total is not None:
        out.append(f"Déficit total (Σ d_A + d_B): {hm3(deficit_total):.1f} Hm³\n")
    out.append(f"Energía total (horizonte completo): {energia_total:,.0f} MWh\n\n")

    # ==========
    # Chequeos globales
    # ==========
    out.append(header("CHEQUEOS GLOBALES (tolerancias 1e-6)", "-"))
    tol = 1e-6
    viol_pref = viol_sup = viol_cons = 0

    for k in range(N):
        m_idx = k % 12
        Qin_m3 = Q_all[k] * seg[m_idx]
        QPD_eff_m3 = QPD_eff_all_m3s[k] * seg[m_idx]

        up = sol['UPREF'][k]
        su = sol['SUP'][k]           # debería ser 0
        inr = sol['IN_VRFI'][k]
        ina = sol['INA'][k]
        inb = sol['INB'][k]
        eb = sol['EB'][k]

        # preferente exacto = QPD efectivo
        if not check_tol(up - QPD_eff_m3, tol): viol_pref += 1

        # SUP debe ser 0
        if abs(su) > tol: viol_sup += 1

        # Conservación en la toma: Qin + SUP = UPREF + IN_R + INA + INB + EB
        cons = Qin_m3 + su - (up + inr + ina + inb + eb)
        if not check_tol(cons, tol): viol_cons += 1

    out.append(f"Violaciones preferente (UPREF=QPD_eff): {viol_pref}\n")
    out.append(f"SUP distinto de 0:                     {viol_sup}\n")
    out.append(f"Violaciones conservación de masa:      {viol_cons}\n\n")

    # ==========
    # REPORTE POR AÑO
    # ==========
    out.append("NOTA: QPD en la tabla es el QPD EFECTIVO (min(QPD_nom, Qin)).\n\n")
    for y in range(Y):
        y0, y1 = 12*y, 12*(y+1)
        titulo = f"REPORTE ANUAL: {nombres[y]}  (mes a mes)"
        out.append(header(titulo))

        # ---- Tabla 1: Física
        out.append("Tabla 1 — Física del sistema (volúmenes en Hm³; caudales en m³/s y Qin/QPD en Hm³/mes)\n")
        line1 = row_line(
            ["Mes","Qin","Qin_m","QPD","QPD_m","SUP","IN_R","INA","INB","EB","Motivo_EB",
             "VRFI prev→fin","A prev→fin","B prev→fin","VRFI %p→f","A %p→f","B %p→f"],
            [4,    6,    7,      6,    7,      7,    7,     7,    7,    7,   11,
             20,             16,          16,         12,        10,      10]
        )
        out.append(line1 + "\n")
        out.append("-"*len(line1) + "\n")

        for k in range(y0, y1):
            m_idx = k % 12
            mm = MESES[m_idx]
            Qin_m3s = Q_all[k]                 # m³/s
            QPD_eff_m3s = QPD_eff_all_m3s[k]   # m³/s
            segm = seg[m_idx]

            Qin_Hm3 = hm3(Qin_m3s * segm)
            QPD_Hm3 = hm3(QPD_eff_m3s * segm)

            SUP = sol['SUP'][k]
            IN_R = sol['IN_VRFI'][k]
            INA = sol['INA'][k]
            INB = sol['INB'][k]
            EB  = sol['EB'][k]

            if k == 0:
                VR_prev = params['V_R_inicial']
                VA_prev = params['V_A_inicial']
                VB_prev = params['V_B_inicial']
            else:
                VR_prev = sol['V_R'][k-1]
                VA_prev = sol['V_A'][k-1]
                VB_prev = sol['V_B'][k-1]

            VR_fin = sol['V_R'][k]
            VA_fin = sol['V_A'][k]
            VB_fin = sol['V_B'][k]

            # diagnóstico motivo EB
            Qin_m3 = Qin_m3s * segm
            Rk = max(0.0, Qin_m3 - (sol['UPREF'][k] - SUP) - IN_R)
            HR_A = max(0.0, params['C_A'] - VA_prev)
            HR_B = max(0.0, params['C_B'] - VB_prev)
            cuotaA = 0.71 * Rk
            cuotaB = 0.29 * Rk
            EB_cap = max(0.0, Rk - (min(cuotaA, HR_A) + min(cuotaB, HR_B)))
            motivo = "capacidad" if EB_cap > 1e-6 else ("opción" if EB > 1e-6 else "-")

            vr_pct = pct_pair(VR_prev, VR_fin, params['C_R'])
            va_pct = pct_pair(VA_prev, VA_fin, params['C_A'])
            vb_pct = pct_pair(VB_prev, VB_fin, params['C_B'])

            out.append(row_line([
                mm,
                fsci(Qin_m3s),
                f(Qin_Hm3,1),
                fsci(QPD_eff_m3s),       # QPD efectivo (m3/s)
                f(QPD_Hm3,1),
                f(hm3(SUP),1),
                f(hm3(IN_R),1),
                f(hm3(INA),1),
                f(hm3(INB),1),
                f(hm3(EB),1),
                motivo,
                f(hm3(VR_prev),1) + "→" + f(hm3(VR_fin),1),
                f(hm3(VA_prev),1) + "→" + f(hm3(VA_fin),1),
                f(hm3(VB_prev),1) + "→" + f(hm3(VB_fin),1),
                vr_pct, va_pct, vb_pct
            ], [4,6,7,6,7,7,7,7,7,7,11,20,16,16,12,10,10]) + "\n")

        out.append("\n")

        # ---- Tabla 2: Servicio
        out.append("Tabla 2 — Servicio (Hm³/mes) + SSR (Hm³) + Energía (MWh)\n")
        line2 = row_line(
            ["Mes","DemA*FE","ServA","dA","DemB*FE","ServB","dB","R_H","Energía",
             "A_out","VRFI→A","B_out","VRFI→B","VRFI tot"],
            [4,   9,        8,     6,   9,        8,     6,    7,    9,
             7,     8,      7,     8,      9]
        )
        out.append(line2 + "\n")
        out.append("-"*len(line2) + "\n")

        for k in range(y0, y1):
            m_idx = k % 12
            mm = MESES[m_idx]
            feA = FE_A_12[m_idx] if FE_A_12 else FE_A
            feB = FE_B_12[m_idx] if FE_B_12 else FE_B
            DemA_fe = feA * demandas_A[m_idx]
            DemB_fe = feB * demandas_B[m_idx]

            R_A = sol['R_A'][k]
            R_B = sol['R_B'][k]
            U_A = sol['UVRFI_A'][k]
            U_B = sol['UVRFI_B'][k]

            ServA = R_A + U_A
            ServB = R_B + U_B

            dA = sol['d_A'][k]
            dB = sol['d_B'][k]
            RH = sol['R_H'][k]
            energia_mwh = (params['eta'] * sol['Q_turb'][k] * seg[m_idx]) / 3_600_000.0

            out.append(row_line([
                mm,
                f(hm3(DemA_fe),1),
                f(hm3(ServA),1),
                f(hm3(dA),1),
                f(hm3(DemB_fe),1),
                f(hm3(ServB),1),
                f(hm3(dB),1),
                f(hm3(RH),1),
                f(energia_mwh,0),
                f(hm3(R_A),1),
                f(hm3(U_A),1),
                f(hm3(R_B),1),
                f(hm3(U_B),1),
                f(hm3(U_A + U_B),1)
            ], [4,9,8,6,9,8,6,7,9,7,8,7,8,9]) + "\n")

        dA_y = sum(sol['d_A'][y0:y1]); dB_y = sum(sol['d_B'][y0:y1])
        EB_y = sum(sol['EB'][y0:y1]); RH_y = sum(sol['R_H'][y0:y1])
        VR_f = sol['V_R'][y1-1]; VA_f = sol['V_A'][y1-1]; VB_f = sol['V_B'][y1-1]
        out.append("\nResumen anual:\n")
        out.append(f"  Déficit riego: {hm3(dA_y+dB_y):.1f} Hm³ (A={hm3(dA_y):.1f}, B={hm3(dB_y):.1f})\n")
        out.append(f"  EB total:      {hm3(EB_y):.1f} Hm³   |  SSR: {hm3(RH_y):.1f} Hm³\n")
        out.append(f"  Stocks fin:    VRFI={hm3(VR_f):.1f} Hm³, A={hm3(VA_f):.1f} Hm³, B={hm3(VB_f):.1f} Hm³\n\n")

    out.append("✓ Reporte terminado.\n")

    outdir = ROOT / 'data' / 'resultados'
    outdir.mkdir(parents=True, exist_ok=True)
    report_path = outdir / "reporte_conectado.txt"
    report_path.write_text("".join(out), encoding="utf-8")
    print(f"📝 Reporte guardado en: {report_path}")


if __name__ == "__main__":
    main()
