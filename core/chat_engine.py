class ChatEngine:
    def __init__(self, client):
        self.client = client

    def marcar_como_leido(self, thread_id):
        # Aquí aplicamos la corrección del error anterior
        return self.client.direct_thread_mark_seen(thread_id)