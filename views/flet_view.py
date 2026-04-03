import flet as ft

class PegasusChatView:
    def __init__(self, on_start_click, on_stop_click):
        self.on_start = on_start_click
        self.on_stop = on_stop_click
        
        # Elementos de la UI
        self.log_messages = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True)
        self.status_dot = ft.CircleAvatar(bgcolor=ft.colors.RED, radius=5)
        self.status_text = ft.Text("Desconectado", italic=True)

    def build(self):
        return ft.Column(
            [
                ft.Row([
                    ft.Text("Pegasus Messenger Engine", size=25, weight="bold"),
                    self.status_dot,
                    self.status_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(),
                
                ft.Container(
                    content=self.log_messages,
                    bgcolor=ft.colors.BLACK12,
                    border_radius=10,
                    expand=True,
                ),
                
                ft.Row([
                    ft.ElevatedButton("Iniciar Bot", icon=ft.icons.PLAY_ARROW, on_click=self.on_start, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE),
                    ft.ElevatedButton("Detener", icon=ft.icons.STOP, on_click=self.on_stop, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ],
            expand=True
        )

    def append_log(self, text, page):
        self.log_messages.controls.append(ft.Text(f"[{ft.datetime.datetime.now().strftime('%H:%M:%S')}] {text}"))
        page.update()