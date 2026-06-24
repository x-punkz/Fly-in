from validate import Parser
from map import Hub, Connection, Drone, Map
from sys import argv
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
        self.drone_img = pygame.image.load("images/drone/drone.png")  # .convert_alpha()
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
        menu_color = (128, 128, 128)
        self.menu.fill(menu_color)

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

        # # extrai listas X e Y rotacionadas para calcular limites
        # xs = [coord[0] for coord in rotated_coords.values()]
        # ys = [coord[1] for coord in rotated_coords.values()]

        # min_x, max_x = min(xs), max(xs)
        # min_y, max_y = min(ys), max(ys)

        # # dx,dy = sao x,y em unidades do mapa, o 1 no max/min eh uma protecao
        # # por zero, caso os hubs tenham a msm x ou y,dx/dy vira 0
        # dx = max(1, max_x - min_x)
        # dy = max(1, max_y - min_y)

        # Pad é a margem (em pixels) entre as bordas da Surface e o mapa usada
        #   ao calcular a escala.
        # Serve para evitar que hubs/conexões encostem nas bordas e para dar
        #   espaço/centralizar o desenho.
        pad = 20

        # apagar talvez
        # scale_x = (game_w - 2*pad) / dx
        # scale_y = (game_h - 2*pad) / dy
        # scale = int(min(scale_x, scale_y))

        def to_screen(rot_x: float, rot_y: float) -> tuple[int, int]:

            # por o centro do mapa de hubs onde eu quiser
            center_y = game_h * 0.90

            # empurra horizontalmente o mapa de hubs
            sx = (rot_x - start_x) * scale + game_w * 0.20

            sy = center_y - (rot_y - start_y) * scale

            return int(sx), int(sy)

        # calcula posicoes na tela a partir das coordenadas rotacionadas
        positions = {
            name: to_screen(*coord) for name, coord in rotated_coords.items()
            }

        return positions, scale

    def draw_drone(self, mapper: Map) -> None:
        '''
            desenha os drones na tela
        '''

        # positions, _ = self.calc_screen_positions(mapper)
        for i, drone in enumerate(mapper.list_drone):
            pos = (drone.screen_x, drone.screen_y)

            offset_x = i * 15
            offset_y = i * 10
            img = pygame.transform.scale(self.drone_img, (300, 300))

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

                drone.current_hub = drone.target_hub
                drone.target_hub = None
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
        # icon_size = max(80, min(180, int(scale * 0.8)))
        # icon_size = baseline  # max(16, int(64 * (scale / baseline)))
        # largura da linha
        # line_w = max(1, int(4 * (scale / baseline)))

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

    def run(self) -> None:
        '''
            Roda o programa
        '''
        running: bool = True
        mapper = self.parse_file()
        # print(mapper.find_path()) p ver se o caminho ta certo.
        frame_count = 0

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

            if frame_count % 60 == 0:
                mapper.move_drone()

            self.animate_drones(mapper)

            self.game.blit(self.bg,  (0, 0))
            self.draw_map(mapper)
            self.draw_drone(mapper)

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
    # try:
        tela = App()
        tela.run()
    # except Exception:
        # print("Image file not found!")


if __name__ == "__main__":
    main()
