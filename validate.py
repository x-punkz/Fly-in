# from pydantic import BaseModel, Field, ValidationError, model_validator
from sys import argv
from map import Hub, Connection, Map
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

                # valida o numero de drones
                if key.startswith("nb_drones"):
                    Map.nb_drones = int(value.strip())

                # valida hubs
                elif "hub" in key:
                    if ((key == "start_hub" and "start" not in value)
                            or (key == "end_hub" and "goal" not in value)):
                        raise ParserError("Start_hub name isn't start or "
                                          "end_hub name isn't goal")
                    if key == "start_hub":
                        self.start_count += 1
                        if self.start_count > 1:
                            raise ParserError("Duplicate start_hub defined.")
                    if key == "end_hub":
                        self.end_count += 1
                        if self.end_count > 1:
                            raise ParserError("Duplicate end_hub defined.")

                    # valida os dados do hub e cria o objeto Hub
                    datas = ValidateDatas.hub_validate(key, value)
                    if len(datas) < 1:
                        raise TypeError(f"The '{key}' has no data.")
                    data, meta_data = datas
                    hub_list.append(Creator.create_hubs(data, meta_data))

                # valida os dados da conexão e cria o objeto Connection
                elif "connection" in key:
                    connect_list: list[Connection] = []
                    datas = ValidateDatas.connection_validate(key, value)
                    if len(datas) < 1:
                        raise TypeError(f"The '{key}' has no data.")
                    endpoints, meta_data = datas
                    connect_list.append(
                        Connection(
                            hub1=endpoints[0],
                            hub2=endpoints[1],
                            # rever isso aqui.
                            max_link_capacity=meta_data["max_link_capacity"]
                            if meta_data and "max_link_capacity" in meta_data
                            else 1
                        )
                    )
                    print("\n--------Lista de conexões----------")



        print("--------Lista de hubs----------\n")
        print(*hub_list, sep="\n")

        print("\n--------Lista de conexões----------")
        print(*connect_list, sep="\n")


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

    @staticmethod
    def connection_validate(key: str, value: str) -> tuple:
        key_names = ["max_link_capacity"]
        value = value.strip()
        brute_data = value.split("[")
        raw = brute_data[0].strip()

        if raw == '':
            raise ParserError(" There is no data for the connection.")

        endpoints = raw.split("-")
        if len(endpoints) != 2 or not endpoints[0] or not endpoints[1]:
            raise ParserError(
                f"Invalid connection format in: "
                f"'{key}: {value}'"
            )

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

            if not len(meta) <= 1:
                raise ParserError("Many Arguments in metadata!")

            for mkey in meta.keys():
                if mkey not in key_names:
                    raise ParserError(f"'{mkey}' is not valid keys name")

        return (endpoints, meta)


class Creator:
    def create_hubs(data: list[str], meta_data: dict[str, str]) -> Hub:
        try:
            hub = Hub(
                    name=data[0],
                    x=data[1],
                    y=data[2]
                )
            if meta_data:
                hub.set_metadata(meta_data)
        except ValidationError as e:
            print(f"In hub_list: {e.errors()[0]["msg"]}")
            exit(1)
        # verifica se todos os hubs têm start e end definidos
        hub.set_start_end()
        return hub

    def create_connections() -> None:
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
