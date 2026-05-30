# from pydantic import BaseModel, Field, ValidationError, model_validator
from sys import argv
from parser import Hub, Map
from pydantic import ValidationError


class Parser:
    def __init__(self, config_file: str) -> None:
        self.config_file = config_file

    def parse(self) -> None:
        # hubs_list = []
        for line in self.config_file.splitlines():
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split(":")

                if key.startswith("nb_drones"):
                    Map.nb_drones = int(value.strip())

                elif key.startswith("start_hub"):
                    datas = Hub.hub_validate(key, value)
                    if len(datas) < 1:
                        raise TypeError(f"The '{key}' has no data.")
                    data, meta_data = datas

                    print(data, meta_data)
    # VER A CARALHA DOS NOMES REPETIDOS DE META, E DIVIDIR AS FUNÇOES EM PARSER
    #             start_hub = Hub(
    #                 name=value[0],
    #                 x=value[1],
    #                 y=value[2],
    #                 start_hub=True,
    #                 )
    # # PRECISO PASSAR OS VALORES DE META P START_HUB
    #             if "color" in meta.keys():
    #                 start_hub.color = meta["color"]
    #             print(start_hub)

                # if key.startswith("hub"):
                # tratar depois os metadados como opcionais aqui!


def validate_input() -> None:
    try:

        with open(argv[1]) as file:
            config_file = file.read()
            config_dict = Parser(config_file)
            config_dict.parse()
    except (Exception, ValidationError) as e:  # PRECISO VER O ERRO DE VALIDATOR E DE EXCEPTION
        #     # if Exception:
        print(e)
        #     # elif ValidationError:
        #     #    print(e.errors()[0]["msg"])
        exit(1)
    return config_dict


validate_input()
