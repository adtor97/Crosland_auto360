# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 20:43:57 2020

@author: Usuario
"""

#%%
from flask import Flask, render_template, request, redirect, url_for, session, Markup
import pandas as pd
from datetime import date
#from flask_login import LoginManager
#from requests import request

from utils import utils_google, utils_data_wrangling, utils_plotly

app = Flask(__name__)
today = str(date.today())
app.secret_key = today

df_results = utils_google.read_ws_data(utils_google.open_ws("Crosland_data_master", "base_general"))
df_results["value"] = df_results["value"].astype(float)

#login_manager = LoginManager()
#login_manager.init_app(app)

@app.route("/")
def home():
    return render_template("home_html.html")

@app.route("/login_admin")
def login_admin():
    return render_template("login_admin_html.html")

@app.route("/login_coll")
def login_coll():
    return render_template("login_coll_html.html")

@app.route("/coll_results", methods=["POST"])
def coll_results_redirect():
    if request.method == 'POST':
        DNI = request.form["DNI"]
        #birthday_year = request.form["birthday_year"]
        df_results["DNI_evaluado"]  = df_results["DNI_evaluado"].astype(str)
        df_results_DNI = df_results.loc[df_results["DNI_evaluado"] == str(DNI)]
        #print(df_results_DNI)
        #df_results_DNI["Fecha Nacimiento_evaluado"] = pd.to_datetime(df_results_DNI["Fecha Nacimiento_evaluado"])
        #df_results_DNI = df_results.loc[df_results["Fecha Nacimiento_evaluado"] == birthday_year]

        session["df_results_DNI"] = df_results_DNI[["value", "Pilar"]].to_json()

        return redirect(url_for("coll_results", DNI=DNI))

    else:
        return "Unknown user start counterattack 0"


@app.route("/coll_results/<DNI>", methods=["GET"])
def coll_results(DNI):
    df_results_DNI=pd.read_json(session["df_results_DNI"])
    #print(type(df_results_DNI), type(df_results))
    #print(df_results_DNI)

    if len(df_results_DNI) == 0:
        return render_template("fail_login_coll_html.html")

    else:

        radar = utils_plotly.build_radar(df_results, df_results_DNI)

        #return "hola"
        return render_template("coll_results_html.html", div_radar = radar)


@app.route("/surveys", methods=["GET", "POST"])
def upload_files():
    if request.method == 'POST':

        try:
            if (request.form["user"] == "crosland" and request.form["password"] == "360report"):
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

    else:
        return "Unknown user start counterattack 0"


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

        try:
            df_complete = utils_data_wrangling.auto360(df_answers, df_coll)
            df_complete_show = df_complete.sample(n=10).reset_index(drop=True)

            ws_temp = utils_google.open_ws("Crosland_data_master", "temp")
            utils_google.pandas_to_sheets(df_complete, ws_temp)

            prom = round(df_complete.value.mean(), 2)

            prom_contagiamos = round(df_complete.loc[df_complete.Pilar == "Contagiamos pasión"].value.mean(), 2)
            prom_excelencia = round(df_complete.loc[df_complete.Pilar == "Buscamos la excelencia"].value.mean(), 2)
            prom_juntos = round(df_complete.loc[df_complete.Pilar == "Trabajamos juntos"].value.mean(), 2)
            prom_disfrutamos = round(df_complete.loc[df_complete.Pilar == "Vivimos y disfrutamos"].value.mean(), 2)

            proms = [prom_contagiamos, prom_excelencia, prom_juntos, prom_disfrutamos]
            values = df_complete.Pilar.unique()

            return render_template('show_initial_results.html',
                                    tables=[df_complete_show.to_html(classes='data')],
                                    titles=df_complete_show.columns.values,
                                    prom = prom, proms = proms)

        except:

            return render_template('fail_data_process.html')

        #return "En total los dataframes tienen " + str(len(df_answers) + len(df_coll)) + " filas"
        #else:
            #return "Hubo un error con los archivos"

    else:
        return "Unknown user start counterattack 0"

@app.route("/final", methods=["GET", "POST"])
#En esta función se guarda el nuevo DF completo, se sube a donde lo lee el Power BI y se generan + envían los PDFs
def final_page():
    if request.method == 'POST':
        return "cerrao causa"


if __name__ == "__main__":
    app.run(debug=False)
