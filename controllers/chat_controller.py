import threading # Importamos la librería nativa de Python para crear hilos

class ChatController:
    def __init__(self, view, engine):
        self.view = view
        self.engine = engine
        
        # Conectar señales de la vista a métodos del controlador
        self.view.btn_conectar.clicked.connect(self.iniciar_servicio)

    def iniciar_servicio(self):
        print("Controlador: Iniciando motor de mensajes en segundo plano...")
        
        # 1. Deshabilitamos el botón temporalmente para que el usuario 
        # no haga 10 clics por desesperación y abra 10 motores a la vez.
        self.view.btn_conectar.setEnabled(False)
        self.view.btn_conectar.setText("Conectando...")
        
        # 2. Creamos un hilo secundario (Thread) que ejecutará el motor
        # 'daemon=True' asegura que si cierras la ventana, el motor se apague también.
        hilo_motor = threading.Thread(target=self.engine.start_polling, daemon=True)
        hilo_motor.start()
        
        print("Motor de Instagram ejecutándose de forma segura.")