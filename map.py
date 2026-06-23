from pydantic import Field, BaseModel, model_validator
from PIL import Image
from collections import deque
import pygame


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
            "blue": (30, 144, 255),
            "brown": (165, 42, 42),
            "crimson": (220, 20, 60),
            "darkred": (139, 0, 0),
            "gold": (255, 215, 0),
            "green": (0, 255, 0),
            "lime": (191, 255, 0),
            "magenta": (255, 0, 255),
            "maroon": (128, 0, 0),
            "rainbow": (106, 90, 205),
            "orange": (255, 128, 0),
            "purple": (128, 0, 128),
            "red": (255, 0, 0),
            "violet": (143, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255)
        }
        if self.name == "start":
            base = Image.open("images/hubs/start_base.png").convert("RGBA")
            mask = Image.open("images/hubs/start_mask.png").convert("L")

        elif self.name == "goal":
            base = Image.open("images/hubs/end_base.png").convert("RGBA")
            mask = Image.open("images/hubs/end_mask.png").convert("L")

        elif self.name == "impossible_goal":
            base = Image.open("images/hubs/rainbow_hub.png").convert("RGBA")
            mask = Image.open("images/hubs/rb_hub.png").convert("L")

        else:
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
            "restricted": "images/hubs/restricted",
            "priority": "images/hubs/priority",
            "blocked": "images/hubs/blocked",
            "normal": "images/hubs/normal",
            "start": "images/hubs/start",
            "goal": "images/hubs/goal"
        }

        if "color" in metadata:
            self.color = metadata["color"]

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
    screen_x: float = 0
    screen_y: float = 0
    target_hub: Hub | None = None
    path: list[str] = []
    path_index: int = 0
    start_delay: int = 0
    active: bool = False


class Map():
    def __init__(self,
                 list_hub: list[Hub],
                 list_conex: list[Connection],
                 nb_drone: int):

        self.list_hub = list_hub
        self.list_conex = list_conex
        self.nb_drone = nb_drone
        self.list_drone = self.create_drone()
        # print("Rota encontrada:", self.find_path())

        for hub in self.list_hub:
            hub.mount_image_hub()

    def create_graph(self) -> list[str]:
        graph = {}

        for conn in self.list_conex:
            start = conn.start_point
            end = conn.end_point

            if start not in graph:
                graph[start] = []

            if end not in graph:
                graph[end] = []

            graph[start].append(end)
            graph[end].append(start)
        return graph

    def get_hub_by_name(self, name) -> Hub | None:
        for hub in self.list_hub:
            if hub.name == name:
                return hub
        return None

    def find_path(self) -> list[str]:
        graph = self.create_graph()

        queue = deque()
        queue.append(("start", ["start"]))

        visited = []

        while queue:
            # popleft remove e devolve o primeiro elemento da fila
            current, path = queue.popleft()
            if current == "goal":
                return path

            if current not in visited:
                visited.append(current)
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        new_path = path + [neighbor]
                        queue.append((neighbor, new_path))
        return []

    def create_drone(self) -> list[Drone]:
        drone_list: list[Drone] = []
        start_hub = self.get_hub_by_name("start")
        route = self.find_path()

        for i in range(self.nb_drone):
            drone = Drone(
                name=f"drone{i}",
                current_hub=start_hub,
                path_index=0,
                path=route,
                start_delay=i * 2,  # cada drone espera 2 movimentos
                active=(i == 0)
            )
            drone_list.append(drone)

        return drone_list

    def move_drone(self):
        for drone in self.list_drone:
            if not drone.active:
                drone.start_delay -= 1
                if drone.start_delay <= 0:
                    drone.active = True
                continue

            if drone.path_index >= len(drone.path) - 1:
                continue

            drone.path_index += 1
            next_hub_name = drone.path[drone.path_index]
            next_hub = self.get_hub_by_name(next_hub_name)
            # aqui ele nao muda de hub direto
            # so define p onde quer ir
            drone.target_hub = next_hub
