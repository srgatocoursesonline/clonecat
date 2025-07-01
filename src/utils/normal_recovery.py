import sqlite3
from pathlib import Path
from typing import Optional

class NormalRecovery:
    def __init__(self, db_path='normal_recovery/normal_clone.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cloned_messages (
                message_id INTEGER PRIMARY KEY
            )
        ''')
        self.conn.commit()

    def is_cloned(self, message_id: int) -> bool:
        self.cursor.execute('SELECT 1 FROM cloned_messages WHERE message_id = ?', (message_id,))
        return self.cursor.fetchone() is not None

    def mark_cloned(self, message_id: int):
        self.cursor.execute('INSERT OR IGNORE INTO cloned_messages (message_id) VALUES (?)', (message_id,))
        self.conn.commit()

    def get_last_cloned_id(self) -> Optional[int]:
        self.cursor.execute('SELECT MAX(message_id) FROM cloned_messages')
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else None

    def clear(self):
        self.cursor.execute('DELETE FROM cloned_messages')
        self.conn.commit()

    def close(self):
        self.conn.close() 