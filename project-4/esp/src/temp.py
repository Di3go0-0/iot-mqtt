import random


def ReturnRandTempHum():
    temp = random.randint(35, 37)
    hum = random.randint(75, 80)

    return {"temp": temp, "hum": hum}
