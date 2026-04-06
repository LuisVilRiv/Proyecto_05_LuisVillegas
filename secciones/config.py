import json
from pathlib import Path


DEFAULT_CONFIG = {
    "slots": {
        "rtp_objetivo": 0.94,
        "volatilidad": "media",
    },
    "ruleta": {
        "apuesta_minima": 1.0,
    },
    "blackjack": {
        "dealer_stand_soft_17": True,
    },
}


def cargar_configuracion(data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    ruta_config = data_dir / "config.json"

    if not ruta_config.exists():
        ruta_config.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return DEFAULT_CONFIG.copy()

    try:
        data = json.loads(ruta_config.read_text(encoding="utf-8"))
        return _mezclar_config(DEFAULT_CONFIG, data)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def _mezclar_config(base: dict, custom: dict) -> dict:
    salida = {}
    for clave, valor in base.items():
        if isinstance(valor, dict):
            salida[clave] = _mezclar_config(valor, custom.get(clave, {}))
        else:
            salida[clave] = custom.get(clave, valor)
    return salida
