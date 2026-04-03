import time
import random
import logging
import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from core.database import db
from core.ai_engine import AIService

class InstagramService:
    def __init__(self):
        self.cl = Client()
        self.ai = AIService()
        self.is_running = False
        self.session_file = "sessions/insta_session.json"
        self.log_callback = None
        # Aseguramos que la carpeta de sesiones exista
        os.makedirs("sessions", exist_ok=True)

    def set_callback(self, callback_func):
        """Permite que la UI le pase su función de imprimir logs"""
        self.log_callback = callback_func
    
    def _ui_log(self, mensaje):
        """Imprime en consola y envía a la interfaz si está conectada"""
        logging.info(mensaje) # Mantiene el log de consola
        if self.log_callback:
            self.log_callback(mensaje)

    def _get_credentials(self):
        """Obtiene el usuario y clave de la base de datos local"""
        with db.get_connection() as conn:
            config = conn.execute("SELECT insta_user, insta_pass FROM settings LIMIT 1").fetchone()
            if not config or not config['insta_user'] or not config['insta_pass']:
                raise ValueError("Credenciales de Instagram no configuradas.")
            return config['insta_user'], config['insta_pass']

    def login(self):
        """Inicia sesión utilizando caché para evitar bloqueos"""
        username, password = self._get_credentials()
        
        try:
            # Intentamos cargar la sesión guardada
            if os.path.exists(self.session_file):
                self.cl.load_settings(self.session_file)
                self.cl.login(username, password)
                logging.info("Sesión recuperada desde archivo local.")
            else:
                self.cl.login(username, password)
                self.cl.dump_settings(self.session_file)
                logging.info("Nuevo inicio de sesión exitoso. Sesión guardada.")
                
        except LoginRequired:
            logging.warning("Sesión expirada. Forzando re-login...")
            self.cl.login(username, password, relogin=True)
            self.cl.dump_settings(self.session_file)
        except Exception as e:
            logging.error(f"Error crítico en login: {e}")
            raise e

    def start_polling(self):
        """Bucle principal que vigila los mensajes"""
        self.is_running = True
        self.login()
        logging.info("Bot de Instagram iniciado. Escuchando mensajes...")

        while self.is_running:
            try:
                # Revisar si el bot fue apagado desde la interfaz
                with db.get_connection() as conn:
                    status = conn.execute("SELECT is_active FROM settings LIMIT 1").fetchone()
                    if status and status['is_active'] == 0:
                        logging.info("Bot pausado desde la interfaz. Esperando...")
                        time.sleep(10)
                        continue

                self._process_unseen_messages()
                
            except Exception as e:
                logging.error(f"Error en el ciclo de escucha: {e}")
            
            # Delay maestro: No saturar los servidores de Meta
            time.sleep(random.uniform(15, 30))

    def stop(self):
        """Detiene el servicio de forma segura"""
        self.is_running = False

    def _process_unseen_messages(self):
        """Procesa hilos con mensajes no leídos"""
        # Obtenemos los hilos (chats) que tienen mensajes sin leer
        threads = self.cl.direct_threads(amount=10, selected_filter="unread")
        
        for thread in threads:
            last_msg = thread.messages[0]
            thread_id = thread.id
            user_id = last_msg.user_id
            text = last_msg.text
            username = thread.users[0].username if thread.users else str(user_id)

            # 1. Evitar respondernos a nosotros mismos
            if user_id == self.cl.user_id:
                continue

            # 2. Verificar si este chat requiere intervención humana
            if self._requires_human(thread_id):
                logging.info(f"Ignorando hilo {thread_id} - Modo manual activado.")
                continue

            # 3. Detectar palabras clave para "Botón de Pánico"
            if self._check_panic_keywords(text, thread_id):
                self._handoff_to_human(thread_id, username)
                continue

            # 4. Comportamiento Humano: Marcar como visto y "pensar"
            self.cl.direct_thread_mark_unread(thread.id, False)
            time.sleep(random.uniform(2, 6)) # Simulamos que estamos leyendo

            # 5. Inteligencia Artificial (El Cerebro)
            respuesta = self.ai.generate_response(text, thread_id)

            # 6. Simulamos el tiempo que tarda en escribir
            tiempo_escritura = len(respuesta) / 15 # Asumiendo 15 caracteres por segundo
            time.sleep(min(tiempo_escritura, 8)) # Máximo 8 segundos de espera
            
            # 7. Enviamos el mensaje
            self.cl.direct_send(respuesta, thread_ids=[thread.id])
            
            # 8. Guardamos en la Base de Datos
            self._log_interaction(thread_id, username, text, respuesta)
            
            # Delay entre clientes
            time.sleep(random.uniform(5, 10))

    # --- Métodos Auxiliares de Lógica de Negocio ---

    def _requires_human(self, thread_id):
        """Consulta en SQLite si este chat está pausado para el bot"""
        with db.get_connection() as conn:
            status = conn.execute("SELECT status FROM chat_status WHERE thread_id = ?", (thread_id,)).fetchone()
            return status and status['status'] == 'PAUSED'

    def _check_panic_keywords(self, text, thread_id):
        """Detecta si el usuario quiere hablar con una persona real"""
        keywords = ["humano", "asesor", "persona", "ayuda", "representante", "agente"]
        return any(keyword in text.lower() for keyword in keywords)

    def _handoff_to_human(self, thread_id, username):
        """Pausa el bot para este chat y avisa al dueño"""
        # Actualizamos o insertamos el estado del hilo a PAUSED
        with db.get_connection() as conn:
            conn.execute('''
                INSERT INTO chat_status (thread_id, status, last_interaction) 
                VALUES (?, 'PAUSED', CURRENT_TIMESTAMP)
                ON CONFLICT(thread_id) DO UPDATE SET status = 'PAUSED', last_interaction = CURRENT_TIMESTAMP
            ''', (thread_id,))
            conn.commit()

        # Mensaje de despedida del bot
        msg_despedida = "Entendido. He pausado mis respuestas automáticas y un asesor humano te atenderá a la brevedad posible."
        self.cl.direct_send(msg_despedida, thread_ids=[thread_id])
        
        logging.warning(f"¡Atención requerida! @{username} ha solicitado un humano.")
        # Aquí más adelante conectaremos el webhook para notificar al celular del cliente.

    def _log_interaction(self, thread_id, username, user_msg, ai_msg):
        """Guarda la conversación en SQLite para la memoria del bot y analíticas"""
        with db.get_connection() as conn:
            conn.execute('''
                INSERT INTO chat_history (thread_id, username, mensaje_usuario, respuesta_ia)
                VALUES (?, ?, ?, ?)
            ''', (thread_id, username, user_msg, ai_msg))
            conn.commit()