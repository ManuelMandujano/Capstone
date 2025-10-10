import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np

# ============================================================================
# RESERVOIR OPTIMIZATION MODEL - EMBALSE NUEVA PUNILLA
# ============================================================================

# Create model
model = gp.Model("Embalse_Nueva_Punilla")

#CONJUNTOS (LISTO)
anos = ['1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
        '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
        '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
        '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
        '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
        '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019']
months = list(range(1, 13))  
temporada_riego = [6,7,8,9,10,11,0]


# PARAMETROS

# CAPACIDADES (h³)
C_TOTAL = 540
C_VRFI = 175
C_TIPO_A = 260
C_TIPO_B = 105
 
# Seconds per month (you'll need to define this properly)
segundos_por_mes = {
    1: 30*24*3600,  # April
    2: 31*24*3600,  # May
    3: 30*24*3600,  # June
    4: 31*24*3600,  # July
    5: 31*24*3600,  # August
    6: 30*24*3600,  # September
    7: 31*24*3600,  # October
    8: 30*24*3600,  # November
    9: 31*24*3600,  # December
    10: 31*24*3600, # January
    11: 28*24*3600, # February (simplified)
    12: 31*24*3600  # March
}

# ============================================================================
# LOAD DATA FROM EXCEL
# ============================================================================

def load_flow_data(file_path):
    """
    Load flow data from Excel file
    Returns dictionaries with flow data indexed by (year, month)
    """
    xls = pd.ExcelFile(file_path)
    
    # Read each sheet/section
    nuble = pd.read_excel(xls, sheet_name='Hoja1', skiprows=4, nrows=31)
    hoya1 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=39, nrows=31)
    hoya2 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=75, nrows=31)
    hoya3 = pd.read_excel(xls, sheet_name='Hoja1', skiprows=110, nrows=31)
    
    # Month mapping: Excel columns are MAY-ABR, we need to map to months 1-12 (APR-MAR)
    # Excel order: MAY JUN JUL AGO SEP OCT NOV DIC ENE FEB MAR ABR
    # Model order: APR MAY JUN JUL AGO SEP OCT NOV DIC ENE FEB MAR (months 1-12)
    excel_col_names = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR']
    model_month_order = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # ABR=12, MAY=1, ..., MAR=11
    
    # Initialize dictionaries
    Q_nuble = {}
    Q_hoya1 = {}
    Q_hoya2 = {}
    Q_hoya3 = {}
    Q_afl = {}  # Total inflow (sum of all sources)
    
    # Process each year
    for idx, row in nuble.iterrows():
        year_str = str(row['AÑO'])
        year = int(year_str.split('/')[0])  # Extract first year (e.g., 1989 from "1989/1990")
        
        # Map Excel columns to model months
        for excel_col, model_month in zip(excel_col_names, model_month_order):
            # Store individual flows
            Q_nuble[year, model_month] = nuble.loc[idx, excel_col]
            Q_hoya1[year, model_month] = hoya1.loc[idx, excel_col]
            Q_hoya2[year, model_month] = hoya2.loc[idx, excel_col]
            Q_hoya3[year, model_month] = hoya3.loc[idx, excel_col]
            
            # Calculate total inflow (sum of all sources)
            Q_afl[year, model_month] = (Q_nuble[year, model_month] + 
                                        Q_hoya1[year, model_month] + 
                                        Q_hoya2[year, model_month] + 
                                        Q_hoya3[year, model_month])
    
    return Q_afl, Q_nuble, Q_hoya1, Q_hoya2, Q_hoya3

# Load the data
data_file = "data/caudales.xlsx"
inflow, Q_nuble, Q_hoya1, Q_hoya2, Q_hoya3 = load_flow_data(data_file)

# ============================================================================
# DEFINE OTHER PARAMETERS
# ============================================================================

# Preferent flow (YOU NEED TO DEFINE THIS - placeholder for now)
preferent_flow = {}
for y in years:
    for m in months:
        preferent_flow[y, m] = 10.0  # REPLACE with actual data

# Losses (evaporation, infiltration, rain) (YOU NEED TO DEFINE THIS)
losses = {}
for y in years:
    for m in months:
        losses[y, m] = 1_000_000  # REPLACE with actual data in m³

# Demands for Type A and B shareholders (YOU NEED TO DEFINE THIS)
demand_A = {}
demand_B = {}
for y in years:
    for m in months:
        demand_A[y, m] = 20.0  # REPLACE with actual data in m³/s
        demand_B[y, m] = 10.0  # REPLACE with actual data in m³/s

# Loss proportions (YOU NEED TO DEFINE THIS)
loss_proportion_VRFI = {}
loss_proportion_A = {}
loss_proportion_B = {}
for y in years:
    for m in months:
        # These should sum to 1.0 for each (year, month)
        loss_proportion_VRFI[y, m] = 0.33
        loss_proportion_A[y, m] = 0.33
        loss_proportion_B[y, m] = 0.34




num_A = 21221
num_B = 7100
DA_a_m = {1:0,2:0,3:0,4:500,5:2000,6:4000,7:6000,8:8000,9:6000,10:4000,11:2000,12:500} #revisar que estas sean las demandas correspondientes
DB_a_b= {1:0,2:0,3:0,4:300,5:1500,6:3000,7:4500,8:6000,9:4500,10:3000,11:1500,12:300}
orden_abr_mar = [4,5,6,7,8,9,10,11,12,1,2,3]
demandas_A = [DA_a_m[m] * num_A for m in orden_abr_mar]
demandas_B = [DB_a_b[m] * num_B for m in orden_abr_mar]
# Delivery factors (currently fixed at 1)
FEA = 1
FEB = 1

# DEMANDA HUMANA (h³/año)
V_C_H = 3.9
#dispobiniliad agua inicial
S_TOTAL_0 = 0  

# ============================================================================
# 5.4 VARIABLES


# Storage volumes at end of month (m³)
storage_VRFI = model.addVars(years, months, lb=0, ub=CAP_VRFI, 
                              name="storage_VRFI")
storage_A = model.addVars(years, months, lb=0, ub=CAP_TYPE_A, 
                          name="storage_A")
storage_B = model.addVars(years, months, lb=0, ub=CAP_TYPE_B, 
                          name="storage_B")
storage_total = model.addVars(years, months, lb=0, ub=CAP_TOTAL, 
                              name="storage_total")

# Inflows to each compartment (m³/s)
inflow_VRFI = model.addVars(years, months, lb=0, name="inflow_VRFI")
inflow_A = model.addVars(years, months, lb=0, name="inflow_A")
inflow_B = model.addVars(years, months, lb=0, name="inflow_B")

# Releases at dam base (m³/s)
release_preferent = model.addVars(years, months, lb=0, name="release_preferent")
release_human = model.addVars(years, months, lb=0, name="release_human")
release_A = model.addVars(years, months, lb=0, name="release_A")
release_B = model.addVars(years, months, lb=0, name="release_B")

# Support from VRFI to A and B (m³/s)
support_VRFI_to_A = model.addVars(years, months, lb=0, name="support_VRFI_to_A")
support_VRFI_to_B = model.addVars(years, months, lb=0, name="support_VRFI_to_B")

# Spillages between compartments (m³/s)
spillage_VRFI = model.addVars(years, months, lb=0, name="spillage_VRFI")
spillage_A = model.addVars(years, months, lb=0, name="spillage_A")
spillage_B_to_A = model.addVars(years, months, lb=0, name="spillage_B_to_A")
spillage_total = model.addVars(years, months, lb=0, name="spillage_total")

# Available and storable flows (m³/s)
flow_available = model.addVars(years, months, lb=0, name="flow_available")
flow_storable = model.addVars(years, months, lb=0, name="flow_storable")

# Deficits (m³/s)
deficit_A = model.addVars(years, months, lb=0, name="deficit_A")
deficit_B = model.addVars(years, months, lb=0, name="deficit_B")

# Turbined flow (m³/s)
flow_turbined = model.addVars(years, months, lb=0, name="flow_turbined")

# ============================================================================
# OBJECTIVE FUNCTION
# ============================================================================

# Minimize total deficit
model.setObjective(
    gp.quicksum(deficit_A[y, m] + deficit_B[y, m] 
                for y in years for m in months),
    GRB.MINIMIZE
)

# ============================================================================
# CONSTRAINTS
# ============================================================================

print("Adding constraints...")

# --- RIVER BALANCE ---
for y in years:
    for m in months:
        # (1) Preferent + available = inflow
        model.addConstr(
            release_preferent[y, m] + flow_available[y, m] == inflow[y, m],
            name=f"river_balance_{y}_{m}"
        )
        
        # (2) Preferent <= inflow
        model.addConstr(
            release_preferent[y, m] <= inflow[y, m],
            name=f"preferent_limit_inflow_{y}_{m}"
        )
        
        # (3) Preferent <= preferent demand
        model.addConstr(
            release_preferent[y, m] <= preferent_flow[y, m],
            name=f"preferent_limit_demand_{y}_{m}"
        )

# --- STORABLE FLOW BALANCE ---
for y in years:
    for m in months:
        # (4) Available = total spillage + storable
        model.addConstr(
            flow_available[y, m] == spillage_total[y, m] + flow_storable[y, m],
            name=f"storable_balance_{y}_{m}"
        )

# --- VRFI BALANCE ---
for y in years:
    for m in months:
        # (5) Storable flow splits into VRFI inflow and VRFI spillage
        model.addConstr(
            flow_storable[y, m] == inflow_VRFI[y, m] + spillage_VRFI[y, m],
            name=f"VRFI_inflow_balance_{y}_{m}"
        )
        
        # (6) VRFI storage balance
        if m == 1:  # April (first month of hydrological year)
            if y == years[0]:  # First year
                # Use initial condition
                prev_storage = INITIAL_STORAGE_TOTAL * (CAP_VRFI / CAP_TOTAL)  # Proportional
            else:
                prev_storage = storage_VRFI[y-1, 12]  # March of previous year
        else:
            prev_storage = storage_VRFI[y, m-1]
        
        model.addConstr(
            storage_VRFI[y, m] == prev_storage + 
            inflow_VRFI[y, m] * seconds_per_month[m] -
            release_human[y, m] * seconds_per_month[m] -
            support_VRFI_to_A[y, m] * seconds_per_month[m] -
            support_VRFI_to_B[y, m] * seconds_per_month[m] -
            loss_proportion_VRFI[y, m] * losses[y, m],
            name=f"VRFI_storage_balance_{y}_{m}"
        )
        
        # (9) VRFI inflow capacity constraint
        model.addConstr(
            inflow_VRFI[y, m] * seconds_per_month[m] <= 
            CAP_VRFI - prev_storage + 
            release_human[y, m] * seconds_per_month[m] +
            support_VRFI_to_A[y, m] * seconds_per_month[m] +
            support_VRFI_to_B[y, m] * seconds_per_month[m],
            name=f"VRFI_inflow_capacity_{y}_{m}"
        )

# (11-12) VRFI spillage distribution
for y in years:
    for m in months:
        model.addConstr(
            inflow_A[y, m] == 0.71 * spillage_VRFI[y, m],
            name=f"spillage_VRFI_to_A_{y}_{m}"
        )
        model.addConstr(
            inflow_B[y, m] == 0.29 * spillage_VRFI[y, m],
            name=f"spillage_VRFI_to_B_{y}_{m}"
        )

# (13-16) Support limits from VRFI
for y in years:
    for m in months:
        if m == 1:
            if y == years[0]:
                prev_storage_VRFI = INITIAL_STORAGE_TOTAL * (CAP_VRFI / CAP_TOTAL)
            else:
                prev_storage_VRFI = storage_VRFI[y-1, 12]
        else:
            prev_storage_VRFI = storage_VRFI[y, m-1]
        
        model.addConstr(
            support_VRFI_to_A[y, m] * seconds_per_month[m] <= 0.71 * prev_storage_VRFI,
            name=f"support_A_limit_{y}_{m}"
        )
        model.addConstr(
            support_VRFI_to_B[y, m] * seconds_per_month[m] <= 0.29 * prev_storage_VRFI,
            name=f"support_B_limit_{y}_{m}"
        )

# --- TYPE A BALANCE ---
for y in years:
    for m in months:
        if m == 1:
            if y == years[0]:
                prev_storage_A = INITIAL_STORAGE_TOTAL * (CAP_TYPE_A / CAP_TOTAL)
            else:
                prev_storage_A = storage_A[y-1, 12]
        else:
            prev_storage_A = storage_A[y, m-1]
        
        # Storage balance for A
        model.addConstr(
            storage_A[y, m] == prev_storage_A +
            inflow_A[y, m] * seconds_per_month[m] +
            spillage_B_to_A[y, m] * seconds_per_month[m] -
            release_A[y, m] * seconds_per_month[m] -
            spillage_A[y, m] * seconds_per_month[m] -
            loss_proportion_A[y, m] * losses[y, m],
            name=f"storage_A_balance_{y}_{m}"
        )
        
        # Release capacity constraint
        model.addConstr(
            release_A[y, m] * seconds_per_month[m] <= 
            prev_storage_A + inflow_A[y, m] * seconds_per_month[m] + 
            support_VRFI_to_A[y, m] * seconds_per_month[m],
            name=f"release_A_capacity_{y}_{m}"
        )

# --- TYPE B BALANCE ---
for y in years:
    for m in months:
        if m == 1:
            if y == years[0]:
                prev_storage_B = INITIAL_STORAGE_TOTAL * (CAP_TYPE_B / CAP_TOTAL)
            else:
                prev_storage_B = storage_B[y-1, 12]
        else:
            prev_storage_B = storage_B[y, m-1]
        
        # Storage balance for B
        model.addConstr(
            storage_B[y, m] == prev_storage_B +
            inflow_B[y, m] * seconds_per_month[m] +
            spillage_A[y, m] * seconds_per_month[m] -
            release_B[y, m] * seconds_per_month[m] -
            spillage_B_to_A[y, m] * seconds_per_month[m] -
            loss_proportion_B[y, m] * losses[y, m],
            name=f"storage_B_balance_{y}_{m}"
        )
        
        # Release capacity constraint
        model.addConstr(
            release_B[y, m] * seconds_per_month[m] <= 
            prev_storage_B + inflow_B[y, m] * seconds_per_month[m] + 
            support_VRFI_to_B[y, m] * seconds_per_month[m],
            name=f"release_B_capacity_{y}_{m}"
        )

# --- TURBINED FLOW ---
for y in years:
    for m in months:
        model.addConstr(
            flow_turbined[y, m] == support_VRFI_to_A[y, m] + support_VRFI_to_B[y, m] +
            release_human[y, m] + release_A[y, m] + release_B[y, m],
            name=f"turbined_flow_{y}_{m}"
        )

# --- DEFICIT DEFINITIONS ---
for y in years:
    for m in months:
        model.addConstr(
            deficit_A[y, m] == delivery_factor_A[y] * demand_A[y, m] - 
            release_A[y, m] - support_VRFI_to_A[y, m],
            name=f"deficit_A_{y}_{m}"
        )
        model.addConstr(
            deficit_B[y, m] == delivery_factor_B[y] * demand_B[y, m] - 
            release_B[y, m] - support_VRFI_to_B[y, m],
            name=f"deficit_B_{y}_{m}"
        )

# --- SUPPORT CONSTRAINTS ---
for y in years:
    for m in months:
        model.addConstr(
            support_VRFI_to_A[y, m] <= release_A[y, m],
            name=f"support_A_limit_release_{y}_{m}"
        )
        model.addConstr(
            support_VRFI_to_B[y, m] <= release_B[y, m],
            name=f"support_B_limit_release_{y}_{m}"
        )

# --- LOSS PROPORTIONS ---
for y in years:
    for m in months:
        model.addConstr(
            loss_proportion_VRFI[y, m] + loss_proportion_A[y, m] + 
            loss_proportion_B[y, m] == 1.0,
            name=f"loss_proportions_{y}_{m}"
        )

# --- TOTAL STORAGE ---
for y in years:
    for m in months:
        model.addConstr(
            storage_total[y, m] == storage_VRFI[y, m] + storage_A[y, m] + storage_B[y, m],
            name=f"total_storage_{y}_{m}"
        )

# --- HUMAN CONSUMPTION ---
for y in years:
    # Annual human consumption must equal fixed volume
    model.addConstr(
        gp.quicksum(release_human[y, m] * seconds_per_month[m] for m in months) == VOL_HUMAN_CONSUMPTION,
        name=f"human_consumption_annual_{y}"
    )

# --- DEMAND LIMITS ---
for y in years:
    for m in months:
        model.addConstr(
            release_A[y, m] + support_VRFI_to_A[y, m] <= demand_A[y, m],
            name=f"demand_limit_A_{y}_{m}"
        )
        model.addConstr(
            release_B[y, m] + support_VRFI_to_B[y, m] <= demand_B[y, m],
            name=f"demand_limit_B_{y}_{m}"
        )

# --- MINIMUM DELIVERY (50% of demand) ---
for y in years:
    for m in months:
        model.addConstr(
            release_A[y, m] >= 0.5 * demand_A[y, m],
            name=f"min_delivery_A_{y}_{m}"
        )
        model.addConstr(
            release_B[y, m] >= 0.5 * demand_B[y, m],
            name=f"min_delivery_B_{y}_{m}"
        )

print("Model built successfully!")
print(f"Variables: {model.NumVars}")
print(f"Constraints: {model.NumConstrs}")

# ============================================================================
# SOLVE
# ============================================================================

# Set parameters
model.Params.TimeLimit = 3600  # 1 hour
model.Params.MIPGap = 0.01  # 1% optimality gap

# Solve
print("\nSolving model...")
model.optimize()

# ============================================================================
# RESULTS
# ============================================================================

if model.status == GRB.OPTIMAL:
    print(f"\nOptimal solution found!")
    print(f"Total deficit: {model.objVal:.2f} m³/s")
    
    # Extract some sample results
    print("\n--- Sample Results (Year 1989, Month 1) ---")
    print(f"Storage VRFI: {storage_VRFI[1989, 1].X:.2f} m³")
    print(f"Storage A: {storage_A[1989, 1].X:.2f} m³")
    print(f"Storage B: {storage_B[1989, 1].X:.2f} m³")
    print(f"Deficit A: {deficit_A[1989, 1].X:.2f} m³/s")
    print(f"Deficit B: {deficit_B[1989, 1].X:.2f} m³/s")
    
else:
    print(f"\nOptimization failed with status: {model.status}")