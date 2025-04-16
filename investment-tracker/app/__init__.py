from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from datetime import datetime

# Inizializzazione delle estensioni
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
csrf = CSRFProtect()  # Inizializza l'estensione CSRF
mail = Mail()         # Inizializza Flask-Mail

def create_app(config_name):
    """Factory function per creare l'istanza dell'applicazione Flask"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inizializzazione delle estensioni con l'app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)  # Inizializzazione CSRF
    mail.init_app(app)  # Inizializzazione di Flask-Mail
    
    # Registrazione dei blueprint
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.portfolio import portfolio as portfolio_blueprint
    app.register_blueprint(portfolio_blueprint, url_prefix='/portfolio')
    
    from app.routes.asset import asset as asset_blueprint
    app.register_blueprint(asset_blueprint, url_prefix='/asset')
    
    from app.routes.analysis import analysis as analysis_blueprint
    app.register_blueprint(analysis_blueprint, url_prefix='/analysis')
    
    from app.routes.errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)
    
    # Registrazione del filtro personalizzato per formattare le valute
    def format_currency(value):
        try:
            # Ad esempio, in questo caso formattiamo come dollari;
            # puoi modificare il simbolo o il formato secondo le tue esigenze.
            return "${:,.2f}".format(float(value))
        except (ValueError, TypeError):
            return value

    app.jinja_env.filters['format_currency'] = format_currency
    
    # Iniezione della data corrente nei template
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    return app
