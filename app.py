import streamlit as st
from datetime import datetime
import pandas as pd
import sqlite3
import hashlib

CURRENCY = 'AOA'

def format_money(v):
    try:
        return f"{CURRENCY} {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return f"{CURRENCY} {v}"

def get_conn():
    import os
    os.makedirs('database', exist_ok=True)
    return sqlite3.connect('database/banco_digital.db', check_same_thread=False)

def ensure_admin(conn):
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL, nome TEXT NOT NULL, cargo TEXT DEFAULT "FUNCIONARIO")''')
    import hashlib
    h = hashlib.sha256('admin123'.encode()).hexdigest()
    cur.execute('INSERT OR IGNORE INTO usuarios (username, senha_hash, nome, cargo) VALUES (?, ?, ?, ?)', ('admin', h, 'Administrador', 'GERENTE'))
    conn.commit()

def main():
    conn = get_conn()
    ensure_admin(conn)
    st.title('BankTech - AOA')
    st.write('App simplificado. Rode `python init_db.py` para popular conta de exemplo.')
    
if __name__ == '__main__':
    main()
