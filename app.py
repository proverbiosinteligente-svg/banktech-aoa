import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import hashlib
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="BankTech - Sistema Bancário",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1E3A8A;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

class BancoDigital:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        os.makedirs('database', exist_ok=True)
        self.conn = sqlite3.connect('database/banco_digital.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Tabela de contas
        self.cursor.execute('''
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
        
        # Tabela de transações
        self.cursor.execute('''
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
        
        # Tabela de usuários (funcionários)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                nome TEXT NOT NULL,
                cargo TEXT DEFAULT 'FUNCIONARIO'
            )
        ''')
        
        # Inserir usuário admin padrão
        self.cursor.execute('''
            INSERT OR IGNORE INTO usuarios (username, senha_hash, nome, cargo)
            VALUES (?, ?, ?, ?)
        ''', ('admin', self.hash_password('admin123'), 'Administrador', 'GERENTE'))
        
        self.conn.commit()
    
    def hash_password(self, password):
        """Gera hash da senha"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verificar_login(self, username, password):
        """Verifica credenciais de login"""
        senha_hash = self.hash_password(password)
        self.cursor.execute(
            'SELECT * FROM usuarios WHERE username = ? AND senha_hash = ?',
            (username, senha_hash)
        )
        return self.cursor.fetchone()
    
    def criar_conta(self, numero, titular, email, cpf, saldo_inicial=0.0, tipo_conta='CORRENTE'):
        """Cria uma nova conta bancária"""
        try:
            data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            self.cursor.execute('''
                INSERT INTO contas (numero, titular, email, cpf, saldo, data_criacao, tipo_conta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (numero, titular, email, cpf, saldo_inicial, data_criacao, tipo_conta))
            
            if saldo_inicial > 0:
                self.registrar_transacao(
                    conta_origem=None,
                    conta_destino=numero,
                    tipo='DEPOSITO_INICIAL',
                    valor=saldo_inicial,
                    descricao=f"Depósito inicial - {tipo_conta}"
                )
            
            self.conn.commit()
            return True, "Conta criada com sucesso!"
        except sqlite3.IntegrityError as e:
            return False, "Erro: Número da conta ou CPF já existente!"
    
    def registrar_transacao(self, conta_origem, conta_destino, tipo, valor, descricao=""):
        """Registra uma transação no banco de dados"""
        data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        self.cursor.execute('''
            INSERT INTO transacoes (conta_origem, conta_destino, tipo, valor, descricao, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (conta_origem, conta_destino, tipo, valor, descricao, data))
        
        self.conn.commit()
    
    def depositar(self, conta, valor):
        """Realiza depósito em conta"""
        if valor <= 0:
            return False, "Valor deve ser positivo!"
        
        self.cursor.execute('SELECT saldo FROM contas WHERE numero = ?', (conta,))
        resultado = self.cursor.fetchone()
        
        if not resultado:
            return False, "Conta não encontrada!"
        
        novo_saldo = resultado[0] + valor
        
        self.cursor.execute(
            'UPDATE contas SET saldo = ? WHERE numero = ?',
            (novo_saldo, conta)
        )
        
        self.registrar_transacao(
            conta_origem=None,
            conta_destino=conta,
            tipo='DEPOSITO',
            valor=valor,
            descricao="Depósito em conta"
        )
        
        self.conn.commit()
        return True, f"Depósito de R$ {valor:.2f} realizado com sucesso!"
    
    def sacar(self, conta, valor):
        """Realiza saque de conta"""
        if valor <= 0:
            return False, "Valor deve ser positivo!"
        
        self.cursor.execute('SELECT saldo FROM contas WHERE numero = ?', (conta,))
        resultado = self.cursor.fetchone()
        
        if not resultado:
            return False, "Conta não encontrada!"
        
        saldo_atual = resultado[0]
        
        if saldo_atual < valor:
            return False, "Saldo insuficiente!"
        
        novo_saldo = saldo_atual - valor
        
        self.cursor.execute(
            'UPDATE contas SET saldo = ? WHERE numero = ?',
            (novo_saldo, conta)
        )
        
        self.registrar_transacao(
            conta_origem=conta,
            conta_destino=None,
            tipo='SAQUE',
            valor=valor,
            descricao="Saque em conta"
        )
        
        self.conn.commit()
        return True, f"Saque de R$ {valor:.2f} realizado com sucesso!"
    
    def transferir(self, conta_origem, conta_destino, valor):
        """Realiza transferência entre contas"""
        if valor <= 0:
            return False, "Valor deve ser positivo!"
        
        # Verifica se as contas existem
        self.cursor.execute('SELECT saldo FROM contas WHERE numero = ?', (conta_origem,))
        resultado_origem = self.cursor.fetchone()
        
        self.cursor.execute('SELECT saldo FROM contas WHERE numero = ?', (conta_destino,))
        resultado_destino = self.cursor.fetchone()
        
        if not resultado_origem:
            return False, "Conta de origem não encontrada!"
        if not resultado_destino:
            return False, "Conta de destino não encontrada!"
        
        saldo_origem = resultado_origem[0]
        
        if saldo_origem < valor:
            return False, "Saldo insuficiente para transferência!"
        
        # Atualiza saldos
        novo_saldo_origem = saldo_origem - valor
        novo_saldo_destino = resultado_destino[0] + valor
        
        self.cursor.execute(
            'UPDATE contas SET saldo = ? WHERE numero = ?',
            (novo_saldo_origem, conta_origem)
        )
        
        self.cursor.execute(
            'UPDATE contas SET saldo = ? WHERE numero = ?',
            (novo_saldo_destino, conta_destino)
        )
        
        # Registra transação
        self.registrar_transacao(
            conta_origem=conta_origem,
            conta_destino=conta_destino,
            tipo='TRANSFERENCIA',
            valor=valor,
            descricao=f"Transferência para {conta_destino}"
        )
        
        self.conn.commit()
        return True, f"Transferência de R$ {valor:.2f} realizada com sucesso!"
    
    def consultar_saldo(self, conta):
        """Consulta saldo da conta"""
        self.cursor.execute('SELECT saldo, titular FROM contas WHERE numero = ?', (conta,))
        resultado = self.cursor.fetchone()
        
        if resultado:
            return True, resultado[0], resultado[1]
        return False, 0, ""
    
    def obter_extrato(self, conta, limite=20):
        """Obtém extrato da conta"""
        self.cursor.execute('''
            SELECT data, tipo, valor, descricao, conta_origem, conta_destino
            FROM transacoes 
            WHERE conta_origem = ? OR conta_destino = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (conta, conta, limite))
        
        return self.cursor.fetchall()
    
    def obter_contas(self):
        """Obtém todas as contas cadastradas"""
        self.cursor.execute('''
            SELECT numero, titular, email, cpf, saldo, data_criacao, tipo_conta
            FROM contas 
            ORDER BY data_criacao DESC
        ''')
        return self.cursor.fetchall()
    
    def obter_estatisticas(self):
        """Obtém estatísticas do banco"""
        self.cursor.execute('SELECT COUNT(*), SUM(saldo) FROM contas')
        total_contas, saldo_total = self.cursor.fetchone()
        
        self.cursor.execute('SELECT COUNT(*) FROM transacoes')
        total_transacoes = self.cursor.fetchone()[0]
        
        return total_contas, saldo_total or 0, total_transacoes

def main():
    # Inicializa o sistema bancário
    banco = BancoDigital()
    
    # Verifica se o usuário está logado
    if 'logado' not in st.session_state:
        st.session_state.logado = False
        st.session_state.usuario = None
        st.session_state.cargo = None
    
    # Página de login se não estiver logado
    if not st.session_state.logado:
        render_login_page(banco)
        return
    
    # Menu principal após login
    render_main_page(banco)

def render_login_page(banco):
    """Renderiza a página de login"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="main-header">🏦 BankTech</h1>', unsafe_allow_html=True)
        st.markdown("### Sistema Bancário Digital")
        st.markdown("---")
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuário")
            password = st.text_input("🔒 Senha", type="password")
            
            if st.form_submit_button("🚀 Entrar no Sistema"):
                if username and password:
                    usuario = banco.verificar_login(username, password)
                    if usuario:
                        st.session_state.logado = True
                        st.session_state.usuario = usuario[1]  # username
                        st.session_state.cargo = usuario[4]    # cargo
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos!")
                else:
                    st.warning("Preencha todos os campos!")
        
        st.markdown("---")
        st.info("**Credenciais de teste:** Usuário: `admin` | Senha: `admin123`")

def render_main_page(banco):
    """Renderiza a página principal após login"""
    
    # Sidebar com menu
    with st.sidebar:
        st.markdown(f"### 👋 Olá, {st.session_state.usuario}!")
        st.markdown(f"**Cargo:** {st.session_state.cargo}")
        st.markdown("---")
        
        menu_options = [
            "📊 Dashboard",
            "📝 Criar Conta", 
            "💰 Operações",
            "📋 Consultar Contas",
            "🔄 Transações",
            "⚙️ Administração"
        ]
        
        selected_menu = st.radio("Navegação", menu_options)
        
        st.markdown("---")
        if st.button("🚪 Sair"):
            st.session_state.logado = False
            st.session_state.usuario = None
            st.session_state.cargo = None
            st.rerun()
    
    # Conteúdo principal baseado no menu selecionado
    if selected_menu == "📊 Dashboard":
        render_dashboard(banco)
    elif selected_menu == "📝 Criar Conta":
        render_criar_conta(banco)
    elif selected_menu == "💰 Operações":
        render_operacoes(banco)
    elif selected_menu == "📋 Consultar Contas":
        render_consultar_contas(banco)
    elif selected_menu == "🔄 Transações":
        render_transacoes(banco)
    elif selected_menu == "⚙️ Administração":
        render_administracao(banco)

def render_dashboard(banco):
    """Renderiza o dashboard"""
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    # Estatísticas
    total_contas, saldo_total, total_transacoes = banco.obter_estatisticas()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Contas", total_contas)
    with col2:
        st.metric("Saldo Total", f"R$ {saldo_total:,.2f}")
    with col3:
        st.metric("Total de Transações", total_transacoes)
    
    st.markdown("---")
    
    # Últimas contas criadas
    st.subheader("📈 Últimas Contas Criadas")
    contas = banco.obter_contas()[:5]  # Últimas 5 contas
    
    if contas:
        dados_contas = []
        for conta in contas:
            dados_contas.append({
                'Número': conta[0],
                'Titular': conta[1],
                'Saldo': f"R$ {conta[4]:,.2f}",
                'Tipo': conta[6],
                'Data Criação': conta[5]
            })
        
        df = pd.DataFrame(dados_contas)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma conta cadastrada ainda.")

def render_criar_conta(banco):
    """Renderiza o formulário de criação de conta"""
    st.markdown('<h1 class="main-header">📝 Criar Nova Conta</h1>', unsafe_allow_html=True)
    
    with st.form("criar_conta_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            numero_conta = st.text_input("Número da Conta*")
            titular = st.text_input("Nome do Titular*")
            cpf = st.text_input("CPF*", placeholder="000.000.000-00")
        
        with col2:
            email = st.text_input("E-mail")
            tipo_conta = st.selectbox("Tipo de Conta", ["CORRENTE", "POUPANÇA", "SALÁRIO"])
            saldo_inicial = st.number_input("Saldo Inicial (R$)", min_value=0.0, value=0.0)
        
        st.markdown("**Campos obrigatórios***")
        
        if st.form_submit_button("✅ Criar Conta"):
            if numero_conta and titular and cpf:
                sucesso, mensagem = banco.criar_conta(
                    numero_conta, titular, email, cpf, saldo_inicial, tipo_conta
                )
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
            else:
                st.warning("Preencha todos os campos obrigatórios!")

def render_operacoes(banco):
    """Renderiza as operações bancárias"""
    st.markdown('<h1 class="main-header">💰 Operações Bancárias</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["💳 Consultar Saldo", "📥 Depositar", "📤 Sacar", "🔄 Transferir"])
    
    with tab1:
        st.subheader("Consultar Saldo")
        conta_consulta = st.text_input("Número da Conta para Consulta")
        if st.button("Consultar Saldo"):
            if conta_consulta:
                sucesso, saldo, titular = banco.consultar_saldo(conta_consulta)
                if sucesso:
                    st.success(f"**Titular:** {titular}")
                    st.success(f"**Saldo:** R$ {saldo:,.2f}")
                else:
                    st.error("Conta não encontrada!")
            else:
                st.warning("Digite o número da conta!")
    
    with tab2:
        st.subheader("Realizar Depósito")
        col1, col2 = st.columns(2)
        with col1:
            conta_deposito = st.text_input("Conta para Depósito")
        with col2:
            valor_deposito = st.number_input("Valor do Depósito (R$)", min_value=0.01)
        
        if st.button("Confirmar Depósito"):
            if conta_deposito and valor_deposito:
                sucesso, mensagem = banco.depositar(conta_deposito, valor_deposito)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
            else:
                st.warning("Preencha todos os campos!")
    
    with tab3:
        st.subheader("Realizar Saque")
        col1, col2 = st.columns(2)
        with col1:
            conta_saque = st.text_input("Conta para Saque")
        with col2:
            valor_saque = st.number_input("Valor do Saque (R$)", min_value=0.01)
        
        if st.button("Confirmar Saque"):
            if conta_saque and valor_saque:
                sucesso, mensagem = banco.sacar(conta_saque, valor_saque)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
            else:
                st.warning("Preencha todos os campos!")
    
    with tab4:
        st.subheader("Realizar Transferência")
        col1, col2 = st.columns(2)
        with col1:
            conta_origem_transf = st.text_input("Conta de Origem")
            conta_destino_transf = st.text_input("Conta de Destino")
        with col2:
            valor_transf = st.number_input("Valor da Transferência (R$)", min_value=0.01)
        
        if st.button("Confirmar Transferência"):
            if conta_origem_transf and conta_destino_transf and valor_transf:
                sucesso, mensagem = banco.transferir(conta_origem_transf, conta_destino_transf, valor_transf)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
            else:
                st.warning("Preencha todos os campos!")

def render_consultar_contas(banco):
    """Renderiza a consulta de contas"""
    st.markdown('<h1 class="main-header">📋 Consultar Contas</h1>', unsafe_allow_html=True)
    
    contas = banco.obter_contas()
    
    if contas:
        dados_contas = []
        for conta in contas:
            dados_contas.append({
                'Número': conta[0],
                'Titular': conta[1],
                'E-mail': conta[2],
                'CPF': conta[3],
                'Saldo': conta[4],
                'Data Criação': conta[5],
                'Tipo': conta[6]
            })
        
        df = pd.DataFrame(dados_contas)
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            filtro_tipo = st.selectbox("Filtrar por tipo:", ["TODOS", "CORRENTE", "POUPANÇA", "SALÁRIO"])
        with col2:
            filtro_nome = st.text_input("Filtrar por nome:")
        
        # Aplicar filtros
        if filtro_tipo != "TODOS":
            df = df[df['Tipo'] == filtro_tipo]
        if filtro_nome:
            df = df[df['Titular'].str.contains(filtro_nome, case=False, na=False)]
        
        st.dataframe(df, use_container_width=True)
        
        # Estatísticas das contas filtradas
        st.subheader("📊 Estatísticas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Contas", len(df))
        with col2:
            st.metric("Saldo Total", f"R$ {df['Saldo'].sum():,.2f}")
        with col3:
            st.metric("Saldo Médio", f"R$ {df['Saldo'].mean():,.2f}")
    
    else:
        st.info("Nenhuma conta cadastrada ainda.")

def render_transacoes(banco):
    """Renderiza o histórico de transações"""
    st.markdown('<h1 class="main-header">🔄 Histórico de Transações</h1>', unsafe_allow_html=True)
    
    conta_extrato = st.text_input("Digite o número da conta para ver o extrato:")
    
    if conta_extrato:
        extrato = banco.obter_extrato(conta_extrato)
        
        if extrato:
            dados_extrato = []
            for transacao in extrato:
                tipo_transacao = transacao[1]
                valor = transacao[2]
                
                if tipo_transacao == 'SAQUE':
                    descricao = f"Saque - {transacao[3]}"
                    valor_formatado = f"-R$ {valor:,.2f}"
                elif tipo_transacao == 'DEPOSITO':
                    descricao = f"Depósito - {transacao[3]}"
                    valor_formatado = f"+R$ {valor:,.2f}"
                elif tipo_transacao == 'TRANSFERENCIA':
                    if transacao[4] == conta_extrato:  # É a conta de destino
                        descricao = f"Transferência recebida de {transacao[4]}"
                        valor_formatado = f"+R$ {valor:,.2f}"
                    else:  # É a conta de origem
                        descricao = f"Transferência enviada para {transacao[5]}"
                        valor_formatado = f"-R$ {valor:,.2f}"
                else:
                    descricao = transacao[3]
                    valor_formatado = f"+R$ {valor:,.2f}"
                
                dados_extrato.append({
                    'Data': transacao[0],
                    'Tipo': tipo_transacao,
                    'Descrição': descricao,
                    'Valor': valor_formatado
                })
            
            df_extrato = pd.DataFrame(dados_extrato)
            st.dataframe(df_extrato, use_container_width=True)
        else:
            st.info("Nenhuma transação encontrada para esta conta.")
    
    # Todas as transações (apenas para administradores)
    if st.session_state.cargo == 'GERENTE':
        st.markdown("---")
        st.subheader("📋 Todas as Transações (Visão Gerencial)")
        
        banco.cursor.execute('''
            SELECT t.data, t.tipo, t.valor, t.descricao, 
                   c1.titular as origem, c2.titular as destino
            FROM transacoes t
            LEFT JOIN contas c1 ON t.conta_origem = c1.numero
            LEFT JOIN contas c2 ON t.conta_destino = c2.numero
            ORDER BY t.id DESC
            LIMIT 100
        ''')
        
        todas_transacoes = banco.cursor.fetchall()
        
        if todas_transacoes:
            dados_todas = []
            for transacao in todas_transacoes:
                dados_todas.append({
                    'Data': transacao[0],
                    'Tipo': transacao[1],
                    'Valor': f"R$ {transacao[2]:,.2f}",
                    'Descrição': transacao[3],
                    'Origem': transacao[4] or 'SISTEMA',
                    'Destino': transacao[5] or 'SISTEMA'
                })
            
            df_todas = pd.DataFrame(dados_todas)
            st.dataframe(df_todas, use_container_width=True)

def render_administracao(banco):
    """Renderiza a área administrativa"""
    if st.session_state.cargo != 'GERENTE':
        st.warning("⚠️ Acesso restrito a gerentes!")
        return
    
    st.markdown('<h1 class="main-header">⚙️ Área Administrativa</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👥 Gerenciar Usuários", "💾 Backup do Sistema"])
    
    with tab1:
        st.subheader("Gerenciar Usuários")
        
        # Formulário para criar novo usuário
        with st.form("novo_usuario_form"):
            st.write("### Adicionar Novo Usuário")
            col1, col2 = st.columns(2)
            
            with col1:
                novo_username = st.text_input("Username*")
                novo_nome = st.text_input("Nome Completo*")
            with col2:
                nova_senha = st.text_input("Senha*", type="password")
                novo_cargo = st.selectbox("Cargo", ["FUNCIONARIO", "GERENTE"])
            
            if st.form_submit_button("➕ Adicionar Usuário"):
                if novo_username and novo_nome and nova_senha:
                    try:
                        senha_hash = banco.hash_password(nova_senha)
                        banco.cursor.execute('''
                            INSERT INTO usuarios (username, senha_hash, nome, cargo)
                            VALUES (?, ?, ?, ?)
                        ''', (novo_username, senha_hash, novo_nome, novo_cargo))
                        banco.conn.commit()
                        st.success("Usuário criado com sucesso!")
                    except sqlite3.IntegrityError:
                        st.error("Username já existe!")
                else:
                    st.warning("Preencha todos os campos!")
        
        # Lista de usuários existentes
        st.write("### Usuários do Sistema")
        banco.cursor.execute('SELECT username, nome, cargo FROM usuarios')
        usuarios = banco.cursor.fetchall()
        
        if usuarios:
            dados_usuarios = []
            for usuario in usuarios:
                dados_usuarios.append({
                    'Username': usuario[0],
                    'Nome': usuario[1],
                    'Cargo': usuario[2]
                })
            
            df_usuarios = pd.DataFrame(dados_usuarios)
            st.dataframe(df_usuarios, use_container_width=True)
    
    with tab2:
        st.subheader("Backup e Estatísticas do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Informações do Banco de Dados**")
            st.info(f"**Local:** database/banco_digital.db")
            
            if st.button("🔄 Atualizar Estatísticas"):
                total_contas, saldo_total, total_transacoes = banco.obter_estatisticas()
                st.metric("Total de Contas", total_contas)
                st.metric("Saldo Total", f"R$ {saldo_total:,.2f}")
                st.metric("Total de Transações", total_transacoes)
        
        with col2:
            st.write("**Ações do Sistema**")
            if st.button("🗃️ Exportar Dados"):
                # Exportar contas para CSV
                contas = banco.obter_contas()
                if contas:
                    df_export = pd.DataFrame(contas, columns=[
                        'Número', 'Titular', 'E-mail', 'CPF', 'Saldo', 'Data_Criação', 'Tipo'
                    ])
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV de Contas",
                        data=csv,
                        file_name="contas_bancarias.csv",
                        mime="text/csv"
                    )

if __name__ == "__main__":
    main()
