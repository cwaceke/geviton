from flask import Flask
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_migrate import Migrate, current
import os
from flask_login import LoginManager
from flask_breadcrumbs import Breadcrumbs
from flask_mail import Mail


app=Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

db=SQLAlchemy(app)

#initialize Mail
mail = Mail(app)

#initialize Flask-Admin
admin=Admin(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

#initialize Breadcrumbs

breadcrumbs=Breadcrumbs(app=app)


from app import routes
from app import models

migrate = Migrate(app, db)


