import flet as ft
import random
import asyncio

# Paleta de colores
GOLD = "#F5B042"
DARK = "#05070A"
CARD_BG = "#0F1626"
EMERALD = "#10B981"
CRIMSON = "#E53E3E"
BLUE = "#3B82F6"

SYMBOLS = ["🍒", "🍋", "🔔", "⭐", "💎", "7️⃣"]
PAYOUTS = {
    "7️⃣": 50, "💎": 20, "🔔": 10, "⭐": 5, "🍒": 3, "🍋": 2
}

# Probabilidades (símbolo menos frecuente -> más valor)
WEIGHTED_SYMBOLS = (
    ["🍒"] * 25 + ["🍋"] * 20 + ["🔔"] * 15 +
    ["⭐"] * 10 + ["💎"] * 5 + ["7️⃣"] * 3
)


def make_reel_cell(symbol: str, size=60, highlight=False) -> ft.Container:
    """Celda individual de la cuadrícula de slots."""
    return ft.Container(
        width=100, height=90,
        alignment=ft.Alignment.CENTER,
        bgcolor="#12203A" if not highlight else "#1E3A5F",
        border_radius=12,
        border=ft.Border.all(2, GOLD if highlight else "#FFFFFF15"),
        shadow=ft.BoxShadow(blur_radius=15, color="#F5B04244") if highlight else None,
        animate=ft.Animation(120, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Text(symbol, size=size),
    )


class SlotsView(ft.Container):
    def __init__(self, page: ft.Page, jugador, storage):
        super().__init__(expand=True, padding=ft.Padding.symmetric(horizontal=40, vertical=20))
        self.main_page = page
        self.jugador = jugador
        self.storage = storage
        self.spinning = False

        # 3 columnas × 3 filas → 9 celdas
        self.grid: list[list[ft.Container]] = [
            [make_reel_cell(random.choice(SYMBOLS)) for _ in range(3)]
            for _ in range(3)
        ]

        self.bet_input = ft.TextField(
            value="10", label="Apuesta ($)", width=130,
            border_color=GOLD, border_radius=10,
            text_align=ft.TextAlign.CENTER,
            color="white",
        )

        self.result_banner = ft.Container(
            visible=False, border_radius=15, padding=12,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            content=ft.Text("", size=22, weight="bold", text_align=ft.TextAlign.CENTER),
        )

        self.saldo_text = ft.Text(
            f"💰 Saldo: ${jugador.saldo:,.2f}", size=15, color=EMERALD, weight="bold"
        )

        self.spin_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.REFRESH_ROUNDED, size=20), ft.Text("GIRAR", weight="bold", size=16)],
                spacing=8, alignment=ft.MainAxisAlignment.CENTER
            ),
            on_click=self.spin,
            width=180, height=55,
            bgcolor=GOLD,
            style=ft.ButtonStyle(
                color=DARK,
                shape=ft.RoundedRectangleBorder(radius=14),
                overlay_color={ft.ControlState.HOVERED: "#D4AF37"},
            ),
        )

        # Construir columnas de la cuadrícula
        reel_columns = ft.Row(
            controls=[
                ft.Column(
                    [self.grid[row][col] for row in range(3)],
                    spacing=8,
                )
                for col in range(3)
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        machine_frame = ft.Container(
            content=ft.Stack([
                # Fondo de la máquina
                ft.Container(
                    content=reel_columns,
                    padding=20,
                    bgcolor="#0A1628",
                    border_radius=20,
                    border=ft.Border.all(3, GOLD),
                    shadow=ft.BoxShadow(blur_radius=40, color="#F5B04233"),
                ),
                # Línea de pago central (decorativa)
                ft.Container(height=2, bgcolor=GOLD + "55", margin=ft.margin.symmetric(vertical=64)),
            ]),
            margin=ft.margin.symmetric(vertical=10),
        )

        self.content = ft.Column(
            controls=[
                # Cabecera
                ft.Row([
                    ft.Column([
                        ft.Text("🎰 MEGA SLOTS", size=30, weight="bold", color=GOLD),
                        ft.Text("3 × 3 • Línea central paga", size=13, color="#9CA3AF"),
                    ]),
                    ft.Container(expand=True),
                    self.saldo_text,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Divider(height=10, color="transparent"),
                machine_frame,
                ft.Divider(height=8, color="transparent"),

                # Controles
                ft.Row([
                    self.bet_input,
                    self.spin_btn,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),

                ft.Divider(height=8, color="transparent"),
                self.result_banner,

                # Tabla de pagos
                ft.Container(
                    content=ft.Row(
                        [ft.Text(f"{s}  ×{m}", size=13, color="#9CA3AF") for s, m in PAYOUTS.items()],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    padding=8,
                    bgcolor="#FFFFFF08",
                    border_radius=10,
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

    async def spin(self, e):
        if self.spinning:
            return
        try:
            apuesta = float(self.bet_input.value or "0")
        except ValueError:
            self._show_result("Valor inválido", CRIMSON)
            return

        if apuesta <= 0:
            self._show_result("Apuesta inválida", CRIMSON)
            return
        if self.jugador.saldo < apuesta:
            self._show_result("❌ Saldo insuficiente", CRIMSON)
            return

        self.spinning = True
        self.spin_btn.disabled = True
        self.result_banner.visible = False
        self.main_page.update()

        # --- Animación de giro por columna ---
        speeds = [0.04, 0.055, 0.07]  # cada columna para en momento distinto
        stops = [12, 16, 20]

        for frame in range(max(stops)):
            for col in range(3):
                if frame < stops[col]:
                    for row in range(3):
                        self.grid[row][col].content.value = random.choice(WEIGHTED_SYMBOLS)
            self.main_page.update()
            await asyncio.sleep(speeds[min(frame // 6, 2)])

        # --- Resultado final ---
        tablero = [
            [random.choice(WEIGHTED_SYMBOLS) for _ in range(3)]
            for _ in range(3)
        ]
        for row in range(3):
            for col in range(3):
                self.grid[row][col].content.value = tablero[row][col]

        # Verificar líneas ganadoras (sólo fila central para simplicidad)
        linea_central = [tablero[1][col] for col in range(3)]
        premio = 0
        win_symbol = None
        if linea_central[0] == linea_central[1] == linea_central[2]:
            win_symbol = linea_central[0]
            premio = apuesta * PAYOUTS.get(win_symbol, 2)

        # Resaltar fila ganadora
        for col in range(3):
            self.grid[1][col].border = ft.Border.all(
                2, GOLD if premio else "#FFFFFF15"
            )
            self.grid[1][col].bgcolor = "#1E3A5F" if premio else "#12203A"

        self.jugador.registrar_jugada("Slots", apuesta, premio, f"{linea_central}")
        self.storage.guardar_jugador(self.jugador)
        self.saldo_text.value = f"💰 Saldo: ${self.jugador.saldo:,.2f}"

        if premio:
            self._show_result(f"🏆 ¡JACKPOT!  +${premio:,.2f}", EMERALD)
        else:
            self._show_result("Sin suerte esta vez… inténtalo de nuevo", "#9CA3AF")

        self.spin_btn.disabled = False
        self.spinning = False
        self.main_page.update()
        if hasattr(self.main_page, "refresh_balance"):
            self.main_page.refresh_balance()

    def _show_result(self, msg, color):
        self.result_banner.visible = True
        self.result_banner.bgcolor = color + "22"
        self.result_banner.border = ft.Border.all(1, color)
        self.result_banner.content.value = msg
        self.result_banner.content.color = color
        self.main_page.update()
