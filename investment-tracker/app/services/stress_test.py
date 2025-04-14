import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

class StressTest:
    """Classe per eseguire stress test su un portafoglio"""
    
    # Definizione degli scenari storici
    SCENARIOS = {
        'dot_com_crash': {
            'name': 'Bolla Dot-Com',
            'start_date': '2000-03-10',
            'end_date': '2002-10-09',
            'description': 'Crollo del mercato dopo la bolla delle dot-com'
        },
        'financial_crisis': {
            'name': 'Crisi Finanziaria 2008',
            'start_date': '2007-10-09',
            'end_date': '2009-03-09',
            'description': 'Crisi finanziaria globale del 2008'
        },
        'covid_crash': {
            'name': 'Pandemia COVID-19',
            'start_date': '2020-02-19',
            'end_date': '2020-03-23',
            'description': 'Crollo del mercato dovuto alla pandemia COVID-19'
        },
        'inflation_2022': {
            'name': 'Crisi Inflazione 2022',
            'start_date': '2021-11-01',
            'end_date': '2022-10-12',
            'description': 'Crisi dovuta all\'aumento dell\'inflazione'
        },
        'euro_debt_crisis': {
            'name': 'Crisi Debito Europeo',
            'start_date': '2011-07-01',
            'end_date': '2012-07-26',
            'description': 'Crisi del debito sovrano europeo'
        }
    }
    
    def __init__(self, assets, weights=None):
        """
        Inizializza lo stress test
        
        Args:
            assets: Lista di oggetti Asset
            weights: Pesi degli asset nel portafoglio (opzionale)
        """
        self.assets = assets
        
        # Se i pesi non sono specificati, assumiamo una distribuzione equa
        if weights is None:
            total_value = sum(asset.current_value() for asset in assets)
            if total_value == 0:
                self.weights = [1/len(assets)] * len(assets)
            else:
                self.weights = [asset.current_value() / total_value for asset in assets]
        else:
            self.weights = weights
            
        # Verifica che i pesi sommino a 1
        if abs(sum(self.weights) - 1.0) > 0.0001:
            self.weights = [w / sum(self.weights) for w in self.weights]
            
    def run_scenario(self, scenario_key):
        """
        Esegue uno scenario di stress test
        
        Args:
            scenario_key: Chiave dello scenario da eseguire
            
        Returns:
            dict: Risultati dello scenario
        """
        if scenario_key not in self.SCENARIOS:
            raise ValueError(f"Scenario '{scenario_key}' non trovato")
            
        scenario = self.SCENARIOS[scenario_key]
        start_date = scenario['start_date']
        end_date = scenario['end_date']
        
        # Ottieni i rendimenti degli asset per il periodo dello scenario
        asset_returns = []
        for asset in self.assets:
            hist = asset.get_historical_data()
            
            # Filtra per il periodo dello scenario
            filtered_hist = hist[(hist.index >= start_date) & (hist.index <= end_date)]
            
            if not filtered_hist.empty:
                # Calcola il rendimento totale per il periodo
                start_price = filtered_hist['Close'].iloc[0]
                end_price = filtered_hist['Close'].iloc[-1]
                total_return = (end_price / start_price) - 1
            else:
                # Se non ci sono dati per questo periodo, assumiamo un proxy di mercato
                # Usiamo S&P 500 come fallback
                sp500 = yf.download('^GSPC', start=start_date, end=end_date)
                if not sp500.empty:
                    start_price = sp500['Close'].iloc[0]
                    end_price = sp500['Close'].iloc[-1]
                    total_return = (end_price / start_price) - 1
                else:
                    total_return = 0  # Fallback se non ci sono dati
                    
            asset_returns.append(total_return)
        
        # Calcola il rendimento del portafoglio
        portfolio_return = sum(r * w for r, w in zip(asset_returns, self.weights))
        
        # Calcola l'impatto in termini di valore
        total_value = sum(asset.current_value() for asset in self.assets)
        value_impact = total_value * portfolio_return
        
        return {
            'scenario': scenario,
            'portfolio_return': portfolio_return * 100,  # in percentuale
            'asset_returns': [r * 100 for r in asset_returns],  # in percentuale
            'value_impact': value_impact
        }
        
    def run_all_scenarios(self):
        """
        Esegue tutti gli scenari di stress test
        
        Returns:
            dict: Risultati di tutti gli scenari
        """
        results = {}
        for scenario_key in self.SCENARIOS:
            try:
                results[scenario_key] = self.run_scenario(scenario_key)
            except Exception as e:
                print(f"Errore nell'esecuzione dello scenario {scenario_key}: {e}")
                results[scenario_key] = None
                
        return results
        
    def monte_carlo_simulation(self, n_simulations=1000, years=10):
        """
        Esegue una simulazione Monte Carlo per stimare i possibili rendimenti futuri
        
        Args:
            n_simulations: Numero di simulazioni
            years: Anni di proiezione
            
        Returns:
            dict: Risultati della simulazione
        """
        # Ottieni i rendimenti storici per ogni asset
        all_returns = []
        for asset in self.assets:
            hist = asset.get_historical_data(period='5y')
            if not hist.empty:
                # Calcola i rendimenti giornalieri
                returns = hist['Close'].pct_change().dropna()
                all_returns.append(returns)
            else:
                # Fallback con S&P 500
                sp500 = yf.download('^GSPC', period='5y')
                returns = sp500['Close'].pct_change().dropna()
                all_returns.append(returns)
                
        # Calcola la media e la deviazione standard dei rendimenti
        mean_returns = [np.mean(r) * 252 for r in all_returns]  # Annualizziamo
        std_returns = [np.std(r) * np.sqrt(252) for r in all_returns]  # Annualizziamo
        
        # Matrice di correlazione
        returns_df = pd.concat(all_returns, axis=1)
        returns_df.columns = [f'asset_{i}' for i in range(len(all_returns))]
        corr_matrix = returns_df.corr()
        
        # Decomponi la matrice di correlazione (Cholesky)
        L = np.linalg.cholesky(corr_matrix)
        
        # Esegui le simulazioni
        n_days = 252 * years
        simulation_results = np.zeros((n_simulations, n_days))
        
        for sim in range(n_simulations):
            # Genera rendimenti correlati
            Z = np.random.normal(0, 1, size=(len(self.assets), n_days))
            correlated_returns = np.dot(L, Z)
            
            # Applica media e deviazione standard
            for i in range(len(self.assets)):
                correlated_returns[i] = correlated_returns[i] * std_returns[i] + mean_returns[i] / 252
                
            # Calcola il rendimento del portafoglio
            portfolio_returns = np.zeros(n_days)
            for i in range(len(self.assets)):
                portfolio_returns += correlated_returns[i] * self.weights[i]
                
            # Calcola il valore cumulativo
            initial_value = 1.0
            cumulative_values = initial_value * np.cumprod(1 + portfolio_returns)
            simulation_results[sim] = cumulative_values
            
        # Calcola percentili per intervalli di confidenza
        percentiles = {
            'lower_5': np.percentile(simulation_results, 5, axis=0),
            'lower_25': np.percentile(simulation_results, 25, axis=0),
            'median': np.percentile(simulation_results, 50, axis=0),
            'upper_75': np.percentile(simulation_results, 75, axis=0),
            'upper_95': np.percentile(simulation_results, 95, axis=0)
        }
        
        # Calcola probabilità di perdita
        final_values = simulation_results[:, -1]
        prob_loss = np.sum(final_values < 1.0) / n_simulations
        
        return {
            'simulation_results': simulation_results,
            'percentiles': percentiles,
            'probability_of_loss': prob_loss * 100,  # in percentuale
            'expected_return': (percentiles['median'][-1] - 1) * 100,  # in percentuale
            'mean_return': (np.mean(final_values) - 1) * 100,  # in percentuale
            'years': years
        }