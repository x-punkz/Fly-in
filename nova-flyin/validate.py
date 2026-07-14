from pydantic import ValidationError
from map import Hub, Connection


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, config_file: str) -> None:
        self.config_file = config_file
        # contador para detectar duplicatas de start e end
        self.start_count = 0
        self.end_count = 0

    def parse(self) -> tuple[list[Hub], list[Connection], int]:
        hub_list: list[Hub] = []
        connect_list: list[Connection] = []
        connect_set: set[tuple[str, str]] = set()

        nb_drone = 0

        for line in self.config_file.splitlines():
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split(":")

                # valida o numero de drones
                if key.startswith("nb_drones"):
                    if value.strip().isdigit() is False:
                        raise ValueError("Drone number isn't an int.")
                    nb_drone = int(value.strip())
                    if nb_drone <= 0:
                        raise ValueError("Nb_drone cannot be negative")

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
                    # if data[0] in hub_list:
                    if any(hub.name == data[0] for hub in hub_list):
                        raise ParserError(f"'{data[0]}' already exists")
                    hub_list.append(Creator.create_hubs(data, meta_data))

                # valida os dados da conexão e cria o objeto Connection
                elif "connection" in key:
                    hub_list_name: list[str] = [hub.name for hub in hub_list]
                    conn_datas = ValidateDatas.connection_validate(key, value)

                    if len(conn_datas) < 1:
                        raise TypeError(f"The '{key}' has no data.")
                    endpoints, m_data = conn_datas

                    sorted_endpoints = sorted(endpoints)
                    connection_id = (sorted_endpoints[0], sorted_endpoints[1])
                    if connection_id in connect_set:
                        raise ParserError(
                            "Duplicate connection: "
                            f"{endpoints[0]}-{endpoints[1]}"
                        )
                    connect_set.add(connection_id)

                    connect_list.append(
                        Creator.create_connections(
                            endpoints,
                            m_data,
                            hub_list_name
                        )
                    )

        return (hub_list, connect_list, nb_drone)


class ValidateDatas:

    @staticmethod
    def hub_validate(key: str, value: str) -> tuple[list[str],
                                                    dict[str, str]]:
        '''
            Valida os dados do vindos do arquivo de configuraçao do Hub.
            Retorna:
                Uma tupla contendo os dados e se existir, os metadados
                para o hub.
        '''
        key_names = ["zone", "color", "max_drones"]
        possible_zones = ["normal", "blocked", "restricted", "priority"]
        value = value.strip()
        brute_data = value.split("[")
        data = brute_data[0].strip().split()
        meta_data: dict[str, str] = {}

        if len(brute_data) != 2:
            return data, meta_data

        brute_metadata = brute_data[1].strip().split("]")

        if not brute_metadata[1]:
            brute_metadata = [brute_metadata[0]]

        if (len(brute_metadata) > 1
                and not brute_metadata[1].strip().startswith("#")):
            raise ParserError(
                f"Many arguments in line in: '{key}: {value}'"
            )

        for item in brute_metadata[0].split():
            key_name, value_name = item.split("=", 1)
            meta_data[key_name] = value_name

        if len(meta_data) > 3:
            raise ParserError("Many Arguments in metadata!")

        if not data:
            raise ParserError(" There is no data for the hub.")

        for key_name in meta_data:
            if key_name not in key_names:
                raise ParserError(f"'{key_name}' is not valid keys name")

            if key_name == "zone" and meta_data["zone"] not in possible_zones:
                raise ParserError(f"{meta_data['zone']} is not a valid zone")

        return data, meta_data

    @staticmethod
    def connection_validate(
        key: str,
        value: str,
    ) -> tuple[list[str], dict[str, int]]:
        '''
            Valida os dados do vindos do arquivo de configuraçao da Conexão.
            Retorna:
                Uma tupla contendo os endpoints das conexões e se existir,
                os metadados para a conexão.
        '''
        key_names = ["max_link_capacity"]
        value = value.strip()
        brute_data = value.split("[")
        raw = brute_data[0].strip()

        if raw == "":
            raise ParserError(" There is no data for the connection.")

        endpoints = raw.split("-")
        if endpoints[0] == endpoints[1]:
            raise ParserError(
                "The connection should not connect to itself: "
                f"'{endpoints[0]}-{endpoints[1]}'"
            )
        if len(endpoints) != 2 or not endpoints[0] or not endpoints[1]:
            raise ParserError(
                f"Invalid connection format in: '{key}: {value}'"
            )

        if len(brute_data) != 2:
            return endpoints, {}

        brute_metadata = brute_data[1].strip().split("]")

        if not brute_metadata[1]:
            brute_metadata = [brute_metadata[0]]

        if (len(brute_metadata) > 1
                and not brute_metadata[1].strip().startswith("#")):
            raise ParserError(
                f"Many arguments in line in: '{key}: {value}'"
            )

        meta_data: dict[str, int] = {}
        for item in brute_metadata[0].split():
            key_name, value_name = item.split("=", 1)
            meta_data[key_name] = int(value_name)

        if len(meta_data) > 1:
            raise ParserError("Many Arguments in metadata!")

        for mkey in meta_data:
            if mkey not in key_names:
                raise ParserError(f"'{mkey}' is not valid keys name")

        return endpoints, meta_data


class Creator:
    @staticmethod
    def create_hubs(data: list[str], meta_data: dict[str, str]) -> Hub:
        '''
            Cria o objeto Hub a partir dos dados validados e adiciona
            os metadados, se existir, e se o hub é start ou end.
        '''
        try:
            x_value = int(data[1])
            y_value = int(data[2])
            hub = Hub(
                name=data[0],
                x=x_value,
                y=y_value,
            )
            if meta_data:
                hub.set_metadata(meta_data)
        except ValidationError as e:
            print(f"In hub_list: {e.errors()[0]['msg']}")
            exit(1)
        # verifica se todos os hubs têm start e end definidos. Se nao, define
        hub.set_start_end()
        return hub

    @staticmethod
    def create_connections(
                           endpoints: list[str],
                           meta_data: dict[str, int],
                           possible_hubs_name: list[str]
                           ) -> Connection:
        '''
            Cria a conexão a partir dos endpoints validados e existentes na
            lista de hubs e adiciona os metadados, se existir.
        '''

        try:
            if len(endpoints) < 2:
                raise ValueError("Not enough endpoints for a connection.")

            if possible_hubs_name is None or len(possible_hubs_name) == 0:
                raise ValueError("No hubs available to connect.")

            if (endpoints[0] in possible_hubs_name and
               endpoints[1] in possible_hubs_name):
                connection = Connection(
                    start_point=endpoints[0],
                    end_point=endpoints[1],
                )
            else:
                raise ParserError(f"The endpoint {endpoints[0]} or \
{endpoints[1]} does not exist in \
the list of hubs.")

            if meta_data and connection is not None:
                connection.set_metadata(meta_data)

        except ValidationError as e:
            print(f"In connect_list: {e.errors()[0]['msg']}")
            exit(1)
        return connection
