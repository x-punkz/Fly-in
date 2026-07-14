from pydantic import Field, BaseModel, model_validator
from PIL import Image
from typing import ClassVar


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
    image_cache: ClassVar[dict[tuple[str, str], Image.Image]] = {}
    cost: int = Field(default=1, ge=1)

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

        elif self.name == "impossible_goal":
            base = Image.open("images/hubs/rainbow_hub.png").convert("RGBA")
            mask = Image.open("images/hubs/rb_hub.png").convert("L")

        elif "goal" in self.name:
            base = Image.open("images/hubs/end_base.png").convert("RGBA")
            mask = Image.open("images/hubs/end_mask.png").convert("L")

        else:
            base = Image.open(f"{self.model}_base.png").convert("RGBA")
            mask = Image.open(f"{self.model}_mask.png").convert("L")

        color = palette[self.color]

        overlay = Image.new("RGBA", base.size, color + (255,))

        result = Image.composite(overlay, base, mask)

        self.image_cache[cache_key] = result

        return result

    def set_metadata(self, metadata: dict[str, str]) -> None:
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
            if self.zone == "restricted":
                self.cost = 2
            # elif self.zone == "normal":
            #     self.cost = 2

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

    def set_metadata(self, metadata: dict[str, int]) -> None:
        if "max_link_capacity" in metadata:
            self.max_link_capacity = int(metadata["max_link_capacity"])


class Drone(BaseModel):
    name: str = Field(...)
    current_hub: Hub | None = Field(...)
    screen_x: float = 0
    screen_y: float = 0
    target_hub: Hub | None = None
    path: list[str] = []
    final_path: list[str] = []
    path_index: int = 0
    active: bool = False
    current_connection: str | None = None
    waiting_turns: int = 0
    moving: bool = False
    paused_on_link: bool = False
    link_pause_pending: bool = False
    waiting_at_midpoint: bool = False


class Map():
    def __init__(self,
                 list_hub: list[Hub],
                 list_conex: list[Connection],
                 nb_drone: int):

        self.list_hub: list[Hub] = list_hub
        self.list_conex: list[Connection] = list_conex
        self.nb_drone: int = nb_drone
        self.reverse: bool = False
        for hub in list_hub:
            if hub.end_hub:
                hub.max_drones = nb_drone
        self.list_drone = self.create_drone()
        # print("Rota encontrada:", self.find_path_w_bfs())

        for hub in self.list_hub:
            hub.mount_image_hub()

    def create_graph(self) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}

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

    def get_hub_by_name(self, name: str) -> Hub | None:
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

    def find_path_w_dijkstra(
            self,
            start: str
            ) -> list[str]:

        graph: dict[str, list[str]] = self.create_graph()

        # start = "start"
        goal = next(hub.name for hub in self.list_hub if hub.end_hub)

        distances: dict[str, float] = {node: float("inf") for node in graph}
        previous: dict[str, str | None] = {node: None for node in graph}

        distances[start] = 0
        unvisited = set(graph.keys())

        while unvisited:

            current: str | None = min(unvisited,
                                      key=lambda node: distances[node]
                                      )
            if current is None:
                break

            unvisited.remove(current)

            if distances[current] == float("inf"):
                break

            if current == goal:
                break

            for neighbor in graph[current]:
                if neighbor == "gate_hell2":
                    continue

                hub = self.get_hub_by_name(neighbor)

                if hub is None or hub.zone == "blocked":
                    continue

                penalty = hub.drones_in_hub

                conn = self.get_connection(current, neighbor)

                if conn is not None:
                    penalty += len(conn.drones_on_link)
                    if len(conn.drones_on_link) >= conn.max_link_capacity:
                        penalty += len(conn.drones_on_link)

                if hub.drones_in_hub >= hub.max_drones:
                    penalty += hub.drones_in_hub

                new_distance = distances[current] + (hub.cost * 2) + penalty

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current

        if distances[goal] == float("inf"):
            return []

        path: list[str] = []
        path_current: str | None = goal

        while path_current is not None:
            path.append(path_current)
            path_current = previous[path_current]

        path.reverse()
        return path

    def create_drone(self) -> list[Drone]:
        drone_list: list[Drone] = []
        start_hub = self.get_hub_by_name("start")
        if start_hub is None:
            raise ValueError("Missing start hub")

        start_hub.drones_in_hub = self.nb_drone
        route = self.find_path_w_dijkstra("start")

        for i in range(self.nb_drone):
            drone = Drone(
                name=f"drone{i}",
                current_hub=start_hub,
                path_index=0,
                path=route,
                final_path=["start"],
                active=False
            )
            drone_list.append(drone)

        return drone_list

    def get_connection(self, start: str, end: str) -> Connection | None:
        for conn in self.list_conex:
            if (
                (conn.start_point == start and conn.end_point == end)
                or
                (conn.start_point == end and conn.end_point == start)
            ):
                return conn
        return None

    def get_drone_by_name(self, name: str) -> Drone | None:
        for drone in self.list_drone:
            if drone.name == name:
                return drone
        return None

    def release_start_drones(self) -> None:
        if (
            not self.list_drone
            or len(self.list_drone[0].path) < 2
        ):
            return

        if not self.list_drone[0].path:
            self.list_drone[0].path = self.find_path_w_dijkstra("start")

        first_conn = self.get_connection(
            self.list_drone[0].path[0],
            self.list_drone[0].path[1]
        )

        next_hub = self.get_hub_by_name(
            self.list_drone[0].path[1]
        )

        if first_conn is None or next_hub is None:
            return

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
                and drone.current_hub is not None
                and drone.current_hub.name == drone.path[0]
            )
        ]

        for drone in waiting[:free_slots]:
            drone.active = True
            first_conn.drones_on_link.append(drone.name)

    def move_drone(self) -> None:

        drones: list[Drone] = []
        if self.reverse:
            drones = list(reversed(self.list_drone))
        else:
            drones = self.list_drone

        for drone in drones:
            if drone.moving:
                continue

            if drone.paused_on_link and drone.target_hub is not None:
                drone.paused_on_link = False
                drone.link_pause_pending = False
                drone.waiting_at_midpoint = False
                drone.moving = True
                continue

            if drone.target_hub is not None:
                continue

            if drone.waiting_turns > 0:
                drone.waiting_turns -= 1
                continue

            if not drone.active:
                drone.active = True
                # continue

            current_hub = drone.current_hub
            if current_hub is None:
                continue

            if self.reverse:
                if not drone.path or (
                    drone.path_index == 0
                    and drone.path
                    and drone.path[0] != current_hub.name
                ):
                    if drone.final_path:
                        drone.path = drone.final_path[::-1]
                    else:
                        drone.path = [current_hub.name]
                    drone.path_index = 0
            else:
                drone.path = self.find_path_w_dijkstra(
                    current_hub.name
                )
                drone.path_index = 0

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
            if next_hub is None:
                continue

            if next_hub.zone == "blocked":
                continue

            drones_coming = sum(
                1 for d in self.list_drone
                if d.target_hub == next_hub
            )

            if (
                next_hub.drones_in_hub + drones_coming
                >= next_hub.max_drones
            ):
                continue

            if drone.name not in next_connection.drones_on_link:
                has_midpoint_pause = False
                for name in next_connection.drones_on_link:
                    other_drone = self.get_drone_by_name(name)
                    if (
                        next_hub.zone == "restricted"
                        and next_hub.cost >= 2
                        and other_drone is not None
                        and other_drone.waiting_at_midpoint
                        and other_drone.target_hub == next_hub
                    ):
                        has_midpoint_pause = True
                        break

                if has_midpoint_pause:
                    continue

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

            current_hub.drones_in_hub -= 1
            drone.target_hub = next_hub
            drone.link_pause_pending = (
                next_hub.zone == "restricted" and next_hub.cost >= 2
            )
            drone.paused_on_link = False
            # drone.current_hub = None
            drone.moving = True

        self.release_start_drones()
