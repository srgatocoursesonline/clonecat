"""
Configurações e fixtures para testes
"""

import pytest
import os
from unittest.mock import MagicMock

@pytest.fixture
def mock_client():
    """Retorna um mock do cliente Telegram"""
    client = MagicMock()
    client.api_id = "123456"
    client.api_hash = "abcdef123456"
    return client

@pytest.fixture
def test_paths():
    """Retorna caminhos para testes"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {
        'downloads': os.path.join(base_dir, 'downloads'),
        'cache': os.path.join(base_dir, 'cache'),
        'recovery': os.path.join(base_dir, 'recovery')
    }

@pytest.fixture
def mock_message():
    """Retorna um mock de mensagem do Telegram"""
    message = MagicMock()
    message.id = 12345
    message.chat.id = 67890
    
    # Atributos do documento
    document = MagicMock()
    attribute = MagicMock()
    attribute.file_name = "test.mp4"
    document.attributes = [attribute]
    message.document = document
    
    return message 