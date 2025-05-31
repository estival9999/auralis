#!/usr/bin/env python3
"""
Teste de transcrição de áudio
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.audio.transcriber import audio_transcriber
from loguru import logger

async def test_transcription():
    """Testa a transcrição de um arquivo de áudio"""
    
    # Verificar se há arquivos de gravação
    recordings_dir = Path("recordings")
    if not recordings_dir.exists():
        logger.error("Diretório recordings não encontrado")
        return
    
    # Listar arquivos WAV
    wav_files = list(recordings_dir.glob("*.wav"))
    if not wav_files:
        logger.error("Nenhum arquivo WAV encontrado em recordings/")
        return
    
    # Usar o arquivo mais recente
    latest_file = max(wav_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Arquivo selecionado: {latest_file}")
    
    # Transcrever
    logger.info("Iniciando transcrição...")
    result = await audio_transcriber.transcribe_audio(str(latest_file))
    
    if result['success']:
        logger.success("Transcrição concluída!")
        logger.info(f"Texto: {result['text'][:200]}..." if len(result['text']) > 200 else f"Texto: {result['text']}")
        logger.info(f"Duração: {result['duration']} segundos")
        logger.info(f"Idioma detectado: {result['language']}")
    else:
        logger.error(f"Erro na transcrição: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_transcription())