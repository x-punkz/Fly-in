
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
        self.font_name = "images/font/Michroma-Regular.ttf"

        self.start_button = pygame.Rect(60, 390, 350, 60)
        self.stop_button = pygame.Rect(60, 460, 350, 60)
        self.reverse_button = pygame.Rect(60, 530, 350, 60)
        self.reset_button = pygame.Rect(60, 600, 350, 60)

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

        points = [
            (20, 20),
            (250, 20),
            (300, 70),
            (390, 70),
            (440, 20),
            (self.menu.get_width() - 20, 20),
            (self.menu.get_width() - 20, self.menu.get_height() - 20),
            (20, self.menu.get_height() - 20)
        ]

        points2 = [
            (35, 140),
            (35, 980),
            (445, 980),
            (445, 40),

        ]

        pygame.draw.lines(
            self.menu,
            (0, 255, 255),
            True,
            points,
            3
        )

        pygame.draw.lines(
            self.menu,
            (0, 255, 255),
            False,
            points2,
            2,
        )

    def draw_button_border(self, name: str, rect: pygame.rect) -> None:
        if name == "start":
            name = "/images/buttons/start"
        elif name == "stop":
            name = "/images/buttons/stop"
        elif name == "reverse":
            name = "/imagens/buttons/reverse"
        elif name == "reset":
            name = "/images/buttons/reset"

        pygame.draw.rect(
            self.menu,
            (255, 0, 255),
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

        end_hub = None
        for hub in mapper.list_hub:
            if hub.end_hub:
                end_hub = hub
                break

        # Desenha a borda do menu
        self.draw_menu_border()

        title_font = pygame.font.Font(self.font_name, 32)

        # title
        pygame.draw.rect(
            self.menu,
            (255, 0, 255),
            (40, 40, 205, 60),
            width=3,
            border_top_left_radius=0,
            border_top_right_radius=0,
            border_bottom_left_radius=0,
            border_bottom_right_radius=20,
        )

        text1 = title_font.render("FLY_IN", False, (0, 255, 255))
        self.menu.blit(text1, (70, 45))
        self.menu.blit(text1, (69, 44))

        # STATUS
        font_title = pygame.font.Font(self.font_name, 20)
        font = pygame.font.Font(self.font_name, 18)

        text2 = font_title.render("STATUS", False, (0, 255, 255))
        self.menu.blit(text2, (60, 125))

        # Horizontal line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (60, 160),
            (400, 160),
            3
        )
        # Vertical line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (400, 145),
            (400, 160),
            3
        )

        self.menu.blit(font.render(
            f"TURNS                         {turn}",
            True,
            (0, 255, 255)),
            (60, 175))

        self.menu.blit(
            font.render(f"DRONES                     {mapper.nb_drone}",
                        True,
                        (0, 255, 255)), (60, 225)
        )
        self.menu.blit(
            font.render(
                "GOAL                        "
                f"{mapper.drones_in_hub(end_hub.name)}/{mapper.nb_drone}",
                True, (0, 255, 255)), (60, 280)
            )

        # CONTROLS
        text3 = font_title.render("CONTROLS", False, (0, 255, 255))
        self.menu.blit(text3, (60, 330))

        # Horizontal line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (60, 370),
            (400, 370),
            3
        )
        # Vertical line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (400, 355),
            (400, 370),
            3
        )

        # MESSAGE
        text4 = font_title.render("MESSAGES", False, (0, 255, 255))
        self.menu.blit(text4, (60, 690))

        # Horizontal line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (60, 725),
            (400, 725),
            3
        )

        # Vertical line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (400, 710),
            (400, 725),
            3
        )

        pygame.draw.rect(
            self.menu,
            (255, 0, 255),
            (65, 740, 335, 120),
            width=2,
            border_top_left_radius=15,
            border_top_right_radius=0,
            border_bottom_left_radius=0,
            border_bottom_right_radius=15,
        )

        # Desenha os botoes
        font = pygame.font.Font(self.font_name, 32)
        # START
        pygame.draw.rect(
            self.menu,
            (0, 0, 0),
            self.start_button,
            border_radius=8
        )
        self.draw_button_border("start", self.start_button)
        text = font.render("START", True, (0, 255, 255))
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
        self.draw_button_border("stop", self.stop_button)
        text = font.render("STOP", True, (0, 255, 255))
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
        self.draw_button_border("reverse", self.reverse_button)
        text = font.render("REVERSE", True, (0, 255, 255))
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
        self.draw_button_border("reset", self.reset_button)
        text = font.render("RESET", True, (0, 255, 255))
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
        frame_count = 0
        turn = 0
        simulation_running = False
        error_message = ""
        error_until = 0

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
                            error_message = [
                                "WAIT ALL DRONES",
                                "    REACH THE GOAL."
                                ]
                            error_until = pygame.time.get_ticks() + 2000

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

            # printar mensagem de erro
            if pygame.time.get_ticks() < error_until:
                error_font = pygame.font.SysFont(self.font_name, 23)
                y = 780

                for line in error_message:
                    text = error_font.render(
                        line,
                        True,
                        (220, 20, 60)
                    )
                    self.menu.blit(text, (150, y))
                    y += 28

            self.virtual_window.blit(self.game, (0, 0))
            self.virtual_window.blit(self.menu, (self.game.get_width(), 0))

            height = self.window.get_height()
            width = self.window.get_width()
            change_size = pygame.transform.scale(self.virtual_window,
                                                 (width, height))
            self.window.blit(change_size, (0, 0))
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
