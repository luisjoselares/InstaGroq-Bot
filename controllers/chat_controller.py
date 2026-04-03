import threading

class ChatController:
    def __init__(self, view, engine):
        self.view = view
        self.engine = engine
        
        # Conectamos ambos botones
        self.view.btn_conectar.clicked.connect(self.iniciar_servicio)
        self.view.btn_desconectar.clicked.connect(self.detener_servicio)

    def iniciar_servicio(self):
        print("Controlador: Iniciando motor de mensajes en segundo plano...")
        self.view.btn_conectar.setEnabled(False)
        self.view.btn_desconectar.setEnabled(True) # Habilitamos el botón de detener
        self.view.btn_conectar.setText("Motor Corriendo...")
        
        hilo_motor = threading.Thread(target=self.engine.start_polling, daemon=True)
        hilo_motor.start()

    def detener_servicio(self):
        print("Controlador: Deteniendo el motor de manera segura...")
        self.engine.stop() # Cambia is_running a False de forma limpia
        
        # Restauramos la interfaz visual
        self.view.btn_conectar.setEnabled(True)
        self.view.btn_desconectar.setEnabled(False)
        self.view.btn_conectar.setText("Conectar Motor")