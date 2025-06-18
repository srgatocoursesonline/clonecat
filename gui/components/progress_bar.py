from PyQt6.QtWidgets import QProgressBar, QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class CloneProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do componente"""
        layout = QVBoxLayout(self)
        
        # Label para status
        self.status_label = QLabel("Aguardando início...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        # Label para detalhes
        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Adiciona widgets ao layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.details_label)
    
    def update_progress(self, value, status=None, details=None):
        """Atualiza o progresso e informações adicionais"""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
        if details:
            self.details_label.setText(details)
    
    def reset(self):
        """Reseta o componente para o estado inicial"""
        self.progress_bar.setValue(0)
        self.status_label.setText("Aguardando início...")
        self.details_label.setText("") 