from datetime import datetime
from app import db
import uuid

class Portfolio(db.Model):
    """Modello per i portafogli di investimento"""
    __tablename__ = 'portfolios'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    benchmark = db.Column(db.String(20))  # Ticker del benchmark di riferimento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chiave esterna per l'utente proprietario
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Relazioni
    assets = db.relationship('Asset', backref='portfolio', lazy='dynamic', cascade='all, delete-orphan')
    
    def current_value(self):
        """Calcola il valore attuale del portafoglio"""
        return sum(asset.current_value() for asset in self.assets)
    
    def invested_capital(self):
        """Calcola il capitale totale investito"""
        return sum(asset.invested_capital() for asset in self.assets)
    
    def total_commissions(self):
        """Calcola il totale delle commissioni pagate"""
        return sum(asset.total_commissions() for asset in self.assets)
    
    def total_return(self):
        """Calcola il rendimento totale"""
        invested = self.invested_capital()
        if invested == 0:
            return 0
        return (self.current_value() - invested) / invested * 100
    
    def asset_count(self):
        """Restituisce il numero di asset nel portafoglio"""
        return self.assets.count()
        
    def first_transaction_date(self):
        """Restituisce la data della prima transazione nel portafoglio"""
        from app.models.transaction import Transaction
        from app.models.asset import Asset
        
        # Trova la prima transazione tra tutti gli asset del portafoglio
        first_transaction = Transaction.query.join(Asset).filter(
            Asset.portfolio_id == self.id
        ).order_by(Transaction.transaction_date.asc()).first()
        
        return first_transaction.transaction_date if first_transaction else None
    
    def __repr__(self):
        return f'<Portfolio {self.name}>'