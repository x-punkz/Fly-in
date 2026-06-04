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


class Drone(BaseModel):
    name: str = Field(...)


class Map(BaseModel):
    nb_drones: int = Field(ge=1)
