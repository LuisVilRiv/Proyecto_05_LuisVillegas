from __future__ import annotations

import hashlib
import json
import math
import random
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional, List, Tuple
import threading
from cloud_assets import ensure_dependencies, CloudAssetManager

from secciones.models import Jugador, PersistenciaCasino
from casino_visual_assets import CasinoTableRenderer

# -------------------------------
# CONSTANTES Y DIRECTORIOS
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "casino_data.json"
AUTH_FILE = DATA_DIR / "casino_auth.json"
SETTINGS_FILE = DATA_DIR / "casino_settings.json"
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
SLOTS_SYMBOLS = ["A", "K", "Q", "J", "7", "$", "*"]
SLOTS_PAY = {"A": 2.0, "K": 3.0, "Q": 4.0, "J": 5.0, "7": 8.0, "$": 12.0, "*": 20.0}

# -------------------------------
# WIDGETS PERSONALIZADOS PREMIUM
# -------------------------------
class CasinoTableFrame(tk.Frame):
    """Frame con apariencia de mesa de casino real"""
    def __init__(self, parent, table_type="general", **kwargs):
        super().__init__(parent, bg="#0A0C15", **kwargs)
        self.table_type = table_type
        self.canvas = tk.Canvas(self, bg="#0A0C15", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._draw_table)
        
    def _draw_table(self, event=None):
        """Dibuja la mesa de casino"""
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        
        if w <= 1 or h <= 1:
            return
            
        if self.table_type == "main":
            self._draw_main_table(w, h)
        elif self.table_type == "slots":
            self._draw_slots_table(w, h)
        elif self.table_type == "roulette":
            self._draw_roulette_table(w, h)
        elif self.table_type == "blackjack":
            self._draw_blackjack_table(w, h)
        else:
            self._draw_general_table(w, h)
    
    def _draw_main_table(self, width, height):
        """Dibuja mesa principal del casino"""
        # Tapete principal
        CasinoTableRenderer.create_table_felt(self.canvas, width, height)
        
        # Área de logo central
        self.canvas.create_rectangle(width//2-150, height//2-80, width//2+150, height//2+80,
                                   fill="#1A5F3F", outline="#DAA520", width=3)
        
        # Fichas decorativas
        chip_positions = [
            (50, 50, 100), (width-70, 50, 25), 
            (50, height-70, 500), (width-70, height-70, 5)
        ]
        for x, y, value in chip_positions:
            CasinoTableRenderer.create_poker_chips(self.canvas, x, y, value)
    
    def _draw_slots_table(self, width, height):
        """Dibuja mesa para slots"""
        # Fondo oscuro tipo máquina
        self.canvas.create_rectangle(0, 0, width, height, fill="#1A1A2E", outline="")
        
        # Marco metálico
        self.canvas.create_rectangle(10, 10, width-10, height-10, 
                                   fill="#16213E", outline="#DAA520", width=4)
        
        # Luces decorativas
        for i in range(0, width, 30):
            color = random.choice(["#FFD700", "#FF69B4", "#00CED1", "#FF6347"])
            self.canvas.create_oval(i+5, 5, i+25, 25, fill=color, outline="")
    
    def _draw_roulette_table(self, width, height):
        """Dibuja mesa de ruleta"""
        # Tapete verde especial para ruleta
        self.canvas.create_rectangle(0, 0, width, height, fill="#0F5132", outline="#8B4513", width=6)
        
        # Rueda de ruleta en el centro
        wheel_radius = min(width, height) // 3
        CasinoTableRenderer.create_roulette_wheel(self.canvas, width//2, height//2, wheel_radius)
        
        # Área de apuestas
        self.canvas.create_rectangle(20, height-120, width-20, height-20,
                                   fill="#1A5F3F", outline="#DAA520", width=2)
    
    def _draw_blackjack_table(self, width, height):
        """Dibuja mesa de blackjack"""
        # Tapete ovalado de blackjack
        self.canvas.create_rectangle(0, 0, width, height, fill="#0F5132", outline="#8B4513", width=6)
        
        # Área ovalada central
        cx, cy = width//2, height//2
        w, h = width-60, height-120
        self.canvas.create_oval(cx-w//2, cy-h//2, cx+w//2, cy+h//2,
                               fill="#1A5F3F", outline="#DAA520", width=3)
        
        # Líneas divisorias
        self.canvas.create_line(cx, cy-h//2+20, cx, cy+h//2-20, 
                               fill="#DAA520", width=2, dash=(10, 5))
    
    def _draw_general_table(self, width, height):
        """Dibuja mesa genérica"""
        CasinoTableRenderer.create_table_felt(self.canvas, width, height)


class AnimatedChipWidget(tk.Frame):
    """Widget que muestra fichas animadas"""
    def __init__(self, parent, value=100, **kwargs):
        super().__init__(parent, bg="#0A0C15", **kwargs)
        self.value = value
        self.canvas = tk.Canvas(self, width=60, height=60, bg="#0A0C15", highlightthickness=0)
        self.canvas.pack()
        self._draw_chip()
        
    def _draw_chip(self):
        """Dibuja la ficha"""
        self.canvas.delete("all")
        CasinoTableRenderer.create_poker_chips(self.canvas, 30, 30, self.value)
    
    def animate_win(self):
        """Animación de victoria"""
        positions = CasinoTableRenderer.animate_chip_fall(self.canvas, 30, 0, 30, 30, 15)
        for i, (x, y) in enumerate(positions):
            self.after(i*50, lambda px=x, py=y: self._move_chip(px, py))
        
    def _move_chip(self, x, y):
        """Mueve la ficha a una posición"""
        self.canvas.delete("all")
        CasinoTableRenderer.create_poker_chips(self.canvas, x, y, self.value)


class RoundedFrame(tk.Canvas):
    """Frame con bordes redondeados y fondo de color sólido."""
    def __init__(self, parent, radius=20, bg_color="#111827", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.radius = radius
        self.bg_color = bg_color
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        self.create_round_rectangle(0, 0, w, h, self.radius, fill=self.bg_color, outline="")

    def create_round_rectangle(self, x1, y1, x2, y2, r, **kwargs):
        points = (
            x1+r, y1, x2-r, y1,
            x2, y1, x2, y1+r,
            x2, y2-r, x2, y2,
            x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r,
            x1, y1+r, x1, y1
        )
        return self.create_polygon(points, smooth=True, **kwargs)


class ModernButton(tk.Button):
    """Botón con hover, colores premium y bordes planos elegantes."""
    def __init__(self, parent, text, command, bg_color, hover_color, fg="white", font=None, **kwargs):
        super().__init__(parent, text=text, command=command, bg=bg_color, fg=fg,
                         relief="flat", font=font or ("Segoe UI", 10, "bold"), **kwargs)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.config(cursor="hand2")

    def on_enter(self, e):
        self.config(bg=self.hover_color)

    def on_leave(self, e):
        self.config(bg=self.bg_color)


class AnimatedLabel(tk.Label):
    """Label que anima su color al cambiar el texto (para el saldo)."""
    def __init__(self, parent, colors: dict, **kwargs):
        super().__init__(parent, **kwargs)
        self.colors = colors
        self.normal_color = colors["text_primary"]
        self.animating = False

    def set_value(self, new_value: float, old_value: Optional[float] = None):
        if old_value is not None and new_value != old_value:
            delta = new_value - old_value
            if delta > 0:
                self.config(fg=self.colors["green"])
            elif delta < 0:
                self.config(fg=self.colors["red"])
            self.after(500, lambda: self.config(fg=self.normal_color))
        self.config(text=f"${new_value:,.2f}")


# -------------------------------
# APLICACIÓN PRINCIPAL
# -------------------------------
class CasinoRoyalePro(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Casino Royale Pro")
        self.geometry("1200x750")
        self.minsize(1100, 700)
        self.configure(bg="#0A0C15")

        # Paleta de colores premium
        self.colors = {
            "bg_dark": "#05070A",
            "bg_card": "#0F1626", # Más oscuro para glassmorphism
            "gold": "#F5B042",
            "red": "#E53E3E",
            "green": "#10B981",
            "text_primary": "#F3F4F6",
            "text_secondary": "#9CA3AF",
            "border": "#2D3748",
            "blue_accent": "#3B82F6",
            "blue_hover": "#2563EB"
        }

        # Fuentes
        self.font_title = ("Segoe UI", 32, "bold")
        self.font_subtitle = ("Segoe UI", 16)
        self.font_body = ("Segoe UI", 12)
        self.font_mono = ("Consolas", 11)

        # Datos y persistencia
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.storage = PersistenciaCasino(str(DATA_FILE))
        self.auth_data = self._load_auth()
        self.settings = self._load_settings()
        self.jugador: Optional[Jugador] = None

        self._setup_styles()
        
        # Modo Pantalla Completa Videojuego
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.quit())
        
        # Iniciar Gestor de Assets
        ensure_dependencies()
        self.asset_manager = CloudAssetManager(str(DATA_DIR / "assets"))
        
        self._build_loading_screen()

    # -------------------------------
    # MÉTODOS AUXILIARES (sin cambios funcionales)
    # -------------------------------
    def _load_auth(self) -> dict:
        if not AUTH_FILE.exists():
            return {"users": {}}
        try:
            return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"users": {}}

    def _save_auth(self) -> None:
        AUTH_FILE.write_text(json.dumps(self.auth_data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_settings(self) -> dict:
        default = {"sound": True, "animations": True, "animation_speed_ms": 85}
        if not SETTINGS_FILE.exists():
            return default
        try:
            raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            merged = default.copy()
            merged.update(raw)
            return merged
        except Exception:
            return default

    def _save_settings(self) -> None:
        SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _play_sound(self, event: str = "default") -> None:
        if not self.settings.get("sound", True):
            return
            
        real_sound_keys = {
            "win": "sound_win",
            "tick": "sound_tick",
            "action": "sound_action"
        }
        
        if event in real_sound_keys and self.asset_manager.audio_initialized:
            self.asset_manager.play_sound(real_sound_keys[event])
            return

        if sys.platform.startswith("win"):
            try:
                import winsound
                tones = {
                    "win": (980, 120),
                    "lose": (240, 180),
                    "action": (520, 80),
                    "tick": (1500, 10),
                    "default": (660, 70),
                }
                freq, dur = tones.get(event, tones["default"])
                winsound.Beep(freq, dur)
            except Exception:
                self.bell()
        else:
            self.bell()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background="#111827", foreground="#F3F4F6", fieldbackground="#111827")
        style.configure("Treeview.Heading", background="#1F2937", foreground="#F5B042", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#3B82F6")])

    def _player(self) -> Jugador:
        if self.jugador is None:
            raise RuntimeError("No autenticado")
        return self.jugador

    def _clear(self) -> None:
        for w in self.winfo_children():
            w.destroy()

    # -------------------------------
    # LOGIN Y CARGA
    # -------------------------------
    def _build_loading_screen(self) -> None:
        self._clear()
        bg_canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        bg_canvas.pack(fill="both", expand=True)
        self._create_gradient(bg_canvas, self.winfo_screenwidth(), self.winfo_screenheight(), "#0A0C15", "#1F2937")

        card = RoundedFrame(self, radius=30, bg_color=self.colors["bg_card"])
        card.place(relx=0.5, rely=0.5, anchor="center", width=500, height=300)
        
        tk.Label(card, text="🎰 CASINO ROYALE PRO", font=self.font_title, bg=self.colors["bg_card"], fg=self.colors["gold"]).pack(pady=(40, 10))
        tk.Label(card, text="Descargando activos inmersivos (HQ)...", font=self.font_subtitle, bg=self.colors["bg_card"], fg=self.colors["text_secondary"]).pack(pady=10)

        progress_var = tk.DoubleVar()
        pb = ttk.Progressbar(card, orient="horizontal", length=350, mode="determinate", variable=progress_var, maximum=100)
        pb.pack(pady=20)
        
        lbl_status = tk.Label(card, text="Iniciando...", bg=self.colors["bg_card"], fg=self.colors["text_secondary"], font=self.font_body)
        lbl_status.pack()

        def update_progress(current, total, msg):
            pct = (current / total) * 100
            self.after(0, lambda: progress_var.set(pct))
            self.after(0, lambda: lbl_status.config(text=msg))

        def load_task():
            self.asset_manager.download_assets(update_progress)
            self.after(500, self._build_login)

        threading.Thread(target=load_task, daemon=True).start()

    def _build_login(self) -> None:
        self._clear()
        # Fondo con gradiente oscuro teatral
        bg_canvas = tk.Canvas(self, bg=self.colors["bg_dark"], highlightthickness=0)
        bg_canvas.pack(fill="both", expand=True)
        self._create_gradient(bg_canvas, self.winfo_screenwidth(), self.winfo_screenheight(), "#05070a", "#151b29")

        # Tarjeta redondeada Glassmorfismo
        card = RoundedFrame(self, radius=40, bg_color="#0F1626")
        card.place(relx=0.5, rely=0.5, anchor="center", width=550, height=480)

        # Efecto brillo neón estático en la card
        bg_canvas.create_oval(self.winfo_screenwidth()/2-200, self.winfo_screenheight()/2-200, 
                             self.winfo_screenwidth()/2+200, self.winfo_screenheight()/2+200, 
                             fill="#DAA520", stipple="gray25", outline="")

        # Textos súper-premium
        tk.Label(card, text="👑", font=("Segoe UI", 40), bg="#0F1626", fg=self.colors["gold"]).pack(pady=(20, 0))
        tk.Label(card, text="CASINO ROYALE", font=("Times New Roman", 30, "bold"), bg="#0F1626", fg=self.colors["gold"]).pack()
        tk.Label(card, text="Paso a la exclusividad", font=("Segoe UI", 12, "italic"), bg="#0F1626", fg=self.colors["text_secondary"]).pack(pady=(0, 20))

        # Campos rediseñados minimalistas
        inner_frame = tk.Frame(card, bg="#0F1626")
        inner_frame.pack(fill="x", padx=60)
        
        tk.Label(inner_frame, text="USUARIO", bg="#0F1626", fg=self.colors["text_secondary"], font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.user_var = tk.StringVar()
        entry_user = tk.Entry(inner_frame, textvariable=self.user_var, font=("Segoe UI", 14), bg="#1a2436", fg="#FFF", insertbackground="#F5B042", relief="flat")
        entry_user.pack(fill="x", pady=(5, 15), ipady=5)

        tk.Label(inner_frame, text="CONTRASEÑA", bg="#0F1626", fg=self.colors["text_secondary"], font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.pass_var = tk.StringVar()
        entry_pass = tk.Entry(inner_frame, textvariable=self.pass_var, font=("Segoe UI", 14), bg="#1a2436", fg="#FFF", insertbackground="#F5B042", relief="flat", show="●")
        entry_pass.pack(fill="x", pady=(5, 20), ipady=5)

        entry_user.focus_set()

        # Botones uniformes alineados
        btn_box = tk.Frame(card, bg="#0F1626")
        btn_box.pack(fill="x", padx=60, pady=10)
        
        btn_login = ModernButton(btn_box, text="ENTRAR", command=self._login, bg_color=self.colors["gold"], hover_color="#D4AF37", fg="#000", font=("Segoe UI", 12, "bold"))
        btn_login.pack(side="left", expand=True, fill="x", padx=(0, 5), ipady=8)

        btn_register = ModernButton(btn_box, text="REGISTRAR", command=self._registrar_usuario, bg_color="#1a2436", hover_color="#2D3748", fg="#FFF", font=("Segoe UI", 12, "bold"))
        btn_register.pack(side="right", expand=True, fill="x", padx=(5, 0), ipady=8)

        # Botón Salir Global (Por estar en Fullscreen)
        btn_quit = ModernButton(self, text="✖ SALIR AL ESCRITORIO", command=self.quit, bg_color=self.colors["bg_dark"], hover_color=self.colors["red"], fg=self.colors["text_secondary"])
        btn_quit.place(x=30, y=30, width=180, height=40)

        self.bind("<Return>", lambda _: self._login())

    def _create_gradient(self, canvas, width, height, color1, color2):
        """Dibuja un gradiente vertical en el canvas."""
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)
        for i in range(height):
            ratio = i / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, width, i, fill=color)

    @staticmethod
    def _hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _login(self) -> None:
        username = self.user_var.get().strip()
        password = self.pass_var.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Completa usuario y contraseña.")
            return
        users = self.auth_data.get("users", {})
        if username not in users:
            messagebox.showerror("Error", "Usuario no registrado. Pulsa 'Registrar usuario'.")
            return
        if users[username] != self._hash_password(password):
            self._play_sound("lose")
            messagebox.showerror("Error", "Contraseña incorrecta.")
            return
        self.jugador = self.storage.cargar_jugador(username)
        self._play_sound("action")
        self._build_dashboard()

    def _registrar_usuario(self) -> None:
        username = self.user_var.get().strip()
        password = self.pass_var.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Completa usuario y contraseña para registrar.")
            return
        if len(password) < 4:
            messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres.")
            return
        users = self.auth_data.setdefault("users", {})
        if username in users:
            messagebox.showerror("Error", "Ese usuario ya existe.")
            return
        users[username] = self._hash_password(password)
        self._save_auth()
        self._play_sound("win")
        messagebox.showinfo("Registro", "Usuario registrado correctamente. Ya puedes entrar.")

    # -------------------------------
    # DASHBOARD PRINCIPAL (RENOVADO)
    # -------------------------------
    def _build_dashboard(self) -> None:
        self.unbind("<Return>")
        self._clear()

        # Mesa de casino como fondo principal
        table_frame = CasinoTableFrame(self, table_type="main")
        table_frame.pack(fill="both", expand=True)

        # Contenedor flotante para elementos UI
        ui_container = tk.Frame(table_frame, bg="#0A0C15", highlightthickness=0)
        ui_container.place(relx=0.5, rely=0.5, anchor="center", width=1100, height=650)

        # Sidebar izquierdo con efecto de cristal
        sidebar = RoundedFrame(ui_container, radius=15, bg_color="#1A1A2E")
        sidebar.pack(side="left", fill="y", padx=(10, 15), pady=10)
        sidebar.config(width=240)
        sidebar.pack_propagate(False)

        # Logo y nombre en sidebar con estilo casino
        logo_frame = tk.Frame(sidebar, bg="#1A1A2E")
        logo_frame.pack(pady=(25, 15))
        
        tk.Label(logo_frame, text="🎰", font=("Segoe UI", 24), bg="#1A1A2E", fg=self.colors["gold"]).pack()
        tk.Label(logo_frame, text="CASINO", font=("Segoe UI", 16, "bold"), bg="#1A1A2E", fg=self.colors["gold"]).pack()
        tk.Label(sidebar, text=f"Jugador: {self._player().nombre}", bg="#1A1A2E", fg=self.colors["text_secondary"], font=self.font_body).pack(pady=(0, 20))

        # Fichas animadas en sidebar
        chips_frame = tk.Frame(sidebar, bg="#1A1A2E")
        chips_frame.pack(pady=10)
        for value, color in [(100, "#FFFFFF"), (25, "#FF0000"), (5, "#0000FF")]:
            chip = AnimatedChipWidget(chips_frame, value=value)
            chip.pack(side="left", padx=5)

        # Botones del menú
        menu_items = [
            ("💰 Caja", self.open_caja, self.colors["green"], "#059669"),
            ("🎰 Slots", self.open_slots, self.colors["blue_accent"], self.colors["blue_hover"]),
            ("🎲 Ruleta", self.open_ruleta, self.colors["blue_accent"], self.colors["blue_hover"]),
            ("♠️ Blackjack", self.open_blackjack, self.colors["blue_accent"], self.colors["blue_hover"]),
            ("📜 Historial", self.open_historial, "#4B5563", "#6B7280"),
            ("📊 Estadísticas", self.open_stats, "#4B5563", "#6B7280"),
            ("⚙️ Configuración", self.open_settings, "#4B5563", "#6B7280"),
            ("📄 Exportar reporte", self.exportar_reporte, "#4B5563", "#6B7280"),
            ("🚪 Cerrar sesión", self._build_login, self.colors["red"], "#B91C1C"),
        ]
        for text, cmd, bg, hover in menu_items:
            btn = ModernButton(sidebar, text=text, command=cmd, bg_color=bg, hover_color=hover, fg="white", font=("Segoe UI", 10, "bold"))
            btn.pack(fill="x", padx=14, pady=5, ipady=6)

        # Área principal derecha con efecto de cristal
        right_area = RoundedFrame(ui_container, radius=15, bg_color="#1A1A2E")
        right_area.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        # Header con saldo animado y estado
        header = RoundedFrame(right_area, radius=15, bg_color=self.colors["bg_card"])
        header.pack(fill="x", pady=(0, 10))
        header.config(height=80)
        header.pack_propagate(False)

        # Avatar con inicial
        avatar_canvas = tk.Canvas(header, width=50, height=50, bg=self.colors["bg_card"], highlightthickness=0)
        avatar_canvas.pack(side="left", padx=15, pady=15)
        avatar_canvas.create_oval(5, 5, 45, 45, fill=self.colors["gold"], outline="")
        initial = self._player().nombre[0].upper()
        avatar_canvas.create_text(25, 25, text=initial, fill=self.colors["bg_card"], font=("Segoe UI", 18, "bold"))

        # Saldo
        self.lbl_saldo = AnimatedLabel(header, colors=self.colors, bg=self.colors["bg_card"], font=("Segoe UI", 22, "bold"), fg=self.colors["text_primary"])
        self.lbl_saldo.pack(side="left", padx=10)

        # Estado
        self.lbl_status = tk.Label(header, text="✅ Listo", bg=self.colors["bg_card"], fg=self.colors["text_secondary"], font=self.font_body)
        self.lbl_status.pack(side="right", padx=15)

        # Contenido dinámico (se mostrarán las vistas de juegos aquí, pero mantendré la estructura original)
        self.content_frame = tk.Frame(right_area, bg=self.colors["bg_dark"])
        self.content_frame.pack(fill="both", expand=True)

        # Panel principal de bienvenida (similar al original pero con mejor diseño)
        self._show_welcome_panel()

        self.refresh_dashboard("Bienvenido")

    def _show_welcome_panel(self):
        """Muestra el panel de bienvenida con accesos rápidos y resumen."""
        for w in self.content_frame.winfo_children():
            w.destroy()

        left_panel = RoundedFrame(self.content_frame, radius=20, bg_color=self.colors["bg_card"])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = RoundedFrame(self.content_frame, radius=20, bg_color=self.colors["bg_card"], width=320)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        # Left panel content
        tk.Label(left_panel, text="🏠 Panel Principal", font=("Segoe UI", 18, "bold"), bg=self.colors["bg_card"], fg=self.colors["gold"]).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(left_panel, text="Accesos rápidos a tus juegos favoritos", font=self.font_subtitle, bg=self.colors["bg_card"], fg=self.colors["text_secondary"]).pack(anchor="w", padx=20, pady=(0, 20))

        quick_buttons = [
            ("💰 Depositar", self.open_caja, self.colors["green"]),
            ("🎰 Slots", self.open_slots, self.colors["blue_accent"]),
            ("🎲 Ruleta", self.open_ruleta, self.colors["blue_accent"]),
            ("♠️ Blackjack", self.open_blackjack, self.colors["blue_accent"]),
        ]
        grid_frame = tk.Frame(left_panel, bg=self.colors["bg_card"])
        grid_frame.pack(padx=20, pady=10, anchor="w")
        for i, (text, cmd, color) in enumerate(quick_buttons):
            btn = ModernButton(grid_frame, text=text, command=cmd, bg_color=color, hover_color="#2563EB" if color != self.colors["green"] else "#059669", width=18, height=2, font=("Segoe UI", 11, "bold"))
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

        # Right panel content
        tk.Label(right_panel, text="📈 Resumen de Sesión", font=("Segoe UI", 14, "bold"), bg=self.colors["bg_card"], fg=self.colors["gold"]).pack(anchor="w", padx=15, pady=(20, 10))
        self.lbl_stats = tk.Label(right_panel, text="", bg=self.colors["bg_card"], fg=self.colors["text_primary"], justify="left", font=self.font_mono)
        self.lbl_stats.pack(anchor="w", padx=15)

        tk.Label(right_panel, text="🕒 Últimos movimientos", font=("Segoe UI", 12, "bold"), bg=self.colors["bg_card"], fg=self.colors["text_secondary"]).pack(anchor="w", padx=15, pady=(15, 5))
        self.last_list = tk.Listbox(right_panel, bg="#1F2937", fg=self.colors["text_primary"], selectbackground=self.colors["blue_accent"], borderwidth=0, highlightthickness=0, font=self.font_mono)
        self.last_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def refresh_dashboard(self, status: str = "Listo") -> None:
        p = self._player()
        self.storage.guardar_jugador(p)
        old_saldo = float(self.lbl_saldo.cget("text").replace("$", "").replace(",", "")) if self.lbl_saldo.cget("text") else 0
        self.lbl_saldo.set_value(p.saldo, old_saldo)
        self.lbl_status.config(text=f"✅ {status}")
        s = p.stats
        if hasattr(self, 'lbl_stats'):
            self.lbl_stats.config(
                text=f"🎲 Jugadas:        {s.jugadas}\n"
                     f"💰 Total apostado: ${s.total_apostado:,.2f}\n"
                     f"🏆 Total ganado:   ${s.total_ganado:,.2f}\n"
                     f"📊 Balance sesión: ${s.balance_sesion:+,.2f}"
            )
            self.last_list.delete(0, "end")
            for item in p.historial[-8:]:
                self.last_list.insert("end", f"{item['juego']:<10} {item['balance']:+.2f}")

    # -------------------------------
    # VENTANAS DE JUEGO (con mejora visual)
    # -------------------------------
    def _parse_amount(self, e: ttk.Entry) -> Optional[float]:
        try:
            v = float(e.get().strip())
            if v <= 0:
                raise ValueError
            return v
        except ValueError:
            messagebox.showerror("Error", "Cantidad inválida.")
            return None

    def open_caja(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Caja - Casino Royale Pro")
        w.geometry("450x300")
        w.configure(bg=self.colors["bg_dark"])
        w.resizable(False, False)

        card = RoundedFrame(w, radius=20, bg_color=self.colors["bg_card"])
        card.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(card, text="💰 CAJA", font=("Segoe UI", 18, "bold"), bg=self.colors["bg_card"], fg=self.colors["gold"]).pack(pady=(20, 5))
        tk.Label(card, text=f"Saldo actual: ${p.saldo:,.2f}", bg=self.colors["bg_card"], fg=self.colors["green"], font=("Segoe UI", 14, "bold")).pack(pady=10)

        frame = tk.Frame(card, bg=self.colors["bg_card"])
        frame.pack(pady=15)
        tk.Label(frame, text="Cantidad:", bg=self.colors["bg_card"], fg=self.colors["text_primary"], font=self.font_body).pack(side="left", padx=5)
        e = ttk.Entry(frame, font=("Segoe UI", 12), width=15)
        e.pack(side="left", padx=5)
        e.focus_set()

        def depositar():
            v = self._parse_amount(e)
            if v is None:
                return
            p.depositar(v)
            self._play_sound("action")
            self.refresh_dashboard("Depósito realizado")
            w.destroy()

        def retirar():
            v = self._parse_amount(e)
            if v is None:
                return
            try:
                p.retirar(v)
            except ValueError as err:
                messagebox.showerror("Error", str(err))
                return
            self._play_sound("action")
            self.refresh_dashboard("Retiro realizado")
            w.destroy()

        btn_frame = tk.Frame(card, bg=self.colors["bg_card"])
        btn_frame.pack(pady=20)
        ModernButton(btn_frame, text="DEPOSITAR", command=depositar, bg_color=self.colors["green"], hover_color="#059669", width=12).pack(side="left", padx=10, ipady=4)
        ModernButton(btn_frame, text="RETIRAR", command=retirar, bg_color=self.colors["red"], hover_color="#B91C1C", width=12).pack(side="left", padx=10, ipady=4)

    def open_slots(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Slots Pro - Casino Royale Pro")
        w.attributes("-fullscreen", True) # Modo videojuego
        w.configure(bg=self.colors["bg_dark"])

        # Botón para salir a la sala (por ser fullscreen)
        btn_exit = ModernButton(w, text="✖ SALIR AL LOBBY", command=w.destroy, bg_color="#1a2436", hover_color=self.colors["red"], fg="#FFF")
        btn_exit.place(x=30, y=30, width=180, height=40)
        w.bind("<Escape>", lambda e: w.destroy())

        # Base Cabinet
        cabinet = tk.Canvas(w, bg="#111", highlightthickness=0)
        cabinet.pack(fill="both", expand=True)

        # Draw Machine Body
        def draw_cabinet(*args):
            cabinet.delete("bg")
            cw, ch = w.winfo_width(), w.winfo_height()
            if cw < 10: cw, ch = 1920, 1080
            
            # Casino carpet backdrop
            cabinet.create_rectangle(0,0,cw,ch, fill="#1a0b2e", tags="bg")
            # Machine metallic housing (Scaled massively)
            cabinet.create_rectangle(cw*0.1, ch*0.05, cw*0.9, ch*0.95, fill="#2c3e50", outline="#f39c12", width=12, tags="bg")
            cabinet.create_rectangle(cw*0.15, ch*0.15, cw*0.85, ch*0.65, fill="#000", outline="#c0392b", width=8, tags="bg") # Screen
            # Slot logo
            cabinet.create_text(cw/2, ch*0.1, text="🍒 MEGA ROYALE SLOTS 🍒", fill="#f1c40f", font=("Arial", 48, "bold"), tags="bg")
            # Bottom panel
            cabinet.create_rectangle(cw*0.1, ch*0.75, cw*0.9, ch*0.95, fill="#34495e", outline="#f39c12", width=8, tags="bg")

        cabinet.bind("<Configure>", draw_cabinet)

        SLOTS_SYMBOLS = ["🍒", "🍋", "🔔", "⭐", "💎", "7️⃣"]
        SLOTS_PAY = {"🍒": 2, "🍋": 3, "🔔": 5, "⭐": 10, "💎": 20, "7️⃣": 50}
        
        # Reels Visuals
        reels_frame = tk.Frame(cabinet, bg="#000")
        reels_frame.place(relx=0.5, rely=0.4, anchor="center")
        
        reel_canvases = []
        for i in range(3):
            # Escala grande (2.5x) para abarcar correctamente en fullscreen
            rc = tk.Canvas(reels_frame, width=300, height=450, bg="#ecf0f1", highlightthickness=5, highlightbackground="#bdc3c7")
            rc.pack(side="left", padx=20)
            reel_canvases.append(rc)
            
        def draw_reels_state(board, blur=False):
            for i, rc in enumerate(reel_canvases):
                rc.delete("all")
                col_symbols = [board[0][i], board[1][i], board[2][i]]
                CasinoTableRenderer.create_slot_reel(rc, 20, 20, col_symbols, blur=blur)
                
        current_board = [["🍒", "🍒", "🍒"] for _ in range(3)]
        draw_reels_state(current_board)

        # Panel de Control Centralizado
        control_panel = tk.Frame(cabinet, bg="#34495e")
        control_panel.place(relx=0.5, rely=0.85, anchor="center", relwidth=0.7, height=180)

        self.slot_lines = 1
        self.slot_bet = 10
        self.slot_spinning = False

        lbl_info = tk.Label(control_panel, text="Líneas: 1 | Apuesta: $10 | Total: $10", bg="#34495e", fg="#FFF", font=("Segoe UI", 24, "bold"))
        lbl_info.pack(pady=15)

        btn_box = tk.Frame(control_panel, bg="#34495e")
        btn_box.pack(fill="x", padx=40)

        def set_bet(amt):
            if self.slot_spinning: return
            self.slot_bet = amt
            update_lbl()
            self._play_sound("action")

        def set_lines(ln):
            if self.slot_spinning: return
            self.slot_lines = ln
            update_lbl()
            self._play_sound("action")

        def update_lbl():
            lbl_info.config(text=f"Líneas: {self.slot_lines} | Apuesta: ${self.slot_bet} | Total: ${self.slot_lines * self.slot_bet}")

        # Botones uniformes exactos
        ModernButton(btn_box, text="Línea +1", command=lambda: set_lines(self.slot_lines % 3 + 1), bg_color="#8e44ad", hover_color="#9b59b6", font=("Arial", 16, "bold")).pack(side="left", expand=True, fill="x", padx=5, ipady=15)
        ModernButton(btn_box, text="Bet $10", command=lambda: set_bet(10), bg_color="#2980b9", hover_color="#3498db", font=("Arial", 16, "bold")).pack(side="left", expand=True, fill="x", padx=5, ipady=15)
        ModernButton(btn_box, text="Bet Max", command=lambda: set_bet(100), bg_color="#c0392b", hover_color="#e74c3c", font=("Arial", 16, "bold")).pack(side="left", expand=True, fill="x", padx=5, ipady=15)
        ModernButton(btn_box, text="SPIN", command=lambda: spin(), bg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 20, "bold")).pack(side="left", expand=True, fill="x", padx=10, ipady=15)
        
        lbl_win = tk.Label(cabinet, text="", bg="#000", fg="#f1c40f", font=("Arial", 40, "bold"))
        lbl_win.place(relx=0.5, rely=0.68, anchor="center")

        def finish_spin():
            pay = 0.0
            det = []
            for idx in range(self.slot_lines):
                row = current_board[idx]
                if row[0] == row[1] == row[2]:
                    mult = SLOTS_PAY[row[0]]
                    pay += self.slot_bet * mult
                    det.append(f"Línea {idx+1}")
                    for rc in reel_canvases:
                        rc.create_rectangle(15, 20 + (idx*130), 285, 140 + (idx*130), outline="#f1c40f", width=8)
                        
            total_bet = self.slot_bet * self.slot_lines
            detail = " | ".join(det) if det else "Sin premio"
            p.registrar_jugada("Slots Real", total_bet, pay, detail)
            self._play_sound("win" if pay > 0 else "lose")
            self.refresh_dashboard("Slots")
            
            if pay > 0:
                lbl_win.config(text=f"¡GANAS ${pay:.2f}!")
            else:
                lbl_win.config(text="")
            
            self.slot_spinning = False

        def spin():
            if self.slot_spinning: return
            total = self.slot_bet * self.slot_lines
            try:
                p.validar_apuesta(total)
            except Exception as e:
                messagebox.showwarning("Error", str(e))
                return
                
            self.slot_spinning = True
            lbl_win.config(text="")
            self._play_sound("action")
            
            def anim_step(step=0):
                if step >= 25:
                    finish_spin()
                    return
                for r in range(3):
                    for c in range(3):
                        current_board[r][c] = random.choice(SLOTS_SYMBOLS)
                draw_reels_state(current_board, blur=True)
                
                if step % 3 == 0: self._play_sound("tick")
                w.after(60, lambda: anim_step(step+1))
                
            anim_step(0)
    def open_ruleta(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Ruleta Inmersiva - Casino Royale Pro")
        w.attributes("-fullscreen", True) # Modo videojuego
        w.configure(bg=self.colors["bg_dark"])
        
        btn_exit = ModernButton(w, text="✖ SALIR AL LOBBY", command=w.destroy, bg_color="#1a2436", hover_color=self.colors["red"], fg="#FFF")
        btn_exit.place(x=30, y=30, width=180, height=40)
        w.bind("<Escape>", lambda e: w.destroy())

        main_canvas = tk.Canvas(w, bg="#0F5132", highlightthickness=0)
        main_canvas.pack(fill="both", expand=True)
        
        # Estado
        self.is_spinning = False
        self.wheel_angle = 0.0
        self.ball_angle = None
        self.current_chip = 10
        self.placed_bets = []
        self.layout_regions = {}
        self.wheel_cx, self.wheel_cy, self.wheel_r = 250, 300, 180
        
        def draw_scene():
            main_canvas.delete("all")
            width, height = w.winfo_width(), w.winfo_height()
            if width < 10: width, height = 1100, 750
            
            CasinoTableRenderer.create_table_felt(main_canvas, width, height)
            self.layout_regions = CasinoTableRenderer.create_roulette_layout(main_canvas, 480, 200, 550, 250)
            CasinoTableRenderer.create_roulette_wheel(main_canvas, self.wheel_cx, self.wheel_cy, self.wheel_r, self.wheel_angle, self.ball_angle, image_manager=self.asset_manager)
            
            for bet in self.placed_bets:
                CasinoTableRenderer.create_poker_chips(main_canvas, bet['x'], bet['y'], bet['monto'], is_stacked=True)

        main_canvas.bind("<Configure>", lambda e: draw_scene())
        
        # Overlay UI
        ui_frame = RoundedFrame(main_canvas, radius=15, bg_color="#1A1A2E")
        ui_frame.place(relx=0.5, rely=0.96, anchor="s", width=800, height=80)
        
        tk.Label(ui_frame, text="Selecciona ficha:", bg="#1A1A2E", fg=self.colors["gold"], font=("Segoe UI", 12, "bold")).place(x=20, y=25)
        
        chip_x = 180
        for val in [5, 10, 25, 100]:
            btn = tk.Button(ui_frame, text=f"${val}", font=("Segoe UI", 10, "bold"), bg="#111", fg="#FFF",
                            command=lambda v=val: set_chip(v), relief="raised", cursor="hand2")
            if val == 5: btn.config(bg="#D32F2F")
            elif val == 10: btn.config(bg="#1976D2")
            elif val == 25: btn.config(bg="#388E3C")
            elif val == 100: btn.config(bg="#212121")
            btn.place(x=chip_x, y=20, width=50, height=40)
            chip_x += 60
            
        lbl_info = tk.Label(ui_frame, text="Total Apostado: $0", bg="#1A1A2E", fg=self.colors["text_primary"], font=("Segoe UI", 12, "bold"))
        lbl_info.place(x=450, y=25)
        
        def set_chip(v):
            self.current_chip = v
            update_info()
        
        def update_info():
            tot = sum(b['monto'] for b in self.placed_bets)
            lbl_info.config(text=f"Total: ${tot} | Ficha: ${self.current_chip}")

        update_info()

        def on_click(e):
            if self.is_spinning: return
            for key, (x1, y1, x2, y2) in self.layout_regions.items():
                if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                    tot = sum(b['monto'] for b in self.placed_bets)
                    if tot + self.current_chip > p.saldo:
                        messagebox.showwarning("Saldo", "No puedes apostar más de lo que tienes.")
                        return
                    self.placed_bets.append({"tipo": key, "monto": self.current_chip, "x": e.x, "y": e.y})
                    self._play_sound("action")
                    draw_scene()
                    update_info()
                    break

        main_canvas.bind("<Button-1>", on_click)
        
        def clear_bets():
            if self.is_spinning: return
            self.placed_bets.clear()
            draw_scene()
            update_info()
            
        btn_clear = ModernButton(ui_frame, text="Deshacer", command=clear_bets, bg_color="#4B5563", hover_color="#6B7280")
        btn_clear.place(x=600, y=20, width=80, height=40)

        def settle_game(winner_num):
            self.is_spinning = False
            total_apostado = sum(b['monto'] for b in self.placed_bets)
            if total_apostado == 0: return
            
            p.validar_apuesta(total_apostado)
            
            reds = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
            color = "rojo" if winner_num in reds else ("verde" if winner_num == 0 else "negro")
            paridad = "par" if winner_num % 2 == 0 else "impar"
            docena = 1 if 1 <= winner_num <= 12 else (2 if 13 <= winner_num <= 24 else (3 if 25 <= winner_num <= 36 else 0))
            mitad = "1-18" if 1 <= winner_num <= 18 else ("19-36" if 19 <= winner_num <= 36 else "")
            
            premio_total = 0
            for bet in self.placed_bets:
                v = bet["tipo"]
                m = bet["monto"]
                if v.isdigit() and int(v) == winner_num: premio_total += m * 36
                elif v == f"doc{docena}": premio_total += m * 3
                elif (v == "rojo" and color == "rojo") or (v == "negro" and color == "negro"): premio_total += m * 2
                elif winner_num != 0 and ((v == "par" and paridad == "par") or (v == "impar" and paridad == "impar")): premio_total += m * 2
                elif winner_num != 0 and ((v == "1-18" and mitad == "1-18") or (v == "19-36" and mitad == "19-36")): premio_total += m * 2
                    
            p.registrar_jugada("Ruleta Real", total_apostado, premio_total, f"Cae {winner_num} ({color})")
            self._play_sound("win" if premio_total > 0 else "lose")
            self.refresh_dashboard("Ruleta terminada")
            
            msg = f"Bola cae en {winner_num} ({color})\n\nApostado: ${total_apostado}\nGanado: ${premio_total}"
            if premio_total > 0:
                messagebox.showinfo("¡Ganaste!", msg)
            else:
                messagebox.showinfo("Resultado", msg)
                
            self.placed_bets.clear()
            draw_scene()
            update_info()

        def spin():
            if self.is_spinning: return
            if not self.placed_bets:
                messagebox.showwarning("Atención", "Pon al menos una apuesta.")
                return
            self.is_spinning = True
            
            seq = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
            target_num = random.choice(seq)
            target_index = seq.index(target_num)
            pocket_angle = 360 / 37
            
            total_frames = 150
            def step(frame):
                if frame >= total_frames:
                    self.wheel_angle %= 360
                    self.ball_angle = (self.wheel_angle + target_index * pocket_angle + (pocket_angle/2)) % 360
                    draw_scene()
                    settle_game(target_num)
                    return
                t = frame / total_frames
                
                wheel_speed = (1 - t) * 6
                self.wheel_angle = (self.wheel_angle + wheel_speed) % 360
                
                ball_speed = (1 - t) * 18
                if self.ball_angle is None: self.ball_angle = 0
                self.ball_angle = (self.ball_angle - ball_speed) % 360
                
                if frame % 10 == 0:
                    self._play_sound("tick")
                
                draw_scene()
                w.after(20, lambda: step(frame+1))

            step(0)

        btn_spin = ModernButton(ui_frame, text="GIRAR", command=spin, bg_color=self.colors["green"], hover_color="#059669")
        btn_spin.place(x=690, y=20, width=90, height=40)


    def open_blackjack(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Blackjack Pro - Casino Royale Pro")
        w.attributes("-fullscreen", True) # Modo videojuego
        w.configure(bg=self.colors["bg_dark"])
        
        btn_exit = ModernButton(w, text="✖ SALIR AL LOBBY", command=w.destroy, bg_color="#1a2436", hover_color=self.colors["red"], fg="#FFF")
        btn_exit.place(x=30, y=30, width=180, height=40)
        w.bind("<Escape>", lambda e: w.destroy())

        main_canvas = tk.Canvas(w, bg="#0F5132", highlightthickness=0)
        main_canvas.pack(fill="both", expand=True)

        self.current_chip = 10
        self.bj_bet = 0
        self.play_mode = False
        
        # Estado del juego
        self.player_hand = []
        self.dealer_hand = []
        self.deck = []

        # Coordenadas y layout
        bet_circle_cx = 550
        bet_circle_cy = 450
        bet_circle_r = 60
        
        def draw_scene():
            main_canvas.delete("all")
            width = w.winfo_width() if w.winfo_width() > 10 else 1100
            height = w.winfo_height() if w.winfo_height() > 10 else 750
            
            # Fondo tapete
            CasinoTableRenderer.create_table_felt(main_canvas, width, height)
            
            # Círculo de apuestas
            main_canvas.create_oval(bet_circle_cx-bet_circle_r, bet_circle_cy-bet_circle_r, 
                                   bet_circle_cx+bet_circle_r, bet_circle_cy+bet_circle_r, 
                                   outline="#DAA520", width=4)
            main_canvas.create_text(bet_circle_cx, bet_circle_cy - 20, text="PLACE BET", 
                                   fill="#DAA520", font=("Segoe UI", 12, "bold"))
            
            if self.bj_bet > 0:
                CasinoTableRenderer.create_poker_chips(main_canvas, bet_circle_cx, bet_circle_cy + 10, self.bj_bet, is_stacked=True)
                
            # Textos de la mesa
            main_canvas.create_text(width/2, 200, text="BLACKJACK PAYS 3 TO 2", fill="#FFF", font=("Arial", 20, "bold"))
            main_canvas.create_text(width/2, 250, text="Dealer must draw to 16, and stand on all 17s", fill="#FFF", font=("Arial", 12))
            
            # Dibujar cartas del dealer
            card_back_img = getattr(self, "asset_manager", None)
            if card_back_img: card_back_img = card_back_img.get_image("texture_card_back", (60, 85))

            for i, card in enumerate(self.dealer_hand):
                x = width/2 - (len(self.dealer_hand)*40) + i * 80
                y = 80
                # Si estamos en juego y es la 2da carta, ocultar
                if self.play_mode and i == 1 and not hasattr(self, 'dealer_turn_active'):
                    CasinoTableRenderer.create_card(main_canvas, x, y, "?", "?", face_up=False, back_image=card_back_img)
                else:
                    CasinoTableRenderer.create_card(main_canvas, x, y, card[:-1], card[-1], face_up=True)

            # Dibujar cartas del jugador
            for i, card in enumerate(self.player_hand):
                x = width/2 - (len(self.player_hand)*40) + i * 80
                y = 550
                CasinoTableRenderer.create_card(main_canvas, x, y, card[:-1], card[-1], face_up=True)

        main_canvas.bind("<Configure>", lambda e: draw_scene())

        ui_frame = RoundedFrame(main_canvas, radius=15, bg_color="#1A1A2E")
        ui_frame.place(relx=0.5, rely=0.96, anchor="s", width=800, height=80)
        
        lbl_info = tk.Label(ui_frame, text="Total Apostado: $0", bg="#1A1A2E", fg=self.colors["text_primary"], font=("Segoe UI", 12, "bold"))
        lbl_info.place(x=450, y=25)

        chip_btns = []
        def build_pregame_ui():
            for w in chip_btns: w.destroy()
            chip_btns.clear()
            
            tk.Label(ui_frame, text="Tus Fichas:", bg="#1A1A2E", fg=self.colors["gold"], font=("Segoe UI", 12, "bold")).place(x=20, y=25)
            chip_x = 120
            for val in [5, 10, 25, 100]:
                btn = tk.Button(ui_frame, text=f"${val}", font=("Segoe UI", 10, "bold"), bg="#111", fg="#FFF",
                                command=lambda v=val: set_chip(v), relief="raised", cursor="hand2")
                if val == 5: btn.config(bg="#D32F2F")
                elif val == 10: btn.config(bg="#1976D2")
                elif val == 25: btn.config(bg="#388E3C")
                elif val == 100: btn.config(bg="#212121")
                btn.place(x=chip_x, y=20, width=50, height=40)
                chip_btns.append(btn)
                chip_x += 60
                
            btn_deal = ModernButton(ui_frame, text="REPARTIR", command=deal, bg_color=self.colors["green"], hover_color="#059669")
            btn_deal.place(x=680, y=20, width=100, height=40)
            chip_btns.append(btn_deal)

        def set_chip(v):
            self.current_chip = v

        def on_click(e):
            if self.play_mode: return
            dist = math.hypot(e.x - bet_circle_cx, e.y - bet_circle_cy)
            if dist <= bet_circle_r:
                if self.bj_bet + self.current_chip > p.saldo:
                    messagebox.showwarning("Saldo", "Sin saldo suficiente.")
                    return
                self.bj_bet += self.current_chip
                lbl_info.config(text=f"Total: ${self.bj_bet}")
                self._play_sound("action")
                draw_scene()

        main_canvas.bind("<Button-1>", on_click)
        
        def val(hand):
            t, a = 0, 0
            for c in hand:
                v = c[:-1]
                if v in ("J","Q","K"): t += 10
                elif v == "A":
                    t += 11; a += 1
                else: t += int(v)
            while t > 21 and a > 0:
                t -= 10; a -= 1
            return t

        game_btns = []
        def build_game_ui():
            for w in chip_btns: w.destroy()
            for w in game_btns: w.destroy()
            game_btns.clear()
            
            btn_hit = ModernButton(ui_frame, text="PEDIR", command=hit, bg_color=self.colors["blue_accent"], hover_color=self.colors["blue_hover"])
            btn_hit.place(x=100, y=20, width=120, height=40)
            btn_stand = ModernButton(ui_frame, text="PLANTARSE", command=stand, bg_color=self.colors["red"], hover_color="#B91C1C")
            btn_stand.place(x=250, y=20, width=120, height=40)
            game_btns.extend([btn_hit, btn_stand])

        def deal():
            if self.bj_bet <= 0:
                messagebox.showwarning("Apuesta", "Coloca al menos una ficha en el círculo de apuestas.")
                return
            p.validar_apuesta(self.bj_bet)
            self.play_mode = True
            
            self.deck = [f"{v}{s}" for v in ["A","2","3","4","5","6","7","8","9","10","J","Q","K"] for s in ["H","D","C","S"]]
            random.shuffle(self.deck)
            
            self.player_hand = [self.deck.pop(), self.deck.pop()]
            self.dealer_hand = [self.deck.pop(), self.deck.pop()]
            
            if hasattr(self, 'dealer_turn_active'): delattr(self, 'dealer_turn_active')
            
            build_game_ui()
            draw_scene()
            self._play_sound("action")
            
            if val(self.player_hand) == 21:
                stand()

        def hit():
            self.player_hand.append(self.deck.pop())
            self._play_sound("action")
            draw_scene()
            if val(self.player_hand) > 21:
                finish_game("💀 Te pasaste.")

        def stand():
            self.dealer_turn_active = True
            draw_scene()
            def dealer_play():
                if val(self.dealer_hand) < 17:
                    self.dealer_hand.append(self.deck.pop())
                    self._play_sound("action")
                    draw_scene()
                    w.after(800, dealer_play)
                else:
                    determine_winner()
            w.after(800, dealer_play)

        def determine_winner():
            vj, vd = val(self.player_hand), val(self.dealer_hand)
            if vd > 21: reward, msg = self.bj_bet * 2, "🎉 El Dealer se pasa. Ganas!"
            elif vj > vd:
                reward = self.bj_bet * 2.5 if vj == 21 and len(self.player_hand) == 2 else self.bj_bet * 2
                msg = "🎉 ¡Ganas la mano!"
            elif vj == vd: reward, msg = self.bj_bet, "🤝 Push (empate)."
            else: reward, msg = 0.0, "😞 Pierdes la mano."
            finish_game(msg, reward)

        def finish_game(result_msg, reward=0.0):
            p.registrar_jugada("Blackjack Real", self.bj_bet, reward, result_msg)
            self._play_sound("win" if reward >= self.bj_bet else "lose")
            self.refresh_dashboard("Blackjack terminado")
            
            if reward > self.bj_bet: messagebox.showinfo("¡Ganaste!", f"{result_msg}\nGanado: ${reward:.2f}")
            else: messagebox.showinfo("Final", result_msg)
            
            self.play_mode = False
            self.player_hand.clear()
            self.dealer_hand.clear()
            self.bj_bet = 0
            lbl_info.config(text="Total: $0")
            for gb in game_btns: gb.destroy()
            if hasattr(self, 'dealer_turn_active'): delattr(self, 'dealer_turn_active')
            build_pregame_ui()
            draw_scene()

        build_pregame_ui()
        draw_scene()
    # -------------------------------
    # HISTORIAL, ESTADÍSTICAS, CONFIGURACIÓN Y EXPORTACIÓN
    # -------------------------------
    def open_historial(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Historial - Casino Royale Pro")
        w.geometry("1050x550")
        w.configure(bg=self.colors["bg_dark"])

        card = RoundedFrame(w, radius=20, bg_color=self.colors["bg_card"])
        card.pack(fill="both", expand=True, padx=15, pady=15)

        cols = ("fecha", "juego", "apuesta", "premio", "balance", "detalle", "saldo")
        tree = ttk.Treeview(card, columns=cols, show="headings", height=20)
        for col, title, width in [
            ("fecha", "Fecha", 150),
            ("juego", "Juego", 100),
            ("apuesta", "Apuesta", 90),
            ("premio", "Premio", 90),
            ("balance", "Balance", 90),
            ("detalle", "Detalle", 400),
            ("saldo", "Saldo", 90),
        ]:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for item in p.historial[-300:]:
            tree.insert("", "end", values=(
                item["fecha"], item["juego"],
                f"{item['apuesta']:.2f}", f"{item['premio']:.2f}",
                f"{item['balance']:+.2f}", item["detalle"],
                f"{item['saldo_post']:.2f}"
            ))

    def open_stats(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Estadísticas Avanzadas - Casino Royale Pro")
        w.geometry("850x550")
        w.configure(bg=self.colors["bg_dark"])

        card = RoundedFrame(w, radius=20, bg_color=self.colors["bg_card"])
        card.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(card, text="📊 ESTADÍSTICAS POR JUEGO", font=("Segoe UI", 16, "bold"), bg=self.colors["bg_card"], fg=self.colors["gold"]).pack(pady=(15, 10))

        canvas = tk.Canvas(card, bg="#1F2937", highlightthickness=0, width=750, height=320)
        canvas.pack(padx=20, pady=15)

        stats = p.estadisticas_globales or {}
        juegos = ["Slots", "Ruleta", "Blackjack"]
        balances = []
        for g in juegos:
            info = stats.get(g, {"apostado": 0.0, "ganado": 0.0})
            balances.append(info["ganado"] - info["apostado"])
        max_abs = max(1.0, max(abs(v) for v in balances))

        x0 = 80
        base_y = 200
        canvas.create_line(50, base_y, 730, base_y, fill=self.colors["border"], width=2)
        for i, (juego, val) in enumerate(zip(juegos, balances)):
            h = int((abs(val) / max_abs) * 140)
            x1 = x0 + i * 200
            x2 = x1 + 100
            y1 = base_y - h if val >= 0 else base_y
            y2 = base_y if val >= 0 else base_y + h
            color = self.colors["green"] if val >= 0 else self.colors["red"]
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            canvas.create_text((x1+x2)//2, base_y+25, text=juego, fill=self.colors["text_primary"], font=("Segoe UI", 11, "bold"))
            canvas.create_text((x1+x2)//2, y1-12 if val >= 0 else y2+12, text=f"${val:+,.2f}", fill=self.colors["gold"], font=("Consolas", 11))

        s = p.stats
        lbl = tk.Label(card, text=f"🎯 Total jugadas: {s.jugadas}  |  💵 Apostado: ${s.total_apostado:,.2f}  |  🏆 Ganado: ${s.total_ganado:,.2f}  |  📈 Balance: ${s.balance_sesion:+,.2f}",
                       bg=self.colors["bg_card"], fg=self.colors["text_secondary"], font=self.font_body)
        lbl.pack(pady=15)

    def open_settings(self) -> None:
        w = tk.Toplevel(self)
        w.title("Configuración - Casino Royale Pro")
        w.geometry("480x350")
        w.configure(bg=self.colors["bg_dark"])

        card = RoundedFrame(w, radius=20, bg_color=self.colors["bg_card"])
        card.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(card, text="⚙️ CONFIGURACIÓN", font=("Segoe UI", 16, "bold"), bg=self.colors["bg_card"], fg=self.colors["gold"]).pack(pady=(20, 15))

        sound_var = tk.BooleanVar(value=bool(self.settings.get("sound", True)))
        anim_var = tk.BooleanVar(value=bool(self.settings.get("animations", True)))
        speed_var = tk.IntVar(value=int(self.settings.get("animation_speed_ms", 85)))

        tk.Checkbutton(card, text="🔊 Activar sonido", variable=sound_var, bg=self.colors["bg_card"], fg=self.colors["text_primary"], selectcolor="#1F2937", activebackground=self.colors["bg_card"]).pack(anchor="w", padx=30, pady=5)
        tk.Checkbutton(card, text="✨ Activar animaciones", variable=anim_var, bg=self.colors["bg_card"], fg=self.colors["text_primary"], selectcolor="#1F2937", activebackground=self.colors["bg_card"]).pack(anchor="w", padx=30, pady=5)
        tk.Label(card, text="Velocidad animación (ms):", bg=self.colors["bg_card"], fg=self.colors["text_secondary"]).pack(anchor="w", padx=30, pady=(10,0))
        scale = tk.Scale(card, from_=20, to=180, orient="horizontal", variable=speed_var, bg=self.colors["bg_card"], fg=self.colors["text_primary"], troughcolor="#374151", highlightthickness=0)
        scale.pack(fill="x", padx=30, pady=5)

        def save():
            self.settings["sound"] = bool(sound_var.get())
            self.settings["animations"] = bool(anim_var.get())
            self.settings["animation_speed_ms"] = int(speed_var.get())
            self._save_settings()
            self.refresh_dashboard("Configuración guardada")
            self._play_sound("default")
            w.destroy()

        btn = ModernButton(card, text="💾 GUARDAR", command=save, bg_color=self.colors["blue_accent"], hover_color=self.colors["blue_hover"], font=("Segoe UI", 11, "bold"))
        btn.pack(pady=20, ipadx=20, ipady=6)

    def exportar_reporte(self) -> None:
        p = self._player()
        report = DATA_DIR / f"reporte_{p.nombre}.txt"
        s = p.stats
        lines = [
            "🏆 CASINO ROYALE PRO - REPORTE DE SESIÓN 🏆",
            "=" * 50,
            f"Jugador: {p.nombre}",
            f"Saldo final: ${p.saldo:,.2f}",
            f"Jugadas: {s.jugadas}",
            f"Apostado: ${s.total_apostado:,.2f}",
            f"Ganado: ${s.total_ganado:,.2f}",
            f"Balance: ${s.balance_sesion:+,.2f}",
            "",
            "📜 Últimos movimientos:",
        ]
        for row in p.historial[-40:]:
            lines.append(f"{row['fecha']} | {row['juego']:<10} | {row['balance']:+.2f} | {row['detalle']}")
        report.write_text("\n".join(lines), encoding="utf-8")
        self._play_sound("default")
        self.refresh_dashboard("Reporte exportado")
        messagebox.showinfo("Reporte", f"Reporte guardado en:\n{report}")


if __name__ == "__main__":
    app = CasinoRoyalePro()
    app.mainloop()