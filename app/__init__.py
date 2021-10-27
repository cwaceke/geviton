from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_migrate import Migrate
import os
from flask_login import LoginManager
from flask_assets import Environment, Bundle



app=Flask(__name__)
#This is the URL for the migrations db 
#app.config['SQLALCHEMY_DATABASE_URI']='postgresql://waceke:1234BN@localhost:5432/simtank_new'
app.config.from_object(os.environ['APP_SETTINGS'])

# 3 slashes is a rel
#now to initialise our dB
db=SQLAlchemy(app)


admin=Admin(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


assets=Environment(app)
assets.url=app.static_url_path

ASSETS_DEBUG = False
ASSETS_AUTO_BUILD = True
scss_all=Bundle("scss/style.scss",
                filters='libsass, cssmin',
                depends=('**/*.scss') ,  
                output="gen/home.%(version)s.css")



css_all=Bundle("https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css",
                "css/styles.css",
                filters='cssmin',
                output="gen/bootstrap.%(version)s.css")


assets.register("scss", scss_all)
assets.register("css",css_all)


from app import routes
from app import models

migrate = Migrate(app, db)


