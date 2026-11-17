# Ruta: tests/test_seleccion_estacion.py en PC LAB - archivo nuevo completo
import pytest

from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo
from centros_de_trabajo.politicas.base import EstadoKiosco, EstacionDeTrabajo
from centros_de_trabajo.ui.seleccion_centro import (
    filtrar_ordenes_por_estacion,
    elegir_estacion_por_nombre,
    contar_por_estacion,
)


class EstacionFalsa(EstacionDeTrabajo):
    def __init__(self, nombre_odoo: str, operaciones: list[str]):
        self.nombre_odoo = nombre_odoo
        # VALOR_GENERICO: ej ["dividir", "posicionar"] para tu plato partidor
        self.operaciones_soportadas = operaciones

    def derivar_estado(self, ot: OrdenDeTrabajo) -> EstadoKiosco:
        return EstadoKiosco.DETENIDO

    def ordenes_validas(self, estado: EstadoKiosco) -> set[Orden]:
        return {Orden.INICIAR}


def _wo(id_odoo: int, operacion: str, workcenter: str) -> OrdenDeTrabajo:
    return OrdenDeTrabajo(
        id_odoo=id_odoo,
        operacion_nombre=operacion,
        estado_odoo="ready",
        workcenter_nombre=workcenter,
        usuario_es_responsable=False,
        existe_cronometro_para_usuario=False,
        duracion_minutos=0.0,
    )


def test_filtra_solo_sus_ordenes():
    plato = EstacionFalsa("Plato Partidor", ["dividir"])
    torno = EstacionFalsa("Torno", ["torneado"])
    todas = [
        _wo(1, "dividir", "Plato Partidor"),
        _wo(2, "torneado", "Torno"),
        _wo(3, "dividir", "Torno"),
    ]
    resultado = filtrar_ordenes_por_estacion(plato, todas)
    assert [o.id_odoo for o in resultado] == [1]


def test_elegir_por_nombre_y_error():
    registro = [EstacionFalsa("Plato Partidor", ["dividir"])]
    assert elegir_estacion_por_nombre("Plato Partidor", registro).nombre_odoo == "Plato Partidor"
    with pytest.raises(ValueError):
        elegir_estacion_por_nombre("No existe", registro)


def test_contar_por_estacion():
    registro = [
        EstacionFalsa("Plato Partidor", ["dividir"]),
        EstacionFalsa("Torno", ["torneado"]),
    ]
    todas = [
        _wo(1, "dividir", "Plato Partidor"),
        _wo(2, "dividir", "Plato Partidor"),
        _wo(3, "torneado", "Torno"),
    ]
    assert contar_por_estacion(registro, todas) == {"Plato Partidor": 2, "Torno": 1}