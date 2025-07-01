import os
import json
import sqlite3
import time
from datetime import datetime
import shutil
from pathlib import Path
from typing import Optional, Dict

class CacheManager:
    def __init__(self, db_path: str, cache_dir: Path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize_db()
        self.cache_dir = cache_dir
        self.progress_file = cache_dir / "download_progress.json"
        
    def initialize_db(self):
        """Inicializa o banco de dados SQLite com as tabelas necessárias"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Criar tabela de cache
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    message_id INTEGER PRIMARY KEY,
                    chat_id INTEGER,
                    file_id TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    download_path TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            raise
    
    def add_cache_entry(self, message_id: int, chat_id: int, file_data: dict):
        """Adiciona uma nova entrada no cache"""
        try:
            current_time = datetime.now().isoformat()
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO cache 
                (message_id, chat_id, file_id, file_name, file_size, 
                download_path, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                chat_id,
                file_data.get('file_id'),
                file_data.get('file_name'),
                file_data.get('file_size'),
                file_data.get('download_path'),
                'pending',
                current_time,
                current_time
            ))
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Erro ao adicionar entrada no cache: {str(e)}")
            self.conn.rollback()
    
    def update_cache_status(self, message_id: int, status: str):
        """Atualiza o status de um download no cache"""
        try:
            current_time = datetime.now().isoformat()
            
            self.cursor.execute('''
                UPDATE cache 
                SET status = ?, updated_at = ?
                WHERE message_id = ?
            ''', (status, current_time, message_id))
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Erro ao atualizar status no cache: {str(e)}")
            self.conn.rollback()
    
    def get_pending_downloads(self):
        """Retorna lista de downloads pendentes"""
        try:
            self.cursor.execute('''
                SELECT * FROM cache 
                WHERE status = 'pending'
                ORDER BY created_at ASC
            ''')
            
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"Erro ao buscar downloads pendentes: {str(e)}")
            return []
    
    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
        
    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Cria tabela de canais
        c.execute('''
            CREATE TABLE IF NOT EXISTS channels
            (username TEXT PRIMARY KEY, 
             last_update REAL,
             total_messages INTEGER,
             total_media INTEGER)
        ''')
        
        # Cria tabela de mídia
        c.execute('''
            CREATE TABLE IF NOT EXISTS media
            (message_id INTEGER PRIMARY KEY,
             channel TEXT,
             media_type TEXT,
             file_path TEXT,
             download_date REAL,
             FOREIGN KEY (channel) REFERENCES channels(username))
        ''')
        
        conn.commit()
        conn.close()
        
    def update_channel_stats(self, username, total_messages, total_media):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO channels
            (username, last_update, total_messages, total_media)
            VALUES (?, ?, ?, ?)
        ''', (username, time.time(), total_messages, total_media))
        
        conn.commit()
        conn.close()
        
    def add_media_entry(self, message_id, channel, media_type, file_path):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO media
            (message_id, channel, media_type, file_path, download_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (message_id, channel, media_type, file_path, time.time()))
        
        conn.commit()
        conn.close()
        
    def get_channel_stats(self, username):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM channels WHERE username = ?', (username,))
        result = c.fetchone()
        
        conn.close()
        
        if result:
            return {
                'username': result[0],
                'last_update': result[1],
                'total_messages': result[2],
                'total_media': result[3]
            }
        return None
        
    def get_media_list(self, channel=None, media_type=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        query = 'SELECT * FROM media WHERE 1=1'
        params = []
        
        if channel:
            query += ' AND channel = ?'
            params.append(channel)
            
        if media_type:
            query += ' AND media_type = ?'
            params.append(media_type)
            
        c.execute(query, params)
        results = c.fetchall()
        
        conn.close()
        
        return [{
            'message_id': r[0],
            'channel': r[1],
            'media_type': r[2],
            'file_path': r[3],
            'download_date': r[4]
        } for r in results]
        
    def clear_old_cache(self, days=7):
        # Remove entradas antigas do banco
        threshold = time.time() - (days * 24 * 60 * 60)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Pega arquivos antigos antes de deletar
        c.execute('SELECT file_path FROM media WHERE download_date < ?', (threshold,))
        old_files = [r[0] for r in c.fetchall()]
        
        # Remove entradas antigas
        c.execute('DELETE FROM media WHERE download_date < ?', (threshold,))
        conn.commit()
        conn.close()
        
        # Remove arquivos físicos
        for file_path in old_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    with open('temp_storage/cache/cache_errors.log', 'a') as f:
                        f.write(f"Erro ao remover arquivo {file_path}: {str(e)}\n")
                        
    def get_cache_size(self) -> float:
        total_size = 0
        temp_dir = self.cache_dir.parent
        
        if temp_dir.exists():
            for path in temp_dir.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
        
        return total_size / (1024 * 1024)  # Converter para MB
    
    def save_progress(self, channel_id: int, last_message_id: int, 
                     total_messages: int, downloaded: int):
        """Salva progresso do download"""
        progress_data = {
            'channel_id': channel_id,
            'last_message_id': last_message_id,
            'total_messages': total_messages,
            'downloaded': downloaded,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def load_progress(self) -> Optional[dict]:
        """Carrega progresso anterior"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return None
    
    def clear_cache(self):
        """Limpa cache após conclusão"""
        if self.progress_file.exists():
            self.progress_file.unlink()
            
    def clear_all_temp_files(self):
        """Remove todos os arquivos temporários"""
        temp_dir = self.cache_dir.parent
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print("✅ Todos os arquivos temporários foram removidos.")
    
    def get_download_stats(self) -> Dict:
        """Retorna estatísticas do download"""
        progress = self.load_progress()
        if progress:
            return {
                'channel_id': progress.get('channel_id'),
                'total_messages': progress.get('total_messages', 0),
                'downloaded': progress.get('downloaded', 0),
                'percentage': (progress.get('downloaded', 0) / progress.get('total_messages', 1)) * 100,
                'last_update': progress.get('timestamp')
            }
        return {
            'channel_id': None,
            'total_messages': 0,
            'downloaded': 0,
            'percentage': 0,
            'last_update': None
        } 