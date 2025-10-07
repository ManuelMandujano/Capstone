#from utils.data_loader import DataLoader
# from pathlib import Path
# import sys
import numpy as np
#from model.data_loader_multi import DataLoaderMulti
#from model.modelo_flujo_multi import EmbalseModelMulti
#from model.params_multi import Parametros


#años

anos = ['1989/1990', '1990/1991', '1991/1992', '1992/1993', '1993/1994',
        '1994/1995', '1995/1996', '1996/1997', '1997/1998', '1998/1999',
        '1999/2000', '2000/2001', '2001/2002', '2002/2003', '2003/2004',
        '2004/2005', '2005/2006', '2006/2007', '2007/2008', '2008/2009',
        '2009/2010', '2010/2011', '2011/2012', '2012/2013', '2013/2014',
        '2014/2015', '2015/2016', '2016/2017', '2017/2018', '2018/2019']



# historicos = DataLoaderMulti.anual("data/tu_archivo.xlsx")  

NUM_SIMULACIONES = 50
DURACION_ANOS = 30 


def simular_escenario( anos_simulados):
    copia_anos = anos.copy()
    lista_resultados = []
    for ano in range(anos_simulados):
        ano_seleccionado = np.random.choice(copia_anos)
        lista_resultados.append(ano_seleccionado)
        copia_anos.remove(ano_seleccionado)
    print(f"Años seleccionados para la simulación: { [x for x in lista_resultados]}")

simular_escenario(DURACION_ANOS)