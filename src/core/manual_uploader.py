import os
import json
import time
import asyncio
from telethon import TelegramClient
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict

class ManualUploader:
    def __init__(self, session_name, api_id, api_hash, temp_dir: str = "temp_storage"):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.upload_progress = {}
        self.load_progress()
        self.temp_dir = Path(temp_dir)
        self.db_path = self.temp_dir / "channel_data.db"
        self.upload_queue = []
        
    def load_progress(self):
        try:
            with open('temp_storage/cache/upload_progress.json', 'r') as f:
                self.upload_progress = json.load(f)
        except:
            self.upload_progress = {}
            
    def save_progress(self):
        with open('temp_storage/cache/upload_progress.json', 'w') as f:
            json.dump(self.upload_progress, f)

    async def upload_file(self, file_path, target_channel):
        try:
            file_id = os.path.basename(file_path)
            
            if file_id in self.upload_progress:
                return True
                
            # Calcula o tamanho do arquivo
            file_size = os.path.getsize(file_path)
            
            # Define o delay baseado no tamanho
            if file_size > 100 * 1024 * 1024:  # 100MB
                delay = 30
            elif file_size > 50 * 1024 * 1024:  # 50MB
                delay = 20
            else:
                delay = 10
                
            # Tenta fazer upload com retry
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    await self.client.send_file(
                        target_channel,
                        file_path
                    )
                    
                    self.upload_progress[file_id] = {
                        'path': file_path,
                        'timestamp': time.time()
                    }
                    self.save_progress()
                    
                    # Espera o delay antes de continuar
                    await asyncio.sleep(delay)
                    return True
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise e
                    await asyncio.sleep(delay * 2)  # Dobra o delay em caso de erro
            
            return False
            
        except Exception as e:
            with open('erros.log', 'a') as f:
                f.write(f"Erro ao fazer upload do arquivo {file_path}: {str(e)}\n")
            return False

    async def start_upload(self, folder_path, target_channel):
        try:
            await self.client.start()
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    await self.upload_file(file_path, target_channel)
                    
        except Exception as e:
            with open('erros.log', 'a') as f:
                f.write(f"Erro no upload manual: {str(e)}\n")
        finally:
            await self.client.disconnect() 

    async def prepare_upload_queue(self):
        """Prepara fila de upload ordenada cronologicamente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE downloaded = TRUE AND uploaded = FALSE
            ORDER BY date ASC
        ''')
        
        messages = cursor.fetchall()
        conn.close()
        
        for msg in messages:
            self.upload_queue.append({
                'id': msg[1],
                'date': msg[2],
                'text': msg[3],
                'media_type': msg[4],
                'media_path': msg[5],
                'caption': msg[6],
                'metadata': json.loads(msg[12]) if msg[12] else {}
            })
        
        return len(self.upload_queue)
    
    async def upload_message(self, client, destination_chat, message_data):
        """Faz upload de uma mensagem reconstruída"""
        try:
            if message_data['media_type'] and message_data['media_path']:
                # Upload com mídia
                media_path = Path(message_data['media_path'])
                
                if media_path.exists():
                    # Determinar método de envio baseado no tipo
                    if message_data['media_type'] == 'photo':
                        await client.send_file(
                            destination_chat,
                            file=str(media_path),
                            caption=message_data['caption'] or message_data['text'],
                            force_document=False
                        )
                    
                    elif message_data['media_type'] == 'video':
                        await client.send_file(
                            destination_chat,
                            file=str(media_path),
                            caption=message_data['caption'] or message_data['text'],
                            supports_streaming=True,
                            force_document=False
                        )
                    
                    elif message_data['media_type'] == 'document':
                        await client.send_file(
                            destination_chat,
                            file=str(media_path),
                            caption=message_data['caption'] or message_data['text'],
                            force_document=True
                        )
                    
                    elif message_data['media_type'] == 'audio':
                        await client.send_file(
                            destination_chat,
                            file=str(media_path),
                            caption=message_data['caption'] or message_data['text'],
                            voice=message_data['metadata'].get('is_voice', False)
                        )
            else:
                # Apenas texto
                if message_data['text']:
                    await client.send_message(
                        destination_chat,
                        message_data['text'],
                        parse_mode='html'
                    )
            
            # Marcar como uploaded
            self.mark_as_uploaded(message_data['id'])
            return True
            
        except Exception as e:
            logging.error(f"Erro ao fazer upload da mensagem {message_data['id']}: {e}")
            return False
    
    def mark_as_uploaded(self, message_id: int):
        """Marca mensagem como uploaded no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET uploaded = TRUE WHERE message_id = ?",
            (message_id,)
        )
        conn.commit()
        conn.close()
    
    def get_upload_stats(self) -> Dict:
        """Retorna estatísticas do processo de upload"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM messages WHERE downloaded = TRUE")
        total_downloaded = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages WHERE uploaded = TRUE")
        total_uploaded = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages WHERE has_media = TRUE")
        total_with_media = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_downloaded': total_downloaded,
            'total_uploaded': total_uploaded,
            'total_with_media': total_with_media,
            'pending': total_downloaded - total_uploaded
        } 