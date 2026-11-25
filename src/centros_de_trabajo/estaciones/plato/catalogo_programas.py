# Ruta: src/centros_de_trabajo/estaciones/plato/catalogo_programas.py en PC LAB - archivo nuevo completo
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from centros_de_trabajo.estaciones.plato.modelo_programa import ErrorG, ProgramaG


# VALOR_GENERICO_EXTS es genérico: aceptamos .nc y .tap porque son el mismo texto G.
EXTENSIONES_PROGRAMA = {".nc", ".tap"}


@dataclass(frozen=True)
class EntradaCatalogo:
    nombre: str
    ruta: Path
    programa: ProgramaG | None
    errores: list[ErrorG] = field(default_factory=list)
    error_carga: str | None = None

    @property
    def valido(self) -> bool:
        return self.error_carga is None and not self.errores

    @property
    def cantidad_lineas(self) -> int:
        if self.programa is None:
            return 0
        return len(self.programa.lineas)


def listar_programas(carpeta: Path) -> list[EntradaCatalogo]:
    """Lista .nc/.tap en orden alfabético, sin detenerte por un archivo roto."""
    if not carpeta.exists():
        return []
    if not carpeta.is_dir():
        raise ValueError(f"{carpeta} no es un directorio")

    archivos = sorted(
        (p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONES_PROGRAMA),
        key=lambda p: p.name.lower(),
    )

    entradas: list[EntradaCatalogo] = []
    for ruta in archivos:
        try:
            programa = ProgramaG.desde_archivo(ruta)
        except (OSError, ValueError, UnicodeDecodeError) as e:
            entradas.append(
                EntradaCatalogo(
                    nombre=ruta.name,
                    ruta=ruta,
                    programa=None,
                    errores=[],
                    error_carga=str(e),
                )
            )
            continue
        errores = programa.validar_para_plato()
        entradas.append(
            EntradaCatalogo(
                nombre=ruta.name,
                ruta=ruta,
                programa=programa,
                errores=errores,
                error_carga=None,
            )
        )
    return entradas