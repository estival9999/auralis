"""
Sistema de processamento de áudio para reuniões AURALIS
Grava, fragmenta e transcreve áudio usando OpenAI Whisper
"""

import os
import wave
import pyaudio
import threading
import time
from pathlib import Path
from typing import List, Tuple, Optional, Callable
import math
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AudioProcessor:
    """Gerencia gravação, fragmentação e transcrição de áudio"""
    
    def __init__(self, output_dir: str = "audio_temp"):
        # Configurar OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no .env")
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Configurações de áudio
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # Taxa otimizada para transcrição
        
        # Controle de gravação
        self.recording = False
        self.frames = []
        self.p = None
        self.stream = None
        
        # Diretório de saída
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Limite de tamanho (25MB em bytes)
        self.max_size_bytes = 25 * 1024 * 1024
        
        # Armazenar último arquivo de transcrição para limpeza
        self.last_transcription_file = None
        
    def start_recording(self, callback: Optional[Callable[[float], None]] = None):
        """
        Inicia a gravação de áudio
        
        Args:
            callback: Função opcional chamada com o nível de áudio (0-1)
        """
        if self.recording:
            return
            
        self.recording = True
        self.frames = []
        
        # Inicializar PyAudio com tratamento de erro
        try:
            self.p = pyaudio.PyAudio()
            
            # Verificar se há dispositivos de entrada disponíveis
            input_device_count = self.p.get_device_count()
            has_input = False
            for i in range(input_device_count):
                info = self.p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    has_input = True
                    break
            
            if not has_input:
                raise Exception("Nenhum dispositivo de entrada de áudio encontrado")
            
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                stream_callback=None
            )
        except Exception as e:
            if self.p:
                self.p.terminate()
            raise Exception(f"Erro ao inicializar áudio: {str(e)}")
        
        # Thread de gravação
        def record():
            while self.recording:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                    
                    # Calcular nível de áudio para callback
                    if callback:
                        audio_data = list(data)
                        # Converter bytes para valores numéricos
                        values = []
                        for i in range(0, len(audio_data), 2):
                            if i + 1 < len(audio_data):
                                value = audio_data[i] | (audio_data[i+1] << 8)
                                if value > 32767:
                                    value -= 65536
                                values.append(value)
                        
                        # Calcular RMS (Root Mean Square)
                        if values:
                            rms = math.sqrt(sum(x**2 for x in values) / len(values))
                            # Normalizar para 0-1
                            level = min(1.0, rms / 32768.0 * 10)
                            callback(level)
                except Exception as e:
                    print(f"Erro na gravação: {e}")
        
        threading.Thread(target=record, daemon=True).start()
        
    def stop_recording(self) -> str:
        """
        Para a gravação e retorna o caminho do arquivo base
        
        Returns:
            Caminho base dos arquivos salvos (sem extensão)
        """
        if not self.recording:
            return ""
            
        self.recording = False
        time.sleep(0.1)  # Aguardar thread terminar
        
        # Fechar stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
            
        # Salvar arquivos fragmentados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = self.output_dir / f"reuniao_{timestamp}"
        
        self._save_fragmented_audio(base_path)
        
        return str(base_path)
        
    def _save_fragmented_audio(self, base_path: Path):
        """
        Salva o áudio em fragmentos de no máximo 25MB
        
        Args:
            base_path: Caminho base para os arquivos (sem extensão)
        """
        if not self.frames:
            return
            
        # Calcular tamanho total
        total_size = len(b''.join(self.frames))
        bytes_per_frame = len(self.frames[0]) if self.frames else 0
        
        if bytes_per_frame == 0:
            return
            
        # Calcular quantos frames cabem em 25MB (com margem de segurança)
        # Considerando header WAV (~44 bytes)
        max_frames_per_file = (self.max_size_bytes - 1024) // bytes_per_frame
        
        # Dividir e salvar
        file_count = 0
        for i in range(0, len(self.frames), max_frames_per_file):
            chunk_frames = self.frames[i:i + max_frames_per_file]
            
            # Criar arquivo WAV
            filename = f"{base_path}_part{file_count:03d}.wav"
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(chunk_frames))
            wf.close()
            
            print(f"✅ Salvo: {filename} ({os.path.getsize(filename) / 1024 / 1024:.1f}MB)")
            file_count += 1
            
    def transcribe_audio_files(self, base_path: str) -> str:
        """
        Transcreve todos os arquivos de áudio fragmentados
        
        Args:
            base_path: Caminho base dos arquivos
            
        Returns:
            Texto completo transcrito
        """
        base_path = Path(base_path)
        audio_files = sorted(base_path.parent.glob(f"{base_path.name}_part*.wav"))
        
        if not audio_files:
            raise ValueError(f"Nenhum arquivo de áudio encontrado com base: {base_path}")
            
        print(f"🎤 Transcrevendo {len(audio_files)} arquivo(s) de áudio...")
        
        transcriptions = []
        
        for i, audio_file in enumerate(audio_files):
            print(f"   Processando {audio_file.name}...")
            
            try:
                with open(audio_file, "rb") as f:
                    # Usar Whisper API
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language="pt",  # Português
                        response_format="text"
                    )
                    
                    transcriptions.append(response)
                    print(f"   ✅ Parte {i+1}/{len(audio_files)} transcrita")
                    
            except Exception as e:
                print(f"   ❌ Erro ao transcrever {audio_file.name}: {e}")
                transcriptions.append(f"[Erro na transcrição da parte {i+1}]")
        
        # Juntar todas as transcrições
        full_text = "\n".join(transcriptions)
        
        # Salvar arquivo de texto único
        text_file = base_path.parent / f"{base_path.name}_transcricao.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print(f"✅ Transcrição completa salva em: {text_file}")
        
        # Armazenar o caminho do arquivo para limpeza posterior
        self.last_transcription_file = text_file
        
        # Limpar arquivos de áudio temporários após transcrição
        for audio_file in audio_files:
            try:
                audio_file.unlink()
                print(f"   🗑️  Arquivo removido: {audio_file.name}")
            except Exception as e:
                print(f"   ⚠️  Não foi possível remover {audio_file.name}: {e}")
        
        return full_text
        
    def process_audio_to_text(self, callback: Optional[Callable[[float], None]] = None) -> Tuple[str, str]:
        """
        Processo completo: grava, para, fragmenta, transcreve
        
        Args:
            callback: Função de callback para nível de áudio
            
        Returns:
            Tupla (caminho_base, texto_transcrito)
        """
        # Este método seria usado para um processo mais automatizado
        # Por enquanto, vamos usar start/stop separadamente
        pass


class AudioRecorder:
    """Interface simplificada para gravação de áudio no frontend"""
    
    def __init__(self):
        self.processor = AudioProcessor()
        self.is_recording = False
        self.audio_level = 0.0
        self.base_path = ""
        self.transcription_file_path = None  # Armazenar caminho do arquivo de transcrição
        
    def toggle_recording(self) -> bool:
        """Alterna entre gravar/parar"""
        if self.is_recording:
            self.base_path = self.processor.stop_recording()
            self.is_recording = False
        else:
            self.processor.start_recording(self._update_level)
            self.is_recording = True
            
        return self.is_recording
        
    def _update_level(self, level: float):
        """Atualiza nível de áudio"""
        self.audio_level = level
        
    def get_transcription(self) -> Optional[str]:
        """Obtém transcrição do último áudio gravado"""
        if not self.base_path:
            return None
            
        try:
            transcription = self.processor.transcribe_audio_files(self.base_path)
            # Armazenar caminho do arquivo de transcrição se existir
            if hasattr(self.processor, 'last_transcription_file'):
                self.transcription_file_path = self.processor.last_transcription_file
            return transcription
        except Exception as e:
            print(f"Erro na transcrição: {e}")
            return None
            
    def get_audio_level(self) -> float:
        """Retorna nível atual do áudio (0-1)"""
        return self.audio_level
    
    def cleanup_transcription_file(self):
        """Remove o arquivo de transcrição após processamento"""
        if self.transcription_file_path and self.transcription_file_path.exists():
            try:
                self.transcription_file_path.unlink()
                print(f"🗑️  Arquivo de transcrição removido: {self.transcription_file_path.name}")
                self.transcription_file_path = None
            except Exception as e:
                print(f"⚠️  Não foi possível remover arquivo de transcrição: {e}")


# Funções auxiliares para teste
def test_audio_recording():
    """Testa gravação de áudio"""
    print("🎤 Teste de gravação de áudio")
    recorder = AudioRecorder()
    
    print("Pressione ENTER para iniciar gravação...")
    input()
    
    recorder.toggle_recording()
    print("🔴 Gravando... Pressione ENTER para parar")
    
    # Mostrar níveis de áudio
    import time
    def show_levels():
        while recorder.is_recording:
            level = recorder.get_audio_level()
            bars = "█" * int(level * 20)
            print(f"\r[{bars:<20}] {level:.2f}", end="", flush=True)
            time.sleep(0.1)
    
    threading.Thread(target=show_levels, daemon=True).start()
    
    input()
    recorder.toggle_recording()
    
    print("\n⏹️  Gravação finalizada!")
    print("🔄 Transcrevendo áudio...")
    
    text = recorder.get_transcription()
    if text:
        print(f"\n📝 Transcrição:\n{text}")
    else:
        print("❌ Erro na transcrição")


if __name__ == "__main__":
    test_audio_recording()