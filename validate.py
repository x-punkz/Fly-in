# from pydantic import BaseModel, Field, ValidationError, model_validator
from sys import argv
from parser import Hub, Map
from pydantic import ValidationError


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, config_file: str) -> None:
        self.config_file = config_file
        # contador para detectar duplicatas de start e end
        self.start_count = 0
        self.end_count = 0

    def parse(self) -> None:
        hub_list: list[Hub] = []
        for line in self.config_file.splitlines():
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split(":")
                if ((key == "start_hub" and "start" not in value)
                        or (key == "end_hub" and "goal" not in value)):
                    raise ParserError("Start_hub name isn't start or "
                                      "end_hub name isn't goal")

                if key.startswith("nb_drones"):
                    Map.nb_drones = int(value.strip())

                elif "hub" in key:
                    # verificar duplicatas de start/goal
                    if key == "start_hub":
                        self.start_count += 1
                        if self.start_count > 1:
                            raise ParserError("Duplicate start_hub defined.")
                    if key == "end_hub":
                        self.end_count += 1
                        if self.end_count > 1:
                            raise ParserError("Duplicate end_hub defined.")

                    datas = ValidateDatas.hub_validate(key, value)
                    if len(datas) < 1:
                        raise TypeError(f"The '{key}' has no data.")
                    data, meta_data = datas
                    try:
                        hub_list.append(
                            Hub(
                                name=data[0],
                                x=data[1],
                                y=data[2]
                            )
                        )
                        if meta_data:
                            hub_list[len(hub_list) - 1].set_metadata(meta_data)
                    except ValidationError as e:
                        print(f"In hub_list: {e.errors()[0]["msg"]}")
                        exit(1)
        for hub in hub_list:
            hub.set_start_end()

        print(*hub_list, sep="\n")

        # fazer os conection


class ValidateDatas:

    @staticmethod
    def hub_validate(key: str, value: str) -> tuple:
        key_names = ["zone", "color", "max_drones"]
        possible_zones = ["normal", "blocked", "restricted", "priority"]
        value = value.strip()
        brute_data = value.split("[")
        data = brute_data[0].strip().split()

        if len(brute_data) != 2:
            meta = None
            pass
        else:
            brute_metadata = brute_data[1].strip().split("]")

            if not brute_metadata[1]:
                brute_metadata = [brute_metadata[0]]

            if (len(brute_metadata) > 1
                    and not brute_metadata[1].strip().startswith("#")):
                raise ParserError(f"Many arguments in line in: \
'{key}: {value}'")

            meta = {k: v
                    for k, v in (
                        item.split("=")
                        for item in brute_metadata[0].split()
                    )}
            if not len(meta) <= 3:
                raise ParserError("Many Arguments in metadata!")

            elif data == ['']:
                raise ParserError(" There is no data for the hub.")
            for key in meta.keys():
                if key not in key_names:
                    raise ParserError(f"'{key}' is not valid keys name")

                if key == 'zone' and meta['zone'] not in possible_zones:
                    raise ParserError(f"{meta['zone']} is not a valid zone")

        return (data, meta)

    def connection_validate(key: str, value: str) -> tuple:
        pass


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
        exit(1)
    return config_dict


validate_input()
