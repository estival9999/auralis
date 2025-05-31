"""
Janela de Histórico de Reuniões do Sistema AURALIS
Visualização e busca de reuniões anteriores
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
                            QSpacerItem, QSizePolicy, QSplitter, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot
from datetime import datetime
from loguru import logger
import asyncio
import sys
sys.path.append('../..')
from src.database.supabase_client import supabase_client

class MeetingLoaderWorker(QThread):
    """Worker thread para carregar reuniões"""
    meetings_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def run(self):
        """Carrega reuniões do banco"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            meetings = loop.run_until_complete(supabase_client.get_meetings(limit=50))
            self.meetings_loaded.emit(meetings)
            
            loop.close()
        except Exception as e:
            logger.error(f"Erro ao carregar reuniões: {e}")
            self.error_occurred.emit(str(e))

class MeetingDetailsWorker(QThread):
    """Worker thread para carregar detalhes de uma reunião"""
    details_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, meeting_id: str):
        super().__init__()
        self.meeting_id = meeting_id
    
    def run(self):
        """Carrega detalhes da reunião"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            details = loop.run_until_complete(supabase_client.get_meeting_details(self.meeting_id))
            if details:
                self.details_loaded.emit(details)
            else:
                self.error_occurred.emit("Reunião não encontrada")
            
            loop.close()
        except Exception as e:
            logger.error(f"Erro ao carregar detalhes: {e}")
            self.error_occurred.emit(str(e))

class HistoryWindow(QWidget):
    """Janela de histórico de reuniões"""
    back_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.meetings_data = []
        self.init_ui()
        
    def init_ui(self):
        """Inicializa interface da janela"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Botão Voltar
        self.back_button = QPushButton("← Voltar")
        self.back_button.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(self.back_button)
        
        # Título
        title = QLabel("Histórico de Reuniões")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title, 1)
        
        # Espaçador para balancear
        header_layout.addWidget(QWidget(), 0)
        
        layout.addLayout(header_layout)
        
        # Campo de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar reuniões...")
        self.search_input.textChanged.connect(self.filter_meetings)
        search_layout.addWidget(self.search_input)
        
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setMaximumWidth(40)
        self.refresh_button.clicked.connect(self.load_meetings)
        search_layout.addWidget(self.refresh_button)
        
        layout.addLayout(search_layout)
        
        # Splitter para lista e detalhes
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Lista de reuniões
        self.meetings_list = QListWidget()
        self.meetings_list.itemClicked.connect(self.on_meeting_selected)
        splitter.addWidget(self.meetings_list)
        
        # Área de detalhes
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Selecione uma reunião para ver os detalhes")
        splitter.addWidget(self.details_text)
        
        # Proporção 40/60
        splitter.setSizes([200, 300])
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        self.load_meetings()
        self.details_text.clear()
        self.search_input.clear()
    
    def load_meetings(self):
        """Carrega lista de reuniões"""
        self.meetings_list.clear()
        self.meetings_list.addItem("Carregando reuniões...")
        
        # Carregar em thread separada
        self.loader_worker = MeetingLoaderWorker()
        self.loader_worker.meetings_loaded.connect(self.on_meetings_loaded)
        self.loader_worker.error_occurred.connect(self.on_load_error)
        self.loader_worker.start()
    
    @pyqtSlot(list)
    def on_meetings_loaded(self, meetings):
        """Processa reuniões carregadas"""
        self.meetings_data = meetings
        self.meetings_list.clear()
        
        if not meetings:
            self.meetings_list.addItem("Nenhuma reunião encontrada")
            return
        
        for meeting in meetings:
            # Formatar item da lista
            titulo = meeting.get('titulo', 'Sem título')
            data_str = meeting.get('data_reuniao', '')
            responsavel = meeting.get('responsavel', 'Não identificado')
            
            # Formatar data
            try:
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                data_formatada = data.strftime('%d/%m/%Y %H:%M')
            except:
                data_formatada = 'Data não disponível'
            
            # Criar item formatado
            item_text = f"{titulo} - {data_formatada} - {responsavel}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, meeting)
            self.meetings_list.addItem(item)
    
    @pyqtSlot(str)
    def on_load_error(self, error):
        """Trata erro no carregamento"""
        self.meetings_list.clear()
        self.meetings_list.addItem(f"Erro ao carregar: {error}")
        logger.error(f"Erro ao carregar reuniões: {error}")
    
    def filter_meetings(self, text):
        """Filtra reuniões baseado no texto de busca"""
        search_text = text.lower()
        
        for i in range(self.meetings_list.count()):
            item = self.meetings_list.item(i)
            if item:
                # Mostrar/ocultar baseado no texto
                item_text = item.text().lower()
                item.setHidden(search_text not in item_text)
    
    def on_meeting_selected(self, item):
        """Carrega detalhes da reunião selecionada"""
        meeting = item.data(Qt.ItemDataRole.UserRole)
        if not meeting or not meeting.get('id'):
            return
        
        self.details_text.setPlainText("Carregando detalhes...")
        
        # Carregar detalhes em thread separada
        self.details_worker = MeetingDetailsWorker(meeting['id'])
        self.details_worker.details_loaded.connect(self.display_meeting_details)
        self.details_worker.error_occurred.connect(self.on_details_error)
        self.details_worker.start()
    
    @pyqtSlot(dict)
    def display_meeting_details(self, meeting):
        """Exibe detalhes formatados da reunião"""
        # Formatar transcrição estruturada
        formatted_text = ""
        
        # Cabeçalho
        titulo = meeting.get('titulo', 'Sem título')
        data_str = meeting.get('data_reuniao', '')
        responsavel = meeting.get('responsavel', 'Não identificado')
        duracao = meeting.get('duracao', 0)
        
        try:
            data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
            data_formatada = data.strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = 'Data não disponível'
        
        formatted_text = f"{titulo} - {data_formatada} - {responsavel}\n"
        formatted_text += f"Duração: {duracao} minutos\n"
        formatted_text += "="*60 + "\n\n"
        
        # Resumo Executivo
        if meeting.get('resumo_executivo'):
            formatted_text += "📋 RESUMO EXECUTIVO:\n"
            formatted_text += meeting['resumo_executivo'] + "\n\n"
        
        # Decisões
        if meeting.get('decisoes'):
            formatted_text += "🎯 DECISÕES TOMADAS:\n"
            for decisao in meeting['decisoes']:
                texto = decisao.get('decisao', 'N/A')
                resp = decisao.get('responsavel', '')
                prazo = decisao.get('prazo', '')
                
                formatted_text += f"• {texto}"
                if resp:
                    formatted_text += f" - Responsável: {resp}"
                if prazo:
                    formatted_text += f" - Prazo: {prazo}"
                formatted_text += "\n"
            formatted_text += "\n"
        
        # Ações
        if meeting.get('acoes'):
            formatted_text += "✅ AÇÕES DEFINIDAS:\n"
            for acao in meeting['acoes']:
                texto = acao.get('acao', 'N/A')
                resp = acao.get('responsavel', '')
                prazo = acao.get('prazo', '')
                
                formatted_text += f"• {texto}"
                if resp:
                    formatted_text += f" - {resp}"
                if prazo:
                    formatted_text += f" - {prazo}"
                formatted_text += "\n"
            formatted_text += "\n"
        
        # Pendências
        if meeting.get('pendencias'):
            formatted_text += "⚠️ PENDÊNCIAS/BLOQUEIOS:\n"
            for pendencia in meeting['pendencias']:
                if isinstance(pendencia, dict):
                    formatted_text += f"• {pendencia.get('item', 'N/A')}\n"
                else:
                    formatted_text += f"• {pendencia}\n"
            formatted_text += "\n"
        
        # Insights
        if meeting.get('insights'):
            formatted_text += "📊 INSIGHTS DA EQUIPE:\n"
            for insight in meeting['insights']:
                if isinstance(insight, dict):
                    formatted_text += f"• {insight.get('item', 'N/A')}\n"
                else:
                    formatted_text += f"• {insight}\n"
            formatted_text += "\n"
        
        # Transcrição completa
        if meeting.get('transcricao_completa'):
            formatted_text += "="*60 + "\n"
            formatted_text += "📄 TRANSCRIÇÃO COMPLETA:\n"
            formatted_text += meeting['transcricao_completa']
        
        self.details_text.setPlainText(formatted_text)
        
        # Rolar para o topo
        cursor = self.details_text.textCursor()
        cursor.setPosition(0)
        self.details_text.setTextCursor(cursor)
    
    @pyqtSlot(str)
    def on_details_error(self, error):
        """Trata erro ao carregar detalhes"""
        self.details_text.setPlainText(f"Erro ao carregar detalhes: {error}")
        logger.error(f"Erro ao carregar detalhes da reunião: {error}")