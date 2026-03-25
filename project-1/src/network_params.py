PARAMS_FILE = "wifi_params.txt"


def write_params(ssid, password):
    with open(PARAMS_FILE, "w") as f:
        f.write("ssid={}\n".format(ssid))
        f.write("password={}\n".format(password))


def read_params():
    try:
        params = {}
        with open(PARAMS_FILE) as f:
            for line in f:
                key, value = line.strip().split("=", 1)
                params[key] = value
        return params.get("ssid"), params.get("password")
    except OSError:
        return None, None
