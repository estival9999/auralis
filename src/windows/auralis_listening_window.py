"""
Janela de Escuta do Auralis do Sistema AURALIS
Interface para gravação de perguntas por voz
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QSpacerItem, QSizePolicy, QProgressBar)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from datetime import datetime
from loguru import logger
import sys
sys.path.append('../..')
from src.audio.audio_recorder import AudioRecorder

class AuralisListeningWindow(QWidget):
    """Janela para gravação de perguntas por voz"""
    recording_finished = pyqtSignal(str)  # Emite caminho do arquivo
    cancel_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder()
        self.is_recording = False
        self.start_time = None
        self.init_ui()
        
    def init_ui(self):
        """Inicializa interface da janela"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Voltar")
        self.back_button.clicked.connect(self.handle_cancel)
        header_layout.addWidget(self.back_button)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Título
        title = QLabel("Pergunte ao Auralis")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Pressione o botão e faça sua pergunta")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Animação do microfone
        self.mic_animation = QLabel("🎤")
        self.mic_animation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mic_animation.setStyleSheet("""
            font-size: 72px;
            color: #64748b;
        """)
        layout.addWidget(self.mic_animation)
        
        # Status
        self.status_label = QLabel("Pronto para gravar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #64748b; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # Timer
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            font-size: 24px;
            font-family: monospace;
            color: #1e293b;
        """)
        self.timer_label.hide()
        layout.addWidget(self.timer_label)
        
        # Indicador de volume
        self.volume_bar = QProgressBar()
        self.volume_bar.setMaximum(100)
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setMaximumHeight(10)
        self.volume_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                background-color: #f3f4f6;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 4px;
            }
        """)
        self.volume_bar.hide()
        layout.addWidget(self.volume_bar)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botão principal
        self.record_button = QPushButton("🎤 Iniciar Gravação")
        self.record_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 15px 30px;
                background-color: #2563eb;
                color: white;
                border-radius: 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.record_button.clicked.connect(self.toggle_recording)
        
        # Container para centralizar botão
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(self.record_button)
        button_layout.addStretch()
        
        layout.addWidget(button_container)
        
        # Dica
        tip_label = QLabel("💡 Dica: Fale claramente e evite ruídos de fundo")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 10px;")
        layout.addWidget(tip_label)
        
        self.setLayout(layout)
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_animation)
        self.pulse_state = 0
        
        # Configurar callback de volume
        self.recorder.set_volume_callback(self.update_volume)
    
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        self.reset_ui()
    
    def toggle_recording(self):
        """Alterna entre iniciar e parar gravação"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Inicia gravação"""
        success = self.recorder.start_recording("pergunta_auralis")
        
        if success:
            self.is_recording = True
            self.start_time = datetime.now()
            
            # Atualizar UI
            self.record_button.setText("⏹ Parar Gravação")
            self.record_button.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    padding: 15px 30px;
                    background-color: #dc2626;
                    color: white;
                    border-radius: 25px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #b91c1c;
                }
            """)
            
            self.status_label.setText("Gravando... Fale sua pergunta")
            self.status_label.setStyleSheet("color: #dc2626; font-size: 14px; font-weight: bold;")
            
            self.timer_label.show()
            self.volume_bar.show()
            
            # Iniciar timers
            self.update_timer.start(100)
            self.pulse_timer.start(500)
            
            logger.info("Gravação de pergunta iniciada")
        else:
            self.status_label.setText("Erro ao acessar microfone")
            self.status_label.setStyleSheet("color: #dc2626; font-size: 14px;")
    
    def stop_recording(self):
        """Para gravação e emite sinal"""
        self.update_timer.stop()
        self.pulse_timer.stop()
        
        file_path = self.recorder.stop_recording()
        
        if file_path:
            logger.info(f"Pergunta gravada: {file_path}")
            self.recording_finished.emit(file_path)
        else:
            self.status_label.setText("Erro ao salvar gravação")
            self.status_label.setStyleSheet("color: #dc2626; font-size: 14px;")
            
            # Reset UI após erro
            QTimer.singleShot(2000, self.reset_ui)
    
    def handle_cancel(self):
        """Cancela gravação se estiver em andamento"""
        if self.is_recording:
            self.recorder.cancel_recording()
            self.update_timer.stop()
            self.pulse_timer.stop()
        
        self.cancel_clicked.emit()
    
    def update_display(self):
        """Atualiza timer"""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            minutes = elapsed.seconds // 60
            seconds = elapsed.seconds % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
    
    def update_volume(self, volume):
        """Atualiza indicador de volume"""
        self.volume_bar.setValue(volume)
    
    def pulse_animation(self):
        """Animação pulsante do microfone"""
        colors = ["#dc2626", "#ef4444", "#f87171", "#ef4444"]
        self.mic_animation.setStyleSheet(f"""
            font-size: 72px;
            color: {colors[self.pulse_state]};
        """)
        self.pulse_state = (self.pulse_state + 1) % len(colors)
    
    def reset_ui(self):
        """Reseta interface para estado inicial"""
        self.is_recording = False
        self.start_time = None
        
        # Resetar botão
        self.record_button.setText("🎤 Iniciar Gravação")
        self.record_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 15px 30px;
                background-color: #2563eb;
                color: white;
                border-radius: 25px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        
        # Resetar labels
        self.status_label.setText("Pronto para gravar")
        self.status_label.setStyleSheet("color: #64748b; font-size: 14px;")
        
        self.mic_animation.setStyleSheet("font-size: 72px; color: #64748b;")
        
        self.timer_label.setText("00:00")
        self.timer_label.hide()
        
        self.volume_bar.setValue(0)
        self.volume_bar.hide()
        
        # Parar timers
        self.update_timer.stop()
        self.pulse_timer.stop()