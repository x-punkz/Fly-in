from pydantic import Field, BaseModel, model_validator
from PIL import Image
from collections import deque


class Hub(BaseModel):
    name: str = Field(...)
    x: int = Field(...)
    y: int = Field(...)
    color: str = Field(default="blue")
    model: str = Field(default="images/hubs/normal")
    drones_in_hub: int = Field(default=0, ge=0)
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
            try:
                self.max_drones = int(metadata["max_drones"])

            except ValueError:
                raise ValueError(
                    f"'{metadata['max_drones']}' "
                    "is not a valid max_drones value"
                )

        if "zone" in metadata:
            self.zone = metadata["zone"]
            self.model = models[self.zone]

    def set_start_end(self) -> None:
        '''
            Seta o hub como 'start' ou como 'end' se o 'name'
        '''
        if self.name == "start":
            self.start_hub = True
        elif "goal" in self.name:
            self.end_hub = True


class Connection(BaseModel):
    start_point: str = Field(...)
    end_point: str = Field(...)
    max_link_capacity: int = Field(default=1, ge=1)
    drones_on_link: list[str] = []

    def set_metadata(self, metadata: dict[str]) -> None:
        if "max_link_capacity" in metadata:
            self.max_link_capacity = int(metadata["max_link_capacity"])


class Drone(BaseModel):
    name: str = Field(...)
    current_hub: Hub = Field(...)
    screen_x: float = 0
    screen_y: float = 0
    target_hub: Hub | None = None
    path: list[str] = []
    path_index: int = 0
    active: bool = False
    current_connection: str | None = None
    waiting_turns: int = 0
    moving: bool = False


class Map():
    def __init__(self,
                 list_hub: list[Hub],
                 list_conex: list[Connection],
                 nb_drone: int):

        self.list_hub = list_hub
        self.list_conex = list_conex
        self.nb_drone = nb_drone
        self.reverse = False
        for hub in list_hub:
            if hub.end_hub:
                hub.max_drones = nb_drone
        self.list_drone = self.create_drone()
        # print("Rota encontrada:", self.find_path_w_bfs())

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

    def drones_in_hub(self, hub_name: str) -> int:
        count = 0

        for drone in self.list_drone:
            if drone.current_hub and drone.current_hub.name == hub_name:
                count += 1

        return count

    def find_path_w_dijkstra(self) -> list[str]:
        pass

    def find_path_w_bfs(self) -> list[str]:
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
        start_hub.drones_in_hub = self.nb_drone
        route = self.find_path_w_bfs()

        for i in range(self.nb_drone):
            drone = Drone(
                name=f"drone{i}",
                current_hub=start_hub,
                path_index=0,
                path=route,
                active=False
            )
            drone_list.append(drone)

        return drone_list

    def get_connection(self, start, end) -> Connection | None:
        for conn in self.list_conex:
            if (
                (conn.start_point == start and conn.end_point == end)
                or
                (conn.start_point == end and conn.end_point == start)
            ):
                return conn
        return None

    def release_start_drones(self) -> None:
        if (
            not self.list_drone
            or len(self.list_drone[0].path) < 2
        ):
            return

        first_conn = self.get_connection(
            self.list_drone[0].path[0],
            self.list_drone[0].path[1]
        )

        next_hub = self.get_hub_by_name(
            self.list_drone[0].path[1]
        )

        free_link = (
            first_conn.max_link_capacity
            - len(first_conn.drones_on_link)
        )

        free_hub = (
            next_hub.max_drones
            - next_hub.drones_in_hub
        )

        free_slots = max(0, min(free_link, free_hub))

        waiting = [
            drone for drone in self.list_drone
            if (
                not drone.active
                and drone.current_hub.name == drone.path[0]
            )
        ]

        for drone in waiting[:free_slots]:
            drone.active = True
            first_conn.drones_on_link.append(drone.name)

    def move_drone(self) -> None:
        self.release_start_drones()
        for drone in self.list_drone:
            if drone.moving or drone.target_hub is not None:
                continue

            if drone.waiting_turns > 0:
                drone.waiting_turns -= 1
                continue

            if not drone.active:
                continue

            if drone.path_index >= len(drone.path) - 1:
                continue

            current_name = drone.path[drone.path_index]
            next_name = drone.path[drone.path_index + 1]

            next_connection = self.get_connection(
                current_name,
                next_name
            )
            if next_connection is None:
                continue

            next_hub = self.get_hub_by_name(next_name)

            if next_hub.zone == "blocked":
                continue

            if next_hub.drones_in_hub >= next_hub.max_drones:
                continue

            if drone.name not in next_connection.drones_on_link:

                if (
                    len(next_connection.drones_on_link)
                    >= next_connection.max_link_capacity
                ):
                    continue

                if drone.current_connection:
                    for conn in self.list_conex:
                        if drone.name in conn.drones_on_link:
                            conn.drones_on_link.remove(drone.name)
                            break
                next_connection.drones_on_link.append(drone.name)

                drone.current_connection = (
                    f"{next_connection.start_point}"
                    f"-{next_connection.end_point}"
                )

            drone.current_hub.drones_in_hub -= 1
            drone.target_hub = next_hub
            # drone.current_hub = None
            drone.moving = True

        self.release_start_drones()
