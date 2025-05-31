from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QListWidget, QListWidgetItem, QLineEdit, QSpacerItem, QSizePolicy, 
                             QTextEdit, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from PyQt6.QtGui import QFont
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
import json
from pathlib import Path

from src.core.style_manager import StyleManager
from src.core.api_client import api_client
from src.core.auth_manager import auth_manager

class HistoryLoadWorker(QThread):
    """Worker thread para carregar histórico do Supabase ou arquivo local"""
    
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def run(self):
        """Carrega dados do histórico das embeddings"""
        try:
            # Tentar carregar do Supabase (da tabela de embeddings)
            try:
                # Buscar reuniões agrupadas por reuniao_id da tabela de embeddings
                response = auth_manager.supabase.table('historico_reunioes_embeddings')\
                    .select('reuniao_id, metadata, created_at')\
                    .eq('tipo_chunk', 'resumo')\
                    .order('created_at', desc=True)\
                    .execute()
                
                meetings = []
                if response.data:
                    # Processar embeddings para reconstruir dados das reuniões
                    for item in response.data:
                        metadata = item.get('metadata', {})
                        if metadata:
                            meeting_data = {
                                'id': item['reuniao_id'],
                                'titulo': metadata.get('titulo', 'Reunião sem título'),
                                'descricao': metadata.get('descricao', 'Sem descrição'),
                                'data_reuniao': item.get('created_at', ''),
                                'duracao_segundos': metadata.get('duracao_segundos', 0),
                                'responsible_usuario_username': metadata.get('responsible_usuario_username', 'N/A'),
                                'status': metadata.get('status', 'concluida'),
                                'tipo_reuniao': metadata.get('tipo_reuniao', 'geral'),
                                'participantes': metadata.get('participantes', []),
                                'resumo': metadata.get('resumo', 'Sem resumo'),
                                'pontos_principais': metadata.get('pontos_principais', []),
                                'tarefas_identificadas': metadata.get('tarefas_identificadas', []),
                                'transcricao_completa': '', # Será carregada dinamicamente se necessário
                                'metadados': metadata.get('metadados', {})
                            }
                            meetings.append(meeting_data)
                
                # Se encontrou dados no Supabase, usar eles
                if meetings:
                    logger.info(f"Carregadas {len(meetings)} reuniões do Supabase (embeddings)")
                    self.data_loaded.emit(meetings)
                    return
                else:
                    logger.info("Nenhuma reunião encontrada no Supabase embeddings, tentando arquivo local...")
                
            except Exception as supabase_error:
                logger.warning(f"Supabase não disponível, carregando dados locais: {supabase_error}")
            
            # Fallback: Carregar do arquivo local
            local_file = Path("cache/reunioes_locais.json")
            if local_file.exists():
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        meetings = json.load(f)
                    
                    # Ordenar por data (mais recente primeiro)
                    meetings.sort(key=lambda x: x.get('data_reuniao', ''), reverse=True)
                    
                    logger.info(f"Carregadas {len(meetings)} reuniões do arquivo local")
                    self.data_loaded.emit(meetings)
                    return
                    
                except Exception as local_error:
                    logger.error(f"Erro ao carregar arquivo local: {local_error}")
            else:
                logger.info("Arquivo local não existe ainda")
            
            # Se chegou aqui, não há dados
            logger.info("Nenhuma reunião encontrada")
            self.data_loaded.emit([])
            
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            self.error_occurred.emit(str(e))

class HistoryWindow(QWidget):
    back_to_home = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.meetings_data = []
        self.worker = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        
        title = QLabel("📅 Histórico de Reuniões")
        title.setProperty("class", "title")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Botão Atualizar
        self.refresh_button = QPushButton("🔄 Atualizar")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.refresh_button.clicked.connect(self.load_meetings)
        header_layout.addWidget(self.refresh_button)
        
        # Botão Voltar
        self.back_button = QPushButton("← Voltar")
        StyleManager.apply_button_style(self.back_button, "secondary")
        self.back_button.clicked.connect(self.back_to_home.emit)
        header_layout.addWidget(self.back_button)
        
        layout.addLayout(header_layout)
        
        # Status de carregamento
        self.status_label = QLabel("Carregando reuniões...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #2196F3;
                border-radius: 5px;
                padding: 10px;
                color: #2196F3;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Campo de busca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por título, responsável...")
        self.search_input.textChanged.connect(self.filter_meetings)
        layout.addWidget(self.search_input)
        
        # Lista de reuniões
        self.meetings_list = QListWidget()
        self.meetings_list.itemClicked.connect(self.show_meeting_details)
        self.meetings_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.meetings_list)
        
        # Área de detalhes (inicialmente oculta)
        self.details_area = QTextEdit()
        self.details_area.setMinimumHeight(200)  # Altura mínima
        self.details_area.setMaximumHeight(400)  # Altura máxima expandida
        self.details_area.setReadOnly(True)
        self.details_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
                padding: 10px;
                font-family: 'Segoe UI', Tahoma, sans-serif;
                font-size: 9pt;
                line-height: 1.4;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        self.details_area.hide()
        layout.addWidget(self.details_area)
        
        self.setLayout(layout)
        
    def load_meetings(self):
        """Carrega a lista de reuniões do Supabase"""
        if self.worker and self.worker.isRunning():
            return
        
        self.status_label.setText("🔄 Carregando reuniões...")
        self.status_label.show()
        self.meetings_list.clear()
        self.details_area.hide()
        self.refresh_button.setEnabled(False)
        
        # Criar worker para carregar dados
        self.worker = HistoryLoadWorker()
        self.worker.data_loaded.connect(self.on_data_loaded)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
        
    def on_data_loaded(self, meetings: List[Dict[str, Any]]):
        """Callback quando dados são carregados"""
        self.meetings_data = meetings
        self.refresh_button.setEnabled(True)
        
        if not meetings:
            self.status_label.setText("📝 Nenhuma reunião encontrada")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 10px;
                    color: #856404;
                }
            """)
            return
        
        self.status_label.hide()
        self.populate_meetings_list(meetings)
        
        logger.info(f"Carregadas {len(meetings)} reuniões do histórico")
        
    def on_error(self, error_message: str):
        """Callback quando ocorre erro"""
        self.refresh_button.setEnabled(True)
        self.status_label.setText(f"❌ Erro ao carregar: {error_message}")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 5px;
                padding: 10px;
                color: #721c24;
            }
        """)
        
        QMessageBox.warning(
            self,
            "Erro",
            f"Não foi possível carregar o histórico:\n\n{error_message}"
        )
        
    def populate_meetings_list(self, meetings: List[Dict[str, Any]]):
        """Popula a lista com as reuniões"""
        for meeting in meetings:
            try:
                # Formatar data
                data_reuniao = meeting.get('data_reuniao', '')
                if data_reuniao:
                    dt = datetime.fromisoformat(data_reuniao.replace('Z', '+00:00'))
                    data_formatada = dt.strftime("%d/%m/%Y %H:%M")
                else:
                    data_formatada = "Data não informada"
                
                # Calcular duração
                duracao_segundos = meeting.get('duracao_segundos', 0)
                if duracao_segundos:
                    duracao_min = duracao_segundos // 60
                    duracao_texto = f"{duracao_min} min"
                else:
                    duracao_texto = "N/A"
                
                # Título da reunião
                titulo = meeting.get('titulo', 'Sem título')
                responsavel = meeting.get('responsible_usuario_username', 'N/A')
                
                # Texto do item
                item_text = f"📝 {titulo}\n📅 {data_formatada} | 👤 {responsavel} | ⏱️ {duracao_texto}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, meeting)
                
                # Estilo baseado no status
                status = meeting.get('status', 'concluida')
                if status == 'concluida':
                    item.setBackground(Qt.GlobalColor.white)
                elif status == 'em_andamento':
                    item.setBackground(Qt.GlobalColor.yellow)
                else:
                    item.setBackground(Qt.GlobalColor.lightGray)
                
                self.meetings_list.addItem(item)
                
            except Exception as e:
                logger.error(f"Erro ao processar reunião: {e}")
                continue
            
    def filter_meetings(self):
        """Filtra reuniões baseado na busca"""
        search_text = self.search_input.text().lower()
        
        for i in range(self.meetings_list.count()):
            item = self.meetings_list.item(i)
            meeting_data = item.data(Qt.ItemDataRole.UserRole)
            
            # Busca no título e responsável
            titulo = meeting_data.get('titulo', '').lower()
            responsavel = meeting_data.get('responsible_usuario_username', '').lower()
            
            show_item = (search_text in titulo or search_text in responsavel)
            item.setHidden(not show_item)
            
    def show_meeting_details(self, item):
        """Mostra detalhes da reunião selecionada"""
        meeting_data = item.data(Qt.ItemDataRole.UserRole)
        
        # Formatar dados
        titulo = meeting_data.get('titulo', 'N/A')
        descricao = meeting_data.get('descricao', 'Sem descrição')
        
        # Data
        data_reuniao = meeting_data.get('data_reuniao', '')
        if data_reuniao:
            dt = datetime.fromisoformat(data_reuniao.replace('Z', '+00:00'))
            data_formatada = dt.strftime("%d/%m/%Y às %H:%M")
        else:
            data_formatada = "N/A"
        
        # Duração
        duracao_segundos = meeting_data.get('duracao_segundos', 0)
        if duracao_segundos:
            duracao_min = duracao_segundos // 60
            duracao_sec = duracao_segundos % 60
            duracao_texto = f"{duracao_min}m {duracao_sec}s"
        else:
            duracao_texto = "N/A"
        
        responsavel = meeting_data.get('responsible_usuario_username', 'N/A')
        status = meeting_data.get('status', 'N/A')
        tipo_reuniao = meeting_data.get('tipo_reuniao', 'N/A')
        
        # Participantes
        participantes = meeting_data.get('participantes', [])
        participantes_texto = ', '.join(participantes) if participantes else 'N/A'
        
        # Resumo
        resumo = meeting_data.get('resumo', 'Sem resumo disponível')
        
        # Pontos principais
        pontos = meeting_data.get('pontos_principais', [])
        if pontos and len(pontos) > 0:
            pontos_texto = '\n'.join([f"• {ponto}" for ponto in pontos])
        else:
            pontos_texto = 'Nenhum ponto identificado'
        
        # Tarefas
        tarefas = meeting_data.get('tarefas_identificadas', [])
        if tarefas and len(tarefas) > 0:
            tarefas_texto = '\n'.join([f"• {tarefa}" for tarefa in tarefas])
        else:
            tarefas_texto = 'Nenhuma tarefa identificada'
        
        # Verificar se o resumo é automático
        metadados = meeting_data.get('metadados', {})
        resumo_automatico = metadados.get('resumo_automatico', False)
        resumo_badge = " 🤖" if resumo_automatico else ""
        
        # Carregar transcrição completa dos embeddings
        transcricao = self._load_full_transcription(meeting_data.get('id'))
        
        details_text = f"""
📝 TÍTULO: {titulo}

📋 DESCRIÇÃO: {descricao}

📅 DATA: {data_formatada}
⏱️ DURAÇÃO: {duracao_texto}
👤 RESPONSÁVEL: {responsavel}
📊 STATUS: {status}
🎯 TIPO: {tipo_reuniao}
👥 PARTICIPANTES: {participantes_texto}

💡 RESUMO{resumo_badge}:
{resumo}

🎯 PONTOS PRINCIPAIS:
{pontos_texto}

✅ TAREFAS IDENTIFICADAS:
{tarefas_texto}

📄 TRANSCRIÇÃO COMPLETA:
{transcricao}
        """.strip()
        
        self.details_area.setText(details_text)
        self.details_area.show()
        
        # Rolar para o topo após mostrar detalhes
        cursor = self.details_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.details_area.setTextCursor(cursor)

    def _load_full_transcription(self, meeting_id: str) -> str:
        """
        Carrega a transcrição completa de uma reunião específica dos embeddings
        
        Args:
            meeting_id: ID da reunião
            
        Returns:
            Transcrição completa reconstituída
        """
        if not meeting_id:
            return "Transcrição não disponível"
        
        try:
            # Buscar todos os chunks de transcrição desta reunião
            response = auth_manager.supabase.table('historico_reunioes_embeddings')\
                .select('texto_chunk, chunk_index')\
                .eq('reuniao_id', meeting_id)\
                .eq('tipo_chunk', 'transcricao')\
                .order('chunk_index')\
                .execute()
            
            if response.data:
                # Reconstruir transcrição ordenando por chunk_index
                chunks = sorted(response.data, key=lambda x: x.get('chunk_index', 0))
                transcricao_parts = []
                
                for chunk in chunks:
                    texto = chunk.get('texto_chunk', '')
                    # Remover prefixo "Reunião '{titulo}':" se presente
                    if texto.startswith('Reunião ') and ':' in texto:
                        texto = texto.split(':', 1)[1].strip()
                    transcricao_parts.append(texto)
                
                transcricao_completa = ' '.join(transcricao_parts)
                logger.info(f"Transcrição carregada: {len(transcricao_completa)} caracteres de {len(chunks)} chunks")
                return transcricao_completa
            else:
                logger.warning(f"Nenhum chunk de transcrição encontrado para reunião {meeting_id}")
                return "Nenhuma transcrição encontrada para esta reunião"
                
        except Exception as e:
            logger.error(f"Erro ao carregar transcrição da reunião {meeting_id}: {e}")
            return f"Erro ao carregar transcrição: {e}"
        
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        self.load_meetings()
        self.search_input.clear()
        self.details_area.hide() 