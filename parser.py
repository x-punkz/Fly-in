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
        if self.start_hub is True and self.end_hub is True:
            print("primeiro if")
            raise ValueError("entrada e saida sao iguais")
        return self

    def set_metadata(self, metadata: dict[str]) -> None:
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


class Drone(BaseModel):
    name: str = Field(...)


class Map(BaseModel):
    nb_drones: int = Field(ge=1)
