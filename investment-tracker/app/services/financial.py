import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from sklearn.linear_model import LinearRegression

def calculate_twr(values, dates):
    """
    Calcola il Time-Weighted Return (TWR)
    
    Args:
        values: Lista di valori del portafoglio
        dates: Lista di date corrispondenti
        
    Returns:
        float: TWR espresso in percentuale
    """
    if len(values) < 2:
        return 0
        
    # Calcola i rendimenti periodici
    periodic_returns = []
    for i in range(1, len(values)):
        r = (values[i] / values[i-1]) - 1
        periodic_returns.append(1 + r)
    
    # TWR è il prodotto dei rendimenti periodici meno 1
    twr = np.prod(periodic_returns) - 1
    return twr * 100  # Converti in percentuale

def calculate_mwr(cash_flows, dates, final_value):
    """
    Calcola il Money-Weighted Return (MWR) o Internal Rate of Return (IRR)
    
    Args:
        cash_flows: Lista di flussi di cassa (positivi per depositi, negativi per prelievi)
        dates: Lista di date corrispondenti
        final_value: Valore finale del portafoglio
        
    Returns:
        float: MWR espresso in percentuale
    """
    if not cash_flows:
        return 0
        
    # Aggiungi il valore finale come ultimo flusso negativo
    all_flows = cash_flows + [-final_value]
    all_dates = dates + [datetime.now()]
    
    # Converti le date in giorni rispetto alla prima data
    day_diffs = [(date - all_dates[0]).days for date in all_dates]
    
    # Calcola l'IRR
    try:
        irr = np.irr(all_flows)
        # Converti il tasso di rendimento giornaliero in annualizzato
        mwr = (1 + irr) ** 365 - 1
        return mwr * 100
    except Exception as e:
        print(f"Errore nel calcolo dell'IRR: {e}")
        return 0

def calculate_cagr(initial_value, final_value, years):
    """
    Calcola il Compound Annual Growth Rate (CAGR)
    
    Args:
        initial_value: Valore iniziale dell'investimento
        final_value: Valore finale dell'investimento
        years: Numero di anni
        
    Returns:
        float: CAGR espresso in percentuale
    """
    if initial_value <= 0 or years <= 0:
        return 0
        
    cagr = (final_value / initial_value) ** (1 / years) - 1
    return cagr * 100

def calculate_volatility(returns, annualize=True):
    """
    Calcola la volatilità (deviazione standard) dei rendimenti
    
    Args:
        returns: Serie di rendimenti percentuali
        annualize: Se True, annualizza la volatilità
        
    Returns:
        float: Volatilità espressa in percentuale
    """
    volatility = np.std(returns)
    
    # Annualizza la volatilità se richiesto (assumendo rendimenti giornalieri)
    if annualize:
        volatility = volatility * np.sqrt(252)
        
    return volatility

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    Calcola il Sharpe Ratio
    
    Args:
        returns: Serie di rendimenti percentuali annualizzati
        risk_free_rate: Tasso privo di rischio (default 2%)
        
    Returns:
        float: Sharpe Ratio
    """
    excess_return = np.mean(returns) - risk_free_rate
    volatility = calculate_volatility(returns)
    
    if volatility == 0:
        return 0
        
    return excess_return / volatility

def calculate_drawdowns(values):
    """
    Calcola i drawdown del portafoglio
    
    Args:
        values: Serie temporale di valori del portafoglio
        
    Returns:
        tuple: (drawdowns, max_drawdown)
    """
    # Calcola il massimo cumulativo
    running_max = np.maximum.accumulate(values)
    
    # Calcola il drawdown come percentuale del massimo
    drawdowns = (values - running_max) / running_max * 100
    
    # Calcola il massimo drawdown
    max_drawdown = np.min(drawdowns)
    
    return drawdowns, max_drawdown

def calculate_beta(portfolio_returns, benchmark_returns):
    """
    Calcola il beta del portafoglio rispetto al benchmark
    
    Args:
        portfolio_returns: Serie di rendimenti del portafoglio
        benchmark_returns: Serie di rendimenti del benchmark
        
    Returns:
        float: Beta
    """
    # Rimuovi i valori NaN
    valid_data = ~(np.isnan(portfolio_returns) | np.isnan(benchmark_returns))
    port_returns = portfolio_returns[valid_data]
    bench_returns = benchmark_returns[valid_data]
    
    if len(port_returns) < 2:
        return 1.0
    
    # Utilizza regressione lineare per calcolare il beta
    model = LinearRegression()
    model.fit(bench_returns.values.reshape(-1, 1), port_returns.values.reshape(-1, 1))
    
    return model.coef_[0][0]

def calculate_alpha(portfolio_returns, benchmark_returns, risk_free_rate=0.02):
    """
    Calcola l'alpha di Jensen del portafoglio
    
    Args:
        portfolio_returns: Serie di rendimenti del portafoglio
        benchmark_returns: Serie di rendimenti del benchmark
        risk_free_rate: Tasso privo di rischio (default 2%)
        
    Returns:
        float: Alpha
    """
    beta = calculate_beta(portfolio_returns, benchmark_returns)
    
    # Calcola rendimenti medi annualizzati
    avg_portfolio_return = np.mean(portfolio_returns) * 252
    avg_benchmark_return = np.mean(benchmark_returns) * 252
    
    # Calcola l'alpha
    alpha = avg_portfolio_return - (risk_free_rate + beta * (avg_benchmark_return - risk_free_rate))
    
    return alpha

def simulate_future_investment(initial_capital, monthly_contribution, years, annual_return, inflation_rate=0.02):
    """
    Simula un investimento futuro con contributi mensili
    
    Args:
        initial_capital: Capitale iniziale
        monthly_contribution: Contributo mensile
        years: Anni di investimento
        annual_return: Rendimento annuo atteso
        inflation_rate: Tasso di inflazione atteso
        
    Returns:
        dict: Risultati della simulazione
    """
    # Calcola il tasso di rendimento mensile
    monthly_return = (1 + annual_return) ** (1/12) - 1
    
    # Calcola il tasso di inflazione mensile
    monthly_inflation = (1 + inflation_rate) ** (1/12) - 1
    
    # Array per memorizzare i valori per ogni mese
    months = years * 12
    nominal_values = np.zeros(months + 1)
    real_values = np.zeros(months + 1)
    
    # Valore iniziale
    nominal_values[0] = initial_capital
    real_values[0] = initial_capital
    
    for i in range(1, months + 1):
        # Calcola il nuovo valore nominale
        nominal_values[i] = (nominal_values[i-1] * (1 + monthly_return)) + monthly_contribution
        
        # Calcola il nuovo valore reale (aggiustato per inflazione)
        real_values[i] = nominal_values[i] / ((1 + monthly_inflation) ** i)
    
    # Calcola statistiche
    total_contributions = initial_capital + (monthly_contribution * months)
    interest_earned = nominal_values[-1] - total_contributions
    
    return {
        'nominal_final_value': nominal_values[-1],
        'real_final_value': real_values[-1],
        'total_contributions': total_contributions,
        'interest_earned': interest_earned,
        'monthly_values': {
            'nominal': nominal_values,
            'real': real_values
        }
    }

def fire_calculator(current_capital, annual_expenses, withdrawal_rate=0.04, annual_return=0.07, inflation_rate=0.02):
    """
    Calcola se è possibile raggiungere l'indipendenza finanziaria (FIRE)
    
    Args:
        current_capital: Capitale attuale
        annual_expenses: Spese annuali attuali
        withdrawal_rate: Tasso di prelievo sicuro (default 4%)
        annual_return: Rendimento annuo atteso
        inflation_rate: Tasso di inflazione atteso
        
    Returns:
        dict: Risultati dell'analisi FIRE
    """
    # Calcola il capitale necessario per il FIRE
    required_capital = annual_expenses / withdrawal_rate
    
    # Calcola quanti anni mancano per raggiungere il capitale necessario
    if current_capital >= required_capital:
        years_to_fire = 0
    else:
        # Calcola anni necessari (formula logaritmica)
        years_to_fire = np.log(required_capital / current_capital) / np.log(1 + annual_return)
    
    # Calcola il potere d'acquisto del capitale dopo l'inflazione
    purchasing_power = required_capital * ((1 + withdrawal_rate - inflation_rate) / (1 + withdrawal_rate))
    
    return {
        'required_capital': required_capital,
        'years_to_fire': years_to_fire,
        'annual_withdrawal': annual_expenses,
        'purchasing_power_after_30_years': purchasing_power * ((1 - inflation_rate) ** 30)
    }

def get_benchmark_data(ticker, period='5y'):
    """
    Ottiene i dati storici di un benchmark
    
    Args:
        ticker: Ticker del benchmark
        period: Periodo di tempo
        
    Returns:
        DataFrame: Dati storici del benchmark
    """
    try:
        benchmark = yf.Ticker(ticker)
        hist = benchmark.history(period=period)
        return hist
    except Exception as e:
        print(f"Errore nel recupero dei dati del benchmark {ticker}: {e}")
        return pd.DataFrame()