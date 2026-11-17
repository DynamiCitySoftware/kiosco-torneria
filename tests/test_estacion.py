# Ruta: tests/test_estacion.py en PC LAB - archivo nuevo completo
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo
from centros_de_trabajo.politicas.base import EstadoKiosco, EstacionDeTrabajo


class EstacionFalsa(EstacionDeTrabajo):
    # VALOR_GENERICO: reemplazalo por tu estacion real, ej nombre_odoo="Plato Partidor"
    nombre_odoo = "Estacion Test"
    operaciones_soportadas = ["operacion test"]

    def derivar_estado(self, ot: OrdenDeTrabajo) -> EstadoKiosco:
        return EstadoKiosco.DETENIDO

    def ordenes_validas(self, estado: EstadoKiosco) -> set[Orden]:
        return {Orden.INICIAR}


def _wo(operacion="operacion test", workcenter="Estacion Test") -> OrdenDeTrabajo:
    return OrdenDeTrabajo(
        id_odoo=1,
        operacion_nombre=operacion,
        estado_odoo="ready",
        workcenter_nombre=workcenter,
        usuario_es_responsable=False,
        existe_cronometro_para_usuario=False,
        duracion_minutos=0.0,
    )


def test_es_mia_coincide_nombre_y_operacion():
    estacion = EstacionFalsa()
    assert estacion.es_mia(_wo()) is True


def test_es_mia_rechaza_otro_centro():
    estacion = EstacionFalsa()
    assert estacion.es_mia(_wo(workcenter="Otra Estacion")) is False


def test_es_mia_rechaza_otra_operacion():
    estacion = EstacionFalsa()
    assert estacion.es_mia(_wo(operacion="otra operacion")) is False