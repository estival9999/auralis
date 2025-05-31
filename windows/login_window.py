from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot
from PyQt6.QtGui import QFont
from src.core.style_manager import StyleManager
from src.core.auth_manager import auth_manager
from loguru import logger
import asyncio

class LoginWorker(QThread):
    """Worker thread para operações de login assíncronas"""
    login_result = pyqtSignal(dict)
    
    def __init__(self, username: str, password: str):
        super().__init__()
        self.username = username
        self.password = password
    
    def run(self):
        """Executa login em thread separada"""
        try:
            # Criar loop de eventos para operações async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Executar login assíncrono
            result = loop.run_until_complete(auth_manager.login(self.username, self.password))
            self.login_result.emit(result)
            
            loop.close()
        except Exception as e:
            logger.error(f"Erro no worker de login: {e}")
            self.login_result.emit({
                "success": False,
                "message": f"Erro interno: {str(e)}"
            })

class LoginWindow(QWidget):
    login_success = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.login_worker = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Sistema de Reuniões")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo com informações dos usuários de teste
        subtitle = QLabel("Usuários de teste: admin, joao.silva, maria.santos, pedro.costa\nSenha para todos: admin123")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #64748b; font-size: 10px; line-height: 1.4;")
        layout.addWidget(subtitle)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Campo Usuário
        user_label = QLabel("Usuário:")
        layout.addWidget(user_label)
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Digite seu usuário (ex: admin)")
        layout.addWidget(self.user_input)
        
        # Campo Senha
        password_label = QLabel("Senha:")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Digite sua senha (admin123)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botão Login
        self.login_button = QPushButton("Confirmar e Logar")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)
        
        # Label para mensagens de erro/status
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "subtitle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Conectar Enter para fazer login
        self.user_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
    def handle_login(self):
        """Processa o login do usuário usando autenticação real"""
        username = self.user_input.text().strip()
        password = self.password_input.text().strip()
        
        # Validação básica
        if not username or not password:
            self.show_error("Por favor, preencha todos os campos")
            return
        
        # Verificar se já há um login em progresso
        if self.login_worker and self.login_worker.isRunning():
            return
        
        # Mostrar status de carregamento
        self.show_status("Autenticando...", "info")
        self.login_button.setEnabled(False)
        
        # Executar login em worker thread
        self.login_worker = LoginWorker(username, password)
        self.login_worker.login_result.connect(self.on_login_result)
        self.login_worker.start()
        
        logger.info(f"Tentativa de login para usuário: {username}")
    
    @pyqtSlot(dict)
    def on_login_result(self, result):
        """Processa resultado do login"""
        self.login_button.setEnabled(True)
        
        if result["success"]:
            logger.info(f"Login bem-sucedido: {result.get('user', {}).get('username')}")
            self.show_status("Login realizado com sucesso!", "success")
            
            # Aguardar um momento antes de navegar
            QThread.msleep(500)
            self.clear_status()
            self.clear_fields()
            self.login_success.emit()
        else:
            logger.warning(f"Falha no login: {result['message']}")
            self.show_error(result["message"])
            
    def show_error(self, message):
        """Exibe mensagem de erro"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #dc2626; font-weight: 500;")
        self.status_label.show()
        
    def show_status(self, message, status_type="info"):
        """Exibe mensagem de status"""
        colors = {
            "info": "#2563eb",
            "success": "#059669",
            "error": "#dc2626"
        }
        
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {colors.get(status_type, '#64748b')}; font-weight: 500;")
        self.status_label.show()
        
    def clear_status(self):
        """Limpa mensagem de status"""
        self.status_label.hide()
        
    def clear_fields(self):
        """Limpa os campos de entrada"""
        self.user_input.clear()
        self.password_input.clear()
        
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        self.clear_status()
        self.user_input.setFocus()
        
        # Pré-preencher com admin para facilitar testes
        if not self.user_input.text():
            self.user_input.setText("admin")
            self.password_input.setText("admin123") 