from validate import Parser
from map import Map
import os


class MapLoader():

    def __init__(self) -> None:
        self.MAP_ROOT: str = "maps"
        self.DIFFICULTY: list[str] = ["easy", "medium", "hard", "challenger"]

    def choose_difficult(self) -> str:
        while True:
            os.system("clear")
            print("\nDifficulties: ")
            print(f"1 - {self.DIFFICULTY[0]} maps")
            print(f"2 - {self.DIFFICULTY[1]} maps")
            print(f"3 - {self.DIFFICULTY[2]} maps")
            print(f"4 - {self.DIFFICULTY[3]} maps")
            print("5 - Quit the simulation\n")

            difficult: str = input("Choose a difficulty: ").strip()

            if difficult.isdigit():
                choose = int(difficult)
                if 1 <= choose <= 4:
                    return self.DIFFICULTY[choose - 1]
                elif difficult == '5':
                    print("Valeu Tamo junto!!!")
                    return "quit"
            else:
                print("Enter a valid number")

    def choose_map(self, difficulty_dir: str) -> str | None:
        try:
            names: list[str] = os.listdir(difficulty_dir)
        except FileNotFoundError:
            print(f"difficulty dir {difficulty_dir} has not found!")
            return None

        maps: list[str] = []
        for name in names:
            path: str = os.path.join(difficulty_dir, name)
            if os.path.isfile(path):
                maps.append(name)
        maps.sort()

        if len(maps) == 0:
            print(f"No map found in '{difficulty_dir}'!")
            return None

        back: int = len(maps) + 1

        while True:
            os.system('clear')
            print("\nChoose the map: ")
            for i in range(len(maps)):
                print(f"{i + 1} -  {maps[i]}")
            print(f"{back} -  Back\n")

            file: str = input("Enter a number of file: ").strip()

            if not file.isdigit():
                print("Invalid number, try again.")
                continue

            choose: int = int(file)

            if choose == back:
                return None

            if 1 <= choose <= len(maps):
                return maps[choose - 1]

            print("Invalid number, try again horse!")

    def parse_file(self, map_file: str) -> Map:
        try:
            file = open(map_file)
            content: str = file.read()
            file.close()
        except Exception as e:
            print(e)
            exit(1)

        parser = Parser(content)
        hubs, connections, nb_drone = parser.parse()

        return Map(list_hub=hubs, list_conex=connections, nb_drone=nb_drone)
