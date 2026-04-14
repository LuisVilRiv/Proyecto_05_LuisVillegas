import flet as ft
import random
import math
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
            daemon=True
        ).start()

# ─── PALETA ─────────────────────────────────────────────────────────────────
GOLD        = "#F5B042"
GOLD_GLOW   = "#F5B04244"
GOLD_DARK   = "#B8860B"
DARK        = "#05070A"
DEEP_NAVY   = "#080E18"
CARD_BG     = "#0F1A2E"
EMERALD     = "#1FD090"
EMERALD_DIM = "#0D9B68"
CRIMSON     = "#F04040"
SILVER      = "#C8CDD6"

WOOD_BASE   = "#1A0A04"
WOOD_MID    = "#3A1A0C"
WOOD_LIGHT  = "#5C2A14"

FELT_CENTER = "#1D7044"
FELT_MID    = "#155534"
FELT_DARK   = "#0C3A20"
FELT_EDGE   = "#071E10"

WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11,
    30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18,
    29, 7, 28, 12, 35, 3, 26
]
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
N = len(WHEEL_ORDER)
CALIBRATION_OFFSET = 0.04  # Ajuste fino para centrar la bola en el PNG


def get_num_color(n):
    if n == 0:   return "#0E7A3C"
    return "#C72B2E" if n in RED_NUMBERS else "#181818"


# ─── CHIP ───────────────────────────────────────────────────────────────────
class Chip(ft.Container):
    def __init__(self, value, size=32):
        colors = {
            1:   ("#F3F4F6", "#D1D5DB"),
            5:   ("#3B82F6", "#1D4ED8"),
            10:  ("#EF4444", "#B91C1C"),
            50:  ("#10B981", "#059669"),
            100: ("#1F2937", "#374151"),
            500: ("#9B5CF6", "#7C3AED"),
        }
        main_color, dark_color = colors.get(value, ("#F5B042", "#B8860B"))
        text_color = "#111827" if value == 1 else "white"
        super().__init__(
            width=size, height=size,
            border_radius=size / 2,
            bgcolor=main_color,
            border=ft.Border.all(2, "#FFFFFFAA" if value < 100 else GOLD),
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(blur_radius=10, color="#000000AA", offset=ft.Offset(2, 3)),
            content=ft.Stack([
                ft.Container(
                    border=ft.Border.all(1, dark_color),
                    border_radius=size / 2,
                    margin=3,
                ),
                ft.Container(
                    content=ft.Text(str(value), size=size * 0.38, weight="bold", color=text_color),
                    alignment=ft.Alignment.CENTER,
                ),
            ]),
        )


# ─── MAIN VIEW ──────────────────────────────────────────────────────────────
class RouletteView(ft.Container):
    def __init__(self, page: ft.Page, jugador, storage):
        super().__init__(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=24, vertical=22),
            bgcolor=CARD_BG,
            border_radius=28,
            border=ft.Border.all(1, "#FFFFFF12"),
            shadow=ft.BoxShadow(blur_radius=30, color="#00000088", offset=ft.Offset(0, 10)),
        )
        self.main_page = page
        self.jugador   = jugador
        self.storage   = storage

        self.selected_chip_value = 10
        self.active_bets   = {}
        self.bet_containers = {}
        self.spinning      = False
        self.history       = []
        self._wheel_angle  = 0.0

        # ── UI Estado ──
        self.status_text = ft.Text(
            "REALIZA TUS APUESTAS",
            size=14, weight="bold", color="#C8CDD6",
            text_align="center",
        )
        self.balance_text = ft.Text(
            f"SALDO: ${self.jugador.saldo:,.2f}",
            size=17, weight="bold", color=EMERALD,
        )

        # ── RULETA ──
        self._wx, self._wy = 210, 210
        self.wheel_layer = ft.Image(
            src="roulette/wheel.png", width=400, height=400, fit="cover",
        )
        self.wheel_container = ft.Container(
            content=self.wheel_layer,
            width=400, height=400,
            border_radius=200,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor="transparent",
            alignment=ft.Alignment.CENTER,
            rotate=ft.Rotate(0, alignment=ft.Alignment.CENTER),
            animate_rotation=ft.Animation(4000, "decelerate"),
        )
        self.ball = ft.Container(
            width=15, height=15, bgcolor="white", border_radius=8,
            shadow=ft.BoxShadow(blur_radius=8, color="#000000CC", spread_radius=1, offset=ft.Offset(1, 2)),
            visible=False,
        )

        def _centered(child, stack_size=420):
            return ft.Container(
                content=child,
                width=stack_size, height=stack_size,
                alignment=ft.Alignment.CENTER,
            )

        wheel_area = ft.Stack([
            # 1. Marco exterior de madera (FONDO SÓLIDO PREMIUM)
            _centered(ft.Container(
                width=398, height=398, border_radius=199,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                    colors=[WOOD_LIGHT, WOOD_MID, WOOD_BASE, "#0A0400"],
                ),
                shadow=ft.BoxShadow(blur_radius=40, color="#000000EE", spread_radius=8, offset=ft.Offset(0, 8)),
            )),

            # 2. Aro dorado exterior (Hollow)
            _centered(ft.Container(
                width=356, height=356, border_radius=178,
                bgcolor="transparent",
                border=ft.Border.all(5, GOLD),
                shadow=ft.BoxShadow(blur_radius=12, color=GOLD_GLOW, spread_radius=2),
            )),

            # 3. VENTANA DE RECORTE (Hides wheel corners)
            _centered(ft.Container(
                content=ft.Stack([
                    # Fondo de fieltro local
                    _centered(ft.Container(width=340, height=340, border_radius=170, bgcolor=FELT_MID), 342),
                    # Imagen giratoria
                    _centered(self.wheel_container, 342),
                ]),
                width=342, height=342, border_radius=171,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                border=ft.Border.all(2, SILVER),
            )),

            # 4. Puntero superior fijo
            ft.Container(
                content=ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color=GOLD, size=30, rotate=math.pi/2),
                top=0, left=0, right=0, height=50,
                alignment=ft.Alignment.CENTER,
            ),

            # 5. La bola (En el stack principal para usar coordenadas cx, cy)
            self.ball,

            # 6. Hub central decorativo
            _centered(ft.Container(
                width=48, height=48, border_radius=24,
                bgcolor="#0B0B0B",
                border=ft.Border.all(3, GOLD),
                shadow=ft.BoxShadow(blur_radius=14, color="#000000CC", spread_radius=2),
                content=ft.Container(
                    width=14, height=14, border_radius=7, bgcolor=GOLD,
                    alignment=ft.Alignment.CENTER,
                ),
            )),
        ], width=420, height=420)

        # ── MESA / BETTING BOARD ──
        self.board = self._create_felt_board()

        # ── CHIP TRAY ──
        self.tray = self._create_chip_tray()

        # ── BOTONES ──
        self.spin_btn = ft.FilledButton(
            "GIRAR RULETA", icon=ft.Icons.AUTORENEW_ROUNDED,
            on_click=self.handle_spin, width=200, height=54, bgcolor=GOLD,
            style=ft.ButtonStyle(
                color=DARK, shape=ft.RoundedRectangleBorder(radius=14),
                overlay_color={ft.ControlState.HOVERED: GOLD_DARK},
                shadow_color=GOLD_GLOW, elevation=6,
            ),
        )
        self.undo_btn = ft.IconButton(
            icon=ft.Icons.UNDO_ROUNDED, on_click=self.undo_last_bet,
            icon_color=GOLD, tooltip="Deshacer última apuesta",
        )
        self.clear_btn = ft.OutlinedButton(
            "LIMPIAR", icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
            on_click=self.clear_bets, width=150, height=54,
            style=ft.ButtonStyle(
                color=CRIMSON,
                side={"": ft.BorderSide(1, CRIMSON + "88")},
                shape=ft.RoundedRectangleBorder(radius=14),
                overlay_color={ft.ControlState.HOVERED: CRIMSON + "18"},
            ),
        )

        # ── STATUS BOX ──
        status_box = ft.Container(
            content=self.status_text,
            bgcolor="#111E30",
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
            border_radius=14,
            border=ft.Border.all(1, "#FFFFFF22"),
            alignment=ft.Alignment.CENTER,
            width=400,
        )

        # ── LAYOUT PRINCIPAL ──
        self.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("RULETA ROYALE", size=26, weight="bold", color=GOLD),
                        ft.Text("♠  EUROPEAN EDITION  ♠", size=11, color="#7E8A9F", weight="bold"),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.Container(
                        content=self.balance_text,
                        padding=ft.Padding.symmetric(horizontal=18, vertical=10),
                        bgcolor=EMERALD + "14",
                        border_radius=12,
                        border=ft.Border.all(1, EMERALD + "40"),
                    ),
                ]),
                padding=ft.Padding.symmetric(horizontal=4),
            ),

            ft.Divider(height=18, color="transparent"),

            ft.Column([
                self._build_casino_table(wheel_area, status_box),
                ft.Container(height=18),
                self.tray,
                ft.Container(height=18),
                ft.Row(
                    [self.spin_btn, self.clear_btn, self.undo_btn],
                    spacing=14, alignment="center",
                ),
            ], expand=True, horizontal_alignment="center"),
        ], spacing=0)

    # ─── MESA DE CASINO ──────────────────────────────────────────────────────
    def _build_casino_table(self, wheel_area, status_box):
        return ft.Container(
            content=ft.Stack([
                # 1. Marco exterior de madera
                ft.Container(
                    expand=True, border_radius=26,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                        colors=[WOOD_LIGHT, WOOD_MID, WOOD_BASE, "#100503"],
                    ),
                    shadow=ft.BoxShadow(
                        blur_radius=48, spread_radius=6,
                        color="#000000CC", offset=ft.Offset(0, 10),
                    ),
                ),
                # 2. Moldura dorada
                ft.Container(border=ft.Border.all(2, GOLD + "99"), border_radius=22, margin=7),
                # 3. Segunda moldura plateada
                ft.Container(border=ft.Border.all(1, SILVER + "55"), border_radius=20, margin=11),
                # 4. Superficie de fieltro
                ft.Container(
                    border_radius=18, margin=14,
                    gradient=ft.RadialGradient(
                        center=ft.Alignment(0, -0.3), radius=1.4,
                        colors=[FELT_CENTER, FELT_MID, FELT_DARK, FELT_EDGE],
                    ),
                    shadow=ft.BoxShadow(blur_radius=20, spread_radius=-4, color="#000000AA"),
                ),
                # 5. Veta de tejido sutil
                ft.Container(
                    border_radius=18, margin=14, opacity=0.04,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                        colors=["#FFFFFF", "#00000000", "#FFFFFF", "#00000000",
                                "#FFFFFF", "#00000000", "#FFFFFF"],
                    ),
                ),
                # 6. Leyenda superior
                ft.Container(
                    content=ft.Text(
                        "◆  R O U L E T T E  ◆",
                        size=12, weight="bold", color="#FFFFFF44",
                        text_align="center", font_family="serif",
                    ),
                    top=24, left=0, right=0,
                    alignment=ft.Alignment.CENTER,
                ),
                # 7. Leyenda inferior
                ft.Container(
                    content=ft.Text(
                        "STRAIGHT UP PAYS 35 TO 1  •  SPLIT PAYS 17 TO 1",
                        size=9, weight="bold", color="#FFFFFF2E",
                        text_align="center", font_family="serif",
                    ),
                    bottom=22, left=0, right=0,
                    alignment=ft.Alignment.CENTER,
                ),
                # 8. Rueda + tablero sobre el fieltro
                ft.Container(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=wheel_area,
                                width=420,
                                height=420,
                                shape=ft.BoxShape.CIRCLE,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                            ),
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(height=20),
                                    ft.Container(
                                        content=self.board,
                                        padding=ft.Padding.symmetric(horizontal=12, vertical=14),
                                        bgcolor="transparent",
                                        border_radius=22,
                                    ),
                                    ft.Container(height=20),
                                    status_box,
                                ], horizontal_alignment="center", spacing=10),
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                bgcolor="transparent",
                            ),
                        ], spacing=22, alignment="center"),
                        padding=ft.Padding.symmetric(horizontal=18, vertical=18),
                        border_radius=24,
                        bgcolor=FELT_MID,
                        border=ft.Border.all(1, GOLD + "22"),
                    ),
                    margin=18,
                    alignment=ft.Alignment.CENTER,
                ),
            ]),
        )

    # ─── TABLERO DE APUESTAS ─────────────────────────────────────────────────
    def _create_felt_board(self):
        rows = [
            [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
        ]

        def _make_tile(val, w=46, h=58, color=None, label=None, font_size=14):
            tile_color = color or get_num_color(val)
            tile_label = label or str(val)
            slot_id = f"num_{val}" if isinstance(val, int) else val

            chips_overlay = ft.Stack([], width=w, height=h)
            self.bet_containers[slot_id] = chips_overlay

            return ft.GestureDetector(
                on_tap=lambda _: self.place_bet(slot_id),
                content=ft.Container(
                    width=w, height=h,
                    bgcolor=tile_color,
                    border=ft.Border.all(1, "#FFFFFF72"),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Stack([
                        ft.Container(
                            content=ft.Text(
                                tile_label, weight="bold",
                                size=font_size, color="white",
                                text_align="center",
                            ),
                            alignment=ft.Alignment.CENTER,
                        ),
                        chips_overlay,
                    ]),
                    animate=ft.Animation(120, "easeOut"),
                ),
            )

        zero = _make_tile(0, w=58, h=182)

        grid_cols = []
        for c in range(12):
            col = ft.Column([_make_tile(rows[r][c]) for r in range(3)], spacing=2)
            grid_cols.append(col)

        cols_label_color = "#1E0E08"
        cols_2to1 = ft.Column([
            _make_tile("COL_3", w=62, h=58, color=cols_label_color, label="2:1", font_size=12),
            _make_tile("COL_2", w=62, h=58, color=cols_label_color, label="2:1", font_size=12),
            _make_tile("COL_1", w=62, h=58, color=cols_label_color, label="2:1", font_size=12),
        ], spacing=2)

        main_grid = ft.Row([zero, ft.Row(grid_cols, spacing=2), cols_2to1], spacing=4)

        dozens_color = "#1C3A22"
        dozens = ft.Row([
            ft.Container(width=62),
            _make_tile("1st 12", w=188, h=40, color=dozens_color, label="1ª DOCENA", font_size=11),
            _make_tile("2nd 12", w=188, h=40, color=dozens_color, label="2ª DOCENA", font_size=11),
            _make_tile("3rd 12", w=188, h=40, color=dozens_color, label="3ª DOCENA", font_size=11),
        ], spacing=2)

        ext_color = "#1C3A22"
        groups = ft.Row([
            ft.Container(width=62),
            _make_tile("1-18",  w=94, h=50, color=ext_color,   label="1–18",   font_size=12),
            _make_tile("EVEN",  w=94, h=50, color=ext_color,   label="PAR",    font_size=12),
            _make_tile("RED",   w=94, h=50, color="#C72B2E",   label="●",      font_size=22),
            _make_tile("BLACK", w=94, h=50, color="#181818",   label="●",      font_size=22),
            _make_tile("ODD",   w=94, h=50, color=ext_color,   label="IMPAR",  font_size=12),
            _make_tile("19-36", w=94, h=50, color=ext_color,   label="19–36",  font_size=12),
        ], spacing=2)

        return ft.Column(
            [main_grid, ft.Container(height=4), dozens, ft.Container(height=4), groups],
            horizontal_alignment="center",
        )

    # ─── CHIP TRAY ──────────────────────────────────────────────────────────
    def _create_chip_tray(self):
        values = [1, 5, 10, 50, 100, 500]
        self.tray_icons = {}

        def _select(val):
            self.selected_chip_value = val
            for v, icon in self.tray_icons.items():
                is_active = v == val
                icon.border = ft.Border.all(3, GOLD if is_active else "transparent")
                icon.shadow  = ft.BoxShadow(blur_radius=18, color=GOLD + "88" if is_active else "transparent")
            self.main_page.update()

        row = ft.Row(spacing=16, alignment="center")
        for v in values:
            c = ft.GestureDetector(
                on_tap=lambda _, val=v: _select(val),
                content=ft.Container(
                    content=Chip(v, size=48),
                    border=ft.Border.all(3, GOLD if v == self.selected_chip_value else "transparent"),
                    border_radius=26, padding=3,
                    animate=ft.Animation(200, "easeOut"),
                    shadow=ft.BoxShadow(
                        blur_radius=18,
                        color=GOLD + "88" if v == self.selected_chip_value else "transparent",
                    ),
                ),
            )
            self.tray_icons[v] = c.content
            row.controls.append(c)

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "S E L E C C I O N A   F I C H A",
                    size=10, color="#8A94A6", weight="bold",
                    text_align="center",
                ),
                ft.Container(height=10),
                row,
            ], horizontal_alignment="center"),
            bgcolor="#12223A",
            padding=ft.Padding.symmetric(horizontal=22, vertical=18),
            border_radius=22,
            border=ft.Border.all(1, "#FFFFFF14"),
            shadow=ft.BoxShadow(blur_radius=18, color="#00000088"),
        )

    # ─── LÓGICA ─────────────────────────────────────────────────────────────
    def place_bet(self, slot_id):
        if self.spinning:
            return
        amount = self.selected_chip_value
        if self.jugador.saldo < amount:
            self.status_text.value = "⚠ SALDO INSUFICIENTE"
            self.status_text.color = CRIMSON
            self.update()
            return

        if not hasattr(self, "bet_history"):
            self.bet_history = []
        self.bet_history.append((slot_id, amount))

        self.jugador.saldo -= amount
        self.active_bets[slot_id] = self.active_bets.get(slot_id, 0) + amount

        stack = self.bet_containers[slot_id]
        offset = len(stack.controls) * 1.5
        stack.controls.append(
            ft.Container(content=Chip(amount, size=24), left=offset, top=offset)
        )

        _play("sounds/action.wav")
        total_bet = sum(self.active_bets.values())
        self.status_text.value = f"APUESTA TOTAL: ${total_bet:,.0f}"
        self.status_text.color = GOLD
        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.main_page.update()

    def undo_last_bet(self, e):
        if self.spinning or not getattr(self, "bet_history", None):
            return
        slot_id, amount = self.bet_history.pop()
        self.jugador.saldo += amount
        self.active_bets[slot_id] -= amount
        if self.active_bets[slot_id] <= 0:
            del self.active_bets[slot_id]
        stack = self.bet_containers[slot_id]
        if stack.controls:
            stack.controls.pop()
        total_bet = sum(self.active_bets.values())
        self.status_text.value = (
            f"DESHECHO: ${amount}" if total_bet > 0 else "REALIZA TUS APUESTAS"
        )
        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.main_page.update()

    def clear_bets(self, e):
        if self.spinning:
            return
        total = sum(self.active_bets.values())
        self.jugador.saldo += total
        self.active_bets.clear()
        if hasattr(self, "bet_history"):
            self.bet_history.clear()
        for stack in self.bet_containers.values():
            stack.controls.clear()
        self.status_text.value = "MESA LIMPIADA"
        self.status_text.color = "#C8CDD6"
        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.main_page.update()

    async def handle_spin(self, e):
        if self.spinning or not self.active_bets:
            if not self.active_bets:
                self.status_text.value = "COLOCA ALGUNA APUESTA"
                self.update()
            return

        self.spinning = True
        self.status_text.value = "✦  GIRANDO  ✦"
        self.status_text.color = GOLD
        self.spin_btn.disabled = True
        self.clear_btn.disabled = True
        self.undo_btn.disabled = True
        self.update()

        seg     = (2 * math.pi) / N
        cx, cy  = self._wx, self._wy
        R_OUTER = 160
        R_SETTLE= 132

        rotations      = random.randint(8, 12)
        wheel_extra    = random.uniform(0, 2 * math.pi)
        self._wheel_angle += rotations * 2 * math.pi + wheel_extra
        wheel_final = self._wheel_angle
        self.wheel_container.rotate.angle = wheel_final
        self.update()

        angle  = -math.pi / 2
        radius = float(R_OUTER)
        self.ball.visible = True

        def _mv(a, r):
            self.ball.left = cx + r * math.cos(a) - 7
            self.ball.top  = cy + r * math.sin(a) - 7

        for i in range(50):
            spd    = 0.38 - i * 0.003
            angle -= spd
            radius -= 0.15
            _mv(angle, radius)
            if i % 5 == 0:
                _play("sounds/tick.wav")
            self.update()
            await asyncio.sleep(0.05)

        spd = 0.18
        for i in range(30):
            spd    = max(0.06, 0.18 - i * 0.002)
            angle -= spd
            radius -= 0.90
            bounce = math.sin(i * 1.8) * 4.5 * max(0.0, (20 - i) / 20)
            _mv(angle, radius + bounce)
            if i % 3 == 0:
                _play("sounds/tick.wav")
            self.update()
            await asyncio.sleep(0.04)

        radius = max(R_SETTLE + 2, radius)
        while spd > 0.008:
            spd    *= 0.88
            angle  -= spd
            radius  = max(R_SETTLE, radius - 0.4)
            jitter  = spd * 18 * math.sin(angle * 4)
            _mv(angle, radius + abs(jitter))
            self.update()
            await asyncio.sleep(0.035)

        _mv(angle, R_SETTLE)
        self.update()

        # Calcular resultado
        ball_norm = angle % (2 * math.pi)
        min_dist, result_idx = float("inf"), 0
        for i in range(N):
            sa = (-math.pi / 2 + i * seg + wheel_final + CALIBRATION_OFFSET) % (2 * math.pi)
            d  = abs(sa - ball_norm)
            if d > math.pi:
                d = 2 * math.pi - d
            if d < min_dist:
                min_dist, result_idx = d, i
        result_num = WHEEL_ORDER[result_idx]

        target_a = (-math.pi / 2 + result_idx * seg + wheel_final + CALIBRATION_OFFSET) % (2 * math.pi)
        while target_a - (angle % (2 * math.pi)) > math.pi:  target_a -= 2 * math.pi
        while (angle % (2 * math.pi)) - target_a > math.pi:  target_a += 2 * math.pi
        for i in range(8):
            t = (i + 1) / 8
            a = (angle % (2 * math.pi)) + (target_a - (angle % (2 * math.pi))) * t
            _mv(a, R_SETTLE)
            self.update()
            await asyncio.sleep(0.03)

        await asyncio.sleep(0.25)

        # Resultado
        total_won = 0
        is_red  = result_num in RED_NUMBERS
        is_even = result_num != 0 and result_num % 2 == 0

        for slot_id, amount in self.active_bets.items():
            won, mul = False, 0
            if   slot_id == f"num_{result_num}":                                    won=True; mul=36
            elif slot_id == "RED"    and is_red:                                    won=True; mul=2
            elif slot_id == "BLACK"  and result_num != 0 and not is_red:            won=True; mul=2
            elif slot_id == "EVEN"   and is_even:                                   won=True; mul=2
            elif slot_id == "ODD"    and result_num != 0 and not is_even:           won=True; mul=2
            elif slot_id == "1-18"   and 1 <= result_num <= 18:                     won=True; mul=2
            elif slot_id == "19-36"  and 19 <= result_num <= 36:                    won=True; mul=2
            elif slot_id == "1st 12" and 1 <= result_num <= 12:                     won=True; mul=3
            elif slot_id == "2nd 12" and 13 <= result_num <= 24:                    won=True; mul=3
            elif slot_id == "3rd 12" and 25 <= result_num <= 36:                    won=True; mul=3
            elif slot_id == "COL_1"  and result_num != 0 and (result_num-1)%3 == 0: won=True; mul=3
            elif slot_id == "COL_2"  and result_num != 0 and (result_num-2)%3 == 0: won=True; mul=3
            elif slot_id == "COL_3"  and result_num != 0 and result_num%3 == 0:     won=True; mul=3
            if won:
                total_won += amount * mul

        self.jugador.saldo += total_won
        self.jugador.registrar_jugada(
            "Ruleta", sum(self.active_bets.values()), total_won, f"Cayó {result_num}"
        )
        self.storage.guardar_jugador(self.jugador)

        if total_won > 0:
            _play("sounds/win.wav")
            self.status_text.value  = f"🏆  GANASTE ${total_won:,.0f}  —  CAYÓ {result_num}"
            self.status_text.color  = EMERALD
        else:
            self.status_text.value  = f"Perdiste  ·  Cayó {result_num}"
            self.status_text.color  = CRIMSON

        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.spinning = False
        self.spin_btn.disabled = False
        self.clear_btn.disabled = False
        self.undo_btn.disabled = False

        await asyncio.sleep(2.5)
        if not self.spinning:
            self.active_bets.clear()
            for stack in self.bet_containers.values():
                stack.controls.clear()
            self.ball.visible = False
            self.main_page.refresh_balance()
            self.update()