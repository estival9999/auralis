#!/bin/bash
# Script simplificado para instalar e executar AURALIS

echo "🎯 AURALIS - Instalação e Execução"
echo "=================================="
echo ""

# Função para detectar distribuição
detect_distro() {
    if [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "redhat"
    elif [ -f /etc/arch-release ]; then
        echo "arch"
    else
        echo "unknown"
    fi
}

# Detectar distribuição
DISTRO=$(detect_distro)
echo "📦 Distribuição detectada: $DISTRO"
echo ""

# Instalar dependências do sistema
echo "📥 Instalando dependências do sistema..."
echo "   (pode ser necessário inserir sua senha)"
echo ""

case $DISTRO in
    debian)
        sudo apt update
        sudo apt install -y python3-pip python3-venv python3-dev
        sudo apt install -y libxcb-xinerama0 libxcb-cursor0
        sudo apt install -y portaudio19-dev
        ;;
    redhat)
        sudo dnf install -y python3-pip python3-devel
        sudo dnf install -y portaudio-devel
        ;;
    arch)
        sudo pacman -S --noconfirm python-pip python-pyqt6
        sudo pacman -S --noconfirm portaudio
        ;;
    *)
        echo "⚠️  Distribuição não reconhecida!"
        echo "   Por favor, instale manualmente:"
        echo "   - Python 3.8+"
        echo "   - pip"
        echo "   - PyQt6"
        echo "   - PortAudio"
        exit 1
        ;;
esac

echo ""
echo "✅ Dependências do sistema instaladas!"
echo ""

# Criar e ativar ambiente virtual
echo "🔧 Configurando ambiente Python..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependências Python
echo "📦 Instalando pacotes Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Instalação concluída!"
echo ""

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  ATENÇÃO: Arquivo .env não encontrado!"
    echo "   O sistema precisa das credenciais configuradas."
    echo "   Veja o arquivo .env no projeto para referência."
    echo ""
    read -p "Deseja continuar mesmo assim? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

# Criar diretórios necessários
mkdir -p logs recordings auralis_memoria update_conhecimento update_historico

echo ""
echo "🚀 Iniciando AURALIS..."
echo ""
sleep 2

# Executar
python main.py