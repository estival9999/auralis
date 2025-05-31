"""
Módulo de transcrição de áudio do Sistema AURALIS
Utiliza OpenAI Whisper para transcrever reuniões
"""
import os
from openai import OpenAI
from pathlib import Path
from typing import Dict, Optional, List
from loguru import logger
import sys
sys.path.append('../..')
from shared.config import OPENAI_API_KEY, OPENAI_MODEL

# Configurar cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

class AudioTranscriber:
    """Gerencia transcrição de áudio para texto"""
    
    def __init__(self):
        self.max_file_size = 25 * 1024 * 1024  # 25MB limite do Whisper
        
    async def transcribe_audio(self, audio_path: str, language: str = "pt") -> Dict:
        """
        Transcreve arquivo de áudio
        
        Args:
            audio_path: Caminho do arquivo de áudio
            language: Idioma do áudio (padrão: português)
            
        Returns:
            Dict com transcrição e metadados
        """
        try:
            audio_file = Path(audio_path)
            
            if not audio_file.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")
            
            file_size = audio_file.stat().st_size
            
            # Verificar tamanho do arquivo
            if file_size > self.max_file_size:
                logger.warning(f"Arquivo muito grande ({file_size} bytes), será dividido")
                return await self._transcribe_large_file(audio_path, language)
            
            # Transcrever arquivo único
            logger.info(f"Iniciando transcrição de: {audio_file.name}")
            
            with open(audio_path, "rb") as audio:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language=language,
                    response_format="verbose_json",
                    prompt="Esta é uma transcrição de reunião corporativa em português do Brasil."
                )
            
            logger.info("Transcrição concluída com sucesso")
            
            return {
                'success': True,
                'text': response.text,
                'segments': response.segments if hasattr(response, 'segments') else [],
                'language': response.language if hasattr(response, 'language') else language,
                'duration': response.duration if hasattr(response, 'duration') else 0
            }
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }
    
    async def _transcribe_large_file(self, audio_path: str, language: str) -> Dict:
        """Transcreve arquivos grandes dividindo em chunks"""
        # TODO: Implementar divisão de arquivos grandes
        # Por enquanto, retornar erro
        return {
            'success': False,
            'error': 'Arquivo muito grande. Divisão ainda não implementada.',
            'text': ''
        }
    
    async def extract_meeting_structure(self, transcription: str) -> Dict:
        """
        Extrai estrutura da reunião usando IA
        
        Args:
            transcription: Texto transcrito
            
        Returns:
            Dict com estrutura extraída
        """
        try:
            prompt = f"""
            Analise a seguinte transcrição de reunião e extraia as informações estruturadas.
            
            Transcrição:
            {transcription}
            
            Extraia e organize:
            1. Resumo executivo (2-3 parágrafos)
            2. Decisões tomadas (com responsáveis e prazos quando mencionados)
            3. Ações definidas (com responsáveis e prazos)
            4. Pendências ou bloqueios identificados
            5. Insights sobre a dinâmica da equipe
            6. Participantes identificados
            
            Responda em formato JSON com a seguinte estrutura:
            {{
                "resumo_executivo": "texto do resumo",
                "decisoes": [
                    {{"decisao": "texto", "responsavel": "nome", "prazo": "data"}}
                ],
                "acoes": [
                    {{"acao": "texto", "responsavel": "nome", "prazo": "data"}}
                ],
                "pendencias": [
                    {{"pendencia": "texto"}}
                ],
                "insights": [
                    {{"insight": "texto"}}
                ],
                "participantes": ["nome1", "nome2"]
            }}
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de reuniões corporativas."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            logger.info("Estrutura da reunião extraída com sucesso")
            return {
                'success': True,
                **result
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair estrutura: {e}")
            return {
                'success': False,
                'error': str(e),
                'resumo_executivo': transcription[:500] + '...' if len(transcription) > 500 else transcription,
                'decisoes': [],
                'acoes': [],
                'pendencias': [],
                'insights': [],
                'participantes': []
            }
    
    async def generate_meeting_title(self, transcription: str, current_title: str = None) -> str:
        """
        Gera ou melhora título da reunião baseado no conteúdo
        
        Args:
            transcription: Texto transcrito
            current_title: Título atual (opcional)
            
        Returns:
            Título sugerido
        """
        try:
            prompt = f"""
            Com base na transcrição abaixo, sugira um título conciso e descritivo para a reunião.
            {f'Título atual: {current_title}' if current_title else ''}
            
            Transcrição (primeiros 1000 caracteres):
            {transcription[:1000]}...
            
            O título deve:
            - Ter no máximo 50 caracteres
            - Capturar o tema principal da reunião
            - Ser profissional e claro
            
            Responda apenas com o título sugerido.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um assistente que cria títulos concisos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=50
            )
            
            suggested_title = response.choices[0].message.content.strip()
            
            # Limitar tamanho e remover aspas se houver
            suggested_title = suggested_title.replace('"', '').replace("'", '')[:50]
            
            return suggested_title or current_title or "Reunião sem título"
            
        except Exception as e:
            logger.error(f"Erro ao gerar título: {e}")
            return current_title or "Reunião sem título"
    
    def estimate_transcription_time(self, file_size: int) -> int:
        """
        Estima tempo de transcrição baseado no tamanho do arquivo
        
        Args:
            file_size: Tamanho do arquivo em bytes
            
        Returns:
            Tempo estimado em segundos
        """
        # Estimativa: ~1MB por minuto de áudio, ~10s de processamento por minuto
        minutes = file_size / (1024 * 1024)
        return int(minutes * 10)

# Instância singleton do transcritor
audio_transcriber = AudioTranscriber()