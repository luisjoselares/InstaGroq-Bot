import sqlite3
import os

class DBConnection:
    def __init__(self, db_name="insta_pegasus.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Permite acceder a datos por nombre de columna
        return conn

    def init_db(self):
        """Maneja la creación inicial y las auto-migraciones"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Tabla de Configuración (Single Row)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    insta_user TEXT,
                    insta_pass TEXT,
                    groq_key TEXT,
                    prompt_sistema TEXT,
                    is_active INTEGER DEFAULT 0,
                    last_sync TIMESTAMP
                )
            ''')

            # 2. Tabla de Logs e Historial (Para el RAG y Analíticas)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    username TEXT,
                    mensaje_usuario TEXT,
                    respuesta_ia TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'AI_HANDLED' -- AI_HANDLED o HUMAN_REQUIRED
                )
            ''')

            # 3. EJEMPLO DE AUTO-MIGRACIÓN:
            # Si en el futuro necesitas agregar una columna 'token_usage', 
            # verificamos si existe, si no, la añadimos.
            try:
                cursor.execute("ALTER TABLE chat_history ADD COLUMN tokens_used INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # La columna ya existe, no hacemos nada

            conn.commit()

# Instancia única para el proyecto
db = DBConnection()