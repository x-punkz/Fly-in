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
        # self.bg = pygame.image.load("") #  escolher a imagem e por o caminho aqui
        self.width, self.height = 1000, 800
        self.window = pygame.display.set_mode((self.width, self.height))

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
            pygame.display.flip()
        pygame.quit()


def main() -> None:
    tela = App()
    tela.run()


if __name__ == "__main__":
    main()
