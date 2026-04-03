from PyQt6.QtWidgets import QMainWindow, QPushButton

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.btn_conectar = QPushButton("Conectar Motor", self)
        # No ponemos lógica aquí, solo definimos la interfaz.