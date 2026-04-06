from __future__ import annotations

import hashlib
import json
import random
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

from secciones.models import Jugador, PersistenciaCasino


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "casino_data.json"
AUTH_FILE = DATA_DIR / "casino_auth.json"
SETTINGS_FILE = DATA_DIR / "casino_settings.json"
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
SLOTS_SYMBOLS = ["A", "K", "Q", "J", "7", "$", "*"]
SLOTS_PAY = {"A": 2.0, "K": 3.0, "Q": 4.0, "J": 5.0, "7": 8.0, "$": 12.0, "*": 20.0}


class CasinoRoyalePro(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Casino Royale Pro")
        self.geometry("1120x700")
        self.minsize(1040, 640)
        self.configure(bg="#0b1020")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.storage = PersistenciaCasino(str(DATA_FILE))
        self.auth_data = self._load_auth()
        self.settings = self._load_settings()
        self.jugador: Optional[Jugador] = None
        self._setup_styles()
        self._build_login()

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
        if sys.platform.startswith("win"):
            try:
                import winsound

                tones = {
                    "win": (980, 120),
                    "lose": (240, 180),
                    "action": (520, 80),
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
        style.configure("Treeview", background="#101a33", foreground="#dbe6ff", fieldbackground="#101a33")
        style.configure("Treeview.Heading", background="#22345c", foreground="#f7c95f", font=("Segoe UI", 10, "bold"))

    def _player(self) -> Jugador:
        if self.jugador is None:
            raise RuntimeError("No autenticado")
        return self.jugador

    def _clear(self) -> None:
        for w in self.winfo_children():
            w.destroy()

    def _build_login(self) -> None:
        self._clear()
        root = tk.Frame(self, bg="#111a33")
        root.pack(fill="both", expand=True)
        tk.Label(root, text="CASINO ROYALE PRO", bg="#111a33", fg="#f7c95f", font=("Segoe UI", 36, "bold")).pack(pady=(60, 10))
        tk.Label(root, text="Interfaz visual profesional", bg="#111a33", fg="#9eb2df", font=("Segoe UI", 12)).pack(pady=(0, 30))

        card = tk.Frame(root, bg="#0f1729", highlightbackground="#2e4068", highlightthickness=1)
        card.pack(ipadx=20, ipady=20)
        tk.Label(card, text="Usuario", bg="#0f1729", fg="#dbe6ff", font=("Segoe UI", 11)).pack(anchor="w")
        self.user_var = tk.StringVar()
        e = ttk.Entry(card, textvariable=self.user_var, font=("Segoe UI", 12), width=32)
        e.pack(pady=(8, 14))
        tk.Label(card, text="Contraseña", bg="#0f1729", fg="#dbe6ff", font=("Segoe UI", 11)).pack(anchor="w")
        self.pass_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.pass_var, font=("Segoe UI", 12), width=32, show="*").pack(pady=(8, 14))
        e.focus_set()
        tk.Button(card, text="Entrar", command=self._login, bg="#2e6ee6", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(
            fill="x", ipady=6
        )
        tk.Button(
            card,
            text="Registrar usuario",
            command=self._register,
            bg="#1d7a57",
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        ).pack(fill="x", ipady=6, pady=(8, 0))
        self.bind("<Return>", lambda _: self._login())

    def _login(self) -> None:
        username = self.user_var.get().strip()
        password = self.pass_var.get().strip()
        if not username:
            messagebox.showerror("Error", "Introduce un usuario.")
            return
        if not password:
            messagebox.showerror("Error", "Introduce una contraseña.")
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

    def _register(self) -> None:
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

    def _build_dashboard(self) -> None:
        self.unbind("<Return>")
        self._clear()

        root = tk.Frame(self, bg="#0b1020")
        root.pack(fill="both", expand=True)
        side = tk.Frame(root, bg="#0f1729", width=230)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        main = tk.Frame(root, bg="#0b1020")
        main.pack(side="left", fill="both", expand=True)

        p = self._player()
        tk.Label(side, text="CASINO", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 20, "bold")).pack(pady=(20, 2))
        tk.Label(side, text=f"Jugador: {p.nombre}", bg="#0f1729", fg="#dbe6ff", font=("Segoe UI", 10)).pack(pady=(0, 18))
        for text, cmd in [
            ("Caja", self.open_caja),
            ("Slots", self.open_slots),
            ("Ruleta", self.open_ruleta),
            ("Blackjack", self.open_blackjack),
            ("Historial", self.open_historial),
            ("Estadisticas", self.open_stats),
            ("Configuracion", self.open_settings),
            ("Exportar reporte", self.exportar_reporte),
            ("Cerrar sesion", self._build_login),
        ]:
            tk.Button(side, text=text, command=cmd, bg="#1a2a4a", fg="#e9f1ff", relief="flat", font=("Segoe UI", 10, "bold")).pack(
                fill="x", padx=14, pady=4, ipady=6
            )

        top = tk.Frame(main, bg="#0f1729", height=72)
        top.pack(fill="x", padx=12, pady=(12, 8))
        top.pack_propagate(False)
        self.lbl_saldo = tk.Label(top, text="", bg="#0f1729", fg="#35d385", font=("Segoe UI", 14, "bold"))
        self.lbl_saldo.pack(side="left", padx=14)
        self.lbl_status = tk.Label(top, text="Listo", bg="#0f1729", fg="#9eb2df", font=("Segoe UI", 10))
        self.lbl_status.pack(side="right", padx=14)

        body = tk.Frame(main, bg="#0b1020")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        left = tk.Frame(body, bg="#0f1729")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.Frame(body, bg="#0f1729", width=300)
        right.pack(side="right", fill="y", padx=(6, 0))
        right.pack_propagate(False)

        tk.Label(left, text="Panel Principal", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=14, pady=(14, 6))
        tk.Label(left, text="Accesos rapidos", bg="#0f1729", fg="#9eb2df", font=("Segoe UI", 11)).pack(anchor="w", padx=14)
        grid = tk.Frame(left, bg="#0f1729")
        grid.pack(anchor="w", padx=12, pady=10)
        for i, (txt, cmd, color) in enumerate(
            [
                ("Depositar", self.open_caja, "#16a34a"),
                ("Slots", self.open_slots, "#2e6ee6"),
                ("Ruleta", self.open_ruleta, "#2e6ee6"),
                ("Blackjack", self.open_blackjack, "#2e6ee6"),
            ]
        ):
            tk.Button(grid, text=txt, command=cmd, bg=color, fg="white", relief="flat", width=18, height=2, font=("Segoe UI", 10, "bold")).grid(
                row=i // 2, column=i % 2, padx=6, pady=6
            )

        tk.Label(right, text="Resumen Sesion", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(14, 8))
        self.lbl_stats = tk.Label(right, text="", bg="#0f1729", fg="#dbe6ff", justify="left", font=("Consolas", 11))
        self.lbl_stats.pack(anchor="w", padx=12)
        tk.Label(right, text="Ultimos movimientos", bg="#0f1729", fg="#9eb2df", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(16, 6))
        self.last_list = tk.Listbox(right, bg="#101a33", fg="#dbe6ff", borderwidth=0, highlightthickness=0)
        self.last_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.refresh_dashboard("Bienvenido")

    def refresh_dashboard(self, status: str = "Listo") -> None:
        p = self._player()
        self.storage.guardar_jugador(p)
        self.lbl_saldo.config(text=f"Saldo: {p.saldo:.2f}")
        self.lbl_status.config(text=status)
        s = p.stats
        self.lbl_stats.config(
            text=f"Jugadas:        {s.jugadas}\nTotal apostado: {s.total_apostado:.2f}\nTotal ganado:   {s.total_ganado:.2f}\nBalance sesion: {s.balance_sesion:+.2f}"
        )
        self.last_list.delete(0, "end")
        for item in p.historial[-8:]:
            self.last_list.insert("end", f"{item['juego']:<10} {item['balance']:+.2f}")

    def _parse_amount(self, e: ttk.Entry) -> Optional[float]:
        try:
            v = float(e.get().strip())
            if v <= 0:
                raise ValueError
            return v
        except ValueError:
            messagebox.showerror("Error", "Valor invalido.")
            return None

    def open_caja(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Caja")
        w.geometry("420x250")
        w.configure(bg="#0f1729")
        tk.Label(w, text=f"Saldo actual: {p.saldo:.2f}", bg="#0f1729", fg="#35d385", font=("Segoe UI", 13, "bold")).pack(pady=12)
        e = ttk.Entry(w, font=("Segoe UI", 12))
        e.pack(fill="x", padx=24)

        def dep() -> None:
            v = self._parse_amount(e)
            if v is None:
                return
            p.depositar(v)
            self._play_sound("action")
            self.refresh_dashboard("Deposito realizado")
            w.destroy()

        def ret() -> None:
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

        row = tk.Frame(w, bg="#0f1729")
        row.pack(pady=20)
        tk.Button(row, text="Depositar", command=dep, bg="#16a34a", fg="white", relief="flat", width=14).pack(side="left", padx=8, ipady=4)
        tk.Button(row, text="Retirar", command=ret, bg="#dc2626", fg="white", relief="flat", width=14).pack(side="left", padx=8, ipady=4)

    def open_slots(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Slots Pro")
        w.geometry("560x430")
        w.configure(bg="#0f1729")
        tk.Label(w, text="Slots Pro", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 15, "bold")).pack(pady=(10, 4))

        form = tk.Frame(w, bg="#0f1729")
        form.pack(pady=6)
        tk.Label(form, text="Apuesta:", bg="#0f1729", fg="#dbe6ff").grid(row=0, column=0, padx=6)
        e_ap = ttk.Entry(form, width=10)
        e_ap.grid(row=0, column=1, padx=6)
        tk.Label(form, text="Lineas (1-3):", bg="#0f1729", fg="#dbe6ff").grid(row=0, column=2, padx=6)
        e_ln = ttk.Entry(form, width=8)
        e_ln.insert(0, "1")
        e_ln.grid(row=0, column=3, padx=6)
        reels = [tk.Label(w, text="- - -", bg="#101a33", fg="#dbe6ff", width=24, font=("Consolas", 14, "bold")) for _ in range(3)]
        for r in reels:
            r.pack(pady=4, padx=30, fill="x")
        out = tk.Label(w, text="", bg="#0f1729", fg="#dbe6ff", font=("Consolas", 11), justify="left")
        out.pack(pady=10)

        def finish() -> None:
            try:
                ap = float(e_ap.get().strip())
                ln = int(e_ln.get().strip())
                if ap <= 0 or ln not in (1, 2, 3):
                    raise ValueError
                total = ap * ln
                p.validar_apuesta(total)
            except Exception:
                messagebox.showerror("Error", "Datos invalidos")
                return
            board = [[random.choice(SLOTS_SYMBOLS) for _ in range(3)] for _ in range(3)]
            pay = 0.0
            det = []
            for idx in [0, 1, 2][:ln]:
                row = board[idx]
                if row[0] == row[1] == row[2]:
                    mult = SLOTS_PAY[row[0]]
                    pay += ap * mult
                    det.append(f"Linea {idx+1} x{mult}")
            detail = " | ".join(det) if det else "Sin premio"
            p.registrar_jugada("Slots", total, pay, detail)
            self._play_sound("win" if pay > 0 else "lose")
            self.refresh_dashboard("Slots terminado")
            for i, r in enumerate(reels):
                r.config(text=" | ".join(board[i]))
            out.config(text=f"{detail}\nPremio: {pay:.2f}")

        def anim(step: int = 0) -> None:
            if step >= 12:
                finish()
                return
            for r in reels:
                r.config(text=" | ".join(random.choice(SLOTS_SYMBOLS) for _ in range(3)))
            speed = int(self.settings.get("animation_speed_ms", 85))
            if not self.settings.get("animations", True):
                speed = 1
            w.after(speed, lambda: anim(step + 1))

        tk.Button(w, text="Girar", command=lambda: anim(), bg="#2e6ee6", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(
            ipady=4, ipadx=16
        )

    def open_ruleta(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Ruleta Pro")
        w.geometry("600x460")
        w.configure(bg="#0f1729")
        tk.Label(w, text="Ruleta Pro", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 15, "bold")).pack(pady=(10, 8))
        tipo = tk.StringVar(value="pleno")
        bar = tk.Frame(w, bg="#0f1729")
        bar.pack()
        for t in [("Pleno", "pleno"), ("Color", "color"), ("Par/Impar", "paridad"), ("Docena", "docena")]:
            tk.Radiobutton(bar, text=t[0], value=t[1], variable=tipo, bg="#0f1729", fg="#dbe6ff", selectcolor="#12203b").pack(side="left", padx=6)
        form = tk.Frame(w, bg="#0f1729")
        form.pack(pady=10)
        tk.Label(form, text="Apuesta:", bg="#0f1729", fg="#dbe6ff").grid(row=0, column=0, padx=6, pady=4)
        e_ap = ttk.Entry(form, width=12)
        e_ap.grid(row=0, column=1, padx=6, pady=4)
        tk.Label(form, text="Valor:", bg="#0f1729", fg="#dbe6ff").grid(row=1, column=0, padx=6, pady=4)
        e_val = ttk.Entry(form, width=12)
        e_val.grid(row=1, column=1, padx=6, pady=4)
        live = tk.Label(w, text="--", bg="#101a33", fg="#f7c95f", font=("Consolas", 28, "bold"), width=8)
        live.pack(pady=(8, 10))
        out = tk.Label(w, text="", bg="#0f1729", fg="#dbe6ff", font=("Consolas", 11))
        out.pack()

        def settle(n: int) -> None:
            try:
                ap = float(e_ap.get().strip())
                if ap <= 0:
                    raise ValueError
                p.validar_apuesta(ap)
            except Exception:
                messagebox.showerror("Error", "Apuesta invalida")
                return
            val = e_val.get().strip().lower()
            color = "verde" if n == 0 else ("rojo" if n in ROJOS else "negro")
            reward = 0.0
            detail = f"Sale {n} ({color})"
            try:
                if tipo.get() == "pleno" and int(val) == n:
                    reward = ap * 36
                elif tipo.get() == "color" and val in ("rojo", "negro") and val == color:
                    reward = ap * 2
                elif tipo.get() == "paridad" and n != 0 and val in ("par", "impar"):
                    if (n % 2 == 0 and val == "par") or (n % 2 != 0 and val == "impar"):
                        reward = ap * 2
                elif tipo.get() == "docena" and int(val) in (1, 2, 3):
                    d = int(val)
                    if (d == 1 and 1 <= n <= 12) or (d == 2 and 13 <= n <= 24) or (d == 3 and 25 <= n <= 36):
                        reward = ap * 3
            except Exception:
                messagebox.showerror("Error", "Valor invalido")
                return
            p.registrar_jugada("Ruleta", ap, reward, detail)
            self._play_sound("win" if reward > 0 else "lose")
            self.refresh_dashboard("Ruleta terminada")
            out.config(text=f"{detail}\nPremio: {reward:.2f}")

        def anim(step: int = 0) -> None:
            if step >= 24:
                n = random.randint(0, 36)
                c = "verde" if n == 0 else ("rojo" if n in ROJOS else "negro")
                live.config(text=str(n), fg={"rojo": "#ef4444", "negro": "#dbe6ff", "verde": "#22c55e"}[c])
                settle(n)
                return
            n = random.randint(0, 36)
            c = "verde" if n == 0 else ("rojo" if n in ROJOS else "negro")
            live.config(text=str(n), fg={"rojo": "#ef4444", "negro": "#dbe6ff", "verde": "#22c55e"}[c])
            w.after(55 + step * 3, lambda: anim(step + 1))

        tk.Button(w, text="Girar ruleta", command=lambda: anim(), bg="#2e6ee6", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(
            pady=10, ipadx=16, ipady=4
        )

    def open_blackjack(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Blackjack Pro")
        w.geometry("660x470")
        w.configure(bg="#0f1729")
        tk.Label(w, text="Blackjack Pro", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 15, "bold")).pack(pady=(10, 8))
        top = tk.Frame(w, bg="#0f1729")
        top.pack()
        tk.Label(top, text="Apuesta:", bg="#0f1729", fg="#dbe6ff").pack(side="left", padx=6)
        e_ap = ttk.Entry(top, width=12)
        e_ap.pack(side="left", padx=6)
        txt = tk.Text(w, bg="#101a33", fg="#dbe6ff", relief="flat", height=16, font=("Consolas", 11))
        txt.pack(fill="both", expand=True, padx=14, pady=12)
        deck = [f"{v}{s}" for v in ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"] for s in ["H", "D", "C", "S"]]

        def val(hand: list[str]) -> int:
            t, a = 0, 0
            for c in hand:
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

        def play() -> None:
            txt.delete("1.0", "end")
            try:
                ap = float(e_ap.get().strip())
                if ap <= 0:
                    raise ValueError
                p.validar_apuesta(ap)
            except Exception:
                messagebox.showerror("Error", "Apuesta invalida")
                return
            random.shuffle(deck)
            j = [deck.pop(), deck.pop()]
            d = [deck.pop(), deck.pop()]
            txt.insert("end", f"Jugador inicial: {j}\nDealer visible: {d[0]}, ?\n\n")
            while val(j) < 17:
                j.append(deck.pop())
                txt.insert("end", f"Jugador pide -> {j} ({val(j)})\n")
            txt.insert("end", "\n")
            while val(d) < 17:
                d.append(deck.pop())
                txt.insert("end", f"Dealer pide -> {d} ({val(d)})\n")
            vj, vd = val(j), val(d)
            if vj > 21:
                reward, result = 0.0, "Pierdes por pasarte."
            elif vd > 21 or vj > vd:
                reward, result = ap * 2, "Ganas la mano."
            elif vj == vd:
                reward, result = ap, "Push (empate)."
            else:
                reward, result = 0.0, "Pierdes la mano."
            p.registrar_jugada("Blackjack", ap, reward, result)
            self._play_sound("win" if reward >= ap else "lose")
            self.refresh_dashboard("Blackjack terminado")
            txt.insert("end", f"\nResultado:\nJugador {vj} vs Dealer {vd}\n{result}\nPremio: {reward:.2f}\n")

        tk.Button(w, text="Repartir", command=play, bg="#2e6ee6", fg="white", relief="flat", font=("Segoe UI", 11, "bold")).pack(
            pady=(0, 10), ipadx=16, ipady=4
        )

    def open_historial(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Historial")
        w.geometry("980x500")
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
            tree.insert("", "end", values=(item["fecha"], item["juego"], f"{item['apuesta']:.2f}", f"{item['premio']:.2f}", f"{item['balance']:+.2f}", item["detalle"], f"{item['saldo_post']:.2f}"))

    def exportar_reporte(self) -> None:
        p = self._player()
        report = DATA_DIR / f"reporte_{p.nombre}.txt"
        s = p.stats
        lines = [
            "CASINO ROYALE PRO - REPORTE",
            "=" * 36,
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
        self._play_sound("default")
        self.refresh_dashboard("Reporte exportado")
        messagebox.showinfo("Reporte", f"Guardado en:\n{report}")

    def open_stats(self) -> None:
        p = self._player()
        w = tk.Toplevel(self)
        w.title("Estadisticas avanzadas")
        w.geometry("760x480")
        w.configure(bg="#0f1729")
        tk.Label(w, text="Estadisticas por juego", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 15, "bold")).pack(pady=(10, 8))
        canvas = tk.Canvas(w, bg="#101a33", highlightthickness=0, width=700, height=300)
        canvas.pack(padx=20, pady=12)

        stats = p.estadisticas_globales or {}
        juegos = ["Slots", "Ruleta", "Blackjack"]
        balances = []
        for g in juegos:
            info = stats.get(g, {"apostado": 0.0, "ganado": 0.0})
            balances.append(info["ganado"] - info["apostado"])
        max_abs = max(1.0, max(abs(v) for v in balances))

        x0 = 70
        base_y = 170
        canvas.create_line(50, base_y, 680, base_y, fill="#6f84b3")
        for i, (juego, val) in enumerate(zip(juegos, balances)):
            h = int((abs(val) / max_abs) * 120)
            x1 = x0 + i * 200
            x2 = x1 + 90
            y1 = base_y - h if val >= 0 else base_y
            y2 = base_y if val >= 0 else base_y + h
            color = "#22c55e" if val >= 0 else "#ef4444"
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            canvas.create_text((x1 + x2) // 2, base_y + 20, text=juego, fill="#dbe6ff", font=("Segoe UI", 10, "bold"))
            canvas.create_text((x1 + x2) // 2, y1 - 10 if val >= 0 else y2 + 12, text=f"{val:+.2f}", fill="#dbe6ff", font=("Consolas", 10))

        s = p.stats
        tk.Label(
            w,
            text=f"Total jugadas: {s.jugadas} | Apostado: {s.total_apostado:.2f} | Ganado: {s.total_ganado:.2f} | Balance: {s.balance_sesion:+.2f}",
            bg="#0f1729",
            fg="#dbe6ff",
            font=("Segoe UI", 10),
        ).pack(pady=(4, 0))

    def open_settings(self) -> None:
        w = tk.Toplevel(self)
        w.title("Configuracion")
        w.geometry("420x300")
        w.configure(bg="#0f1729")
        tk.Label(w, text="Configuracion visual y audio", bg="#0f1729", fg="#f7c95f", font=("Segoe UI", 14, "bold")).pack(pady=(14, 12))

        sound_var = tk.BooleanVar(value=bool(self.settings.get("sound", True)))
        anim_var = tk.BooleanVar(value=bool(self.settings.get("animations", True)))
        speed_var = tk.IntVar(value=int(self.settings.get("animation_speed_ms", 85)))

        tk.Checkbutton(w, text="Activar sonido", variable=sound_var, bg="#0f1729", fg="#dbe6ff", selectcolor="#12203b").pack(anchor="w", padx=24, pady=4)
        tk.Checkbutton(w, text="Activar animaciones", variable=anim_var, bg="#0f1729", fg="#dbe6ff", selectcolor="#12203b").pack(anchor="w", padx=24, pady=4)
        tk.Label(w, text="Velocidad animacion (ms):", bg="#0f1729", fg="#dbe6ff").pack(anchor="w", padx=24, pady=(12, 4))
        scale = tk.Scale(w, from_=20, to=180, orient="horizontal", variable=speed_var, bg="#0f1729", fg="#dbe6ff", troughcolor="#12203b", highlightthickness=0)
        scale.pack(fill="x", padx=24)

        def save() -> None:
            self.settings["sound"] = bool(sound_var.get())
            self.settings["animations"] = bool(anim_var.get())
            self.settings["animation_speed_ms"] = int(speed_var.get())
            self._save_settings()
            self.refresh_dashboard("Configuracion guardada")
            self._play_sound("default")
            w.destroy()

        tk.Button(w, text="Guardar", command=save, bg="#2e6ee6", fg="white", relief="flat", font=("Segoe UI", 10, "bold")).pack(pady=14, ipadx=16, ipady=4)


if __name__ == "__main__":
    app = CasinoRoyalePro()
    app.mainloop()
