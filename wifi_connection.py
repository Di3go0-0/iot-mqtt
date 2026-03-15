import network
import utime
from machine import Pin

led = Pin(2, Pin.OUT)


def connect(NET="UTP", NET_PASSWORD="tecnologica"):
    print("Iniciando conexión WiFi...", NET, NET_PASSWORD)

    wifi = network.WLAN(network.WLAN.IF_STA)

    wifi.active(False)
    utime.sleep(1)
    wifi.active(True)

    if wifi.isconnected():
        wifi.disconnect()
        utime.sleep(1)

    wifi.connect(NET, NET_PASSWORD)

    ATTEMPTS = 4

    while not wifi.isconnected() and ATTEMPTS > 0:
        print("Conectando...")
        led.on()
        utime.sleep_ms(200)
        led.off()
        utime.sleep_ms(800)
        ATTEMPTS -= 1

    if wifi.isconnected():
        print("Conectado!")
        print("IP:", wifi.ifconfig()[0])
        return True
    else:
        print("No se pudo conectar")
        return False
