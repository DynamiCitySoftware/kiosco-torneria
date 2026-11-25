# tests/test_programa_g.py
from pathlib import Path

from centros_de_trabajo.estaciones.plato.modelo_programa import ProgramaG


PROGRAMA_PLATO_VALIDO = """\
G21
G90
F60
G0 A0
G1 A30
G1 A60
G1 A90
"""


def test_acepta_programa_basico_del_plato():
    programa = ProgramaG.desde_texto("plato_01.nc", PROGRAMA_PLATO_VALIDO)

    assert programa.validar_para_plato() == []


def test_rechaza_comando_no_permitido_y_da_numero_de_linea():
    texto = "G21\nG90\nM3\nG1 A30"
    programa = ProgramaG.desde_texto("plato_invalido.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 3 for error in errores)
    assert any("M3" in error.motivo for error in errores)


def test_rechaza_eje_distinto_de_a():
    texto = "G21\nG90\nF60\nG1 X10"
    programa = ProgramaG.desde_texto("eje_invalido.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 4 for error in errores)
    assert any("eje X" in error.motivo for error in errores)


def test_ignora_comentarios_al_validar():
    texto = """\
; M3 en este comentario no es una instrucción
G21 (G43 tampoco es una instrucción)
G90
F60
G1 A30
"""
    programa = ProgramaG.desde_texto("comentarios.nc", texto)

    assert programa.validar_para_plato() == []


def test_movimientos_devuelve_solo_g0_y_g1():
    programa = ProgramaG.desde_texto("plato_01.nc", PROGRAMA_PLATO_VALIDO)

    assert programa.movimientos() == [
        "G0 A0",
        "G1 A30",
        "G1 A60",
        "G1 A90",
    ]


def test_rechaza_archivo_vacio():
    programa = ProgramaG.desde_texto("vacio.nc", "")

    errores = programa.validar_para_plato()

    assert len(errores) == 1
    assert errores[0].linea_nro == 0
    assert errores[0].motivo == "archivo vacío"


def test_carga_archivo_desde_path(tmp_path: Path):
    ruta = tmp_path / "plato_01.nc"
    ruta.write_text(PROGRAMA_PLATO_VALIDO, encoding="utf-8")

    programa = ProgramaG.desde_archivo(ruta)

    assert programa.nombre == "plato_01.nc"
    assert programa.validar_para_plato() == []


def test_rechaza_movimiento_sin_modal_g21():
    texto = "G90\nF60\nG1 A30"
    programa = ProgramaG.desde_texto("falta_g21.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 3 for error in errores)


def test_rechaza_movimiento_sin_modal_g90():
    texto = "G21\nF60\nG1 A30"
    programa = ProgramaG.desde_texto("falta_g90.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 3 for error in errores)


def test_rechaza_g1_sin_velocidad_f():
    texto = "G21\nG90\nG1 A30"
    programa = ProgramaG.desde_texto("falta_feed.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 3 for error in errores)


def test_rechaza_valor_de_eje_malformado():
    texto = "G21\nG90\nF60\nG1 A1.2.3"
    programa = ProgramaG.desde_texto("eje_malformado.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 4 for error in errores)


def test_rechaza_velocidad_no_numerica():
    texto = "G21\nG90\nFabc\nG1 A30"
    programa = ProgramaG.desde_texto("feed_no_numerico.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 3 for error in errores)


def test_rechaza_velocidad_cero():
    texto = "G21\nG90\nF0\nG1 A30"
    programa = ProgramaG.desde_texto("feed_cero.nc", texto)

    errores = programa.validar_para_plato()

    assert any(error.linea_nro == 4 for error in errores)