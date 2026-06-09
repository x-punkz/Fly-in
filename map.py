from pydantic import Field, BaseModel, model_validator


class Hub(BaseModel):
    name: str = Field(...)
    x: int = Field(...)
    y: int = Field(...)
    color: str = Field(default="blue")
    max_drones: int = Field(default=1, ge=1)
    zone: str = Field(default="normal")
    start_hub: bool = Field(default=False)
    end_hub: bool = Field(default=False)

    @model_validator(mode="after")
    def _(self) -> 'Hub':
        '''
        Valida se o hub start e end estao no mesmo lugar.
        '''

        if self.start_hub is True and self.end_hub is True:
            raise ValueError("entrada e saida sao iguais")
        return self

    def set_metadata(self, metadata: dict[str]) -> None:
        '''
        Seta os metadados do hub.
        '''

        if "color" in metadata:
            self.color = metadata["color"]
        if "max_drones" in metadata:
            self.max_drones = metadata["max_drones"]
        if "zone" in metadata:
            self.zone = metadata["zone"]

    def set_start_end(self) -> None:
        '''
            Seta o hub como 'start' ou como 'end' se o 'name'
        '''

        if self.name == "start":
            self.start_hub = True
        elif self.name == "goal":
            self.end_hub = True


class Connection(BaseModel):
    start_point: str = Field(...)
    end_point: str = Field(...)
    max_link_capacity: int = Field(default=1, ge=1)

    def set_metadata(self, metadata: dict[str]) -> None:
        if "max_link_capacity" in metadata:
            self.max_link_capacity = metadata["max_link_capacity"]


class Drone(BaseModel):
    name: str = Field(...)
    current_hub: Hub = Field(...)


class Map():
    def __init__(self,
                 list_hub: list[Hub],
                 list_conex: list[Connection],
                 nb_drone: int):

        self.list_hub = list_hub
        self.list_conex = list_conex
        self.nb_drone = nb_drone
        self.list_drone = self.create_drone()

    def create_drone(self) -> list[Drone]:
        drone_list: list[Drone] = []
        for hub in self.list_hub:
            if hub.name == "start":
                start_hub = hub
        for i in range(self.nb_drone):
            drone_list.append(Drone(name=f"drone{i}", current_hub=start_hub))

        return drone_list


class App:
    pass
