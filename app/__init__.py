from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_migrate import Migrate
import os
from flask_login import LoginManager
from flask_assets import Environment, Bundle
from flask_mail import Mail


app=Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'cwaceke22@gmail.com'
app.config['MAIL_PASSWORD'] = 'Marigo22'
mail = Mail(app)

# 3 slashes is a rel
#now to initialise our dB
db=SQLAlchemy(app)


admin=Admin(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'




from app import routes
from app import models

migrate = Migrate(app, db)


