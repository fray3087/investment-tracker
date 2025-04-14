from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.portfolio import Portfolio
from datetime import datetime



# Crea il blueprint
main = Blueprint('main', __name__)


@main.route('/')
@main.route('/index')
def index():
    """Pagina principale"""
    if current_user.is_authenticated:
        # Ottieni i portafogli dell'utente
        portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
        
        # Calcola il valore totale degli investimenti
        total_value = sum(p.current_value() for p in portfolios)
        
        # Calcola il capitale totale investito
        total_invested = sum(p.invested_capital() for p in portfolios)
        
        # Calcola il rendimento totale
        total_return = 0
        if total_invested > 0:
            total_return = (total_value - total_invested) / total_invested * 100
        
        return render_template('index.html', 
                              title='Dashboard',
                              portfolios=portfolios,
                              total_value=total_value,
                              total_invested=total_invested,
                              total_return=total_return)
    else:
        # Pagina di benvenuto per utenti non autenticati
        return render_template('welcome.html', title='Benvenuto')

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard con panoramica degli investimenti"""
    # Ottieni i portafogli dell'utente
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    
    # Raccogli statistiche per ogni portafoglio
    portfolio_stats = []
    for p in portfolios:
        stats = {
            'id': p.id,
            'name': p.name,
            'value': p.current_value(),
            'invested': p.invested_capital(),
            'return': p.total_return(),
            'asset_count': p.asset_count()
        }
        portfolio_stats.append(stats)
    
    # Totali
    total_value = sum(p['value'] for p in portfolio_stats)
    total_invested = sum(p['invested'] for p in portfolio_stats)
    total_return = 0
    if total_invested > 0:
        total_return = (total_value - total_invested) / total_invested * 100
    
    return render_template('dashboard.html',
                          title='Dashboard',
                          portfolios=portfolio_stats,
                          total_value=total_value,
                          total_invested=total_invested,
                          total_return=total_return)

@main.route('/profile')
@login_required
def profile():
    """Pagina del profilo utente"""
    return render_template('profile.html', title='Profilo', user=current_user)

@main.route('/')
def home():
    return render_template('welcome.html', title='Benvenuto', now=datetime.now())