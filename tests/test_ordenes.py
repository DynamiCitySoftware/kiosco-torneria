# Ruta: tests/test_ordenes.py en PC LAB - archivo nuevo completo
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo


def test_desde_odoo_mapea_workcenter_y_cronometro():
    registro_odoo = {
        "id": 42,
        "name": "dividir",
        "state": "progress",
        # VALOR_GENERICO: ej [7, "Plato Partidor"] en tu torneria_db cuando lo crees
        "workcenter_id": [7, "Plato Partidor"],
        "working_user_ids": [18],
        "duration": 1.5,
    }
    ot = OrdenDeTrabajo.desde_odoo(registro_odoo, uid_actual=18)
    assert ot.id_odoo == 42
    assert ot.operacion_nombre == "dividir"
    assert ot.estado_odoo == "progress"
    assert ot.workcenter_nombre == "Plato Partidor"
    assert ot.existe_cronometro_para_usuario is True
    assert ot.duracion_minutos == 1.5


def test_desde_odoo_sin_cronometro():
    registro_odoo = {
        "id": 43,
        "name": "dividir",
        "state": "ready",
        "workcenter_id": [7, "Plato Partidor"],
        "working_user_ids": [],
        "duration": 0.0,
    }
    ot = OrdenDeTrabajo.desde_odoo(registro_odoo, uid_actual=18)
    assert ot.existe_cronometro_para_usuario is False