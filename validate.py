# from pydantic import BaseModel, Field, ValidationError, model_validator
from sys import argv
from parser import Hub, Map, ValidateDatas
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

                elif "hub" in key:
                    datas = ValidateDatas.hub_validate(key, value)
                    if len(datas) < 1:
                        raise TypeError(f"The '{key}' has no data.")
                    # na hora de validar vejo if "star_hub in key:
                    # hub.start_hub = True"
                    data, meta_data = datas

                    print(data, meta_data)
    # E DIVIDIR AS FUNÇOES EM PARSER
    #             hub_list.append(
    #                 Hub(
        #                 name=value[0],
        #                 x=value[1],
        #                 y=value[2],
        #                 start_hub=True,
    #                 )
    #             )
    # # PRECISO PASSAR OS VALORES DE META P START_HUB
    #             if "color" in meta.keys():
    #                 hub.color = meta["color"]
    #             


                # tratar depois os metadados como opcionais aqui!


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
