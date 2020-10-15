# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 20:43:57 2020

@author: Usuario
"""

#%%
from flask import Flask, render_template, request, redirect, url_for, session, Markup
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import plotly_express as px
from rq import Queue
from worker import conn
#from flask_login import LoginManager
#from requests import request

from utils import utils_google, utils_data_wrangling, utils_plotly

app = Flask(__name__)
q = Queue(connection=conn)
#login_manager = LoginManager()
#login_manager.init_app(app)
#today = str(date.today())
#app.secret_key = today
ws_results = utils_google.open_ws("Crosland_data_master", "base_general")
df_results = q.enqueue(utils_google.read_ws_data(ws_results), 'https://heroku.com/')

try:
    ws_results = utils_google.open_ws("Crosland_data_master", "base_general")
    df_results = q.enqueue(utils_google.read_ws_data(ws_results), 'https://auto360.herokuapp.com/')
    df_results["value"] = df_results["value"].astype(float)
except:
    df_results = pd.DataFrame()
print(len(df_results))
static_folder = os.path.join('static')
try:
    df_users = q.enqueue(utils_google.read_ws_data(utils_google.open_ws("Crosland_data_master", "users")), 'http://heroku.com')
    df_users["DNI"] = df_users["DNI"].astype("str")
except:
    df_users = pd.DataFrame()
print(len(df_users))
try:
    ws_feedback = utils_google.open_ws("Crosland_data_master", "feedback")
    df_feedback_old = q.enqueue(utils_google.read_ws_data(ws_feedback), 'http://heroku.com')
except:
    df_feedback_old = pd.DataFrame()
print(len(df_feedback_old))

@app.route("/")
def home():
    grafo = os.path.join(static_folder, 'Grafo.png')
    return render_template("home_html.html", grafo = grafo)

@app.route("/login_admin")
def login_admin():
    return render_template("login_admin_html.html")

@app.route("/login_coll")
def login_coll():
    return render_template("login_coll_html.html")

@app.route("/coll_results", methods=["POST"])
def coll_results_redirect():

    if request.method == 'POST':
        try:
            DNI = str(int(request.form["DNI"]))
        except:
            DNI = str(request.form["DNI"])
        password = str(request.form["password"])

        df_user  = df_users.loc[(df_users["DNI"] == DNI) & (df_users["password"] == password)]

        if len(df_user) == 0:
            return render_template("fail_login_coll_html.html")

        else:
            return redirect(url_for("coll_results", DNI=DNI))

    else:
        return "Unknown user start counterattack 0"


@app.route("/coll_results/<DNI>", methods=["GET"])
def coll_results(DNI):

    df_results["DNI_evaluado"]  = df_results["DNI_evaluado"].astype(str)
    df_results_DNI = df_results.loc[df_results["DNI_evaluado"] == str(DNI)]

    if (len(df_results_DNI) == 0):
        return render_template("fail_login_coll_html.html")

    else:

        radar = utils_plotly.build_radar_coll(df_results[["Pilar", "value"]], df_results_DNI[["Pilar", "value"]])
        line = utils_plotly.build_lines_coll(df_results_DNI[["Pilar", "value", "Periodo"]])

        #return "hola"
        return render_template("coll_results_html.html", div_radar = radar, div_line = line)


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

        print("antes de la funcion")
        results = q.enqueue(utils_data_wrangling.auto360(df_answers, df_coll), 'http://heroku.com')
        global df_complete
        df_complete = results[0]
        df_complete_show = df_complete.sample(n=10).reset_index(drop=True)
        global df_feedback
        df_feedback = results[1]

        #ws_temp = utils_google.open_ws("Crosland_data_master", "temp")
        #utils_google.pandas_to_sheets(df_complete, ws_temp)

        prom = round(df_complete.value.mean(), 2)
        radar = utils_plotly.build_radar_general(df_complete[["Pilar", "value"]])

        return render_template('show_initial_results.html',
                                tables=[df_complete_show.to_html(classes='data')],
                                titles=df_complete_show.columns.values,
                                prom = prom, div_radar = radar)

        #try:
        #    print("antes de la funcion")
        #    results = q.enqueue(utils_data_wrangling.auto360(df_answers, df_coll), 'http://heroku.com')
        #    global df_complete
        #    df_complete = results[0]
        #    df_complete_show = df_complete.sample(n=10).reset_index(drop=True)
        #    global df_feedback
        #    df_feedback = results[1]

            #ws_temp = utils_google.open_ws("Crosland_data_master", "temp")
            #utils_google.pandas_to_sheets(df_complete, ws_temp)

        #    prom = round(df_complete.value.mean(), 2)
        #    radar = utils_plotly.build_radar_general(df_complete[["Pilar", "value"]])

        #    return render_template('show_initial_results.html',
        #                            tables=[df_complete_show.to_html(classes='data')],
        #                            titles=df_complete_show.columns.values,
        #                            prom = prom, div_radar = radar)

        #except:
        #    return render_template('fail_data_process.html')

    else:
        return "Unknown user start counterattack 0"

@app.route("/final", methods=["GET", "POST"])
#En esta función se guarda el nuevo DF completo, se sube a donde lo lee el Power BI y se generan + envían los PDFs
def final_page():
    if request.method == 'POST':

        year = request.form["year"]
        Q = request.form["Q"]

        df_complete_final = utils_data_wrangling.agregar_Q(df_complete, year, Q)
        df_feedback_final = utils_data_wrangling.agregar_Q(df_feedback, year, Q)

        dates_complete = list(df_complete_final.select_dtypes(include=['datetime64']).columns)
        dates_feedback = list(df_feedback_final.select_dtypes(include=['datetime64']).columns)

        for column in dates_complete:
            df_complete_final[column] = df_complete_final[column].astype("str")
        for column in dates_feedback:
            df_feedback_final[column] = df_feedback_final[column].astype("str")

        df_new = pd.concat([df_results, df_complete_final], axis = 0)
        print(len(df_new))
        q.enqueue(utils_google.pandas_to_sheets(df_new, ws_results), 'http://heroku.com')

        df_new_feedback = pd.concat([df_feedback_old, df_feedback_final], axis = 0)
        q.enqueue(utils_google.pandas_to_sheets(df_new_feedback, ws_feedback), 'http://heroku.com')

        return render_template('final_html.html')

if __name__ == "__main__":
    app.run(debug=True)
