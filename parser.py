from pydantic import Field, BaseModel, model_validator


class ParserError(Exception):
    pass


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

    def hub_validate(key: str, value: str) -> tuple:
        key_names = ["zone", "color", "max_drones"]
        possible_zones = ["normal", "blocked", "restricted", "priority"]
        brute_data = value.strip()
        brute_data = brute_data.replace("]", "").split("[")
        data = brute_data[0].strip().split()
        value = data

        if len(brute_data) != 2:
            meta = None
            pass
        else:
            meta = {k: v
                    for k, v in (
                        item.split("=")
                        for item in brute_data[1].split()
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

class Drone(BaseModel):
    name: str = Field(...)


class Map(BaseModel):
    nb_drones: int = Field(ge=1)
