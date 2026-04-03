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
            # Validación mejorada para el error de credenciales
            if not config or not config['insta_user'] or not config['insta_pass']:
                raise ValueError("Credenciales de Instagram no configuradas en la base de datos.")
            user, pw = config['insta_user'], config['insta_pass']

        # 1. Intentar cargar sesión existente
        if os.path.exists(self.session_file):
            try:
                self.cl.load_settings(self.session_file)
                # IMPORTANTE: Verificamos si la sesión funciona SIN hacer login()
                self.cl.get_timeline_feed() 
                self._ui_log("Sesión recuperada exitosamente.")
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
        except Exception as e:
            # --- SOLUCIÓN PROBLEMA 1 APLICADA AQUÍ ---
            # Atrapamos la excepción 'e' y la enviamos a la interfaz visual (Flet)
            self._ui_log(f"⚠️ ERROR FATAL AL INICIAR: {str(e)}")
            self._ui_log("❌ El motor se ha detenido. Revisa la configuración.")
            self.is_running = False
            return
            # -----------------------------------------

        self._ui_log("Motor en línea. Iniciando monitoreo de bandeja de entrada...")
        ciclos_sin_mensajes = 0

        while self.is_running:
            try:
                with db.get_connection() as conn:
                    status = conn.execute("SELECT is_active FROM settings").fetchone()
                    if not status or status['is_active'] == 0:
                        time.sleep(5)
                        continue

                hay_mensajes_nuevos = False
                hilos_a_procesar = []

                # 1. Bandeja Principal
                try:
                    main_threads = self.cl.direct_threads(amount=10)
                    hilos_a_procesar.extend(main_threads)
                except Exception as e:
                    logging.warning(f"Error al leer bandeja principal: {e}")

                # 2. Bandeja de Solicitudes (Gente que no te sigue)
                try:
                    pending_threads = self.cl.direct_pending_inbox()
                    if pending_threads:
                        hilos_a_procesar.extend(pending_threads)
                except Exception as e:
                    logging.warning(f"Error al leer bandeja de solicitudes: {e}")

                # 3. Procesamos todos los hilos encontrados
                for thread in hilos_a_procesar:
                    try:
                        if not thread.messages: continue
                        last_msg = thread.messages[0]
                        
                        if last_msg.user_id == self.cl.user_id: continue
                        
                        hay_mensajes_nuevos = True
                        ciclos_sin_mensajes = 0
                        
                        # Modo Manual / Pánico
                        if self._requires_human(thread.id): continue
                        if self._check_panic_keywords(last_msg.text):
                            self._handoff_to_human(thread.id, thread.users[0].username)
                            continue

                        self._ui_log(f"Recibiendo mensaje de @{thread.users[0].username}...")
                        
                        # Generamos la respuesta
                        respuesta = self.ai.generate_response(last_msg.text, thread.id)
                        
                        # Tiempo de 'Escribiendo...'
                        time.sleep(random.uniform(3, 6))
                        
                        # Si el mensaje estaba en solicitudes, direct_send lo aprobará automáticamente
                        self.cl.direct_send(respuesta, thread_ids=[thread.id])
                        self.cl.direct_thread_mark_seen(thread.id)
                        
                        self._ui_log(f"Respuesta enviada a @{thread.users[0].username}.")
                        self._log_interaction(thread.id, thread.users[0].username, last_msg.text, respuesta)

                    except Exception as thread_error:
                        logging.error(f"Error aislado en chat {thread.id}: {thread_error}")
                        continue

                # Aviso visual para la interfaz
                if not hay_mensajes_nuevos:
                    ciclos_sin_mensajes += 1
                    if ciclos_sin_mensajes % 3 == 0:
                        self._ui_log("Monitoreando... (Sin mensajes nuevos)")

            except FeedbackRequired:
                self._ui_log("¡Feedback Required! Instagram detectó mucha actividad. Pausando 5 min...")
                time.sleep(300)
            except Exception as e:
                logging.error(f"Error crítico en motor principal: {e}")
            
            # Delay maestro
            time.sleep(random.uniform(12, 22))

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
            
        self.cl.direct_send("Pausé mis respuestas. Un humano te atenderá.", thread_ids=[tid])
        self._ui_log(f"Handoff manual activado para @{user}")

    def _log_interaction(self, tid, user, msg, resp):
        with db.get_connection() as conn:
            conn.execute("INSERT INTO chat_history (thread_id, username, mensaje_usuario, respuesta_ia) VALUES (?,?,?,?)", (tid, user, msg, resp))
            conn.commit()