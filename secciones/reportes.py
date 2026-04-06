import json
from datetime import datetime
from pathlib import Path


def exportar_reporte_sesion(jugador, data_dir: Path) -> Path:
    carpeta = data_dir / "reportes_sesion"
    carpeta.mkdir(parents=True, exist_ok=True)

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = carpeta / f"{jugador.nombre}_sesion_{marca}.json"

    payload = {
        "jugador": jugador.nombre,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saldo_final": round(jugador.saldo, 2),
        "sesion": {
            "jugadas": jugador.stats.jugadas,
            "apostado": round(jugador.stats.total_apostado, 2),
            "ganado": round(jugador.stats.total_ganado, 2),
            "balance": round(jugador.stats.balance_sesion, 2),
        },
        "estadisticas_globales": jugador.estadisticas_globales,
        "ultimos_movimientos": jugador.historial[-25:],
    }

    ruta.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta
