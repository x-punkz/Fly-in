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
        self.bg = pygame.image.load("images/mapa.png")
        # pygame.mixer.music.load() #  da p por musica
        self.width, self.height = 1280, 1060
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
            #     # elif ValidationError:
            exit(1)

        return Map(list_hub=hubs, list_conex=connections, nb_drone=nb_drone)

    def calc_screen_positions(self, mapper: Map) -> tuple[dict[str, tuple], int]:
        '''
            Calcula as posicoes das coordenadas p printar na tela
        '''

        gw, gh = int(self.game.get_width()), int(self.game.get_height())
        # xs, ys = coord x,y no screen
        xs = [int(h.x) for h in mapper.list_hub]
        ys = [int(h.y) for h in mapper.list_hub]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # dx,dy = sao x,y em unidades do mapa, o 1 no max/min eh uma protecao
        # por zero, caso os hubs tenham a msm x ou y,dx/dy vira 0
        dx = max(1, max_x - min_x)
        dy = max(1, max_y - min_y)

        # Pad é a margem (em pixels) entre as bordas da Surface e o mapa usada
        #   ao calcular a escala.
        # Serve para evitar que hubs/conexões encostem nas bordas e para dar
        #   espaço/centralizar o desenho.
        pad = 50

        scale_x = (gw - 2*pad) / dx
        scale_y = (gh - 2*pad) / dy
        scale = int(min(scale_x, scale_y))

        def to_screen(x: int, y: int) -> tuple[int, int]:
            sx = pad + (int(x) - min_x) * scale
            sy = gh - (pad + (int(y) - min_y) * scale)  # inverte y
            return int(sx), int(sy)

        positions = {
            hub.name: to_screen(hub.x, hub.y) for hub in mapper.list_hub
        }
        if 'start' in positions:
            oy = gh // 2 - positions['start'][1]
            positions = {k: (v[0], v[1] + oy) for k, v in positions.items()}
        return positions, scale

    def draw_map(self, mapper: Map) -> None:
        positions, scale = self.calc_screen_positions(mapper)
        baseline = 50
        icon_size = max(16, int(32 * (scale / baseline)))
        # largura da linha
        # line_w = max(1, int(4 * (scale / baseline)))

        # desenhar conexoes
        for conn in mapper.list_conex:
            start_p = positions.get(conn.start_point)
            end_p = positions.get(conn.end_point)
            if start_p and end_p:
                pygame.draw.line(self.game,
                                 (0, 0, 0),
                                 start_p, end_p, width=4)
        # Desenhar hubs (imagem centralizada ou circulo)
        for hub in mapper.list_hub:
            pos = positions[hub.name]
            pos_x = pos[0]
            pos_y = pos[1]
            try:
                img = pygame.image.load(hub.image).convert_alpha()
                # Ajusta o tamanho
                img = pygame.transform.scale(img, (icon_size, icon_size))
                self.game.blit(img,  (pos_x - img.get_width()//2,
                                      pos_y - img.get_height()//2))
            except Exception:
                pygame.draw.circle(self.game, (0, 120, 250), pos, icon_size // 2)

    def run(self) -> None:
        running: bool = True
        mapper = self.parse_file()
        while (running):

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # desenha bg, conexões e hubs em self.game
            self.draw_map(mapper)

            self.virtual_window.blit(self.game, (0, 0))
            self.virtual_window.blit(self.menu, (self.game.get_width(), 0))

            height = self.window.get_height()
            width = self.window.get_width()
            change_size = pygame.transform.scale(self.virtual_window,
                                                 (width, height))
            self.window.blit(change_size, (0, 0))
            self.game.blit(self.bg,  (0, 0))
            # --- p printar o hub ---
            # for hub in maper.list_hub:
            #     self.game.blit(pygame.image.load(hub.image), (2, 3))

            pygame.display.flip()
        pygame.quit()


def main() -> None:
    tela = App()
    tela.run()


if __name__ == "__main__":
    main()
