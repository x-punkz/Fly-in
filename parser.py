from pydantic import Field, BaseModel, model_validator


class Hub(BaseModel):
    name: str = Field(...)
    x: int
    y: int = Field(...)
    color: str
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


class Drone(BaseModel):
    name: str
    nb_drones: int
