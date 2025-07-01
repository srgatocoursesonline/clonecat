import os
import json
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Dict, List, Optional
import sqlite3
import logging

class AdvancedDownloader:
    def __init__(self, temp_dir: str = "temp_storage"):
        self.temp_dir = Path(temp_dir)
        self.setup_directories()
        self.db_path = self.temp_dir / "channel_data.db"
        self.init_database()
    
    def setup_directories(self):
        """Cria estrutura de diretórios necessária"""
        dirs = [
            self.temp_dir / "messages",
            self.temp_dir / "media" / "photos",
            self.temp_dir / "media" / "videos",
            self.temp_dir / "media" / "documents",
            self.temp_dir / "media" / "audio",
            self.temp_dir / "cache"
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """Inicializa banco de dados SQLite para metadados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                message_id INTEGER UNIQUE,
                date TEXT,
                text TEXT,
                media_type TEXT,
                media_path TEXT,
                caption TEXT,
                views INTEGER,
                forwards INTEGER,
                replies INTEGER,
                has_media BOOLEAN,
                downloaded BOOLEAN DEFAULT FALSE,
                uploaded BOOLEAN DEFAULT FALSE,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_info (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def download_message_content(self, client, message, progress_callback=None):
        """Baixa conteúdo de uma mensagem específica"""
        message_data = {
            'id': message.id,
            'date': message.date.isoformat(),
            'text': message.text or message.message,
            'caption': getattr(message, 'caption', None),
            'views': getattr(message, 'views', 0),
            'forwards': getattr(message, 'forwards', 0),
            'media_type': None,
            'media_path': None
        }
        
        # Identificar tipo de mídia
        if message.photo:
            message_data['media_type'] = 'photo'
            media_path = await self.download_photo(client, message)
            message_data['media_path'] = str(media_path)
        
        elif message.video:
            message_data['media_type'] = 'video'
            media_path = await self.download_video(client, message, progress_callback)
            message_data['media_path'] = str(media_path)
        
        elif message.document:
            message_data['media_type'] = 'document'
            media_path = await self.download_document(client, message, progress_callback)
            message_data['media_path'] = str(media_path)
        
        elif message.audio or message.voice:
            message_data['media_type'] = 'audio'
            media_path = await self.download_audio(client, message, progress_callback)
            message_data['media_path'] = str(media_path)
        
        # Salvar metadados da mensagem
        self.save_message_metadata(message_data)
        
        return message_data
    
    async def download_photo(self, client, message):
        """Baixa foto com qualidade máxima"""
        filename = f"photo_{message.id:06d}.jpg"
        filepath = self.temp_dir / "media" / "photos" / filename
        
        if not filepath.exists():
            await client.download_media(
                message.photo,
                file=str(filepath),
                thumb=-1  # Baixa em qualidade máxima
            )
        
        return filepath
    
    async def download_video(self, client, message, progress_callback=None):
        """Baixa vídeo com callback de progresso"""
        filename = f"video_{message.id:06d}.mp4"
        filepath = self.temp_dir / "media" / "videos" / filename
        
        if not filepath.exists():
            try:
                await client.download_media(
                    message,
                    file=str(filepath),
                    progress_callback=progress_callback
                )
            except Exception as e:
                print(f"Erro ao baixar vídeo {message.id}: {e}")
                return None
        
        return filepath
    
    async def download_document(self, client, message, progress_callback=None):
        """Baixa documento"""
        ext = message.file.ext or 'bin'
        filename = f"doc_{message.id:06d}.{ext}"
        filepath = self.temp_dir / "media" / "documents" / filename
        
        if not filepath.exists():
            await client.download_media(
                message.document,
                file=str(filepath),
                progress_callback=progress_callback
            )
        
        return filepath
    
    async def download_audio(self, client, message, progress_callback=None):
        """Baixa áudio ou mensagem de voz"""
        ext = 'ogg' if message.voice else 'mp3'
        filename = f"audio_{message.id:06d}.{ext}"
        filepath = self.temp_dir / "media" / "audio" / filename
        
        if not filepath.exists():
            await client.download_media(
                message,
                file=str(filepath),
                progress_callback=progress_callback
            )
        
        return filepath
    
    def save_message_metadata(self, message_data: dict):
        """Salva metadados da mensagem no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO messages 
            (message_id, date, text, media_type, media_path, caption, 
             views, forwards, has_media, downloaded, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            message_data['id'],
            message_data['date'],
            message_data['text'],
            message_data['media_type'],
            message_data['media_path'],
            message_data['caption'],
            message_data['views'],
            message_data['forwards'],
            bool(message_data['media_type']),
            True,
            json.dumps(message_data)
        ))
        
        conn.commit()
        conn.close() 