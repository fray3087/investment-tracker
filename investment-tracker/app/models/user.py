from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from app import db, login_manager
import uuid

class User(UserMixin, db.Model):
    """Modello per gli utenti del sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    portfolios = db.relationship('Portfolio', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def password(self):
        """La password non è leggibile"""
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """
        Genera l'hash della password usando il metodo 'pbkdf2:sha256', 
        che è supportato da Werkzeug e riconosciuto correttamente da check_password_hash.
        """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def verify_password(self, password):
        """Verifica se la password inserita corrisponde all'hash memorizzato."""
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=3600):
        """Genera un token JWT per il reset della password."""
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_reset_password_token(token):
        """Verifica il token per il reset della password e restituisce l'utente corrispondente."""
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = data.get('reset_password')
            return User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(f"Errore nel verificare il token di reset: {e}")
            return None
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Carica l'utente dal database per Flask-Login."""
    return User.query.get(str(user_id))
