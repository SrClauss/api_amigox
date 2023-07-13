from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_restful import Api
from dotenv import load_dotenv
from os import getenv



load_dotenv()




def create_app():
    

    if getenv('FLASK_ENV') == 'test':
        conectionstring = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(
        getenv('DB_USER'),
        getenv('DB_PASSWORD'),
        getenv('DB_HOST'),
        getenv('DB_PORT'),
        getenv('TEST_DB_NAME')
    )
    else:
        conectionstring = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(
        getenv('DB_USER'),
        getenv('DB_PASSWORD'),
        getenv('DB_HOST'),
        getenv('DB_PORT'),
        getenv('DB_NAME'))
        

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = conectionstring
    app.secret_key = getenv('SECRET_KEY')


    return app


