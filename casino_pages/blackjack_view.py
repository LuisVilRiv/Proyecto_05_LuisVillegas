import flet as ft
import random
import asyncio

GOLD = "#F5B042"
DARK = "#05070A"
CARD_BG = "#0F1626"
EMERALD = "#10B981"
CRIMSON = "#E53E3E"
BLUE = "#3B82F6"

# Colores de palos
SUIT_COLOR = {"H": "#EF4444", "D": "#EF4444", "C": "#1A1A2E", "S": "#1A1A2E"}
SUIT_SYMBOL = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}

RANK_LABELS = {
    "A": "A", "2": "2", "3": "3", "4": "4", "5": "5",
    "6": "6", "7": "7", "8": "8", "9": "9", "10": "10",
    "J": "J", "Q": "Q", "K": "K",
}


def make_card(rank: str, suit: str, hidden=False, animate_in=False) -> ft.Container:
    """Crea una carta de blackjack con diseño premium."""
    if hidden:
        # Reverso de carta con patrón de diamantes
        back = ft.Container(
            width=85, height=120,
            bgcolor="#1A3A6B",
            border_radius=12,
            border=ft.Border.all(2, "#2D5A9E"),
            shadow=ft.BoxShadow(blur_radius=10, color="#00000066", offset=ft.Offset(2, 4)),
            content=ft.Column([
                ft.Container(
                    width=65, height=100,
                    border_radius=8,
                    bgcolor="#15306B",
                    border=ft.Border.all(1, "#2D5A9E"),
                    content=ft.Text("🂠", size=50, text_align=ft.TextAlign.CENTER),
                    alignment=ft.Alignment.CENTER,
                )
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            offset=ft.Offset(0, 0.3 if animate_in else 0),
            opacity=0 if animate_in else 1,
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )
        return back

    color = SUIT_COLOR.get(suit, "#F3F4F6")
    symbol = SUIT_SYMBOL.get(suit, "?")
    label = RANK_LABELS.get(rank, rank)

    card = ft.Container(
        width=85, height=120,
        bgcolor="#F8F9FA",
        border_radius=12,
        border=ft.Border.all(1, "#E5E7EB"),
        shadow=ft.BoxShadow(blur_radius=12, color="#00000055", offset=ft.Offset(2, 4)),
        offset=ft.Offset(0, 0.3 if animate_in else 0),
        opacity=0 if animate_in else 1,
        animate_offset=ft.Animation(280, ft.AnimationCurve.EASE_OUT),
        animate_opacity=ft.Animation(280, ft.AnimationCurve.EASE_OUT),
        content=ft.Stack([
            # Valor + palo arriba izquierda
            ft.Container(
                padding=ft.Padding.only(left=6, top=4),
                content=ft.Column([
                    ft.Text(label, size=14, weight="bold", color=color),
                    ft.Text(symbol, size=12, color=color),
                ], spacing=0),
                alignment=ft.Alignment(-1, -1),
            ),
            # Símbolo central grande
            ft.Container(
                content=ft.Text(symbol, size=36, color=color, weight="bold"),
                alignment=ft.Alignment.CENTER,
            ),
            # Valor + palo abajo derecha (rotado 180°)
            ft.Container(
                padding=ft.Padding.only(right=6, bottom=4),
                content=ft.Column([
                    ft.Text(symbol, size=12, color=color),
                    ft.Text(label, size=14, weight="bold", color=color),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                alignment=ft.Alignment(1, 1),
            ),
        ]),
    )
    return card


class BlackjackView(ft.Container):
    def __init__(self, page: ft.Page, jugador, storage):
        super().__init__(expand=True, padding=ft.Padding.symmetric(horizontal=40, vertical=20))
        self.main_page = page
        self.jugador = jugador
        self.storage = storage
        self.bet_amount = 0.0

        self.dealer_row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        self.player_row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        self.dealer_label = ft.Text("CROUPIER", size=13, color="#9CA3AF", weight="bold")
        self.player_label = ft.Text("TÚ", size=13, color=GOLD, weight="bold")
        self.dealer_score = ft.Text("●  ●", size=20, color="#9CA3AF", weight="bold")
        self.player_score = ft.Text("—", size=20, color=GOLD, weight="bold")

        self.status_text = ft.Text(
            "Pulsa REPARTIR para empezar", size=18, weight="bold", color="#9CA3AF",
            text_align=ft.TextAlign.CENTER
        )

        self.bet_input = ft.TextField(
            value="10", label="Apuesta ($)", width=130,
            border_color=GOLD, border_radius=10, color="white",
            text_align=ft.TextAlign.CENTER,
        )

        self.btn_deal = ft.FilledButton(
            content=ft.Row([ft.Icon(ft.Icons.CASINO, size=18), ft.Text("REPARTIR", weight="bold")],
                           spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            on_click=self.deal, width=155, height=52, bgcolor=EMERALD,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), color=DARK),
        )
        self.btn_hit = ft.FilledButton(
            content=ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=18), ft.Text("PEDIR", weight="bold")],
                           spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            on_click=self.hit, visible=False, width=140, height=52, bgcolor=BLUE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), color="white"),
        )
        self.btn_stand = ft.FilledButton(
            content=ft.Row([ft.Icon(ft.Icons.STOP_CIRCLE_OUTLINED, size=18), ft.Text("PLANTARSE", weight="bold")],
                           spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            on_click=self.stand, visible=False, width=155, height=52, bgcolor="#6B7280",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), color="white"),
        )

        self.deck: list[str] = []
        self.player_hand: list[str] = []
        self.dealer_hand: list[str] = []

        # ---- Mesa verde ----
        dealer_zone = ft.Container(
            content=ft.Column([
                ft.Row([self.dealer_label, ft.Container(expand=True), self.dealer_score],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=8, color="transparent"),
                self.dealer_row,
            ]),
            padding=20,
            bgcolor="#0A3020",
            border_radius=ft.BorderRadius(20, 20, 0, 0),
            border=ft.Border.all(1, "#1A5040"),
            shadow=ft.BoxShadow(blur_radius=20, color="#00000055"),
        )

        player_zone = ft.Container(
            content=ft.Column([
                self.player_row,
                ft.Divider(height=8, color="transparent"),
                ft.Row([self.player_label, ft.Container(expand=True), self.player_score],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            padding=20,
            bgcolor="#0A2818",
            border_radius=ft.BorderRadius(0, 0, 20, 20),
            border=ft.Border.all(1, "#1A5040"),
        )

        divider_felt = ft.Container(height=3, bgcolor="#14603A")

        table = ft.Column([dealer_zone, divider_felt, player_zone], spacing=0)

        controls_bar = ft.Container(
            content=ft.Row([
                self.bet_input,
                self.btn_deal,
                self.btn_hit,
                self.btn_stand,
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
            padding=ft.Padding.symmetric(vertical=12),
        )

        self.content = ft.Column(
            controls=[
                ft.Row([
                    ft.Text("♠ BLACKJACK ROYALE", size=28, weight="bold", color=GOLD),
                    ft.Container(expand=True),
                    ft.Text(f"💰 ${jugador.saldo:,.2f}", size=15, color=EMERALD, weight="bold"),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(height=10, color="transparent"),
                table,
                ft.Divider(height=8, color="transparent"),
                ft.Container(
                    content=self.status_text,
                    padding=12,
                    bgcolor="#FFFFFF08",
                    border_radius=12,
                ) ,
                controls_bar,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
        )

    # ---- Lógica de juego ----

    def _build_deck(self):
        """Zapato de 6 barajas (312 cartas) — estándar de casino real."""
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        suits = ["H", "D", "C", "S"]
        shoe = [f"{r}{s}" for r in ranks for s in suits] * 6   # 6 barajas
        random.shuffle(shoe)
        return shoe

    def _hand_value(self, hand):
        value, aces = 0, 0
        for card in hand:
            r = card[:-1]
            if r in ("J", "Q", "K"):
                value += 10
            elif r == "A":
                value += 11; aces += 1
            else:
                value += int(r)
        while value > 21 and aces:
            value -= 10; aces -= 1
        return value

    def _update_board(self, hide_dealer=False):
        self.player_row.controls = [
            make_card(c[:-1], c[-1], animate_in=False) for c in self.player_hand
        ]
        if hide_dealer:
            self.dealer_row.controls = [
                make_card(self.dealer_hand[0][:-1], self.dealer_hand[0][-1]),
                make_card("", "", hidden=True),
            ]
            self.dealer_score.value = "●  ●"
        else:
            self.dealer_row.controls = [
                make_card(c[:-1], c[-1]) for c in self.dealer_hand
            ]
            self.dealer_score.value = str(self._hand_value(self.dealer_hand))
        self.player_score.value = str(self._hand_value(self.player_hand))
        self.main_page.update()

    async def deal(self, e):
        try:
            apuesta = float(self.bet_input.value or "0")
        except ValueError:
            return
        if apuesta <= 0 or self.jugador.saldo < apuesta:
            self._set_status("Saldo insuficiente", CRIMSON)
            return

        self.bet_amount = apuesta
        self.deck = self._build_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]

        self.btn_deal.visible = False
        self.btn_hit.visible = True
        self.btn_stand.visible = True
        self._set_status("Tu turno — Pide o Plántate", "#9CA3AF")
        self._update_board(hide_dealer=True)

        if self._hand_value(self.player_hand) == 21:
            await self.stand(None)

    async def hit(self, e):
        self.player_hand.append(self.deck.pop())
        self._update_board(hide_dealer=True)
        if self._hand_value(self.player_hand) > 21:
            await self._end_game("💥 ¡Te pasaste!")

    async def stand(self, e):
        self.btn_hit.visible = False
        self.btn_stand.visible = False
        self._set_status("El croupier juega…", "#9CA3AF")
        self._update_board(hide_dealer=False)

        while self._hand_value(self.dealer_hand) < 17:
            await asyncio.sleep(0.6)
            self.dealer_hand.append(self.deck.pop())
            self._update_board(hide_dealer=False)

        p = self._hand_value(self.player_hand)
        d = self._hand_value(self.dealer_hand)

        if d > 21:   await self._end_game("Dealer se pasó. ¡GANASTE!")
        elif p > d:  await self._end_game("🏆 ¡GANASTE!")
        elif p < d:  await self._end_game("Dealer gana.")
        else:        await self._end_game("Empate — Push.")

    async def _end_game(self, msg):
        p = self._hand_value(self.player_hand)
        pago = 0
        if "GANASTE" in msg:
            pago = self.bet_amount * 2
            if p == 21 and len(self.player_hand) == 2:
                pago = self.bet_amount * 2.5  # Blackjack natural
        elif "Empate" in msg:
            pago = self.bet_amount

        self.jugador.registrar_jugada("Blackjack", self.bet_amount, pago, msg)
        self.storage.guardar_jugador(self.jugador)

        color = EMERALD if pago > self.bet_amount else ("#9CA3AF" if pago == self.bet_amount else CRIMSON)
        self._set_status(msg, color)
        self.btn_deal.visible = True
        self.btn_hit.visible = False
        self.btn_stand.visible = False

        self.main_page.refresh_balance()
        self.main_page.update()

    def _set_status(self, text, color):
        self.status_text.value = text
        self.status_text.color = color
        self.main_page.update()
