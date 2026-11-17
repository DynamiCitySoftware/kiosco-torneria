# Ruta: src/centros_de_trabajo/estaciones/inventario.py en PC LAB - archivo nuevo completo
from dataclasses import dataclass
from pathlib import Path
import time

import serial

# VALOR_GENERICO_RUTA: en tu PC LAB es literal "/dev/serial/by-path" y "/dev/serial/by-id"
DIR_BY_PATH = Path("/dev/serial/by-path")
DIR_BY_ID = Path("/dev/serial/by-id")
# BAUDIOS no es genérico, es tu valor real de [[attach-photo-5]]: 115200 de GRBL
BAUDIOS = 115200
TIMEOUT_LECTURA_SEGUNDOS = 0.25
ESPERA_ARRANQUE_SEGUNDOS = 2.0
PLAZO_WELCOME_SEGUNDOS = 5.0


@dataclass(frozen=True)
class Estacion:
    tty: str            # VALOR_GENERICO, ej "/dev/ttyUSB0" en tu PC LAB
    by_path: str
    by_id: str          # etiqueta linda o "(sin by-id, clon sin serie)"
    welcome: str | None # None = sin welcome / TIMEOUT, ej "WS-37 Grbl-EQS 1.1h..."


def construir_mapa_by_id() -> dict[str, str]:
    mapa: dict[str, str] = {}
    if not DIR_BY_ID.exists():
        return mapa
    for link in sorted(DIR_BY_ID.iterdir()):
        try:
            mapa.setdefault(str(link.resolve()), link.name)
        except OSError:
            continue
    return mapa


def listar_ttys_unicos() -> list[dict]:
    mapa_by_id = construir_mapa_by_id()
    vistos: dict[str, dict] = {}
    if not DIR_BY_PATH.exists():
        return []
    for link in sorted(DIR_BY_PATH.iterdir()):
        try:
            tty_real = str(link.resolve())
        except OSError:
            continue
        if tty_real in vistos:
            continue
        vistos[tty_real] = {
            "tty": tty_real,
            "by_path": link.name,
            "by_id": mapa_by_id.get(tty_real, "(sin by-id, clon sin serie)"),
        }
    return sorted(vistos.values(), key=lambda d: d["tty"])


def leer_welcome(puerto: serial.Serial) -> str | None:
    limite = time.monotonic() + PLAZO_WELCOME_SEGUNDOS
    while time.monotonic() < limite:
        linea = puerto.readline().decode("utf-8", errors="replace").strip()
        if linea:
            return linea
    return None


def inventariar_estaciones() -> list[Estacion]:
    estaciones: list[Estacion] = []
    for d in listar_ttys_unicos():
        try:
            with serial.Serial(port=d["tty"], baudrate=BAUDIOS, timeout=TIMEOUT_LECTURA_SEGUNDOS) as puerto:
                puerto.dtr = True
                time.sleep(ESPERA_ARRANQUE_SEGUNDOS)
                welcome = leer_welcome(puerto)
        except (serial.SerialException, OSError):
            welcome = None
        estaciones.append(Estacion(tty=d["tty"], by_path=d["by_path"], by_id=d["by_id"], welcome=welcome))
    return estaciones