from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet
import darkdetect

class ThemeManager:
    def __init__(self):
        self.current_theme = 'dark_teal.xml'
        self.available_themes = [
            'dark_teal.xml',
            'dark_blue.xml',
            'dark_amber.xml',
            'light_teal.xml',
            'light_blue.xml',
            'light_amber.xml'
        ]
    
    def apply_theme(self, window, theme_name=None):
        """Aplica um tema específico ou detecta o tema do sistema"""
        if theme_name:
            self.current_theme = theme_name
        else:
            # Detecta o tema do sistema
            if darkdetect.isDark():
                self.current_theme = 'dark_teal.xml'
            else:
                self.current_theme = 'light_teal.xml'
        
        apply_stylesheet(window, theme=self.current_theme)
    
    def get_available_themes(self):
        """Retorna lista de temas disponíveis"""
        return self.available_themes
    
    def get_current_theme(self):
        """Retorna o tema atual"""
        return self.current_theme 