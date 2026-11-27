# Ruta: src/centros_de_trabajo/ui/plato/ui_plato.py en PC LAB - reemplazar TODO el archivo
from __future__ import annotations

from pathlib import Path
import time

from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from centros_de_trabajo.estaciones.inventario_puertos import listar_puertos
from centros_de_trabajo.estaciones.plato.catalogo_programas import (
    EntradaCatalogo,
    listar_programas,
)


BAUDIOS_POR_DEFECTO = 115200
TIMEOUT_SERIE_SEG = 2.0
LIMITE_X_MAX = 200.0
LIMITE_Y_MAX = 1.0


class VentanaPlato(QMainWindow):
    """Lista programas, conecta serie, consola $$ y jog X/Y por pasos."""

    def __init__(self, carpeta_programas: Path, kiosco: bool = False) -> None:
        super().__init__()
        # carpeta_programas es VALOR GENERICO, en desarrollo ej:
        # Path("src/centros_de_trabajo/estaciones/plato/programas")
        self._carpeta = carpeta_programas
        self._entradas: list[EntradaCatalogo] = []
        self.programa_cargado: EntradaCatalogo | None = None
        self.puerto_conectado: str | None = None
        self._serie = None
        self._pos_x = 0.0
        self._pos_y = 0.0

        self.setWindowTitle("Plato - Programas G")
        if kiosco:
            self.showFullScreen()

        contenedor = QWidget()
        layout = QVBoxLayout()

        # 1) Firmware + puertos + baudios: queda arriba como está.
        fila_conexion = QHBoxLayout()
        self._combo_firmware = QComboBox()
        self._combo_firmware.addItems(["GRBL"])
        self._combo_puerto = QComboBox()
        self._combo_puerto.setMinimumWidth(320)
        self._combo_baud = QComboBox()
        self._combo_baud.addItems(["115200", "9600"])
        self._combo_baud.setCurrentText(str(BAUDIOS_POR_DEFECTO))
        self._boton_conectar = QPushButton("CONECTAR")
        self._boton_actualizar_puertos = QPushButton("ACTUALIZAR PUERTOS")
        self._etiqueta_controlador = QLabel("Controller state: DESCONECTADO")
        fila_conexion.addWidget(QLabel("Firmware:"))
        fila_conexion.addWidget(self._combo_firmware)
        fila_conexion.addWidget(QLabel("Port:"))
        fila_conexion.addWidget(self._combo_puerto, stretch=1)
        fila_conexion.addWidget(QLabel("Baud:"))
        fila_conexion.addWidget(self._combo_baud)
        fila_conexion.addWidget(self._boton_conectar)
        fila_conexion.addWidget(self._boton_actualizar_puertos)
        layout.addLayout(fila_conexion)
        layout.addWidget(self._etiqueta_controlador)

        linea1 = QFrame()
        linea1.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(linea1)

        # Zona media: 2) Programas a la izquierda, 4) Control manual a la derecha.
        medio = QHBoxLayout()

        panel_programas = QWidget()
        panel_programas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay_prog = QVBoxLayout()
        lay_prog.addWidget(QLabel("2) Programas"))
        self._etiqueta_estado = QLabel("Sin programa cargado")
        self._lista = QListWidget()
        self._visor = QPlainTextEdit()
        self._visor.setReadOnly(True)
        self._visor.setMaximumBlockCount(2000)
        self._etiqueta_detalle = QLabel("Detalle: -")
        self._etiqueta_detalle.setWordWrap(True)
        self._boton_cargar = QPushButton("CARGAR")
        self._boton_actualizar = QPushButton("ACTUALIZAR LISTA")
        lay_prog.addWidget(self._etiqueta_estado)
        lay_prog.addWidget(self._lista)
        lay_prog.addWidget(self._visor)
        lay_prog.addWidget(self._etiqueta_detalle)
        lay_prog.addWidget(self._boton_cargar)
        lay_prog.addWidget(self._boton_actualizar)
        panel_programas.setLayout(lay_prog)

        panel_jog = QWidget()
        panel_jog.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay_jog = QVBoxLayout()
        lay_jog.addWidget(QLabel("4) Control manual"))
        lay_jog.addWidget(QLabel("X Step size:"))
        self._step_x = QDoubleSpinBox()
        self._step_x.setRange(0.1, 10.0)
        self._step_x.setValue(1.0)
        lay_jog.addWidget(self._step_x)
        lay_jog.addWidget(QLabel("Y Step size:"))
        self._step_y = QDoubleSpinBox()
        self._step_y.setRange(0.1, 10.0)
        self._step_y.setValue(1.0)
        lay_jog.addWidget(self._step_y)
        lay_jog.addWidget(QLabel("Feed rate:"))
        self._feed = QDoubleSpinBox()
        self._feed.setRange(1.0, 1000.0)
        self._feed.setValue(102.0)
        lay_jog.addWidget(self._feed)
        self._btn_x_menos = QPushButton("X-")
        self._btn_x_mas = QPushButton("X+")
        self._btn_y_menos = QPushButton("Y-")
        self._btn_y_mas = QPushButton("Y+")
        lay_jog.addWidget(self._btn_x_menos)
        lay_jog.addWidget(self._btn_x_mas)
        lay_jog.addWidget(self._btn_y_menos)
        lay_jog.addWidget(self._btn_y_mas)
        self._etiqueta_pos = QLabel("Pos X: 0.0 / 200 | Pos Y: 0.0 / 1")
        self._etiqueta_pos.setWordWrap(True)
        lay_jog.addWidget(self._etiqueta_pos)
        lay_jog.addStretch(1)
        panel_jog.setLayout(lay_jog)

        medio.addWidget(panel_programas, stretch=1)
        medio.addWidget(panel_jog, stretch=1)
        layout.addLayout(medio, stretch=1)

        linea2 = QFrame()
        linea2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(linea2)

        # 3) Consola: ocupa solo la mitad horizontal izquierda.
        fila_consola_titulo = QLabel("3) Consola")
        layout.addWidget(fila_consola_titulo)
        fila_consola = QHBoxLayout()
        panel_consola = QWidget()
        panel_consola.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        lay_cons = QVBoxLayout()
        self._consola_vista = QPlainTextEdit()
        self._consola_vista.setReadOnly(True)
        self._consola_vista.setPlaceholderText("Consola GRBL: conectá y enviá $$")
        self._consola_vista.setMinimumHeight(140)
        self._consola_entrada = QLineEdit()
        self._consola_entrada.setText("$$")
        self._boton_enviar = QPushButton("ENVIAR")
        fila_envio = QHBoxLayout()
        fila_envio.addWidget(self._consola_entrada, stretch=1)
        fila_envio.addWidget(self._boton_enviar)
        lay_cons.addWidget(self._consola_vista)
        lay_cons.addLayout(fila_envio)
        panel_consola.setLayout(lay_cons)
        relleno_consola = QWidget()
        relleno_consola.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        fila_consola.addWidget(panel_consola, stretch=1)
        fila_consola.addWidget(relleno_consola, stretch=1)
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
        self._btn_x_mas.clicked.connect(lambda: self.mover_jog("X", self._step_x.value(), self._feed.value()))
        self._btn_x_menos.clicked.connect(lambda: self.mover_jog("X", -self._step_x.value(), self._feed.value()))
        self._btn_y_mas.clicked.connect(lambda: self.mover_jog("Y", self._step_y.value(), self._feed.value()))
        self._btn_y_menos.clicked.connect(lambda: self.mover_jog("Y", -self._step_y.value(), self._feed.value()))

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
            self._etiqueta_detalle.setText(f"Detalle: {entrada.nombre} válido, {entrada.cantidad_lineas} líneas")
        else:
            resumen = "; ".join(f"L{e.linea_nro}: {e.motivo}" for e in entrada.errores[:3])
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
            return
        try:
            s = serial.Serial(str(ruta), baud, timeout=TIMEOUT_SERIE_SEG)
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
        except Exception as e:
            self.puerto_conectado = None
            self._etiqueta_controlador.setText("Controller state: ERROR APERTURA")
            print(f"[ui_plato] error abriendo {ruta}: {e}", flush=True)

    def _al_enviar_consola(self) -> None:
        texto = self._consola_entrada.text().strip()
        if not texto or self._serie is None:
            self._consola_vista.appendPlainText("! no hay conexión, presioná CONECTAR primero")
            return
        upper = texto.upper()
        if upper.startswith("G") or upper.startswith("M") or upper.startswith("$J"):
            self._consola_vista.appendPlainText(f"! bloqueado en consola MVP: {texto}")
            print(f"[ui_plato] consola bloquea movimiento {texto!r}", flush=True)
            return
        self._enviar_y_leer(texto)

    def mover_jog(self, eje: str, distancia: float, feed: float) -> bool:
        """Mueve un paso jog en X/Y con límite. Devuelve True si GRBL respondió ok."""
        eje = eje.upper()
        if eje not in ("X", "Y"):
            print(f"[ui_plato] mover_jog eje inválido {eje!r}", flush=True)
            return False
        if self._serie is None:
            self._etiqueta_controlador.setText("Controller state: SIN CONEXION PARA MOVER")
            print("[ui_plato] mover_jog sin conexion", flush=True)
            return False
        nueva_x = self._pos_x + (distancia if eje == "X" else 0.0)
        nueva_y = self._pos_y + (distancia if eje == "Y" else 0.0)
        if not (0.0 <= nueva_x <= LIMITE_X_MAX):
            print(f"[ui_plato] mover_jog bloqueado X {nueva_x} fuera de 0..{LIMITE_X_MAX}", flush=True)
            self._consola_vista.appendPlainText(f"! límite X: {nueva_x:.2f} fuera de 0..{LIMITE_X_MAX}")
            return False
        if not (0.0 <= nueva_y <= LIMITE_Y_MAX):
            print(f"[ui_plato] mover_jog bloqueado Y {nueva_y} fuera de 0..{LIMITE_Y_MAX}", flush=True)
            self._consola_vista.appendPlainText(f"! límite Y: {nueva_y:.2f} fuera de 0..{LIMITE_Y_MAX}")
            return False
        comando = f"$J=G21G91{eje}{distancia}F{feed:g}"
        print(f"[ui_plato] mover_jog envia {comando!r}", flush=True)
        self._consola_vista.appendPlainText(f"> {comando}")
        ok = self._enviar_y_leer(comando)
        if ok:
            if eje == "X":
                self._pos_x = nueva_x
            else:
                self._pos_y = nueva_y
            self._etiqueta_pos.setText(f"Pos X: {self._pos_x:.1f} / 200 | Pos Y: {self._pos_y:.1f} / 1")
        return ok

    def _enviar_y_leer(self, texto: str) -> bool:
        try:
            self._serie.write((texto + "\n").encode())
            limite = time.monotonic() + TIMEOUT_SERIE_SEG + 2.0
            while time.monotonic() < limite:
                raw = self._serie.readline()
                if not raw:
                    continue
                txt = raw.decode(errors="replace").rstrip("\r\n")
                if txt == "":
                    continue
                if txt.startswith("<"):
                    self._consola_vista.appendPlainText(f"< {txt}")
                    print(f"[ui_plato] estado {txt!r}", flush=True)
                    continue
                self._consola_vista.appendPlainText(f"< {txt}")
                print(f"[ui_plato] recibe {txt!r}", flush=True)
                bajo = txt.strip().lower()
                if bajo == "ok":
                    return True
                if bajo.startswith("error") or "alarm" in bajo:
                    return False
            print("[ui_plato] sin respuesta ok/timeout", flush=True)
            return False
        except Exception as e:
            self._consola_vista.appendPlainText(f"! error serie: {e}")
            print(f"[ui_plato] error serie {e}", flush=True)
            return False