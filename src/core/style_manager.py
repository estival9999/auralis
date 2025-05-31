"""
Gerenciador de estilos do sistema AURALIS
Baseado nos estilos do projeto windows/
"""
from PyQt6.QtWidgets import QApplication

class StyleManager:
    """Gerencia estilos e temas da aplicação"""
    
    # Paleta de cores moderna
    COLORS = {
        'primary': '#2563eb',
        'primary_hover': '#1d4ed8',
        'success': '#059669',
        'error': '#dc2626',
        'warning': '#d97706',
        'background': '#f8fafc',
        'surface': '#ffffff',
        'text': '#1e293b',
        'text_secondary': '#64748b',
        'border': '#e2e8f0'
    }
    
    # Estilo base da aplicação
    BASE_STYLE = f"""
    QWidget {{
        background-color: {COLORS['background']};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
        font-size: 13px;
        color: {COLORS['text']};
    }}
    
    QLabel {{
        color: {COLORS['text']};
        padding: 2px;
    }}
    
    QLabel[class="title"] {{
        font-size: 18px;
        font-weight: 600;
        color: {COLORS['text']};
        padding: 10px 0;
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        padding: 5px 0;
    }}
    
    QLineEdit {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        color: {COLORS['text']};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS['primary']};
        outline: none;
    }}
    
    QLineEdit:hover {{
        border: 1px solid {COLORS['text_secondary']};
    }}
    
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 16px;
        font-size: 13px;
        font-weight: 500;
        min-height: 36px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: #1e40af;
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_secondary']};
    }}
    
    QPushButton[class="secondary"] {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
    }}
    
    QPushButton[class="secondary"]:hover {{
        background-color: {COLORS['background']};
        border: 1px solid {COLORS['text_secondary']};
    }}
    
    QPushButton[class="danger"] {{
        background-color: {COLORS['error']};
    }}
    
    QPushButton[class="danger"]:hover {{
        background-color: #b91c1c;
    }}
    
    QListWidget {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }}
    
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
        margin: 2px 0;
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
    }}
    
    QListWidget::item:hover {{
        background-color: {COLORS['background']};
    }}
    
    QTextEdit {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px;
        font-size: 13px;
        color: {COLORS['text']};
    }}
    
    QTextEdit:focus {{
        border: 2px solid {COLORS['primary']};
        outline: none;
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS['background']};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_secondary']};
    }}
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QMessageBox {{
        background-color: {COLORS['surface']};
    }}
    
    QMessageBox QLabel {{
        color: {COLORS['text']};
        font-size: 13px;
    }}
    
    QMessageBox QPushButton {{
        min-width: 80px;
    }}
    """
    
    @staticmethod
    def apply_theme(app: QApplication):
        """Aplica o tema à aplicação"""
        app.setStyleSheet(StyleManager.BASE_STYLE)
    
    @staticmethod
    def get_color(color_name: str) -> str:
        """Retorna uma cor específica da paleta"""
        return StyleManager.COLORS.get(color_name, '#000000')