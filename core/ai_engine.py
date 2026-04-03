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
        Genera una respuesta inteligente considerando el historial 
        del chat y el prompt del sistema configurado.
        """
        try:
            client = self._get_client()
            
            # 1. Recuperamos el historial del hilo para darle memoria a la IA
            history = self._get_history(thread_id, limit=6)
            
            # 2. Obtenemos el System Prompt configurado por el usuario
            with db.get_connection() as conn:
                row = conn.execute("SELECT prompt_sistema FROM settings LIMIT 1").fetchone()
                sys_prompt = row['prompt_sistema'] if row and row['prompt_sistema'] else "Eres un asistente profesional."

            # 3. Construimos el paquete de mensajes
            messages = [{"role": "system", "content": sys_prompt}]
            
            # Agregamos la memoria (historial previo)
            for h in history:
                messages.append({"role": "user", "content": h['mensaje_usuario']})
                messages.append({"role": "assistant", "content": h['respuesta_ia']})
            
            # Agregamos el mensaje actual
            messages.append({"role": "user", "content": user_input})

            # 4. Solicitud a la API de Groq
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7, # Creatividad balanceada
                max_tokens=500
            )
            
            return completion.choices[0].message.content

        except Exception as e:
            logging.error(f"Error en AI Service: {e}")
            return "Lo siento, tuve un problema al procesar tu mensaje. ¿Podrías repetirlo?"

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