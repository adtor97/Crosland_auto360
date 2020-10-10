# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 02:42:37 2020

@author: USUARIO
"""

import pandas as pd


# =============================================================================
# # Evaluación 360
# =============================================================================

# Read Response
direct = input("ingresa el nombre del archivo a procesar: ")
df = pd.read_excel(direct,sheet_name='Encuestas')

df.rename(columns={'¿Cuál es tu DNI?Esta información será utilizada exclusivamente para procesar la data y la finalidad es poder hacer seguimiento de quienes han completado la encuesta. Los resultados serán confidenciales y tu evaluación hacia los otros también.':'DNI'},inplace=True)

# Limpieza y Estructuración de data 
columns_len = df.shape[1]
df = df.iloc[:,19:columns_len]
df = df.loc[:,~df.columns.str.contains('que has trabajado los últimos tres meses',case=False)]
df_melt = pd.melt(df,id_vars='DNI',var_name='evaluados')


# df_melt.isnull().sum()
df_melt.dropna(inplace=True)
df_melt.reset_index(inplace=True)

# split evaluados
df_1 = pd.DataFrame(df_melt.evaluados.str.split(':',1).tolist(),
                                   columns = ['Evaluados','que_es'])

# Pivot dataframe
df_melt['evaluados']=df_1['Evaluados']
df_melt['que_es']=df_1['que_es']
df_melt.shape
# split que_es?
# df_que_es = pd.DataFrame(df_melt.que_es.str.split(':',expand=True)[0], columns = ['pilar','basura'])

#$$$$$$$$$$$$$$$$$$$$$$$$
df_melt['que_es']=df_melt.que_es.str.split(':',expand=True)[0]

# remove value no evaluado
df_melt.drop(df_melt[df_melt['value']=='No he trabajado con el/ella'].index,inplace=True)
# NOSE/NOOPINO
df_melt.drop(df_melt[df_melt['value']=='No se/No opino'].index,inplace=True)

# Remove Index column
del df_melt['index']

# DNI to type str
df_melt['DNI'] = df_melt['DNI'].astype(str)

# Split Data Frame in Values | str 
df_values = df_melt.copy()
df_feedback = df_melt.copy()
# =============================================================================
# TREATMENT
# =============================================================================

### Rules 
# 1. Cálculo sin WUF (mambo entre Mambo)  + Otras  Empresa ⇒ Empresas Hermanas 
# 2. Cálculo a WUF ( mambo a WUF)
# 3. Limpieza CTM (Sacar Autoevaluaciones)
# 4. Rpta. Satisfechas (SI ≥ 75% entonces Cuenta)
# 5. N° de Satisfechos ( Si Promedio de evaluación en 5 pilares ≥ 75% ⇒ Cuenta)

# Usamos la base de datos de mamberos para filtrar y aplicar las reglas!
# CARGA DE BBDD MAMBEROS Y WUF
df_croslanderos = pd.read_excel(direct,sheet_name='BD',dtypes={'DNI':str})
df_croslanderos['DNI'] = df_croslanderos.DNI.astype(str)
#mamberos_name = df_croslanderos['Nombre'].tolist()

# Filtro para excluir algún área en el procesamiento del Score
df_wuf = df_croslanderos[df_croslanderos['Unidad de Negocio']=='Wuf']
# wuf_name = df_wuf['Nombre'].tolist()

# COMPLEMENTANDO INFORMACIÓN DE EVALUADO

#df_values['evaluados'] = [get_close_matches(i,mamberos_name,cutoff=0.6)[0] if len(get_close_matches(i,mamberos_name,cutoff=0.6)[0])>0 else 'None' for i in df_values['evaluados']]
# df_complete = pd.merge(df_values,df_croslanderos,left_on='evaluados',right_on='Nombre',how='right')
df_complete = pd.merge(df_values,df_croslanderos,on='DNI',how='right')
# df_croslanderos.dtypes

# Eliminando Nan
df_complete.dropna(inplace=True)

# Regla 1 Para lo mamberos Wuf no afecta en su SCORE

df_complete_without_wuf = df_complete.drop(df_complete[df_complete['Unidad de Negocio']=='Wuf'].index)

# Regla 3 | Filtro CTMR

#Autoevaluados = df_complete_without_wuf[df_complete_without_wuf['evaluados']==df_complete_without_wuf['Nombre Completo']]
df_complete_without_wuf = df_complete_without_wuf[df_complete_without_wuf['evaluados']!=df_complete_without_wuf['Nombre Completo']]

# Treatment df_values

df_complete_without_wuf['value'] = pd.to_numeric(df_complete_without_wuf['value'],errors='coerce')
df_complete_without_wuf.dropna(inplace=True)
df_complete_without_wuf.rename(columns={'que_es':'Pilar'},inplace=True)
# RE - ESCALA [1-4-]

df_complete_without_wuf.loc[df_complete_without_wuf['value'] == 1,'value'] = 0
df_complete_without_wuf.loc[df_complete_without_wuf['value'] == 2,'value'] = 25
df_complete_without_wuf.loc[df_complete_without_wuf['value'] == 3,'value'] = 50
df_complete_without_wuf.loc[df_complete_without_wuf['value'] == 4,'value'] = 75
df_complete_without_wuf.loc[df_complete_without_wuf['value'] == 5,'value'] = 100
#df_complete_without_wuf.loc[df_complete_without_wuf['value']>=75,'status'] = 'Satisfecho' 
#df_complete_without_wuf.loc[df_complete_without_wuf['value']<75,'status'] = 'No Satisfecho'


# GROUP BY
table_score = df_complete_without_wuf.groupby(['evaluados','Pilar'])['value'].agg(['mean','std','count']).unstack()

# GROUP BY BANDA
table_score_by_unidad = df_complete_without_wuf.groupby(['evaluados','Unidad de Negocio','Pilar'])['value'].agg(['mean']).unstack()

# GROUP BY Área
table_score_by_sector = df_complete_without_wuf.groupby(['evaluados','Sector','Pilar'])['value'].agg(['mean']).unstack()

# GROUP BY Jerarquía
df_complete_without_wuf['Peso']=df_complete_without_wuf[['Puesto']].astype('str')
table_score_by_puesto = df_complete_without_wuf.groupby(['evaluados','Puesto','Pilar'])['value'].agg(['mean']).unstack()

# GROUP BY NIVEL OCUPACIONAL
table_score_by_nivocu = df_complete_without_wuf.groupby(['evaluados','Nivel Ocupacional','Pilar'])['value'].agg(['mean','count']).unstack()

table_score_by_count_NIVOCU = df_complete_without_wuf.groupby(['evaluados','Nivel Ocupacional'])['DNI'].agg(['count'])



# =============================================================================
# FEEDBACK
# =============================================================================

# Treatment Feedbak by mamberow

df_feedback= df_feedback[df_feedback['evaluados'].str.contains(r'mejorar')]
df_feedback.value = df_feedback.value.astype(str)
df_feedback.evaluados = df_melt.evaluados.str.split('¿',expand=True)[0]
table_feedback = df_feedback.groupby(['evaluados'])['value'].apply(lambda x: ' ||| '.join(x))

# Save to Excel =>

with pd.ExcelWriter('## Resultados 360 .xlsx') as writer:
    table_score.to_excel(writer,sheet_name='score_by_colaborador')
    table_feedback.to_excel(writer,sheet_name='feedback_by_colaborador')
    table_score_by_nivocu.to_excel(writer,sheet_name='score_by_nivel_ocup')
    table_score_by_unidad.to_excel(writer,sheet_name='score_by_unidad')
    table_score_by_sector.to_excel(writer,sheet_name='score_by_sector')
    table_score_by_puesto.to_excel(writer,sheet_name='score_by_puesto')
    table_score_by_count_NIVOCU.to_excel(writer,sheet_name='conteo unico_by_puesto')
#
## =============================================================================
## Pendientes
## =============================================================================
### Ver eliminar casos de AutoEvaluación (No sé si los hay en esta data)
### Podemos sacar más info ?
#parejas = df_values[df_values['value']=='Evaluar']
#del parejas['value']
#del parejas['que_es']
#pd.merge(parejas
#    
## =============================================================================
## # GRAFICO DE CONTACTO
## =============================================================================
#import networkx as nx
#import matplotlib.pyplot as plt
#
#
#df_base=pd.read_excel("C:\\Users\\USUARIO\\Desktop\\Python\\Grafos\\2019_Q1\\base_columnas.xlsx",sheet_name="parejas")
#df_base=df_base.fillna(0)
#
#print(df_base.head())
#
#
#df_personas=pd.read_excel("C:\\Users\\USUARIO\\Desktop\\Python\\Grafos\\2019_Q1\\base_columnas.xlsx",sheet_name="tribus")
#print(df_personas.head())
#
##agregamos los nodos
##Crear matriz de colores segun tribu
#G=nx.Graph()
#color_map=[]
#G.add_nodes_from(df_personas["mamberos"])
#for i in range(df_personas.shape[0]):
#    color=df_personas.loc[i][2]
#    color_map.append(color)
#print(color_map)
#
#
##agregamos los lados
#plt.figure(figsize=(25,25))
#for i in range(df_base.shape[0]):
#    par=[df_base.loc[i][0],df_base.loc[i][1]]
#    G.add_edges_from([par])
#
#
##otros algoritmos de ordenamiento
##https://networkx.github.io/documentation/stable/reference/drawing.html
#plt.figure(figsize=(25,25))
#pos = nx.kamada_kawai_layout(G)
##dibujar grafo
#nx.draw(G,pos,node_color=color_map,font_size=16,with_labels=True)
#plt.savefig("C:\\Users\\USUARIO\\Desktop\\Python\\Grafos\\2019_Q1\\grafo_directo_complejo.png")
#plt.show()
#    
#
#
#
#
## =============================================================================
## Excel manipulating
## =============================================================================
##  https://axiacore.com/blog/generando-hojas-de-calculo-flexibles-con-python-457/
#from xlwt import Workbook
#
#ages={
#        'Peter': 20,
#        'Karen': 19,
#        'Jessie': 43,
#        'Leonard': 56,
#        'Robert': 30,
#        'Nina': 23,
#    }
#
#number_of_elements = len(ages)
#def first_book():
#    first_book=Workbook()
#    # Sheet definition
#    ws1 = first_book.add_sheet('first_sheet')
#    # Header definition
#    ws1.write(0, 0, 'Name')
#    ws1.write(10,10,'Holi! Mambero %s' %('romero'))
#    ws1.write(0, 1, 'Years old')
#    # Represents the first row in the iteration
#    i = 1 
#    for name, years in ages.items():
#        ws1.write(i, 0, name)
#        ws1.write(i, 1, years)
#        i += 1
#        if i == number_of_elements+1: # For display the latest element
#            break
#    # Saving file
#    first_book.save('first_book.xlsx')
#    
#first_book()
#
## =============================================================================
## PDF TIMES
## =============================================================================
#
## https://stackoverflow.com/questions/20854840/xlsx-and-xlslatest-versions-to-pdf-using-'python/20867193#20867193
#from win32com import client
#xlApp = client.Dispatch("Excel.Application")
#books = xlApp.Workbooks.Open('C:\Users\USUARIO\Desktop\Laptop\Mambo Projects\Toperations\first_book.xlsx')
#ws = books.Worksheets[0]
#ws.Visible = 1
#ws.ExportAsFixedFormat(0, 'C:\\excel\\trial.pdf')
