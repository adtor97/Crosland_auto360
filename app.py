# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 20:43:57 2020

@author: Usuario
"""

#%%
from flask import Flask, render_template, request, redirect, url_for, session, Markup, flash
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import plotly_express as px
import requests
#from rq import Queue
#from worker import conn
#from flask_login import LoginManager
#from requests import request

from utils import utils_google, utils_data_wrangling, utils_plotly, utils_validations

app = Flask(__name__)
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
print(len(df_results))

static_folder = os.path.join('static')

try:
    df_feedback_old = pd.read_csv("data/df_feedback.csv")
except:
    df_feedback_old = pd.DataFrame()
print(len(df_feedback_old))

try:
    df_auto_old = pd.read_csv("data/df_auto.csv")
except:
    df_auto_old = pd.DataFrame()
print(len(df_auto_old))

@app.route("/")
def home():
    grafo = os.path.join(static_folder, 'Grafo.png')
    return render_template("home_html.html", grafo = grafo)

@app.route("/login_admin")
def login_admin():
    return render_template("login_admin_html.html")

@app.route("/action_admin", methods=["GET", "POST"])
def action_admin():
    if request.method == 'POST':
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

@app.route("/previous_results", methods=["GET"])
def download_previous_results():
    if utils_validations.validate_admin(session['user'], session['password']):
        return render_template("download_previous_results.html")
    else: return "Inicia sesión"


@app.route("/login_coll")
def login_coll():
    global df_users
    try:
        #df_users = q.enqueue(utils_google.read_ws_data(utils_google.open_ws("Crosland_data_master", "users")), 'https://auto360.herokuapp.com/')
        df_users = utils_google.read_ws_data(utils_google.open_ws("Crosland_data_master", "users"))
        df_users["DNI"] = df_users["DNI"].astype("str")
    except:
        df_users = pd.DataFrame()
    print(len(df_users))
    return render_template("login_coll_html.html")

@app.route("/coll_results", methods=["POST"])
def coll_results_redirect():

    if request.method == 'POST':
        try:
            DNI = str(int(request.form["DNI"]))
        except:
            DNI = str(request.form["DNI"])
        password = str(request.form["password"])

        session["DNI"] = DNI
        session["password_coll"] = password

        df_user  = df_users.loc[(df_users["DNI"] == DNI) & (df_users["password"] == password)]

        if len(df_user) == 0:
            return render_template("fail_login_coll_html.html")

        else:
            return redirect(url_for("coll_results", DNI=DNI))

    else:
        return "Unknown user start counterattack 0"


@app.route("/coll_results/<DNI>", methods=["GET"])
def coll_results(DNI):
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
    print(len(df_results))
    if len(df_results)==0:
        return render_template("no_results.html")
    else:
        pass
    #print(df_results.columns)
    df_results["DNI_evaluado"]  = df_results["DNI_evaluado"].astype(str)
    df_results_DNI = df_results.loc[df_results["DNI_evaluado"] == str(DNI)]

    if (len(df_results_DNI) == 0):
        return render_template("fail_login_coll_html.html")

    else:

        radar = utils_plotly.build_radar_coll(df_results[["Pilar", "value"]], df_results_DNI[["Pilar", "value"]], df_autoev[["Pilar", "value"]])
        line = utils_plotly.build_lines_coll(df_results_DNI[["Pilar", "value", "Periodo"]])

        dfs_show_coll = utils_data_wrangling.personal_reporting(df_results,df_feedback,df_autoev,str(session["DNI"]))
        dfs_show_coll_html = [x.to_html(classes='data') for x in dfs_show_coll]
        dfs_cols = [x.columns.values for x in dfs_show_coll]
        for i in dfs_show_coll:
            print(len(i))
        #return "hola"
        return render_template("coll_results_html.html", div_radar = radar, div_line = line, tables=dfs_show_coll_html,
        titles=["", "Por pilar", "Por nivel ocupacional", "Feedback", "Autoevaluación"])


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

        try:
            #results = q.enqueue(utils_data_wrangling.auto360(df_answers, df_coll), 'http://heroku.com')
            dfs_auto_survey = utils_data_wrangling.df_split(df_answers)

            global df_auto
            df_auto = utils_data_wrangling.agregar_Q(dfs_auto_survey[0], session["year"], session["Q"])
            df_survey = dfs_auto_survey[1]

            results = utils_data_wrangling.auto360(df_survey, df_coll, session["year"], session["Q"])

            global df_complete
            df_complete = results[0]
            df_complete["DNI_evaluado"] = df_complete["DNI_evaluado"].astype(int).astype(str)
            df_complete_show = df_complete.sample(n=10).reset_index(drop=True)
            global df_feedback
            df_feedback = results[1]

            #ws_temp = utils_google.open_ws("Crosland_data_master", "temp")
            #utils_google.pandas_to_sheets(df_complete, ws_temp)

            prom = round(df_complete.value.mean(), 2)
            #print("pre radar")
            radar = utils_plotly.build_radar_general(df_complete[["Pilar", "value"]])
            #print("pre render")
            #print(df_complete.head())
            #print(df_complete_show.to_html(classes='data'))
            return render_template('show_initial_results.html',
                                    tables=[df_complete_show.to_html(classes='data')],
                                    titles=df_complete_show.columns.values,
                                    prom = prom,
                                    div_radar = radar
                                    )

        except:
            return render_template('fail_data_process.html')

    else:
        return "Unknown user start counterattack 0"

@app.route("/final", methods=["GET", "POST"])
#En esta función se guarda el nuevo DF completo, se sube a donde lo lee el Power BI y se generan + envían los PDFs
def final_page():
    if request.method == 'POST':

        year = session["year"]
        Q = session["Q"]

        global df_complete
        df_complete = df_complete
        global df_feedback
        df_feedback = df_feedback
        global df_auto
        df_auto = df_auto

        df_new = utils_data_wrangling.update(df_complete, "data/df_results.csv")
        #df_new.to_csv("data/df_results.csv", index = False)

        df_new_feedback = utils_data_wrangling.update(df_feedback, "data/df_feedback.csv")
        #df_new_feedback.to_csv("data/df_feedback.csv", index = False)

        df_new_auto = utils_data_wrangling.update(df_auto, "data/df_auto.csv")
        #df_new_auto.to_csv("data/df_auto.csv", index = False)

        return render_template('final_html.html')

if __name__ == "__main__":
    app.run(debug=False)
