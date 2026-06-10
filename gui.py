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
        self.bg = pygame.image.load("images/mapa.png")  # escolher a imagem e por o caminho aqui
        # pygame.mixer.music.load() #  da p por musica
        self.width, self.height = 1000, 800
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

    def run(self) -> None:
        running: bool = True
        while (running):

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.virtual_window.blit(self.game, (0, 0))
            self.virtual_window.blit(self.menu, (self.game.get_width(), 0))

            height = self.window.get_height()
            width = self.window.get_width()
            change_size = pygame.transform.scale(self.virtual_window,
                                                 (width, height))
            self.window.blit(change_size)
            self.game.blit(self.bg)

            pygame.display.flip()
        pygame.quit()


def main() -> None:
    tela = App()
    tela.run()


if __name__ == "__main__":
    main()
