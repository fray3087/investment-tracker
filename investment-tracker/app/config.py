import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

class Config:
    """Classe base di configurazione dell'applicazione"""
    
    # Chiave segreta per sicurezza delle sessioni e CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chiave-segreta-di-default'
    
    # Configurazione database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///investment_tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurazione mail (per reimpostazione password, ecc.)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['email@esempio.com']
    
    # Altre configurazioni
    ITEMS_PER_PAGE = 20
    
class DevelopmentConfig(Config):
    """Configurazione per l'ambiente di sviluppo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configurazione per l'ambiente di produzione"""
    DEBUG = False
    
    # In produzione, usa PostgreSQL invece di SQLite
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log degli errori via e-mail
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if cls.MAIL_USERNAME or cls.MAIL_PASSWORD:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=f'no-reply@{cls.MAIL_SERVER}',
            toaddrs=cls.ADMINS,
            subject='Errore nell\'Applicazione Investment Tracker',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

# Dizionario delle configurazioni disponibili
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}