import random


def ReturnRandTempHum():
    temp = random.randint(30, 40)
    hum = random.randint(70, 90)

    return {"temp": temp, "hum": hum}

