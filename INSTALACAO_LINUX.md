# 🐧 Guia de Instalação AURALIS - Linux

## Passo 1: Verificar Python
```bash
# Verificar se Python está instalado
python3 --version
```
Você precisa do Python 3.8 ou superior.

## Passo 2: Instalar dependências do sistema

### Ubuntu/Debian:
```bash
# Atualizar pacotes
sudo apt update

# Instalar Python e ferramentas necessárias
sudo apt install python3-pip python3-venv python3-dev

# Instalar dependências para PyQt6
sudo apt install libxcb-xinerama0 libxcb-cursor0

# Instalar dependências para áudio
sudo apt install portaudio19-dev python3-pyaudio
```

### Fedora/RedHat:
```bash
sudo dnf install python3-pip python3-devel
sudo dnf install portaudio-devel
```

### Arch/Manjaro:
```bash
sudo pacman -S python-pip python-pyqt6
sudo pacman -S portaudio
```

## Passo 3: Criar ambiente virtual (recomendado)
```bash
# Entrar na pasta do projeto
cd /home/estival/auralis_new

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate
```

## Passo 4: Instalar dependências Python
```bash
# Com o ambiente virtual ativado
pip install --upgrade pip
pip install -r requirements.txt
```

## Passo 5: Executar o sistema

### Opção 1: Usar o script run.sh
```bash
# Dar permissão de execução
chmod +x run.sh

# Executar
./run.sh
```

### Opção 2: Executar diretamente
```bash
# Com ambiente virtual ativado
python main.py
```

### Opção 3: Sem ambiente virtual
```bash
python3 main.py
```

## 🔧 Solução de Problemas

### Erro: "No module named 'PyQt6'"
```bash
pip install PyQt6
```

### Erro: "No module named '_portaudio'"
```bash
# Ubuntu/Debian
sudo apt install python3-pyaudio

# Ou via pip
pip install --upgrade pyaudio
```

### Erro: "qt.qpa.plugin: Could not load the Qt platform plugin"
```bash
# Instalar dependências gráficas
sudo apt install libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0
```

### Erro de permissão no microfone
```bash
# Adicionar usuário ao grupo audio
sudo usermod -a -G audio $USER
# Fazer logout e login novamente
```

## 📝 Comandos Úteis

```bash
# Ver logs em tempo real
tail -f logs/auralis.log

# Verificar se o microfone está funcionando
arecord -l  # Lista dispositivos de gravação

# Testar áudio
speaker-test -t wav -c 2  # Testa saída de som
```

## 🚀 Execução Rápida (todos os comandos)

```bash
# Para Ubuntu/Debian
cd /home/estival/auralis_new
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev portaudio19-dev
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## ⚠️ Importante
- O sistema precisa de interface gráfica (não funciona em servidor sem GUI)
- Precisa de acesso ao microfone para gravação
- As credenciais devem estar configuradas no arquivo .env