# from pydantic import BaseModel, Field, ValidationError, model_validator
from sys import argv
from parser import Hub, Map, ValidateDatas
from pydantic import ValidationError


class Parser:
    def __init__(self, config_file: str) -> None:
        self.config_file = config_file

    def parse(self) -> None:
        hub_list: list[Hub] = []
        for line in self.config_file.splitlines():
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split(":")

                if key.startswith("nb_drones"):
                    Map.nb_drones = int(value.strip())

                elif "hub" in key:
                    datas = ValidateDatas.hub_validate(key, value)
                    if len(datas) < 1:
                        raise TypeError(f"The '{key}' has no data.")
                    data, meta_data = datas
                    hub_list.append(
                        Hub(
                            name=data[0],
                            x=data[1],
                            y=data[2]
                        )
                    )
                    if meta_data:
                        hub_list[len(hub_list) - 1].set_metadata(meta_data)
        for hub in hub_list:
            hub.set_start_end()

        print(*hub_list, sep="\n")

        # fazer os conection


def validate_input() -> None:
    if len(argv) < 2:
        print("   Passe o arquivo de configuraçao!")
        exit(1)
    try:

        with open(argv[1]) as file:
            config_file = file.read()
            config_dict = Parser(config_file)
            config_dict.parse()
    except (Exception, ValidationError) as e:
        # PRECISO VER O ERRO DE VALIDATOR E DE EXCEPTION
        #     # if Exception:
        print(e)
        #     # elif ValidationError:
        #     #    print(e.errors()[0]["msg"])
        exit(1)
    return config_dict


validate_input()
