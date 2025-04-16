from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, TextAreaField, FileField
from wtforms.fields import DateField, DecimalField, FloatField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileAllowed

# Monkey patch per assicurarsi che i campi abbiano l'attributo creation_counter
if not hasattr(DateField, "creation_counter"):
    DateField.creation_counter = 0
if not hasattr(DecimalField, "creation_counter"):
    DecimalField.creation_counter = 0
if not hasattr(FloatField, "creation_counter"):
    FloatField.creation_counter = 0

class TransactionForm(FlaskForm):
    transaction_date = DateField('Data operazione', format='%Y-%m-%d', validators=[DataRequired()])
    transaction_type = SelectField('Tipo di transazione', choices=[
        ('BUY', 'Acquisto'),
        ('SELL', 'Vendita')
    ], validators=[DataRequired()])
    shares = DecimalField('Quantità (azioni)', validators=[DataRequired(), NumberRange(min=0)])
    price = DecimalField('Prezzo per azione', validators=[DataRequired(), NumberRange(min=0)])
    commission = DecimalField('Commissioni', validators=[NumberRange(min=0)], default=0)
    notes = TextAreaField('Note')
    submit = SubmitField('Salva')


class ImportTransactionsForm(FlaskForm):
    csv_file = FileField('File CSV', validators=[
        DataRequired(),
        FileAllowed(['csv'], 'Solo file CSV!')
    ])
    submit = SubmitField('Importa')
