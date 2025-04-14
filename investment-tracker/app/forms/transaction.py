from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

class ImportTransactionsForm(FlaskForm):
    """Form per l'importazione di transazioni da file CSV"""
    csv_file = FileField('File CSV', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'Solo file CSV sono supportati')
    ])
    submit = SubmitField('Importa')