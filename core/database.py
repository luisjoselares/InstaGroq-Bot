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
        """Inicializa las tablas, maneja migraciones y asegura datos semilla."""
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

            # 2. Tabla de Historial: Para la memoria de la IA
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

            # 3. Tabla de Estado de Chats: Controla el modo manual
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_status (
                    thread_id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'ACTIVE',
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- MEJORA 4 APLICADA AQUÍ: EL REGISTRO SEMILLA ---
            # Verificamos si la tabla de configuración está vacía
            cursor.execute("SELECT COUNT(*) FROM settings")
            if cursor.fetchone()[0] == 0:
                # Insertamos una fila en blanco por defecto para que los UPDATEs de la UI funcionen
                cursor.execute("INSERT INTO settings (id, is_active) VALUES (1, 0)")
            # ---------------------------------------------------

            # --- AUTO-MIGRACIÓN ---
            try:
                cursor.execute("ALTER TABLE chat_history ADD COLUMN tokens_used INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # La columna ya existe

            conn.commit()

# Instancia única para ser importada en el resto del proyecto
db = DBConnection()