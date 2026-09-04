from flask import Flask, render_template
from threading import Thread
import asyncio
import logging


def start_flask(agente):
    app = Flask(__name__)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    @app.route("/")
    def ver_mensajes():
        return render_template("index.html", estadoEmergencia = agente.estadoEmergencia, idEmergencia = agente.id_emergencia_activa, agentes = agente.agentesEnMision, mensajes = agente.mensajes)


    app.run(host="localhost", port=5001)