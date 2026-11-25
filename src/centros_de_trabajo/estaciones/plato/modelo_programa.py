# Ruta: src/centros_de_trabajo/estaciones/plato/modelo_programa.py en PC LAB - archivo nuevo completo
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# VALOR_GENERICO_LIMITE es genérico: ej 20000 líneas / 500 KB para no colgar el kiosco
MAX_LINEAS = 20000
MAX_BYTES = 500 * 1024

# Placeholder con sentido para plato que hace engranajes grandes:
# solo movimiento en A + modales mínimos. Todo lo demás bloquea carga con aviso.
COMANDOS_PERMITIDOS = {"G0", "G1", "G4", "G21", "G90", "F"}
EJES_PERMITIDOS = {"A"}


@dataclass(frozen=True)
class ErrorG:
    linea_nro: int
    texto: str
    motivo: str


@dataclass
class ProgramaG:
    nombre: str
    lineas: list[str] = field(default_factory=list)

    @classmethod
    def desde_texto(cls, nombre: str, texto: str) -> ProgramaG:
        lineas = texto.splitlines()
        return cls(nombre=nombre, lineas=lineas)

    @classmethod
    def desde_archivo(cls, ruta: Path) -> ProgramaG:
        # VALOR_GENERICO_RUTA es genérico: ej Path("/var/lib/kiosco/programas/plato_01.nc")
        datos = ruta.read_bytes()
        if len(datos) > MAX_BYTES:
            raise ValueError(f"{ruta.name}: supera {MAX_BYTES} bytes")
        texto = datos.decode("utf-8")
        return cls.desde_texto(ruta.name, texto)

    def _sin_comentario(self, linea: str) -> str:
        # Comentarios GRBL: ';' corta, '(...)' se ignora
        sin_puntoycoma = linea.split(";")[0]
        sin_parentesis = []
        dentro = False
        for ch in sin_puntoycoma:
            if ch == "(":
                dentro = True
                continue
            if ch == ")":
                dentro = False
                continue
            if not dentro:
                sin_parentesis.append(ch)
        return "".join(sin_parentesis).strip()

    def validar_para_plato(self) -> list[ErrorG]:
        errores: list[ErrorG] = []
        if not self.lineas:
            return [ErrorG(0, "", "archivo vacío")]
        if len(self.lineas) > MAX_LINEAS:
            return [ErrorG(0, "", f"supera {MAX_LINEAS} líneas")]
        for i, cruda in enumerate(self.lineas, start=1):
            limpia = self._sin_comentario(cruda)
            if not limpia:
                continue
            tokens = limpia.upper().split()
            cabeza = tokens[0]
            # F60 viene como un solo token, G0/G1/G4/G21/G90 también
            base = "".join([c for c in cabeza if c.isalpha()])
            if cabeza.startswith("F"):
                base = "F"
                cabeza = "F"
            if base not in {"G", "F"}:
                errores.append(ErrorG(i, cruda, f"comando no permitido para plato: {tokens[0]}"))
                continue
            if cabeza not in COMANDOS_PERMITIDOS:
                errores.append(ErrorG(i, cruda, f"{cabeza} bloqueado para plato"))
                continue
            # Si es movimiento, solo eje A permitido
            if cabeza in ("G0", "G1"):
                for t in tokens[1:]:
                    eje = "".join([c for c in t if c.isalpha()])
                    if eje not in EJES_PERMITIDOS and eje not in ("F",):
                        errores.append(ErrorG(i, cruda, f"eje {eje} no permitido en plato, solo A"))
                        break
        return errores

    def movimientos(self) -> list[str]:
        """Devuelve solo las líneas G0/G1 limpias, en orden."""
        movs = []
        for cruda in self.lineas:
            limpia = self._sin_comentario(cruda).upper()
            if limpia.startswith("G0") or limpia.startswith("G1"):
                movs.append(limpia)
        return movs