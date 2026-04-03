class MainController:
    def __init__(self, vista, motor):
        self.vista = vista
        self.motor = motor
        
        # Conectamos señales de la UI a funciones del controlador
        self.vista.boton_actualizar.clicked.connect(self.check_messages)

    def check_messages(self):
        # Lógica para pedirle al motor que busque mensajes
        pass