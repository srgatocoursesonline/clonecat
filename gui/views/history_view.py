from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
import csv

class HistoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface da view de histórico"""
        layout = QVBoxLayout(self)
        
        # Tabela de histórico
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Data", "Canal Origem", "Canal Destino", "Status", "Detalhes"
        ])
        
        # Configurar cabeçalho da tabela
        header = self.history_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Botão para exportar histórico
        self.export_button = QPushButton("Exportar Histórico")
        
        # Adiciona widgets ao layout
        layout.addWidget(self.history_table)
        layout.addWidget(self.export_button)
        
        self.export_button.clicked.connect(self.exportar_csv)
    
    def add_history_item(self, date, source, destination, status, details):
        """Adiciona um novo item ao histórico"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        self.history_table.setItem(row, 0, QTableWidgetItem(date))
        self.history_table.setItem(row, 1, QTableWidgetItem(source))
        self.history_table.setItem(row, 2, QTableWidgetItem(destination))
        self.history_table.setItem(row, 3, QTableWidgetItem(status))
        self.history_table.setItem(row, 4, QTableWidgetItem(details))
    
    def clear_history(self):
        """Limpa o histórico"""
        self.history_table.setRowCount(0)
    
    def exportar_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar histórico como", "historico.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Cabeçalho
                headers = [self.history_table.horizontalHeaderItem(i).text() for i in range(self.history_table.columnCount())]
                writer.writerow(headers)
                # Dados
                for row in range(self.history_table.rowCount()):
                    row_data = []
                    for col in range(self.history_table.columnCount()):
                        item = self.history_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Exportação concluída", f"Histórico exportado para:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao exportar", str(e)) 