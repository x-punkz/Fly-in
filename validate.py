# from pydantic import BaseModel, Field, ValidationError, model_validator
from sys import argv
from parser import Hub, Drone
from pydantic import ValidationError


def parser(config_file: str) -> None:
    hubs_list = []
    possibles_zones = ["normal", "blocked", "restricted", "priority"]
    for line in config_file.splitlines():
        if line.strip() and not line.startswith("#"):
            key, value = line.strip().split(":")

            if key.startswith("nb_drones"):
                Drone.nb_drones = int(value.strip())

            elif key.startswith("start_hub"):
                brute_data = value.strip()
                brute_data = brute_data.replace("]", "").split("[")
                data = brute_data[0].strip().split(" ")
                value = data

                if len(brute_data) != 2:
                    pass
                else:
                    meta = {k: v
                            for k, v in (item.split("=")
                                         for item in brute_data[1].split())}

                    if not len(meta) <= 3:
                        raise ValueError("Many Arguments in metadata!")
                    value.append(meta)

                start_hub = Hub(
                    name=value[0],
                    x=value[1],
                    y=value[2],
                    color="blue",
                    zone="normal",
                    start_hub=True,
                    )
# PRECISO PASSAR OS VALORES DE META P START_HUB
                print(start_hub)

            # if key.startswith("hub"):

                possibles_zones
                # tratar depois os metadados como opcionais aqui!


def validate_input() -> None:
    try:
        config_dict: str
        with open(argv[1]) as file:
            config_file = file.read()
            config_dict = parser(config_file)
    except (Exception, ValidationError) as e:  # PRECISO VER O ERRO DE VALIDATOR E DE EXCEPTION
        if Exception:
            print(e)
        elif ValidationError:
            print(e.errors()[0]["msg"])
        exit(1)
    return config_dict


validate_input()
