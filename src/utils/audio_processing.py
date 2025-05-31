"""
Utilitários para processamento de áudio do Sistema AURALIS
Funções auxiliares para manipulação de arquivos de áudio
"""
import wave
import os
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from loguru import logger

class AudioProcessor:
    """Utilitários para processamento de áudio"""
    
    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """
        Obtém informações sobre arquivo de áudio
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dict com informações do áudio
        """
        try:
            with wave.open(file_path, 'rb') as wf:
                return {
                    'channels': wf.getnchannels(),
                    'sample_width': wf.getsampwidth(),
                    'framerate': wf.getframerate(),
                    'n_frames': wf.getnframes(),
                    'duration': wf.getnframes() / wf.getframerate(),
                    'file_size': os.path.getsize(file_path)
                }
        except Exception as e:
            logger.error(f"Erro ao obter info do áudio: {e}")
            return {}
    
    @staticmethod
    def split_audio_file(file_path: str, chunk_duration: int = 600) -> List[str]:
        """
        Divide arquivo de áudio em chunks menores
        
        Args:
            file_path: Caminho do arquivo original
            chunk_duration: Duração de cada chunk em segundos (padrão: 10 min)
            
        Returns:
            Lista com caminhos dos chunks criados
        """
        chunks = []
        
        try:
            # Obter informações do áudio
            info = AudioProcessor.get_audio_info(file_path)
            if not info:
                return []
            
            total_duration = info['duration']
            framerate = info['framerate']
            
            # Calcular número de chunks necessários
            n_chunks = int(np.ceil(total_duration / chunk_duration))
            
            if n_chunks <= 1:
                # Arquivo já é pequeno o suficiente
                return [file_path]
            
            # Criar diretório para chunks
            base_path = Path(file_path)
            chunks_dir = base_path.parent / f"{base_path.stem}_chunks"
            chunks_dir.mkdir(exist_ok=True)
            
            # Abrir arquivo original
            with wave.open(file_path, 'rb') as wf:
                # Parâmetros do áudio
                params = wf.getparams()
                
                # Frames por chunk
                frames_per_chunk = int(chunk_duration * framerate)
                
                # Criar cada chunk
                for i in range(n_chunks):
                    chunk_path = chunks_dir / f"{base_path.stem}_chunk_{i+1:03d}.wav"
                    
                    # Ler frames do chunk
                    frames = wf.readframes(frames_per_chunk)
                    
                    # Salvar chunk
                    with wave.open(str(chunk_path), 'wb') as chunk_wf:
                        chunk_wf.setparams(params)
                        chunk_wf.writeframes(frames)
                    
                    chunks.append(str(chunk_path))
                    logger.info(f"Chunk criado: {chunk_path.name}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Erro ao dividir áudio: {e}")
            return []
    
    @staticmethod
    def merge_audio_files(file_paths: List[str], output_path: str) -> bool:
        """
        Mescla múltiplos arquivos de áudio em um único arquivo
        
        Args:
            file_paths: Lista de caminhos dos arquivos
            output_path: Caminho do arquivo de saída
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if not file_paths:
                return False
            
            # Usar primeiro arquivo como referência
            with wave.open(file_paths[0], 'rb') as wf:
                params = wf.getparams()
            
            # Criar arquivo de saída
            with wave.open(output_path, 'wb') as out_wf:
                out_wf.setparams(params)
                
                # Adicionar cada arquivo
                for file_path in file_paths:
                    with wave.open(file_path, 'rb') as in_wf:
                        # Verificar compatibilidade
                        if in_wf.getparams()[:3] != params[:3]:
                            logger.warning(f"Arquivo incompatível: {file_path}")
                            continue
                        
                        # Copiar frames
                        frames = in_wf.readframes(in_wf.getnframes())
                        out_wf.writeframes(frames)
            
            logger.info(f"Áudios mesclados em: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao mesclar áudios: {e}")
            return False
    
    @staticmethod
    def calculate_audio_checksum(file_path: str) -> Optional[str]:
        """
        Calcula checksum MD5 do arquivo de áudio
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            String com checksum MD5 ou None em caso de erro
        """
        import hashlib
        
        try:
            md5_hash = hashlib.md5()
            
            with open(file_path, "rb") as f:
                # Ler arquivo em chunks para economizar memória
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            
            return md5_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Erro ao calcular checksum: {e}")
            return None
    
    @staticmethod
    def normalize_audio_volume(file_path: str, target_db: float = -20.0) -> bool:
        """
        Normaliza volume do áudio (requer pydub)
        
        Args:
            file_path: Caminho do arquivo
            target_db: Volume alvo em dB
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            from pydub import AudioSegment
            
            # Carregar áudio
            audio = AudioSegment.from_wav(file_path)
            
            # Calcular ajuste necessário
            change_in_db = target_db - audio.dBFS
            
            # Aplicar normalização
            normalized = audio.apply_gain(change_in_db)
            
            # Salvar (sobrescrever)
            normalized.export(file_path, format="wav")
            
            logger.info(f"Áudio normalizado: {file_path}")
            return True
            
        except ImportError:
            logger.warning("pydub não instalado - normalização não disponível")
            return False
        except Exception as e:
            logger.error(f"Erro ao normalizar áudio: {e}")
            return False