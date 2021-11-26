from sqlalchemy.orm import backref,relationship
from wtforms.fields.core import BooleanField
from app import db, login_manager, app, admin
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

ownership=db.Table('ownership', 
    db.Column('owner_id',db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('project_id',db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))
)
class User(db.Model, UserMixin):
    __tablename__='user'

    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(50), unique=True)
    email=db.Column(db.String, nullable=False, unique=True)
    password=db.Column(db.String(256),nullable=False)
    admin=db.Column(db.Boolean, nullable=False, default=True)
    projects=db.relationship('Project',secondary=ownership, back_populates="users")

    def __repr__(self):

        return "({},{}})".format(self.username, self.email)

 
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

class Project(db.Model):
    __tablename='project'
    id=db.Column(db.Integer,primary_key=True)
    project_name=db.Column(db.String(80),nullable=False)
    users=db.relationship('User',secondary=ownership,back_populates="projects")

    def __repr__(self):

        return "{}".format(self.project_name)

admin.add_view(ModelView(Data, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Project, db.session))