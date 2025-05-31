#!/bin/bash
# Script para configurar áudio WSL2 com Windows

echo "🎤 Configurando áudio WSL2 para usar microfone do Windows"
echo "========================================================="

# Verificar se é WSL2
if grep -q WSL2 /proc/version; then
    echo "✅ WSL2 detectado"
else
    echo "⚠️  Este script é para WSL2. Verifique sua versão."
fi

echo ""
echo "📦 Instalando dependências de áudio..."

# Atualizar sistema
sudo apt update

# Instalar PulseAudio e dependências
sudo apt install -y pulseaudio pulseaudio-utils alsa-utils

# Instalar suporte adicional
sudo apt install -y pavucontrol paprefs

echo ""
echo "🔧 Configurando PulseAudio..."

# Criar configuração do PulseAudio
mkdir -p ~/.config/pulse

# Configurar daemon.conf
cat > ~/.config/pulse/daemon.conf << 'EOF'
# Configuração para WSL2
default-sample-format = s16le
default-sample-rate = 44100
default-sample-channels = 2
default-fragments = 4
default-fragment-size-msec = 25

# Permitir conexões de rede (necessário para Windows)
load-module module-native-protocol-tcp auth-anonymous=1 port=4713
EOF

# Configurar default.pa
cat > ~/.config/pulse/default.pa << 'EOF'
#!/usr/bin/pulseaudio -nF

# Carregar módulos básicos
load-module module-device-restore
load-module module-stream-restore
load-module module-card-restore

# Módulo para conexão TCP (Windows)
load-module module-native-protocol-tcp auth-anonymous=1 port=4713

# Detecção automática de hardware
load-module module-udev-detect

# Módulo de loopback para Windows audio
load-module module-loopback source=auto_null.monitor sink=auto_null

# Configurações de sessão
load-module module-default-device-restore
load-module module-rescue-streams
load-module module-always-sink
load-module module-intended-roles
load-module module-suspend-on-idle
EOF

echo ""
echo "🔗 Configurando variáveis de ambiente..."

# Adicionar configurações ao bashrc
if ! grep -q "PULSE_SERVER" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Configuração de áudio WSL2" >> ~/.bashrc
    echo "export PULSE_SERVER=tcp:localhost:4713" >> ~/.bashrc
    echo "export PULSE_RUNTIME_PATH=/tmp" >> ~/.bashrc
fi

# Configurar para sessão atual
export PULSE_SERVER=tcp:localhost:4713
export PULSE_RUNTIME_PATH=/tmp

echo ""
echo "🪟 PRÓXIMOS PASSOS NO WINDOWS:"
echo ""
echo "1. Instalar PulseAudio no Windows:"
echo "   - Baixe: https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/"
echo "   - Ou via Chocolatey: choco install pulseaudio"
echo ""
echo "2. Configurar PulseAudio no Windows:"
echo "   - Edite: %APPDATA%\\pulse\\default.pa"
echo "   - Adicione: load-module module-native-protocol-tcp auth-anonymous=1"
echo ""
echo "3. Reiniciar PulseAudio no Windows"
echo ""
echo "🔄 COMANDOS PARA TESTAR:"
echo ""
echo "# No WSL2:"
echo "pulseaudio --start"
echo "pactl info"
echo "pactl list sources"
echo ""
echo "# Testar gravação:"
echo "arecord -f cd -d 5 test.wav"
echo ""

echo "✅ Configuração WSL2 concluída!"
echo ""
echo "⚠️  IMPORTANTE: Você precisa configurar o PulseAudio no Windows também!"
echo "   Veja as instruções acima."