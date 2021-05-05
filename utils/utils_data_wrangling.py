import pandas as pd
#from datetime import datetime, timedelta
from math import ceil
from itsdangerous import Signer
from difflib import get_close_matches
import re
import os
from datetime import date
import numpy as np
# =============================================================================
# #EJEMPLO DE EJECUCION
# =============================================================================
# import Auto360
# #Necesitas el csv de resultados
# # Necesitas el BD de COlaboradores en formato HC

# survey = pd.read_csv('CroslandQ2JulioSurveyExport.csv',encoding='utf-8')

# colaboradores = pd.read_excel('Dashboard 360_Q2.xlsx',sheet_name='HC JUNIO',encoding='utf-8')

# holi = Auto360.auto360(df_survey=survey,df_colaboradores=colaboradores)

# #agregamos el YEAR y Q solicitado para subir a la nube
# df_complete = agregar_Q(holi[0],year=2020,Q='Q2')

# #Guardas para revisar, no es necesario
# df_complete.to_csv('df_complete.csv',encoding='utf-8')


# # Ejemplo de peticion de un reporte personal
# personal = personal_reporting(df_complete=holi[0],df_feedback=holi[1],dni='40646048',columna_dni='DNI_evaluado')


# =============================================================================
# #=======================FUNCIONES===============================#
# =============================================================================

def calculate_age(born): # Función para calcular edad
    if born is None:
        return None
    else:

        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def capitalizar_nombre(message):
    message = str(message)
    capitalized_message = " ".join([word.capitalize() for word in message.split(" ")])
    return capitalized_message

def tokenizar(dni):
    # #print(type(dni)) # Punto de revision Input
    if isinstance(dni, float):
        dni = str(int(dni))
    elif isinstance(dni, str):
        dni = str(dni)
    elif isinstance(dni,int):
        dni = str(dni)
    s = Signer('crosland_360')
    #sing solo acepta cadena str
    token_dni = str(s.sign(dni)).split('.')[1]
    return token_dni


def cambioorden_nombre_apellido(message):
    # Invierte el nombre de apellidos y nombres
    # Primero seran los nombre luego los apellidos

    message_list = str(message).split()
    #Cantidad total de apellidos y nombres
    max_word=len(message_list)
    # Reorden de palabras
    order = list(range(2,max_word))
    order.append(0)
    order.append(1)
    message_list = [message_list[i] for i in order]

    new_message = ""
    for word in message_list:
        new_message += str(word) + " "
    new_message = new_message[:-1]
    #new_message = str(message.split()[max_word]+' '+message.split()[0]+' '+message.split()[1])
    return new_message


def agregar_Q(df,year,Q):
    year = str(year)
    Q    = str(Q)

    year_Q = year+'-'+Q
    year_Q = str(year_Q)
    # #print(year_Q)
    # df.assign(Periodo=year_Q)
    # df.assign(year=year)
    # df.assign(Q=Q)
    df['Periodo'] = year_Q
    df['year'] = year
    df['Q'] = Q
    return df

def last_n_q(df,n,columna_periodo='Periodo'):
    #Formato periodo Year-Q4
    periodos_activos = df['Periodo'].drop_duplicates(keep='first')
    periodos_activos = periodos_activos.reset_index()
    periodos_activos = periodos_activos.Periodo.str.split('-Q',expand=True)
    periodos_activos.columns = ['Year','Q']
    periodos_activos.Year = periodos_activos.Year.astype(int)
    periodos_activos.Q = periodos_activos.Q.astype(int)

    # Las 'n' Q

    periodos_activos = periodos_activos.nlargest(n,['Year','Q'])
    periodos_activos['Periodo']=periodos_activos['Year'].astype(str)+'-Q'+periodos_activos['Q'].astype(str)
    periodo_list = periodos_activos['Periodo'].to_list()

    return periodo_list



def df_split(df_survey, df_colaboradores, columna_documento_colaboradores='Numero documento'):
    # Contiene DNI del evaluador -> Autoevaluador
    DNI_survey = "¿Cuál es tu DNI?Esta información será utilizada exclusivamente para procesar la data y la finalidad es poder hacer seguimiento de quienes han completado la encuesta. Los resultados serán confidenciales y tu evaluación hacia los otros también."
    col_autoev = df_survey.columns[df_survey.columns.str.contains('DNI|Autoevaluac',regex=True)]
    # Contiene Preguntas de Autoevaluacion
        # si no hace match con hc, el evaluador es eliminado
    df_survey = df_survey.merge(df_colaboradores[columna_documento_colaboradores],left_on=DNI_survey,right_on="Numero documento",how="inner")

    df_autoev = df_survey[col_autoev].copy()

    if len(df_autoev.columns)<2:
        df_autoev.loc[:,"Puntaje:Autoevaluación | Contagiamos pasión: Te atreves a probar cosas nuevas, levantas la mano cuando tienes alguna idea y si crees que puedes generar un impacto positivo, la ejecutas. Estás siempre dispuesto a asumir nuevos retos e impulsas al resto de tus compañeros a que actúen con esa misma motivación.?"] = 0
        df_autoev.loc[:,"Puntaje:Autoevaluación | Trabajamos juntos: Eres una persona que busca relacionarte con el resto de tus compañeros y siempre estás dispuesto a trabajar en equipo. Respeta a los demás y ves en el logro de uno, el logro de todos."] = 0
        df_autoev.loc[:,"Puntaje:Autoevaluación | Buscamos la excelencia: Eres una persona que no está contenta solo con cumplir sus objetivos en el tiempo y calidad esperados, sino que intenta siempre ir más allá. Estás dispuesto a aprender nuevas cosas y, desde la posición en la que te encuentras, buscas hacer uso de tus fortalezas para contribuir con la meta de tu equipo y de la empresa. Saca de cada experiencia algún aprendizaje y lo comparte con los demás."] = 0
        df_autoev.loc[:,"Puntaje:Autoevaluación | Vivimos y disfrutamos: Encuentras el balance entre el trabajo y tus motivaciones personales. Te enfocas en lo positivo de la vida y le transmites ese estado de ánimo a los demás."] = 0
    else:
        None

    for col in df_autoev.columns[1:]:
        df_autoev.rename(columns={str(col):str(re.split('[|\-:]+',col)[2].strip())},inplace=True)
    df_autoev.rename(columns={str(df_survey.columns[df_survey.columns.str.contains('DNI',regex=True)][0]):'DNI_evaluador'},inplace=True)
    df_autoev = df_autoev.melt(id_vars='DNI_evaluador',var_name='Pilar')
    df_autoev.dropna(inplace=True)

    #r-scale segun Logica de 2020 Q4

    df_autoev.loc[df_autoev['value'] == 0,'value'] = np.nan #Conversion especial de puntaje vacío
    df_autoev.loc[df_autoev['value'] == 1,'value'] = 20
    df_autoev.loc[df_autoev['value'] == 2,'value'] = 40
    df_autoev.loc[df_autoev['value'] == 3,'value'] = 60
    df_autoev.loc[df_autoev['value'] == 4,'value'] = 80
    df_autoev.loc[df_autoev['value'] == 5,'value'] = 100

    len_df_autoev_columns = len(df_autoev.columns)
    df_colaboradores = df_colaboradores.rename(columns={columna_documento_colaboradores: 'DNI_evaluador'})

    # #print(df_colaboradores.columns)
    # #print(df_autoev.columns)
    df_autoev = df_autoev.merge( df_colaboradores, on="DNI_evaluador", how="left")
    dict_cols_autoev_evaluado = {x+"_evaluado":x for x in list(df_autoev.columns[len_df_autoev_columns:])}
    df_autoev = df_autoev.rename(columns = dict_cols_autoev_evaluado)
    # SPLIT ONLY DF SURVEY
    only_col_autoev = df_survey.columns[df_survey.columns.str.contains('Autoevalu',regex=True)]
    df_survey = df_survey.drop(columns = only_col_autoev)


    del only_col_autoev,col_autoev

    return [df_autoev,df_survey]


def dni_format(dni):
    #para string de dni con digitos de ceros faltantes delante
    dni=str(dni)
    if len(dni)==8:
        return dni
    elif len(dni)==0:
        return dni
    elif len(dni)<8:
        dig_faltantes = 8 - len(dni)
        ceros_list = [0]*dig_faltantes
        ceros_list_str = ''
        for cero in ceros_list:
            ceros_list_str += str(cero) + ""
        dni_convert = ceros_list_str+dni
        return dni_convert


def get_close(nombre,lista_nombres,mincut=0.4):

    close_name = get_close_matches(nombre,lista_nombres,cutoff=mincut)
    if len(close_name)==0:
        return nombre
    elif len(close_name)>0:
        return close_name[0]

def simple_nombre(name):
    name = str(name)
    name = name.replace("Del ","").replace("De La ","").replace("De ","")
    name = name.replace("DEL ","").replace("DE LA ","").replace("DE ","")
    new_name = name
    return new_name

def get_quarter(d):
    return "%d-Q%d" % (d.year,ceil(d.month/3)-1)

def auto360(df_survey,df_colaboradores,year,Q,columna_documento_colaboradores='Numero documento'):
    # =============================================================================
    #     VARIABLES
    # =============================================================================
    # Periodo: Year-Q, se usa para discriminar la transformacion de las puntuaciones originales.
    #          a pedido de Crosland segun a partir de determinado periodo seria una transformacion diferente.

    #Seccion Tratamiento de Respuestas 360
    # df_survey : Es el CSV que arroja Survey Gizmo de la encuesta 360
    # df_colaboradores: es (excel) de colaboradores con sus datos personales
    #                   este aun falta actualizarse para leer los datos del archivo que arroja en bruto su sistema de RRHH
    #

    df_survey.rename(columns={df_survey.columns[df_survey.columns.str.contains('DNI')][0]:'DNI_evaluador'},inplace=True)

    # Limpieza y Estructuración de data
    columns_len = df_survey.shape[1]
    #Filtro de respuestas completas
    df_survey = df_survey.loc[df_survey['Status']=='Complete']
    df_survey = df_survey.iloc[:,19:columns_len]
    df_survey = df_survey.loc[:,~df_survey.columns.str.contains('que has trabajado los últimos tres meses',case=False)]

    # Formateo de DNI
    df_melt = pd.melt(df_survey,id_vars='DNI_evaluador',var_name='evaluados')
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

    #$$$$$$$$$$$$$$$$$$$$$$$$
    df_melt['que_es']=df_melt.que_es.str.split(':',expand=True)[0]

    # remove value no evaluado
    df_melt.drop(df_melt[df_melt['value']=='No he trabajado con el/ella'].index,inplace=True)
    # NOSE/NO OPINO
    df_melt.drop(df_melt[df_melt['value']=='No se/No opino'].index,inplace=True)

    # Remove Index column
    del df_melt['index']

    # DNI to type str
    df_melt['DNI_evaluador'] = df_melt['DNI_evaluador'].astype(str)

    # Split Data Frame in Values | str
    df_values = df_melt.copy()

    df_values['DNI_evaluador'] = pd.to_numeric(df_values['DNI_evaluador'],errors='ignore')
    df_values['DNI_evaluador'] = df_values['DNI_evaluador'].astype(int)

    # LIMPIAMOS DF VALUES - Dejamos solo valores numericos 1,2,3,4,5
    df_values['value'] = pd.to_numeric(df_values['value'],errors='coerce')
    df_values = df_values[(df_values['value']>=1) & (df_values['value']<=5)]

    df_values.drop_duplicates(subset=['DNI_evaluador','evaluados','que_es'],keep='first')

    df_values["Nombre Completo_artificial"] = df_values["evaluados"].apply(lambda x: simple_nombre(x))

    # =============================================================================
    # Tratamiento de HC
    # =============================================================================

    df_colaboradores.rename(columns={columna_documento_colaboradores:'DNI'},inplace=True)
    df_colaboradores['DNI'] = df_colaboradores["DNI"].astype(str)

    #Eliminamos filas con contenido vacio
    df_colaboradores.drop(df_colaboradores[df_colaboradores.DNI.isnull()].index, inplace = True)
    df_colaboradores.drop(df_colaboradores[df_colaboradores.DNI=='nan'].index, inplace = True)

    df_colaboradores['Nombre Completo_artificial'] = df_colaboradores['Nombre Completo'].apply(lambda x: simple_nombre(x))
    df_colaboradores['Nombre Completo_artificial'] = df_colaboradores['Nombre Completo_artificial'].apply(cambioorden_nombre_apellido)
    df_colaboradores['Nombre Completo_artificial'] = df_colaboradores['Nombre Completo_artificial'].apply(capitalizar_nombre)

    df_colaboradores['DNI'] = pd.to_numeric(df_colaboradores['DNI'],errors='ignore')
    df_colaboradores['DNI'] = df_colaboradores['DNI'].astype(int)


    # =============================================================================
    #     Agregamos Informacion para Evaluados y Evaluados
    # =============================================================================
    # Copia para cada df EVALUADO vs EVALUADOR

    df_evaluador = df_colaboradores.copy()
    df_evaluados = df_colaboradores.copy()

    ## EVALUADOR | Aquel que evalua a otros
    # Columnas evaluador
    df_evaluador = df_evaluador[['DNI','Nombre Completo','Unidad','Area','Sector','Nivel Ocupacional']]
    df_evaluador.columns = [str(col) + '_evaluador' for col in df_evaluador.columns]

    # Columnas evaluados
    df_evaluados.columns = [str(col) + '_evaluado' for col in df_evaluados.columns]

    # =============================================================================
    #     COMPLEMENTAMOS INFORMACION >>>EVALUADOS & EVALUADOR
    # =============================================================================

    #Merge evaluado & evaluador
    df_complete = pd.merge(df_values,df_evaluados,left_on='Nombre Completo_artificial',right_on='Nombre Completo_artificial_evaluado',how='left') # Usamos el nombredf_complete = pd.merge(df_values,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre

    # MERGUE EVALUADOR # PROBANDO LEFT
    df_complete = pd.merge(df_complete,df_evaluador,on='DNI_evaluador',how='left') # usamos el DNI

    ##
    # =============================================================================
    # @INICIO OBSERVADO
    # DIFFLIB MAGIC # TRATAMIENTO de los que no hicieron merge
    # =============================================================================
    #Observacion> Los nombre que no hacen merge es por la composicion Apellido Nombre

    df_complete_temp = df_complete[df_complete['Nombre Completo_artificial_evaluado'].isnull()]
    df_complete_temp = df_complete_temp[['DNI_evaluador','evaluados','Nombre Completo_artificial','value','que_es']]
    df_complete_temp = df_complete_temp.loc[~df_complete_temp["Nombre Completo_artificial"].str.contains('Sentiment',case=False)]
    df_complete_temp = df_complete_temp.loc[~df_complete_temp["Nombre Completo_artificial"].str.contains('¿Qué crees que debería',case=False)]
    df_complete_temp['Nombre Completo_artificial'] = df_complete_temp["Nombre Completo_artificial"].apply(lambda x:get_close(nombre=x, lista_nombres=df_evaluados['Nombre Completo_artificial_evaluado'].to_list()))

    #Merge evaluado & evaluador
    df_complete_temp = pd.merge(df_complete_temp,df_evaluados,left_on='Nombre Completo_artificial',right_on='Nombre Completo_artificial_evaluado',how='left') # Usamos el nombre
    df_complete_temp = pd.merge(df_complete_temp,df_evaluador,on='DNI_evaluador',how='left') # usamos el DNI

    df_replace_names = df_complete_temp[["evaluados","Nombre Completo_evaluado"]]
    df_replace_names = df_replace_names.rename(columns = {"evaluados":"Nombre encontrado en Alchemer",
                                                                    "Nombre Completo_evaluado": "Nombre encontrado en el HC"})
    df_replace_names = df_replace_names.drop_duplicates()

    #df_complete_temp.drop(columns=["evaluados"],inplace=True)
    #df_complete.dropna(subset = ['DNI_evaluado'],inplace=True)
    df_complete.dropna(subset = ['Nombre Completo_evaluado'],inplace=True)

    df_complete = pd.concat([df_complete,df_complete_temp],ignore_index=True)

    # @FIN OBSERVADO

    # =============================================================================
    #     # COMPLEMENTANDO INFORMACIÓN DE EVALUADO
    # =============================================================================

    # Eliminando Nan
    df_complete.drop(df_complete[df_complete.evaluados.isnull()].index, inplace = True)

    # Regla 3 | Filtro CTMR
    # Elimina las Autoevaluaciones dentro de las evaluaciones
    df_complete = df_complete[df_complete['Nombre Completo_evaluador']!=df_complete['Nombre Completo_evaluado']]

    # Treatment df_values
    df_complete['value'] = pd.to_numeric(df_complete['value'],errors='coerce')
    df_complete.drop(df_complete[df_complete.value.isnull()].index, inplace = True)
    df_complete.rename(columns={'que_es':'Pilar'},inplace=True)

    periodo = str(year)+'-'+str(Q)
    # RE - ESCALA [1-5] -> [0-100]
    if periodo =='2020-Q1'or periodo=='2020-Q2' or periodo =='2020-Q3':
        df_complete.loc[df_complete['value'] == 1,'value'] = 0
        df_complete.loc[df_complete['value'] == 2,'value'] = 25
        df_complete.loc[df_complete['value'] == 3,'value'] = 50
        df_complete.loc[df_complete['value'] == 4,'value'] = 75
        df_complete.loc[df_complete['value'] == 5,'value'] = 100
    else:
        df_complete.loc[df_complete['value'] == 1,'value'] = 20
        df_complete.loc[df_complete['value'] == 2,'value'] = 40
        df_complete.loc[df_complete['value'] == 3,'value'] = 60
        df_complete.loc[df_complete['value'] == 4,'value'] = 80
        df_complete.loc[df_complete['value'] == 5,'value'] = 100

    # STATUS
    df_complete.drop(columns = ["Nombre Completo_artificial","Nombre Completo_artificial_evaluado"],inplace=True)
    df_complete.loc[df_complete.groupby(['DNI_evaluador','Pilar','DNI_evaluado']).value.max == df_complete.value]


    #TOKENIZAR DNI
        # AGREGAR Q
    df_evaluaciones = agregar_Q(df_complete, year=year, Q=Q)

    #df_evaluaciones['Fecha Nacimiento_evaluado'] = df_evaluaciones['Fecha Nacimiento_evaluado'].to_datetime
    df_evaluaciones['edad_evaluado'] = df_evaluaciones['Fecha Nacimiento_evaluado'].apply(calculate_age)
    mean = df_evaluaciones['edad_evaluado'].mean()
    df_evaluaciones['edad_evaluado'].fillna(mean,inplace=True)

    df_evaluaciones['edad_evaluado_rango'] = ['Menor a 20 ' if age<20 else \
                                               'De 20 a 25' if age>=20 and age<25 else \
                                               'De 26 a 30' if age>=26 and age<30 else \
                                               'De 30 a 35' if age>=30 and age<35 else \
                                               'Mayor a 35' for age in df_evaluaciones['edad_evaluado']]
    #Categorización en Generacion por Edades

    df_evaluaciones['generacion_edad'] = [ np.nan if  pd.isna(fechanacimiento) else \
                                                  'Generation Z' if fechanacimiento.year > 1999  else  \
                                                  'Millenials' if fechanacimiento.year > 1981 and fechanacimiento.year < 2000  else  \
                                                  'Generation Y' if fechanacimiento.year > 1965 and fechanacimiento.year < 1982  else  \
                                                  'Baby Boomer' for fechanacimiento in df_evaluaciones['Fecha Nacimiento_evaluado']]

    # =============================================================================
    # FEEDBACK
    # =============================================================================

    # Treatment Feedbak por Colaborador
    # Nuevo procesamiento
    columns_feedback  = ["DNI_evaluador"] + df_survey.columns[df_survey.columns.str.contains('mejorar?')].to_list()

    df_feedback = df_survey[columns_feedback]
    df_feedback = df_feedback.melt(id_vars="DNI_evaluador")
    df_feedback=df_feedback.dropna(axis=0)
    df_feedback = df_feedback.replace('\n',' ', regex=True)
    df_feedback = df_feedback.replace('\n',' ', regex=True)
    df_feedback = df_feedback.replace('|',' ')
    df_feedback = df_feedback.replace(';',' ')
    df_feedback.variable = df_feedback.variable.str.split(':|¿|,',expand=True)[0] # Split + Clean
    df_feedback.variable = df_feedback.variable.str.strip()

    #----------------------------------------------------------------

    #Df_feedback detallado
    df_feedback["Nombre Completo_artificial"] = df_feedback["variable"].apply(lambda x: simple_nombre(x))
    df_feedback['Nombre Completo_artificial'] = df_feedback["Nombre Completo_artificial"].apply(lambda x: capitalizar_nombre(x))
    # df_feedback_v0 = df_feedback.copy()
    # MERGE -> EVALUADO NOMBRE ARTIFICIAL
    df_feedback_detail = pd.merge(df_feedback,df_evaluados[['Nombre Completo_artificial_evaluado','Nombre Completo_evaluado','DNI_evaluado']],left_on='Nombre Completo_artificial',right_on='Nombre Completo_artificial_evaluado',how='left') # Usamos el nombre

    # Tratamiento a lo que no hicieron merge
    df_feedback_detail_temp = df_feedback_detail[df_feedback_detail['Nombre Completo_artificial_evaluado'].isnull()]
    df_feedback_detail = df_feedback_detail.dropna(axis=0)

    #difflib
    df_feedback_detail_temp['Nombre Completo_artificial'] = df_feedback_detail_temp.variable.apply(lambda x:get_close(nombre=x, lista_nombres=df_evaluados['Nombre Completo_artificial_evaluado'].to_list()))
    df_feedback_detail_temp.drop(columns = ["Nombre Completo_artificial_evaluado","Nombre Completo_evaluado","DNI_evaluado"],inplace=True)
    df_feedback_detail_temp = pd.merge(df_feedback_detail_temp,df_evaluados[['Nombre Completo_artificial_evaluado','Nombre Completo_evaluado','DNI_evaluado']],left_on='Nombre Completo_artificial',right_on='Nombre Completo_artificial_evaluado',how='left') # Usamos el nombre
    # no process only to show
    df_feedback_replace_names = df_feedback_detail_temp[["variable","Nombre Completo_evaluado"]]
    df_feedback_replace_names = df_feedback_replace_names.drop_duplicates()
    df_feedback_replace_names.rename(columns={"variable":"Nombre detectado en Alchemer","Nombre Completo_evaluado":"Nombre aproximado en HC"},inplace=True)

    df_feedback = pd.concat([df_feedback_detail,df_feedback_detail_temp],ignore_index=True)

    # MERGE -> EVALUADOR
    df_feedback = pd.merge(df_feedback,df_evaluador[['Nombre Completo_evaluador','DNI_evaluador']],left_on='DNI_evaluador',right_on='DNI_evaluador',how='left') # Cruzamos DNI evaluador
    df_feedback = df_feedback.drop(columns=["Nombre Completo_artificial","Nombre Completo_artificial_evaluado"])
    #----------------------------------------------------------------
    table_feedback = df_feedback.groupby(['Nombre Completo_evaluado'])['value'].apply(lambda x: ' | = | '.join(x))
    table_feedback = pd.DataFrame({'evaluados':table_feedback.index,'feedback':table_feedback.values})
    table_feedback['evaluados'] = table_feedback['evaluados'].str.strip()
    table_feedback = table_feedback.loc[~table_feedback.evaluados.str.contains('Sentiment',case=False)]
    table_feedback = pd.merge(table_feedback,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre

    # TRATAMIENTO PARA LOS VACIOS QUE NO HICIERON MERGE EXACTO
    # Aplicamos DIFFLIB SOLO A LOS NO MERGE

    table_temp = table_feedback[table_feedback['Nombre Completo_evaluado'].isnull()]
    table_temp = table_temp[['evaluados','feedback']]
    table_temp = table_temp.loc[~table_temp.evaluados.str.contains('Sentiment',case=False)]
    table_temp['evaluados'] = table_temp.evaluados.apply(lambda x:get_close(nombre=x, lista_nombres=df_evaluados['Nombre Completo_evaluado'].to_list()))
    table_temp = pd.merge(table_temp,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre

    # Concat no_merge_treatment + merge
    table_feedback.dropna(subset=['Nombre Completo_evaluado'],inplace=True)
    table_feedback = pd.concat([table_feedback,table_temp],ignore_index=True)

    #----------------------------------------------------------------
    # AGREGAR Q
    table_feedback = agregar_Q(table_feedback, year = year, Q = Q )

    df_feedback = agregar_Q(df_feedback, year = year, Q = Q )
    #----------------------------------------------------------------
    #ID TO CONNECT TABLES
    df_evaluaciones["ID"] = df_evaluaciones["DNI_evaluador"].apply(remove_float_str).astype(str) + "_" + df_evaluaciones["DNI_evaluado"].apply(remove_float_str).astype(str) +"_"+ df_evaluaciones["Periodo"].astype(str)
    df_evaluaciones["ID_2"] = df_evaluaciones["DNI_evaluador"].apply(remove_float_str).astype(str) + df_evaluaciones["Periodo"].astype(str)
    df_evaluaciones["ID_3"] = df_evaluaciones["DNI_evaluado"].astype(str) + df_evaluaciones["Periodo"].astype(str)
    df_evaluaciones["ID_3"] = df_evaluaciones["ID_3"].apply(remove_float_str).astype(str)
    df_feedback["ID"] = df_feedback["DNI_evaluador"].apply(remove_float_str).astype(str) +"_" + df_feedback["DNI_evaluado"].apply(remove_float_str).astype(str) +"_"+ df_feedback["Periodo"].astype(str)

    df_replace_names.reset_index(drop=True, inplace=True)
    df_feedback_replace_names.reset_index(drop=True, inplace=True)

    '''OUTPUT

    '''
    return [df_evaluaciones, table_feedback,df_feedback,df_replace_names,df_feedback_replace_names]

def validation_Q(df, year , Q):
    Periodo = str(year)+'-'+str(Q)
    if Periodo in list(df.Periodo):
        return True
    else:
        return False


def update(df_new, df_master_path):
    #print()
    year    = int(df_new.year.unique()[0])
    Q       = df_new.Q.unique()[0]
    Periodo = str(year)+'-'+str(Q)
    if os.path.isfile(df_master_path):
        df_master = pd.read_csv(str(df_master_path),encoding='utf-8')

        if validation_Q(df=df_new, year=year, Q=Q ):
            # Datos menos el periodo que ingreso
            df_master = df_master[~(df_master.Periodo==Periodo)]
            # concateno
            df_master.reset_index(drop=True,inplace=True)
            df_new.reset_index(drop=True,inplace=True)
            df_master = pd.concat([df_master,df_new],axis=0,ignore_index=True)

            df_master.to_csv(str(df_master_path),encoding='utf-8',index = False)
            return df_master

        else:
            df_master.reset_index(drop=True,inplace=True)
            df_new.reset_index(drop=True,inplace=True)
            df_master = pd.concat([df_master,df_new],axis=0,ignore_index=True)
            df_master.to_csv(str(df_master_path),encoding='utf-8',index = False)
            return df_master
    else:
        df_new.to_csv(str(df_master_path),encoding='utf-8',index = False)
        return df_new



def personal_reporting(df_evaluaciones,df_feedback,df_autoev,dni,columna_dni='DNI_evaluado'):

    # Retorn el Reporte Personal correspondiente a un DNI y Periodo Especifico.

    # PERIODOS ACTIVOS ACTUAL ULTIMO 4Q
    # periodo_list            = last_n_q(df = df_evaluaciones,n=4,columna_periodo='Periodo')
    # last_q = last_n_q(df = df_evaluaciones,n=1,columna_periodo='Periodo')
    # df_evaluaciones[columna_dni] = df_evaluaciones[columna_dni].astype(float)
    #print(dni)
    dni = int(dni)
    #print(type(dni))
    #print(df_evaluaciones[columna_dni])
    #filtramos el df_evaluaciones por dni
    df_evaluaciones[columna_dni] = df_evaluaciones[columna_dni].astype(int).values
    #print("df_evaluaciones", df_evaluaciones)
    df_evaluaciones_persona = df_evaluaciones[df_evaluaciones[columna_dni]==dni].copy()
    df_evaluaciones_persona["evaluados"] = df_evaluaciones_persona["evaluados"].values[0]
    #print("df_evaluaciones_persona", df_evaluaciones_persona)
    #MOSTRAMOS LOS ULTIMOS 4 RESULTADOS | n=4.
    df_evaluaciones_persona = df_evaluaciones_persona.loc[df_evaluaciones_persona['Periodo'].isin(last_n_q(df_evaluaciones_persona,n=4))]
    #print("df_evaluaciones_persona.loc", df_evaluaciones_persona)
    #print(df_evaluaciones_persona, len(df_evaluaciones_persona))
    table_score = df_evaluaciones_persona.groupby(['Periodo','evaluados','Pilar'],as_index=False)['value'].agg(['mean','count']).unstack()

    #print("table_score", table_score, len(table_score))
    # Normalizar Nombre de columnas
    table_score.columns = ['-'.join(col).strip() for col in table_score.columns.values]
    #print("table_score.columns", table_score.columns)
    table_score = table_score_order(table_score)
    #table_score = table_score[[table_score.columns[0], table_score.columns[4], table_score.columns[1], table_score.columns[5], table_score.columns[2], table_score.columns[6], table_score.columns[3], table_score.columns[7]]]
    #print("table_score.columns", table_score.columns)
    #print("table_score[[", table_score, len(table_score))
    mean_columns = [x for x in list(table_score.columns) if "mean" in x]
    table_score["Tu promedio"] = table_score.loc[:,mean_columns].mean(numeric_only=True,skipna=True,axis=1)
    #print("table_score[Tu promedio]", table_score["Tu promedio"]  )
    table_score = rename_count_mean_columns(table_score)
    #print("rename_count_mean_columns(table_score)", table_score)
    table_score.reset_index(inplace=True)

    try: table_score.drop(["evaluados"], axis = 1, inplace = True)
    except: pass
    #print("table_score", len(table_score))
    #table_score = table_score[table_score['Periodo'].isin(periodo_list)]

    # GROUP BY NIVEL OCUPACIONAL


    df_evaluaciones_persona_nivocu = df_evaluaciones_persona.loc[df_evaluaciones_persona['Periodo'].isin(last_n_q(df_evaluaciones_persona,n=1))]
    #print("df_evaluaciones_persona_nivocu", df_evaluaciones_persona_nivocu)
    table_score_by_nivocu = df_evaluaciones_persona_nivocu.groupby(['Periodo','evaluados','Nivel Ocupacional_evaluador','Pilar'])['value'].agg(['mean','count']).unstack()


    #print("check niveocu",table_score_by_nivocu)
    #print("---------")

    #print("table_score_by_nivocu", table_score_by_nivocu)
    # Normalizar Nombre de columnas
    table_score_by_nivocu.reset_index(inplace=True)
    table_score_by_nivocu.columns = ['-'.join(col).strip() for col in table_score_by_nivocu.columns.values]
    table_score_by_nivocu.rename(columns={'Periodo-':'Periodo','DNI_evaluado-':'DNI_evaluado','evaluados-':'evaluados'},inplace=True)

    #df_evaluaciones_persona_save = table_score_by_nivocu.copy()
    table_score_by_nivocu = table_score_order_nivocu(table_score_by_nivocu)


    #print(len(table_score_by_nivocu.columns), table_score_by_nivocu.columns)
    #print(table_score_by_nivocu)

    #print("table_score_by_nivocu = table_score_by_nivocu[[table_score_by_nivocu.columns[0], table_score_by_nivocu.columns[1], table_score_by_nivocu.columns[2], table_score_by_nivocu.columns[3], table_score_by_nivocu.columns[7], table_score_by_nivocu.columns[4], table_score_by_nivocu.columns[8], table_score_by_nivocu.columns[5], table_score_by_nivocu.columns[9], table_score_by_nivocu.columns[6], table_score_by_nivocu.columns[10]]]")
    table_score_by_nivocu = rename_count_mean_columns_nivocu(table_score_by_nivocu)
    #print("table_score_by_nivocu = rename_count_mean_columns(table_score_by_nivocu)")
    table_score_by_nivocu.rename(columns={"Nivel Ocupacional_evaluador-":"Nivel Ocupacional"},inplace=True)
    try: table_score_by_nivocu.drop(["evaluados"], axis = 1, inplace = True)
    except: pass
    #print("table_score_by_nivocu", len(table_score_by_nivocu))
    #print(table_score_by_nivocu.columns)

    #FEEDBACK PERSONAL

    #df_feedback[columna_dni] = df_feedback[columna_dni].astype(str)
    #print("feedback total len: ", len(df_feedback))
    df_feedback[columna_dni] = df_feedback[columna_dni].astype(int).values
    #print(df_feedback[columna_dni])
    #print(dni, type(dni))
    #if 40031813 in df_feedback[columna_dni]:#print("yes")
    #else: #print ("no")
    df_feedback_personal = df_feedback.loc[df_feedback[columna_dni]==int(dni)]
    #print("feedback len: ", len(df_feedback))
    df_feedback_personal = df_feedback_personal[["Periodo","feedback"]]
    #print("feedback len: ", len(df_feedback_personal))
    #arreglos de tabla para presentación
    df_feedback_personal = df_feedback_personal.pivot_table(index=['Periodo'],values='feedback',aggfunc=lambda x: ' '.join(x)).T.reset_index()
    df_feedback_personal.rename(columns={'index':''},inplace=True)
    #print("df_feedback_personal", len(df_feedback_personal))
    df_evaluaciones_persona = df_evaluaciones_persona.drop_duplicates(subset=['evaluados'],keep='last')

    # AUTOEVALUACION

    df_autoev_personal = df_autoev[df_autoev['DNI_evaluador']==int(dni)]
    #print(len(df_autoev_personal), df_autoev_personal)
    df_autoev_personal = df_autoev_personal[["Periodo", "Pilar", "value"]].pivot_table(index='Periodo', columns='Pilar', values='value', aggfunc='mean')
    #print("df_autoev_personal = df_autoev_personal[[...]].pivot(index='Periodo', columns='Pilar', values='value')")
    #df_autoev_personal = df_autoev_personal.rename(columns = {"value":"Autoevaluación"})
    df_autoev_personal.reset_index(inplace=True)
    df_autoev_personal = df_autoev_personal.loc[df_autoev_personal["Periodo"]>="2020-Q4"]
    #print("df_autoev_personal.reset_index(inplace=True)")
    df_autoev_personal.columns.name = ""
    df_autoev_personal["Tu promedio"] = df_autoev_personal.mean(numeric_only=True,skipna=True,axis=1)

    #Datos Personales
    df_evaluaciones_persona = df_evaluaciones_persona.tail(1)[['DNI_evaluado','Nombre Completo_evaluado','Sector_evaluado','Descripción Puesto_evaluado']]
    df_evaluaciones_persona.rename(columns={'DNI_evaluado':'DNI','Nombre Completo_evaluado':'Nombre Completo','Sector_evaluado':'Area','Descripción Puesto_evaluado':'Puesto'},inplace=True)


    #Promedio General por periodo
    df_evaluaciones_q = df_evaluaciones.groupby(['Periodo','Pilar']).mean().iloc[:,0:1].reset_index()
    df_evaluaciones_q = df_evaluaciones.reset_index().pivot_table(index=['Periodo'],values='value',columns='Pilar').reset_index()
    #holi = df_evaluaciones_q.loc[:,["Buscamos la excelencia","Vivimos y disfrutamos"]].mean(axis=0)
    df_evaluaciones_q["Promedio Crosland"] = df_evaluaciones_q.mean(numeric_only=True,skipna=True,axis=1)

    #row_1 = pd.DataFrame([df_evaluaciones_q.reset_index().columns.to_list()],columns=df_evaluaciones_q.reset_index().columns.to_list())
    #df_evaluaciones_q = row_1.append(df_evaluaciones_q).T
    #df_evaluaciones_q = df_evaluaciones_q.pivot_table(index=['Pilar'],values='value',columns='Periodo').T
    periodos = list(table_score_by_nivocu.Periodo)
    for i in range(1,len(periodos)):
        if periodos[i] == list(table_score_by_nivocu.Periodo)[i-1]:
            periodos[i]=""
    table_score_by_nivocu["Periodo"] = periodos

    '''

    OUTPUT

    # table_score: Puntaje Personal por Pilar de cada Q
    # table_score_by_nivocu

    '''
    #print("final personal_reporting")
    return df_evaluaciones_persona,df_evaluaciones_q,table_score,table_score_by_nivocu,df_feedback_personal,df_autoev_personal

def table_score_order(table_score):
    n = len(table_score.columns)
    #print(n)
    n_mid = n//2
    #print(n_mid)
    columns = []
    columns_all = list(table_score.columns)
    #print(columns)
    for i in range(n-n_mid):
        #print(i)
        #print(columns_all[i])
        columns.append(columns_all[i])
        #print(columns_all[i+n_mid])
        columns.append(columns_all[i+n_mid])
    #print(columns)
    table_score = table_score[columns]
    return table_score

def table_score_order_nivocu(table_score):

    columns = [x for x in table_score.columns if ("mean" in x ) or ("count" in x)]#list(table_score.columns[0:n_mid])
    columns_all = [x for x in table_score.columns if x not in columns]#list(table_score.columns)
    #print(columns)
    n = len(columns)
    #print(n)
    n_mid = n//2
    #print(n_mid)

    for i in range(n_mid):
        # #print(i)
        # #print(columns[i])
        columns_all.append(columns[i])
        # #print(columns[i+n_mid])
        columns_all.append(columns[i+n_mid])
    #print(columns)
    table_score = table_score[columns_all]
    return table_score

def build_password_df(DNIs):
    #print(DNIs)
    df_dnis = pd.DataFrame(DNIs, columns = ["DNI"])
    #print(df_dnis)
    df_dnis["password"] = df_dnis["DNI"].apply(tokenizar)
    df_dnis["password"] = df_dnis["password"].apply(lambda x: x[1:-1] if x[0] in ["+", "-", "="] else x[:-1])
    df_dnis["password"] = df_dnis["password"]
    #print(df_dnis["password"])
    return df_dnis


def rename_count_mean_columns_nivocu(df):
    #print("rename_count_mean_columns")
    mean_columns = [x for x in df.columns if "mean" in x]
    count_columns = [x for x in df.columns if "count" in x]
    nivocu_columns = [x for x in df.columns if "Nivel Ocupacional_evaluador-" in x]

    new_mean_columns = [x.replace("mean-", "") for x in mean_columns]
    new_count_columns = ["# evaluadores" for x in count_columns]
    new_nivocu_columns = [x.replace("Nivel Ocupacional_evaluador-","Nivel Ocupacional") for x in nivocu_columns]

    zip_dict_columns = zip(mean_columns+count_columns+nivocu_columns, new_mean_columns+new_count_columns+new_nivocu_columns)
    dict_columns = dict(zip_dict_columns)
    #print(dict_columns)

    df = df.rename(columns = dict_columns)
    #print(df)
    #print("final")
    return df

def rename_count_mean_columns(df):
    #print("rename_count_mean_columns")
    mean_columns = [x for x in df.columns if "mean" in x]
    count_columns = [x for x in df.columns if "count" in x]

    new_mean_columns = [x.replace("mean-", "") for x in mean_columns]
    new_count_columns = ["# evaluadores" for x in count_columns]

    zip_dict_columns = zip(mean_columns+count_columns, new_mean_columns+new_count_columns)
    dict_columns = dict(zip_dict_columns)
    #print(dict_columns)

    df = df.rename(columns = dict_columns)
    #print(df)
    #print("final")
    return df

def finder_critical_evaluator(df_results, on="",id_evaluator="DNI_evaluador",id_evaluated="DNI_evaluado",id_value="value",id_periodo="Periodo"):

    critical_table = df_results.groupby([id_periodo,id_evaluator,id_evaluated])[id_value].agg('mean')
    critical_table = critical_table.reset_index()
    #
    scores = critical_table.value
    critical_table['satisfaction_lvl'] = ["Insatisfecho" if score<45 else "Neutro" if score>46 and score<65 else "Satisfecho" for score in scores ]

    # Counting by satisfaction lvl TABLE
    critical_table = critical_table.groupby([id_periodo,id_evaluator,'satisfaction_lvl']).count()
    critical_table = critical_table.reset_index()
    critical_table.drop(columns=id_evaluated,inplace=True)

    evaluator_satisfied_count = critical_table.pivot_table(index=[id_periodo,id_evaluator],columns='satisfaction_lvl',values='value').reset_index()
    evaluator_satisfied_count = evaluator_satisfied_count.fillna(0)
    evaluator_satisfied_count["total"] = evaluator_satisfied_count["Insatisfecho"] + evaluator_satisfied_count["Neutro"] + evaluator_satisfied_count["Satisfecho"]

    evaluator_satisfied_count["porcent_unsatisfied"] = evaluator_satisfied_count["Insatisfecho"] / evaluator_satisfied_count["total"]
    evaluator_satisfied_count['critical_label'] = ["Muy Crítico" if porcent>0.8 else "Critico" if porcent<0.8 and porcent>0.5 else "Moderado" if porcent<0.5 and porcent>0.3 else "Normal" for porcent in evaluator_satisfied_count.porcent_unsatisfied ]

    evaluator_satisfied_count['ID_2'] = evaluator_satisfied_count['DNI_evaluador'].astype(str) + evaluator_satisfied_count['Periodo'].astype(str)
    evaluator_satisfied_count = evaluator_satisfied_count.merge(df_results[["ID_2", "year", "Q"]], on="ID_2", how="left")
    evaluator_satisfied_count = evaluator_satisfied_count.drop_duplicates(subset=["ID_2"])

    return evaluator_satisfied_count

def DNI_PDF_format(x, tipo_doc):
    try:
        if tipo_doc=="DNI" or str(tipo_doc)=="nan":
            str_DNI = str(x)

            n_zeros = 8 - len(str(str_DNI))
            zeros = "0"*n_zeros
            str_DNI = zeros+str_DNI
            return str_DNI
        else:
            return str(x)
    except:
            return str(x)

def try_int_str(x):
    try: str(int(x))
    except: str(x)

    return x


def remove_float_str(x):
    try:
        x = str(x)
        x = x.replace(".0","")
        return x
    except: return x

#%%
# #Testing Zone Script

# df_colaboradores = pd.read_excel("input/HC Setiembre.xlsx",sheet_name="HC SET")
# df_survey = pd.read_csv("input/Output_360_Q3.csv")
# df_survey = df_survey.rename(columns={"¿Cuál es tu DNI?Esta información será utilizada exclusivamente para procesar la data y la finalidad es poder hacer seguimiento de quienes han completado la encuesta. Los resultados serán confidenciales y tu evaluación hacia los otros también.":"DNI"})

# Q="Q3"
# year = "2020"

# df_results = pd.read_csv("output/df_results.csv")
# df_results["ID_3"] = df_results["ID_3"].apply(remove_float_str).astype(str)
# df_results.to_csv("output/df_results.csv",index=False)


# autoev = df_split(df_survey, df_colaboradores, columna_documento_colaboradores='Numero documento')[0]
# autoev = agregar_Q(autoev, year=2020, Q="Q3")
# update(autoev,"output/df_autoev.csv")

# results = auto360(df_survey,df_colaboradores,year,Q,columna_documento_colaboradores='Numero documento')
# #%%
# #autoev = df_split(df_survey, df_colaboradores, columna_documento_colaboradores='Numero documento')
# update(autoev,"output/df_autoev.csv")
# update(results[0],"output/df_results.csv")
# update(results[1],"output/df_feedback.csv")
# update(results[2],"output/df_feedback_detail.csv")
# #%%
# df_survey = pd.read_csv("input/Output_360_Q2.csv")
# df_colaboradores = pd.read_excel("input/HC Junio.xlsx",sheet_name="HC JUNIO")
# year = "2020"
# Q="Q2"


# autoev = df_split(df_survey, df_colaboradores, columna_documento_colaboradores='Numero documento')[0]
# autoev = agregar_Q(autoev, year=2020, Q="Q2")
# update(autoev,"output/df_autoev.csv")

# results = auto360(df_survey,df_colaboradores,year,Q,columna_documento_colaboradores='Numero documento')
#%%

# update(autoev,"output/df_autoev.csv")
# update(results[0],"output/df_results.csv")
# update(results[1],"output/df_feedback.csv")
# update(results[2],"output/df_feedback_detail.csv")
# #results[0].to_excel("results/df_results.xlsx")
#%%
# df_results = pd.read_csv("output/df_results.csv")
# df_feedback = pd.read_csv("output/df_feedback.csv")
# df_autoev = pd.read_csv("output/df_autoev.csv")

# #%%
# #finder debe correrse luego de realizar Update a todas las df
# finder_critical = finder_critical_evaluator(df_results,"DNI_evaluador","DNI_evaluado","value","Periodo")
# finder_critical.to_csv("output/critical_table.csv",index=False)
# #%%

# personal = personal_reporting(df_results,df_feedback=df_feedback,df_autoev=df_autoev,dni='72635322',columna_dni='DNI_evaluado')
#%%
# df_results = pd.read_csv("data/df_results(3).csv")
# df_results = df_results.loc[df_results["Periodo"]=="2020-Q2"]
# # for i in df_results["evaluados"]
# df_results = df_results[ df_results["evaluados"]=="Luz Gissella Ruiz Flores"]
# #print(len(df_results["DNI_evaluador"].unique()))
