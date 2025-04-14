import pandas as pd
import csv
from io import StringIO
from datetime import datetime
from app import db
from app.models.transaction import Transaction
from app.models.asset import Asset
from app.models.portfolio import Portfolio

def generate_csv_template():
    """
    Genera il template CSV per l'importazione delle transazioni
    
    Returns:
        str: Contenuto del file CSV template
    """
    headers = ['ticker', 'transaction_date', 'transaction_type', 'shares', 'price', 'commission', 'notes']
    example_data = [
        ['AAPL', '2023-01-15', 'BUY', '10', '150.25', '9.99', 'Acquisto azioni Apple'],
        ['MSFT', '2023-02-20', 'BUY', '5', '280.15', '9.99', 'Acquisto azioni Microsoft'],
        ['AAPL', '2023-03-10', 'SELL', '3', '170.50', '9.99', 'Vendita parziale azioni Apple']
    ]
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(example_data)
    
    return output.getvalue()

def parse_transaction_csv(file_content, portfolio_id):
    """
    Parsa un file CSV di transazioni e le importa nel database
    
    Args:
        file_content: Contenuto del file CSV
        portfolio_id: ID del portafoglio in cui importare le transazioni
        
    Returns:
        tuple: (successo, report) dove il report contiene statistiche o errori
    """
    try:
        # Leggi il CSV
        df = pd.read_csv(StringIO(file_content))
        
        # Verifica che tutte le colonne richieste siano presenti
        required_columns = ['ticker', 'transaction_date', 'transaction_type', 'shares', 'price']
        for col in required_columns:
            if col not in df.columns:
                return False, f"Colonna richiesta mancante: {col}"
        
        # Inizializza contatori e report
        total_rows = len(df)
        imported_count = 0
        skipped_count = 0
        errors = []
        
        # Ottieni il portafoglio
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return False, f"Portafoglio con ID {portfolio_id} non trovato"
        
        # Itera sulle righe
        for idx, row in df.iterrows():
            try:
                # Gestisci i valori NaN
                commission = row.get('commission') if 'commission' in df.columns and not pd.isna(row['commission']) else None
                notes = row.get('notes') if 'notes' in df.columns and not pd.isna(row['notes']) else None
                
                # Verifica che il tipo di transazione sia valido
                transaction_type = row['transaction_type'].upper()
                if transaction_type not in ['BUY', 'SELL']:
                    errors.append(f"Riga {idx+2}: Tipo di transazione non valido. Deve essere BUY o SELL.")
                    skipped_count += 1
                    continue
                
                # Verifica che le azioni siano un numero positivo
                shares = float(row['shares'])
                if shares <= 0:
                    errors.append(f"Riga {idx+2}: Il numero di azioni deve essere positivo.")
                    skipped_count += 1
                    continue
                
                # Verifica che il prezzo sia valido
                price = float(row['price'])
                if price <= 0:
                    errors.append(f"Riga {idx+2}: Il prezzo deve essere positivo.")
                    skipped_count += 1
                    continue
                
                # Converti la data
                try:
                    transaction_date = datetime.strptime(row['transaction_date'], '%Y-%m-%d')
                except ValueError:
                    errors.append(f"Riga {idx+2}: Formato data non valido. Usa YYYY-MM-DD.")
                    skipped_count += 1
                    continue
                
                # Trova o crea l'asset
                ticker = row['ticker'].upper()
                asset = Asset.query.filter_by(ticker=ticker, portfolio_id=portfolio_id).first()
                
                if not asset:
                    # Se l'asset non esiste, crealo
                    import yfinance as yf
                    ticker_info = yf.Ticker(ticker).info
                    
                    asset_name = ticker_info.get('longName', ticker)
                    asset_type = 'STOCK'  # Default
                    if ticker_info.get('quoteType') == 'ETF':
                        asset_type = 'ETF'
                    
                    asset = Asset(
                        ticker=ticker,
                        name=asset_name,
                        asset_type=asset_type,
                        currency=ticker_info.get('currency', 'USD'),
                        portfolio_id=portfolio_id
                    )
                    db.session.add(asset)
                    db.session.flush()  # Genera l'ID senza committare
                
                # Crea la transazione
                transaction = Transaction(
                    transaction_date=transaction_date,
                    transaction_type=transaction_type,
                    shares=shares,
                    price=price,
                    commission=commission,
                    notes=notes,
                    asset_id=asset.id
                )
                
                db.session.add(transaction)
                imported_count += 1
            
            except Exception as e:
                errors.append(f"Riga {idx+2}: Errore durante l'importazione: {str(e)}")
                skipped_count += 1
        
        # Commit delle modifiche
        db.session.commit()
        
        # Crea il report
        report = {
            'total_rows': total_rows,
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'errors': errors
        }
        
        return True, report
        
    except Exception as e:
        return False, f"Errore nell'elaborazione del file CSV: {str(e)}"