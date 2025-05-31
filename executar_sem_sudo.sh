#!/bin/bash
# Script para executar AURALIS sem precisar de sudo

echo "🎯 AURALIS - Execução sem sudo"
echo "=============================="
echo ""

# Verificar se já tem Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 encontrado: $(python3 --version)"
else
    echo "❌ Python3 não encontrado"
    echo "   Tente executar no Windows diretamente"
    exit 1
fi

# Tentar criar ambiente virtual local
echo ""
echo "📦 Criando ambiente virtual local..."
python3 -m venv --without-pip venv_local 2>/dev/null || {
    echo "⚠️  Não foi possível criar ambiente virtual"
    echo "   Vamos tentar executar diretamente"
}

# Tentar usar pip do usuário
echo ""
echo "📥 Tentando instalar dependências localmente..."

# Criar diretório local para pacotes
mkdir -p local_packages

# Tentar baixar get-pip.py
echo "Baixando pip..."
curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py 2>/dev/null || wget -q https://bootstrap.pypa.io/get-pip.py 2>/dev/null || {
    echo "⚠️  Não foi possível baixar pip"
}

# Instalar pip localmente
if [ -f get-pip.py ]; then
    python3 get-pip.py --user 2>/dev/null
    rm get-pip.py
fi

# Adicionar pip local ao PATH
export PATH="$HOME/.local/bin:$PATH"

# Verificar se pip está disponível
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    echo "✅ Pip disponível"
    
    # Instalar dependências no modo usuário
    echo "📦 Instalando dependências (modo usuário)..."
    python3 -m pip install --user -r requirements.txt
else
    echo "⚠️  Pip não disponível"
fi

# Criar diretórios necessários
echo ""
echo "📁 Criando diretórios..."
mkdir -p logs recordings auralis_memoria update_conhecimento update_historico

# Tentar executar
echo ""
echo "🚀 Tentando executar AURALIS..."
echo ""

# Verificar se temos display (necessário para PyQt)
if [ -z "$DISPLAY" ]; then
    echo "⚠️  AVISO: Variável DISPLAY não definida"
    echo "   Tentando definir DISPLAY=:0"
    export DISPLAY=:0
fi

# Executar
python3 main.py 2>&1 || {
    echo ""
    echo "❌ Erro ao executar"
    echo ""
    echo "🪟 ALTERNATIVA: Execute no Windows PowerShell:"
    echo "   1. Abra o PowerShell"
    echo "   2. Navegue até: cd '\\wsl$\Ubuntu\home\estival\auralis_new'"
    echo "   3. Execute: python main.py"
}