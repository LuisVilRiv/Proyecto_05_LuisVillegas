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
