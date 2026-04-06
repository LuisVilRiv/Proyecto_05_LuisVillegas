import random
from abc import ABC, abstractmethod

from .models import Jugador


class Juego(ABC):
    def __init__(self, nombre: str) -> None:
        self.nombre = nombre

    @abstractmethod
    def jugar(self, jugador: Jugador) -> None:
        raise NotImplementedError

    @staticmethod
    def pedir_apuesta(jugador: Jugador) -> float:
        while True:
            try:
                apuesta = float(input("Ingresa apuesta: ").strip())
                jugador.validar_apuesta(apuesta)
                return round(apuesta, 2)
            except ValueError as error:
                print(f"[ERROR] {error}")


class Slots(Juego):
    def __init__(self, rtp_objetivo: float = 0.94, volatilidad: str = "media") -> None:
        super().__init__("Slots")
        self.simbolos = ["A", "K", "Q", "J", "7", "$", "*"]
        self.lineas = {1: [1], 2: [0, 1], 3: [0, 1, 2]}
        self.rtp_objetivo = max(0.7, min(rtp_objetivo, 0.99))
        self.volatilidad = volatilidad.lower()
        self.tabla_pagos = self._crear_tabla_pagos()

    def _crear_tabla_pagos(self) -> dict:
        base = {"A": 2.0, "K": 3.0, "Q": 4.0, "J": 5.0, "7": 8.0, "$": 12.0, "*": 20.0}
        if self.volatilidad == "alta":
            factor = 1.25
        elif self.volatilidad == "baja":
            factor = 0.85
        else:
            factor = 1.0
        ajuste_rtp = self.rtp_objetivo / 0.94
        return {s: round(v * factor * ajuste_rtp, 2) for s, v in base.items()}

    def _girar(self) -> list:
        return [[random.choice(self.simbolos) for _ in range(3)] for _ in range(3)]

    @staticmethod
    def _mostrar_tablero(tablero: list) -> None:
        print("\nTablero Slots:")
        for fila in tablero:
            print(" | " + " | ".join(fila) + " | ")

    def jugar(self, jugador: Jugador) -> None:
        print("\n--- SLOTS ---")
        apuesta = self.pedir_apuesta(jugador)

        while True:
            try:
                n_lineas = int(input("Lineas a jugar (1-3): ").strip())
                if n_lineas not in (1, 2, 3):
                    raise ValueError("Debes elegir 1, 2 o 3 lineas.")
                break
            except ValueError as error:
                print(f"[ERROR] {error}")

        costo_total = apuesta * n_lineas
        try:
            jugador.validar_apuesta(costo_total)
        except ValueError as error:
            print(f"[ERROR] {error}")
            return

        tablero = self._girar()
        self._mostrar_tablero(tablero)

        premio = 0.0
        detalles = []
        for idx in self.lineas[n_lineas]:
            fila = tablero[idx]
            if fila[0] == fila[1] == fila[2]:
                multiplicador = self.tabla_pagos[fila[0]]
                ganancia_linea = apuesta * multiplicador
                premio += ganancia_linea
                detalles.append(f"Linea {idx + 1} ({fila[0]}x3) x{multiplicador}")

        detalle = ", ".join(detalles) if detalles else "Sin combinacion ganadora"
        jugador.registrar_jugada(self.nombre, costo_total, premio, detalle)
        print(f"Resultado: {detalle}")
        print(f"Premio: {premio:.2f} | Saldo actual: {jugador.saldo:.2f}")


class Ruleta(Juego):
    ROJOS = {
        1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36
    }

    def __init__(self, apuesta_minima: float = 1.0) -> None:
        super().__init__("Ruleta")
        self.apuesta_minima = max(0.1, float(apuesta_minima))

    def _pedir_apuesta_ruleta(self, jugador: Jugador) -> float:
        while True:
            apuesta = self.pedir_apuesta(jugador)
            if apuesta < self.apuesta_minima:
                print(f"[ERROR] La apuesta minima en ruleta es {self.apuesta_minima:.2f}.")
                continue
            return apuesta

    def jugar(self, jugador: Jugador) -> None:
        print("\n--- RULETA ---")
        print("Apuestas disponibles:")
        print("1) Pleno (0-36) [inside]")
        print("2) Calle / Street (1-34, bloque de 3 numeros) [inside]")
        print("3) Cuadro / Corner (1-32, bloque de 4 numeros) [inside]")
        print("4) Color (rojo/negro) [outside]")
        print("5) Par/Impar [outside]")
        print("6) Docena (1-3) [outside]")
        apuesta = self._pedir_apuesta_ruleta(jugador)

        tipo = input("Elige tipo de apuesta: ").strip()
        numero = random.randint(0, 36)
        color = "verde" if numero == 0 else ("rojo" if numero in self.ROJOS else "negro")
        premio = 0.0
        detalle = f"Sale {numero} ({color})"

        try:
            if tipo == "1":
                elegido = int(input("Numero pleno (0-36): ").strip())
                if not 0 <= elegido <= 36:
                    raise ValueError("Numero fuera de rango.")
                if elegido == numero:
                    premio = apuesta * 36
                    detalle += " | Acierto pleno x36"
            elif tipo == "2":
                inicio = int(input("Calle inicial (1,4,7,...,34): ").strip())
                if inicio < 1 or inicio > 34 or (inicio - 1) % 3 != 0:
                    raise ValueError("Calle invalida. Debe iniciar en 1,4,7,...,34.")
                bloque = {inicio, inicio + 1, inicio + 2}
                if numero in bloque:
                    premio = apuesta * 12
                    detalle += f" | Acierto calle {sorted(bloque)} x12"
            elif tipo == "3":
                inicio = int(input("Cuadro esquina superior izq (1-32, no multiplo de 3): ").strip())
                if inicio < 1 or inicio > 32 or inicio % 3 == 0:
                    raise ValueError("Cuadro invalido para el tapete europeo.")
                bloque = {inicio, inicio + 1, inicio + 3, inicio + 4}
                if numero in bloque:
                    premio = apuesta * 9
                    detalle += f" | Acierto cuadro {sorted(bloque)} x9"
            elif tipo == "4":
                elegido = input("Color (rojo/negro): ").strip().lower()
                if elegido not in ("rojo", "negro"):
                    raise ValueError("Color invalido.")
                if elegido == color:
                    premio = apuesta * 2
                    detalle += " | Acierto color x2"
            elif tipo == "5":
                elegido = input("Par o impar: ").strip().lower()
                if elegido not in ("par", "impar"):
                    raise ValueError("Debes escribir par o impar.")
                if numero != 0:
                    if (numero % 2 == 0 and elegido == "par") or (numero % 2 != 0 and elegido == "impar"):
                        premio = apuesta * 2
                        detalle += " | Acierto par/impar x2"
            elif tipo == "6":
                docena = int(input("Docena (1=1-12, 2=13-24, 3=25-36): ").strip())
                if docena not in (1, 2, 3):
                    raise ValueError("Docena invalida.")
                if (docena == 1 and 1 <= numero <= 12) or (docena == 2 and 13 <= numero <= 24) or (
                    docena == 3 and 25 <= numero <= 36
                ):
                    premio = apuesta * 3
                    detalle += " | Acierto docena x3"
            else:
                print("[ERROR] Opcion de apuesta no valida.")
                return
        except ValueError as error:
            print(f"[ERROR] {error}")
            return

        jugador.registrar_jugada(self.nombre, apuesta, premio, detalle)
        print(f"Resultado: {detalle}")
        print(f"Premio: {premio:.2f} | Saldo actual: {jugador.saldo:.2f}")


class Blackjack(Juego):
    def __init__(self, dealer_stand_soft_17: bool = True) -> None:
        super().__init__("Blackjack")
        self.mazo = []
        self.dealer_stand_soft_17 = dealer_stand_soft_17

    def _barajar(self) -> None:
        valores = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        palos = ["H", "D", "C", "S"]
        self.mazo = [f"{v}{p}" for v in valores for p in palos]
        random.shuffle(self.mazo)

    def _repartir(self) -> str:
        if not self.mazo:
            self._barajar()
        return self.mazo.pop()

    @staticmethod
    def _valor_mano(mano: list) -> int:
        total = 0
        ases = 0
        for carta in mano:
            valor = carta[:-1]
            if valor in ("J", "Q", "K"):
                total += 10
            elif valor == "A":
                total += 11
                ases += 1
            else:
                total += int(valor)
        while total > 21 and ases > 0:
            total -= 10
            ases -= 1
        return total

    @staticmethod
    def _es_soft_17(mano: list) -> bool:
        total = 0
        ases = 0
        for carta in mano:
            valor = carta[:-1]
            if valor in ("J", "Q", "K"):
                total += 10
            elif valor == "A":
                total += 11
                ases += 1
            else:
                total += int(valor)
        while total > 21 and ases > 0:
            total -= 10
            ases -= 1
        return total == 17 and ases > 0

    def _jugar_mano(self, mano: list, dealer_visible: str, apuesta: float, puede_doblar: bool) -> tuple[list, float]:
        while True:
            total = self._valor_mano(mano)
            print(f"Dealer muestra: {dealer_visible}")
            print(f"Tu mano: {mano} -> {total}")
            if total >= 21:
                break
            opciones = "h=pedir, s=plantarse"
            if puede_doblar:
                opciones += ", d=doblar"
            accion = input(f"Accion ({opciones}): ").strip().lower()
            if accion == "h":
                mano.append(self._repartir())
            elif accion == "s":
                break
            elif accion == "d" and puede_doblar:
                mano.append(self._repartir())
                apuesta *= 2
                break
            else:
                print("[ERROR] Accion no valida.")
        return mano, apuesta

    def jugar(self, jugador: Jugador) -> None:
        print("\n--- BLACKJACK ---")
        apuesta = self.pedir_apuesta(jugador)
        self._barajar()

        mano = [self._repartir(), self._repartir()]
        dealer = [self._repartir(), self._repartir()]
        seguro = 0.0

        if dealer[0].startswith("A"):
            toma_seguro = input("Dealer muestra As. Tomar seguro? (s/n): ").strip().lower()
            if toma_seguro == "s":
                seguro = apuesta / 2
                try:
                    jugador.validar_apuesta(apuesta + seguro)
                except ValueError as error:
                    print(f"[ERROR] {error}")
                    seguro = 0.0

        manos = [(mano, apuesta)]
        if mano[0][:-1] == mano[1][:-1]:
            split = input("Cartas iguales. Quieres split? (s/n): ").strip().lower()
            if split == "s":
                try:
                    jugador.validar_apuesta(apuesta * 2 + seguro)
                except ValueError as error:
                    print(f"[ERROR] {error}")
                    return
                mano1 = [mano[0], self._repartir()]
                mano2 = [mano[1], self._repartir()]
                manos = [(mano1, apuesta), (mano2, apuesta)]

        total_apuesta = sum(item[1] for item in manos) + seguro
        try:
            jugador.validar_apuesta(total_apuesta)
        except ValueError as error:
            print(f"[ERROR] {error}")
            return

        manos_finales = []
        for i, (m, a) in enumerate(manos, start=1):
            print(f"\nMano #{i}")
            mano_final, apuesta_final = self._jugar_mano(m, dealer[0], a, puede_doblar=True)
            manos_finales.append((mano_final, apuesta_final))

        valor_dealer = self._valor_mano(dealer)
        while valor_dealer < 17 or (
            valor_dealer == 17 and not self.dealer_stand_soft_17 and self._es_soft_17(dealer)
        ):
            dealer.append(self._repartir())
            valor_dealer = self._valor_mano(dealer)

        print(f"\nDealer: {dealer} -> {valor_dealer}")
        premio_total = 0.0
        detalle = []

        dealer_blackjack = valor_dealer == 21 and len(dealer) == 2
        if seguro > 0 and dealer_blackjack:
            premio_total += seguro * 3
            detalle.append("Seguro ganado")

        for idx, (m, a) in enumerate(manos_finales, start=1):
            valor = self._valor_mano(m)
            if valor > 21:
                detalle.append(f"Mano {idx}: bust")
            elif dealer_blackjack and not (valor == 21 and len(m) == 2):
                detalle.append(f"Mano {idx}: pierde vs blackjack dealer")
            elif valor == 21 and len(m) == 2 and not dealer_blackjack:
                premio_total += a * 2.5
                detalle.append(f"Mano {idx}: blackjack")
            elif valor_dealer > 21 or valor > valor_dealer:
                premio_total += a * 2
                detalle.append(f"Mano {idx}: gana")
            elif valor == valor_dealer:
                premio_total += a
                detalle.append(f"Mano {idx}: push")
            else:
                detalle.append(f"Mano {idx}: pierde")

        jugador.registrar_jugada(self.nombre, total_apuesta, premio_total, " | ".join(detalle))
        print(f"Resultado: {' | '.join(detalle)}")
        print(f"Premio: {premio_total:.2f} | Saldo actual: {jugador.saldo:.2f}")
