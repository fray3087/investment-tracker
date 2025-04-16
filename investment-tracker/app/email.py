# app/email.py
from flask import current_app, url_for
from flask_mail import Message
from app import mail  # Assicurati che 'mail' sia inizializzato in app/__init__.py

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    msg = Message('Resetta la tua password',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'''Ciao {user.username},

Per reimpostare la tua password, visita il seguente link:
{url_for('auth.reset_password', token=token, _external=True)}

Se non hai richiesto il reset, ignora questo messaggio.

Saluti,
Il team di Investment Tracker
'''
    mail.send(msg)
