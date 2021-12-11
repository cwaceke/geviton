from flask_wtf import FlaskForm
from wtforms import StringField, SelectField 
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, Email, ValidationError, Length, EqualTo
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import User, Project, Data
from flask_login import current_user

class ProjectDetails(FlaskForm):
    device_type=SelectField('Device Type',[DataRequired()],
                choices=[("", "-- select an option --"),
                    ('waterLevelGPS','Water Level with GPS'),
                    ('landSurvey', 'Land Survey Beacons'),])
    
    project_name=StringField('Project Name',[DataRequired()]) 
    def validate_project_name(self, project_name):
        project = Project.query.filter_by(project_name=project_name.data).first()
        if project:
            raise ValidationError('That project name is taken. Please choose a different one.')

def choice_query():
    return Project.query.join(User.projects).filter(User.id==current_user.id).all()
class InviteUser(FlaskForm):
    projects=QuerySelectField(query_factory=choice_query, allow_blank=True)
    email=StringField('Email',[DataRequired(),Email()])


class RegistrationDetails(FlaskForm):
    email_field=StringField('Email',[DataRequired(), Email(message='Not a valid email'), Length(min=6)])
    username=StringField('Username',[DataRequired(), Length(min=4, max=20)])
    password=PasswordField('Password', [DataRequired(message="Please fill out this field")])
    password_confirm=PasswordField(' Confirm Password ', [DataRequired(),EqualTo(fieldname="password", message="Your Passwords Do Not Match")] )

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email_field(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class ProjectRegistrationDetails(FlaskForm):
    email_field=StringField('Email',[DataRequired(), Email(message='Not a valid email'), Length(min=6)])
    username=StringField('Username',[DataRequired(), Length(min=4, max=20)])
    password=PasswordField('Password', [DataRequired(message="Please fill out this field")])
    password_confirm=PasswordField(' Confirm Password ', [DataRequired(),EqualTo(fieldname="password", message="Your Passwords Do Not Match")] )

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email_field(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class LoginDetails (FlaskForm):
    email_field=StringField('Email',[DataRequired(), Email()])
    password=PasswordField('Password', [DataRequired()])
    def validate_email_field(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('That email is not registered. Sign up to continue')


class ResetEmail (FlaskForm):
    email_field=StringField('Email',[DataRequired(), Email()])

    def validate_email_field(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register to continue')

class ResetPassword(FlaskForm):
    password=PasswordField('Password', [DataRequired(message="Please fill out this field")])
    password_confirm=PasswordField(' Confirm Password ', [DataRequired(),EqualTo(fieldname="password", message="Your Passwords Do Not Match")] )


