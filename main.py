import flet as ft
import threading
from core.instagram_engine import InstagramService
from views.flet_view import PegasusChatView

def main(page: ft.Page):
    page.title = "Pegasus ERP - Instagram Module"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Actualizado a la nueva API de Flet para ventanas
    page.window.width = 600
    page.window.height = 500

    # 1. Instanciamos el Motor
    motor = InstagramService()

    # 2. Funciones de control
    def iniciar_motor(e):
        view.status_dot.bgcolor = ft.Colors.GREEN # Actualizado
        view.status_text.value = "Ejecutando..."
        view.append_log("Iniciando motor de Instagram...", page)
        
        # Ejecutar en hilo para no bloquear la UI
        thread = threading.Thread(target=motor.start_polling, daemon=True)
        thread.start()
        page.update()

    def detener_motor(e):
        motor.stop()
        view.status_dot.bgcolor = ft.Colors.RED # Actualizado
        view.status_text.value = "Detenido"
        view.append_log("Orden de detención enviada.", page)
        page.update()

    # 3. Instanciamos la Vista y la añadimos a la página
    view = PegasusChatView(iniciar_motor, detener_motor)
    page.add(view.build())

    # 4. Conectamos los logs del motor para que aparezcan en la UI
    motor.set_callback(lambda msg: view.append_log(msg, page))

if __name__ == "__main__":
    ft.app(target=main)