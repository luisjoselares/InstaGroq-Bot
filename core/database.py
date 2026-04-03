import sqlite3
import os

class DBConnection:
    def __init__(self, db_name="insta_pegasus.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        """Establece la conexión. Usamos row_factory para acceder a datos por nombre de columna."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row 
        return conn

    def init_db(self):
        """Inicializa las tablas y maneja auto-migraciones básicas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Tabla de Configuración: Almacena credenciales y estado del bot
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

            # 2. Tabla de Historial: Para la memoria de la IA (Contexto)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    username TEXT,
                    mensaje_usuario TEXT,
                    respuesta_ia TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'AI_HANDLED'
                )
            ''')

            # 3. Tabla de Estado de Chats: Controla el modo manual (Botón de Pánico)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_status (
                    thread_id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE' o 'PAUSED'
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- AUTO-MIGRACIÓN ---
            # Si decides añadir el conteo de tokens en el futuro para Pegasus
            try:
                cursor.execute("ALTER TABLE chat_history ADD COLUMN tokens_used INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # La columna ya existe

            conn.commit()

# Instancia única para ser importada en el resto del proyecto
db = DBConnection()