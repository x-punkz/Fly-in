# from pydantic import BaseModel, Field, ValidationError, model_validator
from sys import argv


def parser(config_file: str) -> None:
    for line in config_file.splitlines():
        if line.strip() and not line.startswith("#"):
            key, value = line.split(":")
            if key.startswith("nb_drones"):
                nb_drones = int(value.strip())

            if key.startswith("start_hub"):
                value = value.strip().split(" ")
                name, x, y = str(value[0]), int(value[1]), int(value[2])
                # tratar depois os metadados como opcionais aqui!


def validate_input() -> None:
    try:
        config_dict: str
        with open(argv[1]) as file:
            config_file = file.read()
            config_dict = parser(config_file)
    except Exception as e:
        print(e)
        exit(1)
    return config_dict


validate_input()
