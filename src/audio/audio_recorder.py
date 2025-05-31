"""
Módulo de gravação de áudio do Sistema AURALIS
Gerencia captura e salvamento de áudio
"""
import wave
import pyaudio
import threading
import os
from datetime import datetime
from pathlib import Path
from loguru import logger
import numpy as np
import sys
sys.path.append('../..')
from shared.config import AUDIO_FORMAT, AUDIO_SAMPLE_RATE, AUDIO_CHUNK_SIZE

class AudioRecorder:
    """Gerencia gravação de áudio"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.is_paused = False
        self.recording_thread = None
        self.current_filename = None
        self.audio_dir = Path("recordings")
        self.audio_dir.mkdir(exist_ok=True)
        
        # Configurações de áudio
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = AUDIO_SAMPLE_RATE
        self.chunk = AUDIO_CHUNK_SIZE
        
        # Callbacks
        self.volume_callback = None
        
    def start_recording(self, filename_prefix="recording"):
        """Inicia gravação de áudio"""
        if self.is_recording:
            logger.warning("Gravação já em andamento")
            return False
        
        try:
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_filename = self.audio_dir / f"{filename_prefix}_{timestamp}.wav"
            
            # Inicializar stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.frames = []
            self.is_recording = True
            self.is_paused = False
            
            # Iniciar thread de gravação
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()
            
            logger.info(f"Gravação iniciada: {self.current_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar gravação: {e}")
            self.cleanup()
            return False
    
    def _record_audio(self):
        """Thread de gravação contínua"""
        while self.is_recording:
            try:
                if not self.is_paused and self.stream:
                    # Ler chunk de áudio
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                    
                    # Calcular volume para callback
                    if self.volume_callback:
                        volume = self._calculate_volume(data)
                        self.volume_callback(volume)
                        
            except Exception as e:
                logger.error(f"Erro durante gravação: {e}")
                break
    
    def pause_recording(self):
        """Pausa a gravação"""
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            logger.info("Gravação pausada")
            return True
        return False
    
    def resume_recording(self):
        """Retoma a gravação"""
        if self.is_recording and self.is_paused:
            self.is_paused = False
            logger.info("Gravação retomada")
            return True
        return False
    
    def stop_recording(self):
        """Para a gravação e salva o arquivo"""
        if not self.is_recording:
            return None
        
        try:
            # Parar gravação
            self.is_recording = False
            
            # Aguardar thread terminar
            if self.recording_thread:
                self.recording_thread.join(timeout=2.0)
            
            # Fechar stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Salvar arquivo
            if self.frames and self.current_filename:
                self._save_audio_file()
                logger.info(f"Gravação salva: {self.current_filename}")
                return str(self.current_filename)
            else:
                logger.warning("Nenhum dado de áudio para salvar")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao parar gravação: {e}")
            return None
        finally:
            self.cleanup()
    
    def cancel_recording(self):
        """Cancela gravação sem salvar"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Aguardar thread
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        
        # Limpar recursos
        self.cleanup()
        self.frames = []
        self.current_filename = None
        
        logger.info("Gravação cancelada")
    
    def _save_audio_file(self):
        """Salva frames de áudio em arquivo WAV"""
        try:
            with wave.open(str(self.current_filename), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
                
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo de áudio: {e}")
            raise
    
    def _calculate_volume(self, data):
        """Calcula volume do chunk de áudio (0-100)"""
        try:
            # Converter bytes para array numpy
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Verificar se há dados válidos
            if len(audio_data) == 0:
                return 0
            
            # Calcular RMS (Root Mean Square) com proteção contra NaN
            mean_square = np.mean(audio_data.astype(np.float64)**2)
            if np.isnan(mean_square) or mean_square <= 0:
                return 0
                
            rms = np.sqrt(mean_square)
            
            # Normalizar para 0-100
            volume = min(100, int(rms / 32768 * 100))
            return volume
            
        except Exception as e:
            logger.error(f"Erro ao calcular volume: {e}")
            return 0
    
    def get_recording_duration(self):
        """Retorna duração atual da gravação em segundos"""
        if not self.frames:
            return 0
        
        bytes_per_sample = self.audio.get_sample_size(self.format)
        total_bytes = len(self.frames) * self.chunk * bytes_per_sample
        duration = total_bytes / (self.rate * self.channels * bytes_per_sample)
        return int(duration)
    
    def set_volume_callback(self, callback):
        """Define callback para atualização de volume"""
        self.volume_callback = callback
    
    def cleanup(self):
        """Limpa recursos"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
    
    def get_available_devices(self):
        """Lista dispositivos de áudio disponíveis"""
        devices = []
        try:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxInputChannels']
                    })
            return devices
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos: {e}")
            return []
    
    def __del__(self):
        """Destrutor - garante limpeza de recursos"""
        self.cleanup()
        if hasattr(self, 'audio'):
            self.audio.terminate()