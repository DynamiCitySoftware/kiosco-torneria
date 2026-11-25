# Ruta: tests/test_catalogo_programas.py en PC LAB - archivo nuevo completo
from pathlib import Path

from centros_de_trabajo.estaciones.plato.catalogo_programas import listar_programas


PROGRAMA_VALIDO = """\
G21
G90
F60
G0 A0
G1 A30
G1 A60
G1 A90
"""

PROGRAMA_INVALIDO = "G21\nG90\nM3\nG1 A30\n"


def _escribir(carpeta: Path, nombre: str, texto: str) -> Path:
    ruta = carpeta / nombre
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def test_carpeta_vacia_devuelve_lista_vacia(tmp_path: Path):
    assert listar_programas(tmp_path) == []


def test_carpeta_inexistente_devuelve_lista_vacia(tmp_path: Path):
    assert listar_programas(tmp_path / "no_existe") == []


def test_lista_ordenada_y_solo_extensiones_validas(tmp_path: Path):
    _escribir(tmp_path, "b_plato.nc", PROGRAMA_VALIDO)
    _escribir(tmp_path, "a_plato.tap", PROGRAMA_VALIDO)
    _escribir(tmp_path, "nota.txt", PROGRAMA_VALIDO)

    entradas = listar_programas(tmp_path)

    assert [e.nombre for e in entradas] == ["a_plato.tap", "b_plato.nc"]


def test_marca_valido_e_invalido_sin_ocultar(tmp_path: Path):
    _escribir(tmp_path, "ok.nc", PROGRAMA_VALIDO)
    _escribir(tmp_path, "mal.nc", PROGRAMA_INVALIDO)

    entradas = listar_programas(tmp_path)
    por_nombre = {e.nombre: e for e in entradas}

    assert por_nombre["ok.nc"].valido is True
    assert por_nombre["ok.nc"].cantidad_lineas == 7
    assert por_nombre["mal.nc"].valido is False
    assert len(por_nombre["mal.nc"].errores) >= 1


def test_archivo_ilegible_no_rompe_listado(tmp_path: Path, monkeypatch):
    buena = _escribir(tmp_path, "ok.nc", PROGRAMA_VALIDO)
    _escribir(tmp_path, "roto.nc", PROGRAMA_VALIDO)
    real_desde_archivo = __import__(
        "centros_de_trabajo.estaciones.plato.modelo_programa", fromlist=["ProgramaG"]
    ).ProgramaG.desde_archivo

    def falla_selectiva(ruta: Path):
        if ruta.name == "roto.nc":
            raise OSError("permiso denegado simulado")
        return real_desde_archivo(ruta)

    monkeypatch.setattr(
        "centros_de_trabajo.estaciones.plato.catalogo_programas.ProgramaG.desde_archivo",
        staticmethod(falla_selectiva),
    )

    entradas = listar_programas(tmp_path)
    por_nombre = {e.nombre: e for e in entradas}

    assert por_nombre["ok.nc"].valido is True
    assert por_nombre["roto.nc"].valido is False
    assert por_nombre["roto.nc"].error_carga is not None
    assert buena.exists()