from centros_de_trabajo.hardware.grbl.controlador import ControladorG
from centros_de_trabajo.hardware.grbl.orden import OrdenDeMovimiento

ctrl = ControladorG()  # usa PUERTO_DEFAULT que es VALOR GENERICO
ctrl.set_modals()
cuadrado = OrdenDeMovimiento(nombre="cuadrado-2mm", lineas=["G1 X1 Y0 F60", "G1 X1 Y1", "G1 X0 Y1", "G1 X0 Y0"])
cuadrado.ejecutar(ctrl)
ctrl.close()