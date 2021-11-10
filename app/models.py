
from app import db, admin, login_manager, app
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Data(db.Model):
    __tablename__='data'
    id=db.Column(db.Integer, primary_key=True)
    project_name=db.Column(db.String(80),nullable=False)
    device_id=db.Column(db.String(50))
    time=db.Column(db.String(50))
    payload=db.Column(db.String(50),nullable=False)
    battery=db.Column(db.Integer,nullable=False)
    latitude=db.Column(db.String(20))
    longitude=db.Column(db.String(20))
    level=db.Column(db.Integer)
    
    
    

    def __repr__(self):
        return "<Data(device_id='{}',project='{}', time='{}', payload_data='{}')>"\
                .format(self.device_id,self.project_name, self.time, self.payload)

class Project(db.Model):
    __tablename='projects'
    id=db.Column(db.Integer,primary_key=True)
    project_name=db.Column(db.String(80),nullable=False)
    ownerId=db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)

    def __init__(self, project_name, ownerId):
        self.project_name = project_name
        self.ownerId = ownerId

    

    def __repr__(self):
        return f"Project(self.project_name, self.ownerId)"

    

class User(db.Model, UserMixin):
    __tablename__='users'
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(50), unique=True)
    email=db.Column(db.String, nullable=False, unique=True)
    password=db.Column(db.String(256))
    project=db.relationship('Project',backref='owner')


    def __repr__(self):

        return f"User(self.username, self.email)"

 
    def get_reset_token(self, expires_sec=1800):
        s=Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id':self.id}).decode('utf-8')
        
    @staticmethod
    def verify_reset_token(token):
        s=Serializer(app.config['SECRET_KEY'])
        try:
            user_id=s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)



admin.add_view(ModelView(Data, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Project, db.session))