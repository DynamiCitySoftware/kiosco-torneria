# Ruta: src/centros_de_trabajo/ui/seleccion_centro.py en PC LAB - reemplazar TODO el archivo
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.politicas.base import EstacionDeTrabajo


def filtrar_ordenes_por_estacion(
    estacion_seleccionada: EstacionDeTrabajo,
    todas_las_ordenes: list[OrdenDeTrabajo],
) -> list[OrdenDeTrabajo]:
    return [ot for ot in todas_las_ordenes if estacion_seleccionada.es_mia(ot)]


def elegir_estacion_por_nombre(
    nombre_odoo_buscado: str,
    registro_estaciones: list[EstacionDeTrabajo],
) -> EstacionDeTrabajo:
    for estacion in registro_estaciones:
        if estacion.nombre_odoo == nombre_odoo_buscado:
            return estacion
    raise ValueError(f"No hay estacion registrada con nombre_odoo={nombre_odoo_buscado!r}")


def contar_por_estacion(
    registro_estaciones: list[EstacionDeTrabajo],
    todas_las_ordenes: list[OrdenDeTrabajo],
) -> dict[str, int]:
    return {
        estacion.nombre_odoo: len(filtrar_ordenes_por_estacion(estacion, todas_las_ordenes))
        for estacion in registro_estaciones
    }


class VentanaSeleccion(QMainWindow):
    def __init__(self, backend_a_usar: Backend, registro_estaciones: list[EstacionDeTrabajo]) -> None:
        super().__init__()
        self._backend = backend_a_usar
        self._registro = registro_estaciones
        self.estacion_elegida: EstacionDeTrabajo | None = None
        self.setWindowTitle("Kiosco Tornería - Elegir estación")
        self.showFullScreen()

        contenedor = QWidget()
        layout = QVBoxLayout()
        self._etiqueta = QLabel("Elegí estación de trabajo")
        self._lista = QListWidget()
        self._boton_abrir = QPushButton("ABRIR ESTACION [F1]")
        layout.addWidget(self._etiqueta)
        layout.addWidget(self._lista)
        layout.addWidget(self._boton_abrir)
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)
        self._boton_abrir.clicked.connect(self._al_abrir)
        self.recargar()

    def recargar(self) -> None:
        print("[seleccion] recargar inicio", flush=True)
        todas = self._backend.listar_ordenes()
        conteos = contar_por_estacion(self._registro, todas)
        self._lista.clear()
        for estacion in self._registro:
            n = conteos.get(estacion.nombre_odoo, 0)
            self._lista.addItem(f"{estacion.nombre_odoo} — {n} órdenes")
        print(f"[seleccion] conteos={conteos}", flush=True)

    def _al_abrir(self) -> None:
        fila = self._lista.currentRow()
        if fila < 0 or fila >= len(self._registro):
            self._etiqueta.setText("Elegí una estación primero")
            return
        self.estacion_elegida = self._registro[fila]
        print(f"[seleccion] elegido={self.estacion_elegida.nombre_odoo}", flush=True)
        self.close()