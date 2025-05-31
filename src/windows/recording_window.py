"""
Janela de Gravação do Sistema AURALIS
Interface para gravação de reuniões
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QSpacerItem, QSizePolicy, QMessageBox, QProgressBar)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QPalette
from datetime import datetime, timedelta
from loguru import logger
import sys
sys.path.append('../..')
from src.audio.audio_recorder import AudioRecorder

class RecordingThread(QThread):
    """Thread para gerenciar gravação"""
    volume_update = pyqtSignal(int)
    
    def __init__(self, recorder):
        super().__init__()
        self.recorder = recorder
        self.recorder.set_volume_callback(self.on_volume_update)
    
    def on_volume_update(self, volume):
        """Callback de atualização de volume"""
        self.volume_update.emit(volume)

class RecordingWindow(QWidget):
    """Janela de gravação em andamento"""
    recording_finished = pyqtSignal(str)  # Emite caminho do arquivo
    recording_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder()
        self.recording_thread = None
        self.start_time = None
        self.meeting_data = {}
        self.is_paused = False
        self.init_ui()
        
    def init_ui(self):
        """Inicializa interface da janela"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("Gravação em Andamento")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Informações da reunião
        self.meeting_info = QLabel("")
        self.meeting_info.setProperty("class", "subtitle")
        self.meeting_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meeting_info.setWordWrap(True)
        layout.addWidget(self.meeting_info)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Indicador de gravação
        self.recording_indicator = QLabel("🔴 REC")
        self.recording_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_indicator.setStyleSheet("""
            font-size: 32px;
            color: #dc2626;
            font-weight: bold;
        """)
        layout.addWidget(self.recording_indicator)
        
        # Timer
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            font-family: monospace;
        """)
        layout.addWidget(self.timer_label)
        
        # Indicador de volume
        self.volume_bar = QProgressBar()
        self.volume_bar.setMaximum(100)
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background-color: #f3f4f6;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #059669;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.volume_bar)
        
        volume_label = QLabel("Nível de áudio")
        volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_label.setStyleSheet("font-size: 11px; color: #64748b;")
        layout.addWidget(volume_label)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botões de controle
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Botão Pausar/Retomar
        self.pause_button = QPushButton("⏸ Pausar")
        self.pause_button.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_button)
        
        # Botão Finalizar
        self.stop_button = QPushButton("⏹ Finalizar")
        self.stop_button.setStyleSheet("background-color: #059669; font-weight: bold;")
        self.stop_button.clicked.connect(self.stop_recording)
        controls_layout.addWidget(self.stop_button)
        
        # Botão Cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setProperty("class", "danger")
        self.cancel_button.clicked.connect(self.cancel_recording)
        controls_layout.addWidget(self.cancel_button)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        
        # Timer para atualizar cronômetro
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        # Timer para piscar indicador
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_indicator)
        self.blink_state = True
    
    def set_meeting_data(self, data):
        """Define dados da reunião"""
        self.meeting_data = data
        
        # Atualizar informações na tela
        titulo = data.get('titulo', 'Sem título')
        responsavel = data.get('responsavel', 'Não identificado')
        self.meeting_info.setText(f"{titulo}\n{responsavel}")
    
    def start_recording(self):
        """Inicia a gravação"""
        try:
            # Gerar nome do arquivo baseado no título
            titulo_safe = self.meeting_data.get('titulo', 'reuniao').replace(' ', '_')
            titulo_safe = ''.join(c for c in titulo_safe if c.isalnum() or c in ('_', '-'))
            
            # Iniciar gravação
            success = self.recorder.start_recording(titulo_safe)
            
            if success:
                self.start_time = datetime.now()
                self.is_paused = False
                
                # Criar thread de gravação
                self.recording_thread = RecordingThread(self.recorder)
                self.recording_thread.volume_update.connect(self.update_volume)
                
                # Iniciar timers
                self.update_timer.start(100)  # Atualizar a cada 100ms
                self.blink_timer.start(1000)  # Piscar a cada 1s
                
                logger.info(f"Gravação iniciada para: {self.meeting_data.get('titulo')}")
            else:
                QMessageBox.critical(
                    self,
                    "Erro",
                    "Não foi possível iniciar a gravação.\nVerifique o microfone."
                )
                self.recording_cancelled.emit()
                
        except Exception as e:
            logger.error(f"Erro ao iniciar gravação: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao iniciar gravação: {str(e)}"
            )
            self.recording_cancelled.emit()
    
    def toggle_pause(self):
        """Alterna entre pausar e retomar"""
        if self.is_paused:
            if self.recorder.resume_recording():
                self.is_paused = False
                self.pause_button.setText("⏸ Pausar")
                self.recording_indicator.setText("🔴 REC")
                self.blink_timer.start()
        else:
            if self.recorder.pause_recording():
                self.is_paused = True
                self.pause_button.setText("▶ Retomar")
                self.recording_indicator.setText("⏸ PAUSADO")
                self.recording_indicator.setStyleSheet("""
                    font-size: 32px;
                    color: #d97706;
                    font-weight: bold;
                """)
                self.blink_timer.stop()
    
    def stop_recording(self):
        """Para a gravação e salva"""
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "Deseja finalizar a gravação?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.finalize_recording()
    
    def cancel_recording(self):
        """Cancela a gravação"""
        reply = QMessageBox.warning(
            self,
            "Cancelar Gravação",
            "Tem certeza que deseja cancelar?\nA gravação será perdida.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.recorder.cancel_recording()
            self.cleanup()
            self.recording_cancelled.emit()
    
    def finalize_recording(self):
        """Finaliza e salva a gravação"""
        try:
            # Parar timers
            self.update_timer.stop()
            self.blink_timer.stop()
            
            # Calcular duração
            if self.start_time:
                duration = (datetime.now() - self.start_time).seconds
                self.meeting_data['duracao'] = duration // 60  # Em minutos
            
            # Parar gravação
            file_path = self.recorder.stop_recording()
            
            if file_path:
                logger.info(f"Gravação finalizada: {file_path}")
                self.cleanup()
                self.recording_finished.emit(file_path)
            else:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Não foi possível salvar a gravação."
                )
                self.recording_cancelled.emit()
                
        except Exception as e:
            logger.error(f"Erro ao finalizar gravação: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao salvar gravação: {str(e)}"
            )
            self.recording_cancelled.emit()
    
    def update_display(self):
        """Atualiza display do timer"""
        if self.start_time and not self.is_paused:
            elapsed = datetime.now() - self.start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            
            self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def blink_indicator(self):
        """Faz o indicador de gravação piscar"""
        if not self.is_paused:
            self.blink_state = not self.blink_state
            if self.blink_state:
                self.recording_indicator.setStyleSheet("""
                    font-size: 32px;
                    color: #dc2626;
                    font-weight: bold;
                """)
            else:
                self.recording_indicator.setStyleSheet("""
                    font-size: 32px;
                    color: #fca5a5;
                    font-weight: bold;
                """)
    
    @pyqtSlot(int)
    def update_volume(self, volume):
        """Atualiza indicador de volume"""
        self.volume_bar.setValue(volume)
    
    def cleanup(self):
        """Limpa recursos"""
        self.update_timer.stop()
        self.blink_timer.stop()
        if self.recording_thread:
            self.recording_thread.quit()
            self.recording_thread.wait()
    
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        # Resetar interface
        self.timer_label.setText("00:00:00")
        self.volume_bar.setValue(0)
        self.is_paused = False
        self.pause_button.setText("⏸ Pausar")
        self.recording_indicator.setText("🔴 REC")