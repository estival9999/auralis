from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from src.core.style_manager import StyleManager
from src.core.auth_manager import auth_manager
from loguru import logger

class HomeWindow(QWidget):
    navigate_to_history = pyqtSignal()
    navigate_to_pre_recording = pyqtSignal()
    navigate_to_auralis = pyqtSignal()
    logout_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header com informações do usuário
        self.create_user_header(layout)
        
        # Título de boas-vindas
        title = QLabel("Menu Principal")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Escolha uma opção:")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaçador superior
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botão Histórico
        self.history_button = QPushButton("📜 Histórico")
        self.history_button.clicked.connect(self.navigate_to_history.emit)
        layout.addWidget(self.history_button)
        
        # Botão Iniciar (corrigido para navigate_to_pre_recording)
        self.start_button = QPushButton("🔴 Iniciar")
        StyleManager.apply_button_style(self.start_button, "success")
        self.start_button.clicked.connect(self.navigate_to_pre_recording.emit)
        layout.addWidget(self.start_button)
        
        # Botão Auralis
        self.auralis_button = QPushButton("🤖 Auralis")
        StyleManager.apply_button_style(self.auralis_button, "secondary")
        self.auralis_button.clicked.connect(self.navigate_to_auralis.emit)
        layout.addWidget(self.auralis_button)
        
        # Espaçador inferior
        layout.addItem(QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botão Logout
        self.logout_button = QPushButton("🚪 Logout")
        StyleManager.apply_button_style(self.logout_button, "danger")
        self.logout_button.clicked.connect(self.handle_logout)
        layout.addWidget(self.logout_button)
        
        self.setLayout(layout)
    
    def create_user_header(self, layout):
        """Cria header com informações do usuário"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Label de boas-vindas
        self.welcome_label = QLabel("Bem-vindo!")
        self.welcome_label.setStyleSheet("color: #059669; font-weight: 600; font-size: 14px;")
        
        # Status de conexão
        self.connection_status = QLabel("🔌 Offline")
        self.connection_status.setStyleSheet("color: #dc2626; font-size: 12px;")
        
        header_layout.addWidget(self.welcome_label)
        header_layout.addStretch()
        header_layout.addWidget(self.connection_status)
        
        layout.addWidget(header_widget)
    
    def handle_logout(self):
        """Processa logout do usuário"""
        try:
            auth_manager.logout()
            logger.info("Usuário fez logout")
            self.logout_requested.emit()
        except Exception as e:
            logger.error(f"Erro durante logout: {e}")
    
    def on_window_show(self):
        """Chamado quando a janela é mostrada - atualiza informações do usuário"""
        self.update_user_info()
        self.check_connection_status()
    
    def update_user_info(self):
        """Atualiza informações do usuário logado"""
        try:
            current_user = auth_manager.get_current_user()
            if current_user:
                username = current_user.get('username', 'Usuário')
                email = current_user.get('email', '')
                
                welcome_text = f"Bem-vindo, {username}!"
                if email:
                    welcome_text += f"\n{email}"
                
                self.welcome_label.setText(welcome_text)
                logger.info(f"Interface atualizada para usuário: {username}")
            else:
                self.welcome_label.setText("Bem-vindo!")
                logger.warning("Nenhum usuário autenticado encontrado")
        except Exception as e:
            logger.error(f"Erro ao atualizar informações do usuário: {e}")
            self.welcome_label.setText("Bem-vindo!")
    
    def check_connection_status(self):
        """Verifica e atualiza status da conexão"""
        try:
            if auth_manager.supabase and auth_manager.is_authenticated():
                self.connection_status.setText("🟢 Online")
                self.connection_status.setStyleSheet("color: #059669; font-size: 12px;")
            else:
                self.connection_status.setText("🔴 Offline")
                self.connection_status.setStyleSheet("color: #dc2626; font-size: 12px;")
        except Exception as e:
            logger.error(f"Erro ao verificar status de conexão: {e}")
            self.connection_status.setText("⚠️ Erro")
            self.connection_status.setStyleSheet("color: #d97706; font-size: 12px;") 