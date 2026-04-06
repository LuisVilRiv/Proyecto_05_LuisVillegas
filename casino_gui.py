"""
Casino Royale - GUI Pro
"""

from __future__ import annotations

import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

from secciones.models import Jugador, PersistenciaCasino


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMG_DIR = BASE_DIR / "img"
DATA_FILE = DATA_DIR / "casino_data.json"

SLOTS_SYMBOLS = ["A", "K", "Q", "J", "7", "$", "*"]
SLOTS_PAY = {"A": 2.0, "K": 3.0, "Q": 4.0, "J": 5.0, "7": 8.0, "$": 12.0, "*": 20.0}
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


class CasinoRoyaleApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Casino Royale - Professional Edition")
        self.geometry("1180x720")
        self.minsize(1080, 660)
        self.configure(bg="#0b1020")

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.storage = PersistenciaCasino(str(DATA_FILE))
        self.jugador: Optional[Jugador] = None

        self._bg_image = None
        self._icon_image = None
        self._load_optional_assets()
        self._setup_styles()
        self._build_login_view()

    def _load_optional_assets(self) -> None:
        icon_path = IMG_DIR / "icon.png"
        if icon_path.exists():
            try:
                self._icon_image = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, self._icon_image)
            except Exception:
                pass

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TFrame", background="#121a2f")
        style.configure("Panel.TFrame", background="#0f1729")
        style.configure("Title.TLabel", background="#121a2f", foreground="#f8c555", font=("Segoe UI", 18, "bold"))
        style.configure("Body.TLabel", background="#121a2f", foreground="#d2d9e8", font=("Segoe UI", 10))
        style.configure("Stat.TLabel", background="#0f1729", foreground="#dbe4f7", font=("Consolas", 11))
        style.configure("Treeview", background="#0f1729", foreground="#e4ebfa", fieldbackground="#0f1729")
        style.configure("Treeview.Heading", background="#1f2a44", foreground="#f8c555", font=("Segoe UI", 10, "bold"))

    def _current_player(self) -> Jugador:
        if self.jugador is None:
            raise RuntimeError("No hay jugador autenticado")
        return self.jugador

    def _clear_window(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

    def _build_login_view(self) -> None:
        self._clear_window()
        wrapper = ttk.Frame(self, style="Dark.TFrame")
        wrapper.pack(fill="both", expand=True)

        left = ttk.Frame(wrapper, style="Dark.TFrame")
        left.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        right = ttk.Frame(wrapper, style="Dark.TFrame")
        right.pack(side="right", fill="y", padx=20, pady=20)

        tk.Label(
            left,
            text="CASINO ROYALE",
            bg="#121a2f",
            fg="#f8c555",
            font=("Segoe UI", 40, "bold"),
        ).pack(anchor="w", pady=(20, 6))
        tk.Label(
            left,
            text="Arquitectura de Sistemas de Azar - Edicion Visual Pro",
            bg="#121a2f",
            fg="#8ea0c9",
            font=("Segoe UI", 13),
        ).pack(anchor="w", pady=(0, 20))
        self._build_feature_cards(left)

        login_card = tk.Frame(right, bg="#0f1729", highlightbackground="#2d4068", highlightthickness=1)
        login_card.pack(fill="x", ipadx=10, ipady=8)
        tk.Label(login_card, text="Acceso al Casino", bg="#0f1729", fg="#f8c555", font=("Segoe UI", 16, "bold")).pack(pady=(16, 8))
        tk.Label(login_card, text="Usuario", bg="#0f1729", fg="#d2d9e8", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        self.username_var = tk.StringVar()
        entry = ttk.Entry(login_card, textvariable=self.username_var, font=("Segoe UI", 12), width=24)
        entry.pack(padx=20, pady=(6, 14), fill="x")
        entry.focus_set()

        tk.Button(
            login_card,
            text="Entrar",
            bg="#2d63d9",
            fg="#f3f7ff",
            activebackground="#3a76f0",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            command=self._login,
        ).pack(fill="x", padx=20, pady=(0, 16), ipady=7)
        tk.Label(login_card, text="Persistencia: data/casino_data.json", bg="#0f1729", fg="#7486ad", font=("Segoe UI", 9)).pack(
            pady=(0, 12)
        )
        self.bind("<Return>", lambda _: self._login())

    def _build_feature_cards(self, parent: tk.Widget) -> None:
        features = [
            ("Slots", "Animacion de giro + multiples lineas de pago"),
            ("Ruleta", "Simulacion visual de giro + apuestas externas"),
            ("Blackjack", "Motor rapido con reparto y crupier automatico"),
            ("Analytics", "Historial y reporte exportable de sesion"),
        ]
        container = tk.Frame(parent, bg="#121a2f")
        container.pack(fill="x")
        for title, desc in features:
            card = tk.Frame(container, bg="#0f1729", highlightbackground="#2d4068", highlightthickness=1)
            card.pack(fill="x", pady=6)
            tk.Label(card, text=title, bg="#0f1729", fg="#f8c555", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
            tk.Label(card, text=desc, bg="#0f1729", fg="#a7b6d7", font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(0, 8))

    def _login(self) -> None:
        nombre = self.username_var.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Introduce un nombre de usuario.")
            return
        self.jugador = self.storage.cargar_jugador(nombre)
        self._build_dashboard()

    def _build_dashboard(self) -> None:
        self.unbind("<Return>")
        self._clear_window()

        root = tk.Frame(self, bg="#0b1020")
        root.pack(fill="both", expand=True)

        sidebar = tk.Frame(root, bg="#0f1729", width=240, highlightbackground="#23314f", highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        main = tk.Frame(root, bg="#0b1020")
        main.pack(side="left", fill="both", expand=True)

        p = self._current_player()
        tk.Label(sidebar, text="CASINO ROYALE", bg="#0f1729", fg="#f8c555", font=("Segoe UI", 18, "bold")).pack(pady=(18, 4))
        tk.Label(sidebar, text=f"Jugador: {p.nombre}", bg="#0f1729", fg="#d8e1f8", font=("Segoe UI", 11)).pack(pady=(0, 20))

        self._sidebar_button(sidebar, "Caja", self.open_caja)
        self._sidebar_button(sidebar, "Slots", self.open_slots)
        self._sidebar_button(sidebar, "Ruleta", self.open_ruleta)
        self._sidebar_button(sidebar, "Blackjack", self.open_blackjack)
        self._sidebar_button(sidebar, "Historial", self.open_historial)
        self._sidebar_button(sidebar, "Exportar reporte", self.exportar_reporte)
        self._sidebar_button(sidebar, "Cerrar sesion", self._build_login_view)

        top = tk.Frame(main, bg="#0f1729", height=74, highlightbackground="#23314f", highlightthickness=1)
        top.pack(fill="x", padx=12, pady=(12, 8))
        top.pack_propagate(False)

        self.lbl_saldo = tk.Label(top, text="", bg="#0f1729", fg="#3be188", font=("Segoe UI", 14, "bold"))
        self.lbl_saldo.pack(side="left", padx=16)
        self.lbl_status = tk.Label(top, text="Sistema listo", bg="#0f1729", fg="#9cb0d8", font=("Segoe UI", 10))
        self.lbl_status.pack(side="right", padx=16)

        content = tk.Frame(main, bg="#0b1020")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        left = tk.Frame(content, bg="#0f1729", highlightbackground="#23314f", highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(content, bg="#0f1729", width=300, highlightbackground="#23314f", highlightthickness=1)
        right.pack(side="right", fill="y", padx=(6, 0))
        right.pack_propagate(False)

        tk.Label(left, text="Panel de Control", bg="#0f1729", fg="#f8c555", font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            left,
            text="Selecciona un modulo desde la barra lateral para jugar o gestionar tu bankroll.",
            bg="#0f1729",
            fg="#9cb0d8",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=14, pady=(0, 10))

        quick = tk.Frame(left, bg="#0f1729")
        quick.pack(anchor="w", padx=12, pady=8)
        self._quick_tile(quick, "Depositar", "#16a34a", self.open_caja, 0, 0)
        self._quick_tile(quick, "Slots", "#2d63d9", self.open_slots, 0, 1)
        self._quick_tile(quick, "Ruleta", "#2d63d9", self.open_ruleta, 1, 0)
        self._quick_tile(quick, "Blackjack", "#2d63d9", self.open_blackjack, 1, 1)

        tk.Label(right, text="Resumen Sesion", bg="#0f1729", fg="#f8c555", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(12, 8))
        self.lbl_stats = tk.Label(right, text="", bg="#0f1729", fg="#dbe6ff", justify="left", font=("Consolas", 11))
        self.lbl_stats.pack(anchor="w", padx=12)

        tk.Label(right, text="Ultimos movimientos", bg="#0f1729", fg="#9cb0d8", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(16, 6))
        self.list_last_moves = tk.Listbox(right, bg="#111c34", fg="#dbe6ff", borderwidth=0, highlightthickness=0)
        self.list_last_moves.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.refresh_dashboard()

    def _sidebar_button(self, parent: tk.Widget, text: str, command) -> None:
        tk.Button(
            parent,
            text=text,
            command=command,
            bg="#162441",
            fg="#eaf1ff",
            activebackground="#1d3157",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        ).pack(fill="x", padx=14, pady=4, ipady=6)

    def _quick_tile(self, parent: tk.Widget, text: str, color: str, command, row: int, col: int) -> None:
        tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            relief="flat",
            width=18,
            height=2,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=row, column=col, padx=6, pady=6)

    def refresh_dashboard(self, status: str = "Sistema listo") -> None:
        p = self._current_player()
        self.storage.guardar_jugador(p)
        self.lbl_saldo.config(text=f"Saldo actual: {p.saldo:.2f}")
        self.lbl_status.config(text=status)
        s = p.stats
        self.lbl_stats.config(
            text=(
                f"Jugadas:        {s.jugadas}\n"
                f"Total apostado: {s.total_apostado:.2f}\n"
                f"Total ganado:   {s.total_ganado:.2f}\n"
                f"Balance sesion: {s.balance_sesion:+.2f}"
            )
        )
        self.list_last_moves.delete(0, "end")
        for item in p.historial[-8:]:
            self.list_last_moves.insert("end", f"{item['juego']:<10} {item['balance']:+.2f}")

    def _parse_amount(self, entry: ttk.Entry) -> Optional[float]:
        try:
            amount = float(entry.get().strip())
            if amount <= 0:
                raise ValueError
            return round(amount, 2)
        except ValueError:
            messagebox.showerror("Error", "Monto invalido. Debe ser numerico y mayor que 0.")
            return None

    def open_caja(self) -> None:
        p = self._current_player()
        w = tk.Toplevel(self)
        w.title("Caja - Gestion de Bankroll")
        w.geometry("430x250")
        w.configure(bg="#0f1729")
        tk.Label(w, text=f"Saldo actual: {p.saldo:.2f}", bg="#0f1729", fg="#3be188", font=("Segoe UI", 13, "bold")).pack(pady=(16, 14))
        e = ttk.Entry(w, font=("Segoe UI", 12))
        e.pack(fill="x", padx=24)

        def dep() -> None:
            amount = self._parse_amount(e)
            if amount is None:
                return
            try:
                p.depositar(amount)
            except ValueError as error:
                messagebox.showerror("Error", str(error))
                return
            self.refresh_dashboard("Deposito realizado")
            w.destroy()

        def ret() -> None:
            amount = self._parse_amount(e)
            if amount is None:
                return
            try:
                p.retirar(amount)
            except ValueError as error:
                messagebox.showerror("Error", str(error))
                return
            self.refresh_dashboard("Retiro realizado")
            w.destroy()

        row = tk.Frame(w, bg="#0f1729")
        row.pack(pady=24)
        tk.Button(row, text="Depositar", command=dep, bg="#16a34a", fg="white", relief="flat", width=14).pack(side="left", padx=8, ipady=4)
        tk.Button(row, text="Retirar", command=ret, bg="#dc2626", fg="white", relief="flat", width=14).pack(side="left", padx=8, ipady=4)

    def open_slots(self) -> None:
        p = self._current_player()
        w = tk.Toplevel(self)
        w.title("Slots Pro")
        w.geometry("560x430")
        w.configure(bg="#0f1729")
        tk.Label(w, text="Slots Pro", bg="#0f1729", fg="#f8c555", font=("Segoe UI", 15, "bold")).pack(pady=(10, 4))

        form = tk.Frame(w, bg="#0f1729")
        form.pack(pady=6)
        tk.Label(form, text="Apuesta por linea:", bg="#0f1729", fg="#dbe6ff").grid(row=0, column=0, padx=6)
        e_ap = ttk.Entry(form, width=10)
        e_ap.grid(row=0, column=1, padx=6)
        tk.Label(form, text="Lineas (1-3):", bg="#0f1729", fg="#dbe6ff").grid(row=0, column=2, padx=6)
        e_ln = ttk.Entry(form, width=8)
        e_ln.insert(0, "1")
        e_ln.grid(row=0, column=3, padx=6)

        reels = [tk.Label(w, text="- - -", bg="#111c34", fg="#dbe6ff", width=24, font=("Consolas", 14, "bold")) for _ in range(3)]
        for r in reels:
            r.pack(pady=4, padx=30, fill="x")

        out = tk.Label(w, text="", bg="#0f1729", fg="#dbe6ff", font=("Consolas", 11), justify="left")
        out.pack(pady=10)

        def final_spin() -> None:
            try:
                ap = float(e_ap.get().strip())
                ln = int(e_ln.get().strip())
                if ap <= 0 or ln not in (1, 2, 3):
                    raise ValueError
                total = round(ap * ln, 2)
                p.validar_apuesta(total)
            except Exception:
                messagebox.showerror("Error", "Apuesta o lineas invalidas.")
                return

            board = [[random.choice(SLOTS_SYMBOLS) for _ in range(3)] for _ in range(3)]
            payout = 0.0
            details = []
            for idx in [0, 1, 2][:ln]:
                row = board[idx]
                if row[0] == row[1] == row[2]:
                    mult = SLOTS_PAY[row[0]]
                    payout += ap * mult
                    details.append(f"Linea {idx + 1}: {row[0]}x3 x{mult}")
            detail = " | ".join(details) if details else "Sin combinacion ganadora"
            p.registrar_jugada("Slots", total, round(payout, 2), detail)
            self.refresh_dashboard("Slots finalizado")
            for idx, reel in enumerate(reels):
                reel.config(text=" | ".join(board[idx]))
            out.config(text=f"{detail}\nPremio: {payout:.2f}")

        def animate(frame: int = 0) -> None:
            if frame >= 13:
                final_spin()
                return
            for reel in reels:
                reel.config(text=" | ".join(random.choice(SLOTS_SYMBOLS) for _ in range(3)))
            w.after(85, lambda: animate(frame + 1))

        tk.Button(w, text="Girar", command=lambda: animate(), bg="#2d63d9", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(
            ipady=4, ipadx=18
        )

    def open_ruleta(self) -> None:
        p = self._current_player()
        w = tk.Toplevel(self)
        w.title("Ruleta Pro")
        w.geometry("600x470")
        w.configure(bg="#0f1729")

        tk.Label(w, text="Ruleta Pro", bg="#0f1729", fg="#f8c555", font=("Segoe UI", 15, "bold")).pack(pady=(10, 8))
        tipo = tk.StringVar(value="pleno")
        selector = tk.Frame(w, bg="#0f1729")
        selector.pack()
        for txt, val in [("Pleno", "pleno"), ("Color", "color"), ("Par/Impar", "paridad"), ("Docena", "docena")]:
            tk.Radiobutton(selector, text=txt, variable=tipo, value=val, bg="#0f1729", fg="#dbe6ff", selectcolor="#12203b").pack(side="left", padx=6)

        form = tk.Frame(w, bg="#0f1729")
        form.pack(pady=10)
        tk.Label(form, text="Apuesta:", bg="#0f1729", fg="#dbe6ff").grid(row=0, column=0, padx=6, pady=4)
        e_ap = ttk.Entry(form, width=12)
        e_ap.grid(row=0, column=1, padx=6, pady=4)
        tk.Label(form, text="Valor:", bg="#0f1729", fg="#dbe6ff").grid(row=1, column=0, padx=6, pady=4)
        e_val = ttk.Entry(form, width=12)
        e_val.grid(row=1, column=1, padx=6, pady=4)

        live = tk.Label(w, text="--", bg="#111c34", fg="#f8c555", font=("Consolas", 28, "bold"), width=8)
        live.pack(pady=(8, 10))
        out = tk.Label(w, text="", bg="#0f1729", fg="#dbe6ff", font=("Consolas", 11))
        out.pack()

        def resolve_bet(winning_number: int) -> None:
            try:
                ap = float(e_ap.get().strip())
                if ap <= 0:
                    raise ValueError
                p.validar_apuesta(ap)
            except Exception:
                messagebox.showerror("Error", "Apuesta invalida.")
                return

            bet_value = e_val.get().strip().lower()
            color = "verde" if winning_number == 0 else ("rojo" if winning_number in ROJOS else "negro")
            reward = 0.0
            t = tipo.get()
            detail = f"Sale {winning_number} ({color})"
            try:
                if t == "pleno" and int(bet_value) == winning_number:
                    reward = ap * 36
                    detail += " | Pleno x36"
                elif t == "color" and bet_value in ("rojo", "negro") and bet_value == color:
                    reward = ap * 2
                    detail += " | Color x2"
                elif t == "paridad" and winning_number != 0 and bet_value in ("par", "impar"):
                    if (winning_number % 2 == 0 and bet_value == "par") or (winning_number % 2 != 0 and bet_value == "impar"):
                        reward = ap * 2
                        detail += " | Par/Impar x2"
                elif t == "docena":
                    doc = int(bet_value)
                    if doc in (1, 2, 3):
                        if (doc == 1 and 1 <= winning_number <= 12) or (doc == 2 and 13 <= winning_number <= 24) or (
                            doc == 3 and 25 <= winning_number <= 36
                        ):
                            reward = ap * 3
                            detail += " | Docena x3"
            except Exception:
                messagebox.showerror("Error", "Valor de apuesta invalido para el tipo seleccionado.")
                return

            p.registrar_jugada("Ruleta", ap, round(reward, 2), detail)
            self.refresh_dashboard("Ruleta finalizada")
            out.config(text=f"{detail}\nPremio: {reward:.2f}")

        def animate(step: int = 0) -> None:
            if step >= 24:
                final_number = random.randint(0, 36)
                final_color = "verde" if final_number == 0 else ("rojo" if final_number in ROJOS else "negro")
                live.config(text=f"{final_number}", fg={"rojo": "#ef4444", "negro": "#dbe6ff", "verde": "#22c55e"}[final_color])
                resolve_bet(final_number)
                return
            temp = random.randint(0, 36)
            temp_color = "verde" if temp == 0 else ("rojo" if temp in ROJOS else "negro")
            live.config(text=f"{temp}", fg={"rojo": "#ef4444", "negro": "#dbe6ff", "verde": "#22c55e"}[temp_color])
            w.after(55 + step * 3, lambda: animate(step + 1))

        tk.Button(w, text="Girar ruleta", command=lambda: animate(), bg="#2d63d9", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(
            pady=10, ipadx=16, ipady=4
        )

    def open_blackjack(self) -> None:
        p = self._current_player()
        w = tk.Toplevel(self)
        w.title("Blackjack Pro")
        w.geometry("660x480")
        w.configure(bg="#0f1729")

        tk.Label(w, text="Blackjack Pro", bg="#0f1729", fg="#f8c555", font=("Segoe UI", 15, "bold")).pack(pady=(10, 8))
        top = tk.Frame(w, bg="#0f1729")
        top.pack()
        tk.Label(top, text="Apuesta:", bg="#0f1729", fg="#dbe6ff").pack(side="left", padx=6)
        e_ap = ttk.Entry(top, width=12)
        e_ap.pack(side="left", padx=6)

        text = tk.Text(w, bg="#111c34", fg="#dbe6ff", relief="flat", height=16, font=("Consolas", 11))
        text.pack(fill="both", expand=True, padx=14, pady=12)

        deck = [f"{v}{palo}" for v in ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"] for palo in ["H", "D", "C", "S"]]

        def value(hand: list[str]) -> int:
            total, aces = 0, 0
            for card in hand:
                v = card[:-1]
                if v in ("J", "Q", "K"):
                    total += 10
                elif v == "A":
                    total += 11
                    aces += 1
                else:
                    total += int(v)
            while total > 21 and aces > 0:
                total -= 10
                aces -= 1
            return total

        def play() -> None:
            text.delete("1.0", "end")
            try:
                ap = float(e_ap.get().strip())
                if ap <= 0:
                    raise ValueError
                p.validar_apuesta(ap)
            except Exception:
                messagebox.showerror("Error", "Apuesta invalida.")
                return

            random.shuffle(deck)
            player = [deck.pop(), deck.pop()]
            dealer = [deck.pop(), deck.pop()]

            text.insert("end", f"Jugador inicial: {player}\nDealer visible: {dealer[0]}, ?\n\n")
            self.update_idletasks()

            while value(player) < 17:
                player.append(deck.pop())
                text.insert("end", f"Jugador pide -> {player} ({value(player)})\n")
                self.update_idletasks()
                w.after(120)
            text.insert("end", "\n")
            while value(dealer) < 17:
                dealer.append(deck.pop())
                text.insert("end", f"Dealer pide -> {dealer} ({value(dealer)})\n")
                self.update_idletasks()
                w.after(120)

            vp = value(player)
            vd = value(dealer)
            if vp > 21:
                reward, result = 0.0, "Pierdes por pasarte."
            elif vd > 21 or vp > vd:
                reward, result = ap * 2, "Ganas la mano."
            elif vp == vd:
                reward, result = ap, "Push (empate)."
            else:
                reward, result = 0.0, "Pierdes la mano."

            p.registrar_jugada("Blackjack", ap, round(reward, 2), result)
            self.refresh_dashboard("Blackjack finalizado")
            text.insert("end", f"\nResultado final:\nJugador {vp} vs Dealer {vd}\n{result}\nPremio: {reward:.2f}\n")

        tk.Button(w, text="Repartir", command=play, bg="#2d63d9", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(
            pady=(0, 10), ipadx=16, ipady=4
        )

    def open_historial(self) -> None:
        p = self._current_player()
        w = tk.Toplevel(self)
        w.title("Historial de Movimientos")
        w.geometry("980x500")
        w.configure(bg="#0f1729")

        cols = ("fecha", "juego", "apuesta", "premio", "balance", "detalle", "saldo")
        tree = ttk.Treeview(w, columns=cols, show="headings")
        for col, title, width in [
            ("fecha", "Fecha", 150),
            ("juego", "Juego", 100),
            ("apuesta", "Apuesta", 90),
            ("premio", "Premio", 90),
            ("balance", "Balance", 90),
            ("detalle", "Detalle", 350),
            ("saldo", "Saldo", 90),
        ]:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for item in p.historial[-300:]:
            tree.insert(
                "",
                "end",
                values=(
                    item["fecha"],
                    item["juego"],
                    f"{item['apuesta']:.2f}",
                    f"{item['premio']:.2f}",
                    f"{item['balance']:+.2f}",
                    item["detalle"],
                    f"{item['saldo_post']:.2f}",
                ),
            )

    def exportar_reporte(self) -> None:
        p = self._current_player()
        report = DATA_DIR / f"reporte_{p.nombre}.txt"
        s = p.stats
        lines = [
            "CASINO ROYALE - REPORTE DE SESION",
            "=" * 42,
            f"Jugador: {p.nombre}",
            f"Saldo final: {p.saldo:.2f}",
            f"Jugadas: {s.jugadas}",
            f"Apostado: {s.total_apostado:.2f}",
            f"Ganado: {s.total_ganado:.2f}",
            f"Balance: {s.balance_sesion:+.2f}",
            "",
            "Ultimos movimientos:",
        ]
        for row in p.historial[-40:]:
            lines.append(f"{row['fecha']} | {row['juego']:<10} | {row['balance']:+.2f} | {row['detalle']}")
        report.write_text("\n".join(lines), encoding="utf-8")
        self.refresh_dashboard("Reporte exportado")
        messagebox.showinfo("Reporte", f"Reporte guardado en:\n{report}")


if __name__ == "__main__":
    app = CasinoRoyaleApp()
    app.mainloop()
"""
Casino Royale - Version GUI (tkinter)
"""

# Legacy block preserved below intentionally.
# from __future__ import annotations

import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from secciones.models import PersistenciaCasino


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "casino_data.json"

SLOTS_SYMBOLS = ["A", "K", "Q", "J", "7", "$", "*"]
SLOTS_PAY = {"A": 2.0, "K": 3.0, "Q": 4.0, "J": 5.0, "7": 8.0, "$": 12.0, "*": 20.0}
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


class CasinoRoyaleApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Casino Royale")
        self.geometry("900x620")
        self.minsize(860, 560)
        self.configure(bg="#0f172a")

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.storage = PersistenciaCasino(str(DATA_FILE))
        self.jugador = None

        self._build_login_view()

    def _clear_window(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

    def _build_login_view(self) -> None:
        self._clear_window()
        wrapper = tk.Frame(self, bg="#0f172a")
        wrapper.pack(expand=True, fill="both")

        card = tk.Frame(wrapper, bg="#111827", bd=0, highlightthickness=1, highlightbackground="#334155")
        card.place(relx=0.5, rely=0.5, anchor="center", width=450, height=260)

        tk.Label(card, text="CASINO ROYALE", bg="#111827", fg="#fbbf24", font=("Segoe UI", 24, "bold")).pack(
            pady=(20, 4)
        )
        tk.Label(card, text="Login / Registro por usuario", bg="#111827", fg="#cbd5e1", font=("Segoe UI", 11)).pack(
            pady=(0, 20)
        )

        self.username_var = tk.StringVar()
        entry = ttk.Entry(card, textvariable=self.username_var, font=("Segoe UI", 12))
        entry.pack(padx=28, fill="x")
        entry.focus_set()

        tk.Button(
            card, text="Entrar", bg="#f59e0b", fg="#111827", font=("Segoe UI", 11, "bold"), relief="flat", command=self._login
        ).pack(pady=22, ipadx=18, ipady=6)

        self.bind("<Return>", lambda _: self._login())

    def _login(self) -> None:
        nombre = self.username_var.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Introduce un nombre de usuario.")
            return
        self.jugador = self.storage.cargar_jugador(nombre)
        self._build_main_view()

    def _build_main_view(self) -> None:
        self.unbind("<Return>")
        self._clear_window()

        top = tk.Frame(self, bg="#111827", height=72)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text=f"Jugador: {self.jugador.nombre}", bg="#111827", fg="#e2e8f0", font=("Segoe UI", 13, "bold")).pack(
            side="left", padx=16
        )
        self.lbl_saldo = tk.Label(top, text="", bg="#111827", fg="#22c55e", font=("Segoe UI", 12, "bold"))
        self.lbl_saldo.pack(side="left", padx=20)

        center = tk.Frame(self, bg="#0f172a")
        center.pack(fill="both", expand=True, padx=14, pady=14)

        panel_left = tk.Frame(center, bg="#111827", highlightthickness=1, highlightbackground="#334155")
        panel_left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        panel_right = tk.Frame(center, bg="#111827", width=280, highlightthickness=1, highlightbackground="#334155")
        panel_right.pack(side="right", fill="y", padx=(8, 0))
        panel_right.pack_propagate(False)

        tk.Label(panel_left, text="Mesa Principal", bg="#111827", fg="#fbbf24", font=("Segoe UI", 16, "bold")).pack(pady=(12, 10))
        grid = tk.Frame(panel_left, bg="#111827")
        grid.pack(pady=6)
        self._action_button(grid, "Caja", self.open_caja, 0, 0)
        self._action_button(grid, "Slots", self.open_slots, 0, 1)
        self._action_button(grid, "Ruleta", self.open_ruleta, 1, 0)
        self._action_button(grid, "Blackjack", self.open_blackjack, 1, 1)
        self._action_button(grid, "Historial", self.open_historial, 2, 0)
        self._action_button(grid, "Exportar reporte", self.exportar_reporte, 2, 1)

        tk.Label(panel_right, text="Resumen Sesion", bg="#111827", fg="#fbbf24", font=("Segoe UI", 14, "bold")).pack(pady=(14, 10))
        self.lbl_stats = tk.Label(panel_right, text="", bg="#111827", fg="#e2e8f0", justify="left", font=("Consolas", 11))
        self.lbl_stats.pack(anchor="w", padx=14)
        self.refresh_dashboard()

    def _action_button(self, parent: tk.Widget, text: str, command, row: int, col: int) -> None:
        tk.Button(
            parent, text=text, command=command, bg="#1d4ed8", fg="#eff6ff", relief="flat", font=("Segoe UI", 11, "bold"), width=22, height=2
        ).grid(row=row, column=col, padx=8, pady=8)

    def refresh_dashboard(self) -> None:
        self.storage.guardar_jugador(self.jugador)
        self.lbl_saldo.config(text=f"Saldo: {self.jugador.saldo:.2f}")
        s = self.jugador.stats
        self.lbl_stats.config(
            text=f"Jugadas:        {s.jugadas}\nTotal apostado: {s.total_apostado:.2f}\nTotal ganado:   {s.total_ganado:.2f}\nBalance sesion: {s.balance_sesion:+.2f}"
        )

    def open_caja(self) -> None:
        w = tk.Toplevel(self)
        w.title("Caja")
        w.geometry("360x220")
        w.configure(bg="#111827")
        tk.Label(w, text=f"Saldo actual: {self.jugador.saldo:.2f}", bg="#111827", fg="#22c55e", font=("Segoe UI", 12, "bold")).pack(pady=12)
        e = ttk.Entry(w, font=("Segoe UI", 11))
        e.pack(fill="x", padx=24)

        def monto() -> float | None:
            try:
                v = float(e.get().strip())
                if v <= 0:
                    raise ValueError
                return v
            except ValueError:
                messagebox.showerror("Error", "Monto invalido")
                return None

        def dep() -> None:
            v = monto()
            if v is None:
                return
            self.jugador.depositar(v)
            self.refresh_dashboard()
            w.destroy()

        def ret() -> None:
            v = monto()
            if v is None:
                return
            try:
                self.jugador.retirar(v)
            except ValueError as err:
                messagebox.showerror("Error", str(err))
                return
            self.refresh_dashboard()
            w.destroy()

        f = tk.Frame(w, bg="#111827")
        f.pack(pady=22)
        tk.Button(f, text="Depositar", command=dep, bg="#16a34a", fg="white", relief="flat").pack(side="left", padx=8)
        tk.Button(f, text="Retirar", command=ret, bg="#dc2626", fg="white", relief="flat").pack(side="left", padx=8)

    def open_slots(self) -> None:
        w = tk.Toplevel(self)
        w.title("Slots")
        w.geometry("460x340")
        w.configure(bg="#111827")
        tk.Label(w, text="Slots", bg="#111827", fg="#fbbf24", font=("Segoe UI", 13, "bold")).pack(pady=10)
        f = tk.Frame(w, bg="#111827")
        f.pack()
        tk.Label(f, text="Apuesta:", bg="#111827", fg="#e2e8f0").grid(row=0, column=0, padx=6, pady=4)
        e_ap = ttk.Entry(f, width=10)
        e_ap.grid(row=0, column=1, padx=6, pady=4)
        tk.Label(f, text="Lineas (1-3):", bg="#111827", fg="#e2e8f0").grid(row=0, column=2, padx=6, pady=4)
        e_ln = ttk.Entry(f, width=8)
        e_ln.insert(0, "1")
        e_ln.grid(row=0, column=3, padx=6, pady=4)
        out = tk.Label(w, text="", bg="#111827", fg="#cbd5e1", font=("Consolas", 11), justify="left")
        out.pack(pady=14)

        def girar() -> None:
            try:
                ap = float(e_ap.get().strip())
                ln = int(e_ln.get().strip())
                if ap <= 0 or ln not in (1, 2, 3):
                    raise ValueError
                costo = ap * ln
                self.jugador.validar_apuesta(costo)
            except Exception:
                messagebox.showerror("Error", "Datos invalidos")
                return
            tab = [[random.choice(SLOTS_SYMBOLS) for _ in range(3)] for _ in range(3)]
            premio = 0.0
            detalles = []
            for idx in [0, 1, 2][:ln]:
                if tab[idx][0] == tab[idx][1] == tab[idx][2]:
                    m = SLOTS_PAY[tab[idx][0]]
                    premio += ap * m
                    detalles.append(f"Linea {idx+1} x{m}")
            det = " | ".join(detalles) if detalles else "Sin premio"
            self.jugador.registrar_jugada("Slots", costo, premio, det)
            self.refresh_dashboard()
            out.config(text="\n".join(" | ".join(x) for x in tab) + f"\n\n{det}\nPremio: {premio:.2f}")

        tk.Button(w, text="Girar", command=girar, bg="#2563eb", fg="white", relief="flat").pack(ipadx=16, ipady=4)

    def open_ruleta(self) -> None:
        w = tk.Toplevel(self)
        w.title("Ruleta")
        w.geometry("520x340")
        w.configure(bg="#111827")
        tipo = tk.StringVar(value="pleno")
        tk.Label(w, text="Ruleta", bg="#111827", fg="#fbbf24", font=("Segoe UI", 13, "bold")).pack(pady=10)
        bar = tk.Frame(w, bg="#111827")
        bar.pack()
        for t in [("Pleno", "pleno"), ("Color", "color"), ("Par/Impar", "par"), ("Docena", "docena")]:
            tk.Radiobutton(bar, text=t[0], value=t[1], variable=tipo, bg="#111827", fg="#e2e8f0", selectcolor="#1f2937").pack(side="left", padx=6)
        f = tk.Frame(w, bg="#111827")
        f.pack(pady=10)
        tk.Label(f, text="Apuesta:", bg="#111827", fg="#e2e8f0").grid(row=0, column=0, padx=6, pady=4)
        e_ap = ttk.Entry(f, width=12)
        e_ap.grid(row=0, column=1, padx=6, pady=4)
        tk.Label(f, text="Valor:", bg="#111827", fg="#e2e8f0").grid(row=1, column=0, padx=6, pady=4)
        e_val = ttk.Entry(f, width=12)
        e_val.grid(row=1, column=1, padx=6, pady=4)
        out = tk.Label(w, text="", bg="#111827", fg="#cbd5e1", font=("Consolas", 11), justify="left")
        out.pack(pady=12)

        def lanzar() -> None:
            try:
                ap = float(e_ap.get().strip())
                if ap <= 0:
                    raise ValueError
                self.jugador.validar_apuesta(ap)
            except Exception:
                messagebox.showerror("Error", "Apuesta invalida")
                return
            val = e_val.get().strip().lower()
            num = random.randint(0, 36)
            color = "verde" if num == 0 else ("rojo" if num in ROJOS else "negro")
            premio = 0.0
            detalle = f"Sale {num} ({color})"
            try:
                if tipo.get() == "pleno" and int(val) == num:
                    premio = ap * 36
                elif tipo.get() == "color" and val in ("rojo", "negro") and val == color:
                    premio = ap * 2
                elif tipo.get() == "par" and num != 0 and val in ("par", "impar"):
                    if (num % 2 == 0 and val == "par") or (num % 2 != 0 and val == "impar"):
                        premio = ap * 2
                elif tipo.get() == "docena" and int(val) in (1, 2, 3):
                    d = int(val)
                    if (d == 1 and 1 <= num <= 12) or (d == 2 and 13 <= num <= 24) or (d == 3 and 25 <= num <= 36):
                        premio = ap * 3
            except Exception:
                messagebox.showerror("Error", "Valor invalido para ese tipo")
                return
            self.jugador.registrar_jugada("Ruleta", ap, premio, detalle)
            self.refresh_dashboard()
            out.config(text=f"{detalle}\nPremio: {premio:.2f}")

        tk.Button(w, text="Lanzar", command=lanzar, bg="#2563eb", fg="white", relief="flat").pack(ipadx=14, ipady=4)

    def open_blackjack(self) -> None:
        w = tk.Toplevel(self)
        w.title("Blackjack")
        w.geometry("560x380")
        w.configure(bg="#111827")
        tk.Label(w, text="Blackjack rapido", bg="#111827", fg="#fbbf24", font=("Segoe UI", 13, "bold")).pack(pady=10)
        f = tk.Frame(w, bg="#111827")
        f.pack()
        tk.Label(f, text="Apuesta:", bg="#111827", fg="#e2e8f0").pack(side="left")
        e_ap = ttk.Entry(f, width=12)
        e_ap.pack(side="left", padx=8)
        out = tk.Text(w, bg="#0b1220", fg="#e2e8f0", height=12, relief="flat")
        out.pack(fill="both", padx=14, pady=12)
        mazo = [f"{v}{p}" for v in ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"] for p in ["H", "D", "C", "S"]]

        def val(m):
            t, a = 0, 0
            for c in m:
                v = c[:-1]
                if v in ("J", "Q", "K"):
                    t += 10
                elif v == "A":
                    t += 11
                    a += 1
                else:
                    t += int(v)
            while t > 21 and a > 0:
                t -= 10
                a -= 1
            return t

        def repartir() -> None:
            out.delete("1.0", "end")
            try:
                ap = float(e_ap.get().strip())
                if ap <= 0:
                    raise ValueError
                self.jugador.validar_apuesta(ap)
            except Exception:
                messagebox.showerror("Error", "Apuesta invalida")
                return
            random.shuffle(mazo)
            j = [mazo.pop(), mazo.pop()]
            d = [mazo.pop(), mazo.pop()]
            while val(j) < 17:
                j.append(mazo.pop())
            while val(d) < 17:
                d.append(mazo.pop())
            vj, vd = val(j), val(d)
            if vj > 21:
                premio, msg = 0.0, "Pierdes por pasarte."
            elif vd > 21 or vj > vd:
                premio, msg = ap * 2, "Ganas."
            elif vj == vd:
                premio, msg = ap, "Empate (push)."
            else:
                premio, msg = 0.0, "Pierdes."
            self.jugador.registrar_jugada("Blackjack", ap, premio, msg)
            self.refresh_dashboard()
            out.insert("end", f"Tu mano: {j} -> {vj}\nDealer: {d} -> {vd}\n\n{msg}\nPremio: {premio:.2f}")

        tk.Button(w, text="Repartir", command=repartir, bg="#2563eb", fg="white", relief="flat").pack(ipadx=14, ipady=4)

    def open_historial(self) -> None:
        w = tk.Toplevel(self)
        w.title("Historial")
        w.geometry("860x420")
        cols = ("fecha", "juego", "apuesta", "premio", "balance", "detalle", "saldo")
        tree = ttk.Treeview(w, columns=cols, show="headings", height=16)
        for col, title, width in [
            ("fecha", "Fecha", 140),
            ("juego", "Juego", 90),
            ("apuesta", "Apuesta", 80),
            ("premio", "Premio", 80),
            ("balance", "Balance", 80),
            ("detalle", "Detalle", 280),
            ("saldo", "Saldo", 80),
        ]:
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for item in self.jugador.historial[-200:]:
            tree.insert("", "end", values=(item["fecha"], item["juego"], f"{item['apuesta']:.2f}", f"{item['premio']:.2f}", f"{item['balance']:+.2f}", item["detalle"], f"{item['saldo_post']:.2f}"))

    def exportar_reporte(self) -> None:
        ruta = DATA_DIR / f"reporte_{self.jugador.nombre}.txt"
        s = self.jugador.stats
        txt = [
            f"Jugador: {self.jugador.nombre}",
            f"Saldo: {self.jugador.saldo:.2f}",
            f"Jugadas: {s.jugadas}",
            f"Apostado: {s.total_apostado:.2f}",
            f"Ganado: {s.total_ganado:.2f}",
            f"Balance: {s.balance_sesion:+.2f}",
            "",
        ]
        for i in self.jugador.historial[-25:]:
            txt.append(f"{i['fecha']} | {i['juego']} | {i['balance']:+.2f} | {i['detalle']}")
        ruta.write_text("\n".join(txt), encoding="utf-8")
        messagebox.showinfo("Reporte", f"Reporte guardado:\n{ruta}")


if __name__ == "__main__":
    app = CasinoRoyaleApp()
    app.mainloop()
