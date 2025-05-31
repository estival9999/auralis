#!/usr/bin/env python3
"""
Script para testar e configurar áudio no WSL
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pyaudio():
    """Testa PyAudio"""
    print("🎤 Testando PyAudio...")
    
    try:
        import pyaudio
        print("✅ PyAudio importado com sucesso")
        
        # Criar instância
        audio = pyaudio.PyAudio()
        print("✅ PyAudio inicializado")
        
        # Listar dispositivos
        print("\n🔍 Dispositivos de áudio encontrados:")
        device_count = audio.get_device_count()
        print(f"Total de dispositivos: {device_count}")
        
        input_devices = []
        for i in range(device_count):
            try:
                info = audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    input_devices.append(info)
                    print(f"  📥 {i}: {info['name']} (Canais: {info['maxInputChannels']})")
                else:
                    print(f"  📤 {i}: {info['name']} (Saída apenas)")
            except Exception as e:
                print(f"  ❌ {i}: Erro ao ler dispositivo - {e}")
        
        if input_devices:
            print(f"\n✅ {len(input_devices)} dispositivos de entrada encontrados!")
            
            # Testar gravação com primeiro dispositivo
            print("\n🧪 Testando gravação com primeiro dispositivo...")
            try:
                device_info = input_devices[0]
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    input_device_index=device_info['index'],
                    frames_per_buffer=1024
                )
                
                print("📹 Gravando por 2 segundos...")
                data = stream.read(1024 * 44100 // 1024 * 2)  # 2 segundos
                stream.stop_stream()
                stream.close()
                print("✅ Teste de gravação bem-sucedido!")
                
            except Exception as e:
                print(f"❌ Erro no teste de gravação: {e}")
        else:
            print("\n❌ Nenhum dispositivo de entrada encontrado")
        
        audio.terminate()
        return True
        
    except ImportError:
        print("❌ PyAudio não está instalado")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar PyAudio: {e}")
        return False

def test_system_audio():
    """Testa áudio do sistema"""
    print("\n🔧 Testando configuração do sistema...")
    
    import subprocess
    
    # Testar ALSA
    try:
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ALSA funcionando")
            print("📋 Dispositivos ALSA:")
            print(result.stdout)
        else:
            print("⚠️ ALSA pode ter problemas")
            print(result.stderr)
    except:
        print("❌ arecord não encontrado")
    
    # Testar PulseAudio
    try:
        result = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n✅ PulseAudio funcionando")
            print("📋 Fontes de áudio:")
            print(result.stdout)
        else:
            print("\n⚠️ PulseAudio pode ter problemas")
    except:
        print("\n❌ PulseAudio não encontrado")

def get_wsl_solutions():
    """Mostra soluções para WSL"""
    print("""
🔧 SOLUÇÕES PARA ÁUDIO NO WSL:

1. 📥 INSTALAR PULSEAUDIO NO WINDOWS:
   - Baixe: https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/
   - Ou use: choco install pulseaudio (se tiver Chocolatey)

2. 🔗 CONFIGURAR WSL PARA USAR PULSEAUDIO DO WINDOWS:
   export PULSE_SERVER=tcp:localhost:4713
   echo 'export PULSE_SERVER=tcp:localhost:4713' >> ~/.bashrc

3. 🪟 USAR DIRETAMENTE NO WINDOWS:
   - Copie o projeto para Windows: \\wsl$\\Ubuntu\\home\\estival\\auralis_new
   - Instale Python no Windows
   - Execute: python main.py

4. 🐳 USAR COM WSL2 + PULSEAUDIO:
   sudo apt update
   sudo apt install pulseaudio
   pulseaudio --start

5. 🎯 ALTERNATIVA SIMPLES:
   - Use o sistema para todas as funcionalidades EXCETO gravação
   - Para gravar: use qualquer app externo e importe o arquivo

📝 COMANDOS PARA TESTAR:
   # Ver dispositivos
   arecord -l
   
   # Testar gravação
   arecord -f cd -d 5 test.wav
   
   # Ver configuração PulseAudio
   pactl info
""")

def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              🎤 AURALIS - Teste de Áudio               ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Testar PyAudio
    pyaudio_ok = test_pyaudio()
    
    # Testar sistema
    test_system_audio()
    
    # Mostrar soluções
    get_wsl_solutions()
    
    if not pyaudio_ok:
        print("\n⚠️ RECOMENDAÇÃO: Execute o sistema no Windows para ter áudio completo")
    else:
        print("\n✅ Sistema de áudio configurado!")

if __name__ == "__main__":
    main()