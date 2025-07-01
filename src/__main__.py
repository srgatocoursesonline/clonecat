"""
Ponto de entrada principal do Clonecat
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    """Função principal do aplicativo"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 