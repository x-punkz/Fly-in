from pydantic import Field, BaseModel, model_validator
from PIL import Image


class Hub(BaseModel):
    name: str = Field(...)
    x: int = Field(...)
    y: int = Field(...)
    color: str = Field(default="blue")
    model: str = Field(default="images/hubs/normal")
    max_drones: int = Field(default=1, ge=1)
    zone: str = Field(default="normal")
    start_hub: bool = Field(default=False)
    end_hub: bool = Field(default=False)
    image_cache: dict = {}

    @model_validator(mode="after")
    def _(self) -> 'Hub':
        '''
        Valida se o hub start e end estao no mesmo lugar.
        '''

        if self.start_hub is True and self.end_hub is True:
            raise ValueError("entrada e saida sao iguais")
        return self

    def mount_image_hub(self) -> Image.Image:

        cache_key = (self.model, self.color)

        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

        palette = {
            "black": (0, 0, 0),
            "blue": (0, 128, 255),
            "brown": (165, 42, 42),
            "crimson": (220, 20, 60),
            "darkred": (139, 0, 0),
            "gold": (255, 215, 0),
            "green": (0, 255, 0),
            "lime": (191, 255, 0),
            "magenta": (255, 0, 255),
            "maroon": (128, 0, 0),
            "orange": (255, 128, 0),
            "purple": (128, 0, 128),
            "red": (255, 0, 0),
            "violet": (143, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255)
        }

        base = Image.open(f"{self.model}_base.png").convert("RGBA")
        mask = Image.open(f"{self.model}_mask.png").convert("L")

        color = palette[self.color]

        overlay = Image.new("RGBA", base.size, color + (255,))

        result = Image.composite(overlay, base, mask)

        self.image_cache[cache_key] = result

        return result

    def set_metadata(self, metadata: dict[str]) -> None:
        '''
        Seta os metadados do hub.
        '''

        models = {
            "restricted": "images/hubs/restrict",
            "priority": "images/hubs/priority",
            "blocked": "images/hubs/blocked",
            "normal": "images/hubs/normal",
            "start": "images/hubs/start",
            "goal": "images/hubs/goal"
        }

        if "color" in metadata:
            if metadata["color"] == "rainbow":
                 return Image.open("images/hubs/rainbow_hub.png"
                                   ).convert("RGBA")
                # self.color = metadata["color"]
                # # self.model = "images/hubs/rainbow_hub.png"
            else:
                self.color = metadata["color"]
                # self.model = f"images/hubs/{self.model}"

        if "max_drones" in metadata:
            self.max_drones = metadata["max_drones"]

        if "zone" in metadata:
            self.zone = metadata["zone"]
            self.model = models[self.zone]

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
    image: str = "images/drone/drone.png"


class Map():
    def __init__(self,
                 list_hub: list[Hub],
                 list_conex: list[Connection],
                 nb_drone: int):

        self.list_hub = list_hub
        self.list_conex = list_conex
        self.nb_drone = nb_drone
        self.list_drone = self.create_drone()

        for hub in self.list_hub:
            hub.mount_image_hub()

    def create_drone(self) -> list[Drone]:
        drone_list: list[Drone] = []
        # Conferir este list hub no current_hub, pq tem q ser start_hub
        for i in range(self.nb_drone):
            drone_list.append(Drone(name=f"drone{i}", current_hub=self.list_hub[0]))

        return drone_list


class App:
    pass
