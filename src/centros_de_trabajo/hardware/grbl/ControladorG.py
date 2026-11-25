import serial
import time

class ControladorG:
    def __init__(self,puerto="/dev/ttyUSB0", baudios=115200, modo_abs="G90", unidad="G21",feed_rate="F100"):
        self.x0, self.y0, self.z0 = 0, 0, 0
        self.baudios = baudios
        self.modo_abs = modo_abs
        self.unidad = unidad
        self.feed_rate = feed_rate
        self.puerto_serie = serial.Serial(self.puerto, self.baudios, timeout=2)
        self.modals = f"{unidad} {modo_abs} {feed_rate}"


    def enviar(self, linea):
        '''Envia orden de movimiento via puerto serie'''
        print(f">>> {linea}")

        encoded = f"{linea}\n".encode()
        self.puerto_serie.write(encoded)
        respuesta = self.puerto_serie.readline().decode().strip()

        print(f"<<< {respuesta}")

        if respuesta.startswith("error"):
            raise RuntimeError(f"GRBL rechazó: {linea} -> {respuesta}")
        return respuesta



    def set_modals(self, unidad="G21", modo="G90", feed="F100"):
        """Su función es fijar contexto en la placa, no solo en memoria."""
        # unidad, modo, feed son VALORES GENERICOS de prueba en vacío
        self.enviar(f"{unidad} {modo}")
        self.enviar(feed)


    def close(self):
        self._serie.close()
