from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField, TextAreaField, FileField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileAllowed


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
