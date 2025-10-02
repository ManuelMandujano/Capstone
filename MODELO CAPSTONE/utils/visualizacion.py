# utils/visualizacion.py
import matplotlib.pyplot as plt
import pandas as pd

class Visualizador:
    def __init__(self):
        pass
    
    def plot_resultados_mensuales(self, solucion, titulo="Resultados Mensuales"):
        """Graficar resultados mensuales"""
        meses = ['MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC', 'ENE', 'FEB', 'MAR', 'ABR']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Volúmenes almacenados
        ax1.plot(meses, solucion['volumenes_R'], label='Reserva Fija', marker='o')
        ax1.plot(meses, solucion['volumenes_A'], label='Acciones A', marker='s')
        ax1.plot(meses, solucion['volumenes_B'], label='Acciones B', marker='^')
        ax1.set_title('Volúmenes Almacenados')
        ax1.set_ylabel('m³')
        ax1.legend()
        ax1.grid(True)
        
        # Entregas
        ax2.bar(meses, solucion['entregas_A'], alpha=0.7, label='Entrega A')
        ax2.bar(meses, solucion['entregas_B'], alpha=0.7, label='Entrega B', bottom=solucion['entregas_A'])
        ax2.bar(meses, solucion['entregas_H'], alpha=0.7, label='Consumo Humano', 
                bottom=[a+b for a,b in zip(solucion['entregas_A'], solucion['entregas_B'])])
        ax2.set_title('Entregas Mensuales')
        ax2.set_ylabel('m³')
        ax2.legend()
        
        # Déficits
        ax3.bar(meses, solucion['deficits_A'], alpha=0.7, label='Déficit A', color='red')
        ax3.bar(meses, solucion['deficits_B'], alpha=0.7, label='Déficit B', color='darkred', 
                bottom=solucion['deficits_A'])
        ax3.set_title('Déficits de Riego')
        ax3.set_ylabel('m³')
        ax3.legend()
        
        # Caudal turbinado
        ax4.plot(meses, solucion['turbinado'], label='Caudal Turbinado', marker='o', color='green')
        ax4.set_title('Generación Hidroeléctrica')
        ax4.set_ylabel('m³/s')
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('data/resultados/grafico_resultados.png', dpi=300, bbox_inches='tight')
        plt.show()