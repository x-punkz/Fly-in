from validate import Parser
from map import Map, Hub
from sys import argv, exc_info
import pygame
from pygame import Surface as surf, Rect


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Fly_in")
        icon = pygame.image.load("images/icon.png")
        pygame.display.set_icon(icon)
        self.bg = pygame.image.load("images/map/iso.png")
        # Musica
        pygame.mixer.init()
        self.sound_on: bool = True
        pygame.mixer.music.load("songs/cyberpunk.mp3")
        pygame.mixer.music.play(-1)
        self.sound_icon_size: tuple[int, int] = (180, 200)
        self.play: surf = pygame.image.load("songs/music.png")
        self.play: surf = pygame.transform.scale(self.play,
                                                 self.sound_icon_size)
        self.mute: surf = pygame.image.load("songs/mute.png")
        self.mute: surf = pygame.transform.scale(self.mute,
                                                 self.sound_icon_size)
        self.sound_pos: tuple[int, int] = (
            60 + (275 - self.sound_icon_size[0]) // 2,
            740 + 120 - 20
        )
        self.sound_rect: Rect = self.play.get_rect(topleft=self.sound_pos)
        self.drone_img: surf = pygame.image.load("images/drone/drone.png")
        # botoes
        self.start_img: surf = pygame.image.load("images/button/start.png")
        self.stop_img: surf = pygame.image.load("images/button/stop.png")
        self.reverse_img: surf = pygame.image.load("images/button/reverse.png")
        self.reset_img: surf = pygame.image.load("images/button/reset.png")
        self.turn_button: surf = pygame.image.load("images/button/turns.png")
        self.drone_button: surf = pygame.image.load("images/button/drone.png")
        self.goal_button: surf = pygame.image.load("images/button/goal.png")

        screen_info: pygame.display._VidInfo = pygame.display.Info()
        self.base_width: int = 1600
        self.base_height: int = 1016
        self.width: int = 1600
        self.height: int = 1016
        if screen_info.current_w > 0 and screen_info.current_h > 0:
            self.width = min(self.width, max(960, int(screen_info.current_w)))
            self.height = min(self.height, max(720,
                                               int(screen_info.current_h)
                                               ))

        self.window = pygame.display.set_mode((self.width, self.height),
                                              pygame.RESIZABLE)
        self.virtual_window = pygame.Surface((self.base_width,
                                              self.base_height),
                                             pygame.SRCALPHA)
        self.game = pygame.Surface((int(self.base_width * 3 / 4),
                                    self.base_height),
                                   pygame.SRCALPHA)
        self.menu = pygame.Surface((int(self.base_width * 1 / 4),
                                    self.base_height),
                                   pygame.SRCALPHA)
        game_color = (255, 255, 255)
        self.menu.fill(game_color)
        self.font_name = "images/font/Michroma-Regular.ttf"

        self.start_button = Rect(60, 390, 285, 60)
        self.stop_button = Rect(60, 460, 285, 60)
        self.reverse_button = Rect(60, 530, 285, 60)
        self.reset_button = Rect(60, 600, 285, 60)

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
            print(e)
            exit(1)

        return Map(list_hub=hubs, list_conex=connections, nb_drone=nb_drone)

    def calc_screen_positions(self,
                              mapper: Map) -> tuple[dict[str,
                                                         tuple[int, int]
                                                         ], float]:
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

        return positions, scale

    def get_window_scale(self) -> tuple[float, float, int, int]:
        window_w, window_h = self.window.get_size()
        if window_w <= 0 or window_h <= 0:
            return 1.0, 1.0, 0, 0

        scale_x = window_w / self.base_width
        scale_y = window_h / self.base_height
        if scale_x <= 0 or scale_y <= 0:
            return 1.0, 1.0, 0, 0

        return scale_x, scale_y, 0, 0

    def render_to_window(self) -> None:
        scale_x, scale_y, _, _ = self.get_window_scale()
        if scale_x <= 0 or scale_y <= 0:
            return

        scaled_surface = pygame.transform.smoothscale(
            self.virtual_window,
            (int(self.base_width * scale_x), int(self.base_height * scale_y))
        )

        self.window.fill((0, 0, 0))
        self.window.blit(scaled_surface, (0, 0))

    def to_virtual_coordinates(
            self,
            pos: tuple[int, int]
            ) -> tuple[float, float]:
        scale_x, scale_y, _, _ = self.get_window_scale()
        if scale_x <= 0 or scale_y <= 0:
            return pos[0], pos[1]

        virtual_x = pos[0] / scale_x
        virtual_y = pos[1] / scale_y
        return virtual_x, virtual_y

    def draw_drone(self, mapper: Map) -> None:
        '''
            desenha os drones na tela
        '''

        stack_count: dict[str, int] = {}

        for drone in mapper.list_drone:
            current_hub = drone.current_hub
            hub_name = current_hub.name if current_hub is not None else ""
            stack_index = stack_count.get(hub_name, 0)
            stack_count[hub_name] = stack_index + 1

            pos = (drone.screen_x, drone.screen_y)

            offset_x = 0
            offset_y = -stack_index * 15
            img = pygame.transform.scale(self.drone_img, (100, 100))

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
        move_speed = 8

        for drone in mapper.list_drone:
            current_hub = drone.current_hub
            target_hub = drone.target_hub
            if current_hub is None or target_hub is None:
                continue

            if drone.paused_on_link:
                continue

            target_pos: tuple[float, float] = positions[target_hub.name]
            if drone.link_pause_pending:
                start_pos = positions[current_hub.name]
                target_pos = (
                    (start_pos[0] + target_pos[0]) / 2,
                    (start_pos[1] + target_pos[1]) / 2,
                )
            target_x = target_pos[0]
            target_y = target_pos[1]

            # dx,dy == distancia horiz e distancia vert
            dx = target_x - drone.screen_x
            dy = target_y - drone.screen_y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= move_speed:
                drone.screen_x = target_x
                drone.screen_y = target_y

                if drone.link_pause_pending:
                    drone.link_pause_pending = False
                    drone.paused_on_link = True
                    drone.waiting_at_midpoint = True
                    drone.moving = False
                    continue

                for conn in mapper.list_conex:
                    if drone.name in conn.drones_on_link:
                        conn.drones_on_link.remove(drone.name)
                        break

                drone.current_hub = target_hub
                drone.waiting_at_midpoint = False

                # mudança estranha
                if not mapper.reverse:
                    drone.final_path.append(drone.current_hub.name)

                drone.current_hub.drones_in_hub += 1

                if drone.current_hub.zone in ("normal", "priority"):
                    drone.waiting_turns = 0
                elif drone.current_hub.zone == "restricted":
                    drone.waiting_turns = 0

                drone.target_hub = None
                drone.path_index += 1
                drone.moving = False
            else:
                dir_x = dx / distance
                dir_y = dy / distance

                drone.screen_x += dir_x * move_speed
                drone.screen_y += dir_y * move_speed

    def draw_map(self, mapper: Map) -> None:
        '''
            Desenha o mapa completo
        '''
        positions, _ = self.calc_screen_positions(mapper)

        num_hubs = len(mapper.list_hub)

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
                size = pil_img.size
                data = pil_img.tobytes()

                img = pygame.image.frombytes(
                    data,
                    size,
                    "RGBA"
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
            (285, 60),
            (350, 60),
            (380, 20),
            (self.menu.get_width() - 20, 20),
            (self.menu.get_width() - 20, self.menu.get_height() - 20),
            (20, self.menu.get_height() - 20)
        ]

        points2 = [
            (35, 140),
            (35, 980),
            (365, 980),
            (365, 70),

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

    def draw_button_border(self, name: str, rect: Rect) -> None:
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

        end_hub: Hub | None = None
        for hub in mapper.list_hub:
            if hub.end_hub:
                end_hub = hub
                break

        if end_hub is None:
            return

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
            (340, 160),
            3
        )
        # Vertical line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (340, 145),
            (340, 160),
            3
        )
        # logo turns
        self.menu.blit(self.turn_button, (60, 175))

        turns_text = font.render(
            f"TURNS                         {turn}",
            True,
            (0, 255, 255),
        )
        self.menu.blit(turns_text, (105, 175))

        # logo drone
        self.menu.blit(self.drone_button, (60, 225))
        drones_text = font.render(
            f"DRONES                     {mapper.nb_drone}",
            True,
            (0, 255, 255),
        )
        self.menu.blit(drones_text, (105, 225))

        # logo goal
        self.menu.blit(self.goal_button, (60, 280))
        goal_text = font.render(
            "GOAL                        "
            f"{mapper.drones_in_hub(end_hub.name)}/{mapper.nb_drone}",
            True,
            (0, 255, 255),
        )
        self.menu.blit(goal_text, (105, 280))

        # CONTROLS
        text3 = font_title.render("CONTROLS", False, (0, 255, 255))
        self.menu.blit(text3, (60, 330))

        # Horizontal line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (60, 370),
            (340, 370),
            3
        )
        # Vertical line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (340, 355),
            (340, 370),
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
            (340, 725),
            3
        )

        # Vertical line
        pygame.draw.line(
            self.menu,
            (255, 0, 255),
            (340, 710),
            (340, 725),
            3
        )

        pygame.draw.rect(
            self.menu,
            (255, 0, 255),
            (65, 740, 275, 120),
            width=2,
            border_top_left_radius=15,
            border_top_right_radius=0,
            border_bottom_left_radius=0,
            border_bottom_right_radius=15,
        )

        # Desenha os botoes
        font = pygame.font.Font(self.font_name, 32)
        padding = 18
        # START
        pygame.draw.rect(
            self.menu,
            (0, 0, 0),
            self.start_button,
            border_radius=8
        )
        self.draw_button_border("start", self.start_button)
        img_rect1 = self.start_img.get_rect(left=self.start_button.left
                                            + padding)
        img_rect1.centery = self.start_button.centery
        self.menu.blit(self.start_img, img_rect1)

        # STOP
        pygame.draw.rect(
            self.menu,
            (2, 2, 2),
            self.stop_button,
            border_radius=8
        )
        self.draw_button_border("stop", self.stop_button)
        img_rect2 = self.stop_img.get_rect(left=self.stop_button.left
                                           + padding)
        img_rect2.centery = self.stop_button.centery
        self.menu.blit(self.stop_img, img_rect2)

        # REVERSE
        pygame.draw.rect(
            self.menu,
            (2, 2, 2),
            self.reverse_button,
            border_radius=8
        )
        self.draw_button_border("reverse", self.reverse_button)
        img_rect3 = self.reverse_img.get_rect(left=self.reverse_button.left
                                              + padding)
        img_rect3.centery = self.reverse_button.centery
        self.menu.blit(self.reverse_img, img_rect3)

        # RESET
        pygame.draw.rect(
            self.menu,
            (2, 2, 2),
            self.reset_button,
            border_radius=8
        )
        self.draw_button_border("reset", self.reset_button)
        img_rect4 = self.reset_img.get_rect(left=self.reset_button.left
                                            + padding)
        img_rect4.centery = self.reset_button.centery
        self.menu.blit(self.reset_img, img_rect4)

        # SOUND
        sound_bg_rect = self.play.get_rect(topleft=self.sound_pos)

        if self.sound_on:
            self.menu.blit(self.play, self.sound_pos)
        else:
            self.menu.blit(self.mute, self.sound_pos)
        self.sound_rect = sound_bg_rect

    def run(self) -> None:
        '''
            Roda o programa
        '''
        running: bool = True
        mapper = self.parse_file()
        frame_count = 0
        turn = 0
        simulation_running = False
        error_message: list[str] = []
        error_until = 0

        end_hub: Hub | None = None
        for hub in mapper.list_hub:
            if hub.end_hub:
                end_hub = hub
                break

        # Fazer drone se mover animado
        positions, _ = self.calc_screen_positions(mapper)
        for drone in mapper.list_drone:
            if drone.current_hub is None:
                continue
            start_pos = positions["start"]
            drone.screen_x = start_pos[0]
            drone.screen_y = start_pos[1]

        while running:

            frame_count += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    virtual_mouse = self.to_virtual_coordinates(event.pos)
                    if virtual_mouse[0] < self.game.get_width():
                        continue

                    menu_mouse = (
                        virtual_mouse[0] - self.game.get_width(),
                        virtual_mouse[1]
                    )
                    if self.sound_rect.collidepoint(menu_mouse):
                        if self.sound_on:
                            pygame.mixer.music.pause()
                            self.sound_on = False
                        else:
                            pygame.mixer.music.unpause()
                            self.sound_on = True

                    if self.start_button.collidepoint(menu_mouse):
                        simulation_running = True

                    elif self.stop_button.collidepoint(menu_mouse):
                        simulation_running = False
                        error_message = [
                            "DRONES",
                            "   ARE STOPED."
                            ]
                        error_until = pygame.time.get_ticks() + 2000
                        print("Stop")

                    elif self.reverse_button.collidepoint(menu_mouse):
                        if end_hub is None:
                            continue

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
                                drone.path = drone.final_path[::-1]
                                drone.path_index = 0
                                drone.current_connection = None
                                drone.target_hub = None
                                drone.active = False
                                drone.moving = False

                            error_message = [
                                "REVERSE",
                                "     IS ENABLED."
                                ]
                            error_until = pygame.time.get_ticks() + 2000
                            print("reverse")

                    elif self.reset_button.collidepoint(menu_mouse):
                        simulation_running = False
                        turn = 0
                        frame_count = 0
                        mapper = self.parse_file()
                        positions, _ = self.calc_screen_positions(mapper)

                        for drone in mapper.list_drone:
                            if drone.current_hub is None:
                                continue
                            start_pos = positions["start"]
                            drone.screen_x = start_pos[0]
                            drone.screen_y = start_pos[1]

                        error_message = [
                            "THE DRONE POSITIONS",
                            "    HAVE BEEN RESET."
                            ]
                        error_until = pygame.time.get_ticks() + 2000
                        print("Reset")

            if frame_count % 60 == 0 and simulation_running:
                # if simulation_running:

                moving = False
                for drone in mapper.list_drone:
                    if drone.moving:
                        moving = True
                        break

                if not moving:
                    if end_hub is None:
                        continue

                    target = "start" if mapper.reverse else end_hub.name

                    if mapper.drones_in_hub(target) < mapper.nb_drone:
                        turn += 1
                        mapper.move_drone()

            self.animate_drones(mapper)

            self.game.blit(
                pygame.transform.scale(self.bg, self.game.get_size()),
                (0, 0)
            )
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
                    self.menu.blit(text, (120, y))
                    y += 28

            self.virtual_window.blit(self.game, (0, 0))
            self.virtual_window.blit(self.menu, (self.game.get_width(), 0))

            self.render_to_window()
            # desenha bg, conexões e hubs em self.game

            pygame.display.flip()
        pygame.quit()


def main() -> None:
    try:
        tela = App()
        tela.run()
    except Exception as e:
        exc_tb = exc_info()[2]
        error_line = exc_tb.tb_lineno if exc_tb is not None else -1
        print(f"Erro in line {error_line}: {e}")


if __name__ == "__main__":
    main()
