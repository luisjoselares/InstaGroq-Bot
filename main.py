import sys
import logging
from PyQt6.QtWidgets import QApplication

# Importamos las piezas siguiendo tu estructura modular
from views.main_view import ChatWindow
from core.instagram_engine import InstagramEngine
from controllers.main_controller import MainController

def main():
    # Configuración básica de logs para ver el error del motor si ocurre
    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)

    # 1. Instanciamos la Vista (UI)
    vista = ChatWindow()

    # 2. Instanciamos el Modelo/Motor (Lógica de Instagram)
    # Aquí es donde vive la corrección del 'direct_thread_mark_seen'
    motor = InstagramEngine()

    # 3. El Controlador une a ambos
    # Le pasamos la vista y el motor para que los gestione
    controlador = MainController(vista, motor)

    vista.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()