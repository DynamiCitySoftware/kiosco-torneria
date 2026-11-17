# Ruta: scripts/leer_dispositivos_usb.py en PC LAB - reemplazar TODO el archivo
from pathlib import Path
import time

import serial

DIR_BY_PATH = Path("/dev/serial/by-path")
DIR_BY_ID = Path("/dev/serial/by-id")
# BAUDIOS no es genérico, es tu valor real de [[attach-photo-5]]: 115200 del monitor GRBL
BAUDIOS = 115200
TIMEOUT_LECTURA_SEGUNDOS = 0.25
ESPERA_ARRANQUE_SEGUNDOS = 2.0
PLAZO_WELCOME_SEGUNDOS = 5.0


def construir_mapa_by_id() -> dict[str, str]:
    """Devuelve {tty_resuelto: nombre_by_id}. Si no hay by-id, devuelve {}."""
    mapa: dict[str, str] = {}
    if not DIR_BY_ID.exists():
        return mapa
    for link in sorted(DIR_BY_ID.iterdir()):
        try:
            tty_real = str(link.resolve())
            mapa.setdefault(tty_real, link.name)
        except OSError:
            continue
    return mapa


def listar_dispositivos_unicos() -> list[dict]:
    """Lista por by-path, deduplica usb vs usbv2 que apuntan al mismo tty."""
    mapa_by_id = construir_mapa_by_id()
    vistos_por_tty: dict[str, dict] = {}
    if not DIR_BY_PATH.exists():
        print(f"ERROR: no existe {DIR_BY_PATH}", flush=True)
        return []
    for link in sorted(DIR_BY_PATH.iterdir()):
        try:
            tty_real = str(link.resolve())
        except OSError as e:
            print(f"{link} -> ERROR resolve: {e}", flush=True)
            continue
        # Si ya vimos este ttyUSBx es el duplicado usb/usbx2, lo salteamos
        if tty_real in vistos_por_tty:
            continue
        etiqueta_by_id = mapa_by_id.get(tty_real, "(sin by-id, clon sin serie)")
        vistos_por_tty[tty_real] = {
            "tty": tty_real,
            "by_path": link.name,
            "by_id": etiqueta_by_id,
        }
    return sorted(vistos_por_tty.values(), key=lambda d: d["tty"])


def leer_welcome(puerto: serial.Serial) -> str | None:
    """Lee la primera línea no vacía hasta que vence el plazo."""
    limite = time.monotonic() + PLAZO_WELCOME_SEGUNDOS
    while time.monotonic() < limite:
        linea_bytes = puerto.readline()
        linea = linea_bytes.decode("utf-8", errors="replace").strip()
        if linea:
            return linea
    return None


def main() -> None:
    dispositivos = listar_dispositivos_unicos()
    if not dispositivos:
        print(f"No se encontraron dispositivos en {DIR_BY_PATH}", flush=True)
        return
    print(f"Dispositivos encontrados: {len(dispositivos)}", flush=True)
    for d in dispositivos:
        try:
            with serial.Serial(
                port=d["tty"],
                baudrate=BAUDIOS,
                timeout=TIMEOUT_LECTURA_SEGUNDOS,
            ) as puerto:
                puerto.dtr = True
                time.sleep(ESPERA_ARRANQUE_SEGUNDOS)
                welcome = leer_welcome(puerto)
                if welcome is None:
                    print(f"{d['tty']} <- by-path:{d['by_path']} <- by-id:{d['by_id']} -> (sin welcome / TIMEOUT)", flush=True)
                else:
                    print(f"{d['tty']} <- by-path:{d['by_path']} <- by-id:{d['by_id']} -> {welcome}", flush=True)
        except (serial.SerialException, OSError) as e:
            print(f"{d['tty']} -> ERROR al abrir o leer: {e}", flush=True)


if __name__ == "__main__":
    main()