from datetime import datetime
from app import db
import uuid

class Transaction(db.Model):
    """Modello per le transazioni finanziarie"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_date = db.Column(db.DateTime, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # BUY o SELL
    shares = db.Column(db.Float, nullable=False)  # Numero di azioni
    price = db.Column(db.Float, nullable=False)  # Prezzo per azione
    commission = db.Column(db.Float)  # Commissione (opzionale)
    notes = db.Column(db.Text)  # Note sulla transazione
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chiave esterna per l'asset
    asset_id = db.Column(db.String(36), db.ForeignKey('assets.id'), nullable=False)
    
    def total_amount(self):
        """Calcola l'importo totale della transazione (esclusa commissione)"""
        return self.shares * self.price
    
    def total_with_commission(self):
        """Calcola l'importo totale della transazione (inclusa commissione)"""
        total = self.total_amount()
        if self.commission:
            total += self.commission
        return total
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.shares} shares at {self.price}>'