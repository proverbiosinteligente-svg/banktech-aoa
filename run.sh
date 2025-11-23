#!/usr/bin/env python3
"""
Script de execução automática do Sistema Bancário
"""

import os
import sys
import subprocess
import platform

def check_python():
    """Verifica se Python está instalado"""
    try:
        version = sys.version_info
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
        return True
    except:
        print("❌ Python não encontrado!")
        print("📥 Baixe em: https://www.python.org/downloads/")
        return False

def install_requirements():
    """Instala as dependências necessárias"""
    print("\n📦 Instalando dependências...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências!")
        return False

def init_database():
    """Inicializa o banco de dados"""
    print("\n🗃️ Inicializando banco de dados...")
    try:
        from database.init_database import init_database
        init_database()
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

def run_system():
    """Executa o sistema bancário"""
    print("\n🚀 Iniciando Sistema Bancário...")
    print("📢 O sistema abrirá automaticamente no seu navegador")
    print("⏳ Aguarde alguns segundos...")
    print("\n🔐 Credenciais de acesso:")
    print("   👤 Usuário: admin")
    print("   🔒 Senha: admin123")
    print("\n⏸️  Para parar o sistema: Ctrl+C no terminal")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Sistema encerrado!")
    except Exception as e:
        print(f"❌ Erro ao executar o sistema: {e}")

def main():
    """Função principal"""
    print("=" * 60)
    print("🏦 SISTEMA BANCÁRIO DIGITAL - BankTech")
    print("=" * 60)
    
    # Verificar Python
    if not check_python():
        return
    
    # Instalar dependências
    if not install_requirements():
        return
    
    # Inicializar banco de dados
    if not init_database():
        return
    
    # Executar sistema
    run_system()

if __name__ == "__main__":
    main()
