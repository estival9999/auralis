#!/bin/bash
# Script para executar o Sistema AURALIS

echo "🎯 AURALIS - Sistema Inteligente de Reuniões"
echo "==========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

# Verificar/criar ambiente virtual
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null

# Verificar/instalar dependências
echo "📋 Verificando dependências..."
pip install -q --upgrade pip

if [ ! -f ".deps_installed" ]; then
    echo "📥 Instalando dependências..."
    pip install -r requirements.txt
    touch .deps_installed
else
    echo "✅ Dependências já instaladas"
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p logs recordings auralis_memoria update_conhecimento update_historico

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "   Por favor, configure as credenciais em .env"
    echo "   Veja .env.example para referência"
    exit 1
fi

# Executar aplicação
echo ""
echo "🚀 Iniciando AURALIS..."
echo ""
python main.py

# Desativar ambiente virtual ao sair
deactivate 2>/dev/null || true