from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """Form per il login degli utenti"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Accedi')

class RegistrationForm(FlaskForm):
    """Form per la registrazione di nuovi utenti"""
    username = StringField('Nome utente', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Ripeti Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrati')
    
    def validate_username(self, username):
        """Valida che il nome utente non sia già in uso"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Questo nome utente è già in uso. Scegli un altro nome.')
    
    def validate_email(self, email):
        """Valida che l'email non sia già in uso"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Questa email è già registrata. Usa un\'altra email o accedi.')

class ResetPasswordRequestForm(FlaskForm):
    """Form per richiedere il reset della password"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Richiedi Reset Password')

class ResetPasswordForm(FlaskForm):
    """Form per reimpostare la password"""
    password = PasswordField('Nuova Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Ripeti Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reimposta Password')