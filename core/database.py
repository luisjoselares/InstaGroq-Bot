import sqlite3
import os
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path="data/pegasus_bot.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            # Tabla de configuración (ya incluye groq_key)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    insta_user TEXT,
                    insta_pass TEXT,
                    groq_key TEXT,
                    prompt_sistema TEXT,
                    is_active INTEGER DEFAULT 0,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insertar registro semilla si no existe
            conn.execute('INSERT OR IGNORE INTO settings (id, is_active) VALUES (1, 0)')
            
            # Tabla de historial de chat
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    username TEXT,
                    mensaje_usuario TEXT,
                    respuesta_ia TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    tokens_used INTEGER
                )
            ''')
            
            # Tabla de estados de chat (para handoff manual)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chat_status (
                    thread_id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'ACTIVE'
                )
            ''')
            conn.commit()

    # --- MÉTODOS ACTUALIZADOS PARA INCLUIR GROQ KEY ---
    def update_credentials(self, user, password, groq_key):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE settings SET insta_user = ?, insta_pass = ?, groq_key = ? WHERE id = 1",
                (user, password, groq_key)
            )
            conn.commit()

    def get_credentials(self):
        with self.get_connection() as conn:
            # Seleccionamos también la groq_key
            row = conn.execute("SELECT insta_user, insta_pass, groq_key FROM settings WHERE id = 1").fetchone()
            return row if row else None

# Instancia global para importar en otros archivos
db = DatabaseManager()