from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
#from app.utils.email import send_password_reset_email

# Crea il blueprint
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Gestisce il login degli utenti"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Email o password non valida')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        
        # Reindirizza alla pagina richiesta o alla home
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Accedi', form=form)

@auth.route('/logout')
def logout():
    """Gestisce il logout degli utenti"""
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Gestisce la registrazione di nuovi utenti"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('Congratulazioni, registrazione completata!')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='Registrazione', form=form)

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Gestisce la richiesta di reset password"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Ti è stata inviata un\'email con le istruzioni per reimpostare la password')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password_request.html',
                           title='Reimposta Password', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Gestisce il reset password con token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('La tua password è stata reimpostata.')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)