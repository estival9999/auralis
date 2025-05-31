"""
Janela Principal (Menu) do Sistema AURALIS
Hub central de navegação
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from loguru import logger
import sys
sys.path.append('../..')
from src.core.auth_manager import auth_manager
from src.database.supabase_client import supabase_client

class HomeWindow(QWidget):
    """Janela principal com menu de opções"""
    historico_clicked = pyqtSignal()
    iniciar_clicked = pyqtSignal()
    auralis_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Inicializa interface da janela"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header com informações do usuário
        self.create_user_header(layout)
        
        # Título
        title = QLabel("Menu Principal")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("O que deseja fazer?")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Container para botões principais
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        
        # Botão Histórico
        self.history_button = QPushButton("📜 Histórico")
        self.history_button.setStyleSheet("font-size: 14px; padding: 15px;")
        self.history_button.clicked.connect(self.historico_clicked.emit)
        buttons_layout.addWidget(self.history_button)
        
        # Botão Iniciar Gravação
        self.start_button = QPushButton("🔴 Iniciar")
        self.start_button.setStyleSheet("""
            font-size: 14px; 
            padding: 15px; 
            background-color: #059669;
            font-weight: bold;
        """)
        self.start_button.clicked.connect(self.iniciar_clicked.emit)
        buttons_layout.addWidget(self.start_button)
        
        # Botão Auralis
        self.auralis_button = QPushButton("🤖 Auralis")
        self.auralis_button.setStyleSheet("""
            font-size: 14px; 
            padding: 15px;
            background-color: #2563eb;
        """)
        self.auralis_button.clicked.connect(self.auralis_clicked.emit)
        buttons_layout.addWidget(self.auralis_button)
        
        layout.addWidget(buttons_container)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botão Sair (menor)
        self.logout_button = QPushButton("Sair")
        self.logout_button.setProperty("class", "secondary")
        self.logout_button.clicked.connect(self.handle_logout)
        self.logout_button.setMaximumWidth(100)
        
        # Container para centralizar botão logout
        logout_container = QWidget()
        logout_layout = QHBoxLayout(logout_container)
        logout_layout.addStretch()
        logout_layout.addWidget(self.logout_button)
        logout_layout.addStretch()
        
        layout.addWidget(logout_container)
        
        self.setLayout(layout)
    
    def create_user_header(self, layout):
        """Cria header com informações do usuário"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Informações do usuário
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)
        
        self.welcome_label = QLabel("Bem-vindo!")
        self.welcome_label.setStyleSheet("color: #059669; font-weight: 600; font-size: 14px;")
        user_info_layout.addWidget(self.welcome_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet("color: #64748b; font-size: 11px;")
        user_info_layout.addWidget(self.user_info_label)
        
        # Status de conexão
        self.connection_status = QLabel("● Conectado")
        self.connection_status.setStyleSheet("color: #059669; font-size: 11px;")
        
        header_layout.addLayout(user_info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.connection_status)
        
        layout.addWidget(header_widget)
    
    def handle_logout(self):
        """Processa logout do usuário"""
        try:
            auth_manager.logout()
            logger.info("Usuário fez logout")
            self.logout_clicked.emit()
        except Exception as e:
            logger.error(f"Erro durante logout: {e}")
    
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        self.update_user_info()
        self.check_connection_status()
    
    def update_user_info(self):
        """Atualiza informações do usuário logado"""
        user = auth_manager.get_current_user()
        if user:
            nome = user.get('nome_completo', user.get('username', 'Usuário'))
            cargo = user.get('cargo', '')
            area = user.get('area', '')
            
            self.welcome_label.setText(f"Bem-vindo, {nome}!")
            
            info_parts = []
            if cargo:
                info_parts.append(cargo)
            if area:
                info_parts.append(area)
            
            if info_parts:
                self.user_info_label.setText(" | ".join(info_parts))
            else:
                self.user_info_label.setText("")
    
    def check_connection_status(self):
        """Verifica status de conexão com Supabase"""
        try:
            # Verificar se cliente está configurado
            if supabase_client.client:
                self.connection_status.setText("● Conectado")
                self.connection_status.setStyleSheet("color: #059669; font-size: 11px;")
            else:
                self.connection_status.setText("● Offline")
                self.connection_status.setStyleSheet("color: #dc2626; font-size: 11px;")
        except:
            self.connection_status.setText("● Offline")
            self.connection_status.setStyleSheet("color: #dc2626; font-size: 11px;")