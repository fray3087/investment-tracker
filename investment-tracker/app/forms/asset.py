from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, FileField, DecimalField, FloatField
from wtforms.fields.html5 import DateField  # Import corretto per WTForms 2.3.3
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileAllowed

class AssetSearchForm(FlaskForm):
    """Form per la ricerca di strumenti finanziari"""
    query = StringField('Cerca per Ticker, ISIN o Nome', validators=[DataRequired(), Length(min=1, max=50)])
    portfolio_id = SelectField('Portafoglio', validators=[DataRequired()])
    submit = SubmitField('Cerca')

class AssetForm(FlaskForm):
    """Form per la creazione e modifica di asset"""
    ticker = StringField('Ticker', validators=[DataRequired(), Length(max=20)])
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    isin = StringField('ISIN', validators=[Optional(), Length(max=12)])
    asset_type = SelectField('Tipo', choices=[
        ('STOCK', 'Azione'),
        ('ETF', 'ETF'),
        ('BOND', 'Obbligazione'),
        ('FUND', 'Fondo'),
        ('CRYPTO', 'Criptovaluta'),
        ('COMMODITY', 'Materia Prima'),
        ('FOREX', 'Valuta'),
        ('OTHER', 'Altro')
    ], validators=[DataRequired()])
    currency = SelectField('Valuta', choices=[
        ('EUR', 'Euro (EUR)'),
        ('USD', 'Dollaro USA (USD)'),
        ('GBP', 'Sterlina (GBP)'),
        ('JPY', 'Yen (JPY)'),
        ('CHF', 'Franco Svizzero (CHF)'),
        ('CAD', 'Dollaro Canadese (CAD)'),
        ('AUD', 'Dollaro Australiano (AUD)'),
        ('CNY', 'Yuan (CNY)')
    ], validators=[DataRequired()])
    submit = SubmitField('Salva')

class TransactionForm(FlaskForm):
    """Form per la creazione e modifica di transazioni"""
    transaction_date = DateField('Data Transazione', format='%Y-%m-%d', validators=[DataRequired()])
    transaction_type = SelectField('Tipo', choices=[
        ('BUY', 'Acquisto'),
        ('SELL', 'Vendita')
    ], validators=[DataRequired()])
    shares = FloatField('Quantità', validators=[DataRequired(), NumberRange(min=0.0001)])
    price = FloatField('Prezzo per unità', validators=[DataRequired(), NumberRange(min=0.0001)])
    commission = FloatField('Commissione', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Note', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Salva')

class ImportTransactionsForm(FlaskForm):
    """Form per l'importazione di transazioni da file CSV"""
    csv_file = FileField('File CSV', validators=[
        DataRequired(),
        FileAllowed(['csv'], 'Solo file CSV sono supportati')
    ])
    submit = SubmitField('Importa')
