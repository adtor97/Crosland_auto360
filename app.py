# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 20:43:57 2020

@author: Usuario
"""

#%%
from flask import Flask, render_template, request
import pandas as pd
#from flask_login import LoginManager
#from requests import request

from utils import utils_data_wrangling

app = Flask(__name__)
#login_manager = LoginManager()
#login_manager.init_app(app)

@app.route("/")
def login():
    return render_template("login_html.html")


@app.route("/surveys", methods=["GET", "POST"])
def upload_files():
    if request.method == 'POST':

        try:
            if (request.form["user"] == "crosland" and request.form["password"] == "360report"):
                return render_template("surveys_files_html.html")
            else:
                return render_template("fail_login.html")

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

            #df_complete.to_csv("outputs/pre_df_complete.csv")

            return render_template('show_initial_results.html',  tables=[df_complete_show.to_html(classes='data')], titles=df_complete_show.columns.values)

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


if __name__ == '__main__':
    app.run()
