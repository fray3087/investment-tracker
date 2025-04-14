from flask import Blueprint, render_template

# Crea il blueprint
errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def not_found_error(error):
    """Gestisce errori 404 - Pagina non trovata"""
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(500)
def internal_error(error):
    """Gestisce errori 500 - Errore interno del server"""
    from app import db
    db.session.rollback()  # In caso di errore, annulla le transazioni pendenti
    return render_template('errors/500.html'), 500

@errors.app_errorhandler(403)
def forbidden_error(error):
    """Gestisce errori 403 - Accesso negato"""
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(429)
def too_many_requests(error):
    """Gestisce errori 429 - Troppe richieste"""
    return render_template('errors/429.html'), 429