import utime
from captive_portal import start_portal
from mqtt_client import (
    conectar_mqtt,
    suscribirse,
    solicitar_llave,
    publicar,
    tiene_clave,
)
from button import fue_presionado
from wifi_connection import sta, led, connect
from network_params import load_all_credentials, save_credentials
from temp import ReturnRandTempHum

print("Iniciando en 3 segundos... (Ctrl+C para interrumpir)")
utime.sleep(3)

USER = "espGhoul"
ESP8A = "esp8a"

while True:
    try:
        # Intentar conectar con credenciales guardadas
        connected = False
        creds = load_all_credentials()
        if creds:
            print("Intentando credenciales guardadas...")
            for c in creds:
                print("  Probando:", c["ssid"])
                if connect(c["ssid"], c["password"]):
                    connected = True
                    break

        # Si no se pudo, lanzar portal cautivo
        if not connected:
            print("Lanzando portal de configuracion WiFi...")
            start_portal()

        print("Conectando al broker MQTT...")
        client = conectar_mqtt("broker.hivemq.com", 1883)

        if not client:
            print("No se pudo conectar al broker MQTT")
            led.off()
            utime.sleep(5)
            continue

        # Suscribirse a iot_pub_get y iot_esp_topic
        suscribirse(client, USER)

        # Solicitar llave publica del servidor
        solicitar_llave(client, USER)

        # Esperar a recibir la llave del servidor
        print("Esperando llave del servidor...")
        timeout = utime.ticks_ms()
        while not tiene_clave():
            client.check_msg()
            if utime.ticks_diff(utime.ticks_ms(), timeout) > 10000:
                print("Timeout esperando llave, reintentando...")
                solicitar_llave(client, USER)
                timeout = utime.ticks_ms()
            utime.sleep_ms(100)

        print("Clave compartida establecida, iniciando envio de datos")
        last_send = utime.ticks_ms()

        while sta.isconnected():
            try:
                client.check_msg()
            except Exception as e:
                print("Error MQTT check_msg:", e)
                break

            presionado, state = fue_presionado()
            if presionado:
                print("Boton state:", state)
                try:
                    publicar(client, "led", {"state": state}, USER, to=ESP8A)
                except Exception as e:
                    print("Error publicando boton:", e)
                    break

            if utime.ticks_diff(utime.ticks_ms(), last_send) >= 2000:
                data = ReturnRandTempHum()
                print("Enviando sensor:", data)
                try:
                    publicar(
                        client,
                        "humtemp",
                        {"temp": data["temp"], "hum": data["hum"]},
                        USER,
                    )
                except Exception as e:
                    print("Error publicando sensor:", e)
                    break
                last_send = utime.ticks_ms()

            utime.sleep_ms(100)

        print("WiFi desconectado, relanzando...")
        led.off()

    except Exception as e:
        print("Error inesperado:", e)
        led.off()
        utime.sleep(5)
