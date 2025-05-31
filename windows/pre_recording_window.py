from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QFont
from src.core.style_manager import StyleManager

class PreRecordingWindow(QWidget):
    start_recording = pyqtSignal()
    back_to_home = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Nova Gravação")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Preencha as informações:")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Campo Usuário (somente leitura)
        user_label = QLabel("Usuário:")
        layout.addWidget(user_label)
        
        self.user_display = QLineEdit()
        self.user_display.setText("Demo User")  # Usuário fixo para demo
        self.user_display.setReadOnly(True)
        layout.addWidget(self.user_display)
        
        # Campo Data (somente leitura)
        date_label = QLabel("Data:")
        layout.addWidget(date_label)
        
        self.date_display = QLineEdit()
        self.date_display.setReadOnly(True)
        layout.addWidget(self.date_display)
        
        # Campo Título (editável)
        title_label = QLabel("Título da Reunião:")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ex: Alinhamento de projeto, Revisão semanal...")
        layout.addWidget(self.title_input)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancelar")
        StyleManager.apply_button_style(self.cancel_button, "secondary")
        self.cancel_button.clicked.connect(self.back_to_home.emit)
        buttons_layout.addWidget(self.cancel_button)
        
        self.confirm_button = QPushButton("Confirmar")
        StyleManager.apply_button_style(self.confirm_button, "success")
        self.confirm_button.clicked.connect(self.handle_confirm)
        buttons_layout.addWidget(self.confirm_button)
        
        layout.addLayout(buttons_layout)
        
        # Label para mensagens de erro
        self.error_label = QLabel("")
        self.error_label.setProperty("class", "subtitle")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        self.setLayout(layout)
        
        # Conectar Enter para confirmar
        self.title_input.returnPressed.connect(self.handle_confirm)
        
    def handle_confirm(self):
        """Processa a confirmação dos dados"""
        title = self.title_input.text().strip()
        
        if not title:
            self.show_error("Por favor, digite um título para a reunião")
            return
            
        if len(title) < 3:
            self.show_error("O título deve ter pelo menos 3 caracteres")
            return
            
        # Salvar dados temporariamente (para demo)
        self.meeting_data = {
            'user': self.user_display.text(),
            'date': self.date_display.text(),
            'title': title
        }
        
        self.clear_error()
        self.start_recording.emit()
        
    def show_error(self, message):
        """Exibe mensagem de erro"""
        self.error_label.setText(message)
        self.error_label.setStyleSheet("color: #dc2626;")
        self.error_label.show()
        
    def clear_error(self):
        """Limpa mensagem de erro"""
        self.error_label.hide()
        
    def update_datetime(self):
        """Atualiza data e hora atual"""
        current_datetime = QDateTime.currentDateTime()
        formatted_date = current_datetime.toString("dd/MM/yyyy - hh:mm")
        self.date_display.setText(formatted_date)
        
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        self.update_datetime()
        self.title_input.clear()
        self.clear_error()
        self.title_input.setFocus() 