"""
Janela de Chat com Auralis do Sistema AURALIS
Interface de conversação com assistente IA
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QTextEdit, QLineEdit, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot, QTimer
from PyQt6.QtGui import QTextCursor
from datetime import datetime
from pathlib import Path
from loguru import logger
import asyncio
import json
import sys
sys.path.append('../..')
from backend.agents.agente_orquestrador import agente_orquestrador
from backend.agents.agente_brainstorm import agente_brainstorm
from backend.agents.agente_consulta_inteligente import agente_consulta_inteligente
from src.core.auth_manager import auth_manager
from src.audio.transcriber import audio_transcriber
from shared.config import AURALIS_MEMORIA_DIR

class AuralisWorker(QThread):
    """Worker thread para processar perguntas"""
    response_ready = pyqtSignal(dict)
    
    def __init__(self, pergunta: str, contexto: dict):
        super().__init__()
        self.pergunta = pergunta
        self.contexto = contexto
    
    def run(self):
        """Processa pergunta em thread separada"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Processar com orquestrador
            resultado = loop.run_until_complete(
                agente_orquestrador.processar_pergunta(self.pergunta, self.contexto)
            )
            
            # Se necessário, executar agente específico
            if resultado.get('agente') and resultado['agente'] != 'orquestrador':
                resultado = loop.run_until_complete(
                    self._executar_agente(resultado)
                )
            
            self.response_ready.emit(resultado)
            loop.close()
            
        except Exception as e:
            logger.error(f"Erro ao processar pergunta: {e}")
            self.response_ready.emit({
                'sucesso': False,
                'erro': str(e),
                'mensagem': 'Desculpe, ocorreu um erro ao processar sua pergunta.'
            })
    
    async def _executar_agente(self, comando: dict) -> dict:
        """Executa agente específico baseado no comando"""
        agente = comando.get('agente')
        acao = comando.get('acao')
        parametros = comando.get('parametros', {})
        
        try:
            if agente == 'brainstorm':
                resultado = await agente_brainstorm.gerar_ideias(parametros)
                return self._formatar_resposta_brainstorm(resultado)
            
            elif agente == 'consulta_inteligente':
                if acao == 'buscar_reunioes':
                    resultado = await agente_consulta_inteligente.buscar_reunioes(parametros)
                elif acao == 'buscar_conhecimento':
                    resultado = await agente_consulta_inteligente.buscar_conhecimento(parametros)
                elif acao == 'analisar_equipe':
                    resultado = await agente_consulta_inteligente.analisar_equipe(parametros)
                else:
                    resultado = {'sucesso': False, 'mensagem': 'Ação não reconhecida'}
                
                return self._formatar_resposta_consulta(resultado, acao)
            
            else:
                return comando
                
        except Exception as e:
            logger.error(f"Erro ao executar agente {agente}: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'mensagem': f'Erro ao executar {agente}'
            }
    
    def _formatar_resposta_brainstorm(self, resultado: dict) -> dict:
        """Formata resposta do agente de brainstorm"""
        if not resultado.get('sucesso'):
            return resultado
        
        resposta = "🧠 **Ideias Geradas:**\n\n"
        
        for i, ideia in enumerate(resultado.get('ideias', []), 1):
            resposta += f"**{i}. {ideia.get('titulo', 'Ideia')}**\n"
            resposta += f"{ideia.get('descricao', '')}\n"
            
            if ideia.get('beneficios'):
                resposta += "\n*Benefícios:*\n"
                for beneficio in ideia['beneficios']:
                    resposta += f"- {beneficio}\n"
            
            resposta += f"\n*Complexidade:* {ideia.get('complexidade', 'N/A')}\n"
            resposta += f"*Prazo estimado:* {ideia.get('prazo_estimado', 'N/A')}\n"
            resposta += "\n---\n\n"
        
        return {
            'sucesso': True,
            'resposta': resposta,
            'tipo_resposta': 'brainstorm'
        }
    
    def _formatar_resposta_consulta(self, resultado: dict, acao: str) -> dict:
        """Formata resposta do agente de consulta"""
        if not resultado.get('sucesso'):
            return resultado
        
        if acao == 'buscar_reunioes':
            if resultado.get('analise'):
                return {
                    'sucesso': True,
                    'resposta': resultado['analise'].get('resposta_completa', ''),
                    'tipo_resposta': 'consulta_reunioes'
                }
            else:
                return {
                    'sucesso': True,
                    'resposta': resultado.get('mensagem', 'Nenhuma reunião encontrada.'),
                    'tipo_resposta': 'consulta_reunioes'
                }
        
        elif acao == 'buscar_conhecimento':
            return {
                'sucesso': True,
                'resposta': resultado.get('resposta', 'Nenhuma informação encontrada.'),
                'tipo_resposta': 'consulta_conhecimento'
            }
        
        elif acao == 'analisar_equipe':
            if resultado.get('analise'):
                return {
                    'sucesso': True,
                    'resposta': resultado['analise'].get('analise_completa', ''),
                    'tipo_resposta': 'analise_equipe'
                }
            else:
                return resultado
        
        return resultado

class AuralisChatWindow(QWidget):
    """Janela de chat com assistente Auralis"""
    back_clicked = pyqtSignal()
    ask_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.messages = []
        self.worker = None
        self.memoria_path = AURALIS_MEMORIA_DIR / f"sessao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.init_ui()
        
    def init_ui(self):
        """Inicializa interface da janela"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Voltar")
        self.back_button.clicked.connect(self.handle_back)
        header_layout.addWidget(self.back_button)
        
        title = QLabel("🤖 Auralis")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title, 1)
        
        # Botão de voz
        self.voice_button = QPushButton("🎤")
        self.voice_button.setMaximumWidth(40)
        self.voice_button.clicked.connect(self.ask_clicked.emit)
        header_layout.addWidget(self.voice_button)
        
        layout.addLayout(header_layout)
        
        # Área de chat (scrollable)
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.chat_area, 1)
        
        # Área de entrada
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Digite sua pergunta...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Indicador de digitação
        self.typing_indicator = QLabel("Auralis está pensando...")
        self.typing_indicator.setStyleSheet("color: #64748b; font-style: italic;")
        self.typing_indicator.hide()
        layout.addWidget(self.typing_indicator)
        
        self.setLayout(layout)
    
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        # Mensagem de boas-vindas
        self.add_message(
            "Auralis",
            "Olá! Sou a Auralis, sua assistente inteligente. Como posso ajudar você hoje?\n\n"
            "Posso:\n"
            "• Buscar informações em reuniões anteriores\n"
            "• Gerar ideias e sugestões criativas\n"
            "• Consultar a base de conhecimento\n"
            "• Analisar dinâmica de equipe\n\n"
            "O que gostaria de saber?",
            is_user=False
        )
        
        self.input_field.setFocus()
    
    def send_message(self):
        """Envia mensagem do usuário"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Adicionar mensagem do usuário
        self.add_message("Você", text, is_user=True)
        
        # Limpar campo
        self.input_field.clear()
        
        # Desabilitar entrada durante processamento
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.typing_indicator.show()
        
        # Preparar contexto
        user = auth_manager.get_current_user()
        contexto = {
            'usuario': user,
            'historico': self.messages[-5:],  # Últimas 5 mensagens
            'timestamp': datetime.now().isoformat()
        }
        
        # Processar em thread separada
        try:
            self.worker = AuralisWorker(text, contexto)
            self.worker.response_ready.connect(self.handle_response)
            self.worker.start()
        except Exception as e:
            logger.error(f"Erro ao criar worker: {e}")
            self.handle_response({
                'sucesso': False,
                'mensagem': 'Erro ao processar pergunta. Verifique as configurações.'
            })
    
    @pyqtSlot(dict)
    def handle_response(self, resultado):
        """Processa resposta da IA"""
        # Reabilitar entrada
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.typing_indicator.hide()
        
        # Adicionar resposta
        if resultado.get('sucesso'):
            resposta = resultado.get('resposta', 'Desculpe, não consegui processar sua pergunta.')
        else:
            resposta = resultado.get('mensagem', 'Ocorreu um erro ao processar sua pergunta.')
        
        self.add_message("Auralis", resposta, is_user=False)
        
        # Focar no campo de entrada
        self.input_field.setFocus()
        
        # Salvar na memória
        self.save_to_memory()
    
    def add_message(self, sender: str, text: str, is_user: bool = True):
        """Adiciona mensagem ao chat"""
        timestamp = datetime.now().strftime("%H:%M")
        
        # Formatar mensagem
        if is_user:
            html = f"""
            <div style="text-align: right; margin: 10px 0;">
                <span style="color: #64748b; font-size: 11px;">{timestamp}</span><br>
                <span style="background-color: #2563eb; color: white; padding: 8px 12px; 
                      border-radius: 12px; display: inline-block; max-width: 70%;">
                    {text}
                </span>
            </div>
            """
        else:
            # Processar markdown básico para Auralis
            formatted_text = text.replace('**', '<b>').replace('**', '</b>')
            formatted_text = formatted_text.replace('*', '<i>').replace('*', '</i>')
            formatted_text = formatted_text.replace('\n', '<br>')
            
            html = f"""
            <div style="text-align: left; margin: 10px 0;">
                <span style="color: #64748b; font-size: 11px;">{sender} - {timestamp}</span><br>
                <span style="background-color: #f3f4f6; color: #1e293b; padding: 8px 12px; 
                      border-radius: 12px; display: inline-block; max-width: 70%;">
                    {formatted_text}
                </span>
            </div>
            """
        
        # Adicionar ao chat
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        
        # Scroll para o final
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )
        
        # Adicionar à lista de mensagens
        self.messages.append({
            'sender': sender,
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'is_user': is_user
        })
    
    def process_audio_question(self, audio_path: str):
        """Processa pergunta gravada em áudio"""
        self.add_message("Sistema", "Transcrevendo áudio...", is_user=False)
        
        # TODO: Implementar transcrição e processamento
        # Por enquanto, simular
        QTimer.singleShot(2000, lambda: self.add_message(
            "Sistema", 
            "Desculpe, a transcrição de áudio ainda está em desenvolvimento.",
            is_user=False
        ))
    
    def handle_back(self):
        """Processa voltar - limpa memória da sessão"""
        # Salvar sessão antes de sair
        self.save_to_memory()
        
        # Limpar contexto do orquestrador
        agente_orquestrador.limpar_contexto()
        
        # Limpar chat
        self.chat_area.clear()
        self.messages = []
        
        self.back_clicked.emit()
    
    def save_to_memory(self):
        """Salva conversa na memória local"""
        try:
            memoria_data = {
                'sessao_id': self.memoria_path.stem,
                'usuario': auth_manager.get_current_user(),
                'inicio': self.messages[0]['timestamp'] if self.messages else None,
                'fim': datetime.now().isoformat(),
                'mensagens': self.messages
            }
            
            with open(self.memoria_path, 'w', encoding='utf-8') as f:
                json.dump(memoria_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"Sessão salva em: {self.memoria_path}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar memória: {e}")