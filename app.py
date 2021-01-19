# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 20:43:57 2020

@author: Usuario
"""

#%%
from flask import Flask, render_template, request, redirect, url_for, session, Markup, flash, send_file, make_response
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os, io, zipfile, time
#import plotly_express as px
import requests
from flask_bootstrap import Bootstrap
import pdfkit
from time import sleep
import plotly
import shutil
import flask_excel as excel
import numpy as np
import warnings
from pandas.core.common import SettingWithCopyWarning


warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

#from rq import Queue
#from worker import conn
#from flask_login import LoginManager
#from requests import request

from utils import utils_data_wrangling, utils_plotly, utils_validations#, utils_google

app = Flask(__name__)
Bootstrap(app)

pd.options.display.float_format = "{:,.2f}".format
# Env.
wkhtmltopdf_path = os.environ['wkhtmltopdf_path']
path_crosland = os.environ['path_crosland']

# Local @Cesar
#wkhtmltopdf_path = "C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"
#path_crosland = "D:\Proyectos\Freelance\Crosland\Github - Produccion 3\Crosland_auto360"

# Local @Adrian
#path_crosland = "C:/Users/Usuario/Documents/Freelos/Crosland/Crosland_auto360"
#wkhtmltopdf_path = "C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe"

#q = Queue(connection=conn)
#login_manager = LoginManager()
#login_manager.init_app(app)
today = str(date.today())
app.secret_key = today
#ws_results = utils_google.open_ws("Crosland_data_master", "base_general")
#df_results = q.enqueue(utils_google.read_ws_data(ws_results), 'https://heroku.com/')

try:
    df_results = pd.read_csv("data/df_results.csv")
except:
    df_results = pd.DataFrame()
#print(df_results.columns)

try:
    Qs = list(df_results.Periodo.unique())
    Qs.sort()
except:
    Qs = []
#print(Qs)

static_folder = os.path.join('static')

try:
    df_feedback_old = pd.read_csv("data/df_feedback.csv")
except:
    df_feedback_old = pd.DataFrame()
#print(len(df_feedback_old))

try:
    df_auto_old = pd.read_csv("data/df_auto.csv")
except:
    df_auto_old = pd.DataFrame()
#print(len(df_auto_old))

@app.route("/")
def home():
    grafo = os.path.join(static_folder, 'Grafo.png')
    return render_template("home_html.html", grafo = grafo)

@app.route("/login_admin")
def login_admin():
    return render_template("login_admin_html.html")

@app.route("/action_admin", methods=["POST", "GET"])
def action_admin():

    try:
        session['user'] = request.form["user"]
        session['password'] = request.form["password"]
    except:
        pass

    try:
        if utils_validations.validate_admin(session['user'], session['password']):
            return render_template("action_admin_html.html")
        else:
            return render_template("fail_login_admin_html.html")
    except:
        return render_template("fail_login_admin_html.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if utils_validations.validate_admin(session['user'], session['password']):
        return render_template("dashboard_html.html")
    else: return "Inicia sesión"


@app.route("/previous_results", methods=["GET"])
def download_previous_results():
    if utils_validations.validate_admin(session['user'], session['password']):
        global Qs
        Qs = Qs
        return render_template("download_previous_results.html", buttons=Qs)
    else: return "Inicia sesión"

@app.route("/download_action", methods=["POST"])
def download_action():

    if utils_validations.validate_admin(session['user'], session['password']):
        try:
            Q = request.form["Q_button"]
            file_path = path_crosland + "crosland_app/PDFs/" + Q
            #file_path = path_crosland + "/PDFs/" + Q # local_path

            timestr = time.strftime("%Y%m%d-%H%M%S")
            fileName = "reportes_360_{}.zip".format(timestr)
            memory_file = io.BytesIO()

            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        zipf.write(os.path.join(root, file))
            memory_file.seek(0)
            return send_file(memory_file,
                            attachment_filename=fileName,
                            as_attachment=True)

                            #return str(request.form["Q_button"])
        except:
            global Qs
            Qs = Qs

            flash('Aún no se han generado usuarios ni contraseñas')
            return render_template("download_previous_results.html", buttons=Qs)

    else: return "Inicia sesión"

@app.route("/login_coll")
def login_coll():
    global df_users
    try:
        df_users = pd.read_csv("data/df_users_passwords.csv")
    except:
        df_users = pd.DataFrame()
    #print(len(df_users))
    return render_template("login_coll_html.html")

@app.route("/coll_results", methods=["POST"])
def coll_results_redirect():

    if request.method == 'POST':
        try:
            DNI = int(request.form["DNI"])
        except:
            DNI = str(request.form["DNI"])
        password = str(request.form["password"])

        session["DNI"] = int(DNI)
        session["password_coll"] = password
        #print(df_users.password)
        try:
            df_user  = df_users.loc[(df_users["DNI"].astype(int) == DNI) & (df_users["password"] == password)]
        except: return render_template("fail_login_coll_html.html")

        if len(df_user) == 0:
            return render_template("fail_login_coll_html.html")

        else:
            return redirect(url_for("coll_results", DNI=DNI), code=307)

    else:
        return "Unknown user start counterattack 0"


@app.route("/coll_results/<DNI>", methods=["POST"])
def coll_results(DNI):
    DNI = int(DNI)
    try:
        df_results = pd.read_csv("data/df_results.csv")
    except:
        df_results = pd.DataFrame()
    try:
        df_feedback = pd.read_csv("data/df_feedback.csv")
    except:
        df_feedback = pd.DataFrame()
    try:
        df_autoev = pd.read_csv("data/df_auto.csv")
    except:
        df_autoev = pd.DataFrame()
    #print(len(df_results))
    if len(df_results)==0:
        return render_template("no_results.html")
    else:
        pass
    #print(df_results.columns)
    df_results["DNI_evaluado"]  = df_results["DNI_evaluado"].astype(int).values
    #print("df_results", len(df_results))
    df_results_DNI = df_results.loc[df_results["DNI_evaluado"] == int(DNI)]
    #print("df_results_DNI", len(df_results_DNI))
    df_autoev_DNI = df_autoev.loc[df_autoev["DNI_evaluador"] == int(DNI)]

    if (len(df_results_DNI) == 0):
        return render_template("fail_login_coll_html.html")

    else:

        radar = utils_plotly.build_radar_coll(df_results[["Pilar", "value"]], df_results_DNI[["Pilar", "value"]], df_autoev_DNI[["Pilar", "value", "Periodo"]])
        line = utils_plotly.build_lines_coll(df_results_DNI[["Pilar", "value", "Periodo"]])

        radar_name = "radar_" + str(DNI) + ".png"
        line_name = "line_" + str(DNI) + ".png"

        radar.write_image(path_crosland + "crosland_app/static/tmp/" + radar_name)
        line.write_image(path_crosland + "crosland_app/static/tmp/" + line_name)

        #radar.write_image(path_crosland + "/static/tmp/" + radar_name)
        #line.write_image(path_crosland + "/static/tmp/" + line_name)

        dfs_show_coll = utils_data_wrangling.personal_reporting(df_results,df_feedback,df_autoev,str(session["DNI"]))
        dfs_show_coll[1].rename(columns={"Nivel Ocupacional_evaluador-":"Rango"},inplace=True) # Mandar esta pinche linea al util_sta_wragling/personal_reporting


        print(dfs_show_coll)


        dfs_show_coll_html = [x.set_index(x.columns[0]).T.to_html(classes='data').replace('border="1"','border="0"') for x in dfs_show_coll]
        dfs_cols = [x.columns.values for x in dfs_show_coll]
        #for i in dfs_show_coll:
            #print(len(i))
        #return "hola"
        return render_template("coll_results_html.html", radar_name = "/static/tmp/" + radar_name, line_name = "/static/tmp/" + line_name, tables=dfs_show_coll_html,
        titles=["","Informacion personal", "Calificación Crosland","Calificación Personal", "Calificación Personal por nivel ocupacional", "Feedback", "Autoevaluación"])


@app.route("/surveys", methods=["GET", "POST"])
def upload_files():

    try:
        if utils_validations.validate_admin(session['user'], session['password']):
            return render_template("surveys_files_html.html")

        else:
            return render_template("fail_login_admin_html.html")

    except:
        try:
            file_format_error = request.form["error_button"]
            if file_format_error == "user_error" or file_format_error == "data_process_error":
                return render_template("surveys_files_html.html")
            else:
                return "Unknown user start counterattack 1"
        except:
            return "Unknown user start counterattack 2"

    #else:
#        return "Unknown user start counterattack 0"


@app.route("/results", methods=["GET", "POST"])
#EN LA VALIDACION AGREGAR CANTIDADES ANTERIORES VS NUEVAS COMO CANTIDAD DE PERSONAS, AREAS, QS
def see_results():
    if request.method == 'POST':

        try:
            df_answers = pd.read_csv(request.files.get('file_answers'), encoding = "utf-8")

        except:
            try:
                df_answers = pd.read_excel(request.files.get('file_answers'))
            except:
                return render_template("fail_file_format.html")

        try:
            df_coll = pd.read_csv(request.files.get('file_collaborators'))

        except:
            try:
                df_coll = pd.read_excel(request.files.get('file_collaborators'))

            except:
                return render_template("fail_file_format.html")

        year = request.form["year"]
        Q = request.form["Q"]

        if utils_validations.validate_Q(Q):
            pass
        else:
            flash('Hubo un error colocando el Q, por favor vuelva a intentarlo')
            return redirect("/surveys")

        yearQ = str(year) + "-" + str(Q)
        session["year"] = year
        session["Q"] = Q

        Periodo = str(session["year"]) + "-" + session["Q"]

        try:

            dfs_auto_survey = utils_data_wrangling.df_split(df_answers)
            global df_auto
            df_auto = utils_data_wrangling.agregar_Q(dfs_auto_survey[0], session["year"], session["Q"])
            df_survey = dfs_auto_survey[1]

            results = utils_data_wrangling.auto360(df_survey, df_coll, session["year"], session["Q"])

            global df_complete
            df_complete = results[0]
            #df_complete = df_complete.drop("DNI_evaluador", axis = 1)
            global df_results
            df_results = df_results
            new_columns = [x for x in df_complete.columns if x not in df_results.columns]
            df_new_columns = pd.DataFrame(new_columns, columns = ["Columnas nuevas"])
            old_columns = [x for x in df_results.columns if x not in df_complete.columns]
            df_old_columns = pd.DataFrame(old_columns, columns = ["Columnas faltantes"])
            #print(df_complete["DNI_evaluado"].unique())
            df_complete.replace([np.inf, -np.inf], np.nan, inplace=True)
            #print("df_complete.replace([np.inf, -np.inf], np.nan, inplace=True")
            df_complete = df_complete.dropna(subset=["DNI_evaluado"])
            #print("df_complete = df_complete.dropna(subset=[DNI_evaluado])")
            df_complete["DNI_evaluado"] = df_complete["DNI_evaluado"].apply(utils_data_wrangling.try_int_str)
            #print("df_complete[DNI_evaluado] = df_complete[DNI_evaluado].apply(utils_data_wrangling.try_int_str)")
            df_complete_show = df_complete.sample(n=10).reset_index(drop=True).drop("DNI_evaluador", axis = 1)
            #print("df_complete_show = df_complete.sample(n=10).reset_index(drop=True).drop(DNI_evaluador, axis = 1)")
            global df_feedback
            #print("global df_feedback")
            df_feedback = results[1]
            df_feedback = df_feedback.dropna(subset=["DNI_evaluado"])
            df_feedback["DNI_evaluado"] = df_feedback["DNI_evaluado"].apply(utils_data_wrangling.try_int_str)
            #print("df_feedback = results[1]")

            #ws_temp = utils_google.open_ws("Crosland_data_master", "temp")
            #utils_google.pandas_to_sheets(df_complete, ws_temp)

            prom = round(df_complete.value.mean(), 2)
            #print("prom = round(df_complete.value.mean(), 2)")

            #print("pre radar")
            radar = utils_plotly.build_radar_general(df_complete[["Pilar", "value"]])
            #print("radar = utils_plotly.build_radar_general(df_complete[[Pilar, value]])")
            radar_name = "radar_" + str(Periodo) + ".png"
            #print("radar_name = radar_ + str(Periodo) + .png")

            radar.write_image(path_crosland + "crosland_app/static/tmp/" + radar_name)
            #radar.write_image(path_crosland + "/static/tmp/" + radar_name) # local_path

            #print("radar.write_image(path_crosland + /static/tmp/ + radar_name)")
            #print("pre render")
            #print(df_complete.head())
            #print(df_complete_show.to_html(classes='data'))`

            return render_template('show_initial_results.html',
                                                tables1=[df_complete_show.to_html(classes='data')],
                                                titles1=df_complete_show.columns.values,
                                                prom = prom,
                                                radar_name = "/static/tmp/" + radar_name,
                                                tables2=[df_new_columns.to_html(classes='data')],
                                                titles2=df_new_columns.columns.values,
                                                tables3=[df_old_columns.to_html(classes='data')],
                                                titles3=df_old_columns.columns.values,
                                                )

        except:
            return render_template('fail_data_process.html')

    else:
        return "Unknown user start counterattack 0"

@app.route("/final", methods=["GET", "POST"])
#En esta función se guarda el nuevo DF completo, se sube a donde lo lee el Power BI y se generan + envían los PDFs
def final_page_action():
    if request.method == 'POST':

        try:
            if utils_validations.validate_admin(session['user'], session['password']):
                pass
            else: return ("Error al cargar la página iniciar sesión")
        except: return ("Error al cargar la página iniciar sesión")

        year = session["year"]
        Q = session["Q"]
        Periodo = str(session["year"]) + "-" + session["Q"]

        Periodo_path = path_crosland + "crosland_app/PDFs/"+Periodo
        #Periodo_path = path_crosland + "/PDFs/"+Periodo # local_path

        try:
            shutil.rmtree(Periodo_path, ignore_errors=True)
        except: pass
        os.mkdir(Periodo_path)

        global df_complete
        df_complete = df_complete
        global df_feedback
        df_feedback = df_feedback
        global df_auto
        df_auto = df_auto
        #print(df_complete)
        df_new = utils_data_wrangling.update(df_complete, "data/df_results.csv")
        #print(df_new)
        DNIs = [int(x) for x in df_complete.DNI_evaluado.unique()]
        session["DNIs"] = DNIs
        DNIs_all = [int(x) for x in df_new.DNI_evaluado.unique()]
        df_users_passwords = utils_data_wrangling.build_password_df(DNIs_all)
        df_complete = df_new.loc[df_new["Periodo"]<=Periodo]
        df_complete["DNI_evaluado"]  = df_complete["DNI_evaluado"].astype(int)
        #print(df_users_passwords)
        df_users_passwords.to_csv("data/df_users_passwords.csv", encoding='utf-8', index = False)
        #df_users_passwords = df_users_passwords.to_csv(index = False)
        #resp_df_users_passwords = make_response(df_users_passwords)
        #resp_df_users_passwords.headers["Content-Disposition"] = "attachment; filename=export.csv"
        #resp_df_users_passwords.headers["Content-Type"] = "text/csv"

        #print("saved users pass")
        df_new_feedback = utils_data_wrangling.update(df_feedback, "data/df_feedback.csv")
        df_feedback = df_new_feedback.loc[df_new_feedback["Periodo"]<=Periodo]
        df_auto["DNI_evaluador"] = df_auto["DNI_evaluador"].astype(int)
        #df_new_feedback.to_csv("data/df_feedback.csv", index = False)

        df_new_auto = utils_data_wrangling.update(df_auto, "data/df_auto.csv")
        df_auto = df_new_auto.loc[df_new_auto["Periodo"]<=Periodo]
        #df_new_auto.to_csv("data/df_auto.csv", index = False)

        global df_results
        df_results = pd.read_csv("data/df_results.csv")


        global df_feedback_old
        df_feedback_old = pd.read_csv("data/df_feedback.csv")


        global df_auto_old
        df_auto_old = pd.read_csv("data/df_auto.csv")


        global Qs
        Qs = list(df_results.Periodo.unique())
        Qs.sort()
        Periodo_path = Periodo_path.replace("/", ";")

        return redirect(url_for("dnis_chunks", Periodo_path=Periodo_path, Periodo=Periodo), code=307)

@app.route("/dnis_chunks/<Periodo_path>/<Periodo>", methods=["POST"])
def dnis_chunks(Periodo_path, Periodo):

    try:
        if utils_validations.validate_admin(session['user'], session['password']):
            pass
        else: return ("Error al cargar la página iniciar sesión")
    except: return ("Error al cargar la página iniciar sesión")

    global df_complete
    df_complete = df_complete
    global df_feedback
    df_feedback = df_feedback
    global df_auto
    df_auto = df_auto

    Periodo_path = Periodo_path.replace(";", "/")

    options = {
                "enable-local-file-access": None
                }
    path_wkthmltopdf = wkhtmltopdf_path

    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    DNIs = session["DNIs"]
    if len(DNIs)>=30:
        DNIs_temp = DNIs[:30]
        session["DNIs"] = DNIs[30:]
    else:
        DNIs_temp = DNIs[:30]
        session["DNIs"] = []
    #i = 0
    print(len(DNIs))
    for DNI in DNIs_temp:
        #i+=1
        #print(DNI, i)
        df_complete_DNI = df_complete.loc[df_complete["DNI_evaluado"] == int(DNI)]
        name = df_complete_DNI["Nombre Completo_evaluado"].values[0]

        file_name = str(DNI) + "_" + name + "_" + Periodo + '.pdf'

        df_auto_DNI = df_auto.loc[df_auto["DNI_evaluador"] == int(DNI)]
        #print("NOMBREEE: ", name)
        if (len(df_complete_DNI) == 0):
            print("no results 1")
            render = render_template("home_html.html")
            pdfkit.from_string(render,"/PDFs/" + Periodo + "/" + file_name,configuration=config, options=options)

        else:

            try:

                #radar = utils_plotly.build_radar_coll(df_new[["Pilar", "value"]], df_complete_DNI[["Pilar", "value"]], df_auto_DNI[["Pilar", "value"]])
                #line = utils_plotly.build_lines_coll(df_complete_DNI[["Pilar", "value", "Periodo"]])

                #radar_name = "radar_" + str(DNI) + ".png"
                #line_name = "line_" + str(DNI) + ".png"

                #radar.write_image(path + "/static/tmp/" + radar_name)
                #line.write_image(path + "/static/tmp/" + line_name)

                dfs_show_coll = utils_data_wrangling.personal_reporting(df_complete,df_feedback,df_auto,int(DNI))
                #print(dfs_show_coll)
                #dfs_show_coll[1].rename(columns={"Nivel Ocupacional_evaluador-":"Rango"},inplace=True) # Mandar esta pinche linea al util_sta_wragling/personal_reporting
                #print(dfs_show_coll[1])
                #print(dfs_show_coll)

                dfs_show_coll_html = [x.set_index(x.columns[0]).T.to_html(classes='data').replace('border="1"','border="0"') for x in dfs_show_coll]
                dfs_cols = [x.columns.values for x in dfs_show_coll]
                #print(dfs_cols)
                #for i in dfs_show_coll:
                    #print(len(i))
                #return "hola"

                css_path = path_crosland + "crosland_app/static/css_colab_results.css"
                logo_path = path_crosland + "crosland_app/static/pictures/crosland.png"

                #css_path = path_crosland + "/static/css_colab_results.css"
                #logo_path = path_crosland + "/static/pictures/crosland.png"

                render = render_template("coll_results_html_download.html", css_path = css_path, tables=dfs_show_coll_html,logo_path = logo_path,
                                        titles=["","Informacion personal", "Calificación Crosland","Calificación Personal", "Calificación Personal por nivel ocupacional", "Feedback", "Autoevaluación"])
                #print(DNI, len())
                pdfkit.from_string(render,Periodo_path + "/" + file_name,configuration=config, options=options, css=css_path)

            except:
                print("no results 2")
                render = render_template("no_results.html")
                pdfkit.from_string(render,Periodo_path + "/" + file_name,configuration=config, options=options)

    Periodo_path = Periodo_path.replace("/", ";")
    if len(session["DNIs"])>0:
        return redirect(url_for("dnis_chunks", Periodo_path=Periodo_path, Periodo=Periodo), code=307)
    else:
        return render_template('final_html.html')

@app.route("/download_users_passwords", methods=["GET", "POST"])
#En esta función se guarda el nuevo DF completo, se sube a donde lo lee el Power BI y se generan + envían los PDFs
def download_users_passwords():
    try: df_users_passwords = pd.read_csv("data/df_users_passwords.csv")
    except: df_users_passwords = pd.DataFrame()

    resp = make_response(df_users_passwords.to_csv(index=False))
    resp.headers["Content-Disposition"] = "attachment; filename=df_users_passwords.csv"
    resp.headers["Content-Type"] = "text/csv"

    return resp


@app.route("/pdf_tutorial", methods=["GET", "POST"])
# DESCARGA TUTORIAL PDF
def pdf_tutorial():
    try:
        if utils_validations.validate_admin(session['user'], session['password']):
            return send_file(path_crosland+"crosland_app/static/files_to_download/Tutorial_Actualizando_Dashboard.pdf",attachment_filename="Tutorial_Actualizando_Dashboard.pdf")
            #return send_file(path_crosland+"/static/files_to_download/Tutorial_Actualizando_Dashboard.pdf",attachment_filename="Tutorial_Actualizando_Dashboard.pdf")

        else:
            return render_template("fail_login_admin_html.html")

    except:
        return "Error al leer archivo/Inicie sesión como administrador"


@app.route("/template_pbix", methods=["GET", "POST"])
# DESCARGA TEMPLATE DASHBOARD_360.pbix
def template_dashboard_360():
    try:
        if utils_validations.validate_admin(session['user'], session['password']):
            return send_file(path_crosland+"crosland_app/static/files_to_download/Dashboard_360.pbix",attachment_filename="Dashboard_360.pbix",as_attachment=True)
            #return send_file(path_crosland+"/static/files_to_download/Dashboard_360.pbix",attachment_filename="Dashboard_360.pbix",as_attachment=True)

        else:
            return render_template("fail_login_admin_html.html")

    except:
        return "Error al leer archivo/Inicie sesión como administrador"



@app.route("/download/RcFE9jRH/ukLas/j8n3k", methods=["GET", "POST"])
#Link de descargar df_results
def down_results():
    try: #df_auto = pd.read_csv("data/df_auto.csv")
        df_auto = pd.read_csv("data/df_results.csv")
        resp = make_response(df_auto.to_csv(index=False))
        resp.headers["Content-Disposition"] = "attachment; filename=df_results.csv"
        resp.headers["Content-Type"] = "text/csv"

        return resp

    except: return "Error al leer archivo"

    #return excel.make_response_from_array(list(df_auto.values), "csv", file_name="df_results")



@app.route("/download/lWdREEWWOuI/r0j8n3k/j8ndsad3k", methods=["GET", "POST"])
#Link de descargar df_auto
def down_auto():
    try: #df_auto = pd.read_csv("data/df_auto.csv")
        df_auto = pd.read_csv("data/df_auto.csv")
        resp = make_response(df_auto.to_csv(index=False))
        resp.headers["Content-Disposition"] = "attachment; filename=df_auto.csv"
        resp.headers["Content-Type"] = "text/csv"

        return resp

    except: return "Error al leer archivo"

if __name__ == "__main__":
    excel.init_excel(app)
    app.run(debug=False)
