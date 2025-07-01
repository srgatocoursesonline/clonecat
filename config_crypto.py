import json
import base64
from cryptography.fernet import Fernet, InvalidToken
from getpass import getpass
import os

CONFIG_FILE = 'config.json'

# Gera uma chave Fernet a partir de uma senha
def password_to_key(password: str) -> bytes:
    # Usa SHA256 para garantir 32 bytes
    import hashlib
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

# Salva config criptografado
def save_encrypted_config(api_id, api_hash, password):
    key = password_to_key(password)
    f = Fernet(key)
    data = json.dumps({'api_id': api_id, 'api_hash': api_hash}).encode()
    token = f.encrypt(data)
    with open(CONFIG_FILE, 'wb') as fp:
        fp.write(token)

# Lê config criptografado
def load_encrypted_config(password):
    key = password_to_key(password)
    f = Fernet(key)
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, 'rb') as fp:
        token = fp.read()
    try:
        data = f.decrypt(token)
        config = json.loads(data.decode())
        return config['api_id'], config['api_hash']
    except InvalidToken:
        print('Senha incorreta ou arquivo corrompido.')
        return None 