import flet as ft
from datetime import datetime

class PegasusChatView:
    def __init__(self, on_start_click, on_stop_click, on_save_creds_click):
        self.on_start = on_start_click
        self.on_stop = on_stop_click
        self.on_save_creds = on_save_creds_click
        
        # Elementos visuales base
        self.log_messages = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True)
        self.status_dot = ft.CircleAvatar(bgcolor=ft.Colors.RED, radius=5)
        self.status_text = ft.Text("Desconectado", italic=True)
        
        # --- Formulario de Configuración (Actualizado con Groq Key) ---
        self.txt_user = ft.TextField(label="Usuario IG", width=180, text_size=13)
        self.txt_pass = ft.TextField(label="Contraseña IG", password=True, can_reveal_password=True, width=180, text_size=13)
        self.txt_groq = ft.TextField(label="Groq API Key", password=True, can_reveal_password=True, width=220, text_size=13)
        self.btn_save_creds = ft.ElevatedButton("Guardar Config.", icon=ft.Icons.SAVE, on_click=self.on_save_creds, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)

    def build(self):
        return ft.Column(
            [
                ft.Row([
                    ft.Text("Pegasus Messenger Engine", size=25, weight="bold"),
                    self.status_dot,
                    self.status_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(),
                
                # --- SECCIÓN DE CONFIGURACIÓN ---
                ft.Row([
                    self.txt_user,
                    self.txt_pass,
                    self.txt_groq,
                    self.btn_save_creds
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                
                ft.Divider(),
                
                ft.Container(
                    content=self.log_messages,
                    bgcolor=ft.Colors.BLACK12,
                    border_radius=10,
                    expand=True,
                ),
                
                ft.Row([
                    ft.ElevatedButton("Iniciar Bot", icon=ft.Icons.PLAY_ARROW, on_click=self.on_start, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                    ft.ElevatedButton("Detener", icon=ft.Icons.STOP, on_click=self.on_stop, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ],
            expand=True
        )

    def append_log(self, text, page):
        hora_actual = datetime.now().strftime('%H:%M:%S')
        self.log_messages.controls.append(ft.Text(f"[{hora_actual}] {text}"))
        page.update()