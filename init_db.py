import sqlite3
import os

def init_database():
    """Inicializa o banco de dados com tabelas e dados iniciais"""
    
    # Garante que o diretório existe
    os.makedirs('database', exist_ok=True)
    
    # Conecta ao banco de dados
    conn = sqlite3.connect('database/banco_digital.db')
    cursor = conn.cursor()
    
    print("🔄 Inicializando banco de dados...")
    
    # Cria tabelas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas (
            numero TEXT PRIMARY KEY,
            titular TEXT NOT NULL,
            email TEXT,
            cpf TEXT UNIQUE,
            saldo REAL DEFAULT 0.0,
            data_criacao TEXT,
            tipo_conta TEXT DEFAULT 'CORRENTE'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conta_origem TEXT,
            conta_destino TEXT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            data TEXT,
            FOREIGN KEY (conta_origem) REFERENCES contas (numero),
            FOREIGN KEY (conta_destino) REFERENCES contas (numero)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            cargo TEXT DEFAULT 'FUNCIONARIO'
        )
    ''')
    
    # Insere usuário admin padrão
    import hashlib
    senha_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (username, senha_hash, nome, cargo)
        VALUES (?, ?, ?, ?)
    ''', ('admin', senha_hash, 'Administrador do Sistema', 'GERENTE'))
    
    # Insere algumas contas de exemplo
    from datetime import datetime
    
    contas_exemplo = [
        ('1001', 'João Silva', 'joao@email.com', '123.456.789-00', 1500.00, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 'CORRENTE'),
        ('1002', 'Maria Santos', 'maria@email.com', '987.654.321-00', 2500.00, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 'POUPANÇA'),
        ('1003', 'Pedro Oliveira', 'pedro@email.com', '456.123.789-00', 500.00, datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 'CORRENTE'),
    ]
    
    for conta in contas_exemplo:
        cursor.execute('''
            INSERT OR IGNORE INTO contas (numero, titular, email, cpf, saldo, data_criacao, tipo_conta)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', conta)
    
    conn.commit()
    conn.close()
    
    print("✅ Banco de dados inicializado com sucesso!")
    print("📊 Contas de exemplo criadas:")
    print("   - 1001: João Silva (R$ 1.500,00)")
    print("   - 1002: Maria Santos (R$ 2.500,00)") 
    print("   - 1003: Pedro Oliveira (R$ 500,00)")
    print("\n🔐 Usuário padrão: admin / admin123")

if __name__ == "__main__":
    init_database()
