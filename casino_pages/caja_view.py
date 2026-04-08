import flet as ft

GOLD = "#F5B042"
DARK = "#05070A"
CARD_BG = "#0F1626"
EMERALD = "#10B981"
CRIMSON = "#E53E3E"


def _quick_amount_btn(label, on_click) -> ft.Container:
    return ft.Container(
        content=ft.Text(label, size=13, weight="bold", color=GOLD),
        on_click=on_click,
        bgcolor="#F5B04215",
        border=ft.Border.all(1, GOLD + "44"),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


class CajaView(ft.Container):
    def __init__(self, page: ft.Page, jugador, storage):
        super().__init__(
            expand=True,
            padding=ft.Padding.symmetric(horizontal=50, vertical=24),
        )
        self.main_page = page
        self.jugador = jugador
        self.storage = storage

        # --- Saldo grande ---
        self.saldo_display = ft.Text(
            f"${self.jugador.saldo:,.2f}",
            size=56, weight="bold", color=EMERALD,
        )

        # --- Input de monto ---
        self.amount_input = ft.TextField(
            label="Monto a operar",
            width=260,
            border_color=GOLD,
            border_radius=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            color="white",
            prefix=ft.Text("$  ", color="#9CA3AF"),
            text_size=18,
        )

        def set_amount(val):
            def handler(e):
                self.amount_input.value = str(val)
                self.main_page.update()
            return handler

        quick_btns = ft.Row(
            [_quick_amount_btn(f"${v}", set_amount(v)) for v in [10, 50, 100, 500, 1000]],
            spacing=8, alignment=ft.MainAxisAlignment.CENTER,
        )

        # --- Botones de acción ---
        deposit_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=20), ft.Text("DEPOSITAR", weight="bold", size=15)],
                spacing=8, alignment=ft.MainAxisAlignment.CENTER,
            ),
            on_click=self.handle_deposit,
            width=185, height=55, bgcolor=EMERALD,
            style=ft.ButtonStyle(
                color=DARK,
                shape=ft.RoundedRectangleBorder(radius=14),
                overlay_color={ft.ControlState.HOVERED: "#0DA070"},
            ),
        )
        withdraw_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.REMOVE_CIRCLE_OUTLINE, size=20), ft.Text("RETIRAR", weight="bold", size=15)],
                spacing=8, alignment=ft.MainAxisAlignment.CENTER,
            ),
            on_click=self.handle_withdraw,
            width=185, height=55, bgcolor=CRIMSON,
            style=ft.ButtonStyle(
                color="white",
                shape=ft.RoundedRectangleBorder(radius=14),
                overlay_color={ft.ControlState.HOVERED: "#B03030"},
            ),
        )

        # --- Historial de movimientos ---
        movimientos = self.jugador.historial[::-1][:8]

        def _mov_card(m):
            positivo = m.get("balance", 0) > 0
            amount_color = EMERALD if positivo else CRIMSON
            icon = ft.Icons.ARROW_UPWARD if positivo else ft.Icons.ARROW_DOWNWARD
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=18, color=amount_color),
                        width=36, height=36, border_radius=18,
                        bgcolor=amount_color + "22",
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column([
                        ft.Text(m.get("detalle", "—").title(), size=14, weight="bold", color="white"),
                        ft.Text(m.get("fecha", ""), size=11, color="#6B7280"),
                    ], spacing=1, expand=True),
                    ft.Text(
                        f"{m.get('balance', 0):+,.2f}",
                        size=16, weight="bold", color=amount_color,
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#111B2D",
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                border=ft.Border.all(1, amount_color + "22"),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            )

        historial_col = ft.Column(
            controls=[_mov_card(m) for m in movimientos] if movimientos else [
                ft.Text("Sin movimientos aún", color="#6B7280", size=14, italic=True)
            ],
            spacing=8,
        )

        # --- Layout principal ---
        self.content = ft.Row(
            controls=[
                # Panel izquierdo (saldo + operaciones)
                ft.Container(
                    content=ft.Column([
                        ft.Text("S A L D O   D I S P O N I B L E", size=11, weight="bold", color="#9CA3AF"),
                        ft.Divider(height=6, color="transparent"),
                        self.saldo_display,
                        ft.Divider(height=28, color="#FFFFFF11"),
                        self.amount_input,
                        ft.Divider(height=10, color="transparent"),
                        quick_btns,
                        ft.Divider(height=20, color="transparent"),
                        ft.Row([deposit_btn, withdraw_btn], spacing=16, alignment=ft.MainAxisAlignment.CENTER),
                    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=2,
                    bgcolor=CARD_BG,
                    border_radius=20,
                    padding=30,
                    border=ft.Border.all(1, "#FFFFFF11"),
                    shadow=ft.BoxShadow(blur_radius=30, color="#00000055"),
                ),

                ft.Container(width=24),

                # Panel derecho (historial)
                ft.Container(
                    content=ft.Column([
                        ft.Text("Ú L T I M O S   M O V I M I E N T O S", size=11, weight="bold", color="#9CA3AF"),
                        ft.Divider(height=14, color="transparent"),
                        historial_col,
                    ], spacing=0),
                    expand=3,
                    bgcolor=CARD_BG,
                    border_radius=20,
                    padding=24,
                    border=ft.Border.all(1, "#FFFFFF11"),
                    shadow=ft.BoxShadow(blur_radius=30, color="#00000055"),
                ),
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def handle_deposit(self, e):
        try:
            val = float(self.amount_input.value or "0")
            if val <= 0:
                raise ValueError("Monto debe ser positivo")
            self.jugador.depositar(val)
            self.storage.guardar_jugador(self.jugador)
            self.saldo_display.value = f"${self.jugador.saldo:,.2f}"
            self._show_notification(f"✅  Depósito de ${val:,.2f} realizado", EMERALD)
        except Exception as err:
            self._show_notification(f"❌  {err}", CRIMSON)

    def handle_withdraw(self, e):
        try:
            val = float(self.amount_input.value or "0")
            if val <= 0:
                raise ValueError("Monto debe ser positivo")
            self.jugador.retirar(val)
            self.storage.guardar_jugador(self.jugador)
            self.saldo_display.value = f"${self.jugador.saldo:,.2f}"
            self._show_notification(f"✅  Retiro de ${val:,.2f} realizado", CRIMSON)
        except Exception as err:
            self._show_notification(f"❌  {err}", CRIMSON)

    def _show_notification(self, msg, color):
        sb = ft.SnackBar(
            ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color="white"), ft.Text(msg, color="white", weight="bold")]),
            bgcolor=color,
            duration=3000,
        )
        self.main_page.overlay.append(sb)
        sb.open = True
        self.main_page.refresh_balance()
        self.main_page.update()
