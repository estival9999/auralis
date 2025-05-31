#!/usr/bin/env python3
"""
Sistema AURALIS - Aplicação Principal
Sistema Inteligente de Reuniões e Gestão do Conhecimento
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from loguru import logger

# Adicionar diretórios ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar configurações e gerenciadores
from shared.config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, LOG_LEVEL, LOG_FORMAT
from src.core.style_manager import StyleManager
from src.core.auth_manager import auth_manager

# Configurar logging
logger.remove()
logger.add(sys.stderr, format=LOG_FORMAT, level=LOG_LEVEL)
logger.add("logs/auralis.log", rotation="1 day", retention="7 days", format=LOG_FORMAT, level=LOG_LEVEL)

# Importar janelas
from src.windows.login_window import LoginWindow
from src.windows.home_window import HomeWindow
from src.windows.history_window import HistoryWindow
from src.windows.pre_recording_window import PreRecordingWindow
from src.windows.recording_window import RecordingWindow
from src.windows.auralis_chat_window import AuralisChatWindow
from src.windows.auralis_listening_window import AuralisListeningWindow

class MainWindow(QMainWindow):
    """Janela principal do sistema AURALIS"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setFixedSize(QSize(WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Widget central com stack de janelas
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Criar janelas
        self.create_windows()
        
        # Conectar sinais
        self.connect_signals()
        
        # Iniciar na janela de login
        self.stacked_widget.setCurrentIndex(0)
        
        # Centralizar janela na tela
        self.center_window()
        
        logger.info(f"{APP_NAME} iniciado com sucesso")
    
    def create_windows(self):
        """Cria todas as janelas do sistema"""
        # Janela 0: Login
        self.login_window = LoginWindow()
        self.stacked_widget.addWidget(self.login_window)
        
        # Janela 1: Menu Principal
        self.home_window = HomeWindow()
        self.stacked_widget.addWidget(self.home_window)
        
        # Janela 2: Histórico
        self.history_window = HistoryWindow()
        self.stacked_widget.addWidget(self.history_window)
        
        # Janela 3: Pré-gravação
        self.pre_recording_window = PreRecordingWindow()
        self.stacked_widget.addWidget(self.pre_recording_window)
        
        # Janela 4: Gravação
        self.recording_window = RecordingWindow()
        self.stacked_widget.addWidget(self.recording_window)
        
        # Janela 5: Chat Auralis
        self.auralis_chat_window = AuralisChatWindow()
        self.stacked_widget.addWidget(self.auralis_chat_window)
        
        # Janela 6: Escuta Auralis
        self.auralis_listening_window = AuralisListeningWindow()
        self.stacked_widget.addWidget(self.auralis_listening_window)
    
    def connect_signals(self):
        """Conecta sinais entre janelas"""
        # Login
        self.login_window.login_success.connect(lambda: self.show_window(1))
        
        # Home
        self.home_window.historico_clicked.connect(lambda: self.show_window(2))
        self.home_window.iniciar_clicked.connect(lambda: self.show_window(3))
        self.home_window.auralis_clicked.connect(lambda: self.show_window(5))
        self.home_window.logout_clicked.connect(lambda: self.show_window(0))  # Voltar para login ao fazer logout
        
        # Histórico
        self.history_window.back_clicked.connect(lambda: self.show_window(1))
        
        # Pré-gravação
        self.pre_recording_window.confirm_clicked.connect(self.start_recording)
        self.pre_recording_window.cancel_clicked.connect(lambda: self.show_window(1))
        
        # Gravação
        self.recording_window.recording_finished.connect(self.on_recording_finished)
        self.recording_window.recording_cancelled.connect(lambda: self.show_window(1))
        
        # Chat Auralis
        self.auralis_chat_window.back_clicked.connect(lambda: self.show_window(1))
        self.auralis_chat_window.ask_clicked.connect(lambda: self.show_window(6))
        
        # Escuta Auralis
        self.auralis_listening_window.recording_finished.connect(self.on_auralis_question_recorded)
        self.auralis_listening_window.cancel_clicked.connect(lambda: self.show_window(5))
    
    def show_window(self, index: int):
        """Mostra janela específica"""
        self.stacked_widget.setCurrentIndex(index)
        
        # Chamar método on_window_show se existir
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'on_window_show'):
            current_widget.on_window_show()
        
        logger.debug(f"Janela {index} exibida")
    
    def start_recording(self, meeting_data: dict):
        """Inicia gravação com dados da reunião"""
        self.recording_window.set_meeting_data(meeting_data)
        self.show_window(4)
        self.recording_window.start_recording()
    
    def on_recording_finished(self, file_path: str):
        """Processa fim da gravação"""
        logger.info(f"Gravação finalizada: {file_path}")
        self.show_window(1)
        
        # Aqui você adicionaria o processamento da transcrição
        # e salvamento no banco de dados
        QMessageBox.information(
            self,
            "Gravação Concluída",
            "Reunião gravada com sucesso!\nA transcrição será processada em breve."
        )
    
    def on_auralis_question_recorded(self, file_path: str):
        """Processa pergunta gravada para Auralis"""
        logger.info(f"Pergunta gravada: {file_path}")
        
        # Voltar para chat e processar pergunta
        self.show_window(5)
        self.auralis_chat_window.process_audio_question(file_path)
    
    def center_window(self):
        """Centraliza janela na tela"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        # Fazer logout se necessário
        if auth_manager.is_authenticated():
            auth_manager.logout()
        
        logger.info(f"{APP_NAME} encerrado")
        event.accept()

def main():
    """Função principal"""
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Criar aplicação
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Aplicar tema
    StyleManager.apply_theme(app)
    
    # Criar e mostrar janela principal
    window = MainWindow()
    window.show()
    
    # Executar aplicação
    sys.exit(app.exec())

if __name__ == "__main__":
    main()