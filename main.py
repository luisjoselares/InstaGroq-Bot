import flet as ft
import threading
from core.database import db
from core.instagram_engine import InstagramService

insta_service = InstagramService()

def main(page: ft.Page):
    page.title = "Pegasus Social AI"
    page.window_width = 450
    page.window_height = 650
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    titulo = ft.Text("Gestor de IA para Instagram", size=24, weight=ft.FontWeight.BOLD)
    
    # ==========================================
    # 1. PESTAÑA: PANEL DE CONTROL
    # ==========================================
    status_text = ft.Text("Estado: DETENIDO", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)
    log_console = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    
    def write_log(message):
        log_console.controls.append(ft.Text(f"> {message}", size=12, color=ft.Colors.GREEN_200))
        page.update()

    insta_service.set_callback(write_log)

    def toggle_bot(e):
        with db.get_connection() as conn:
            status = conn.execute("SELECT is_active FROM settings LIMIT 1").fetchone()
            current_state = status['is_active'] if status else 0
            new_state = 1 if current_state == 0 else 0
            
            conn.execute("UPDATE settings SET is_active = ?", (new_state,))
            conn.commit()

            if new_state == 1:
                btn_toggle.text = "DETENER BOT"
                btn_toggle.style = ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                status_text.value = "Estado: ACTIVO"
                status_text.color = ft.Colors.GREEN_400
                write_log("Iniciando motor de Instagram...")
                threading.Thread(target=insta_service.start_polling, daemon=True).start()
            else:
                btn_toggle.text = "INICIAR BOT"
                btn_toggle.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                status_text.value = "Estado: DETENIDO"
                status_text.color = ft.Colors.RED_400
                write_log("Bot pausado. Se detendrá al finalizar el ciclo actual.")
                insta_service.stop()
        page.update()

    btn_toggle = ft.ElevatedButton(
        "INICIAR BOT", 
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
        on_click=toggle_bot,
        width=200, height=50
    )

    tab_dashboard = ft.Tab(
        text="Panel de Control",
        icon=ft.Icons.DASHBOARD,
        content=ft.Column([
            ft.Container(height=10),
            ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.Row([btn_toggle], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.Text("Registro de Actividad:", weight=ft.FontWeight.BOLD),
            ft.Container(
                content=log_console,
                border=ft.border.all(1, ft.Colors.WHITE24),
                border_radius=5, padding=10, expand=True
            )
        ])
    )

    # ==========================================
    # 2. PESTAÑA: CONFIGURACIÓN
    # ==========================================
    
    # Recuperar datos actuales para pre-llenar el formulario
    with db.get_connection() as conn:
        config = conn.execute("SELECT * FROM settings LIMIT 1").fetchone()
        if not config:
            # Insertar fila por defecto si no existe
            conn.execute("INSERT INTO settings (insta_user, insta_pass, groq_key, prompt_sistema, is_active) VALUES ('','','','Eres un asistente virtual.',0)")
            conn.commit()
            config = conn.execute("SELECT * FROM settings LIMIT 1").fetchone()

    txt_user = ft.TextField(label="Usuario de Instagram", value=config['insta_user'])
    txt_pass = ft.TextField(label="Contraseña", value=config['insta_pass'], password=True, can_reveal_password=True)
    txt_groq = ft.TextField(label="API Key de Groq", value=config['groq_key'], password=True, can_reveal_password=True)
    txt_prompt = ft.TextField(label="Prompt del Sistema (IA)", value=config['prompt_sistema'], multiline=True, min_lines=4)

    def save_settings(e):
        with db.get_connection() as conn:
            conn.execute('''
                UPDATE settings 
                SET insta_user = ?, insta_pass = ?, groq_key = ?, prompt_sistema = ?
            ''', (txt_user.value, txt_pass.value, txt_groq.value, txt_prompt.value))
            conn.commit()
        
        write_log("¡Configuración guardada en la base de datos!")
        
        # Muestra un pequeño mensaje de éxito nativo
        page.open(ft.SnackBar(ft.Text("Configuración guardada exitosamente")))
        page.update()

    btn_save = ft.ElevatedButton("Guardar Configuración", on_click=save_settings, icon=ft.Icons.SAVE)

    tab_config = ft.Tab(
        text="Ajustes",
        icon=ft.Icons.SETTINGS,
        content=ft.Column([
            ft.Container(height=10),
            txt_user,
            txt_pass,
            txt_groq,
            txt_prompt,
            ft.Container(height=10),
            ft.Row([btn_save], alignment=ft.MainAxisAlignment.END)
        ], scroll=ft.ScrollMode.AUTO)
    )

    # ==========================================
    # 3. RENDERIZADO PRINCIPAL
    # ==========================================
    
    # Reseteo de seguridad al abrir la app
    with db.get_connection() as conn:
        conn.execute("UPDATE settings SET is_active = 0")
        conn.commit()

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[tab_dashboard, tab_config],
        expand=1,
    )

    write_log("Sistema inicializado.")

    page.add(
        ft.Column([
            titulo,
            ft.Divider(),
            tabs
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)