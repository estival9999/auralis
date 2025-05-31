"""
Janela de Pré-Gravação do Sistema AURALIS
Configuração antes de iniciar gravação de reunião
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QSpacerItem, QSizePolicy, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt
from datetime import datetime
from loguru import logger
import sys
sys.path.append('../..')
from src.core.auth_manager import auth_manager

class PreRecordingWindow(QWidget):
    """Janela de configuração pré-gravação"""
    confirm_clicked = pyqtSignal(dict)  # Emite dados da reunião
    cancel_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Inicializa interface da janela"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header com botão voltar
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Voltar")
        self.back_button.clicked.connect(self.cancel_clicked.emit)
        header_layout.addWidget(self.back_button)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Título
        title = QLabel("Nova Reunião")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Configure os dados da reunião")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Campos automáticos (somente leitura)
        
        # Usuário
        user_label = QLabel("Usuário:")
        layout.addWidget(user_label)
        
        self.user_field = QLineEdit()
        self.user_field.setReadOnly(True)
        self.user_field.setStyleSheet("background-color: #f3f4f6;")
        layout.addWidget(self.user_field)
        
        # Área
        area_label = QLabel("Área:")
        layout.addWidget(area_label)
        
        self.area_field = QLineEdit()
        self.area_field.setReadOnly(True)
        self.area_field.setStyleSheet("background-color: #f3f4f6;")
        layout.addWidget(self.area_field)
        
        # Data/Hora
        datetime_label = QLabel("Data/Hora:")
        layout.addWidget(datetime_label)
        
        self.datetime_field = QLineEdit()
        self.datetime_field.setReadOnly(True)
        self.datetime_field.setStyleSheet("background-color: #f3f4f6;")
        layout.addWidget(self.datetime_field)
        
        # Campo manual - Título
        title_label = QLabel("Título da Reunião:*")
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ex: Alinhamento de projeto X")
        self.title_input.returnPressed.connect(self.handle_confirm)
        layout.addWidget(self.title_input)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setProperty("class", "secondary")
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        buttons_layout.addWidget(self.cancel_button)
        
        buttons_layout.addStretch()
        
        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.setStyleSheet("background-color: #059669; font-weight: bold;")
        self.confirm_button.clicked.connect(self.handle_confirm)
        buttons_layout.addWidget(self.confirm_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        # Atualizar campos automáticos
        user = auth_manager.get_current_user()
        
        if user:
            self.user_field.setText(user.get('nome_completo', user.get('username', '')))
            self.area_field.setText(user.get('area', 'Não especificada'))
        else:
            self.user_field.setText("Usuário não identificado")
            self.area_field.setText("N/A")
        
        # Atualizar data/hora
        now = datetime.now()
        self.datetime_field.setText(now.strftime("%d/%m/%Y - %H:%M"))
        
        # Limpar e focar no título
        self.title_input.clear()
        self.title_input.setFocus()
    
    def handle_confirm(self):
        """Processa confirmação da reunião"""
        titulo = self.title_input.text().strip()
        
        # Validar título
        if not titulo:
            QMessageBox.warning(
                self,
                "Atenção",
                "Por favor, informe o título da reunião."
            )
            self.title_input.setFocus()
            return
        
        # Coletar dados da reunião
        user = auth_manager.get_current_user()
        if user:
            meeting_data = {
                'titulo': titulo,
                'responsavel': user.get('nome_completo', user.get('username', 'Não identificado')),
                'area': user.get('area', 'Não especificada'),
                'data_reuniao': datetime.now().isoformat(),
                'user_id': user.get('id', ''),
                'participantes': [user.get('nome_completo', user.get('username', ''))]
            }
        else:
            # Se não houver usuário logado, usar valores padrão
            meeting_data = {
                'titulo': titulo,
                'responsavel': 'Não identificado',
                'area': 'Não especificada',
                'data_reuniao': datetime.now().isoformat(),
                'user_id': '',
                'participantes': []
            }
        
        logger.info(f"Iniciando gravação da reunião: {titulo}")
        
        # Emitir sinal com dados
        self.confirm_clicked.emit(meeting_data)