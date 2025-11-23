import sqlite3
import os
from datetime import datetime
import hashlib

def init_database():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect('database/banco_digital.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS contas (numero TEXT PRIMARY KEY, titular TEXT NOT NULL, email TEXT, cpf TEXT UNIQUE, saldo REAL DEFAULT 0.0, data_criacao TEXT, tipo_conta TEXT DEFAULT "CORRENTE")''')
    cur.execute('''CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, conta_origem TEXT, conta_destino TEXT, tipo TEXT NOT NULL, valor REAL NOT NULL, descricao TEXT, data TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL, nome TEXT NOT NULL, cargo TEXT DEFAULT "FUNCIONARIO")''')
    h = hashlib.sha256('admin123'.encode()).hexdigest()
    cur.execute('INSERT OR IGNORE INTO usuarios (username, senha_hash, nome, cargo) VALUES (?, ?, ?, ?)', ('admin', h, 'Administrador do Sistema', 'GERENTE'))
    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    examples = [
        ('1001', 'João Silva', 'joao@email.com', '123.456.789-00', 150000.00, now, 'CORRENTE'),
        ('1002', 'Maria Santos', 'maria@email.com', '987.654.321-00', 250000.00, now, 'POUPANÇA'),
        ('1003', 'Pedro Oliveira', 'pedro@email.com', '456.123.789-00', 50000.00, now, 'CORRENTE'),
    ]
    for c in examples:
        cur.execute('INSERT OR IGNORE INTO contas (numero, titular, email, cpf, saldo, data_criacao, tipo_conta) VALUES (?, ?, ?, ?, ?, ?, ?)', c)
    conn.commit()
    conn.close()
    print('Database initialized with example accounts (AOA).')

if __name__ == '__main__':
    init_database()
