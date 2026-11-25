# Ruta: src/centros_de_trabajo/estaciones/inventario.py en PC LAB - reemplazar TODO el archivo
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


DIR_BY_PATH = Path("/dev/serial/by-path")
DIR_BY_ID = Path("/dev/serial/by-id")


@dataclass(frozen=True)
class PuertoSerie:
    # by_path es VALOR REAL de Linux, ej: pci-0000:00:10.0-usb-0:2:1.0-port0
    # no es genérico, es lo que devuelve ls -l /dev/serial/by-path/
    nombre_by_path: str
    ruta_by_path: Path
    etiqueta_by_id: str | None
    ruta_tty: Path


def listar_puertos(
    dir_by_path: Path = DIR_BY_PATH,
    dir_by_id: Path = DIR_BY_ID,
) -> list[PuertoSerie]:
    """Lista puertos por by-path, deduplica mismo tty, agrega etiqueta by-id si existe."""
    if not dir_by_path.exists():
        return []

    # Mapa tty resuelto -> etiqueta by-id
    etiquetas: dict[str, str] = {}
    if dir_by_id.exists():
        for entrada in dir_by_id.iterdir():
            try:
                tty_resuelto = os.path.realpath(entrada)
            except OSError:
                continue
            # Si dos clones colisionan en by-id, gana uno. Por eso by-id es solo etiqueta.
            etiquetas.setdefault(tty_resuelto, entrada.name)

    vistos_tty: set[str] = set()
    puertos: list[PuertoSerie] = []
    for entrada in sorted(dir_by_path.iterdir(), key=lambda p: p.name):
        try:
            tty_resuelto = os.path.realpath(entrada)
        except OSError:
            continue
        if tty_resuelto in vistos_tty:
            continue
        vistos_tty.add(tty_resuelto)
        puertos.append(
            PuertoSerie(
                nombre_by_path=entrada.name,
                ruta_by_path=entrada,
                etiqueta_by_id=etiquetas.get(tty_resuelto),
                ruta_tty=Path(tty_resuelto),
            )
        )
    return puertos