import network
import utime
from machine import Pin

led = Pin(2, Pin.OUT)


def connect(ssid, password, max_attempts=2):
    print("Conectando a WiFi:", ssid)

    sta = network.WLAN(network.WLAN.IF_STA)
    sta.active(False)
    utime.sleep(1)
    sta.active(True)

    if sta.isconnected():
        sta.disconnect()
        utime.sleep(1)

    sta.connect(ssid, password)

    attempts = max_attempts * 4  # 4 parpadeos por intento (~4s por intento)

    while not sta.isconnected() and attempts > 0:
        led.on()
        utime.sleep_ms(200)
        led.off()
        utime.sleep_ms(800)
        attempts -= 1

    if sta.isconnected():
        print("Conectado! IP:", sta.ifconfig()[0])
        led.on()
        return True
    else:
        print("No se pudo conectar después de", max_attempts, "intentos")
        led.off()
        return False
