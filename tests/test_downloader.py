import unittest
from unittest.mock import MagicMock, patch
from src.core.advanced_downloader import AdvancedDownloader

class TestAdvancedDownloader(unittest.TestCase):
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.client = MagicMock()
        self.download_path = "./downloads"
        self.downloader = AdvancedDownloader(self.client, self.download_path)
    
    @patch('os.path.join')
    async def test_download_media_with_progress(self, mock_join):
        """Testa o download de mídia com progresso"""
        # Configura o mock
        mock_join.return_value = "./downloads/test.mp4"
        message = MagicMock()
        message.document.attributes = []
        
        # Executa o download
        result = await self.downloader.download_media_with_progress(message)
        
        # Verifica se o cliente foi chamado corretamente
        self.client.download_media.assert_called_once()
        self.assertIsNotNone(result)
    
    def test_get_file_name(self):
        """Testa a extração do nome do arquivo"""
        # Cria um mock de mensagem com atributos
        message = MagicMock()
        attribute = MagicMock()
        attribute.file_name = "test.mp4"
        message.document.attributes = [attribute]
        
        # Testa a extração do nome
        result = self.downloader._get_file_name(message)
        self.assertEqual(result, "test.mp4")
    
    def test_get_file_name_without_attributes(self):
        """Testa a extração do nome quando não há atributos"""
        # Cria um mock de mensagem sem atributos
        message = MagicMock()
        message.document.attributes = []
        
        # Testa a extração do nome
        result = self.downloader._get_file_name(message)
        self.assertTrue(result.startswith("unknown_"))

if __name__ == '__main__':
    unittest.main() 