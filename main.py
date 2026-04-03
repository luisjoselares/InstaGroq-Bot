import flet as ft
import threading
from core.database import db
from core.instagram_engine import InstagramService

# Instancia global del servicio
insta_service = InstagramService()

def main(page: ft.Page):
    page.title = "InstaGroq - Pegasus AI"
    page.window_width = 450
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    titulo = ft.Text("Gestor de IA para Instagram", size=24, weight=ft.FontWeight.BOLD)
    
    # --- 1. CONFIGURACIÓN DE LOGS ---
    log_console = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    
    def write_log(message):
        # Corregido a ft.Colors
        log_console.controls.append(ft.Text(f"> {message}", size=12, color=ft.Colors.GREEN_200))
        page.update()

    insta_service.set_callback(write_log)

    # --- 2. ELEMENTOS DEL DASHBOARD ---
    # Corregido a ft.Colors
    status_text = ft.Text("Estado: DETENIDO", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD)

    def toggle_bot(e):
        with db.get_connection() as conn:
            status = conn.execute("SELECT is_active FROM settings LIMIT 1").fetchone()
            current_state = status['is_active'] if status else 0
            new_state = 1 if current_state == 0 else 0
            
            conn.execute("UPDATE settings SET is_active = ?", (new_state,))
            conn.commit()

            if new_state == 1:
                btn_toggle.text = "DETENER BOT"
                # Corregido a ft.Colors
                btn_toggle.style = ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                status_text.value = "Estado: ACTIVO"
                status_text.color = ft.Colors.GREEN_400
                write_log("Iniciando motor de Instagram...")
                threading.Thread(target=insta_service.start_polling, daemon=True).start()
            else:
                btn_toggle.text = "INICIAR BOT"
                # Corregido a ft.Colors
                btn_toggle.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                status_text.value = "Estado: DETENIDO"
                status_text.color = ft.Colors.RED_400
                write_log("Bot pausado. Deteniendo ciclo...")
                insta_service.stop()
        page.update()

    btn_toggle = ft.ElevatedButton(
        "INICIAR BOT",
        # Corregido a ft.Colors
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
        on_click=toggle_bot,
        width=200,
        height=50
    )

    # --- 3. ELEMENTOS DE AJUSTES ---
    with db.get_connection() as conn:
        config = conn.execute("SELECT * FROM settings LIMIT 1").fetchone()
        if not config:
            conn.execute("INSERT INTO settings (insta_user, insta_pass, groq_key, prompt_sistema, is_active) VALUES ('','','','Eres un asistente virtual.',0)")
            conn.commit()
            config = conn.execute("SELECT * FROM settings LIMIT 1").fetchone()

    txt_user = ft.TextField(label="Usuario de Instagram", value=config['insta_user'])
    txt_pass = ft.TextField(label="Contraseña", value=config['insta_pass'], password=True, can_reveal_password=True)
    txt_groq = ft.TextField(label="API Key de Groq", value=config['groq_key'], password=True, can_reveal_password=True)
    txt_prompt = ft.TextField(label="Prompt del Sistema", value=config['prompt_sistema'], multiline=True, min_lines=3)

    def save_settings(e):
        with db.get_connection() as conn:
            conn.execute('''
                UPDATE settings SET insta_user=?, insta_pass=?, groq_key=?, prompt_sistema=?
            ''', (txt_user.value, txt_pass.value, txt_groq.value, txt_prompt.value))
            conn.commit()
        
        page.overlay.append(ft.SnackBar(ft.Text("Configuración guardada exitosamente"), open=True))
        write_log("Configuración actualizada.")
        page.update()

    # Corregido a ft.Icons
    btn_save = ft.ElevatedButton("Guardar Configuración", on_click=save_settings, icon=ft.Icons.SAVE)

    # --- 4. CONTENEDORES DE VISTA ---
    
    content_dashboard = ft.Column([
        ft.Container(height=10),
        ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=10),
        ft.Row([btn_toggle], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=15),
        ft.Text("Registro de Actividad:", weight=ft.FontWeight.BOLD),
        ft.Container(
            content=log_console,
            # Corregido a ft.Colors y ft.Border (mayúsculas)
            border=ft.Border.all(1, ft.Colors.WHITE24),
            border_radius=10,
            padding=10,
            expand=True
        )
    ], expand=True)

    content_config = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Container(height=10),
            txt_user,
            txt_pass,
            txt_groq,
            txt_prompt,
            ft.Container(height=10),
            ft.Row([btn_save], alignment=ft.MainAxisAlignment.END)
        ], scroll=ft.ScrollMode.AUTO),
        expand=True
    )

    # Contenedor principal dinámico
    main_container = ft.Container(content=content_dashboard, expand=True)

    # --- 5. NAVEGACIÓN CUSTOM ---
    def change_tab(e):
        if e.control.selected_index == 0:
            main_container.content = content_dashboard
        else:
            main_container.content = content_config
        main_container.update()

    # Corregido a ft.Icons
    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Panel de Control"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Ajustes"),
        ],
        on_change=change_tab,
        selected_index=0
    )

    # --- 6. INICIALIZACIÓN DE PÁGINA ---
    with db.get_connection() as conn:
        conn.execute("UPDATE settings SET is_active = 0")
        conn.commit()

    write_log("Sistema listo.")
    
    page.add(
        titulo,
        ft.Divider(),
        main_container,
        nav_bar
    )

if __name__ == "__main__":
    ft.app(target=main)