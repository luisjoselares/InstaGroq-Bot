from groq import Groq
from core.database import db # Importamos nuestra instancia de conexión
import logging

class AIService:
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"
        self._client = None

    def _get_client(self):
        """Lazy loading del cliente para asegurar que tenemos la API Key"""
        if self._client is None:
            # Buscamos la configuración en la DB
            with db.get_connection() as conn:
                config = conn.execute("SELECT groq_key FROM settings LIMIT 1").fetchone()
                if config and config['groq_key']:
                    self._client = Groq(api_key=config['groq_key'])
                else:
                    raise ValueError("API Key de Groq no configurada en la base de datos.")
        return self._client

    def get_system_prompt(self):
        """Recupera el prompt configurado por el cliente o uno por defecto"""
        with db.get_connection() as conn:
            row = conn.execute("SELECT prompt_sistema FROM settings LIMIT 1").fetchone()
            if row and row['prompt_sistema']:
                return row['prompt_sistema']
            return "Eres un asistente amable y profesional. Responde de forma concisa."

    def generate_response(self, user_input, thread_id):
        """Genera una respuesta considerando el historial del chat"""
        try:
            client = self._get_client()
            
            # 1. Recuperamos el historial de este hilo (últimos 6 mensajes para no quemar tokens)
            history = self._get_history(thread_id, limit=6)
            
            # 2. Construimos el payload de mensajes
            messages = [{"role": "system", "content": self.get_system_prompt()}]
            
            # Añadimos el historial previo
            for h in history:
                messages.append({"role": "user", "content": h['mensaje_usuario']})
                messages.append({"role": "assistant", "content": h['respuesta_ia']})
            
            # Añadimos el mensaje actual
            messages.append({"role": "user", "content": user_input})

            # 3. Inferencia en Groq
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7, # Balance entre creatividad y precisión
                max_tokens=500
            )
            
            respuesta = completion.choices[0].message.content
            return respuesta

        except Exception as e:
            logging.error(f"Error en AI Service: {e}")
            return "Lo siento, tuve un problema técnico. ¿Puedes repetir?"

    def _get_history(self, thread_id, limit=6):
        """Busca en SQLite los mensajes anteriores de este usuario"""
        with db.get_connection() as conn:
            return conn.execute(
                "SELECT mensaje_usuario, respuesta_ia FROM chat_history "
                "WHERE thread_id = ? ORDER BY timestamp DESC LIMIT ?",
                (thread_id, limit)
            ).fetchall()[::-1] # Invertimos para que sea cronológico