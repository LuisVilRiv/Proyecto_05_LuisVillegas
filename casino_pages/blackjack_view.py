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
            daemon=True
        ).start()

# ─── PALETA REFINADA ────────────────────────────────────────────────────────
GOLD    = "#F5B042"
DARK    = "#05070A"
CARD_BG = "#0F1A2E"
EMERALD = "#1FD090"        # ↑ más brillante → mayor contraste sobre fondo oscuro
CRIMSON = "#F04040"        # ↑ ligeramente más vivo
BLUE    = "#4A9EFF"        # ↑ más luminoso que #3B82F6

# Colores de palos — los de copa y diamante se mantienen rojo puro;
# picas y tréboles usamos un negro cálido (nunca navy puro) para que
# el símbolo se lea bien en la carta blanca
SUIT_COLOR  = {"H": "#D62B2B", "D": "#D62B2B", "C": "#1A1A1A", "S": "#1A1A1A"}
SUIT_SYMBOL = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}
RANK_LABELS = {
    "A": "A", "2": "2", "3": "3", "4": "4", "5": "5",
    "6": "6", "7": "7", "8": "8", "9": "9", "10": "10",
    "J": "J", "Q": "Q", "K": "K",
}

# Fondos de fieltro (más ricos)
FELT_CENTER = "#1D7044"
FELT_MID    = "#155534"
FELT_DARK   = "#0C3A20"
FELT_EDGE   = "#071E10"
WOOD_MID    = "#3A1A0C"
WOOD_BASE   = "#1A0A04"


def make_card(rank: str, suit: str, hidden=False, animate_in=False) -> ft.Container:
    if hidden:
        return ft.Container(
            width=90, height=130, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=15, color="#000000AA", offset=ft.Offset(3, 5)),
            content=ft.Image(src="cards/back.png", fit="cover", border_radius=12),
            offset=ft.Offset(0, 0.4 if animate_in else 0),
            opacity=0 if animate_in else 1,
            animate_offset=ft.Animation(400, "easeOut"),
            animate_opacity=ft.Animation(400, "easeOut"),
        )

    color  = SUIT_COLOR.get(suit, "#D62B2B")
    symbol = SUIT_SYMBOL.get(suit, "?")
    label  = RANK_LABELS.get(rank, rank)

    return ft.Container(
        width=90, height=130,
        bgcolor="#FDFDFD",
        border_radius=12,
        border=ft.Border.all(1, "#CCCCCC"),
        shadow=ft.BoxShadow(blur_radius=16, color="#00000077", offset=ft.Offset(2, 5)),
        offset=ft.Offset(0, 0.4 if animate_in else 0),
        opacity=0 if animate_in else 1,
        animate_offset=ft.Animation(350, "easeOutBack"),
        animate_opacity=ft.Animation(350, "easeOut"),
        content=ft.Stack([
            ft.Container(
                gradient=ft.RadialGradient(
                    center=ft.Alignment(0, 0), radius=1.5,
                    colors=["#FFFFFF", "#F2F2F2"],
                ),
                border_radius=12,
            ),
            ft.Container(
                padding=ft.padding.only(left=8, top=6),
                content=ft.Column([
                    ft.Text(label, size=18, weight="bold", color=color),
                    ft.Text(symbol, size=14, color=color),
                ], spacing=-2),
                alignment=ft.Alignment(-1, -1),
            ),
            ft.Container(
                content=ft.Text(symbol, size=48, color=color, weight="bold"),
                alignment=ft.Alignment.CENTER,
            ),
            ft.Container(
                padding=ft.padding.only(right=8, bottom=6),
                content=ft.Column([
                    ft.Text(symbol, size=14, color=color),
                    ft.Text(label, size=18, weight="bold", color=color),
                ], spacing=-2, horizontal_alignment="end"),
                alignment=ft.Alignment(1, 1),
            ),
        ]),
    )


class BlackjackView(ft.Container):
    def __init__(self, page: ft.Page, jugador, storage):
        super().__init__(
            expand=True,
            padding=ft.padding.symmetric(horizontal=40, vertical=24),
            bgcolor=CARD_BG,
            border_radius=28,
            border=ft.Border.all(1, "#FFFFFF12"),
            shadow=ft.BoxShadow(blur_radius=30, color="#00000088", offset=ft.Offset(0, 10)),
        )
        self.main_page = page
        self.jugador   = jugador
        self.storage   = storage
        self.bet_amount = 0.0

        self.dealer_row = ft.Row(spacing=-20, alignment="center")
        self.player_row = ft.Row(spacing=-20, alignment="center")

        self.dealer_label = ft.Text("BANCA",    size=13, color="#B0B8C8", weight="bold")  # ↑
        self.player_label = ft.Text("JUGADOR",  size=13, color=GOLD,     weight="bold")
        self.dealer_score = ft.Text("?",        size=22, color="#B0B8C8", weight="bold")  # ↑
        self.player_score = ft.Text("—",        size=22, color=GOLD,     weight="bold")

        self.status_text = ft.Text(
            "MESA DE ALTA APUESTA",
            size=18, weight="bold", color="#C8CDD6",    # ↑ era #9CA3AF
            text_align="center",
        )

        self.bet_input = ft.TextField(
            value="10", label="Apuesta ($)", width=150,
            border_color=GOLD + "88", border_radius=16, color="white",
            bgcolor="#172B46", content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
            text_align="center", focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#8A94A6"),
        )

        # ── Botones ──
        self.btn_deal = ft.FilledButton(
            content=ft.Text("REPARTIR", weight="bold"),
            on_click=self.deal, width=160, height=55, bgcolor=GOLD,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=15), color=DARK,
                overlay_color={ft.ControlState.HOVERED: "#D4930A"},
                shadow_color=GOLD + "55", elevation=5,
            ),
        )
        self.btn_hit = ft.FilledButton(
            content=ft.Text("PEDIR CARTA", weight="bold"),
            on_click=self.hit, visible=False, width=150, height=55, bgcolor=BLUE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=15), color="white",
                overlay_color={ft.ControlState.HOVERED: "#2D7ACC"},
                shadow_color=BLUE + "44", elevation=5,
            ),
        )
        self.btn_stand = ft.FilledButton(
            content=ft.Text("PLANTARSE", weight="bold"),
            on_click=self.stand, visible=False, width=150, height=55, bgcolor="#4B5563",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=15), color="white",
                overlay_color={ft.ControlState.HOVERED: "#374151"},
                shadow_color="#37415155", elevation=4,
            ),
        )

        self.deck: list[str] = []
        self.player_hand: list[str] = []
        self.dealer_hand: list[str] = []

        # ── Mesa de casino unificada ──
        table_felt = ft.Container(
            width=940,
            border_radius=28,
            border=ft.Border.all(2, GOLD + "88"),
            bgcolor="#0B2E1A",
            padding=ft.padding.symmetric(horizontal=24, vertical=22),
            shadow=ft.BoxShadow(blur_radius=48, color="#00000099", spread_radius=8, offset=ft.Offset(0, 12)),
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("BLACKJACK  PAYS  3  TO  2", size=12, weight="bold", color="#FFFFFF66", font_family="serif"),
                        ft.Container(height=10),
                        ft.Row([self.dealer_label, ft.Container(expand=True), self.dealer_score], alignment="center"),
                        ft.Container(height=16),
                        self.dealer_row,
                    ], spacing=0),
                ], alignment="center"),
                ft.Container(height=14, width=860, bgcolor="#FFFFFF10"),
                ft.Container(height=18),
                ft.Row([
                    self.player_label,
                    ft.Container(expand=True),
                    self.player_score,
                ], alignment="center"),
                ft.Container(height=10),
                self.player_row,
                ft.Container(height=18),
                ft.Text("INSURANCE  PAYS  2  TO  1", size=11, weight="bold", color="#FFFFFF44", font_family="serif", text_align="center"),
            ], spacing=16, horizontal_alignment="center"),
        )

        self.saldo_display = ft.Text(
            f"${jugador.saldo:,.2f}", size=16, color=EMERALD, weight="bold",
        )

        self.content = ft.Column(
            controls=[
                # Header
                ft.Row([
                    ft.Column([
                        ft.Text("ROYALE BLACKJACK", size=30, weight="bold", color=GOLD),
                        ft.Text("♠  HIGH STAKES TABLE  ♠", size=11, color="#7E8A9F", weight="bold"),
                    ], spacing=2),
                    ft.Container(expand=True),
                    ft.Container(
                        content=self.saldo_display,
                        padding=ft.padding.symmetric(horizontal=14, vertical=8),
                        bgcolor=EMERALD + "14",
                        border_radius=10,
                        border=ft.Border.all(1, EMERALD + "44"),
                    ),
                ]),
                ft.Container(height=20),
                table_felt,
                ft.Container(height=18),
                # Status
                ft.Container(
                    content=self.status_text,
                    padding=14,
                    bgcolor="#111E30",
                    border_radius=14,
                    border=ft.Border.all(1, "#FFFFFF22"),
                ),
                # Controles
                ft.Container(
                    content=ft.Row(
                        [self.bet_input, self.btn_deal, self.btn_hit, self.btn_stand],
                        alignment="center", spacing=20,
                    ),
                    padding=ft.padding.symmetric(vertical=20),
                ),
            ],
            expand=True,
        )
        self.deck = self._build_deck()

    # ─── LÓGICA ─────────────────────────────────────────────────────────────
    def _build_deck(self):
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        suits = ["H", "D", "C", "S"]
        shoe  = [f"{r}{s}" for r in ranks for s in suits] * 6
        import secrets
        rng = random.Random(secrets.token_bytes(32))
        rng.shuffle(shoe)
        rng.shuffle(shoe)
        return shoe

    def _hand_value(self, hand):
        value, aces = 0, 0
        for card in hand:
            r = card[:-1]
            if r in ("J", "Q", "K"):  value += 10
            elif r == "A":             value += 11; aces += 1
            else:                      value += int(r)
        while value > 21 and aces:
            value -= 10; aces -= 1
        return value

    async def _update_board(self, hide_dealer=False):
        self.player_row.controls = [make_card(c[:-1], c[-1]) for c in self.player_hand]
        if hide_dealer:
            self.dealer_row.controls = [
                make_card(self.dealer_hand[0][:-1], self.dealer_hand[0][-1]),
                make_card("", "", hidden=True),
            ]
            self.dealer_score.value = "?"
        else:
            self.dealer_row.controls = [make_card(c[:-1], c[-1]) for c in self.dealer_hand]
            self.dealer_score.value  = str(self._hand_value(self.dealer_hand))
        self.player_score.value = str(self._hand_value(self.player_hand))
        self.main_page.update()

    async def deal(self, e):
        try:
            apuesta = float(self.bet_input.value or "0")
        except ValueError:
            return
        if apuesta <= 0 or self.jugador.saldo < apuesta:
            self._set_status("⚠ Saldo insuficiente", CRIMSON)
            return

        self.bet_amount = apuesta
        self.jugador.saldo -= apuesta
        self.saldo_display.value = f"${self.jugador.saldo:,.2f}"

        if len(self.deck) < 52:
            self.deck = self._build_deck()
            self._set_status("♻  Nuevo shoe barajado", "#8A94A6")
            await asyncio.sleep(0.8)

        p1, d1, p2, d2 = self.deck.pop(), self.deck.pop(), self.deck.pop(), self.deck.pop()
        self.player_hand = [p1, p2]
        self.dealer_hand = [d1, d2]

        self.btn_deal.visible  = False
        self.btn_hit.visible   = True
        self.btn_stand.visible = True
        self._set_status("¿Pedir carta o Plantarse?", GOLD)

        _play("sounds/action.wav")
        await self._update_board(hide_dealer=True)

        player_bj = self._hand_value(self.player_hand) == 21
        dealer_bj = self._hand_value(self.dealer_hand) == 21

        if dealer_bj or player_bj:
            self.btn_hit.visible   = False
            self.btn_stand.visible = False
            await self._update_board(hide_dealer=False)
            await asyncio.sleep(0.6)
            if dealer_bj and player_bj:
                await self._end_game("EMPATE — DOBLE BLACKJACK")
            elif dealer_bj:
                await self._end_game("BLACKJACK DE LA BANCA")
            else:
                await self._end_game("🃏 ¡BLACKJACK! GANASTE")

    async def hit(self, e):
        _play("sounds/action.wav")
        self.player_hand.append(self.deck.pop())
        await self._update_board(hide_dealer=True)
        if self._hand_value(self.player_hand) > 21:
            await self._end_game("💥 TE PASASTE")

    async def stand(self, e):
        self.btn_hit.visible   = False
        self.btn_stand.visible = False
        await self._update_board(hide_dealer=False)

        while self._hand_value(self.dealer_hand) < 17:
            await asyncio.sleep(0.8)
            _play("sounds/action.wav")
            self.dealer_hand.append(self.deck.pop())
            await self._update_board(hide_dealer=False)

        p, d = self._hand_value(self.player_hand), self._hand_value(self.dealer_hand)
        if   d > 21: await self._end_game("¡LA BANCA SE PASA! GANASTE")
        elif p > d:  await self._end_game("🏆 ¡GANASTE!")
        elif p < d:  await self._end_game("GANA LA BANCA")
        else:        await self._end_game("EMPATE")

    async def _end_game(self, msg):
        p    = self._hand_value(self.player_hand)
        pago = 0
        if "GANASTE" in msg:
            pago = self.bet_amount * 2
            if p == 21 and len(self.player_hand) == 2:
                pago = self.bet_amount * 2.5
            _play("sounds/win.wav")
        elif "EMPATE" in msg:
            pago = self.bet_amount

        self.jugador.saldo += pago
        self.jugador.registrar_jugada("Blackjack", self.bet_amount, pago, msg)
        self.storage.guardar_jugador(self.jugador)

        color = EMERALD if pago > self.bet_amount else (GOLD if pago == self.bet_amount else CRIMSON)
        self._set_status(msg, color)
        self.saldo_display.value = f"${self.jugador.saldo:,.2f}"
        self.btn_deal.visible  = True
        self.btn_hit.visible   = False
        self.btn_stand.visible = False
        self.main_page.refresh_balance()

    def _set_status(self, text, color):
        self.status_text.value = text
        self.status_text.color = color
        self.main_page.update()