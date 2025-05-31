#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QMessageBox, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont
from loguru import logger
import os
import threading

from ..core.audio_manager import audio_manager
from ..core.api_client import api_client
from ..core.auth_manager import auth_manager
from ..core.ai_manager import ai_manager
from ..core.style_manager import StyleManager
from ..core.agents.meeting_summarizer import meeting_summarizer

class SaveMeetingWorker(QThread):
    """Worker thread para salvar reunião no Supabase e gerar embeddings"""
    
    meeting_saved = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, titulo: str, responsible_username: str, 
                 transcricao: str, duracao_segundos: int, 
                 data_reuniao: str, arquivo_audio_url: Optional[str] = None):
        super().__init__()
        self.titulo = titulo
        self.responsible_username = responsible_username
        self.transcricao = transcricao
        self.duracao_segundos = duracao_segundos
        self.data_reuniao = data_reuniao
        self.arquivo_audio_url = arquivo_audio_url
    
    def run(self):
        """Salva a reunião diretamente como embeddings no Supabase"""
        try:
            logger.info("🔍 DEBUG: SaveMeetingWorker iniciado")
            
            # Gerar resumo automático se há transcrição suficiente
            resumo_gerado = "Resumo será gerado automaticamente"
            pontos_principais = []
            tarefas_identificadas = []
            
            if self.transcricao and len(self.transcricao.strip()) > 50:
                try:
                    logger.info("🔍 DEBUG: Gerando resumo automático...")
                    summary_result = meeting_summarizer.generate_meeting_summary(
                        transcricao=self.transcricao,
                        titulo=self.titulo
                    )
                    
                    resumo_gerado = summary_result.get('resumo', resumo_gerado)
                    pontos_principais = summary_result.get('pontos_principais', [])
                    tarefas_identificadas = summary_result.get('tarefas_identificadas', [])
                    
                    logger.info(f"🔍 DEBUG: ✅ Resumo gerado - {len(pontos_principais)} pontos, {len(tarefas_identificadas)} tarefas")
                    
                except Exception as summary_error:
                    logger.warning(f"🔍 DEBUG: ⚠️ Erro ao gerar resumo automático: {summary_error}")
            
            # Gerar ID único para a reunião
            meeting_id = str(uuid.uuid4())
            logger.info(f"🔍 DEBUG: Meeting ID gerado: {meeting_id}")
            
            # Tentar salvar diretamente como embeddings no Supabase
            try:
                logger.info("🔍 DEBUG: Salvando reunião como embeddings...")
                
                # Gerar embeddings diretamente sem salvar na tabela principal
                if self.transcricao and len(self.transcricao.strip()) > 10:
                    self._generate_embeddings_async(meeting_id, {
                        'titulo': self.titulo,
                        'descricao': f"Reunião gravada em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        'data_reuniao': self.data_reuniao,
                        'duracao_segundos': self.duracao_segundos,
                        'responsible_usuario_username': self.responsible_username,
                        'transcricao_completa': self.transcricao,
                        'resumo': resumo_gerado,
                        'pontos_principais': pontos_principais,
                        'tarefas_identificadas': tarefas_identificadas,
                        'status': 'concluida',
                        'tipo_reuniao': 'geral',
                        'metadados': {
                            'fonte': 'gravacao_local',
                            'versao_app': '1.0.0',
                            'resumo_automatico': True if len(pontos_principais) > 0 else False
                        }
                    })
                    
                    logger.info(f"🔍 DEBUG: ✅ Reunião salva como embeddings: {meeting_id}")
                    self.meeting_saved.emit(True, "Reunião salva no Supabase como embeddings!")
                    return
                else:
                    logger.warning("🔍 DEBUG: ⚠️ Transcrição muito curta para embeddings")
                    
            except Exception as supabase_error:
                logger.warning(f"🔍 DEBUG: ❌ Erro do Supabase embeddings, salvando localmente: {supabase_error}")
            
            # Fallback: Salvar em arquivo local
            logger.info("🔍 DEBUG: Salvando em arquivo local...")
            local_file = Path("cache/reunioes_locais.json")
            local_file.parent.mkdir(exist_ok=True)
            
            # Preparar dados da reunião para arquivo local
            reuniao_data = {
                "id": meeting_id,
                "titulo": str(self.titulo),
                "descricao": f"Reunião gravada em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "data_reuniao": self.data_reuniao,
                "duracao_segundos": int(self.duracao_segundos),
                "local_reuniao": "Gravação Local",
                "participantes": [str(self.responsible_username)],
                "transcricao_completa": str(self.transcricao) if self.transcricao else "",
                "resumo": resumo_gerado,
                "pontos_principais": pontos_principais,
                "tarefas_identificadas": tarefas_identificadas,
                "responsible_usuario_username": str(self.responsible_username),
                "arquivo_audio_url": str(self.arquivo_audio_url) if self.arquivo_audio_url else None,
                "status": "concluida",
                "tipo_reuniao": "geral",
                "confidencialidade": "normal",
                "qualidade_audio": 4,
                "idioma": "pt-BR",
                "metadados": {
                    "fonte": "gravacao_local",
                    "versao_app": "1.0.0",
                    "resumo_automatico": True if len(pontos_principais) > 0 else False
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Carregar reuniões existentes
            reunioes_existentes = []
            if local_file.exists():
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        reunioes_existentes = json.load(f)
                    logger.info(f"🔍 DEBUG: Carregadas {len(reunioes_existentes)} reuniões existentes")
                except Exception as load_error:
                    logger.warning(f"🔍 DEBUG: Erro ao carregar reuniões existentes: {load_error}")
                    reunioes_existentes = []
            
            # Adicionar nova reunião
            reunioes_existentes.insert(0, reuniao_data)
            
            # Salvar arquivo atualizado
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(reunioes_existentes, f, ensure_ascii=False, indent=2)
            
            logger.info(f"🔍 DEBUG: ✅ Reunião salva localmente em: {local_file}")
            self.meeting_saved.emit(True, "Reunião salva localmente!")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"🔍 DEBUG: ❌ Erro crítico no SaveMeetingWorker: {error_msg}")
            self.meeting_saved.emit(False, f"Erro: {error_msg}")
    
    def _generate_embeddings_async(self, meeting_id: str, meeting_data: dict):
        """Gera embeddings para a reunião de forma assíncrona"""
        try:
            # Criar um novo loop de eventos para este thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Executar a geração de embeddings
            loop.run_until_complete(self._generate_embeddings(meeting_id, meeting_data))
            loop.close()
            
        except Exception as e:
            logger.error(f"Erro ao executar geração de embeddings: {e}")
            raise
    
    async def _generate_embeddings(self, meeting_id: str, meeting_data: dict):
        """Gera embeddings para o conteúdo da reunião dividido em chunks inteligentes"""
        try:
            # Preparar conteúdo para embedding
            title = meeting_data.get('titulo', '')
            description = meeting_data.get('descricao', '')
            transcription = meeting_data.get('transcricao_completa', '')
            
            logger.info(f"Gerando embeddings em chunks para reunião: {title}")
            
            # 1. Criar chunk do resumo/título
            summary_content = f"Título: {title}. Descrição: {description}"
            summary_embedding = await ai_manager.generate_embedding(summary_content)
            
            if summary_embedding:
                await self._save_embedding_chunk(
                    meeting_id, summary_content, 0, 'resumo', 
                    summary_embedding, title, description, len(transcription)
                )
                logger.info(f"✅ Chunk de resumo salvo para reunião {meeting_id}")
            
            # 2. Dividir transcrição em chunks menores se há conteúdo suficiente
            if transcription and len(transcription.strip()) > 50:
                chunks = self._split_transcription_into_chunks(transcription, max_chunk_size=800)
                logger.info(f"Transcrição dividida em {len(chunks)} chunks")
                
                for i, chunk_text in enumerate(chunks, 1):
                    # Adicionar contexto do título ao chunk
                    chunk_with_context = f"Reunião '{title}': {chunk_text}"
                    
                    chunk_embedding = await ai_manager.generate_embedding(chunk_with_context)
                    
                    if chunk_embedding:
                        await self._save_embedding_chunk(
                            meeting_id, chunk_with_context, i, 'transcricao',
                            chunk_embedding, title, description, len(chunk_text)
                        )
                        logger.info(f"✅ Chunk {i}/{len(chunks)} salvo para reunião {meeting_id}")
                    
                    # Pequena pausa para não sobrecarregar a API
                    await asyncio.sleep(0.1)
            
            logger.info(f"✅ Todos os embeddings gerados para reunião {meeting_id}")
            
        except Exception as e:
            logger.error(f"Erro ao gerar embeddings para reunião {meeting_id}: {e}")
            raise
    
    def _split_transcription_into_chunks(self, text: str, max_chunk_size: int = 800) -> list:
        """
        Divide a transcrição em chunks inteligentes baseados em sentenças
        
        Args:
            text: Texto da transcrição
            max_chunk_size: Tamanho máximo de cada chunk
            
        Returns:
            Lista de chunks de texto
        """
        chunks = []
        
        # Dividir por sentenças (pontos, exclamações, interrogações)
        import re
        sentences = re.split(r'[.!?]+', text)
        
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Se adicionar a sentença não ultrapassar o limite, adicionar
            if len(current_chunk) + len(sentence) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                # Salvar chunk atual se não estiver vazio
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Se a sentença em si é muito grande, dividir por palavras
                if len(sentence) > max_chunk_size:
                    words = sentence.split()
                    word_chunk = ""
                    
                    for word in words:
                        if len(word_chunk) + len(word) + 1 <= max_chunk_size:
                            if word_chunk:
                                word_chunk += " " + word
                            else:
                                word_chunk = word
                        else:
                            if word_chunk:
                                chunks.append(word_chunk.strip())
                            word_chunk = word
                    
                    if word_chunk:
                        current_chunk = word_chunk
                    else:
                        current_chunk = ""
                else:
                    current_chunk = sentence
        
        # Adicionar último chunk se houver
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _save_embedding_chunk(self, meeting_id: str, chunk_text: str, chunk_index: int, 
                                   chunk_type: str, embedding: list, title: str, description: str, 
                                   original_size: int):
        """
        Salva um chunk individual de embedding
        
        Args:
            meeting_id: ID da reunião
            chunk_text: Texto do chunk
            chunk_index: Índice do chunk
            chunk_type: Tipo do chunk (resumo, transcricao)
            embedding: Vetor de embedding
            title: Título da reunião
            description: Descrição da reunião
            original_size: Tamanho original do texto
        """
        try:
            embedding_data = {
                'reuniao_id': meeting_id,
                'texto_chunk': chunk_text,
                'chunk_index': chunk_index,
                'tipo_chunk': chunk_type,
                'embedding': embedding,
                'embedding_model': 'text-embedding-3-small',
                'metadata': {
                    'titulo': title,
                    'descricao': description,
                    'tamanho_chunk': len(chunk_text),
                    'tamanho_original': original_size,
                    'tipo': chunk_type
                },
                'created_at': datetime.now().isoformat()
            }
            
            # Inserir na tabela de embeddings
            result = auth_manager.supabase.table('historico_reunioes_embeddings')\
                .insert(embedding_data).execute()
            
            if not result.data:
                logger.warning(f"⚠️ Problema ao salvar chunk {chunk_index} da reunião {meeting_id}")
                
        except Exception as e:
            logger.error(f"Erro ao salvar chunk {chunk_index} da reunião {meeting_id}: {e}")
            raise

class RecordingWindow(QWidget):
    """Janela principal para gravação de reuniões"""
    
    back_to_home = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.recording_start_time = None
        self.current_meeting_id = None
        self.is_paused = False
        self.save_worker = None
        self.meeting_title = None  # Título personalizado da reunião
        
        # Timer para atualizar tempo de gravação
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_recording_time)
        
        self.setup_ui()
        self.setup_audio_callbacks()
        
        # Configurar chunk duration padrão para 30 segundos
        audio_manager.chunk_duration = 30
    
    def setup_ui(self):
        """Configura a interface"""
        self.setWindowTitle("Gravação de Reunião")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("🎙️ Gravação de Reunião")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Status da gravação
        self.status_label = QLabel("Pronto para iniciar gravação")
        self.status_label.setFont(QFont("Segoe UI", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                color: #495057;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Tempo de gravação
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Courier", 24, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                background-color: #f0f8ff;
                border: 1px solid #2196F3;
                border-radius: 8px;
                padding: 10px;
                margin: 10px 0;
            }
        """)
        layout.addWidget(self.time_label)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botões de controle
        self.create_control_buttons(layout)
        
        # Espaçador inferior
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    
    def create_control_buttons(self, layout):
        """Cria os botões de controle"""
        # Botão Iniciar
        self.start_btn = QPushButton("🎙️ Iniciar Gravação")
        self.start_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.start_btn.clicked.connect(self.start_recording)
        layout.addWidget(self.start_btn)
        
        # Botão Pausar (inicialmente oculto)
        self.pause_btn = QPushButton("⏸️ Pausar")
        self.pause_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.pause_btn.clicked.connect(self.pause_recording)
        self.pause_btn.setVisible(False)
        layout.addWidget(self.pause_btn)
        
        # Botão Parar/Retomar (inicialmente é Parar)
        self.stop_btn = QPushButton("⏹️ Parar")
        self.stop_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setVisible(False)
        layout.addWidget(self.stop_btn)
        
        # Botão Finalizar (inicialmente oculto)
        self.finish_btn = QPushButton("✅ Finalizar")
        self.finish_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.finish_btn.clicked.connect(self.finish_recording)
        self.finish_btn.setVisible(False)
        layout.addWidget(self.finish_btn)
        
        # Botão Voltar
        self.back_btn = QPushButton("← Voltar")
        self.back_btn.setFont(QFont("Segoe UI", 10))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.back_btn.clicked.connect(self.back_to_home.emit)
        layout.addWidget(self.back_btn)
    
    def setup_audio_callbacks(self):
        """Configura callbacks do audio manager"""
        audio_manager.on_recording_started = self.on_recording_started
        audio_manager.on_recording_stopped = self.on_recording_stopped
        audio_manager.on_error = self.on_audio_error
    
    def start_recording(self):
        """Inicia a gravação"""
        try:
            # Gerar ID único para a reunião
            self.current_meeting_id = str(uuid.uuid4())
            
            # Iniciar gravação (usando dispositivo padrão)
            audio_manager.start_recording(self.current_meeting_id, device_index=None)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar gravação: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao iniciar gravação:\n{e}")
    
    def pause_recording(self):
        """Pausa a gravação"""
        try:
            audio_manager.pause_recording()
            self.is_paused = True
            
            # Pausar o cronômetro também
            self.update_timer.stop()
            
            # Atualizar interface: pausar -> hide, parar -> retomar
            self.pause_btn.setVisible(False)
            self.stop_btn.setText("▶️ Retomar")
            self.stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 30px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.stop_btn.clicked.disconnect()
            self.stop_btn.clicked.connect(self.resume_recording)
            
            self.status_label.setText("⏸️ Gravação pausada")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 2px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 15px;
                    color: #856404;
                }
            """)
            
        except Exception as e:
            logger.error(f"Erro ao pausar gravação: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao pausar gravação:\n{e}")
    
    def resume_recording(self):
        """Retoma a gravação"""
        try:
            audio_manager.resume_recording()
            self.is_paused = False
            
            # Retomar o cronômetro também
            self.update_timer.start(1000)
            
            # Restaurar interface normal: mostrar pausar, parar volta a ser parar
            self.pause_btn.setVisible(True)
            self.stop_btn.setText("⏹️ Parar")
            self.stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 30px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            self.stop_btn.clicked.disconnect()
            self.stop_btn.clicked.connect(self.stop_recording)
            
            self.status_label.setText("🔴 Gravando...")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    border: 2px solid #c3e6cb;
                    border-radius: 8px;
                    padding: 15px;
                    color: #155724;
                }
            """)
            
        except Exception as e:
            logger.error(f"Erro ao retomar gravação: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao retomar gravação:\n{e}")
    
    def stop_recording(self):
        """Para a gravação"""
        try:
            audio_manager.stop_recording()
            
        except Exception as e:
            logger.error(f"Erro ao parar gravação: {e}")
            QMessageBox.critical(self, "Erro", f"Falha ao parar gravação:\n{e}")
    
    def finish_recording(self):
        """Finaliza e salva a reunião no Supabase"""
        logger.info("🔍 DEBUG: finish_recording() iniciado")
        
        if not self.current_meeting_id or not self.recording_start_time:
            logger.warning(f"🔍 DEBUG: Dados inválidos - meeting_id: {self.current_meeting_id}, start_time: {self.recording_start_time}")
            self.back_to_home.emit()
            return
        
        # Obter dados da reunião
        current_user = auth_manager.get_current_user()
        if not current_user:
            logger.error("🔍 DEBUG: Usuário não autenticado")
            QMessageBox.warning(self, "Erro", "Usuário não autenticado")
            self.back_to_home.emit()
            return
        
        username = current_user.get('username', 'usuario_desconhecido')
        logger.info(f"🔍 DEBUG: Usuário obtido: {username}")
        
        # Calcular duração
        duracao_segundos = int((datetime.now() - self.recording_start_time).total_seconds())
        logger.info(f"🔍 DEBUG: Duração calculada: {duracao_segundos} segundos")
        
        # Obter título da reunião
        titulo = self.meeting_title or f"Reunião {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        logger.info(f"🔍 DEBUG: Título da reunião: {titulo}")
        
        # Obter transcrições
        logger.info(f"🔍 DEBUG: Obtendo transcrições para meeting_id: {self.current_meeting_id}")
        transcricoes = audio_manager.get_cached_transcriptions(self.current_meeting_id)
        transcricao_completa = ""
        
        if transcricoes:
            logger.info(f"🔍 DEBUG: Encontradas {len(transcricoes)} transcrições")
            # Concatenar todas as transcrições
            textos = []
            for i, transcricao in enumerate(transcricoes):
                if 'text' in transcricao:
                    textos.append(transcricao['text'])
                    logger.debug(f"🔍 DEBUG: Transcrição {i}: {transcricao['text'][:50]}...")
            transcricao_completa = " ".join(textos)
            logger.info(f"🔍 DEBUG: Transcrição completa: {len(transcricao_completa)} caracteres")
        else:
            logger.warning("🔍 DEBUG: Nenhuma transcrição encontrada")
        
        # URL do arquivo de áudio (se disponível)
        audio_file_path = f"cache/audio/recording_{self.current_meeting_id}.wav"
        arquivo_audio_url = audio_file_path if audio_file_path else None
        logger.info(f"🔍 DEBUG: Arquivo de áudio: {arquivo_audio_url}")
        
        # Mostrar status de salvamento
        self.status_label.setText("💾 Salvando reunião...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 2px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                color: #856404;
            }
        """)
        
        self.finish_btn.setEnabled(False)
        
        logger.info("🔍 DEBUG: Criando SaveMeetingWorker...")
        
        # Criar worker para salvar
        self.save_worker = SaveMeetingWorker(
            titulo=titulo,
            responsible_username=username,
            transcricao=transcricao_completa,
            duracao_segundos=duracao_segundos,
            data_reuniao=self.recording_start_time.isoformat(),
            arquivo_audio_url=arquivo_audio_url
        )
        
        self.save_worker.meeting_saved.connect(self.on_meeting_saved)
        logger.info("🔍 DEBUG: Iniciando SaveMeetingWorker...")
        self.save_worker.start()
    
    def on_meeting_saved(self, success: bool, message: str):
        """Callback quando reunião é salva"""
        if success:
            self.status_label.setText("✅ Reunião salva com sucesso!")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    border: 2px solid #c3e6cb;
                    border-radius: 8px;
                    padding: 15px;
                    color: #155724;
                }
            """)
            
            # Limpar arquivos de áudio locais após salvamento bem-sucedido
            if self.current_meeting_id:
                self._cleanup_audio_files(self.current_meeting_id)
            
            # Aguardar um pouco e voltar para home
            QTimer.singleShot(2000, self.back_to_home.emit)
            
        else:
            self.status_label.setText(f"❌ Erro ao salvar: {message}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    border: 2px solid #f5c6cb;
                    border-radius: 8px;
                    padding: 15px;
                    color: #721c24;
                }
            """)
            
            # Reabilitar botão para tentar novamente
            self.finish_btn.setEnabled(True)
        
        logger.info(f"Salvamento da reunião: {message}")
    
    def _cleanup_audio_files(self, meeting_id: str):
        """
        Remove arquivos de áudio e transcrições da reunião específica após salvamento
        
        Args:
            meeting_id: ID da reunião para limpar
        """
        try:
            # Usar o método do AudioManager para limpeza
            audio_manager.cleanup_meeting_files(meeting_id)
                
        except Exception as e:
            logger.error(f"Erro durante limpeza de arquivos: {e}")
    
    def on_recording_started(self, meeting_id: str):
        """Callback quando gravação inicia"""
        self.recording_start_time = datetime.now()
        
        # Atualizar interface
        self.start_btn.setVisible(False)
        self.pause_btn.setVisible(True)
        self.stop_btn.setVisible(True)
        self.back_btn.setVisible(False)
        
        self.status_label.setText("🔴 Gravando...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                border: 2px solid #c3e6cb;
                border-radius: 8px;
                padding: 15px;
                color: #155724;
            }
        """)
        
        # Iniciar timer para atualizar tempo
        self.update_timer.start(1000)
        
        logger.info(f"Gravação iniciada na interface: {meeting_id}")
    
    def on_recording_stopped(self, final_file: Optional[str]):
        """Callback quando gravação para"""
        logger.info(f"🔍 DEBUG: on_recording_stopped chamado com final_file: {final_file}")
        
        # Parar timer
        self.update_timer.stop()
        
        # Atualizar interface para estado finalizado
        self.pause_btn.setVisible(False)
        self.stop_btn.setVisible(False)
        self.finish_btn.setVisible(True)
        
        if final_file:
            logger.info(f"🔍 DEBUG: Gravação finalizada com sucesso: {final_file}")
            self.status_label.setText("✅ Gravação finalizada com sucesso!")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d1ecf1;
                    border: 2px solid #bee5eb;
                    border-radius: 8px;
                    padding: 15px;
                    color: #0c5460;
                }
            """)
        else:
            logger.error("🔍 DEBUG: Erro ao finalizar gravação - final_file é None")
            self.status_label.setText("❌ Erro ao finalizar gravação")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    border: 2px solid #f5c6cb;
                    border-radius: 8px;
                    padding: 15px;
                    color: #721c24;
                }
            """)
        
        logger.info(f"🔍 DEBUG: Interface atualizada - botão Finalizar visível: {self.finish_btn.isVisible()}")
        logger.info(f"Gravação finalizada na interface: {self.current_meeting_id}")
    
    def on_audio_error(self, error_message: str):
        """Callback para erros de áudio"""
        QMessageBox.critical(self, "Erro de Áudio", error_message)
        
        # Resetar interface
        self.reset_interface()
    
    def update_recording_time(self):
        """Atualiza o tempo de gravação"""
        if not self.recording_start_time:
            return
        
        elapsed = datetime.now() - self.recording_start_time
        
        # Formatar tempo como HH:MM:SS
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.setText(time_str)
    
    def reset_interface(self):
        """Reseta a interface para o estado inicial"""
        self.update_timer.stop()
        self.recording_start_time = None
        self.current_meeting_id = None
        self.is_paused = False
        
        # Restaurar botões
        self.start_btn.setVisible(True)
        self.pause_btn.setVisible(False)
        self.stop_btn.setVisible(False)
        self.finish_btn.setVisible(False)
        self.back_btn.setVisible(True)
        
        # Resetar stop button para estado original
        self.stop_btn.setText("⏹️ Parar")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.stop_btn.clicked.disconnect()
        self.stop_btn.clicked.connect(self.stop_recording)
        
        # Restaurar labels
        self.status_label.setText("Pronto para iniciar gravação")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                color: #495057;
            }
        """)
        
        self.time_label.setText("00:00:00")
    
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        if audio_manager.is_recording:
            reply = QMessageBox.question(
                self, 
                "Gravação em Andamento",
                "Há uma gravação em andamento. Deseja parar e sair?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                audio_manager.stop_recording()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def set_meeting_title(self, title: str):
        """Define o título da reunião"""
        self.meeting_title = title
        logger.info(f"Título da reunião definido: {title}") 