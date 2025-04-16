from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.transaction import Transaction
from app.forms.asset import AssetForm, TransactionForm, AssetSearchForm
from app.forms.transaction import ImportTransactionsForm
from app.utils.csv_import import generate_csv_template, parse_transaction_csv
import yfinance as yf
from datetime import datetime
import json

# Crea il blueprint
asset = Blueprint('asset', __name__)

from app.services.finnhub import search_symbol  # <-- in cima al file asset.py

@asset.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = AssetSearchForm()

    portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
    form.portfolio_id.choices = [(p.id, p.name) for p in portfolios]

    results = []

    if form.validate_on_submit():
        query = form.query.data.upper()
        portfolio_id = form.portfolio_id.data

        try:
            # Tentativo diretto con yfinance
            ticker = yf.Ticker(query)
            hist = ticker.history(period='1d')
            if not hist.empty:
                results.append({
                    'ticker': query,
                    'name': query,
                    'type': 'STOCK',
                    'exchange': 'Yahoo Finance'
                })
            else:
                # Fallback a Finnhub
                finnhub_results = search_symbol(query)
                for item in finnhub_results:
                    if item.get("symbol") and item.get("type") != "":
                        results.append({
                            'ticker': item.get("symbol"),
                            'name': item.get("description", item.get("symbol")),
                            'type': item.get("type"),
                            'exchange': item.get("displaySymbol")
                        })

        except Exception as e:
            flash(f"Errore nella ricerca: {e}", 'danger')
            return redirect(url_for('asset.search'))

        if not results:
            flash("Nessuno strumento trovato. Verifica il simbolo o il nome.", "warning")

        return render_template('asset/search.html',
                               title='Risultati ricerca',
                               results=results,
                               portfolio_id=portfolio_id,
                               form=form)

    # Se c'è un portfolio_id da GET, preimpostalo
    portfolio_id = request.args.get('portfolio_id')
    if portfolio_id:
        form.portfolio_id.data = portfolio_id

    return render_template("asset/search.html",
                           title='Cerca strumento',
                           form=form)


@asset.route('/add/<portfolio_id>/<ticker>', methods=['GET', 'POST'])
@login_required
def add(portfolio_id, ticker):
    """Aggiunge un nuovo asset al portafoglio"""
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    
    # Verifica proprietà del portafoglio
    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato ad aggiungere asset a questo portafoglio')
        return redirect(url_for('portfolio.list'))
    
    # Controlla se l’asset esiste già
    existing_asset = Asset.query.filter_by(ticker=ticker, portfolio_id=portfolio_id).first()
    if existing_asset:
        flash(f'Lo strumento {ticker} è già presente nel portafoglio')
        return redirect(url_for('asset.view', id=existing_asset.id))

    # Prova a ottenere il prezzo usando get_current_price() con fallback
    temp_asset = Asset(ticker=ticker)
    try:
        price = temp_asset.get_current_price()
        if price == 0:
            flash(f"⚠️ Nessun dato di prezzo disponibile per {ticker}. Verifica il simbolo o riprova più tardi.")
            return redirect(url_for('asset.search', portfolio_id=portfolio_id))
    except Exception as e:
        flash(f"Errore nel recupero delle informazioni per {ticker}: {e}")
        return redirect(url_for('asset.search', portfolio_id=portfolio_id))

    # Prova a ottenere info base da yfinance (ma ignora errori)
    name = ticker
    asset_type = 'STOCK'
    currency = 'USD'
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        name = info.get('longName', ticker)
        asset_type = info.get('quoteType', 'STOCK')
        currency = info.get('currency', 'USD')
    except Exception as e:
        print(f"[INFO FALLBACK] Errore info YF per {ticker}: {e}")

    # Precompila il form
    form = AssetForm()
    form.ticker.data = ticker
    form.name.data = name
    form.asset_type.data = asset_type
    form.currency.data = currency

    if form.validate_on_submit():
        # Salva nel DB
        new_asset = Asset(
            ticker=form.ticker.data,
            name=form.name.data,
            isin=form.isin.data,
            asset_type=form.asset_type.data,
            currency=form.currency.data,
            portfolio_id=portfolio_id
        )
        db.session.add(new_asset)
        db.session.commit()
        flash(f'✅ Asset {new_asset.name} aggiunto con successo!')
        return redirect(url_for('asset.view', id=new_asset.id))

    return render_template('asset/add.html',
                           title=f'Aggiungi {ticker}',
                           form=form,
                           ticker=ticker,
                           portfolio=portfolio)


@asset.route('/view/<id>')
@login_required
def view(id):
    """Visualizza i dettagli di un asset"""
    asset_obj = Asset.query.get_or_404(id)
    portfolio = Portfolio.query.get_or_404(asset_obj.portfolio_id)

    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato a visualizzare questo asset')
        return redirect(url_for('portfolio.list'))

    transactions = Transaction.query.filter_by(asset_id=id).order_by(Transaction.transaction_date.desc()).all()

    stats = {
        'current_shares': asset_obj.current_shares(),
        'current_value': asset_obj.current_value(),
        'invested_capital': asset_obj.invested_capital(),
        'total_commissions': asset_obj.total_commissions(),
        'performance': asset_obj.calculate_my_performance(),
        'current_price': asset_obj.get_current_price()
    }

    performance = {}
    periods = {
        '1m': '1 mese',
        '3m': '3 mesi',
        '6m': '6 mesi',
        'ytd': 'Anno corrente',
        '1y': '1 anno',
        '3y': '3 anni',
        '5y': '5 anni',
        'max': 'Dall\'inizio'
    }

    for period_key, period_name in periods.items():
        try:
            perf = asset_obj.calculate_performance(period_key)
            performance[period_key] = {
                'name': period_name,
                'value': perf
            }
        except Exception as e:
            print(f"Errore nel calcolo della performance {period_name}: {e}")

    hist_data = asset_obj.get_historical_data(period='1y')
    chart_data = []

    if not hist_data.empty:
        for date, row in hist_data.iterrows():
            chart_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': row['Close']
            })

    return render_template('asset/view.html',
                           title=asset_obj.name,
                           asset=asset_obj,
                           portfolio=portfolio,
                           transactions=transactions,
                           stats=stats,
                           performance=performance,
                           chart_data=json.dumps(chart_data))

@asset.route('/delete/<id>', methods=['POST'])
@login_required
def delete(id):
    asset_obj = Asset.query.get_or_404(id)
    portfolio = Portfolio.query.get_or_404(asset_obj.portfolio_id)

    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato a eliminare questo asset')
        return redirect(url_for('portfolio.list'))

    portfolio_id = asset_obj.portfolio_id
    db.session.delete(asset_obj)
    db.session.commit()

    flash('Asset eliminato con successo')
    return redirect(url_for('portfolio.view', id=portfolio_id))

@asset.route('/transaction/add/<asset_id>', methods=['GET', 'POST'])
@login_required
def add_transaction(asset_id):
    asset_obj = Asset.query.get_or_404(asset_id)
    portfolio = Portfolio.query.get_or_404(asset_obj.portfolio_id)

    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato ad aggiungere transazioni a questo asset')
        return redirect(url_for('portfolio.list'))

    form = TransactionForm()

    if form.validate_on_submit():
        new_transaction = Transaction(
            transaction_date=form.transaction_date.data,
            transaction_type=form.transaction_type.data,
            shares=form.shares.data,
            price=form.price.data,
            commission=form.commission.data,
            notes=form.notes.data,
            asset_id=asset_id
        )

        db.session.add(new_transaction)
        db.session.commit()

        flash('Transazione aggiunta con successo')
        return redirect(url_for('asset.view', id=asset_id))

    form.price.data = asset_obj.get_current_price()

    return render_template('asset/add_transaction.html',
                           title=f'Aggiungi transazione - {asset_obj.name}',
                           form=form,
                           asset=asset_obj)

@asset.route('/transaction/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    asset_obj = Asset.query.get_or_404(transaction.asset_id)
    portfolio = Portfolio.query.get_or_404(asset_obj.portfolio_id)

    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato a modificare questa transazione')
        return redirect(url_for('portfolio.list'))

    form = TransactionForm(obj=transaction)

    if form.validate_on_submit():
        transaction.transaction_date = form.transaction_date.data
        transaction.transaction_type = form.transaction_type.data
        transaction.shares = form.shares.data
        transaction.price = form.price.data
        transaction.commission = form.commission.data
        transaction.notes = form.notes.data

        db.session.commit()

        flash('Transazione aggiornata con successo')
        return redirect(url_for('asset.view', id=asset_obj.id))

    return render_template('asset/edit_transaction.html',
                           title=f'Modifica transazione - {asset_obj.name}',
                           form=form,
                           transaction=transaction,
                           asset=asset_obj)

@asset.route('/transaction/delete/<id>', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    asset_obj = Asset.query.get_or_404(transaction.asset_id)
    portfolio = Portfolio.query.get_or_404(asset_obj.portfolio_id)

    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato a eliminare questa transazione')
        return redirect(url_for('portfolio.list'))

    asset_id = transaction.asset_id
    db.session.delete(transaction)
    db.session.commit()

    flash('Transazione eliminata con successo')
    return redirect(url_for('asset.view', id=asset_id))

@asset.route('/import/<portfolio_id>', methods=['GET', 'POST'])
@login_required
def import_transactions(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    if portfolio.user_id != current_user.id:
        flash('Non sei autorizzato a importare transazioni in questo portafoglio')
        return redirect(url_for('portfolio.list'))

    form = ImportTransactionsForm()

    if form.validate_on_submit():
        csv_file = form.csv_file.data
        csv_content = csv_file.read().decode('utf-8')

        success, result = parse_transaction_csv(csv_content, portfolio_id)

        if success:
            flash(f'Importazione completata: {result["imported_count"]} transazioni importate, {result["skipped_count"]} saltate')
            if result["errors"]:
                for error in result["errors"]:
                    flash(error, 'warning')

            return redirect(url_for('portfolio.view', id=portfolio_id))
        else:
            flash(f'Errore durante l\'importazione: {result}', 'danger')

    template = generate_csv_template()

    return render_template('asset/import.html',
                           title='Importa transazioni',
                           form=form,
                           portfolio=portfolio,
                           template=template)

@asset.route('/download_template')
@login_required
def download_template():
    template = generate_csv_template()
    return Response(
        template,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=transactions_template.csv"}
    )
