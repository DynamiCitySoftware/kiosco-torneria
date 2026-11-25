# Ruta: src/centros_de_trabajo/ui/plato/ui_plato.py en PC LAB - reemplazar TODO el archivo
from __future__ import annotations

from pathlib import Path
import time

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from centros_de_trabajo.estaciones.inventario_puertos import listar_puertos
from centros_de_trabajo.estaciones.plato.catalogo_programas import (
    EntradaCatalogo,
    listar_programas,
)


# VALOR_GENERICO_BAUD es genérico con valor inicial real tuyo: 115200 de tu captura.
# VALOR_GENERICO_TIMEOUT es genérico: 2.0 segundos para welcome y consola.
BAUDIOS_POR_DEFECTO = 115200
TIMEOUT_SERIE_SEG = 2.0


class VentanaPlato(QMainWindow):
    """Lista programas, permite cargarlos, conecta serie y consola $$."""

    def __init__(self, carpeta_programas: Path, kiosco: bool = False) -> None:
        super().__init__()
        # carpeta_programas es VALOR GENERICO, en desarrollo ej:
        # Path("src/centros_de_trabajo/estaciones/plato/programas")
        self._carpeta = carpeta_programas
        self._entradas: list[EntradaCatalogo] = []
        self.programa_cargado: EntradaCatalogo | None = None
        self.puerto_conectado: str | None = None
        self._serie = None

        self.setWindowTitle("Plato - Programas G")
        if kiosco:
            self.showFullScreen()

        contenedor = QWidget()
        layout = QVBoxLayout()

        fila_conexion = QHBoxLayout()
        self._combo_firmware = QComboBox()
        self._combo_firmware.addItems(["GRBL"])
        self._combo_puerto = QComboBox()
        self._combo_baud = QComboBox()
        self._combo_baud.addItems(["115200", "9600"])
        self._combo_baud.setCurrentText(str(BAUDIOS_POR_DEFECTO))
        self._boton_conectar = QPushButton("CONECTAR")
        self._boton_actualizar_puertos = QPushButton("ACTUALIZAR PUERTOS")
        self._etiqueta_controlador = QLabel("Controller state: DESCONECTADO")
        fila_conexion.addWidget(QLabel("Firmware:"))
        fila_conexion.addWidget(self._combo_firmware)
        fila_conexion.addWidget(QLabel("Port:"))
        fila_conexion.addWidget(self._combo_puerto)
        fila_conexion.addWidget(QLabel("Baud:"))
        fila_conexion.addWidget(self._combo_baud)
        fila_conexion.addWidget(self._boton_conectar)
        fila_conexion.addWidget(self._boton_actualizar_puertos)
        layout.addLayout(fila_conexion)
        layout.addWidget(self._etiqueta_controlador)

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

        # Consola serie estilo UGS
        self._consola_vista = QPlainTextEdit()
        self._consola_vista.setReadOnly(True)
        self._consola_vista.setPlaceholderText("Consola GRBL: conectá y enviá $$")
        self._consola_entrada = QLineEdit()
        self._consola_entrada.setPlaceholderText("Escribí $$ y presioná ENVIAR")
        self._consola_entrada.setText("$$")
        self._boton_enviar = QPushButton("ENVIAR")
        fila_consola = QHBoxLayout()
        fila_consola.addWidget(self._consola_entrada)
        fila_consola.addWidget(self._boton_enviar)
        layout.addWidget(QLabel("Consola:"))
        layout.addWidget(self._consola_vista)
        layout.addLayout(fila_consola)

        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        self._lista.currentRowChanged.connect(self._al_seleccionar)
        self._boton_cargar.clicked.connect(self._al_cargar)
        self._boton_actualizar.clicked.connect(self.recargar)
        self._boton_actualizar_puertos.clicked.connect(self.recargar_puertos)
        self._boton_conectar.clicked.connect(self._al_conectar)
        self._boton_enviar.clicked.connect(self._al_enviar_consola)
        self._consola_entrada.returnPressed.connect(self._al_enviar_consola)

        self.recargar_puertos()
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

    def recargar_puertos(self) -> None:
        puertos = listar_puertos()
        self._combo_puerto.clear()
        for p in puertos:
            etiqueta = p.etiqueta_by_id or "(sin by-id, clon sin serie)"
            self._combo_puerto.addItem(f"{p.nombre_by_path} | {etiqueta}", userData=str(p.ruta_by_path))
        print(f"[ui_plato] puertos={len(puertos)}", flush=True)
        if not puertos:
            self._etiqueta_controlador.setText("Controller state: SIN PUERTOS")

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
            self.programa_cargado = None
            self._etiqueta_estado.setText(f"No cargado: {entrada.nombre} tiene errores")
            print(f"[ui_plato] bloqueo carga {entrada.nombre} errores={len(entrada.errores)}", flush=True)
            return
        self.programa_cargado = entrada
        self._etiqueta_estado.setText(f"Cargado: {entrada.nombre}")
        print(f"[ui_plato] cargado {entrada.nombre} lineas={entrada.cantidad_lineas}", flush=True)

    def _al_conectar(self) -> None:
        ruta = self._combo_puerto.currentData()
        baud_txt = self._combo_baud.currentText()
        if not ruta:
            self._etiqueta_controlador.setText("Controller state: SIN PUERTO SELECCIONADO")
            return
        try:
            baud = int(baud_txt)
        except ValueError:
            self._etiqueta_controlador.setText("Controller state: BAUD INVALIDO")
            return
        # Cierra anterior si había
        try:
            if self._serie is not None:
                self._serie.close()
        except Exception:
            pass
        self._serie = None
        try:
            import serial
        except ImportError:
            self._etiqueta_controlador.setText("Controller state: FALTA PYSERIAL")
            print("[ui_plato] falta pyserial en el entorno", flush=True)
            return
        try:
            s = serial.Serial(str(ruta), baud, timeout=TIMEOUT_SERIE_SEG)
            # No limpiamos de más: GRBL manda welcome solo al reset.
            # Esperamos primera línea no vacía.
            limite = time.monotonic() + TIMEOUT_SERIE_SEG + 2.0
            welcome = None
            while time.monotonic() < limite:
                raw = s.readline()
                if not raw:
                    continue
                txt = raw.decode(errors="replace").strip()
                if txt:
                    welcome = txt
                    break
            if welcome:
                self._serie = s
                self.puerto_conectado = str(ruta)
                self._etiqueta_controlador.setText(f"Controller state: IDLE | {welcome}")
                self._consola_vista.appendPlainText(f"< {welcome}")
                print(f"[ui_plato] conectado {ruta} baud={baud} welcome={welcome!r}", flush=True)
            else:
                s.close()
                self.puerto_conectado = None
                self._etiqueta_controlador.setText("Controller state: NO_DISPONIBLE")
                print(f"[ui_plato] sin welcome {ruta} baud={baud}", flush=True)
        except Exception as e:
            self.puerto_conectado = None
            self._etiqueta_controlador.setText("Controller state: ERROR APERTURA")
            print(f"[ui_plato] error abriendo {ruta}: {e}", flush=True)

    def _al_enviar_consola(self) -> None:
        texto = self._consola_entrada.text().strip()
        if not texto:
            return
        if self._serie is None:
            self._consola_vista.appendPlainText("! no hay conexión, presioná CONECTAR primero")
            return
        # Solo consulta en este paso: $$, $I, $G, ?. Bloqueamos G/M de movimiento.
        # VALOR_GENERICO_PERMITIDOS es genérico: ej ["$$", "$I", "$G", "?"] para este MVP.
        upper = texto.upper()
        if upper.startswith("G") or upper.startswith("M") or upper.startswith("G0") or upper.startswith("G1"):
            self._consola_vista.appendPlainText(f"! bloqueado en consola MVP: {texto}")
            print(f"[ui_plato] consola bloquea movimiento {texto!r}", flush=True)
            return
        try:
            self._consola_vista.appendPlainText(f"> {texto}")
            print(f"[ui_plato] consola envia {texto!r}", flush=True)
            self._serie.write((texto + "\n").encode())
            limite = time.monotonic() + TIMEOUT_SERIE_SEG + 2.0
            while time.monotonic() < limite:
                raw = self._serie.readline()
                if not raw:
                    continue
                txt = raw.decode(errors="replace").rstrip("\r\n")
                if txt == "":
                    continue
                self._consola_vista.appendPlainText(f"< {txt}")
                print(f"[ui_plato] consola recibe {txt!r}", flush=True)
                if txt.strip().lower() in ("ok", "error"):
                    break
                # $$ devuelve muchas líneas y termina en ok
                if len(self._consola_vista.toPlainText()) > 20000:
                    break
        except Exception as e:
            self._consola_vista.appendPlainText(f"! error serie: {e}")
            print(f"[ui_plato] consola error {e}", flush=True)