from asciimatics.effects import Effect
from asciimatics.renderers import Renderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication
from asciimatics.event import KeyboardEvent
import math
import logging

# 1. Set up logging configuration
logging.basicConfig(
    filename="termitek.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
)


class Block:
    def __init__(self, symbol, tooltip, walkable=True):
        self.symbol = symbol
        self.tooltip = tooltip
        self.walkable = walkable


class World:
    def __init__(self, game_map):
        self.blocks = {
            "#": Block("#", "Wall: Impenetrable barrier.", False),
            ".": Block(".", "Ground: Walkable terrain."),
            "T": Block("T", "Tree: A source of wood."),
            "M": Block("M", "Machine: Used for automation."),
        }
        self.map = [[self.blocks[cell] for cell in row] for row in game_map]

    def get_block(self, x, y):
        if 0 <= y < len(self.map) and 0 <= x < len(self.map[0]):
            return self.map[y][x]
        return None


game_map = [
    "###############",
    "......T....#..#",
    "#.....#....#..#",
    "#..M..#....#..#",
    "#.....#....#..#",
    "#.....#....#..#",
    "###############",
]


class Player:
    def __init__(self, x, y):
        # Player's position
        self.x = x
        self.y = y

        # Player's viewing angle (for future 3D rendering)
        self.angle = 0

    def get_heading(self):
        # Define a small threshold for floating point precision
        epsilon = 0.01

        if abs(self.angle) < epsilon:
            return "N"
        elif abs(self.angle - (math.pi / 2)) < epsilon:
            return "E"
        elif abs(self.angle - math.pi) < epsilon:
            return "S"
        elif abs(self.angle - (3 * math.pi / 2)) < epsilon:
            return "W"
        # If angle doesn't exactly match, just return the nearest cardinal direction

        index = int(((self.angle + (math.pi / 4)) % (2 * math.pi)) / (math.pi / 2))

        if index >= 4:
            index = index % 4

        return ["N", "E", "S", "W"][index]

    def move_left(self, world: World):
        if can_move_to(self.x - 1, self.y, world):
            self.x -= 1

    def move_right(self, world: World):
        if can_move_to(self.x + 1, self.y, world):
            self.x += 1

    def move_up(self, world: World):
        if can_move_to(self.x, self.y - 1, world):
            self.y -= 1

    def move_down(self, world: World):
        if can_move_to(self.x, self.y + 1, world):
            self.y += 1

    def rotate_left(self, amount):
        self.angle -= amount

    def rotate_right(self, amount):
        self.angle += amount

    def get_position(self):
        return self.x, self.y

    def get_angle(self):
        return self.angle


class BaseEffect(Effect):
    def __init__(self, screen: Screen, player: Player, world: World):
        super(BaseEffect, self).__init__(screen)
        self._screen = screen
        self.player = player
        self.world = world

    def reset(self):
        pass

    def stop_frame(self):
        return 0

    def _update(self, frame_no):
        pass


class PlayerEffect(BaseEffect):
    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            key = event.key_code

            if is_movement_key(key):
                player_pos = self.player.get_position()
                if key == Screen.KEY_LEFT and can_move_to(
                    player_pos[0] - 1, player_pos[1], self.world
                ):
                    self.player.move_left(self.world)
                elif key == Screen.KEY_RIGHT and can_move_to(
                    player_pos[0] + 1, player_pos[1], self.world
                ):
                    self.player.move_right(self.world)
                elif key == Screen.KEY_UP and can_move_to(
                    player_pos[0], player_pos[1] - 1, self.world
                ):
                    self.player.move_up(self.world)
                elif key == Screen.KEY_DOWN and can_move_to(
                    player_pos[0], player_pos[1] + 1, self.world
                ):
                    self.player.move_down(self.world)
                elif key == ord("a"):
                    self.player.angle -= math.pi / 16
                elif key == ord("d"):
                    self.player.angle += math.pi / 16
                logging.info(f"Player moved to: {player_pos}")
            elif key == Screen.KEY_ESCAPE:
                logging.info("Goodbye :)")
                raise StopApplication("User pressed ESC")

            # After processing the event, force an update to all effects.
            self._screen.force_update()

        return event


class MinimapEffect(BaseEffect):
    def _update(self, frame_no):
        self._draw_minimap()

    def _draw_minimap(self):
        for y, row in enumerate(self.world.map):
            for x, cell in enumerate(row):
                color = (
                    Screen.COLOUR_GREEN if cell.symbol == "T" else Screen.COLOUR_BLACK
                )
                self._screen.print_at(cell.symbol, x, y, bg=color)

        # Draw player on the minimap
        player_x, player_y = self.player.get_position()
        self._screen.print_at("P", int(player_x), int(player_y), bg=Screen.COLOUR_BLACK)


class InventoryEffect(BaseEffect):
    def _update(self, frame_no):
        self._screen.print_at(
            "Inventory: TODO", 0, len(self.world.map) + 4, colour=Screen.COLOUR_BLUE
        )


class CompassEffect(BaseEffect):
    def _update(self, frame_no):
        # You can render compass using ASCII art or simple direction letters based on the player's angle.
        compass_dir = self.player.get_heading()
        text_heading = "[  {}  ]".format(compass_dir)
        self._screen.print_at(
            text_heading, 0, len(self.world.map) + 2, colour=Screen.COLOUR_YELLOW
        )

        text_xy = "[{} , {}]".format(*self.player.get_position())
        self._screen.print_at(
            text_xy, 0, len(self.world.map) + 3, colour=Screen.COLOUR_YELLOW
        )


class View3DEffect(BaseEffect):
    def _update(self, frame_no):
        render_3d_view(
            self._screen,
            self.player,
            self.world,
            len(self.world.map[0]) + 2,
            0,
        )


FOV = math.pi / 4  # 45 degree field of view
MAX_DISTANCE = 10  # Maximum distance a ray can travel


def can_move_to(x, y, world: World):
    block = world.get_block(x, y)
    if block is None:
        return False
    if not block.walkable:
        return False
    return True


def is_movement_key(key):
    movement_keys = [
        Screen.KEY_LEFT,
        Screen.KEY_RIGHT,
        Screen.KEY_UP,
        Screen.KEY_DOWN,
        ord("a"),
        ord("d"),
    ]
    return key in movement_keys


def render_3d_view(screen, player: Player, world: World, start_x, start_y):
    screen_width = screen.width // 2
    screen_height = screen.height
    player_position = player.get_position()
    player_angle = player.get_angle()
    max_depth = 8
    step = 0.05

    for x in range(screen_width):
        ray_angle = player_angle + (x - screen_width // 2) * (math.pi / screen_width)
        ray_pos = list(player_position)
        sin, cos = math.sin(ray_angle), math.cos(ray_angle)
        depth = 0
        hit_tree = False

        # Raycasting loop
        while depth < max_depth:
            ray_pos[0] += cos * step
            ray_pos[1] += sin * step
            depth += step

            map_x, map_y = int(ray_pos[0]), int(ray_pos[1])
            if 0 <= map_x < len(world.map[0]) and 0 <= map_y < len(world.map):
                if world.get_block(map_x, map_y).symbol == "T":
                    hit_tree = True
                    break

        # Calculate height based on depth (perspective projection)
        if hit_tree:
            object_height = screen_height / (depth * 1.5)  # Trees are shorter
            object_top = max(0, int(screen_height / 2 - object_height / 2))
            object_bottom = min(
                screen_height, int(screen_height / 2 + object_height / 2)
            )
            color = Screen.COLOUR_GREEN  # Trees are green
        else:
            object_height = screen_height / depth if depth > 0 else screen_height
            object_top = max(0, int(screen_height / 2 - object_height / 2))
            object_bottom = min(
                screen_height, int(screen_height / 2 + object_height / 2)
            )
            color = Screen.COLOUR_WHITE  # Walls are white

        # Draw the column
        for y in range(object_top, object_bottom):
            screen.print_at("#", start_x + x, start_y + y, bg=color)

        # Draw ceiling and floor if needed
        for y in range(0, object_top):
            screen.print_at(" ", start_x + x, start_y + y, bg=Screen.COLOUR_BLUE)
        for y in range(object_bottom, screen_height):
            screen.print_at(".", start_x + x, start_y + y, bg=Screen.COLOUR_GREEN)


def game(screen):
    player = Player(1, 1)
    world = World(game_map)
    scenes = [
        Scene(
            [
                MinimapEffect(screen, player, world),
                CompassEffect(screen, player, world),
                View3DEffect(screen, player, world),
                PlayerEffect(screen, player, world),
                InventoryEffect(screen, player, world),
            ],
            -1,
        )
    ]
    screen.play(scenes, stop_on_resize=True)


Screen.wrapper(game)
