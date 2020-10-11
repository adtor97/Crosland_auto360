import pandas as pd
from datetime import datetime, timedelta
import math
### Ejemplo de ejecucion
##survey = pd.read_csv('20201010074230-SurveyExport.csv',''encoding='utf-8')
##colaboradores = pdf.read_excel('Encuestas y BD_Q2.xlsx',sheet_name='BD',encoding='utf-8')
# import Auto360
# Auto360.auto360(df_survey=survey,df_colaboradores=colaboradores)

def get_quarter(d):
    return "%d-Q%d" % (d.year,math.ceil(d.month/3)-1)

def auto360(df_survey,df_colaboradores):
    #Seccion Tratamiento de Respuestas 360
    # df_survey : Es el CSV que arroja Survey Gizmo de la encuesta 360
    # df_colaboradores: es (excel) de colaboradores con sus datos personales
    #                   este aun falta actualizarse para leer los datos del archivo que arroja en bruto su sistema de RRHH


    #df = pd.read_csv(df_survey,encoding='utf-8')
    df_survey.rename(columns={'¿Cuál es tu DNI?Esta información será utilizada exclusivamente para procesar la data y la finalidad es poder hacer seguimiento de quienes han completado la encuesta. Los resultados serán confidenciales y tu evaluación hacia los otros también.':'DNI'},inplace=True)

    # Limpieza y Estructuración de data
    columns_len = df_survey.shape[1]
    df_survey = df_survey.iloc[:,19:columns_len]
    df_survey = df_survey.loc[:,~df_survey.columns.str.contains('que has trabajado los últimos tres meses',case=False)]
    df_melt = pd.melt(df_survey,id_vars='DNI',var_name='evaluados')

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
    ###df_croslanderos = pd.read_excel(df_survey,sheet_name='BD',dtypes={'DNI':str})
    df_colaboradores['DNI'] = df_colaboradores.DNI.astype(str)
    #mamberos_name = df_croslanderos['Nombre'].tolist()

    # Filtro para excluir algún área en el procesamiento del Score
    ##df_wuf = df_croslanderos[df_croslanderos['Unidad de Negocio']=='Wuf']
    # wuf_name = df_wuf['Nombre'].tolist()

    # COMPLEMENTANDO INFORMACIÓN DE EVALUADO

    #df_values['evaluados'] = [get_close_matches(i,mamberos_name,cutoff=0.6)[0] if len(get_close_matches(i,mamberos_name,cutoff=0.6)[0])>0 else 'None' for i in df_values['evaluados']]
    # df_complete = pd.merge(df_values,df_croslanderos,left_on='evaluados',right_on='Nombre',how='right')
    df_complete = pd.merge(df_values,df_colaboradores,on='DNI',how='right')
    # df_croslanderos.dtypes

    # Eliminando Nan
    df_complete.dropna(inplace=True)

    # Regla 1 Para la misma ORG. su Score
    ##df_complete_whitout_filter = df_complete.drop(df_complete[df_complete['Unidad de Negocio']=='Wuf'].index)

    # Regla 3 | Filtro CTMR
    # Elimina las Autoevaluaciones
    #Autoevaluados = df_complete[df_complete['evaluados']==df_complete['Nombre Completo']]
    df_complete = df_complete[df_complete['evaluados']!=df_complete['Nombre Completo']]

    # Treatment df_values

    df_complete['value'] = pd.to_numeric(df_complete['value'],errors='coerce')
    df_complete.dropna(inplace=True)
    df_complete.rename(columns={'que_es':'Pilar'},inplace=True)
    # RE - ESCALA [1-4-]

    df_complete.loc[df_complete['value'] == 1,'value'] = 0
    df_complete.loc[df_complete['value'] == 2,'value'] = 25
    df_complete.loc[df_complete['value'] == 3,'value'] = 50
    df_complete.loc[df_complete['value'] == 4,'value'] = 75
    df_complete.loc[df_complete['value'] == 5,'value'] = 100
    #df_complete.loc[df_complete['value']>=75,'status'] = 'Satisfecho'
    #df_complete.loc[df_complete['value']<75,'status'] = 'No Satisfecho'

    # =============================================================================
    #     REPORTES PERSONALES
    # =============================================================================

    # GROUP BY
    table_score = df_complete.groupby(['evaluados','Pilar'],as_index=False)['value'].agg(['mean','count']).unstack()
    #table_score = df_complete.groupby(['evaluados','Pilar'],as_index=False)['value'].aggregate({'Score':'mean','Count':'count'})
    table_score.columns = ['-'.join(col).strip() for col in table_score.columns.values]
    # GROUP BY Unidad de Negocio
    table_score_by_unidad = df_complete.groupby(['evaluados','Unidad de Negocio','Pilar'])['value'].agg(['mean']).unstack()

    # GROUP BY Sector
    table_score_by_sector = df_complete.groupby(['evaluados','Sector','Pilar'])['value'].agg(['mean']).unstack()

    # GROUP BY Jerarquía
    df_complete['Peso']=df_complete[['Puesto']].astype('str')
    table_score_by_puesto = df_complete.groupby(['evaluados','Puesto','Pilar'])['value'].agg(['mean']).unstack()

    # GROUP BY NIVEL OCUPACIONAL
    table_score_by_nivocu = df_complete.groupby(['evaluados','Nivel Ocupacional','Pilar'])['value'].agg(['mean','count']).unstack()

    table_score_by_count_NIVOCU = df_complete.groupby(['evaluados','Nivel Ocupacional'])['DNI'].agg(['count'])

    # =============================================================================
    # FEEDBACK
    # =============================================================================

    # Treatment Feedbak por Colaborador

    df_feedback= df_feedback[df_feedback['evaluados'].str.contains(r'mejorar')]
    df_feedback.value = df_feedback.value.astype(str)
    df_feedback.evaluados = df_melt.evaluados.str.split('¿',expand=True)[0]
    table_feedback = df_feedback.groupby(['evaluados'])['value'].apply(lambda x: ' ||| '.join(x))

    # =============================================================================
    # TO GENERAL REPORT
    # =============================================================================
    # Headers : DNI +| Nombre+ | Nivel Ocupacional +| Peso~ | Unidad de Negocio +| Area +
    #           Puesto +| Jefe Directo * | Sede +| Fecha de Ingreso +| Score-'nombre del pilar'~ |Count-'nombre del pilar' ~
    #           Periodo ~ | Sexo +| Fecha de Nacimiento +| Edad ~| Promedio General ~ | # Evaluadores ~ | Rango de Edad ~
    # * No es proveido ni obtenido de manera artificial
    # ~ Variables obtenidas por procesamiento
    # + Varibales obtenidas desde la BD de Colaboradores

    # Save to Excel =>

    with pd.ExcelWriter('#_Resultados_360.xlsx') as writer:
        table_score.to_excel(writer,sheet_name='score_by_colaborador')
        table_feedback.to_excel(writer,sheet_name='feedback_by_colaborador')
        table_score_by_nivocu.to_excel(writer,sheet_name='score_by_nivel_ocup')
        table_score_by_unidad.to_excel(writer,sheet_name='score_by_unidad')
        table_score_by_sector.to_excel(writer,sheet_name='score_by_sector')
        table_score_by_puesto.to_excel(writer,sheet_name='score_by_puesto')
        table_score_by_count_NIVOCU.to_excel(writer,sheet_name='conteo unico_by_puesto')

    return df_complete
