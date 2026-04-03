from PyQt6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("InstaGroq Bot Control")
        self.resize(300, 150)
        
        # Crear un widget central y un layout vertical
        widget_central = QWidget()
        layout = QVBoxLayout()
        
        # Definir botones
        self.btn_conectar = QPushButton("Conectar Motor", self)
        self.btn_desconectar = QPushButton("Detener Motor", self)
        self.btn_desconectar.setEnabled(False) # Apagado por defecto hasta que conectes
        
        # Agregar al layout
        layout.addWidget(self.btn_conectar)
        layout.addWidget(self.btn_desconectar)
        
        widget_central.setLayout(layout)
        self.setCentralWidget(widget_central)