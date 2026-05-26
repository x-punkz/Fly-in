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

            if key.startswith("start_hub"):
                data = value.strip()
                data = data.replace("]", "")
                meta_data = data.split("[")
                data = meta_data[0].strip().split(" ")
                meta_data = meta_data[1]
                value = value.strip().split(" ")
                data_list = meta_data.split(" ")

                
                start_hub = Hub(
                    name=value[0],
                    x=value[1],
                    y=value[2],
                    color="blue",
                    zone="normal",
                    start_hub=True,
                    )
                print(data)
                print(meta_data)
                print(tu, tutu)
            # if key.startswith("hub"):

                possibles_zones
                # tratar depois os metadados como opcionais aqui!


def validate_input() -> None:
    try:
        config_dict: str
        with open(argv[1]) as file:
            config_file = file.read()
            config_dict = parser(config_file)
    except (Exception, ValidationError) as e:
        # print(e.errors()[0]["msg"])
        print(e)
        exit(1)
    return config_dict


validate_input()
