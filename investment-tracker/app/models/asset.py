from datetime import datetime
from app import db
import uuid
import yfinance as yf
import pandas as pd

class Asset(db.Model):
    """Modello per gli strumenti finanziari"""
    __tablename__ = 'assets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticker = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    isin = db.Column(db.String(12))
    asset_type = db.Column(db.String(50))  # azione, ETF, obbligazione, ecc.
    currency = db.Column(db.String(3))  # EUR, USD, ecc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Campi per memorizzare dati storici (per migliorare le performance)
    last_price = db.Column(db.Float)
    last_price_update = db.Column(db.DateTime)
    
    # Chiave esterna per il portafoglio
    portfolio_id = db.Column(db.String(36), db.ForeignKey('portfolios.id'), nullable=False)
    
    # Relazioni
    transactions = db.relationship('Transaction', backref='asset', lazy='dynamic', cascade='all, delete-orphan')
    
    def current_shares(self):
        """Calcola il numero attuale di azioni possedute"""
        return sum(t.shares for t in self.transactions)
    
    def current_value(self):
        """Calcola il valore attuale dell'asset"""
        shares = self.current_shares()
        
        # Se non ci sono azioni, il valore è 0
        if shares == 0:
            return 0
            
        # Ottieni il prezzo attuale
        current_price = self.get_current_price()
        
        return shares * current_price
    
    def invested_capital(self):
        """Calcola il capitale investito (escluse le commissioni)"""
        return sum(t.shares * t.price for t in self.transactions if t.transaction_type == 'BUY') - \
               sum(t.shares * t.price for t in self.transactions if t.transaction_type == 'SELL')
    
    def total_commissions(self):
        """Calcola il totale delle commissioni pagate"""
        return sum(t.commission for t in self.transactions if t.commission is not None)
    
    def get_current_price(self):
        """Ottiene il prezzo attuale usando yfinance"""
        # Se il prezzo è stato aggiornato di recente, usalo
        if self.last_price and self.last_price_update and \
           (datetime.utcnow() - self.last_price_update).total_seconds() < 3600:  # 1 ora
            return self.last_price
            
        # Altrimenti, ottieni il prezzo da Yahoo Finance
        try:
            ticker_data = yf.Ticker(self.ticker)
            price = ticker_data.history(period='1d')['Close'].iloc[-1]
            
            # Aggiorna il prezzo nel database
            self.last_price = price
            self.last_price_update = datetime.utcnow()
            db.session.commit()
            
            return price
        except Exception as e:
            print(f"Errore nel recupero del prezzo per {self.ticker}: {e}")
            # In caso di errore, usa l'ultimo prezzo noto
            return self.last_price or 0
    
    def get_historical_data(self, period='max'):
        """Ottiene i dati storici dell'asset"""
        try:
            ticker_data = yf.Ticker(self.ticker)
            hist = ticker_data.history(period=period)
            return hist
        except Exception as e:
            print(f"Errore nel recupero dei dati storici per {self.ticker}: {e}")
            return pd.DataFrame()
    
    def calculate_performance(self, period):
        """Calcola la performance dell'asset per un periodo specifico"""
        hist = self.get_historical_data(period=period)
        
        if hist.empty:
            return 0
            
        # Calcola il rendimento percentuale
        first_price = hist['Close'].iloc[0]
        last_price = hist['Close'].iloc[-1]
        
        return (last_price - first_price) / first_price * 100
    
    def calculate_my_performance(self):
        """Calcola la performance personale basata sulle transazioni"""
        invested = self.invested_capital()
        current = self.current_value()
        
        if invested == 0:
            return 0
            
        return (current - invested) / invested * 100
    
    def __repr__(self):
        return f'<Asset {self.ticker}>'