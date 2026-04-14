import flet as ft
import random
import asyncio
import os
import threading
import winsound

_ASSETS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets"))

def _play(rel_path):
    full = os.path.join(_ASSETS, rel_path.replace("/", os.sep))
    if os.path.exists(full):
        threading.Thread(
            target=lambda: winsound.PlaySound(full, winsound.SND_FILENAME),
            daemon=True,
        ).start()

# ─── PALETA REFINADA ────────────────────────────────────────────────────────
GOLD    = "#F5B042"
GOLD_DIM= "#D4930A"
DARK    = "#05070A"
CARD_BG = "#0F1A2E"
EMERALD = "#1FD090"
CRIMSON = "#F04040"
BLUE    = "#4A9EFF"

SYMBOL_MAP = {
    "🍒": "slots/cherry.png",
    "🍋": "slots/lemon.png",
    "🔔": "slots/bell.png",
    "⭐": "slots/star.png",
    "💎": "slots/diamond.png",
    "7️⃣": "slots/seven.png",
}
SYMBOLS = list(SYMBOL_MAP.keys())
PAYOUTS = {
    "7️⃣": 50, "💎": 20, "🔔": 10, "⭐": 5, "🍒": 3, "🍋": 2,
}
WEIGHTED_SYMBOLS = (
    ["🍒"] * 25 + ["🍋"] * 20 + ["🔔"] * 15 +
    ["⭐"] * 10 + ["💎"] * 5 + ["7️⃣"] * 3
)


def make_reel_cell(symbol: str, highlight=False):
    img_path = SYMBOL_MAP.get(symbol, "slots/cherry.png")
    img = ft.Image(src=img_path, width=80, height=80, fit="contain")
    cell = ft.Container(
        width=120, height=120,
        alignment=ft.Alignment.CENTER,
        bgcolor="#0B2439" if not highlight else "#1E3E66",
        border_radius=22,
        border=ft.Border.all(
            2, GOLD if highlight else "#FFFFFF22",
        ),
        shadow=ft.BoxShadow(blur_radius=22, color=GOLD + "44") if highlight else ft.BoxShadow(blur_radius=16, color="#00000066", offset=ft.Offset(0, 5)),
        animate=ft.Animation(150, "easeInOut"),
        content=ft.Container(
            width=100, height=100, border_radius=18,
            bgcolor="#081827",
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(blur_radius=18, color="#000000AA", offset=ft.Offset(0, 5)),
            content=img,
        ),
    )
    return cell, img


class SlotsView(ft.Container):
    def __init__(self, page: ft.Page, jugador, storage):
        super().__init__(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=40, vertical=12),
            bgcolor=CARD_BG,
            border_radius=28,
            border=ft.Border.all(1, "#FFFFFF12"),
            shadow=ft.BoxShadow(blur_radius=28, color="#00000088", offset=ft.Offset(0, 10)),
        )
        self.main_page = page
        self.jugador   = jugador
        self.storage   = storage
        self.spinning  = False

        self.grid: list[list[ft.Container]] = []
        self.grid_images: list[list[ft.Image]] = []
        for _ in range(3):
            row_cells = []
            row_images = []
            for _ in range(3):
                cell, img = make_reel_cell(random.choice(SYMBOLS))
                row_cells.append(cell)
                row_images.append(img)
            self.grid.append(row_cells)
            self.grid_images.append(row_images)

        self.bet_input = ft.TextField(
            value="10", label="Apuesta ($)", width=150,
            border_color=GOLD + "88", border_radius=16,
            text_align="center", color="white",
            bgcolor="#172B46",
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            cursor_color=GOLD,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#8A94A6"),
        )

        self.result_banner = ft.Container(
            visible=False, border_radius=15, padding=14,
            animate=ft.Animation(400, "elasticOut"),
            content=ft.Text("", size=22, weight="bold", text_align="center"),
        )

        self.saldo_text = ft.Text(
            f"💰  ${jugador.saldo:,.2f}",
            size=15, color=EMERALD, weight="bold",
        )

        self.spin_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.REFRESH_ROUNDED, size=20), ft.Text("GIRAR", weight="bold", size=16)],
                spacing=8, alignment="center",
            ),
            on_click=self.spin, width=200, height=60, bgcolor=GOLD,
            style=ft.ButtonStyle(
                color=DARK,
                shape=ft.RoundedRectangleBorder(radius=15),
                overlay_color={ft.ControlState.HOVERED: GOLD_DIM},
                shadow_color=GOLD + "44", elevation=6,
            ),
        )

        reel_columns = ft.Row(
            controls=[
                ft.Column([self.grid[row][col] for row in range(3)], spacing=14)
                for col in range(3)
            ],
            spacing=14, alignment="center",
        )

        # ── Máquina premium ──
        machine_frame = ft.Container(
            width=900,
            height=750,
            content=ft.Stack([
                ft.Container(
                    expand=True, border_radius=36,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                        colors=["#09141E", "#0D1D2D", "#07111F"],
                    ),
                    border=ft.Border.all(3, GOLD + "66"),
                    shadow=ft.BoxShadow(blur_radius=58, color="#00000099", spread_radius=10, offset=ft.Offset(0, 14)),
                ),
                ft.Container(
                    top=16, left=16, right=16, bottom=16,
                    border_radius=28,
                    bgcolor="#071926",
                    border=ft.Border.all(1, "#FFFFFF12"),
                ),
                ft.Container(
                    top=18, left=20, right=20, height=62,
                    border_radius=ft.BorderRadius(24, 24, 12, 12),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
                        colors=[GOLD + "22", GOLD + "55", GOLD + "22"],
                    ),
                    content=ft.Row([
                        ft.Icon(ft.Icons.CELEBRATION_OUTLINED, size=22, color=GOLD),
                        ft.Text("ROYAL JACKPOT", size=18, weight="bold", color=GOLD),
                    ], alignment="center", spacing=10),
                ),
                ft.Container(
                    top=110, left=42, right=42, height=500,
                    border_radius=28,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                        colors=["#0C1E32", "#08203B", "#02111F"],
                    ),
                    border=ft.Border.all(1, "#FFFFFF12"),
                    shadow=ft.BoxShadow(blur_radius=20, color="#00000066", offset=ft.Offset(0, 10)),
                    content=ft.Column([
                        ft.Container(height=24),
                        ft.Row([
                            ft.Container(width=12, height=12, border_radius=6, bgcolor="#F5B042"),
                            ft.Container(width=12, height=12, border_radius=6, bgcolor="#EF4444"),
                            ft.Container(width=12, height=12, border_radius=6, bgcolor="#10B981"),
                            ft.Container(expand=True),
                            ft.Text("BONUS", size=12, weight="bold", color="#8EA4D2"),
                        ], alignment="center", spacing=8),
                        ft.Container(height=18),
                        ft.Container(
                            expand=True,
                            bgcolor="#071926",
                            border_radius=24,
                            padding=ft.padding.all(18),
                            border=ft.Border.all(1, "#FFFFFF14"),
                            content=reel_columns,
                        ),
                    ], spacing=10),
                ),
                ft.Container(
                    height=42, bottom=20, left=80, right=80,
                    border_radius=18,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
                        colors=["#F7C54833", "#F7C54811", "#F7C54833"],
                    ),
                ),
                ft.Container(
                    width=20, height=100, left=24, top=130,
                    border_radius=ft.BorderRadius(20, 20, 14, 14),
                    bgcolor="#15253D",
                    border=ft.Border.all(1, "#FFFFFF14"),
                ),
                ft.Container(
                    width=20, height=100, right=24, top=130,
                    border_radius=ft.BorderRadius(20, 20, 14, 14),
                    bgcolor="#15253D",
                    border=ft.Border.all(1, "#FFFFFF14"),
                ),
            ]),
            margin=ft.margin.symmetric(vertical=15),
        )

        # ── Tabla de pagos ──
        payout_table = ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Image(src=SYMBOL_MAP[s], width=22, height=22),
                        ft.Text(f"×{m}", size=13, color="#C8CDD6", weight="bold"),
                    ], spacing=6)
                    for s, m in PAYOUTS.items()
                ],
                alignment="center", spacing=14,
            ),
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
            bgcolor="#102645",
            border_radius=16,
            border=ft.Border.all(1, "#FFFFFF14"),
            margin=ft.margin.only(top=8),
        )

        self.content = ft.Column(
            controls=[
                ft.Row([
                    ft.Column([
                        ft.Text("🎰 ROYAL SLOTS", size=34, weight="bold", color=GOLD),
                        ft.Text("PREMIUM EDITION  •  3×3", size=13, color="#7E8A9F", italic=True),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.Container(
                        content=self.saldo_text,
                        padding=ft.Padding.symmetric(horizontal=16, vertical=9),
                        bgcolor=EMERALD + "14",
                        border_radius=10,
                        border=ft.Border.all(1, EMERALD + "44"),
                    ),
                ], alignment="spaceBetween"),
                ft.Divider(height=15, color="transparent"),
                machine_frame,
                ft.Divider(height=15, color="transparent"),
                ft.Row([self.bet_input, self.spin_btn], alignment="center", spacing=25),
                ft.Divider(height=15, color="transparent"),
                self.result_banner,
                payout_table,
            ],
            horizontal_alignment="center",
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
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
            self._show_result("⚠ Saldo insuficiente", CRIMSON)
            return

        self.spinning = True
        self.spin_btn.disabled = True
        self.result_banner.visible = False

        # Resetar estilos de todas las celdas
        for r in range(3):
            for c in range(3):
                self.grid[r][c].border = ft.Border.all(2, "#FFFFFF28")
                self.grid[r][c].bgcolor = "#13243E"
                self.grid[r][c].shadow  = ft.BoxShadow(blur_radius=14, color="#00000066", offset=ft.Offset(0, 3))

        self.main_page.update()

        stops = [15, 20, 25]
        for frame in range(max(stops)):
            updated = False
            for col in range(3):
                if frame < stops[col]:
                    for row in range(3):
                        sym = random.choice(WEIGHTED_SYMBOLS)
                        self.grid_images[row][col].src = SYMBOL_MAP[sym]
                    updated = True
            if updated:
                if frame % 2 == 0:
                    _play("sounds/tick.wav")
                self.main_page.update()
                await asyncio.sleep(0.06)

        tablero = [[random.choice(WEIGHTED_SYMBOLS) for _ in range(3)] for _ in range(3)]
        for row in range(3):
            for col in range(3):
                self.grid_images[row][col].src = SYMBOL_MAP[tablero[row][col]]

        # ── LÓGICA DE PREMIOS MÚLTIPLES ──
        PAYLINES = [
            [(0,0), (0,1), (0,2)], # Horizontal Top
            [(1,0), (1,1), (1,2)], # Horizontal Mid
            [(2,0), (2,1), (2,2)], # Horizontal Bottom
            [(0,0), (1,1), (2,2)], # Diagonal 1
            [(0,2), (1,1), (2,0)]  # Diagonal 2
        ]

        total_premio = 0
        winning_cells = set()
        num_wins = 0

        for line in PAYLINES:
            coords = line
            s1 = tablero[coords[0][0]][coords[0][1]]
            s2 = tablero[coords[1][0]][coords[1][1]]
            s3 = tablero[coords[2][0]][coords[2][1]]

            if s1 == s2 == s3:
                num_wins += 1
                line_prize = apuesta * PAYOUTS.get(s1, 2)
                total_premio += line_prize
                for r, c in coords:
                    winning_cells.add((r, c))

        if total_premio > 0:
            _play("sounds/win.wav")
            for r, c in winning_cells:
                self.grid[r][c].border = ft.Border.all(3, GOLD)
                self.grid[r][c].bgcolor = "#1E3E66"
                self.grid[r][c].shadow  = ft.BoxShadow(blur_radius=22, color=GOLD + "88")

        self.jugador.registrar_jugada("Slots", apuesta, total_premio, f"Wins: {num_wins}")
        self.storage.guardar_jugador(self.jugador)
        self.saldo_text.value = f"💰  ${self.jugador.saldo:,.2f}"

        if total_premio > 0:
            msg = f"🔥 ¡JACKPOT! +${total_premio:,.2f}"
            if num_wins > 1:
                msg += f" ({num_wins} LÍNEAS)"
            self._show_result(msg, EMERALD)
        else:
            self._show_result("Suerte para la próxima", "#B0B8C8")

        self.spin_btn.disabled = False
        self.spinning = False
        self.main_page.update()
        if hasattr(self.main_page, "refresh_balance"):
            self.main_page.refresh_balance()

    def _show_result(self, msg, color):
        self.result_banner.visible         = True
        self.result_banner.bgcolor         = color + "18"
        self.result_banner.border          = ft.Border.all(1, color + "88")
        self.result_banner.content.value   = msg
        self.result_banner.content.color   = color
        self.main_page.update()