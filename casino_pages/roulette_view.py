import flet as ft
import random
import math
import asyncio

# --- COLORS & THEME ---
GOLD = "#F5B042"
GOLD_DARK = "#B8860B"
DARK = "#05070A"
EMERALD = "#10B981"
EMERALD_DARK = "#064E3B"
CRIMSON = "#E53E3E"
WOOD_DARK = "#3D1D13"
WOOD_LIGHT = "#5D2E1F"
SILVER = "#C0C0C0"

WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11,
    30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18,
    29, 7, 28, 12, 35, 3, 26
]
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
N = len(WHEEL_ORDER)

# --- UTILS ---
def get_num_color(n):
    if n == 0: return "#117A3C"
    return "#C0282B" if n in RED_NUMBERS else "#1C1C1C"

# --- COMPONENTS ---

class Chip(ft.Container):
    """High-fidelity vector chip using purely Flet primitives."""
    def __init__(self, value, size=32):
        colors = {
            1: ("#FFFFFF", "#D1D5DB"),
            5: ("#3B82F6", "#1D4ED8"),
            10: ("#EF4444", "#B91C1C"),
            50: ("#10B981", "#059669"),
            100: ("#1F2937", "#111827"),
            500: ("#8B5CF6", "#6D28D9"),
        }
        main_color, dark_color = colors.get(value, ("#F5B042", "#B8860B"))
        
        super().__init__(
            width=size, height=size,
            border_radius=size/2,
            bgcolor=main_color,
            border=ft.Border.all(2, "white" if value < 100 else "#F5B042"),
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(blur_radius=8, color="#00000088", offset=ft.Offset(2, 2)),
            content=ft.Stack([
                # Outer ring details
                ft.Container(
                    border=ft.Border.all(1, dark_color, ft.BorderStyle.SOLID),
                    border_radius=size/2,
                    margin=2,
                ),
                # Value label
                ft.Container(
                    content=ft.Text(str(value), size=size*0.4, weight="bold", color="white" if value > 1 else "black"),
                    alignment=ft.Alignment.CENTER,
                )
            ])
        )

def _build_realistic_wheel(size=320) -> ft.Stack:
    center = size / 2
    seg = 2 * math.pi / N
    label_r = center * 0.75
    hub_r = center * 0.22

    # 1. Outer Wood Frame (3D effect with radial/linear layering)
    outer_wood = ft.Container(
        width=size, height=size,
        border_radius=size / 2,
        gradient=ft.RadialGradient(
            colors=[WOOD_LIGHT, WOOD_DARK, "#1A0F0A"],
            center=ft.Alignment.CENTER,
            radius=1.0,
        ),
        shadow=ft.BoxShadow(blur_radius=20, color="black", spread_radius=2),
    )

    # 2. Chrome Ring (Sweep for rotation effect)
    chrome_ring = ft.Container(
        width=size * 0.96, height=size * 0.96,
        left=size * 0.02, top=size * 0.02,
        border_radius=size / 2,
        border=ft.Border.all(4, SILVER),
        gradient=ft.SweepGradient(
            colors=[SILVER, WHITE := "#FFFFFF", SILVER, "#888888", SILVER],
            stops=[0.0, 0.25, 0.5, 0.75, 1.0],
        )
    )

    # 3. Inner Number Track (Sweep Gradient)
    stops = []
    colors = []
    for i, num in enumerate(WHEEL_ORDER):
        col = get_num_color(num)
        stops.append(i / N)
        colors.append(col)
        stops.append((i + 1) / N - 0.001)
        colors.append(col)
    stops.append(1.0)
    colors.append(get_num_color(WHEEL_ORDER[0]))

    number_disc = ft.ShaderMask(
        shader=ft.PaintSweepGradient(
            center=ft.Alignment.CENTER,
            colors=colors,
            color_stops=stops,
            start_angle=-(math.pi / 2),
            end_angle=-(math.pi / 2) + 2 * math.pi,
        ),
        content=ft.Container(
            width=size * 0.88, height=size * 0.88,
            left=size * 0.06, top=size * 0.06,
            bgcolor="white",
            border_radius=size / 2,
        ),
    )

    # 4. Numbers and Dividers
    elements = []
    for i, num in enumerate(WHEEL_ORDER):
        angle = -(math.pi / 2) + i * seg + seg / 2
        nx = center + label_r * 0.92 * math.cos(angle)
        ny = center + label_r * 0.92 * math.sin(angle)
        
        elements.append(ft.Container(
            content=ft.Text(str(num), size=10, weight="bold", color="white"),
            left=nx - 10, top=ny - 8,
            width=20, height=16,
            alignment=ft.Alignment.CENTER,
            rotate=ft.Rotate(angle + math.pi/2),
        ))
        
        # Shiny Dividers
        d_angle = -(math.pi / 2) + i * seg
        dx = center + (center * 0.88) * math.cos(d_angle)
        dy = center + (center * 0.88) * math.sin(d_angle)
        elements.append(ft.Container(
            width=2, height=size*0.1,
            bgcolor=GOLD,
            left=dx - 1, top=dy - size*0.05,
            rotate=ft.Rotate(d_angle),
            opacity=0.6,
        ))

    # 5. Hub / Spinner
    hub = ft.Container(
        width=size * 0.3, height=size * 0.3,
        left=center - size * 0.15, top=center - size * 0.15,
        border_radius=size * 0.15,
        bgcolor="#111",
        border=ft.Border.all(3, GOLD),
        shadow=ft.BoxShadow(blur_radius=15, color="black"),
        gradient=ft.RadialGradient(
            colors=["#333", "black"],
            center=ft.Alignment.CENTER,
        ),
        content=ft.Stack([
            ft.Container(
                content=ft.Icon(ft.Icons.CASINO_ROUNDED, color=GOLD, size=24),
                alignment=ft.Alignment.CENTER,
            )
        ])
    )

    return ft.Stack(
        [outer_wood, chrome_ring, number_disc, *elements, hub],
        width=size, height=size,
    )

class RouletteView(ft.Container):
    def __init__(self, page: ft.Page, jugador, storage):
        super().__init__(expand=True, padding=20)
        self.main_page = page
        self.jugador = jugador
        self.storage = storage
        
        self.selected_chip_value = 10
        self.active_bets = {} # { "slot_id": total_amount }
        self.bet_containers = {} # { "slot_id": Container }
        self.spinning = False
        self.history = []

        # UI State
        self.status_text = ft.Text("REALIZA TUS APUESTAS", size=14, weight="bold", color="#9CA3AF")
        self.balance_text = ft.Text(f"SALDO: ${self.jugador.saldo:,.2f}", size=18, weight="bold", color=EMERALD)
        
        # --- WHEEL ---
        self.wheel_layer = _build_realistic_wheel(340)
        self.wheel_container = ft.Container(
            content=self.wheel_layer,
            rotate=ft.Rotate(0, alignment=ft.Alignment.CENTER),
            animate_rotation=ft.Animation(3500, ft.AnimationCurve.DECELERATE),
        )
        
        self.ball = ft.Container(
            width=14, height=14,
            bgcolor="white",
            border_radius=7,
            shadow=ft.BoxShadow(blur_radius=5, color="black"),
            offset=ft.Offset(0, -11), # Positioned at the outer rim initially
            animate_offset=ft.Animation(3500, ft.AnimationCurve.DECELERATE),
            visible=False,
        )

        wheel_area = ft.Stack([
            ft.Container(
                content=ft.Text("▼", color=GOLD, size=40),
                alignment=ft.Alignment.TOP_CENTER,
            ),
            ft.Container(
                content=self.wheel_container,
                margin=ft.padding.only(top=30),
            ),
            ft.Container(
                content=self.ball,
                width=340, height=340,
                margin=ft.padding.only(top=30),
                alignment=ft.Alignment.CENTER,
            )
        ], width=400, alignment=ft.Alignment.CENTER)

        # --- BETTING BOARD ---
        self.board = self._create_felt_board()

        # --- CHIP TRAY ---
        self.tray = self._create_chip_tray()

        # --- CONTROLS ---
        self.spin_btn = ft.FilledButton(
            "GIRAR RULETA",
            icon=ft.Icons.AUTORENEW_ROUNDED,
            on_click=self.handle_spin,
            width=200, height=54,
            bgcolor=GOLD,
            style=ft.ButtonStyle(color=DARK, shape=ft.RoundedRectangleBorder(radius=12)),
        )
        
        self.undo_btn = ft.IconButton(
            icon=ft.Icons.UNDO_ROUNDED,
            on_click=self.undo_last_bet,
            icon_color=GOLD,
            tooltip="Deshacer última apuesta",
        )
        
        self.clear_btn = ft.OutlinedButton(
            "LIMPIAR MESA",
            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
            on_click=self.clear_bets,
            width=180, height=54,
            style=ft.ButtonStyle(color=CRIMSON, side={ft.ControlState.DEFAULT: ft.BorderSide(1, CRIMSON)}),
        )

        # --- MAIN LAYOUT ---
        self.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("🎰 RULETA INTERACTIVA ROYALE", size=24, weight="bold", color=GOLD),
                    ft.Container(expand=True),
                    self.balance_text,
                ]),
                padding=ft.Padding.symmetric(horizontal=20)
            ),
            
            ft.Row([
                # Left: Wheel and info
                ft.Column([
                    wheel_area,
                    ft.Container(height=20),
                    ft.Container(
                        content=self.status_text,
                        bgcolor="#111B2D",
                        padding=15,
                        border_radius=12,
                        border=ft.Border.all(1, "#FFFFFF11"),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Container(height=20),
                    ft.Row([self.spin_btn, self.clear_btn, self.undo_btn], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                ], expand=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                
                # Right: Board
                ft.Column([
                    ft.Container(
                        content=self.board,
                        bgcolor="#064E3B",
                        padding=20,
                        border_radius=20,
                        border=ft.Border.all(3, WOOD_DARK),
                        shadow=ft.BoxShadow(blur_radius=30, color="black"),
                    ),
                    ft.Container(height=20),
                    self.tray,
                ], expand=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ], expand=True, spacing=40),
        ])

    def _create_felt_board(self):
        # 3x12 Grid + 0 block + Bottom groups
        rows = [
            [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
        ]
        
        def _make_tile(val, w=45, h=60, color=None, label=None):
            tile_color = color or get_num_color(val)
            tile_label = label or str(val)
            slot_id = f"num_{val}" if isinstance(val, int) else val
            
            # Stack to hold the tile + placed chips
            chips_overlay = ft.Stack([], width=w, height=h)
            self.bet_containers[slot_id] = chips_overlay
            
            return ft.GestureDetector(
                on_tap=lambda _: self.place_bet(slot_id),
                content=ft.Container(
                    width=w, height=h,
                    bgcolor=tile_color,
                    border=ft.Border.all(1, "white54"),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Stack([
                        ft.Container(content=ft.Text(tile_label, weight="bold", size=14, color="white"), alignment=ft.Alignment.CENTER),
                        chips_overlay
                    ])
                )
            )

        # Zero block
        zero = _make_tile(0, w=60, h=184) # Covers all 3 rows height

        grid_cols = []
        for c in range(12):
            col = ft.Column([_make_tile(rows[r][c]) for r in range(3)], spacing=2)
            grid_cols.append(col)

        # Columns (2 to 1) at the end of each row
        cols_2to1 = ft.Column([
            _make_tile("COL_3", w=60, h=60, color="#1A0F0A", label="2 to 1"),
            _make_tile("COL_2", w=60, h=60, color="#1A0F0A", label="2 to 1"),
            _make_tile("COL_1", w=60, h=60, color="#1A0F0A", label="2 to 1"),
        ], spacing=2)

        main_grid = ft.Row([zero, ft.Row(grid_cols, spacing=2), cols_2to1], spacing=4)

        # Dozens (1st 12, etc.)
        dozens = ft.Row([
            ft.Container(width=64), # Padding for zero
            _make_tile("1st 12", w=186, h=40, color="#1A0F0A", label="1st 12"),
            _make_tile("2nd 12", w=186, h=40, color="#1A0F0A", label="2nd 12"),
            _make_tile("3rd 12", w=186, h=40, color="#1A0F0A", label="3rd 12"),
        ], spacing=2)

        # External groups (Red/Black, etc.)
        groups_red_black = ft.Row([
            ft.Container(width=64), # Padding for zero
            _make_tile("1-18", w=92, h=50, color="#1A0F0A", label="1-18"),
            _make_tile("EVEN", w=92, h=50, color="#1A0F0A", label="PAR"),
            _make_tile("RED", w=92, h=50, color="#C0282B", label="ROJO"),
            _make_tile("BLACK", w=92, h=50, color="#1C1C1C", label="NEGRO"),
            _make_tile("ODD", w=92, h=50, color="#1A0F0A", label="IMPAR"),
            _make_tile("19-36", w=92, h=50, color="#1A0F0A", label="19-36"),
        ], spacing=2)

        return ft.Column([
            main_grid,
            ft.Container(height=4),
            dozens,
            ft.Container(height=4),
            groups_red_black
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _create_chip_tray(self):
        values = [1, 5, 10, 50, 100, 500]
        self.tray_icons = {}
        
        def _select(val):
            self.selected_chip_value = val
            for v, icon in self.tray_icons.items():
                icon.border = ft.Border.all(3, GOLD if v == val else "transparent")
                icon.shadow = ft.BoxShadow(blur_radius=15, color=GOLD if v == val else "transparent")
            self.main_page.update()

        row = ft.Row(spacing=20, alignment=ft.MainAxisAlignment.CENTER)
        for v in values:
            c = ft.GestureDetector(
                on_tap=lambda _, val=v: _select(val),
                content=ft.Container(
                    content=Chip(v, size=46),
                    border=ft.Border.all(3, GOLD if v == self.selected_chip_value else "transparent"),
                    border_radius=25,
                    padding=2,
                    animate=ft.Animation(200, "easeOut"),
                )
            )
            self.tray_icons[v] = c.content
            row.controls.append(c)
        
        return ft.Container(
            content=row,
            bgcolor="#111B2D",
            padding=15,
            border_radius=30,
            border=ft.Border.all(1, "#FFFFFF11"),
        )

    def place_bet(self, slot_id):
        if self.spinning: return
        
        amount = self.selected_chip_value
        if self.jugador.saldo < amount:
            self.status_text.value = "SALDO INSUFICIENTE"
            self.status_text.color = CRIMSON
            self.update()
            return

        # Keep track of history for UNDO
        if not hasattr(self, "bet_history"): self.bet_history = []
        self.bet_history.append((slot_id, amount))
        
        # Deduct balance
        self.jugador.saldo -= amount
        self.active_bets[slot_id] = self.active_bets.get(slot_id, 0) + amount
        
        # Visual chip
        stack = self.bet_containers[slot_id]
        # Offset chips slightly if stacked
        offset = len(stack.controls) * 1.5
        stack.controls.append(
            ft.Container(
                content=Chip(amount, size=24),
                left=offset, top=offset,
            )
        )
        
        total_bet = sum(self.active_bets.values())
        self.status_text.value = f"APUESTA TOTAL: ${total_bet:,.0f}"
        self.status_text.color = GOLD
        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.main_page.update()

    def undo_last_bet(self, e):
        if self.spinning or not getattr(self, "bet_history", None): return
        
        slot_id, amount = self.bet_history.pop()
        
        # Refund
        self.jugador.saldo += amount
        self.active_bets[slot_id] -= amount
        if self.active_bets[slot_id] <= 0:
            del self.active_bets[slot_id]
        
        # Remove visual chip
        stack = self.bet_containers[slot_id]
        if stack.controls:
            stack.controls.pop()
        
        total_bet = sum(self.active_bets.values())
        self.status_text.value = f"DESHECHO: ${amount}" if total_bet > 0 else "REALIZA TUS APUESTAS"
        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.main_page.update()

    def clear_bets(self, e):
        if self.spinning: return
        # Refund total
        total = sum(self.active_bets.values())
        self.jugador.saldo += total
        self.active_bets.clear()
        if hasattr(self, "bet_history"): self.bet_history.clear()
        for stack in self.bet_containers.values():
            stack.controls.clear()
        
        self.status_text.value = "MESA LIMPIADA"
        self.status_text.color = "#9CA3AF"
        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.main_page.update()

    async def handle_spin(self, e):
        if self.spinning or not self.active_bets: 
            if not self.active_bets: self.status_text.value = "COLOCA ALGUNA APUESTA"; self.update()
            return
        
        self.spinning = True
        self.status_text.value = "Girando..."
        self.status_text.color = GOLD
        self.spin_btn.disabled = True
        self.clear_btn.disabled = True
        self.undo_btn.disabled = True
        self.update()

        # Generate result
        result_num = random.choice(WHEEL_ORDER)
        
        # Animation target
        idx = WHEEL_ORDER.index(result_num)
        seg = (2 * math.pi) / N
        # Target angle to align index 0 with top ▼
        # The ▼ is at index 0. So if result is index `idx`, we need to rotate wheel by `-idx * seg`
        # Plus multiple full rotations
        rotations = random.randint(8, 12)
        target_angle = (rotations * 2 * math.pi) - (idx * seg)
        
        self.wheel_container.rotate.angle = target_angle
        
        # Ball animation
        self.ball.visible = True
        # The ball "falls" toward the inner track
        self.ball.offset = ft.Offset(0.1 * random.random(), -0.4) 
        
        self.update()
        await asyncio.sleep(3.6)
        
        # Ball "lands" in a slot (jitter effect)
        self.ball.offset = ft.Offset(0, -0.3)
        self.update()
        await asyncio.sleep(0.4)

        # Logic: Check all bets
        total_won = 0
        details = []
        is_red = result_num in RED_NUMBERS
        is_even = result_num != 0 and result_num % 2 == 0
        
        for slot_id, amount in self.active_bets.items():
            won = False
            multiplier = 0
            
            if slot_id == f"num_{result_num}":
                won = True; multiplier = 36
            elif slot_id == "RED" and is_red:
                won = True; multiplier = 2
            elif slot_id == "BLACK" and result_num != 0 and not is_red:
                won = True; multiplier = 2
            elif slot_id == "EVEN" and is_even:
                won = True; multiplier = 2
            elif slot_id == "ODD" and result_num != 0 and not is_even:
                won = True; multiplier = 2
            elif slot_id == "1-18" and 1 <= result_num <= 18:
                won = True; multiplier = 2
            elif slot_id == "19-36" and 19 <= result_num <= 36:
                won = True; multiplier = 2
            elif slot_id == "1st 12" and 1 <= result_num <= 12:
                won = True; multiplier = 3
            elif slot_id == "2nd 12" and 13 <= result_num <= 24:
                won = True; multiplier = 3
            elif slot_id == "3rd 12" and 25 <= result_num <= 36:
                won = True; multiplier = 3
            elif slot_id == "COL_1" and result_num != 0 and (result_num - 1) % 3 == 0:
                won = True; multiplier = 3
            elif slot_id == "COL_2" and result_num != 0 and (result_num - 2) % 3 == 0:
                won = True; multiplier = 3
            elif slot_id == "COL_3" and result_num != 0 and result_num % 3 == 0:
                won = True; multiplier = 3
            
            if won:
                prize = amount * multiplier
                total_won += prize
                details.append(f"{slot_id}: +${prize}")

        # Update player
        self.jugador.saldo += total_won
        self.jugador.registrar_jugada("Ruleta", sum(self.active_bets.values()), total_won, f"Cayó {result_num}")
        self.storage.guardar_jugador(self.jugador)

        # Update UI
        if total_won > 0:
            self.status_text.value = f"¡GANASTE ${total_won:,.0f}! (CAYÓ {result_num})"
            self.status_text.color = EMERALD
        else:
            self.status_text.value = f"PERDISTE (CAYÓ {result_num})"
            self.status_text.color = CRIMSON
        
        self.balance_text.value = f"SALDO: ${self.jugador.saldo:,.2f}"
        self.spinning = False
        self.spin_btn.disabled = False
        self.clear_btn.disabled = False
        self.undo_btn.disabled = False
        
        # Clear visual bets after result (casino cleanup)
        await asyncio.sleep(2)
        if not self.spinning:
            self.active_bets.clear()
            for stack in self.bet_containers.values():
                stack.controls.clear()
            self.ball.visible = False
            self.main_page.refresh_balance()
            self.update()
