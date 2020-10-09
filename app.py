# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 20:43:57 2020

@author: Usuario
"""

#%%
from flask import Flask, render_template, request
#from flask_login import LoginManager
#from requests import request

app = Flask(__name__)
#login_manager = LoginManager()
#login_manager.init_app(app)

@app.route("/")
def api_root():
    return render_template("login_html.html")


@app.route("/surveys", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        if request.form["user"] == "crosland" and request.form["password"] == "360report":
            
            return "sube tus archivos acá juasjuasjuasjuas"
        else:
            return "Usuario o contraseña equivocado(s), por favor vuelve a intentar"

    else:
        return "¿Te conozco?"

if __name__ == '__main__':
    app.run()




