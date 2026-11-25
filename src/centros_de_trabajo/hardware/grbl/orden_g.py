from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrdenDeMovimiento:
    """Su función es representar un bloque multilinea listo para ejecutar."""
    nombre: str  # VALOR GENERICO, ej "cuadrado-2mm"
    lineas: list[str] = field(default_factory=list)

    def ejecutar(self, controlador) -> list[str]:
        respuestas = []
        for linea in self.lineas:
            respuestas.append(controlador.enviar(linea))
        return respuestas