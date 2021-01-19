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
# ##EJEMPLO DE EJECUCION
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
# ##=======================FUNCIONES===============================##
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
    yearQ = year+'-'+Q
    df['Periodo'] = yearQ
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

def df_split(df_survey):
    # Contiene DNI del evaluador -> Autoevaluador
    col_autoev = df_survey.columns[df_survey.columns.str.contains('DNI|Autoevaluac',regex=True)]
    # Contiene Preguntas de Autoevaluacion

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

    df_autoev.loc[df_autoev['value'] == 0,'value'] = 0 #Conversion especial de puntaje vacío
    df_autoev.loc[df_autoev['value'] == 1,'value'] = 20
    df_autoev.loc[df_autoev['value'] == 2,'value'] = 40
    df_autoev.loc[df_autoev['value'] == 3,'value'] = 60
    df_autoev.loc[df_autoev['value'] == 4,'value'] = 80
    df_autoev.loc[df_autoev['value'] == 5,'value'] = 100

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

    #Critico
    df_survey = df_survey.loc[df_survey['Status']=='Complete']

    survey=df_survey.copy()

    df_survey = df_survey.iloc[:,19:columns_len]
    df_survey = df_survey.loc[:,~df_survey.columns.str.contains('que has trabajado los últimos tres meses',case=False)]

    ##print('DNI_Unicos_Evaluadores: '+str(len(df_survey['DNI_evaluador'].unique()))) # Punto de revision

    # Formateo de DNI

    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].astype(str)
    #df_survey['DNI_evaluador'].replace({'nan':None},inplace=True)
    #df_survey['DNI_evaluador'] = pd.to_numeric(df_survey['DNI_evaluador'],errors='ignore')
    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].astype(int)
    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].astype(str)

    ##print(type(df_survey.DNI_evaluador))
    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].apply(dni_format)

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
    # df_que_es = pd.DataFrame(df_melt.que_es.str.split(':',expand=True)[0], columns = ['pilar','basura'])

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

    ##print('# DNI unico Evaluadores - pre merge: '+str(len(df_values['DNI_evaluador'].unique())))  # Punto de revision




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

    df_colaboradores.rename(columns={columna_documento_colaboradores:'DNI'},inplace=True)
    df_colaboradores['DNI'] = df_colaboradores["DNI"].astype(str)

    #Eliminamos filas con contenido vacio
    df_colaboradores.drop(df_colaboradores[df_colaboradores.DNI.isnull()].index, inplace = True)
    df_colaboradores.drop(df_colaboradores[df_colaboradores.DNI=='nan'].index, inplace = True)

    df_colaboradores['Nombre Completo'] = df_colaboradores['Nombre Completo'].apply(cambioorden_nombre_apellido)
    df_colaboradores['Nombre Completo'] = df_colaboradores['Nombre Completo'].apply(capitalizar_nombre)

    df_colaboradores['DNI'] = pd.to_numeric(df_colaboradores['DNI'],errors='ignore')
    df_colaboradores['DNI'] = df_colaboradores['DNI'].astype(int)

    #df_colaboradores['DNI'] = df_colaboradores['DNI'].apply(dni_format)

    # =============================================================================
    #     Agregamos Informacion para Evaluados y Evaluados
    # =============================================================================
    # Copia para cada df EVALUADO vs EVALUADOR

    df_evaluador = df_colaboradores.copy()
    df_evaluados = df_colaboradores.copy()

    # Le damos formato segun necesidad
    ### EVALUADOR | Aquel que evalua a otros
    #df_evaluador.rename(columns={'DNI':'DNI_evaluador'},inplace=True)
    # del evaluador solo necesitamos los stes campos
    df_evaluador = df_evaluador[['DNI','Nombre Completo','Unidad','Area','Sector','Nivel Ocupacional']]
    #Agregamos el identificador _evaluador
    df_evaluador.columns = [str(col) + '_evaluador' for col in df_evaluador.columns]

    ### EVALUADO | Aquel que recibe una puntacion segun opiniones de otros
    #OBS: Del Evaluado no tenemos DNI! solo nombre, hagamos match con el nombre
    #Agregamos el identificador _evaluado
    df_evaluados.columns = [str(col) + '_evaluado' for col in df_evaluados.columns]
    # De momento aceptaremos todos los campos

    # =============================================================================
    #     COMPLEMENTAMOS INFORMACION >>>EVALUADOS & EVALUADOR
    # =============================================================================
    # #print(len(df_values['evaluados']))

    # MERGUE EVALUADO # PROBANDO LEFT

    df_complete = pd.merge(df_values,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre
    ##print(len(df_complete['Nombre Completo_evaluado'].unique()))

    #df_complete = pd.merge(df_complete,df_evaluador,right_on='DNI_evaluador',left_on='DNI_evaluador',how='left') # usamos el DNI

    # MERGUE EVALUADOR # PROBANDO LEFT
    df_complete = pd.merge(df_complete,df_evaluador,on='DNI_evaluador',how='left') # usamos el DNI

    ####
    # =============================================================================
    # DIFFLIB MAGIC # TRATAMIENTO de los que no hicieron merge
    # =============================================================================
    # Borramos los datos que no hicieron merge

    ##print('test')
    df_complete_temp = df_complete[df_complete['Nombre Completo_evaluado'].isnull()]
    ##print(df_complete_temp)
    df_complete_temp = df_complete_temp[['DNI_evaluador','evaluados','value','que_es']]

    df_complete_temp = df_complete_temp.loc[~df_complete_temp.evaluados.str.contains('Sentiment',case=False)]

    df_complete_temp['evaluados'] = df_complete_temp.evaluados.apply(lambda x:get_close(nombre=x, lista_nombres=df_evaluados['Nombre Completo_evaluado'].to_list()))
    df_complete_temp = pd.merge(df_complete_temp,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre
    df_complete_temp = pd.merge(df_complete_temp,df_evaluador,on='DNI_evaluador',how='left') # usamos el DNI
    ##print(table_temp)
    ##print(df_complete_temp)
    # Concatenamos los null tratados y completados
    # #print('test')
    df_complete.dropna(subset = ['DNI_evaluado'],inplace=True)

    df_complete = pd.concat([df_complete,df_complete_temp],ignore_index=True)


    # Filtro para excluir algún área en el procesamiento del Score
    # =============================================================================
    #     # COMPLEMENTANDO INFORMACIÓN DE EVALUADO
    # =============================================================================

    # Eliminando Nan
    df_complete.drop(df_complete[df_complete.evaluados.isnull()].index, inplace = True)

    # Regla 1 Para la misma ORG. su Score
    ##df_complete_whitout_filter = df_complete.drop(df_complete[df_complete['Unidad de Negocio']=='Wuf'].index)

    # Regla 3 | Filtro CTMR
    # Elimina las Autoevaluaciones

    df_complete = df_complete[df_complete['Nombre Completo_evaluador']!=df_complete['Nombre Completo_evaluado']]

    # Treatment df_values

    df_complete['value'] = pd.to_numeric(df_complete['value'],errors='coerce')
    df_complete.drop(df_complete[df_complete.value.isnull()].index, inplace = True)
    df_complete.rename(columns={'que_es':'Pilar'},inplace=True)


    # From variable year & Q
    periodo = str(year)+'-'+str(Q)
    ##print('test')
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

    df_complete.loc[df_complete.groupby(['DNI_evaluador','Pilar','DNI_evaluado']).value.max == df_complete.value]

    df_complete.drop(['Nombre Completo_evaluador'],axis=1,inplace=True)

    #TOKENIZAR DNI
    #df_complete['DNI_evaluador'] = df_complete['DNI_evaluador'].apply(tokenizar)
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
    #survey copia del df_survey
    df_feedback = survey[survey.columns[survey.columns.str.contains('mejorar')]]
    df_feedback = df_feedback.melt()
    df_feedback=df_feedback.dropna(axis=0)
    #split
    df_feedback.variable = df_feedback.variable.str.split(':|¿|,',expand=True)[0]
    table_feedback = df_feedback.groupby(['variable'])['value'].apply(lambda x: ' | = | '.join(x))

    #--------------------
    #df_feedback= df_feedback[df_feedback['evaluados'].str.contains(r'mejorar')]
    #df_feedback.value = df_feedback.value.astype(str)
    #df_feedback.evaluados = df_melt.evaluados.str.split('¿',expand=True)[0]
    #table_feedback = df_feedback.groupby(['evaluados'])['value'].apply(lambda x: ' | = | '.join(x))
    #---
    # Convertir el group by to Dataframe

    table_feedback = pd.DataFrame({'evaluados':table_feedback.index,'feedback':table_feedback.values})
        #
    table_feedback['evaluados'] = table_feedback['evaluados'].str.strip()
        #
    table_feedback = table_feedback.loc[~table_feedback.evaluados.str.contains('Sentiment',case=False)]
        #
    table_feedback = pd.merge(table_feedback,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre

    # TRATAMIENTO PARA LOS VACIOS QUE NO HICIERON MERGE EXACTO
    # Aplicamos DIFFLIB SOLO A LOS NO MERGE
        # table_temp
    table_temp = table_feedback[table_feedback['Nombre Completo_evaluado'].isnull()]
    table_temp = table_temp[['evaluados','feedback']]
    table_temp = table_temp.loc[~table_temp.evaluados.str.contains('Sentiment',case=False)]
    table_temp['evaluados'] = table_temp.evaluados.apply(lambda x:get_close(nombre=x, lista_nombres=df_evaluados['Nombre Completo_evaluado'].to_list()))
    table_temp = pd.merge(table_temp,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre

    # Concatenamos los null tratados y completados
    table_feedback.dropna(subset=['Nombre Completo_evaluado'],inplace=True)
    table_feedback = pd.concat([table_feedback,table_temp],ignore_index=True)
    # AGREGAR Q
    table_feedback = agregar_Q(table_feedback, year = year, Q = Q )
    # =============================================================================
    # TO GENERAL REPORT
    # =============================================================================
    # Headers : DNI +| Nombre+ | Nivel Ocupacional +| Peso~ | Unidad de Negocio +| Area +
    #           Puesto +| Jefe Directo * | Sede +| Fecha de Ingreso +| Score-'nombre del pilar'~ |Count-'nombre del pilar' ~
    #           Periodo ~ | Sexo +| Fecha de Nacimiento +| Edad ~| Promedio General ~ | # Evaluadores ~ | Rango de Edad ~
    # * No es proveido ni obtenido de manera artificial
    # ~ Variables obtenidas por procesamiento
    # + Varibales obtenidas desde la BD de Colaboradores

    '''OUTPUT
    # df_complete
    # table_feedback
    '''
    return [df_evaluaciones, table_feedback]


def validation_Q(df, year , Q):
    Periodo = str(year)+'-'+str(Q)
    if Periodo in list(df.Periodo):
        return True
    else:
        return False


def update(df_new, df_master_path):
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

    dni = int(dni)
    #print(dni)
    #print(df_evaluaciones[columna_dni])
    #filtramos el df_evaluaciones por dni
    df_evaluaciones[columna_dni] = df_evaluaciones[columna_dni].astype(int).values
    df_evaluaciones_persona = df_evaluaciones[df_evaluaciones[columna_dni]==dni].copy()
    #MOSTRAMOS LOS ULTIMOS 4 RESULTADOS | n=4.
    df_evaluaciones_persona = df_evaluaciones_persona.loc[df_evaluaciones_persona['Periodo'].isin(last_n_q(df_evaluaciones_persona,n=4))]

    #print(df_evaluaciones_persona, len(df_evaluaciones_persona))
    table_score = df_evaluaciones_persona.groupby(['Periodo','evaluados','Pilar'],as_index=False)['value'].agg(['mean','count']).unstack()
    #print(table_score, len(table_score))
    # Normalizar Nombre de columnas
    table_score.columns = ['-'.join(col).strip() for col in table_score.columns.values]
    table_score = table_score[[table_score.columns[0], table_score.columns[4], table_score.columns[1], table_score.columns[5], table_score.columns[2], table_score.columns[6], table_score.columns[3], table_score.columns[7]]]
    #print(table_score, len(table_score))
    table_score = rename_count_mean_columns(table_score)
    table_score.reset_index(inplace=True)
    try: table_score.drop(["evaluados"], axis = 1, inplace = True)
    except: pass
    #print("table_score", len(table_score))
    #table_score = table_score[table_score['Periodo'].isin(periodo_list)]

    # GROUP BY NIVEL OCUPACIONAL

    table_score_by_nivocu = df_evaluaciones_persona.groupby(['Periodo','evaluados','Nivel Ocupacional_evaluador','Pilar'])['value'].agg(['mean','count']).unstack()
    # Normalizar Nombre de columnas
    table_score_by_nivocu.reset_index(inplace=True)
    table_score_by_nivocu.columns = ['-'.join(col).strip() for col in table_score_by_nivocu.columns.values]
    #print("table_score_by_nivocu.columns = ['-'.join(col).strip() for col in table_score_by_nivocu.columns.values]")

    table_score_by_nivocu.rename(columns={'Periodo-':'Periodo','DNI_evaluado-':'DNI_evaluado','evaluados-':'evaluados'},inplace=True)
    #print("table_score_by_nivocu.rename(columns={'Periodo-':'Periodo','DNI_evaluado-':'DNI_evaluado','evaluados-':'evaluados'},inplace=True)")
    table_score_by_nivocu = table_score_by_nivocu[[table_score_by_nivocu.columns[0], table_score_by_nivocu.columns[1], table_score_by_nivocu.columns[2], table_score_by_nivocu.columns[3], table_score_by_nivocu.columns[7], table_score_by_nivocu.columns[4], table_score_by_nivocu.columns[8], table_score_by_nivocu.columns[5], table_score_by_nivocu.columns[9], table_score_by_nivocu.columns[6], table_score_by_nivocu.columns[10]]]
    #print("table_score_by_nivocu = table_score_by_nivocu[[table_score_by_nivocu.columns[0], table_score_by_nivocu.columns[1], table_score_by_nivocu.columns[2], table_score_by_nivocu.columns[3], table_score_by_nivocu.columns[7], table_score_by_nivocu.columns[4], table_score_by_nivocu.columns[8], table_score_by_nivocu.columns[5], table_score_by_nivocu.columns[9], table_score_by_nivocu.columns[6], table_score_by_nivocu.columns[10]]]")
    table_score_by_nivocu = rename_count_mean_columns(table_score_by_nivocu)
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
    #if 40031813 in df_feedback[columna_dni]:print("yes")
    #else: print ("no")
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
    #autoev[autoev['DNI_evaluador']==40646048]
    #df_autoev[columna_dni] = df_autoev['DNI_evaluador'].astype(int).astype(str)
    #print(len(df_autoev), df_autoev)
    df_autoev_personal = df_autoev[df_autoev['DNI_evaluador']==int(dni)]
    #print(len(df_autoev_personal), df_autoev_personal)
    df_autoev_personal = df_autoev_personal[["Periodo", "Pilar", "value"]].pivot_table(index='Periodo', columns='Pilar', values='value', aggfunc='mean')
    #print("df_autoev_personal = df_autoev_personal[[...]].pivot(index='Periodo', columns='Pilar', values='value')")
    #df_autoev_personal = df_autoev_personal.rename(columns = {"value":"Autoevaluación"})
    df_autoev_personal.reset_index(inplace=True)
    df_autoev_personal = df_autoev_personal.loc[df_autoev_personal["Periodo"]>="2020-Q4"]
    #print("df_autoev_personal.reset_index(inplace=True)")
    df_autoev_personal.columns.name = ""

    #Datos Personales
    df_evaluaciones_persona = df_evaluaciones_persona.tail(1)[['DNI_evaluado','Nombre Completo_evaluado','Area_evaluado','Descripción Puesto_evaluado']]
    df_evaluaciones_persona.rename(columns={'DNI_evaluado':'DNI','Nombre Completo_evaluado':'Nombre Completo','Area_evaluado':'Area','Descripción Puesto_evaluado':'Puesto'},inplace=True)

    #Promedio General por periodo
    df_evaluaciones_q = df_evaluaciones.groupby(['Periodo','Pilar']).mean().iloc[:,0:1].reset_index()
    df_evaluaciones_q = df_evaluaciones.reset_index().pivot_table(index=['Periodo'],values='value',columns='Pilar').reset_index()
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
    print("final personal_reporting")
    return df_evaluaciones_persona,df_evaluaciones_q,table_score,table_score_by_nivocu,df_feedback_personal,df_autoev_personal


def build_password_df(DNIs):
    #print(DNIs)
    df_dnis = pd.DataFrame(DNIs, columns = ["DNI"])
    #print(df_dnis)
    df_dnis["password"] = df_dnis["DNI"].apply(tokenizar)
    df_dnis["password"] = df_dnis["password"].apply(lambda x: x[1:-1] if x[0] in ["+", "-", "="] else x[:-1])
    df_dnis["password"] = df_dnis["password"]
    #print(df_dnis["password"])
    return df_dnis


def rename_count_mean_columns(df):
    #print("rename_count_mean_columns")
    mean_columns = [x for x in df.columns if "mean" in x]
    count_columns = [x for x in df.columns if "count" in x]
    nivocu_columns = [x for x in df.columns if "Nivel Ocupacional_evaluador-" in x]

    new_mean_columns = [x.replace("mean-", "") for x in mean_columns]
    new_count_columns = ["# evaluadores" for x in count_columns]
    new_nivocu_columns = [x.replace("Nivel Ocupacional_evaluador-","Rango") for x in nivocu_columns]

    zip_dict_columns = zip(mean_columns+count_columns+nivocu_columns, new_mean_columns+new_count_columns+new_nivocu_columns)
    dict_columns = dict(zip_dict_columns)
    #print(dict_columns)

    df = df.rename(columns = dict_columns)
    #print(df)
    #print("final")
    return df

def try_int_str(x):
    try: str(int(x))
    except: str(x)

    return x
