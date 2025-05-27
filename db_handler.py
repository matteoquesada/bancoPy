import sqlite3

DB_PATH = "cuentas.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cuentas (
            account_number TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            saldo REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_account(account_number, nombre, saldo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO cuentas (account_number, nombre, saldo) VALUES (?, ?, ?)', (account_number, nombre, saldo))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
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
    c.execute('SELECT account_number, nombre, saldo FROM cuentas WHERE account_number = ?', (account_number,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"account_number": row[0], "nombre": row[1], "saldo": row[2]}
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
    c.execute('SELECT account_number, nombre, saldo FROM cuentas')
    rows = c.fetchall()
    conn.close()
    return [{"account_number": row[0], "nombre": row[1], "saldo": row[2]} for row in rows]