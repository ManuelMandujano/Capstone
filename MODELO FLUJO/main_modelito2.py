# main_modelito2.py
from model.modelito2 import EmbalseNuevaPunilla

def main():
    # Crear instancia del modelo
    embalse_model = EmbalseNuevaPunilla()
    
    # Resolver el modelo
    print("Iniciando optimización del Embalse Nueva Punilla...")
    solution = embalse_model.solve()
    
    if solution:
        print("✓ Modelo resuelto exitosamente")
        print(f"Valor objetivo (déficit total): {solution['obj_val']:.2f} Hm³")
        print(f"Status del solver: {solution['status']}")
        
        # Aquí puedes agregar más análisis de resultados
        if solution['obj_val'] == 0:
            print("✓ No hay déficit de riego - objetivo alcanzado")
        else:
            print(f"⚠️  Existe un déficit total de {solution['obj_val']:.2f} Hm³")
            
    else:
        print("❌ Error al resolver el modelo")

if __name__ == "__main__":
    main()