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

app = Flask(__name__)
#login_manager = LoginManager()
#login_manager.init_app(app)

@app.route("/")
def login():
    return render_template("login_html.html")


@app.route("/surveys", methods=["GET", "POST"])
def upload_files():
    if request.method == 'POST':
        if request.form["user"] == "crosland" and request.form["password"] == "360report":
            
            return render_template("surveys_files_html.html")
        else:
            return "Usuario o contraseña equivocado(s), por favor vuelve a intentar"

    else:
        return "¿Te conozco?"
    
    
@app.route("/results", methods=["GET", "POST"])
def see_results():
    if request.method == 'POST':    

        df_answers = pd.read_excel(request.files.get('file_answers'))
        df_coll = pd.read_excel(request.files.get('file_collaborators'))
        
        return "En total los dataframes tienen " + str(len(df_answers) + len(df_coll)) + " columnas"
        #else:
            #return "Hubo un error con los archivos"

    else:
        return "¿Te conozco?"

if __name__ == '__main__':
    app.run()




