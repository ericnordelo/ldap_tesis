import os
# import ldap
import json

from flask import Flask, request
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app import config, utils


# Inicializando la aplicación de flask en modo API
app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'some-secret-string'
app.config['JWT_SECRET_KEY'] = 'dfsasdfsdf7sd6f923f98f8asdff6sdftsdffdsfui3fy2fy87dfgtsdfsd8f'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/token/refresh'

db = SQLAlchemy(app)
jwt = JWTManager(app)
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})


@app.before_first_request
def create_tables():
    db.create_all()


# Configuraciones según el entorno
configuration = config.set_environment(os.getenv("LDAP_API_ENVIRONMENT"))


from app import resources

api.add_resource(resources.UserLogin, '/login')
api.add_resource(resources.UserLogout, '/logout')
api.add_resource(resources.Users, '/usuarios')
api.add_resource(resources.Workers, '/trabajadores')
api.add_resource(resources.Students, '/estudiantes')
api.add_resource(resources.Externs, '/externos')
api.add_resource(resources.SecurityQuestions, '/p/preguntasdeseguridad')
api.add_resource(resources.ChangePassword, '/p/cambiar')
api.add_resource(resources.Admins, '/administradores')
api.add_resource(resources.ServiceStudentInternetQuote, '/servicios/cuotadeinternet/estudiantes')

