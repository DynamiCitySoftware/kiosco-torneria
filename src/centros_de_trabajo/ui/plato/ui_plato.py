# Ruta: src/centros_de_trabajo/ui/plato/ui_plato.py en PC LAB - archivo nuevo completo
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from centros_de_trabajo.estaciones.plato.catalogo_programas import (
    EntradaCatalogo,
    listar_programas,
)


class VentanaPlato(QMainWindow):
    """Lista programas .nc/.tap, previsualiza y carga solo el válido."""

    def __init__(self, carpeta_programas: Path, kiosco: bool = False) -> None:
        super().__init__()
        # carpeta_programas es VALOR GENERICO, en desarrollo ej:
        # Path("src/centros_de_trabajo/estaciones/plato/programas")
        self._carpeta = carpeta_programas
        self._entradas: list[EntradaCatalogo] = []
        self.programa_cargado: EntradaCatalogo | None = None

        self.setWindowTitle("Plato - Programas G")
        if kiosco:
            self.showFullScreen()

        contenedor = QWidget()
        layout = QVBoxLayout()

        self._etiqueta_estado = QLabel("Sin programa cargado")
        self._lista = QListWidget()
        self._visor = QPlainTextEdit()
        self._visor.setReadOnly(True)
        self._visor.setPlaceholderText("Seleccioná un programa para previsualizar")
        self._etiqueta_detalle = QLabel("Detalle: -")
        self._boton_cargar = QPushButton("CARGAR")
        self._boton_actualizar = QPushButton("ACTUALIZAR LISTA")

        layout.addWidget(self._etiqueta_estado)
        layout.addWidget(self._lista)
        layout.addWidget(self._visor)
        layout.addWidget(self._etiqueta_detalle)
        layout.addWidget(self._boton_cargar)
        layout.addWidget(self._boton_actualizar)
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        self._lista.currentRowChanged.connect(self._al_seleccionar)
        self._boton_cargar.clicked.connect(self._al_cargar)
        self._boton_actualizar.clicked.connect(self.recargar)

        self.recargar()

    def recargar(self) -> None:
        print(f"[ui_plato] listando {self._carpeta}", flush=True)
        self._entradas = listar_programas(self._carpeta)
        self._lista.clear()
        for entrada in self._entradas:
            marca = "OK" if entrada.valido else "ERROR"
            self._lista.addItem(f"[{marca}] {entrada.nombre} ({entrada.cantidad_lineas} lin)")
        print(f"[ui_plato] encontrados={len(self._entradas)}", flush=True)
        if self._entradas:
            self._lista.setCurrentRow(0)
        else:
            self._visor.clear()
            self._etiqueta_detalle.setText("Detalle: carpeta sin programas .nc/.tap")

    def _entrada_seleccionada(self) -> EntradaCatalogo | None:
        fila = self._lista.currentRow()
        if fila < 0 or fila >= len(self._entradas):
            return None
        return self._entradas[fila]

    def _al_seleccionar(self, fila: int) -> None:
        entrada = self._entrada_seleccionada()
        if entrada is None:
            return
        if entrada.programa is None:
            self._visor.clear()
            self._etiqueta_detalle.setText(f"Detalle: {entrada.nombre} -> {entrada.error_carga}")
            return
        self._visor.setPlainText("\n".join(entrada.programa.lineas))
        if entrada.valido:
            self._etiqueta_detalle.setText(
                f"Detalle: {entrada.nombre} válido, {entrada.cantidad_lineas} líneas"
            )
        else:
            resumen = "; ".join(
                f"L{e.linea_nro}: {e.motivo}" for e in entrada.errores[:3]
            )
            resto = "" if len(entrada.errores) <= 3 else f" (+{len(entrada.errores)-3} más)"
            self._etiqueta_detalle.setText(f"Detalle: {entrada.nombre} inválido -> {resumen}{resto}")

    def _al_cargar(self) -> None:
        entrada = self._entrada_seleccionada()
        if entrada is None:
            self._etiqueta_estado.setText("Elegí un programa primero")
            return
        if not entrada.valido:
            # Cargar significa seleccionar en UI, no mover el plato.
            self.programa_cargado = None
            self._etiqueta_estado.setText(f"No cargado: {entrada.nombre} tiene errores")
            print(f"[ui_plato] bloqueo carga {entrada.nombre} errores={len(entrada.errores)}", flush=True)
            return
        self.programa_cargado = entrada
        self._etiqueta_estado.setText(f"Cargado: {entrada.nombre}")
        print(f"[ui_plato] cargado {entrada.nombre} lineas={entrada.cantidad_lineas}", flush=True)