import flet as ft
import threading
from core.instagram_engine import InstagramService
from core.database import db
from views.flet_view import PegasusChatView

def main(page: ft.Page):
    page.title = "Pegasus ERP - Instagram Module"
    page.theme_mode = ft.ThemeMode.DARK
    # Ensanchamos un poco más la ventana para que quepan los 3 inputs
    page.window.width = 850 
    page.window.height = 600

    # 1. Instanciamos el Motor
    motor = InstagramService()

    # 2. Funciones de control
    def iniciar_motor(e):
        view.status_dot.bgcolor = ft.Colors.GREEN
        view.status_text.value = "Ejecutando..."
        view.append_log("Iniciando motor de Instagram...", page)
        
        # Ejecutar en hilo para no bloquear la UI
        thread = threading.Thread(target=motor.start_polling, daemon=True)
        thread.start()
        page.update()

    def detener_motor(e):
        motor.stop()
        view.status_dot.bgcolor = ft.Colors.RED
        view.status_text.value = "Detenido"
        view.append_log("Orden de detención enviada.", page)
        page.update()

    def guardar_credenciales(e):
        usuario = view.txt_user.value.strip()
        clave = view.txt_pass.value.strip()
        groq_key = view.txt_groq.value.strip()
        
        if not usuario or not clave or not groq_key:
            view.append_log("⚠️ Error: Todos los campos de configuración son obligatorios.", page)
            return
            
        # Actualizamos la base de datos con los 3 valores
        db.update_credentials(usuario, clave, groq_key)
        view.append_log("✅ Configuración guardada exitosamente en la base de datos.", page)

    # 3. Instanciamos la Vista
    view = PegasusChatView(iniciar_motor, detener_motor, guardar_credenciales)
    
    # 4. Cargar credenciales previas si existen en la BD
    credenciales = db.get_credentials()
    if credenciales:
        if credenciales['insta_user']:
            view.txt_user.value = credenciales['insta_user']
            view.txt_pass.value = credenciales['insta_pass']
        if credenciales['groq_key']:
            view.txt_groq.value = credenciales['groq_key']

    page.add(view.build())

    # 5. Conectamos los logs del motor para que aparezcan en la UI
    motor.set_callback(lambda msg: view.append_log(msg, page))

if __name__ == "__main__":
    ft.app(target=main)