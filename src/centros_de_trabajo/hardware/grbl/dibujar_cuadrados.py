import serial
import time

# Valores genéricos de prueba en vacío, cambialos para tu caso real.
PUERTO = "/dev/ttyUSB0"  # valor genérico: reemplazalo por tu puerto real de /dev/serial/by-id/
BAUDIOS = 115200  # valor genérico estándar de GRBL
LADO = 2.0  # valor genérico: lado del cuadrado en mm
FEED = 100.0  # valor genérico: velocidad en mm/min
CANTIDAD = 4  # valor genérico: cuántos cuadrados
PASO_ORIGEN = 3.0  # valor genérico: 2mm de lado + 1mm de separación


def enviar(ser, linea):
    """Su función es mandar una línea y esperar su ok."""
    print(f">>> {linea}")
    ser.write((linea + "\n").encode())
    respuesta = ser.readline().decode().strip()
    print(f"<<< {respuesta}")
    if respuesta.startswith("error"):
        raise RuntimeError(f"GRBL rechazó: {linea} -> {respuesta}")
    return respuesta


def set_modals(ser, feed=FEED):
    """Su función es fijar milímetros, absoluto y velocidad base."""
    enviar(ser, "G21 G90")
    enviar(ser, f"F{feed:g}")


def dibujar_un_cuadrado(ser, origen_x, lado=LADO):
    """Su función es dibujar un cuadrado de lado dado desde origen_x."""
    x0 = origen_x
    x1 = origen_x + lado
    enviar(ser, f"G1 X{x1:g} Y0")
    enviar(ser, f"G1 X{x1:g} Y{lado:g}")
    enviar(ser, f"G1 X{x0:g} Y{lado:g}")
    enviar(ser, f"G1 X{x0:g} Y0")


def dibujar_cuadrados(ser, cantidad=CANTIDAD):
    """Su función es repetir el cuadrado y reposicionar en rápido."""
    set_modals(ser)
    for i in range(cantidad):
        origen = i * PASO_ORIGEN
        # G0 es traslado en aire, no dibuja.
        enviar(ser, f"G0 X{origen:g} Y0")
        dibujar_un_cuadrado(ser, origen)


if __name__ == "__main__":
    with serial.Serial(PUERTO, BAUDIOS, timeout=2) as ser:
        time.sleep(2)  # espera a que GRBL reinicie y mande el welcome
        ser.reset_input_buffer()
        dibujar_cuadrados(ser)