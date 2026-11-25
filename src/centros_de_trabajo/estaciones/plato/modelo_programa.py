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
        import math
        import re

        errores: list[ErrorG] = []

        if not self.lineas:
            return [ErrorG(0, "", "archivo vacío")]

        if len(self.lineas) > MAX_LINEAS:
            return [ErrorG(0, "", f"supera {MAX_LINEAS} líneas")]

        # Lee palabras G-code compactas o separadas por espacios:
        # G1 A30, G1A30 y F60.
        patron_palabra = re.compile(
            r"([A-Za-z])\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
        )

        g21_activo = False
        g90_activo = False
        velocidad_f: float | None = None

        for numero_linea, linea_cruda in enumerate(self.lineas, start=1):
            limpia = self._sin_comentario(linea_cruda)
            if not limpia:
                continue

            palabras: list[tuple[str, float, str]] = []
            posicion = 0
            fragmento_invalido: str | None = None

            for coincidencia in patron_palabra.finditer(limpia):
                separador = limpia[posicion:coincidencia.start()]
                if separador.strip():
                    fragmento_invalido = separador.strip()
                    break

                letra = coincidencia.group(1).upper()
                texto_valor = coincidencia.group(2)
                valor = float(texto_valor)

                if not math.isfinite(valor):
                    fragmento_invalido = coincidencia.group(0)
                    break

                palabras.append((letra, valor, coincidencia.group(0)))
                posicion = coincidencia.end()

            if fragmento_invalido is None and limpia[posicion:].strip():
                fragmento_invalido = limpia[posicion:].strip()

            if fragmento_invalido is not None or not palabras:
                detalle = fragmento_invalido or limpia
                errores.append(
                    ErrorG(
                        numero_linea,
                        linea_cruda,
                        f"palabra o valor inválido: {detalle}",
                    )
                )
                continue

            codigos_g: list[str] = []
            linea_invalida = False

            for letra, valor, palabra_original in palabras:
                if letra == "G":
                    if not valor.is_integer():
                        errores.append(
                            ErrorG(
                                numero_linea,
                                linea_cruda,
                                f"código G inválido: {palabra_original}",
                            )
                        )
                        linea_invalida = True
                        continue

                    codigo_g = f"G{int(valor)}"
                    if codigo_g not in COMANDOS_PERMITIDOS:
                        errores.append(
                            ErrorG(
                                numero_linea,
                                linea_cruda,
                                f"{codigo_g} bloqueado para plato",
                            )
                        )
                        linea_invalida = True
                        continue

                    codigos_g.append(codigo_g)

                elif letra in {"X", "Y", "Z"}:
                    errores.append(
                        ErrorG(
                            numero_linea,
                            linea_cruda,
                            f"eje {letra} no permitido en plato, solo A",
                        )
                    )
                    linea_invalida = True

                elif letra not in {"A", "F", "P"}:
                    errores.append(
                        ErrorG(
                            numero_linea,
                            linea_cruda,
                            f"comando no permitido para plato: {palabra_original}",
                        )
                    )
                    linea_invalida = True

            codigos_movimiento = [
                codigo for codigo in codigos_g if codigo in {"G0", "G1"}
            ]

            if len(codigos_movimiento) > 1:
                errores.append(
                    ErrorG(
                        numero_linea,
                        linea_cruda,
                        "no se permiten varios modos de movimiento en la misma línea",
                    )
                )
                linea_invalida = True

            if any(letra == "A" for letra, _, _ in palabras) and not codigos_movimiento:
                errores.append(
                    ErrorG(
                        numero_linea,
                        linea_cruda,
                        "el eje A solo se permite en bloques G0 o G1",
                    )
                )
                linea_invalida = True

            if any(letra == "P" for letra, _, _ in palabras) and "G4" not in codigos_g:
                errores.append(
                    ErrorG(
                        numero_linea,
                        linea_cruda,
                        "el parámetro P solo se permite con G4",
                    )
                )
                linea_invalida = True

            valores_f = [valor for letra, valor, _ in palabras if letra == "F"]
            if len(valores_f) > 1:
                errores.append(
                    ErrorG(numero_linea, linea_cruda, "hay más de un valor F en la línea")
                )
                linea_invalida = True

            if linea_invalida:
                continue

            # Los códigos modales de esta línea quedan activos desde aquí.
            if "G21" in codigos_g:
                g21_activo = True
            if "G90" in codigos_g:
                g90_activo = True
            if valores_f:
                velocidad_f = valores_f[0]
                if velocidad_f <= 0:
                    errores.append(
                        ErrorG(
                            numero_linea,
                            linea_cruda,
                            "la velocidad F debe ser mayor que cero",
                        )
                    )

            if not codigos_movimiento:
                continue

            codigo_movimiento = codigos_movimiento[0]

            if not g21_activo:
                errores.append(
                    ErrorG(
                        numero_linea,
                        linea_cruda,
                        "el movimiento requiere G21 activo",
                    )
                )

            if not g90_activo:
                errores.append(
                    ErrorG(
                        numero_linea,
                        linea_cruda,
                        "el movimiento requiere G90 activo",
                    )
                )

            if codigo_movimiento == "G1":
                if velocidad_f is None:
                    errores.append(
                        ErrorG(
                            numero_linea,
                            linea_cruda,
                            "G1 requiere una velocidad F definida",
                        )
                    )
                elif velocidad_f <= 0:
                    errores.append(
                        ErrorG(
                            numero_linea,
                            linea_cruda,
                            "G1 requiere una velocidad F mayor que cero",
                        )
                    )

        return errores

    def movimientos(self) -> list[str]:
        """Devuelve solo las líneas G0/G1 limpias, en orden."""
        movs = []
        for cruda in self.lineas:
            limpia = self._sin_comentario(cruda).upper()
            if limpia.startswith("G0") or limpia.startswith("G1"):
                movs.append(limpia)
        return movs