import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from qt_material import apply_stylesheet
from gui.components.progress_bar import CloneProgressBar
from gui.views.history_view import HistoryView
import threading
from gui.clonador_gui import clonar_canal_gui

class MainWindow(QMainWindow):
    progress_signal = pyqtSignal(int, str)
    status_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(object, str, str)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloneCat - Clonador de Canais Telegram")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.main_layout = main_layout
        
        # Configurar tema dark
        apply_stylesheet(self, theme='dark_teal.xml')
        
        self.setup_ui()
        # Conectar sinais aos slots
        self.progress_signal.connect(self.progress.update_progress)
        self.status_signal.connect(lambda status: self.progress.update_progress(self.progress.progress_bar.value(), status=status))
        self.finish_signal.connect(self._on_finish)
        self.error_signal.connect(self._on_error)
    
    def setup_ui(self):
        """Configura os elementos da interface"""
        # Campos de entrada
        self.input_origem = QLineEdit()
        self.input_origem.setPlaceholderText("Canal de origem (ID numérico)")
        self.input_origem.setStyleSheet("color: white;")
        self.input_destino = QLineEdit()
        self.input_destino.setPlaceholderText("Canal de destino (opcional)")
        self.input_destino.setStyleSheet("color: white;")
        self.start_button = QPushButton("Iniciar Clonagem")
        self.start_button.clicked.connect(self.start_clonagem)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_origem)
        input_layout.addWidget(self.input_destino)
        input_layout.addWidget(self.start_button)
        self.main_layout.insertLayout(0, input_layout)

        # Barra de progresso
        self.progress = CloneProgressBar()
        self.main_layout.addWidget(self.progress)
        # Histórico
        self.history = HistoryView()
        self.main_layout.addWidget(self.history)

        # Seleção de tipo de conteúdo (padrão: tudo)
        self.content_types = ["text", "photo", "video", "audio", "document", "sticker"]

    def start_clonagem(self):
        origem = self.input_origem.text()
        destino = self.input_destino.text()
        # TODO: obter api_id e api_hash do config.json
        import json
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                api_id = config["api_id"]
                api_hash = config["api_hash"]
        except Exception as e:
            self.progress.update_progress(0, status="Erro ao carregar credenciais", details=str(e))
            return
        self.progress.reset()
        self.progress.update_progress(0, status="Iniciando clonagem...", details="")
        self.start_button.setEnabled(False)
        # Thread para não travar a interface
        thread = threading.Thread(target=self.run_clonagem, args=(api_id, api_hash, origem, destino))
        thread.start()

    def run_clonagem(self, api_id, api_hash, origem, destino):
        def on_progress(value, status):
            self.progress_signal.emit(value, status)
        def on_status(status):
            self.status_signal.emit(status)
        def on_finish(destino, channel_name, channel_description):
            self.finish_signal.emit(destino, channel_name, channel_description)
        def on_error(msg):
            self.error_signal.emit(msg)
        clonar_canal_gui(
            api_id, api_hash, origem, destino, self.content_types,
            on_progress, on_status, on_finish, on_error
        )

    def _on_finish(self, destino, channel_name, channel_description):
        self.progress.update_progress(100, status="Clonagem concluída!", details=f"Canal: {channel_name}")
        from datetime import datetime
        self.history.add_history_item(
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            self.input_origem.text(),
            str(destino),
            "Concluído",
            channel_description
        )
        self.start_button.setEnabled(True)
        canal_link = self.gerar_link_canal(destino)
        msg = f"Nome do canal de destino: {channel_name}\nID: {destino}\n"
        if canal_link:
            msg += f"Link: {canal_link}"
        QMessageBox.information(self, "Clonagem concluída!", msg)

    def _on_error(self, msg):
        self.progress.update_progress(0, status="Erro", details=msg)
        from datetime import datetime
        self.history.add_history_item(
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            self.input_origem.text(),
            "",
            "Erro",
            msg
        )
        self.start_button.setEnabled(True)

    def gerar_link_canal(self, canal_id):
        # Se for canal público, o link é t.me/username, mas se for privado, pode tentar gerar convite
        # Aqui só monta o link padrão, pois não temos username. Se quiser buscar username, precisa da API.
        try:
            canal_id = str(canal_id)
            if canal_id.startswith("-100"):
                return f"https://t.me/c/{canal_id[4:]}"
            return None
        except Exception:
            return None

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 