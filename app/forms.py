from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, Email, ValidationError, Length, EqualTo, NumberRange
from app.models import User, Project

class ProjectDetails(FlaskForm):
    device_type=SelectField('Device Type',[DataRequired()],
                choices=[("", "-- select an option --"),
                    ('waterLevelGPS','Water Level with GPS'),
                    ('waterLevel','Water level no GPS',),
                    ('waterQlty','Water Quality')])
    
    project_name=StringField('Project Name',[DataRequired()]) 
    def validate_project_name(self, project_name):
        project = Project.query.filter_by(project_name=project_name.data).first()
        if project:
            raise ValidationError('That project name is taken. Please choose a different one.')
class TankDetails(FlaskForm):
    tank_height=IntegerField('Tank Height',[DataRequired(), NumberRange(min=0, max=5.0, message="Value is out of range")])


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

class LoginDetails (FlaskForm):
    email_field=StringField('Email',[DataRequired(), Email()])
    password=PasswordField('Password', [DataRequired()])