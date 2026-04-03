import sqlite3
import os

class DBConnection:
    def __init__(self, db_name="insta_pegasus.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        """Establece la conexión y permite acceso por nombre de columna."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row 
        return conn

    def init_db(self):
        """Maneja la creación inicial y las auto-migraciones de las tablas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Tabla de Configuración: Almacena credenciales y estado global del bot.
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

            # 2. Tabla de Historial: Almacena los mensajes para la memoria de la IA y analíticas.
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

            # 3. Tabla de Estado de Chats: Controla el "Botón de Pánico" por cada conversación.
            # Esta tabla es vital para que el motor de Instagram sepa a quién no responder.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_status (
                    thread_id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE' o 'PAUSED'
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- SECCIÓN DE AUTO-MIGRACIONES ---
            # Permite actualizar la estructura de la base de datos sin borrar datos existentes.
            
            # Ejemplo: Agregar columna para conteo de tokens si no existe.
            try:
                cursor.execute("ALTER TABLE chat_history ADD COLUMN tokens_used INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # La columna ya existe.

            conn.commit()

# Instancia única (Singleton) para ser importada en todo el proyecto.
db = DBConnection()