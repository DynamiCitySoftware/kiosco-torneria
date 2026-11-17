# Ruta: src/centros_de_trabajo/__main__.py en PC LAB - reemplazar TODO el archivo
import sys
from PyQt6.QtWidgets import QApplication

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.backends.odoo import OdooBackend
from centros_de_trabajo.config import Config
from centros_de_trabajo.ui.seleccion_centro import VentanaSeleccion


def construir_backend_desde_config(config: Config) -> Backend:
    if config.backend == "odoo":
        return OdooBackend(url=config.odoo_url, db=config.odoo_db, user=config.odoo_user, key_file=config.odoo_key_file)
    return FakeBackend([])


def main() -> None:
    config = Config.desde_entorno()
    backend_a_usar = construir_backend_desde_config(config)
    # VALOR_GENERICO_REGISTRO es genérico: lista vacía hasta que crees estacion_plato_1
    # Ej real: registro = [estacion_plato_1]
    registro: list = []
    app = QApplication(sys.argv)
    seleccion = VentanaSeleccion(backend_a_usar, registro)
    if not config.kiosco:
        seleccion.showNormal()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()