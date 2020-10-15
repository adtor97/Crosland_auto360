import pandas as pd
from datetime import datetime, timedelta
import math
from itsdangerous import Signer
from difflib import get_close_matches


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
# personal_reporting(df_complete=holi[0],df_feedback=holi[1],dni='40646048',columna_dni='DNI_evaluado')


# =============================================================================
# ##=======================FUNCIONES===============================##
# =============================================================================

def capitalizar_nombre(message):
    message = str(message)
    capitalized_message = " ".join([word.capitalize() for word in message.split(" ")])
    return capitalized_message

def tokenizar(dni):
    #print(type(dni))
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
    return "%d-Q%d" % (d.year,math.ceil(d.month/3)-1)

def auto360(df_survey,df_colaboradores,columna_documento_colaboradores='Numero documento'):
    #Seccion Tratamiento de Respuestas 360
    # df_survey : Es el CSV que arroja Survey Gizmo de la encuesta 360
    # df_colaboradores: es (excel) de colaboradores con sus datos personales
    #                   este aun falta actualizarse para leer los datos del archivo que arroja en bruto su sistema de RRHH
    #df = pd.read_csv(df_survey,encoding='utf-8')
    df_survey.rename(columns={'¿Cuál es tu DNI?Esta información será utilizada exclusivamente para procesar la data y la finalidad es poder hacer seguimiento de quienes han completado la encuesta. Los resultados serán confidenciales y tu evaluación hacia los otros también.':'DNI_evaluador'},inplace=True)

    # Limpieza y Estructuración de data
    columns_len = df_survey.shape[1]

    #Critico
    df_survey = df_survey.loc[df_survey['Status']=='Complete']

    df_survey = df_survey.iloc[:,19:columns_len]
    df_survey = df_survey.loc[:,~df_survey.columns.str.contains('que has trabajado los últimos tres meses',case=False)]
    #print('DNI_Unicos_Evaluadores: '+str(len(df_survey['DNI_evaluador'].unique())))

    # Formateo de DNI

    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].astype(str)
    #df_survey['DNI_evaluador'].replace({'nan':None},inplace=True)
    #df_survey['DNI_evaluador'] = pd.to_numeric(df_survey['DNI_evaluador'],errors='ignore')
    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].astype(int)
    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].astype(str)

    #print(type(df_survey.DNI_evaluador))
    #df_survey['DNI_evaluador'] = df_survey['DNI_evaluador'].apply(dni_format)

    df_melt = pd.melt(df_survey,id_vars='DNI_evaluador',var_name='evaluados')

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
    #df_values.drop(no_df_value_index,inplace=True)

    #df_values['value'] = pd.to_numeric(df_values['value'],errors='coerce')
    #df_values.drop(df_values[df_values.value.isnull()].index, inplace = True)
    df_values.drop_duplicates(subset=['DNI_evaluador','evaluados','que_es'],keep='first')
    #print('# DNI unico Evaluadores - pre merge: '+str(len(df_values['DNI_evaluador'].unique())))
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
    ###df_croslanderos = pd.read_excel(df_survey,sheet_name='BD',dtypes={'DNI':str})

    df_colaboradores.rename(columns={columna_documento_colaboradores:'DNI'},inplace=True)
    df_colaboradores['DNI'] = df_colaboradores.DNI.astype(str)

    #Eliminamos filas con contenido vacio
    df_colaboradores.drop(df_colaboradores[df_colaboradores.DNI.isnull()].index, inplace = True)
    df_colaboradores.drop(df_colaboradores[df_colaboradores.DNI=='nan'].index, inplace = True)

    df_colaboradores['Nombre Completo'] = df_colaboradores['Nombre Completo'].apply(cambioorden_nombre_apellido)
    #df_colaboradores['Nombre Completo'].apply(cambioorden_nombre_apellido)
    df_colaboradores['Nombre Completo'] = df_colaboradores['Nombre Completo'].apply(capitalizar_nombre)

    df_colaboradores['DNI'] = pd.to_numeric(df_colaboradores['DNI'],errors='ignore')
    df_colaboradores['DNI'] = df_colaboradores['DNI'].astype(int)

    #df_colaboradores['DNI'] = df_colaboradores['DNI'].apply(dni_format)

    # Obtenemos nombre cercanos
    # Recordamos que los nombres obtenidos de los evaluados en Survey se ingresa manualmente
    # Obtendremos con diff lib los nombre mas cecanos a los de la base de datos.



    #PROBANDO
    #df_values['evaluados'] = df_values['evaluados'].apply(lambda x:get_close(nombre=x, lista_nombres=df_colaboradores['Nombre Completo'].to_list()))

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
    # print(len(df_values['evaluados']))

    # MERGUE EVALUADO # PROBANDO LEFT

    df_complete = pd.merge(df_values,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre
    #print(len(df_complete['Nombre Completo_evaluado'].unique()))

    #df_complete = pd.merge(df_complete,df_evaluador,right_on='DNI_evaluador',left_on='DNI_evaluador',how='left') # usamos el DNI

    # MERGUE EVALUADOR # PROBANDO LEFT
    df_complete = pd.merge(df_complete,df_evaluador,on='DNI_evaluador',how='left') # usamos el DNI

    ####
    # tratamiento de los que no hicieron merge
    # Borramos los datos que no hicieron merge


    df_complete_temp = df_complete[df_complete['Nombre Completo_evaluado'].isnull()]

    df_complete_temp = df_complete_temp[['DNI_evaluador','evaluados','value','que_es']]

    df_complete_temp = df_complete_temp.loc[~df_complete_temp.evaluados.str.contains('Sentiment',case=False)]

    df_complete_temp['evaluados'] = df_complete_temp.evaluados.apply(lambda x:get_close(nombre=x, lista_nombres=df_evaluados['Nombre Completo_evaluado'].to_list()))

    df_complete_temp = pd.merge(df_complete_temp,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre
    df_complete_temp = pd.merge(df_complete_temp,df_evaluador,on='DNI_evaluador',how='left') # usamos el DNI
    #print(table_temp)
    #print(df_complete_temp)
    # Concatenamos los null tratados y completados

    df_complete.dropna(subset = ['DNI_evaluado'],inplace=True)

    df_complete = pd.concat([df_complete,df_complete_temp],ignore_index=True)


    # Filtro para excluir algún área en el procesamiento del Score
    # COMPLEMENTANDO INFORMACIÓN DE EVALUADO

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



    # RE - ESCALA [1-5] -> [0-100]

    df_complete.loc[df_complete['value'] == 1,'value'] = 0
    df_complete.loc[df_complete['value'] == 2,'value'] = 25
    df_complete.loc[df_complete['value'] == 3,'value'] = 50
    df_complete.loc[df_complete['value'] == 4,'value'] = 75
    df_complete.loc[df_complete['value'] == 5,'value'] = 100
    #df_complete.loc[df_complete['value']>=75,'status'] = 'Satisfecho'
    #df_complete.loc[df_complete['value']<75,'status'] = 'No Satisfecho'
    df_complete.loc[df_complete.groupby(['DNI_evaluador','Pilar','DNI_evaluado']).value.max == df_complete.value]

    #df_complete['DNI_evaluador'] = pd.to_numeric(df_complete['DNI_evaluador'],errors='coerce')
    #df_complete['DNI_evaluador'] = df_complete['DNI_evaluador'].astype(int)
    df_complete.drop(['Nombre Completo_evaluador'],axis=1,inplace=True)

    #TOKENIZAR DNI
    df_complete['DNI_evaluador'] = df_complete['DNI_evaluador'].apply(tokenizar)

    #corrige el formato de los DNIs
    #df_complete['DNI_evaluado'] = pd.to_numeric(df_complete['DNI_evaluado'],errors='coerce')
    #df_complete['DNI_evaluado'] = df_complete['DNI_evaluado'].astype(int)

    # df_colaboradores['DNI'] = df_colaboradores['DNI'].apply(dni_format)
    # print(df_colaboradores['DNI'])
    # =============================================================================
    # FEEDBACK
    # =============================================================================

    # Treatment Feedbak por Colaborador

    df_feedback= df_feedback[df_feedback['evaluados'].str.contains(r'mejorar')]
    df_feedback.value = df_feedback.value.astype(str)
    df_feedback.evaluados = df_melt.evaluados.str.split('¿',expand=True)[0]
    table_feedback = df_feedback.groupby(['evaluados'])['value'].apply(lambda x: ' | = | '.join(x))

    # Convertir el group by to Dataframe
    table_feedback = pd.DataFrame({'evaluados':table_feedback.index,'feedback':table_feedback.values})

    table_feedback['evaluados'] = table_feedback['evaluados'].str.strip()
    table_feedback = table_feedback.loc[~table_feedback.evaluados.str.contains('Sentiment',case=False)]
    #merge para obtener el nombre de los usuarios.
    table_feedback = pd.merge(table_feedback,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre
    # tratamiento de los que no hicieron merge
    # Borramos los datos que no hicieron merge


    table_temp = table_feedback[table_feedback['Nombre Completo_evaluado'].isnull()]

    table_temp = table_temp[['evaluados','feedback']]

    table_temp = table_temp.loc[~table_temp.evaluados.str.contains('Sentiment',case=False)]

    table_temp['evaluados'] = table_temp.evaluados.apply(lambda x:get_close(nombre=x, lista_nombres=df_evaluados['Nombre Completo_evaluado'].to_list()))

    table_temp = pd.merge(table_temp,df_evaluados,left_on='evaluados',right_on='Nombre Completo_evaluado',how='left') # Usamos el nombre
    #print(table_temp)

    # Concatenamos los null tratados y completados

    table_feedback.dropna(subset=['Nombre Completo_evaluado'],inplace=True)

    table_feedback = pd.concat([table_feedback,table_temp],ignore_index=True)





    # =============================================================================
    # TO GENERAL REPORT
    # =============================================================================
    # Headers : DNI +| Nombre+ | Nivel Ocupacional +| Peso~ | Unidad de Negocio +| Area +
    #           Puesto +| Jefe Directo * | Sede +| Fecha de Ingreso +| Score-'nombre del pilar'~ |Count-'nombre del pilar' ~
    #           Periodo ~ | Sexo +| Fecha de Nacimiento +| Edad ~| Promedio General ~ | # Evaluadores ~ | Rango de Edad ~
    # * No es proveido ni obtenido de manera artificial
    # ~ Variables obtenidas por procesamiento
    # + Varibales obtenidas desde la BD de Colaboradores

    return [df_complete, table_feedback]

def agregar_Q(df,year,Q):
    year = str(year)
    Q    = str(Q)
    yearQ = year+'-'+Q
    df['Periodo'] = yearQ
    return df


def personal_reporting(df_complete,df_feedback,dni='all',columna_dni='DNI_evaluado'):
    # =============================================================================
    #     REPORTES PERSONALES # independizar en otra funcion
    # =============================================================================
    # GROUP BY
    periodos_activos = df_complete['Periodo'].drop_duplicates(keep='first')
    periodos_activos = periodos_activos.reset_index()
    periodos_activos = periodos_activos.Periodo.str.split('-Q',expand=True)
    periodos_activos.columns = ['Year','Q']
    periodos_activos.Year = periodos_activos.Year.astype(int)
    periodos_activos.Q = periodos_activos.Q.astype(int)
    # Mostramos los 4 ultimos Q

    periodos_activos.nlargest(4,['Year','Q'])
    periodos_activos['Periodo']=periodos_activos['Year'].astype(str)+'-Q'+periodos_activos['Q'].astype(str)
    periodo_list = periodos_activos['Periodo'].to_list()

    df_complete[columna_dni] = df_complete[columna_dni].astype(float)

    if dni=='all': # caso global
        table_score = df_complete.groupby(['DNI_evaluado','evaluados','Pilar'],as_index=False)['value'].agg(['mean','count']).unstack()
        # Normalizar Nombre de columnas
        table_score.columns = ['-'.join(col).strip() for col in table_score.columns.values]
        table_score.reset_index(inplace=True)

        # GROUP BY NIVEL OCUPACIONAL

        table_score_by_nivocu = df_complete.groupby(['DNI_evaluado','evaluados','Nivel Ocupacional_evaluador','Pilar'])['value'].agg(['mean','count']).unstack()
        # Normalizar Nombre de columnas
        table_score_by_nivocu.columns = ['-'.join(col).strip() for col in table_score_by_nivocu.columns]
        table_score_by_nivocu.reset_index(inplace=True)
        #table_score_by_nivocu.columns = ['-'.join(col).strip() for col in table_score_by_nivocu.columns.values]
        table_score_by_nivocu.rename(columns={'DNI_evaluado-':'DNI_evaluado','evaluados-':'evaluados'},inplace=True)
        # FEEDBACK GLOBAL, DEVUELVE EL MISMO DF_FEEDBACK
        return table_score,table_score_by_nivocu,df_feedback

    else : # caso que ingresa dni particular
        dni = float(dni)
        #filtramos el df_complete por dni
        df_complete = df_complete[df_complete['DNI_evaluado']==dni]
        table_score = df_complete.groupby(['Periodo','evaluados','Pilar'],as_index=False)['value'].agg(['mean','count']).unstack()
        # Normalizar Nombre de columnas
        table_score.columns = ['-'.join(col).strip() for col in table_score.columns.values]
        table_score.reset_index(inplace=True)
        table_score = table_score[table_score['Periodo'].isin(periodo_list)]

        #table_personal_score = table_score.loc[table_score[columna_dni]==dni]

        # GROUP BY NIVEL OCUPACIONAL

        table_score_by_nivocu = df_complete.groupby(['Periodo','evaluados','Nivel Ocupacional_evaluador','Pilar'])['value'].agg(['mean','count']).unstack()
        # Normalizar Nombre de columnas
        table_score_by_nivocu.reset_index(inplace=True)
        table_score_by_nivocu.columns = ['-'.join(col).strip() for col in table_score_by_nivocu.columns.values]
        table_score_by_nivocu.rename(columns={'DNI_evaluado-':'DNI_evaluado','evaluados-':'evaluados'},inplace=True)
        #reporting persona
        #table_personal_score_by_nivocu = table_score_by_nivocu.loc[table_score_by_nivocu[columna_dni]==dni]

        #FEEDBACK PERSONAL
        df_feedback = df_feedback.loc[df_feedback[columna_dni]==dni]
        #return table_personal_score,table_personal_score_by_nivocu,table_feedback_personal
        return table_score,table_score_by_nivocu,df_feedback




##=============================TESTING===============================##

def reporting(df_to_report):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    # Help
    def drawMyRuler(pdf):
        pdf.drawString(100,810, 'x100')
        pdf.drawString(200,810, 'x200')
        pdf.drawString(300,810, 'x300')
        pdf.drawString(400,810, 'x400')
        pdf.drawString(500,810, 'x500')

        pdf.drawString(10,100, 'y100')
        pdf.drawString(10,200, 'y200')
        pdf.drawString(10,300, 'y300')
        pdf.drawString(10,400, 'y400')
        pdf.drawString(10,500, 'y500')
        pdf.drawString(10,600, 'y600')
        pdf.drawString(10,700, 'y700')
        pdf.drawString(10,800, 'y800')

    # Datos Generales del Pdf
    documentTitle='Holi'
    title = 'EVALUACIÓN 360 DE PILARES'

    pdf = canvas.Canvas('reporte.pdf',pagesize=A4)
    drawMyRuler(pdf)
    # =============================================================================
    # #Titulo
    # =============================================================================
    pdf.setFont("Helvetica", 12)

    pdf.setFillColorRGB(0.02, 0.33, 0.64)
    pdf.setStrokeColorRGB(0.02, 0.33, 0.64)
    pdf.rect(100,755,400,30, fill=1)
    #Text title
    pdf.setFillColorRGB(1, 1, 1)
    pdf.drawCentredString(300, 770, title)

    # =============================================================================
    # Informacion Personal
    # =============================================================================
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 9)

    pdf.setTitle(documentTitle)

    pdf.drawCentredString(270, 730, 'DNI: '+df_to_report.iloc[0]['DNI'])
    pdf.drawCentredString(270, 720, 'Nombre Completo: '+df_to_report.iloc[0]['Nombre Completo'])
    pdf.drawCentredString(270, 710, 'Area: '+df_to_report.iloc[0]['Sector'])
    pdf.drawCentredString(270, 700, 'Puesto: '+df_to_report.iloc[0]['Puesto'])

    # =============================================================================
    # #Seccion Data General
    # =============================================================================

    pdf.setFont("Helvetica", 9)

    pdf.setFillColorRGB(0.83, 0.83, 0.83)
    pdf.setStrokeColorRGB(0.83, 0.83, 0.83)
    pdf.rect(100,670,400,15, fill=1)
    #Text title
    pdf.setFillColorRGB(0, 0, 0)
    pdf.drawCentredString(300, 675, 'Calificacion Crosland')

    pdf.drawString(100,100,"Hello World")

    pdf.showPage()
    pdf.save()
