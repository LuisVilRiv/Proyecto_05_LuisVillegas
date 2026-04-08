import json
import os
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionStats:
    total_apostado: float = 0.0
    total_ganado: float = 0.0
    jugadas: int = 0

    @property
    def balance_sesion(self) -> float:
        return self.total_ganado - self.total_apostado


@dataclass
class Jugador:
    nombre: str
    saldo: float = 0.0
    historial: list = field(default_factory=list)
    stats: SessionStats = field(default_factory=SessionStats)
    estadisticas_globales: dict = field(default_factory=dict)
    # Gamificación
    nivel: int = 1
    xp: int = 0
    racha_victorias: int = 0
    max_racha: int = 0
    logros: list = field(default_factory=list)

    def depositar(self, monto: float) -> None:
        if monto <= 0:
            raise ValueError("El deposito debe ser mayor que cero.")
        self.saldo += monto
        self._agregar_historial("deposito", monto)

    def retirar(self, monto: float) -> None:
        if monto <= 0:
            raise ValueError("El retiro debe ser mayor que cero.")
        if monto > self.saldo:
            raise ValueError("Saldo insuficiente para retiro.")
        self.saldo -= monto
        self._agregar_historial("retiro", -monto)

    def validar_apuesta(self, apuesta: float) -> None:
        if apuesta <= 0:
            raise ValueError("La apuesta debe ser mayor que cero.")
        if apuesta > self.saldo:
            raise ValueError("No tienes saldo suficiente para esa apuesta.")

    def registrar_jugada(self, juego: str, apuesta: float, premio: float, detalle: str) -> None:
        self.saldo -= apuesta
        self.saldo += premio
        self.stats.total_apostado += apuesta
        self.stats.total_ganado += premio
        self.stats.jugadas += 1
        self._actualizar_estadisticas_globales(juego, apuesta, premio)
        if premio > apuesta:  # Victoria
            self.registrar_victoria(premio)
        else:  # Derrota o empate
            self.registrar_derrota()
        self.historial.append(
            {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "juego": juego,
                "apuesta": round(apuesta, 2),
                "premio": round(premio, 2),
                "balance": round(premio - apuesta, 2),
                "detalle": detalle,
                "saldo_post": round(self.saldo, 2),
            }
        )

    def _actualizar_estadisticas_globales(self, juego: str, apuesta: float, premio: float) -> None:
        if juego not in self.estadisticas_globales:
            self.estadisticas_globales[juego] = {
                "jugadas": 0,
                "apostado": 0.0,
                "ganado": 0.0,
            }
        info = self.estadisticas_globales[juego]
        info["jugadas"] += 1
        info["apostado"] = round(info["apostado"] + apuesta, 2)
        info["ganado"] = round(info["ganado"] + premio, 2)

    def _agregar_historial(self, tipo: str, monto: float) -> None:
        self.historial.append(
            {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "juego": "caja",
                "apuesta": 0.0,
                "premio": round(monto, 2),
                "balance": round(monto, 2),
                "detalle": tipo,
                "saldo_post": round(self.saldo, 2),
            }
        )

    def registrar_victoria(self, premio: float) -> None:
        """Registra una victoria para la racha"""
        self.racha_victorias += 1
        self.max_racha = max(self.max_racha, self.racha_victorias)
        self.ganar_xp(int(premio // 10))  # XP basado en premio

    def registrar_derrota(self) -> None:
        """Resetea la racha de victorias"""
        self.racha_victorias = 0

    def ganar_xp(self, cantidad: int) -> None:
        """Añade XP y sube de nivel si es necesario"""
        self.xp += cantidad
        xp_necesario = self.nivel * 100  # XP necesario = nivel * 100
        while self.xp >= xp_necesario:
            self.xp -= xp_necesario
            self.nivel += 1
            xp_necesario = self.nivel * 100
            self.verificar_logros()
            # Aquí podríamos añadir un callback para reproducir sonido de level up

    def verificar_logros(self) -> None:
        """Verifica y añade logros desbloqueados"""
        logros_nuevos = []
        if self.nivel >= 5 and "Nivel 5" not in self.logros:
            logros_nuevos.append("Nivel 5")
        if self.max_racha >= 5 and "Racha de 5" not in self.logros:
            logros_nuevos.append("Racha de 5")
        if self.stats.jugadas >= 100 and "100 Jugadas" not in self.logros:
            logros_nuevos.append("100 Jugadas")
        self.logros.extend(logros_nuevos)


class PersistenciaCasino:
    def __init__(self, ruta_archivo: str) -> None:
        self.ruta_archivo = ruta_archivo
        self._data = self._cargar_todo()

    def _cargar_todo(self) -> dict:
        os.makedirs(os.path.dirname(self.ruta_archivo), exist_ok=True)
        if not os.path.exists(self.ruta_archivo):
            return {"usuarios": {}}
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as file:
                data = json.load(file)
            if "usuarios" not in data:
                data["usuarios"] = {}
            return data
        except (json.JSONDecodeError, OSError):
            return {"usuarios": {}}

    def _guardar_todo(self) -> None:
        with open(self.ruta_archivo, "w", encoding="utf-8") as file:
            json.dump(self._data, file, indent=2, ensure_ascii=False)

    def cargar_jugador(self, nombre: str) -> Jugador:
        usuarios = self._data["usuarios"]
        if nombre not in usuarios:
            usuarios[nombre] = {"saldo": 0.0, "historial": []}
            self._guardar_todo()
        info = usuarios[nombre]
        return Jugador(
            nombre=nombre,
            saldo=float(info.get("saldo", 0.0)),
            historial=info.get("historial", []),
            estadisticas_globales=info.get("estadisticas_globales", {}),
        )

    def guardar_jugador(self, jugador: Jugador) -> None:
        self._data["usuarios"][jugador.nombre] = {
            "saldo": round(jugador.saldo, 2),
            "historial": jugador.historial[-200:],
            "estadisticas_globales": jugador.estadisticas_globales,
        }
        self._guardar_todo()
