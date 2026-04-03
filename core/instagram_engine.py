import time
import random
import logging
import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, FeedbackRequired
from core.database import db
from core.ai_engine import AIService

class InstagramService:
    def __init__(self):
        self.cl = Client()
        self.ai = AIService()
        self.is_running = False
        self.session_file = "sessions/insta_session.json"
        self.log_callback = None
        os.makedirs("sessions", exist_ok=True)

    def set_callback(self, callback_func):
        self.log_callback = callback_func

    def _ui_log(self, mensaje):
        logging.info(mensaje)
        if self.log_callback:
            self.log_callback(mensaje)

    def login(self):
        """Inicia sesión de forma inteligente para evitar bloqueos por 'Login Dudoso'."""
        with db.get_connection() as conn:
            config = conn.execute("SELECT insta_user, insta_pass FROM settings LIMIT 1").fetchone()
            if not config or not config['insta_user']:
                raise ValueError("Credenciales no configuradas.")
            user, pw = config['insta_user'], config['insta_pass']

        # 1. Intentar cargar sesión existente
        if os.path.exists(self.session_file):
            try:
                self.cl.load_settings(self.session_file)
                # IMPORTANTE: Verificamos si la sesión funciona SIN hacer login()
                self.cl.get_timeline_feed() 
                self._ui_log("Sesión recuperada (Sin login necesario).")
                return # Sesión válida, salimos con éxito
            except Exception:
                self._ui_log("Sesión antigua expirada. Intentando re-login...")
        
        # 2. Si no hay sesión o expiró, hacemos un 'Hard Login'
        try:
            self._ui_log(f"Iniciando sesión formal para @{user}...")
            # Esperamos un poco antes de loguear para parecer humanos
            time.sleep(random.uniform(2, 5)) 
            self.cl.login(user, pw)
            self.cl.dump_settings(self.session_file)
            self._ui_log("Nuevo login exitoso y sesión guardada.")
        except ChallengeRequired:
            self._ui_log("¡DESAFÍO DETECTADO! Abre Instagram en tu móvil y aprueba el inicio.")
            raise
        except Exception as e:
            self._ui_log(f"Error crítico en login: {str(e)}")
            raise

    def start_polling(self):
        self.is_running = True
        try:
            self.login()
        except Exception:
            self.is_running = False
            return

        while self.is_running:
            try:
                with db.get_connection() as conn:
                    status = conn.execute("SELECT is_active FROM settings").fetchone()
                    if not status or status['is_active'] == 0:
                        time.sleep(5)
                        continue

                # Filtro unread
                threads = self.cl.direct_threads(amount=10, selected_filter="unread")
                
                for thread in threads:
                    # MEJORA 5: Aislamiento de errores. Si un chat falla, no tumba al resto.
                    try:
                        if not thread.messages: continue
                        last_msg = thread.messages[0]
                        
                        if last_msg.user_id == self.cl.user_id: continue
                        
                        # Modo Manual / Pánico
                        if self._requires_human(thread.id): continue
                        if self._check_panic_keywords(last_msg.text):
                            self._handoff_to_human(thread.id, thread.users[0].username)
                            continue

                        self._ui_log(f"Nuevo mensaje de @{thread.users[0].username}")
                        
                        # Generamos la respuesta PRIMERO
                        respuesta = self.ai.generate_response(last_msg.text, thread.id)
                        
                        # Tiempo de 'Escribiendo...'
                        time.sleep(random.uniform(5, 12))
                        
                        # Intentamos enviarlo
                        self.cl.direct_send(respuesta, thread_ids=[thread.id])
                        
                        # SOLO DESPUÉS de un envío exitoso, lo marcamos como leído en Instagram
                        self.cl.direct_thread_mark_seen(thread.id)
                        
                        self._ui_log(f"Respondido a @{thread.users[0].username}")
                        self._log_interaction(thread.id, thread.users[0].username, last_msg.text, respuesta)

                    except Exception as thread_error:
                        # Si falla un solo chat (ej. Groq se cayó para este mensaje), lo reportamos
                        # y usamos 'continue' para seguir atendiendo a las otras 9 personas en cola.
                        logging.error(f"Error aislado en chat {thread.id}: {thread_error}")
                        continue

            except FeedbackRequired:
                self._ui_log("¡Feedback Required! Instagram detectó mucha actividad. Pausando 10 min...")
                time.sleep(600)
            except Exception as e:
                # Este except principal ahora solo atrapa errores masivos (como pérdida de conexión a internet)
                logging.error(f"Error crítico en motor principal: {e}")
            
            # Delay maestro: Fundamental para no ser detectado
            time.sleep(random.uniform(30, 60))

    def stop(self):
        self.is_running = False

    def _requires_human(self, tid):
        with db.get_connection() as conn:
            row = conn.execute("SELECT status FROM chat_status WHERE thread_id = ?", (tid,)).fetchone()
            return row and row['status'] == 'PAUSED'

    def _check_panic_keywords(self, text):
        return any(k in text.lower() for k in ["humano", "persona", "asesor", "ayuda", "atencion"])

    def _handoff_to_human(self, tid, user):
        with db.get_connection() as conn:
            conn.execute("INSERT INTO chat_status (thread_id, status) VALUES (?, 'PAUSED') ON CONFLICT(thread_id) DO UPDATE SET status='PAUSED'", (tid,))
            conn.commit()
            
        # --- CORRECCIÓN MENOR PREVENTIVA ---
        # Se asegura el uso del kwarg thread_ids para evitar que envíe el tid como user_id
        self.cl.direct_send("Pausé mis respuestas. Un humano te atenderá.", thread_ids=[tid])
        
        self._ui_log(f"Handoff manual activado para @{user}")

    def _log_interaction(self, tid, user, msg, resp):
        with db.get_connection() as conn:
            conn.execute("INSERT INTO chat_history (thread_id, username, mensaje_usuario, respuesta_ia) VALUES (?,?,?,?)", (tid, user, msg, resp))
            conn.commit()