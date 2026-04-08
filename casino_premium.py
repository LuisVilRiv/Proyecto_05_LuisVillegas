import flet as ft
import hashlib
import json
import re
import traceback
from pathlib import Path
from secciones.models import Jugador, PersistenciaCasino

# -------------------------------
# CONFIGURACIÓN Y CONSTANTES
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "casino_data.json"
AUTH_FILE = DATA_DIR / "casino_auth.json"

COLORS = {
    "bg_dark": "#05070A",
    "bg_card": "#0F1626",
    "gold": "#F5B042",
    "gold_hover": "#D4AF37",
    "emerald": "#10B981",
    "crimson": "#E53E3E",
    "text_primary": "#F3F4F6",
    "text_secondary": "#9CA3AF",
    "glass_bg": "#1A202C99",
}

SECURITY_QUESTIONS = [
    "¿Nombre de tu primera mascota?",
    "¿Ciudad donde naciste?",
    "¿Nombre de tu escuela primaria?",
    "¿Modelo de tu primer coche?",
    "¿Nombre de tu héroe de la infancia?"
]

# -------------------------------
# COMPONENTES PREMIUM
# -------------------------------
def create_neon_button(text, on_click, width=350, height=55):
    # Usamos FilledButton que es el estándar moderno
    return ft.FilledButton(
        content=ft.Text(text, weight="bold", size=16),
        on_click=on_click,
        width=width, height=height,
        bgcolor=COLORS["gold"],
        color=COLORS["bg_dark"],
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=15),
            overlay_color={ft.ControlState.HOVERED: COLORS["gold_hover"]},
        )
    )

def validate_password(password):
    if len(password) < 8: return False, "Mínimo 8 caracteres"
    if not re.search(r"\d", password): return False, "Falta un número"
    if not re.search(r"[@$!%*#?&]", password): return False, "Falta un símbolo (@$!%*#?&)"
    return True, ""

# -------------------------------
# APLICACIÓN PRINCIPAL
# -------------------------------
def main(page: ft.Page):
    print("DEBUG: Iniciando aplicación...")
    
    # --- CONFIGURACIÓN DE PÁGINA ---
    page.title = "Casino Royale Premium"
    page.bgcolor = COLORS["bg_dark"]
    page.window.width = 1100
    page.window.height = 800
    # Eliminado center() para evitar Warnings de corrutinas en modo síncrono
    page.theme = ft.Theme(font_family="Outfit")
    page.padding = 0
    page.spacing = 0
    
    storage = PersistenciaCasino(str(DATA_FILE))
    
    def load_auth():
        if not AUTH_FILE.exists(): return {"users": {}}
        try: return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        except: return {"users": {}}
    
    auth_data = load_auth()

    def save_auth():
        DATA_DIR.mkdir(exist_ok=True)
        AUTH_FILE.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")

    def show_message(text, color=COLORS["gold"]):
        print(f"MSG: {text}")
        sb = ft.SnackBar(ft.Text(text, weight="bold"), bgcolor=color)
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def render_auth_container(content):
        page.clean()
        layout = ft.Container(
            expand=True,
            gradient=ft.RadialGradient(
                center=ft.Alignment(0, 0),
                radius=1.5,
                colors=[COLORS["gold"] + "11", COLORS["bg_dark"]],
            ),
            content=ft.Column([
                ft.Container(
                    content=content,
                    width=450,
                    bgcolor=COLORS["glass_bg"],
                    border_radius=30,
                    blur=ft.Blur(10, 10, ft.BlurStyle.OUTER),
                    border=ft.Border.all(1, "#FFFFFF22"),
                    padding=40,
                )
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER
        )
        page.add(layout)
        page.update()

    def show_login(e=None):
        print("DEBUG: Mostrando pantalla de Login")
        user_input = ft.TextField(label="Usuario", prefix_icon=ft.Icons.PERSON, border_color=COLORS["gold"], width=350, border_radius=15)
        pass_input = ft.TextField(label="Contraseña", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True, border_color=COLORS["gold"], width=350, border_radius=15)

        def login_handler(e):
            try:
                username = user_input.value.strip()
                password = pass_input.value.strip()
                print(f"DEBUG: Intentando login para '{username}'")
                
                if not username:
                    show_message("Ingresa un usuario")
                    return

                users = auth_data.get("users", {})
                if username not in users:
                    print(f"DEBUG: Usuario '{username}' no existe")
                    show_register_prompt(username)
                    return

                user_data = users[username]
                stored_hash = user_data if isinstance(user_data, str) else user_data.get("hash")
                
                if hashlib.sha256(password.encode()).hexdigest() == stored_hash:
                    print(f"DEBUG: Login EXITOSO")
                    page.session.store.set("jugador", storage.cargar_jugador(username))
                    show_dashboard()
                else:
                    print(f"DEBUG: Contraseña INCORRECTA")
                    show_message("Contraseña incorrecta", COLORS["crimson"])
            except Exception as ex:
                print(f"ERROR EN LOGIN: {ex}")
                traceback.print_exc()

        def show_register_prompt(tried_name):
            dlg = ft.AlertDialog(
                title=ft.Text("Usuario no encontrado"),
                content=ft.Text(f"¿Quieres crear una cuenta para '{tried_name}'?"),
                actions=[
                    ft.TextButton("No", on_click=lambda _: (setattr(dlg, "open", False), page.update())),
                    ft.TextButton("Sí, registrar", on_click=lambda _: (setattr(dlg, "open", False), show_register()))
                ]
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        ui = ft.Column([
            ft.Text("🎰", size=60),
            ft.Text("CASINO ROYALE", size=32, weight="bold", color=COLORS["gold"]),
            ft.Divider(height=40, color="transparent"),
            user_input, pass_input,
            ft.TextButton("¿Problemas con tu clave?", on_click=show_recovery, style=ft.ButtonStyle(color=COLORS["text_secondary"])),
            ft.Divider(height=20, color="transparent"),
            create_neon_button("ENTRAR AL CASINO", on_click=login_handler),
            ft.TextButton("NUEVO JUGADOR", on_click=show_register, style=ft.ButtonStyle(color=COLORS["gold"]))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        render_auth_container(ui)

    def show_register(e=None):
        print("DEBUG: Entrando a pantalla de registro")
        reg_user = ft.TextField(label="Usuario", border_color=COLORS["gold"], width=350, border_radius=15)
        reg_pass = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, border_color=COLORS["gold"], width=350, border_radius=15)
        reg_secret_q = ft.Dropdown(label="Pregunta de Seguridad", options=[ft.dropdown.Option(q) for q in SECURITY_QUESTIONS], width=350, border_radius=15)
        reg_secret_a = ft.TextField(label="Respuesta", border_color=COLORS["gold"], width=350, border_radius=15)

        def register_handler(e):
            try:
                username = reg_user.value.strip()
                password = reg_pass.value.strip()
                question = reg_secret_q.value
                answer = reg_secret_a.value.strip().lower()

                if not all([username, password, question, answer]):
                    show_message("Faltan datos", COLORS["crimson"])
                    return
                
                is_valid, error = validate_password(password)
                if not is_valid:
                    show_message(error, COLORS["crimson"])
                    return

                if username in auth_data.get("users", {}):
                    show_message("Ya existe este usuario", COLORS["crimson"])
                    return
                
                auth_data.setdefault("users", {})[username] = {
                    "hash": hashlib.sha256(password.encode()).hexdigest(),
                    "question": question,
                    "answer_hash": hashlib.sha256(answer.encode()).hexdigest()
                }
                save_auth()
                show_message("¡Registrado!", COLORS["emerald"])
                show_login()
            except Exception as ex:
                print(f"ERROR EN REGISTRO: {ex}")

        ui = ft.Column([
            ft.Text("MEMBRESÍA", size=28, weight="bold", color=COLORS["gold"]),
            ft.Divider(height=20, color="transparent"),
            reg_user, reg_pass, reg_secret_q, reg_secret_a,
            ft.Divider(height=20, color="transparent"),
            create_neon_button("OBTENER ACCESO", on_click=register_handler),
            ft.TextButton("Volver", on_click=show_login)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        render_auth_container(ui)

    def show_recovery(e=None):
        recover_user = ft.TextField(label="Usuario", border_color=COLORS["gold"], width=350, border_radius=15)
        
        def start_recovery(e):
            username = recover_user.value.strip()
            users = auth_data.get("users", {})
            if username in users:
                user_data = users[username]
                if isinstance(user_data, dict) and "question" in user_data:
                    show_recovery_step2(username, user_data)
                else: show_message("Sin datos de recuperación", COLORS["crimson"])
            else: show_message("No existe", COLORS["crimson"])

        ui = ft.Column([
            ft.Text("RECUPERAR", size=26, weight="bold", color=COLORS["gold"]),
            recover_user,
            create_neon_button("SIGUIENTE", on_click=start_recovery),
            ft.TextButton("Cancelar", on_click=show_login)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        render_auth_container(ui)

    def show_recovery_step2(username, user_data):
        answer_input = ft.TextField(label=f"Pregunta: {user_data['question']}", width=350, border_radius=15)
        new_pass_input = ft.TextField(label="Nueva Contraseña", password=True, width=350, border_radius=15)

        def reset_handler(e):
            if hashlib.sha256(answer_input.value.strip().lower().encode()).hexdigest() == user_data["answer_hash"]:
                is_valid, error = validate_password(new_pass_input.value.strip())
                if is_valid:
                    auth_data["users"][username]["hash"] = hashlib.sha256(new_pass_input.value.strip().encode()).hexdigest()
                    save_auth()
                    show_message("Reiniciada!", COLORS["emerald"])
                    show_login()
                else: show_message(error, COLORS["crimson"])
            else: show_message("Incorrecto", COLORS["crimson"])

        ui = ft.Column([ft.Text("RESET"), answer_input, new_pass_input, create_neon_button("GUARDAR", on_click=reset_handler)], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        render_auth_container(ui)

    # --- DASHBOARD ---

    def show_dashboard(e=None):
        print("DEBUG: Entrando al Dashboard...")
        try:
            page.clean()
            jugador = page.session.store.get("jugador")
            if not jugador:
                show_login()
                return

            content_container = ft.Container(
                expand=True,
                padding=ft.Padding.only(right=24, top=16, bottom=16),
            )

            active_view = {"key": "dashboard"}

            # --- Nav items ---
            NAV_ITEMS = [
                ("dashboard", ft.Icons.HOME_ROUNDED,      "Inicio"),
                ("caja",      ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, "Caja"),
                ("slots",     ft.Icons.GAMES_ROUNDED,     "Slots"),
                ("ruleta",    ft.Icons.CASINO_ROUNDED,    "Ruleta"),
                ("blackjack", ft.Icons.STYLE_ROUNDED,     "Blackjack"),
            ]

            nav_buttons: dict[str, ft.Container] = {}

            def _make_nav_btn(key, icon, label, active=False):
                bg = COLORS["gold"] + "22" if active else "transparent"
                txt_color = COLORS["gold"] if active else "#9CA3AF"
                border = ft.Border.all(1, COLORS["gold"] + "44") if active else ft.Border.all(1, "transparent")
                btn = ft.Container(
                    key=key,
                    content=ft.Row([
                        ft.Icon(icon, size=20, color=txt_color),
                        ft.Text(label, size=14, color=txt_color, weight="bold" if active else "normal"),
                    ], spacing=12),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    border_radius=12,
                    bgcolor=bg,
                    border=border,
                    animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                    on_click=lambda _, k=key: navigate(k),
                )
                nav_buttons[key] = btn
                return btn

            def _refresh_nav(active_key):
                for k, btn in nav_buttons.items():
                    is_active = k == active_key
                    btn.bgcolor = COLORS["gold"] + "22" if is_active else "transparent"
                    btn.border = ft.Border.all(1, COLORS["gold"] + "44") if is_active else ft.Border.all(1, "transparent")
                    row = btn.content
                    row.controls[0].color = COLORS["gold"] if is_active else "#9CA3AF"
                    row.controls[1].color = COLORS["gold"] if is_active else "#9CA3AF"
                    row.controls[1].weight = "bold" if is_active else "normal"

            def navigate(view_type):
                print(f"DEBUG: Navegando a {view_type}")
                active_view["key"] = view_type
                _refresh_nav(view_type)
                content_container.content = None

                if view_type == "dashboard":
                    content_container.content = _build_home(jugador)
                elif view_type == "slots":
                    from casino_pages.slots_view import SlotsView
                    content_container.content = SlotsView(page, jugador, storage)
                elif view_type == "caja":
                    from casino_pages.caja_view import CajaView
                    content_container.content = CajaView(page, jugador, storage)
                elif view_type == "ruleta":
                    from casino_pages.roulette_view import RouletteView
                    content_container.content = RouletteView(page, jugador, storage)
                elif view_type == "blackjack":
                    from casino_pages.blackjack_view import BlackjackView
                    content_container.content = BlackjackView(page, jugador, storage)
                page.update()

            def _build_home(j):
                saldo_card = ft.Container(
                    content=ft.Column([
                        ft.Text("S A L D O   D I S P O N I B L E", size=11, color="#9CA3AF", weight="bold"),
                        ft.Text(f"${j.saldo:,.2f}", size=52, weight="bold", color=COLORS["emerald"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    bgcolor=COLORS["bg_card"],
                    border_radius=20,
                    padding=ft.Padding.symmetric(horizontal=40, vertical=28),
                    border=ft.Border.all(1, COLORS["emerald"] + "33"),
                    shadow=ft.BoxShadow(blur_radius=30, color="#10B98122"),
                    expand=True,
                )

                def _shortcut(icon, label, key):
                    return ft.Container(
                        content=ft.Column([
                            ft.Icon(icon, size=36, color=COLORS["gold"]),
                            ft.Text(label, size=13, color="#D1D5DB", weight="bold"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        on_click=lambda _, k=key: navigate(k),
                        bgcolor=COLORS["bg_card"],
                        border_radius=16,
                        padding=24,
                        border=ft.Border.all(1, "#FFFFFF11"),
                        width=130, height=110,
                        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
                    )

                shortcuts = ft.Row(
                    [
                        _shortcut(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, "Caja", "caja"),
                        _shortcut(ft.Icons.GAMES_ROUNDED, "Slots", "slots"),
                        _shortcut(ft.Icons.CASINO_ROUNDED, "Ruleta", "ruleta"),
                        _shortcut(ft.Icons.STYLE_ROUNDED, "Blackjack", "blackjack"),
                    ],
                    spacing=16,
                    alignment=ft.MainAxisAlignment.CENTER,
                )

                return ft.Column(
                    [
                        ft.Text(f"¡Bienvenido de vuelta, {j.nombre}! 👋",
                                size=26, weight="bold", color="white"),
                        ft.Divider(height=20, color="transparent"),
                        saldo_card,
                        ft.Divider(height=24, color="transparent"),
                        ft.Text("Acceso Rápido", size=14, color="#9CA3AF", weight="bold"),
                        ft.Divider(height=10, color="transparent"),
                        shortcuts,
                    ],
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                )

            # --- Barra lateral premium ---
            nav_col = ft.Column(
                [_make_nav_btn(k, ic, lb, k == "dashboard") for k, ic, lb in NAV_ITEMS],
                spacing=4,
            )

            page.lbl_saldo = ft.Text(
                f"${jugador.saldo:,.2f}", size=14, weight="bold", color=COLORS["emerald"]
            )
            avatar_letter = jugador.nombre[0].upper() if jugador.nombre else "U"

            sidebar = ft.Container(
                width=230,
                bgcolor=COLORS["bg_card"],
                padding=ft.Padding.symmetric(horizontal=14, vertical=20),
                border=ft.Border.all(0, "transparent"),
                # Right border only via a Stack trick isn't easy in Flet, so use shadow
                shadow=ft.BoxShadow(blur_radius=24, color="#00000055", offset=ft.Offset(4, 0)),
                content=ft.Column(
                    [
                        # Logo
                        ft.Container(
                            content=ft.Column([
                                ft.Text("🎰", size=36),
                                ft.Text("C A S I N O   R O Y A L E", size=12, weight="bold", color=COLORS["gold"]),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                            padding=ft.Padding.only(bottom=20),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Divider(height=1, color="#FFFFFF11"),
                        ft.Container(height=12),
                        nav_col,
                        ft.Container(expand=True),
                        ft.Divider(height=1, color="#FFFFFF11"),
                        ft.Container(height=10),
                        # Perfil + saldo
                        ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(avatar_letter, weight="bold", size=16),
                                bgcolor=COLORS["gold"], color=COLORS["bg_dark"],
                                radius=18,
                            ),
                            ft.Column([
                                ft.Text(jugador.nombre, size=13, weight="bold", color="white"),
                                page.lbl_saldo,
                            ], spacing=1),
                        ], spacing=10),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=16, color=COLORS["crimson"]),
                                ft.Text("Cerrar Sesión", size=13, color=COLORS["crimson"]),
                            ], spacing=8),
                            on_click=show_login,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                            border_radius=10,
                            bgcolor=COLORS["crimson"] + "11",
                        ),
                    ],
                    expand=True,
                    spacing=0,
                ),
            )

            page.add(ft.Row([sidebar, content_container], expand=True, spacing=0))
            navigate("dashboard")

        except Exception as ex:
            print(f"ERROR EN DASHBOARD: {ex}")
            traceback.print_exc()

    def refresh_balance():
        jugador = page.session.store.get("jugador")
        if jugador and hasattr(page, "lbl_saldo"):
            page.lbl_saldo.value = f"${jugador.saldo:,.2f}"
            page.update()
    page.refresh_balance = refresh_balance

    show_login()

if __name__ == "__main__":
    ft.run(main)
