from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class SimulationForm(FlaskForm):
    """Form per la simulazione di investimenti futuri"""
    initial_capital = FloatField('Capitale iniziale (€)', validators=[DataRequired(), NumberRange(min=0)])
    initial_portfolio = SelectField('Usa valore del portafoglio', validators=[Optional()])
    monthly_contribution = FloatField('Contributo mensile (€)', validators=[DataRequired(), NumberRange(min=0)])
    years = IntegerField('Anni di investimento', validators=[DataRequired(), NumberRange(min=1, max=50)])
    annual_return = FloatField('Rendimento annuo atteso (%)', validators=[DataRequired(), NumberRange(min=-20, max=30)])
    inflation_rate = FloatField('Tasso di inflazione atteso (%)', validators=[DataRequired(), NumberRange(min=0, max=20)])
    submit = SubmitField('Simula')

class FireForm(FlaskForm):
    """Form per il calcolatore FIRE (Financial Independence, Retire Early)"""
    current_capital = FloatField('Capitale attuale (€)', validators=[DataRequired(), NumberRange(min=0)])
    current_portfolio = SelectField('Usa valore del portafoglio', validators=[Optional()])
    annual_expenses = FloatField('Spese annuali (€)', validators=[DataRequired(), NumberRange(min=0)])
    withdrawal_rate = FloatField('Tasso di prelievo sicuro (%)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    annual_return = FloatField('Rendimento annuo atteso (%)', validators=[DataRequired(), NumberRange(min=-5, max=30)])
    inflation_rate = FloatField('Tasso di inflazione atteso (%)', validators=[DataRequired(), NumberRange(min=0, max=20)])
    monthly_contribution = FloatField('Contributo mensile (€)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Calcola')

class StressTestForm(FlaskForm):
    """Form per lo stress test del portafoglio"""
    portfolio_id = SelectField('Portafoglio', validators=[DataRequired()])
    scenario = SelectField('Scenario', choices=[
        ('dot_com_crash', 'Bolla Dot-Com (2000-2002)'),
        ('financial_crisis', 'Crisi Finanziaria (2007-2009)'),
        ('covid_crash', 'Pandemia COVID-19 (2020)'),
        ('inflation_2022', 'Crisi Inflazione (2021-2022)'),
        ('euro_debt_crisis', 'Crisi Debito Europeo (2011-2012)')
    ], validators=[DataRequired()])
    submit = SubmitField('Esegui Stress Test')