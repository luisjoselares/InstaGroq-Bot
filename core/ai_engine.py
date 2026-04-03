from groq import Groq
from core.database import db
import logging

class AIService:
    def __init__(self):
        # Modelo de alto rendimiento para respuestas rápidas y precisas
        self.model = "llama-3.3-70b-versatile"
        self._client = None

    def _get_client(self):
        """Lazy loading: Solo instancia el cliente de Groq cuando se necesita."""
        if self._client is None:
            with db.get_connection() as conn:
                config = conn.execute("SELECT groq_key FROM settings LIMIT 1").fetchone()
                if config and config['groq_key']:
                    self._client = Groq(api_key=config['groq_key'])
                else:
                    raise ValueError("API Key de Groq no encontrada en la base de datos.")
        return self._client

    def generate_response(self, user_input, thread_id):
        """
        Genera una respuesta inteligente validando que no existan nulos en la memoria.
        """
        # 0. Defensa rápida: Si el usuario mandó un sticker o nota de voz vacía
        user_input_clean = str(user_input).strip() if user_input else ""
        if not user_input_clean:
            # Evitamos gastar tokens de la API si no hay texto que leer
            return "He recibido un mensaje multimedia o un formato que aún no puedo leer. ¿Podrías escribírmelo?"

        try:
            client = self._get_client()
            history = self._get_history(thread_id, limit=6)
            
            with db.get_connection() as conn:
                row = conn.execute("SELECT prompt_sistema FROM settings LIMIT 1").fetchone()
                sys_prompt = row['prompt_sistema'] if row and row['prompt_sistema'] else "Eres un asistente profesional."

            messages = [{"role": "system", "content": sys_prompt}]
            
            # Agregamos la memoria con VALIDACIÓN ANTI-CRASH
            for h in history:
                # Limpiamos los datos de SQLite por si vienen como None o con puros espacios
                msg_user = str(h['mensaje_usuario']).strip() if h['mensaje_usuario'] else ""
                msg_ia = str(h['respuesta_ia']).strip() if h['respuesta_ia'] else ""
                
                # Solo inyectamos a la memoria si realmente hay texto útil
                if msg_user:
                    messages.append({"role": "user", "content": msg_user})
                if msg_ia:
                    messages.append({"role": "assistant", "content": msg_ia})
            
            # Agregamos el mensaje actual (ya validado en el paso 0)
            messages.append({"role": "user", "content": user_input_clean})

            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7, 
                max_tokens=500
            )
            
            return completion.choices[0].message.content

        except Exception as e:
            logging.error(f"Error en AI Service: {e}")
            return "Lo siento, tuve un inconveniente procesando tu mensaje. ¿Podrías repetirlo?"
        
    def _get_history(self, thread_id, limit=6):
        """Recupera los últimos mensajes de SQLite para este usuario específico."""
        with db.get_connection() as conn:
            # Traemos los últimos mensajes ordenados por tiempo
            rows = conn.execute(
                "SELECT mensaje_usuario, respuesta_ia FROM chat_history "
                "WHERE thread_id = ? ORDER BY timestamp DESC LIMIT ?",
                (thread_id, limit)
            ).fetchall()
            
            # Los invertimos para que estén en orden cronológico (viejo -> nuevo)
            return rows[::-1]