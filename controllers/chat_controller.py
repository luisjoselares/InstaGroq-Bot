class ChatController:
    def __init__(self, view, engine):
        self.view = view
        self.engine = engine
        
        # Conectar señales de la vista a métodos del controlador
        self.view.btn_conectar.clicked.connect(self.iniciar_servicio)

    def iniciar_servicio(self):
        print("Controlador: Iniciando motor de mensajes...")
        # Aquí llamarías a los métodos de self.engine