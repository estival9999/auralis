from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QScrollArea, QTextEdit, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
from PyQt6.QtGui import QFont
from src.core.style_manager import StyleManager
from src.core.ai_manager_novo import ai_manager_novo  # Usando novo sistema
from loguru import logger
import asyncio

class ResponseWorker(QThread):
    """Worker thread para gerar respostas da IA usando sistema de agentes"""
    
    response_generated = pyqtSignal(str, dict)  # resposta + metadados
    error_occurred = pyqtSignal(str)
    
    def __init__(self, question: str):
        super().__init__()
        self.question = question
        
    def run(self):
        """Gera resposta da IA usando agentes especialistas"""
        try:
            # Executar função async em thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(ai_manager_novo.generate_response(self.question))
            
            if response:
                # Obter estatísticas do sistema
                stats = ai_manager_novo.get_estatisticas_sistema()
                self.response_generated.emit(response, stats)
            else:
                self.error_occurred.emit("Resposta vazia da IA")
                
            loop.close()
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com agentes: {e}")
            self.error_occurred.emit(f"Erro: {str(e)}")

class AuralisChatWindow(QWidget):
    start_listening = pyqtSignal()
    back_to_home = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.chat_history = []
        self.response_worker = None
        self.session_id = None  # ID da sessão atual
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        
        title = QLabel("🤖 Auralis AI - Agentes Especialistas")
        title.setProperty("class", "title")
        header_layout.addWidget(title)
        
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Botão Nova Conversa
        self.new_chat_button = QPushButton("🆕 Nova Conversa")
        StyleManager.apply_button_style(self.new_chat_button, "primary")
        self.new_chat_button.clicked.connect(self.start_new_conversation)
        header_layout.addWidget(self.new_chat_button)
        
        # Botão Voltar
        self.back_button = QPushButton("← Voltar")
        StyleManager.apply_button_style(self.back_button, "secondary")
        self.back_button.clicked.connect(self.handle_back)
        header_layout.addWidget(self.back_button)
        
        layout.addLayout(header_layout)
        
        # Info da sessão
        self.session_info = QLabel("💬 Nova sessão será criada ao fazer primeira pergunta")
        self.session_info.setProperty("class", "subtitle")
        self.session_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.session_info)
        
        # Área de chat
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setMaximumHeight(150)
        self.chat_area.setPlaceholderText("💬 Suas conversas com Auralis aparecerão aqui...")
        layout.addWidget(self.chat_area)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Status/Instrução
        self.status_label = QLabel("Clique em 'Perguntar' para fazer uma pergunta por áudio")
        self.status_label.setProperty("class", "subtitle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botão Perguntar
        self.ask_button = QPushButton("🎤 Perguntar")
        StyleManager.apply_button_style(self.ask_button, "success")
        self.ask_button.clicked.connect(self.start_listening.emit)
        layout.addWidget(self.ask_button)
        
        self.setLayout(layout)
        
    def start_new_conversation(self):
        """Inicia nova conversa"""
        try:
            # Finalizar sessão anterior se existir
            if self.session_id:
                asyncio.create_task(ai_manager_novo.finalizar_conversa_atual())
            
            # Limpar chat local ANTES de iniciar nova sessão
            self.clear_chat()
            
            # Iniciar nova sessão
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.session_id = loop.run_until_complete(ai_manager_novo.iniciar_nova_conversa())
            
            loop.close()
            
            # Atualizar interface
            self.session_info.setText(f"💬 Nova conversa iniciada: {self.session_id[:8]}...")
            self.status_label.setText("Conversa iniciada! Faça sua primeira pergunta.")
            
            logger.info(f"Nova conversa iniciada: {self.session_id}")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar nova conversa: {e}")
            self.status_label.setText(f"Erro ao iniciar conversa: {str(e)}")
        
    def add_question(self, question_text):
        """Adiciona uma pergunta ao chat e gera resposta real da Auralis"""
        logger.info(f"Pergunta recebida para Auralis: {question_text}")
        
        # Verificar se há sessão ativa, se não, criar uma
        if not self.session_id:
            self.start_new_conversation()
        
        # Adicionar pergunta do usuário
        self.add_message("Você", question_text, is_user=True)
        
        # Verificar se IA está disponível
        if not ai_manager_novo.openai_client:
            self.add_message("Auralis", "Desculpe, o sistema de IA não está disponível no momento. Verifique a configuração da OpenAI.", is_user=False)
            return
        
        # Mostrar "Auralis pensando..."
        self.status_label.setText("🤔 Auralis está analisando com agentes especialistas...")
        self.ask_button.setEnabled(False)
        
        # Iniciar worker para gerar resposta
        self.response_worker = ResponseWorker(question_text)
        self.response_worker.response_generated.connect(self.on_response_generated)
        self.response_worker.error_occurred.connect(self.on_response_error)
        self.response_worker.start()
        
    def on_response_generated(self, response: str, stats: dict):
        """Callback quando resposta é gerada pelos agentes"""
        logger.info(f"Resposta gerada por agentes: {response[:100]}...")
        
        # Adicionar resposta da Auralis com informações dos agentes
        self.add_message("Auralis", response, is_user=False)
        
        # Mostrar informações sobre quais agentes foram usados
        if stats and 'agentes' in stats:
            agentes_info = []
            for nome, info in stats['agentes'].items():
                if info['interacoes_total'] > 0:
                    agentes_info.append(nome)
            
            if agentes_info:
                agentes_text = " | ".join(agentes_info)
                self.add_system_message(f"🧠 Processado por: {agentes_text}")
        
        # Atualizar estatísticas da sessão
        if stats and 'conversacao' in stats and stats['conversacao']:
            total_msgs = stats['conversacao'].get('total_mensagens', 0)
            self.session_info.setText(f"💬 Sessão ativa: {total_msgs} mensagens")
        
        # Restaurar estado normal
        self.status_label.setText("Faça sua próxima pergunta ou volte ao menu")
        self.ask_button.setEnabled(True)
        
    def on_response_error(self, error_message: str):
        """Callback quando ocorre erro na geração de resposta"""
        logger.error(f"Erro na geração de resposta: {error_message}")
        
        # Adicionar mensagem de erro
        self.add_message("Auralis", f"Desculpe, não consegui processar sua pergunta: {error_message}", is_user=False)
        
        # Restaurar estado normal
        self.status_label.setText("Tente fazer outra pergunta")
        self.ask_button.setEnabled(True)
        
    def add_message(self, sender, message, is_user=True):
        """Adiciona uma mensagem ao chat"""
        from PyQt6.QtCore import QDateTime
        
        timestamp = QDateTime.currentDateTime().toString("hh:mm")
        
        if is_user:
            formatted_message = f"<div style='margin-bottom: 10px;'><b style='color: #2563eb;'>[{timestamp}] Você:</b><br>{message}</div>"
        else:
            formatted_message = f"<div style='margin-bottom: 10px;'><b style='color: #059669;'>[{timestamp}] Auralis:</b><br>{message}</div>"
        
        # Adicionar ao histórico
        self.chat_history.append({
            'sender': sender,
            'message': message,
            'timestamp': timestamp,
            'is_user': is_user
        })
        
        # Atualizar area de chat
        current_html = self.chat_area.toHtml()
        if "<html>" not in current_html:
            new_html = formatted_message
        else:
            new_html = current_html.replace("</body></html>", formatted_message + "</body></html>")
        
        self.chat_area.setHtml(new_html)
        
        # Scroll para o final
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_system_message(self, message):
        """Adiciona mensagem do sistema (informações sobre agentes)"""
        from PyQt6.QtCore import QDateTime
        
        timestamp = QDateTime.currentDateTime().toString("hh:mm")
        formatted_message = f"<div style='margin-bottom: 5px; font-size: 11px; color: #666;'><i>[{timestamp}] {message}</i></div>"
        
        # Atualizar area de chat
        current_html = self.chat_area.toHtml()
        if "<html>" not in current_html:
            new_html = formatted_message
        else:
            new_html = current_html.replace("</body></html>", formatted_message + "</body></html>")
        
        self.chat_area.setHtml(new_html)
        
        # Scroll para o final
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def handle_back(self):
        """Confirma se deve voltar e limpar conversa"""
        from PyQt6.QtWidgets import QMessageBox
        
        if self.chat_history:
            reply = QMessageBox.question(
                self,
                "Finalizar Conversa",
                "Deseja finalizar a conversa com Auralis?\nO histórico será salvo no banco de dados.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Finalizar sessão antes de voltar
                if self.session_id:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(ai_manager_novo.finalizar_conversa_atual())
                        loop.close()
                        logger.info("Sessão finalizada ao sair")
                    except Exception as e:
                        logger.error(f"Erro ao finalizar sessão: {e}")
                
                self.clear_chat()
                self.back_to_home.emit()
        else:
            self.back_to_home.emit()
            
    def clear_chat(self):
        """Limpa o chat e histórico"""
        self.chat_history.clear()
        self.chat_area.clear()
        self.session_id = None
        self.status_label.setText("Clique em 'Perguntar' para fazer uma pergunta por áudio")
        self.session_info.setText("💬 Nova sessão será criada ao fazer primeira pergunta")
        
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        if not self.chat_history:
            # Verificar se IA está disponível
            if ai_manager_novo.openai_client:
                welcome_message = "Olá! Sou a Auralis com sistema de agentes especialistas. Posso ajudar com análise de reuniões e consulta na base de conhecimento. Como posso ajudá-lo hoje?"
            else:
                welcome_message = "Olá! Sou a Auralis, mas no momento o sistema de IA não está configurado. Verifique as configurações da OpenAI."
                
            self.add_message("Auralis", welcome_message, is_user=False)
            self.add_system_message("🤖 Sistema de agentes especialistas ativo")
            
    def closeEvent(self, event):
        """Cleanup ao fechar janela"""
        try:
            if self.response_worker and self.response_worker.isRunning():
                self.response_worker.wait(2000)
            
            # Finalizar sessão se existir
            if self.session_id:
                asyncio.create_task(ai_manager_novo.finalizar_conversa_atual())
                
        except Exception as e:
            logger.error(f"Erro no cleanup do chat: {e}")
            
        super().closeEvent(event) 