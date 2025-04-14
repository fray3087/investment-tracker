import os
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.transaction import Transaction

# Crea l'istanza dell'app usando la configurazione appropriata
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    """Funzione per aggiungere variabili al contesto della shell di Flask"""
    return {
        'db': db,
        'User': User,
        'Portfolio': Portfolio,
        'Asset': Asset,
        'Transaction': Transaction
    }

if __name__ == '__main__':
    app.run(debug=True)