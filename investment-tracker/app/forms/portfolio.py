from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional

class PortfolioForm(FlaskForm):
    """Form per la creazione e modifica di portafogli"""
    name = StringField('Nome del portafoglio', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=500)])
    benchmark = SelectField('Benchmark di riferimento', choices=[
        ('', 'Nessun benchmark'),
        ('^GSPC', 'S&P 500'),
        ('^IXIC', 'NASDAQ Composite'),
        ('^DJI', 'Dow Jones Industrial Average'),
        ('^STOXX50E', 'EURO STOXX 50'),
        ('^FTSE', 'FTSE 100'),
        ('^N225', 'Nikkei 225'),
        ('VWCE.MI', 'Vanguard FTSE All-World UCITS ETF'),
        ('CSSPX.MI', 'iShares Core S&P 500 UCITS ETF'),
        ('SWDA.MI', 'iShares Core MSCI World UCITS ETF'),
        ('IWDA.AS', 'iShares Core MSCI World UCITS ETF')
    ], validators=[Optional()])
    submit = SubmitField('Salva')