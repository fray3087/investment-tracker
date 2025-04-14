from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.forms.portfolio import PortfolioForm
from app.services.financial import calculate_twr, calculate_mwr, calculate_cagr, calculate_drawdowns
import yfinance as yf
import pandas as pd
from datetime import datetime

# Crea il blueprint
portfolio = Blueprint('portfolio', __name__)

@portfolio.route('/list')
@login_required
def list():
    """Lista dei portafogli dell'utente"""
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    return render_template('portfolio/list.html', 
                          title='I miei portafogli',
                          portfolios=portfolios)

@portfolio.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Crea un nuovo portafoglio"""
    form = PortfolioForm()
    
    if form.validate_on_submit():
        new_portfolio = Portfolio(
            name=form.name.data,
            description=form.description.data,
            benchmark=form.benchmark.data,
            user_id=current_user.id
        )
        db.session.add(new_portfolio)
        db.session.commit()
        flash('Portafoglio creato con successo!')
        return redirect(url_for('portfolio.view', id=new_portfolio.id))
    
    return render_template('portfolio/create.html',
                          title='Nuovo Portafoglio',
                          form=form)

@portfolio.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifica un portafoglio esistente"""
    portfolio_obj = Portfolio.query.get_or_404(id)
    
    # Verifica che l'utente sia il proprietario del portafoglio
    if portfolio_obj.user_id != current_user.id:
        flash('Non sei autorizzato a modificare questo portafoglio')
        return redirect(url_for('portfolio.list'))
    
    form = PortfolioForm(obj=portfolio_obj)
    
    if form.validate_on_submit():
        portfolio_obj.name = form.name.data
        portfolio_obj.description = form.description.data
        portfolio_obj.benchmark = form.benchmark.data
        
        db.session.commit()
        flash('Portafoglio aggiornato con successo!')
        return redirect(url_for('portfolio.view', id=portfolio_obj.id))
    
    return render_template('portfolio/edit.html',
                          title='Modifica Portafoglio',
                          form=form,
                          portfolio=portfolio_obj)

@portfolio.route('/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    """Elimina un portafoglio"""
    portfolio_obj = Portfolio.query.get_or_404(id)
    
    # Verifica che l'utente sia il proprietario del portafoglio
    if portfolio_obj.user_id != current_user.id:
        flash('Non sei autorizzato a eliminare questo portafoglio')
        return redirect(url_for('portfolio.list'))
    
    db.session.delete(portfolio_obj)
    db.session.commit()
    
    flash('Portafoglio eliminato con successo')
    return redirect(url_for('portfolio.list'))

@portfolio.route('/view/<id>')
@login_required
def view(id):
    """Visualizza i dettagli di un portafoglio"""
    portfolio_obj = Portfolio.query.get_or_404(id)
    
    # Verifica che l'utente sia il proprietario del portafoglio
    if portfolio_obj.user_id != current_user.id:
        flash('Non sei autorizzato a visualizzare questo portafoglio')
        return redirect(url_for('portfolio.list'))
    
    # Ottieni gli asset del portafoglio
    assets = Asset.query.filter_by(portfolio_id=id).all()
    
    # Calcola le statistiche del portafoglio
    stats = {
        'current_value': portfolio_obj.current_value(),
        'invested_capital': portfolio_obj.invested_capital(),
        'total_commissions': portfolio_obj.total_commissions(),
        'total_return': portfolio_obj.total_return(),
        'asset_count': portfolio_obj.asset_count()
    }
    
    # Preparare i dati degli asset per la visualizzazione
    asset_data = []
    for asset in assets:
        asset_info = {
            'id': asset.id,
            'ticker': asset.ticker,
            'name': asset.name,
            'shares': asset.current_shares(),
            'value': asset.current_value(),
            'invested': asset.invested_capital(),
            'return': asset.calculate_my_performance(),
            'price': asset.get_current_price()
        }
        asset_data.append(asset_info)
    
    return render_template('portfolio/view.html',
                          title=portfolio_obj.name,
                          portfolio=portfolio_obj,
                          stats=stats,
                          assets=asset_data)

@portfolio.route('/performance/<id>')
@login_required
def performance(id):
    """Visualizza le performance di un portafoglio"""
    portfolio_obj = Portfolio.query.get_or_404(id)
    
    # Verifica che l'utente sia il proprietario del portafoglio
    if portfolio_obj.user_id != current_user.id:
        flash('Non sei autorizzato a visualizzare questo portafoglio')
        return redirect(url_for('portfolio.list'))
    
    # Ottieni gli asset del portafoglio
    assets = Asset.query.filter_by(portfolio_id=id).all()
    
    # Ottieni la data della prima transazione
    first_date = portfolio_obj.first_transaction_date()
    if not first_date:
        flash('Non ci sono transazioni in questo portafoglio')
        return redirect(url_for('portfolio.view', id=id))
    
    # Calcola le performance per diversi periodi
    performance_data = {}
    periods = {
        '1m': '1 mese',
        '3m': '3 mesi',
        '6m': '6 mesi',
        'ytd': 'Anno corrente',
        '1y': '1 anno',
        '3y': '3 anni',
        '5y': '5 anni',
        'max': 'Dall\'inizio'
    }
    
    now = datetime.now()
    
    for period_key, period_name in periods.items():
        # Verifica se il periodo è applicabile (in base alla prima transazione)
        applicable = True
        
        if period_key == '3y' and (now - first_date).days < 365*3:
            applicable = False
        elif period_key == '5y' and (now - first_date).days < 365*5:
            applicable = False
        elif period_key == '1y' and (now - first_date).days < 365:
            applicable = False
        elif period_key == '6m' and (now - first_date).days < 180:
            applicable = False
        elif period_key == '3m' and (now - first_date).days < 90:
            applicable = False
        elif period_key == '1m' and (now - first_date).days < 30:
            applicable = False
        
        if applicable:
            # Calcola performance
            return_data = calculate_portfolio_performance(portfolio_obj, assets, period_key)
            performance_data[period_key] = {
                'name': period_name,
                'data': return_data
            }
    
    # Ottieni dati benchmark se specificato
    benchmark_data = None
    if portfolio_obj.benchmark:
        try:
            ticker = yf.Ticker(portfolio_obj.benchmark)
            benchmark_hist = ticker.history(period='5y')
            benchmark_data = {
                'ticker': portfolio_obj.benchmark,
                'name': ticker.info.get('shortName', portfolio_obj.benchmark),
                'data': benchmark_hist
            }
        except Exception as e:
            print(f"Errore nel recupero del benchmark {portfolio_obj.benchmark}: {e}")
    
    return render_template('portfolio/performance.html',
                          title=f'Performance di {portfolio_obj.name}',
                          portfolio=portfolio_obj,
                          performance=performance_data,
                          benchmark=benchmark_data)

def calculate_portfolio_performance(portfolio, assets, period):
    """Calcola le performance del portafoglio"""
    # Raccogli dati storici per ogni asset
    asset_data = []
    for asset in assets:
        hist = asset.get_historical_data(period=period)
        if not hist.empty:
            asset_data.append({
                'ticker': asset.ticker,
                'weight': asset.current_value() / portfolio.current_value() if portfolio.current_value() > 0 else 0,
                'data': hist
            })
    
    # Se non ci sono dati, restituisci None
    if not asset_data:
        return None
    
    # Calcola il valore giornaliero del portafoglio
    portfolio_values = []
    dates = []
    
    # Utilizza l'indice della prima serie per le date
    reference_dates = asset_data[0]['data'].index
    
    for date in reference_dates:
        total_value = 0
        for asset_info in asset_data:
            # Verifica se la data è presente nei dati dell'asset
            if date in asset_info['data'].index:
                asset_value = asset_info['data'].loc[date, 'Close'] * asset_info['weight']
                total_value += asset_value
        
        portfolio_values.append(total_value)
        dates.append(date)
    
    # Calcola TWR
    twr = calculate_twr(portfolio_values, dates)
    
    # Calcola Drawdown
    drawdowns, max_drawdown = calculate_drawdowns(portfolio_values)
    
    # Calcola CAGR (se il periodo lo consente)
    cagr = None
    if len(portfolio_values) >= 2:
        days = (dates[-1] - dates[0]).days
        years = days / 365.25
        if years >= 1:  # Solo se abbiamo almeno un anno di dati
            cagr = calculate_cagr(portfolio_values[0], portfolio_values[-1], years)
    
    return {
        'values': portfolio_values,
        'dates': dates,
        'twr': twr,
        'max_drawdown': max_drawdown,
        'cagr': cagr
    }