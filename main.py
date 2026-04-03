import sys
import logging
from PyQt6.QtWidgets import QApplication

# Importaciones corregidas para coincidir con tus archivos y clases reales
from views.chat_views import ChatWindow
from core.instagram_engine import InstagramService
from controllers.chat_controller import ChatController

def main():
    # Configuración básica de logs
    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)

    # 1. Instanciamos la Vista (UI)
    vista = ChatWindow()

    # 2. Instanciamos el Modelo/Motor con el nombre correcto
    motor = InstagramService()

    # 3. Usamos el controlador correcto que hace match con los botones de la vista
    controlador = ChatController(vista, motor)

    vista.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()