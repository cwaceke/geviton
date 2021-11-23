from flask import render_template,url_for
from flask_mail import Message
from app import app, mail
from threading import Thread
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_reset_email(user):
    token = user.get_reset_token()
    send_email('Reset Your Password',
               sender=app.config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def generate_invite_token(project, expires_sec=1800):
    serializer=Serializer(app.config['SECRET_KEY'], expires_sec)
    return serializer.dumps(project,salt=app.config['SECURITY_PASSWORD_SALT'] )

def send_invite_email(user, project_name):
    token=generate_invite_token(project_name)
    send_email('Project Invite',
                sender=app.config['MAIL_USERNAME'],
                recipients=[user],
                text_body=render_template('email/invite_email.txt',
                                            project=project_name,token=token),
                html_body=render_template('email/invite_email.html',
                                            project=project_name,token=token))