from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.forms.analysis import SimulationForm, FireForm, StressTestForm
from app.services.financial import simulate_future_investment, fire_calculator
from app.services.stress_test import StressTest
import pandas as pd
import numpy as np
import json
import yfinance as yf
from datetime import datetime
from sklearn.linear_model import LinearRegression

# Crea il blueprint
analysis = Blueprint('analysis', __name__)

@analysis.route('/dashboard')
@login_required
def dashboard():
    """Dashboard di analisi globale"""
    # Ottieni i portafogli dell'utente
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    
    # Se non ci sono portafogli, reindirizza alla creazione
    if not portfolios:
        flash('Crea un portafoglio per iniziare')
        return redirect(url_for('portfolio.create'))
    
    # Calcola i totali generali
    total_value = sum(p.current_value() for p in portfolios)
    total_invested = sum(p.invested_capital() for p in portfolios)
    total_return = 0
    if total_invested > 0:
        total_return = (total_value - total_invested) / total_invested * 100
    
    # Calcola l'allocazione per asset type
    allocation = {}
    for portfolio in portfolios:
        for asset in portfolio.assets:
            asset_type = asset.asset_type or 'Non specificato'
            if asset_type not in allocation:
                allocation[asset_type] = 0
            allocation[asset_type] += asset.current_value()
    
    # Converti in percentuali
    allocation_percent = {}
    for asset_type, value in allocation.items():
        if total_value > 0:
            allocation_percent[asset_type] = (value / total_value) * 100
        else:
            allocation_percent[asset_type] = 0
    
    # Ottieni i primi 5 asset per valore
    all_assets = []
    for portfolio in portfolios:
        for asset in portfolio.assets:
            all_assets.append({
                'id': asset.id,
                'ticker': asset.ticker,
                'name': asset.name,
                'value': asset.current_value(),
                'portfolio': portfolio.name
            })
    
    # Ordina per valore e prendi i primi 5
    top_assets = sorted(all_assets, key=lambda x: x['value'], reverse=True)[:5]
    
    # Calcola i dati storici aggregati
    historical_data = calculate_historical_portfolio_values(portfolios)
    
    return render_template('analysis/dashboard.html',
                          title='Analisi Investimenti',
                          portfolios=portfolios,
                          total_value=total_value,
                          total_invested=total_invested,
                          total_return=total_return,
                          allocation=allocation_percent,
                          top_assets=top_assets,
                          historical_data=json.dumps(historical_data))

def calculate_historical_portfolio_values(portfolios):
    """Calcola i valori storici aggregati dei portafogli"""
    # Dizionario per memorizzare i valori giornalieri
    daily_values = {}
    
    for portfolio in portfolios:
        for asset in portfolio.assets:
            # Ottieni dati storici dell'asset
            hist = asset.get_historical_data(period='1y')
            if hist.empty:
                continue
                
            # Calcola il peso attuale dell'asset
            weight = asset.current_value() / portfolio.current_value() if portfolio.current_value() > 0 else 0
            
            # Moltiplica i prezzi storici per il peso attuale
            for date, row in hist.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                if date_str not in daily_values:
                    daily_values[date_str] = 0
                daily_values[date_str] += row['Close'] * weight
    
    # Converti in formato per il grafico
    result = []
    for date, value in sorted(daily_values.items()):
        result.append({
            'date': date,
            'value': value
        })
    
    return result

@analysis.route('/simulation', methods=['GET', 'POST'])
@login_required
def simulation():
    """Simulazione di investimenti futuri"""
    form = SimulationForm()
    
    # Carica opzioni per il portafoglio iniziale
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    form.initial_portfolio.choices = [('0', 'Nessuno')] + [(p.id, p.name) for p in portfolios]
    
    if form.validate_on_submit():
        # Ottieni il capitale iniziale (dal form o dal portafoglio selezionato)
        initial_capital = form.initial_capital.data
        if form.initial_portfolio.data != '0':
            portfolio = Portfolio.query.get(form.initial_portfolio.data)
            if portfolio and portfolio.user_id == current_user.id:
                initial_capital = portfolio.current_value()
        
        # Esegui la simulazione
        result = simulate_future_investment(
            initial_capital=initial_capital,
            monthly_contribution=form.monthly_contribution.data,
            years=form.years.data,
            annual_return=form.annual_return.data / 100,  # Converti in decimale
            inflation_rate=form.inflation_rate.data / 100  # Converti in decimale
        )
        
        # Prepara i dati per i grafici
        chart_data = []
        for i, (nominal, real) in enumerate(zip(result['monthly_values']['nominal'], result['monthly_values']['real'])):
            chart_data.append({
                'month': i,
                'nominal': nominal,
                'real': real
            })
        
        return render_template('analysis/simulation_results.html',
                              title='Risultati Simulazione',
                              result=result,
                              form_data={
                                  'initial_capital': initial_capital,
                                  'monthly_contribution': form.monthly_contribution.data,
                                  'years': form.years.data,
                                  'annual_return': form.annual_return.data,
                                  'inflation_rate': form.inflation_rate.data
                              },
                              chart_data=json.dumps(chart_data))
    
    # Valori predefiniti
    form.annual_return.data = 7.0
    form.inflation_rate.data = 2.0
    
    return render_template('analysis/simulation.html',
                          title='Simulazione Investimenti',
                          form=form)

@analysis.route('/fire', methods=['GET', 'POST'])
@login_required
def fire():
    """Calcolatore FIRE (Financial Independence, Retire Early)"""
    form = FireForm()
    
    # Carica opzioni per il portafoglio attuale
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    form.current_portfolio.choices = [('0', 'Nessuno')] + [(p.id, p.name) for p in portfolios]
    
    if form.validate_on_submit():
        # Ottieni il capitale attuale (dal form o dal portafoglio selezionato)
        current_capital = form.current_capital.data
        if form.current_portfolio.data != '0':
            portfolio = Portfolio.query.get(form.current_portfolio.data)
            if portfolio and portfolio.user_id == current_user.id:
                current_capital = portfolio.current_value()
        
        # Esegui il calcolo FIRE
        result = fire_calculator(
            current_capital=current_capital,
            annual_expenses=form.annual_expenses.data,
            withdrawal_rate=form.withdrawal_rate.data / 100,  # Converti in decimale
            annual_return=form.annual_return.data / 100,  # Converti in decimale
            inflation_rate=form.inflation_rate.data / 100  # Converti in decimale
        )
        
        # Se aggiungiamo contributi mensili
        if form.monthly_contribution.data > 0:
            # Calcoliamo quanto tempo ci vuole con i contributi mensili
            monthly_return = (1 + form.annual_return.data / 100) ** (1/12) - 1
            target_capital = result['required_capital']
            
            # Simulazione mese per mese
            capital = current_capital
            months = 0
            max_months = 12 * 100  # Limitiamo a 100 anni
            
            while capital < target_capital and months < max_months:
                capital = capital * (1 + monthly_return) + form.monthly_contribution.data
                months += 1
            
            years_with_contributions = months / 12
            result['years_with_contributions'] = years_with_contributions
            result['monthly_contribution'] = form.monthly_contribution.data
        
        return render_template('analysis/fire_results.html',
                              title='Risultati FIRE',
                              result=result,
                              form_data={
                                  'current_capital': current_capital,
                                  'annual_expenses': form.annual_expenses.data,
                                  'withdrawal_rate': form.withdrawal_rate.data,
                                  'annual_return': form.annual_return.data,
                                  'inflation_rate': form.inflation_rate.data,
                                  'monthly_contribution': form.monthly_contribution.data
                              })
    
    # Valori predefiniti
    form.withdrawal_rate.data = 4.0
    form.annual_return.data = 7.0
    form.inflation_rate.data = 2.0
    
    return render_template('analysis/fire.html',
                          title='Calcolatore FIRE',
                          form=form)

@analysis.route('/stress_test/<portfolio_id>', methods=['GET', 'POST'])
@login_required
def stress_test(portfolio_id):
    """Stress test del portafoglio"""
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    
    # Verifica che l'utente sia il proprietario del portafoglio
    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato a visualizzare questo portafoglio')
        return redirect(url_for('portfolio.list'))
    
    # Ottieni gli asset del portafoglio
    assets = Asset.query.filter_by(portfolio_id=portfolio_id).all()
    
    # Se non ci sono asset, mostra un messaggio
    if not assets:
        flash('Aggiungi asset al portafoglio per eseguire lo stress test')
        return redirect(url_for('portfolio.view', id=portfolio_id))
    
    # Crea l'oggetto StressTest
    stress_test = StressTest(assets)
    
    # Esegui gli scenari
    scenarios_results = stress_test.run_all_scenarios()
    
    # Esegui la simulazione Monte Carlo
    monte_carlo_results = stress_test.monte_carlo_simulation(n_simulations=500, years=10)
    
    # Prepara i dati per i grafici
    monte_carlo_data = {
        'median': monte_carlo_results['percentiles']['median'].tolist(),
        'lower_5': monte_carlo_results['percentiles']['lower_5'].tolist(),
        'upper_95': monte_carlo_results['percentiles']['upper_95'].tolist(),
        'years': monte_carlo_results['years']
    }
    
    return render_template('analysis/stress_test.html',
                          title=f'Stress Test - {portfolio.name}',
                          portfolio=portfolio,
                          scenarios=scenarios_results,
                          monte_carlo=monte_carlo_results,
                          monte_carlo_data=json.dumps(monte_carlo_data))

@analysis.route('/correlation/<portfolio_id>')
@login_required
def correlation(portfolio_id):
    """Analisi di correlazione tra gli asset del portafoglio"""
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    
    # Verifica che l'utente sia il proprietario del portafoglio
    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato a visualizzare questo portafoglio')
        return redirect(url_for('portfolio.list'))
    
    # Ottieni gli asset del portafoglio
    assets = Asset.query.filter_by(portfolio_id=portfolio_id).all()
    
    # Se non ci sono abbastanza asset, mostra un messaggio
    if len(assets) < 2:
        flash('Servono almeno 2 asset per calcolare la correlazione')
        return redirect(url_for('portfolio.view', id=portfolio_id))
    
    # Ottieni i rendimenti giornalieri per ogni asset
    returns_data = {}
    for asset in assets:
        hist = asset.get_historical_data(period='1y')
        if not hist.empty:
            returns = hist['Close'].pct_change().dropna()
            returns_data[asset.ticker] = returns
    
    # Crea un DataFrame con tutti i rendimenti
    returns_df = pd.DataFrame(returns_data)
    
    # Calcola la matrice di correlazione
    corr_matrix = returns_df.corr()
    
    # Converti la matrice in un formato per il grafico a calore
    correlation_data = []
    for i, ticker1 in enumerate(corr_matrix.index):
        for j, ticker2 in enumerate(corr_matrix.columns):
            correlation_data.append({
                'x': ticker1,
                'y': ticker2,
                'value': corr_matrix.iloc[i, j]
            })
    
    # Prepara i dati per il grafico a dispersione
    scatter_data = {}
    for asset in assets:
        if asset.ticker in returns_data:
            scatter_data[asset.ticker] = returns_data[asset.ticker].tolist()
    
    return render_template('analysis/correlation.html',
                          title=f'Correlazione - {portfolio.name}',
                          portfolio=portfolio,
                          assets=assets,
                          correlation_matrix=corr_matrix.to_html(classes='table table-striped table-hover'),
                          correlation_data=json.dumps(correlation_data),
                          scatter_data=json.dumps(scatter_data))

@analysis.route('/compare', methods=['GET', 'POST'])
@login_required
def compare():
    """Confronta le performance di diversi portafogli"""
    # Ottieni i portafogli dell'utente
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    
    # Se non ci sono abbastanza portafogli, mostra un messaggio
    if len(portfolios) < 2:
        flash('Servono almeno 2 portafogli per il confronto')
        return redirect(url_for('portfolio.list'))
    
    selected_ids = request.form.getlist('portfolio_ids')
    
    if request.method == 'POST' and selected_ids:
        # Filtra i portafogli selezionati
        selected_portfolios = [p for p in portfolios if p.id in selected_ids]
        
        # Calcola le performance per ogni portafoglio
        performance_data = {}
        for portfolio in selected_portfolios:
            performance = calculate_portfolio_performance(portfolio, portfolio.assets.all(), '1y')
            if performance and performance['values']:
                # Normalizza i valori (primo valore = 100)
                first_value = performance['values'][0]
                normalized_values = [v / first_value * 100 for v in performance['values']]
                
                performance_data[portfolio.name] = {
                    'values': normalized_values,
                    'dates': [d.strftime('%Y-%m-%d') for d in performance['dates']],
                    'twr': performance['twr'],
                    'max_drawdown': performance['max_drawdown']
                }
        
        # Confronta con benchmark selezionato
        benchmark_ticker = request.form.get('benchmark')
        benchmark_data = None
        
        if benchmark_ticker:
            try:
                benchmark = yf.Ticker(benchmark_ticker)
                hist = benchmark.history(period='1y')
                
                if not hist.empty:
                    # Normalizza i valori del benchmark (primo valore = 100)
                    first_value = hist['Close'].iloc[0]
                    normalized_values = [v / first_value * 100 for v in hist['Close']]
                    
                    benchmark_data = {
                        'name': benchmark.info.get('shortName', benchmark_ticker),
                        'values': normalized_values,
                        'dates': [d.strftime('%Y-%m-%d') for d in hist.index]
                    }
            except Exception as e:
                print(f"Errore nel recupero del benchmark {benchmark_ticker}: {e}")
        
        return render_template('analysis/compare_results.html',
                              title='Confronto Portafogli',
                              portfolios=selected_portfolios,
                              performance_data=json.dumps(performance_data),
                              benchmark_data=json.dumps(benchmark_data) if benchmark_data else None)
    
    # Opzioni benchmark
    benchmarks = [
        {'ticker': '^GSPC', 'name': 'S&P 500'},
        {'ticker': '^IXIC', 'name': 'NASDAQ Composite'},
        {'ticker': '^DJI', 'name': 'Dow Jones Industrial Average'},
        {'ticker': '^STOXX50E', 'name': 'EURO STOXX 50'},
        {'ticker': '^FTSE', 'name': 'FTSE 100'},
        {'ticker': '^N225', 'name': 'Nikkei 225'},
        {'ticker': 'VWCE.MI', 'name': 'Vanguard FTSE All-World UCITS ETF'},
        {'ticker': 'CSSPX.MI', 'name': 'iShares Core S&P 500 UCITS ETF'},
        {'ticker': 'SWDA.MI', 'name': 'iShares Core MSCI World UCITS ETF'},
        {'ticker': 'IWDA.AS', 'name': 'iShares Core MSCI World UCITS ETF'}
    ]
    
    return render_template('analysis/compare.html',
                          title='Confronto Portafogli',
                          portfolios=portfolios,
                          benchmarks=benchmarks)

def calculate_portfolio_performance(portfolio, assets, period):
    """Calcola le performance di un portafoglio"""
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
    
    # Calcola i rendimenti giornalieri
    returns = []
    for i in range(1, len(portfolio_values)):
        r = (portfolio_values[i] / portfolio_values[i-1]) - 1
        returns.append(r)
    
    # Calcola TWR
    twr = 0
    if len(returns) > 0:
        # TWR è il prodotto cumulativo dei rendimenti periodici
        twr = (np.prod([1 + r for r in returns]) - 1) * 100  # in percentuale
    
    # Calcola Drawdown
    max_value = portfolio_values[0]
    max_drawdown = 0
    
    for value in portfolio_values:
        max_value = max(max_value, value)
        drawdown = (max_value - value) / max_value * 100  # in percentuale
        max_drawdown = min(max_drawdown, -drawdown)  # usiamo valori negativi per i drawdown
    
    return {
        'values': portfolio_values,
        'dates': dates,
        'returns': returns,
        'twr': twr,
        'max_drawdown': max_drawdown
    }