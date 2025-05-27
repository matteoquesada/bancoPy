import sqlite3
import uuid
from datetime import datetime

DB_PATH = "cuentas_banco.db" # Changed DB name slightly to avoid conflict if old one exists

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Add phone_number to cuentas table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cuentas (
            account_number TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            saldo REAL NOT NULL,
            phone_number TEXT UNIQUE
        )
    ''')
    # Create transactions table for audit logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            from_account_number TEXT,
            to_account_number TEXT,
            to_phone_number TEXT, 
            amount REAL NOT NULL,
            currency TEXT,
            status TEXT NOT NULL, 
            description TEXT,
            external_transaction_id TEXT,
            hmac_signature_sent TEXT,
            hmac_signature_received TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_account(account_number, nombre, saldo, phone_number=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO cuentas (account_number, nombre, saldo, phone_number) VALUES (?, ?, ?, ?)', 
                  (account_number, nombre, saldo, phone_number))
        conn.commit()
        return True
    except sqlite3.IntegrityError: # Handles duplicate account_number or phone_number
        return False
    finally:
        conn.close()

def delete_account(account_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM cuentas WHERE account_number = ?', (account_number,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted

def get_account(account_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT account_number, nombre, saldo, phone_number FROM cuentas WHERE account_number = ?', (account_number,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"account_number": row[0], "nombre": row[1], "saldo": row[2], "phone_number": row[3]}
    return None

def get_account_by_phone(phone_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT account_number, nombre, saldo, phone_number FROM cuentas WHERE phone_number = ?', (phone_number,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"account_number": row[0], "nombre": row[1], "saldo": row[2], "phone_number": row[3]}
    return None

def update_balance(account_number, new_saldo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE cuentas SET saldo = ? WHERE account_number = ?', (new_saldo, account_number))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def list_accounts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT account_number, nombre, saldo, phone_number FROM cuentas')
    rows = c.fetchall()
    conn.close()
    return [{"account_number": row[0], "nombre": row[1], "saldo": row[2], "phone_number": row[3]} for row in rows]

def log_transaction(transaction_type, amount, currency, status, 
                    from_account_number=None, to_account_number=None, to_phone_number=None,
                    description=None, external_transaction_id=None, 
                    hmac_signature_sent=None, hmac_signature_received=None, notes=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    tx_id = str(uuid.uuid4())
    ts = datetime.utcnow().isoformat()
    try:
        c.execute('''
            INSERT INTO transactions (
                transaction_id, timestamp, transaction_type, from_account_number, to_account_number, to_phone_number,
                amount, currency, status, description, external_transaction_id, 
                hmac_signature_sent, hmac_signature_received, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tx_id, ts, transaction_type, from_account_number, to_account_number, to_phone_number,
              amount, currency, status, description, external_transaction_id,
              hmac_signature_sent, hmac_signature_received, notes))
        conn.commit()
        return tx_id
    except Exception as e:
        # In a real app, use proper logging here
        print(f"Error logging transaction: {e}")
        return None
    finally:
        conn.close()