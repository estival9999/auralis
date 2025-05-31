from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QPropertyAnimation, QRect, QThread
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
from src.core.style_manager import StyleManager
from src.core.ai_manager import ai_manager
from loguru import logger

class ListeningAnimationWidget(QWidget):
    """Widget que simula a animação de "ouvindo" """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.animation_step = 0
        self.setup_animation()
        
    def setup_animation(self):
        """Configura a animação"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        
    def start_animation(self):
        """Inicia a animação"""
        self.animation_timer.start(100)  # Atualiza a cada 100ms
        
    def stop_animation(self):
        """Para a animação"""
        self.animation_timer.stop()
        self.animation_step = 0
        self.update()
        
    def update_animation(self):
        """Atualiza o passo da animação"""
        self.animation_step = (self.animation_step + 1) % 30
        self.update()
        
    def paintEvent(self, event):
        """Desenha a animação de ondas sonoras"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Configurar cores
        color = QColor("#2563eb")
        pen = QPen(color)
        pen.setWidth(3)
        painter.setPen(pen)
        
        # Dimensões
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        
        # Desenhar ondas concêntricas
        for i in range(3):
            radius = 10 + (i * 15) + (self.animation_step * 2) % 30
            alpha = max(0, 255 - (self.animation_step * 10 + i * 50))
            
            wave_color = QColor(color)
            wave_color.setAlpha(alpha)
            pen.setColor(wave_color)
            painter.setPen(pen)
            
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

class TranscriptionWorker(QThread):
    """Worker thread para transcrição de áudio"""
    
    transcription_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
        
    def run(self):
        """Executa a transcrição"""
        try:
            # Parar escuta e transcrever
            transcription = ai_manager.stop_listening_and_transcribe()
            
            if transcription and not self.should_stop:
                self.transcription_completed.emit(transcription)
            elif not self.should_stop:
                self.error_occurred.emit("Nenhum áudio detectado ou transcrição vazia")
                
        except Exception as e:
            if not self.should_stop:
                logger.error(f"Erro na transcrição: {e}")
                self.error_occurred.emit(f"Erro na transcrição: {str(e)}")
    
    def stop(self):
        """Para o worker"""
        self.should_stop = True

class AuralisListeningWindow(QWidget):
    question_completed = pyqtSignal(str)  # Emite a pergunta transcrita
    listening_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_listening = False
        self.transcription_worker = None
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.record_audio_chunk)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("🎤 Auralis Ouvindo...")
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2563eb; font-weight: bold;")
        layout.addWidget(title)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Widget de animação
        self.animation_widget = ListeningAnimationWidget()
        layout.addWidget(self.animation_widget)
        
        # Status label
        self.status_label = QLabel("Fale sua pergunta agora...")
        self.status_label.setProperty("class", "subtitle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("❌ Cancelar")
        StyleManager.apply_button_style(self.cancel_button, "danger")
        self.cancel_button.clicked.connect(self.handle_cancel)
        buttons_layout.addWidget(self.cancel_button)
        
        self.complete_button = QPushButton("✅ Concluir")
        StyleManager.apply_button_style(self.complete_button, "success")
        self.complete_button.clicked.connect(self.handle_complete)
        buttons_layout.addWidget(self.complete_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def start_listening(self):
        """Inicia a escuta real"""
        try:
            # Iniciar escuta com AIManager
            result = ai_manager.start_listening_for_question()
            
            if result == "listening_started":
                self.is_listening = True
                self.animation_widget.start_animation()
                self.status_label.setText("🎙️ Fale agora... Clique em 'Concluir' quando terminar")
                
                # Iniciar timer para gravar chunks
                self.recording_timer.start(100)  # Gravar a cada 100ms
                
                logger.info("Escuta iniciada para Auralis")
            else:
                raise Exception("Falha ao iniciar escuta")
                
        except Exception as e:
            logger.error(f"Erro ao iniciar escuta: {e}")
            self.status_label.setText(f"❌ Erro: {str(e)}")
            
    def record_audio_chunk(self):
        """Grava um chunk de áudio"""
        if self.is_listening:
            success = ai_manager.record_audio_chunk()
            if not success:
                logger.warning("Falha ao gravar chunk de áudio")
        
    def handle_complete(self):
        """Processa a conclusão da pergunta"""
        if self.is_listening:
            self.stop_listening()
            self.show_processing()
            
    def handle_cancel(self):
        """Cancela a escuta"""
        self.stop_listening()
        
        # Parar AIManager se necessário
        try:
            ai_manager.stop_listening_and_transcribe()
        except Exception:
            pass
            
        self.listening_cancelled.emit()
        
    def stop_listening(self):
        """Para a escuta"""
        self.is_listening = False
        self.recording_timer.stop()
        self.animation_widget.stop_animation()
        
    def show_processing(self):
        """Mostra estado de processamento e inicia transcrição"""
        self.status_label.setText("⏳ Processando áudio e transcrevendo...")
        self.complete_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # Iniciar worker de transcrição
        self.transcription_worker = TranscriptionWorker()
        self.transcription_worker.transcription_completed.connect(self.on_transcription_completed)
        self.transcription_worker.error_occurred.connect(self.on_transcription_error)
        self.transcription_worker.start()
        
    def on_transcription_completed(self, transcription: str):
        """Callback quando transcrição é concluída"""
        logger.info(f"Transcrição recebida: {transcription}")
        
        self.status_label.setText(f"✅ Pergunta transcrita: '{transcription}'")
        
        # Emitir pergunta após pequeno delay
        QTimer.singleShot(1500, lambda: self.question_completed.emit(transcription))
        
    def on_transcription_error(self, error_message: str):
        """Callback quando ocorre erro na transcrição"""
        logger.error(f"Erro na transcrição: {error_message}")
        
        self.status_label.setText(f"❌ {error_message}")
        self.complete_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        # Voltar ao chat após delay
        QTimer.singleShot(3000, self.listening_cancelled.emit)
        
    def on_window_show(self):
        """Chamado quando a janela é mostrada"""
        # Reset do estado
        self.complete_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        # Verificar se AIManager está disponível
        if not ai_manager.openai_client:
            self.status_label.setText("❌ Sistema de IA não configurado")
            self.complete_button.setEnabled(False)
            return
            
        self.start_listening()
        
    def closeEvent(self, event):
        """Cleanup ao fechar janela"""
        try:
            if self.transcription_worker and self.transcription_worker.isRunning():
                self.transcription_worker.stop()
                self.transcription_worker.wait(2000)
                
            self.stop_listening()
            
        except Exception as e:
            logger.error(f"Erro no cleanup: {e}")
            
        super().closeEvent(event) 