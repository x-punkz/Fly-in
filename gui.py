
from validate import Parser
from map import Map, Hub
from sys import argv, exc_info
import pygame


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Fly_in")
        icon = pygame.image.load("images/icon.png")
        pygame.display.set_icon(icon)
        # escolher a imagem e por o caminho aqui
        self.bg = pygame.image.load("images/map/iso.png")
        # pygame.mixer.music.load() #  da p por musica
        self.drone_img = pygame.image.load("images/drone/drone.png")
        screen_info: pygame.display._VidInfo = pygame.display.Info()
        self.width: int = int(screen_info.current_w)
        self.height: int = int(1016)

        # self.width, self.height = 1744, 768
        self.window = pygame.display.set_mode((self.width, self.height),
                                              pygame.RESIZABLE)
        self.virtual_window = pygame.Surface((self.width, self.height))
        self.game = pygame.Surface((self.width * 3/4, self.height))
        self.menu = pygame.Surface((self.width * 1/4, self.height))
        game_color = (255, 255, 255)
        self.menu.fill(game_color)

        self.start_button = pygame.Rect(40, 180, 180, 50)
        self.stop_button = pygame.Rect(250, 180, 180, 50)
        self.reverse_button = pygame.Rect(40, 250, 180, 50)
        self.reset_button = pygame.Rect(250, 250, 180, 50)

    @staticmethod
    def coordenadas_giradas(x: float,
                            y: float,
                            unidade: float = 1) -> tuple[float, float]:
        """
        Converte coordenadas cartesianas (x, y) para um sistema isométrico
        rotacionado.
        Fórmula: X = unidade * (x - y), Y = unidade * (x + y)
        Retorna tupla (X, Y) em ponto flutuante.
        """
        X = unidade * (x*2 - y)
        Y = unidade * (x + y*2)
        return X, Y

    @staticmethod
    def parse_file() -> Map:
        if len(argv) < 2:
            print("   Passe o arquivo de configuraçao!")
            exit(1)
        try:
            with open(argv[1]) as file:
                config_file = file.read()
                config_dict = Parser(config_file)
                hubs, connections, nb_drone = config_dict.parse()
        except (Exception) as e:
            # PRECISO VER O ERRO DE VALIDATOR E DE EXCEPTION
            #     # if Exception:
            print(e)
            exit(1)

        return Map(list_hub=hubs, list_conex=connections, nb_drone=nb_drone)

    def calc_screen_positions(self,
                              mapper: Map) -> tuple[dict[str, tuple], int]:
        '''
            Calcula as posicoes das coordenadas p printar na tela
            Agora aplicando uma transformação isométrica (coordenadas giradas)
            antes de calcular a escala e posicionamento na tela.
        '''

        game_w = int(self.game.get_width())
        game_h = int(self.game.get_height())

        # Cria um dicionário com as coordenadas rotacionadas (isométricas)
        rotated_coords: dict[str, tuple[float, float]] = {
            hub.name: self.coordenadas_giradas(float(hub.x),
                                               float(hub.y),
                                               unidade=1)
            for hub in mapper.list_hub
        }
        # dica do gepeto pro caminho ocupar 75% da cidade
        start_x, start_y = rotated_coords["start"]
        if "impossible_goal" in rotated_coords:
            goal_x, goal_y = rotated_coords["impossible_goal"]
        else:
            goal_x, goal_y = rotated_coords["goal"]

        route_width = max(1, abs(goal_x - start_x))
        scale = (game_w * 0.75) / route_width

        # limitador vertical tbm
        ys = [coord[1] for coord in rotated_coords.values()]
        route_height = max(ys) - min(ys)

        scale_height = (game_h * 0.70) / max(1, route_height)

        scale = min(scale, scale_height)

        # tentando aumentar a altura p mapas largos
        ratio = route_width / max(1, route_height)
        vertical_factor = 1.0
        if ratio > 1.8:
            vertical_factor = 1.35

        def to_screen(rot_x: float, rot_y: float) -> tuple[int, int]:

            # por o centro do mapa de hubs onde eu quiser
            center_y = game_h * 0.90

            # empurra horizontalmente o mapa de hubs
            sx = (rot_x - start_x) * scale + game_w * 0.20

            sy = center_y - (rot_y - start_y) * scale * vertical_factor
            # sy = center_y - (rot_y - start_y) * scale

            return int(sx), int(sy)

        positions = {}

        for name, (rot_x, rot_y) in rotated_coords.items():

            positions[name] = to_screen(rot_x, rot_y)
        # calcula posicoes na tela a partir das coordenadas rotacionadas
        # positions = {
        #     name: to_screen(*coord) for name, coord in rotated_coords.items()
        #     }

        return positions, scale

    def draw_drone(self, mapper: Map) -> None:
        '''
            desenha os drones na tela
        '''

        # positions, _ = self.calc_screen_positions(mapper)
        for i, drone in enumerate(mapper.list_drone):
            pos = (drone.screen_x, drone.screen_y)

            offset_x = i * 0
            offset_y = -i * 15
            img = pygame.transform.scale(self.drone_img, (100, 100))

            # self.game.blit(
            #     img,
            #     (
            #         pos[0] - img.get_width() // 2,
            #         pos[1] - img.get_height() // 2
            #     )
            #  usar quando usar offset
            self.game.blit(
                img,
                (
                    pos[0] - img.get_width() // 2 + offset_x,
                    pos[1] - img.get_height() // 2 + offset_y
                )
            )

    def animate_drones(self, mapper: Map) -> None:
        '''
            Anima os drones fazendo eles andarem alguns pixels por frame
        '''
        positions, _ = self.calc_screen_positions(mapper)
        speed = 5

        for drone in mapper.list_drone:
            if drone.target_hub is None:
                continue

            target_pos = positions[drone.target_hub.name]
            target_x = target_pos[0]
            target_y = target_pos[1]

            # dx,dy == distancia horiz e distancia vert
            dx = target_x - drone.screen_x
            dy = target_y - drone.screen_y

            if abs(dx) <= speed and abs(dy) <= speed:
                drone.screen_x = target_x
                drone.screen_y = target_y

                for conn in mapper.list_conex:
                    if drone.name in conn.drones_on_link:
                        conn.drones_on_link.remove(drone.name)
                        break

                drone.current_hub = drone.target_hub

                if drone.current_hub.zone in ("normal", "priority"):
                    drone.waiting_turns = 0
                elif drone.current_hub.zone == "restricted":
                    drone.waiting_turns = 1

                drone.current_hub = drone.target_hub
                drone.current_hub.drones_in_hub += 1
                drone.target_hub = None
                drone.path_index += 1
                drone.moving = False
            else:
                distance = (dx * dx + dy * dy) ** 0.5
                dir_x = dx / distance
                dir_y = dy / distance

                drone.screen_x += dir_x * speed
                drone.screen_y += dir_y * speed

    def draw_map(self, mapper: Map) -> None:
        '''
            Desenha o mapa completo
        '''
        positions, _ = self.calc_screen_positions(mapper)

        num_hubs = len(mapper.list_hub)

        # baseline = 200

        # tamanho dos predios, calc o tamanho e depois limita no maximo
        icon_size = int(1200 / (num_hubs ** 0.5))
        icon_size = max(100, min(icon_size, 220))

        # desenhar conexoes
        for conn in mapper.list_conex:

            start_p = positions.get(conn.start_point)
            end_p = positions.get(conn.end_point)
            if start_p and end_p:
                pygame.draw.line(self.game,
                                 (255, 0, 255),
                                 start_p, end_p, width=3)
                pygame.draw.line(self.game,
                                 (255, 255, 255),
                                 start_p, end_p, width=1)
        # Desenhar hubs (imagem centralizada ou circulo)
        for hub in mapper.list_hub:
            pos = positions[hub.name]
            pos_x = pos[0]
            pos_y = pos[1]
            try:
                pil_img = hub.mount_image_hub()
                mode = pil_img.mode
                size = pil_img.size
                data = pil_img.tobytes()

                img = pygame.image.frombytes(
                    data,
                    size,
                    mode
                )
                # Ajusta o tamanho
                img = pygame.transform.scale(img, (icon_size, icon_size))
                self.game.blit(img,  (pos_x - img.get_width()//2,
                                      pos_y - img.get_height()//2))
            except Exception as e:
                print("ERROR HUB:")
                print(e)

                pygame.draw.circle(
                    self.game,
                    (0, 120, 250),
                    pos, icon_size // 2)

    def draw_menu_border(self) -> None:

        pygame.draw.rect(
            self.menu,
            (255, 20, 147),      # cor da borda
            (10, 10,
                self.menu.get_width() - 20,
                self.menu.get_height() - 20),
            width=3,              # espessura da linha
            border_radius=12      # cantos arredondados
        )

        pygame.draw.rect(
            self.menu,
            (238, 130, 238),      # cor da borda
            (10, 10,
                self.menu.get_width() - 20,
                self.menu.get_height() - 20),
            width=2,              # espessura da linha
            border_radius=12      # cantos arredondados
        )

        pygame.draw.rect(
            self.menu,
            (0, 255, 255),      # cor da borda
            (20, 20,
                self.menu.get_width() - 40,
                self.menu.get_height() - 40),
            width=2,              # espessura da linha
            border_radius=12      # cantos arredondados
        )

    def draw_button_border(self, color: str, rect: pygame.rect) -> None:
        if color == "green":
            color = (0, 255, 0)
        elif color == "red":
            color = (255, 0, 0)
        elif color == "orange":
            color = (255, 140, 0)
        elif color == "blue":
            color = (123, 104, 238)

        pygame.draw.rect(
            self.menu,
            color,
            rect,
            width=4,
            border_radius=12
        )

        pygame.draw.rect(
            self.menu,
            (216, 191, 216),
            rect,
            width=2,
            border_radius=12
        )

    def draw_menu(self, mapper: Map, turn: int) -> None:
        '''
            Desenha o menu lateral
        '''
        # Desenha as informaçoes
        self.menu.fill((2, 2, 2))

        # Desenha a borda do menu
        self.draw_menu_border()

        font = pygame.font.SysFont("DejaVu Sans Bold", 32)
        end_hub = None
        for hub in mapper.list_hub:
            if hub.end_hub:
                end_hub = hub
                break

        infos = [
            f"Turns: {turn}",
            f"Drone: {mapper.nb_drone}",
            f"Goal: {mapper.drones_in_hub(end_hub.name)}"
            f" / {mapper.nb_drone}"]

        y = 40
        for info in infos:
            text = font.render(info, True, (0, 255, 255))
            self.menu.blit(text, (40, y))
            y += 40

        # Desenha os botoes
        font = pygame.font.SysFont("DejaVu Sans Bold", 32)
        # START
        pygame.draw.rect(
            self.menu,
            (0, 0, 0),
            self.start_button,
            border_radius=8
        )
        self.draw_button_border("green", self.start_button)
        text = font.render("START", True, (50, 205, 50))
        self.menu.blit(
            text,
            text.get_rect(center=self.start_button.center)
        )

        # STOP
        pygame.draw.rect(
            self.menu,
            (2, 2, 2),
            self.stop_button,
            border_radius=8
        )
        self.draw_button_border("red", self.stop_button)
        text = font.render("STOP", True, (220, 20, 60))
        self.menu.blit(
            text,
            text.get_rect(center=self.stop_button.center)
        )
        # REVERSE
        pygame.draw.rect(
            self.menu,
            (2, 2, 2),
            self.reverse_button,
            border_radius=8
        )
        self.draw_button_border("blue", self.reverse_button)
        text = font.render("REVERSE", True, (123, 104, 238))
        self.menu.blit(
            text,
            text.get_rect(center=self.reverse_button.center)
        )

        # RESET
        pygame.draw.rect(
            self.menu,
            (2, 2, 2),
            self.reset_button,
            border_radius=8
        )
        self.draw_button_border("orange", self.reset_button)
        text = font.render("RESET", True, (210, 105, 30))
        self.menu.blit(
            text,
            text.get_rect(center=self.reset_button.center)
        )

    def run(self) -> None:
        '''
            Roda o programa
        '''
        running: bool = True
        mapper = self.parse_file()
        # print(mapper._w_bfs()) p ver se o caminho ta certo.
        frame_count = 0
        font = pygame.font.SysFont("DejaVu Sans Bold", 30)
        turn = 0
        simulation_running = False

        end_hub: Hub = None
        for hub in mapper.list_hub:
            if hub.end_hub:
                end_hub = hub
                break

        # Fazer drone se mover animado
        positions, _ = self.calc_screen_positions(mapper)
        for drone in mapper. list_drone:
            start_pos = positions["start"]
            drone.screen_x = start_pos[0]
            drone.screen_y = start_pos[1]

        while running:

            frame_count += 1
            turn_text = font.render(
                f"TURNS: {turn}",
                True,
                (0, 255, 255)
                )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:

                    mouse = (
                        event.pos[0] - self.game.get_width(),
                        event.pos[1]
                    )

                    if self.start_button.collidepoint(mouse):
                        simulation_running = True

                    elif self.stop_button.collidepoint(mouse):
                        simulation_running = False
                        print("Stop")

                    elif self.reverse_button.collidepoint(mouse):
                        if (
                            mapper.drones_in_hub(end_hub.name)
                            != mapper.nb_drone
                        ):
                            # colocar p printar no menu
                            # error_msg = font.render(
                            #         "Aguarde os drones chegarem ao goal",
                            #         True,
                            #         (0, 255, 255)
                            #     )
                            # self.menu.blit(error_msg, (250, 190))
                            print("espera porra")

                        elif not mapper.reverse:
                            mapper.reverse = True
                            simulation_running = True

                            for drone in mapper.list_drone:
                                drone.path = drone.path[::-1]
                                drone.path_index = 0
                                drone.current_connection = None
                                drone.target_hub = None
                                drone.active = False
                                drone.moving = False

                            print("reverse")

                    elif self.reset_button.collidepoint(mouse):
                        simulation_running = False
                        turn = 0
                        frame_count = 0
                        mapper = self.parse_file()
                        positions, _ = self.calc_screen_positions(mapper)

                        for drone in mapper. list_drone:
                            start_pos = positions["start"]
                            drone.screen_x = start_pos[0]
                            drone.screen_y = start_pos[1]

                        print("Reset")

            if frame_count % 60 == 0:
                if simulation_running and frame_count % 60 == 0:

                    target = "start" if mapper.reverse else end_hub.name

                    if mapper.drones_in_hub(target) < mapper.nb_drone:
                        turn += 1
                        mapper.move_drone()

            self.animate_drones(mapper)

            self.game.blit(self.bg,  (0, 0))
            self.draw_map(mapper)
            self.draw_drone(mapper)
            self.draw_menu(mapper, turn)

            self.virtual_window.blit(self.game, (0, 0))
            self.virtual_window.blit(self.menu, (self.game.get_width(), 0))

            height = self.window.get_height()
            width = self.window.get_width()
            change_size = pygame.transform.scale(self.virtual_window,
                                                 (width, height))
            self.window.blit(change_size, (0, 0))
            self.window.blit(turn_text, (30, 20))
            # desenha bg, conexões e hubs em self.game

            pygame.display.flip()
        pygame.quit()


def main() -> None:
    try:
        tela = App()
        tela.run()
    except Exception as e:
        exc_type, exc_obj, exc_tb = exc_info()
        error_line = exc_tb.tb_lineno
        print(f"Erro in line {error_line}: {e}")


if __name__ == "__main__":
    main()
