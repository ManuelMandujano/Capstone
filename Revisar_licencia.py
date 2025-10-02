import gurobipy as gp

try:
    # Crear un modelo vacío
    model = gp.Model("test_model")
    model.setParam('OutputFlag', 0)  # Silenciar la salida

    # Agregar una variable
    x = model.addVar(name="x")

    # Agregar una restricción
    model.addConstr(x >= 1, "c0")

    # Definir la función objetivo
    model.setObjective(x, gp.GRB.MINIMIZE)

    # Optimizar
    model.optimize()

    print("✅ Gurobi está funcionando correctamente.")
    print(f"Valor óptimo: {x.X}")

except gp.GurobiError as e:
    print("❌ Error al usar Gurobi:")
