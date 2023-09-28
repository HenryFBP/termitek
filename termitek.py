from asciimatics.effects import Effect
from asciimatics.renderers import Renderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication
from asciimatics.event import KeyboardEvent
import math
import logging
from typing import Tuple, List
import random

# 1. Set up logging configuration
logging.basicConfig(
    filename="termitek.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
)


class Item:
    def __init__(self, symbol, tooltip, name, amount) -> None:
        self.symbol = symbol
        self.tooltip = tooltip
        self.name = name
        self.amount = amount


class Items:
    @staticmethod
    def Log():
        return Item("L", "A log.", "Log", 1)


class Block:
    def __init__(
        self,
        symbol,
        tooltip,
        walkable=True,
        mineable=False,
        droptable: List[List[Item] | List[float]] = [],
    ):
        self.symbol = symbol
        self.tooltip = tooltip
        self.walkable = walkable
        self.mineable = mineable
        self.droptable = droptable

    def drop_items(self) -> List[Item]:
        if not self.droptable:
            return []

        items, probabilities = self.droptable
        dropped_items = []

        for prob, item in zip(items, probabilities):
            if random.random() < prob:
                dropped_items.append(item)

        return dropped_items


class Blocks:
    @staticmethod
    def Wall():
        return Block("#", "Wall: Impenetrable barrier.", False)

    @staticmethod
    def Ground():
        return Block(".", "Ground: Walkable terrain.")

    @staticmethod
    def Tree():
        return Block(
            "T",
            "Tree: A source of wood.",
            False,
            True,
            [[1.0, 1.0, 1.0], [Items.Log(), Items.Log(), Items.Log()]],
        )

    @staticmethod
    def Machine():
        return Block("M", "Machine: Used for automation.", False, True)


class World:
    def __init__(self, game_map):
        self.blocks = {
            "#": Blocks.Wall(),
            ".": Blocks.Ground(),
            "T": Blocks.Tree(),
            "M": Blocks.Machine(),
        }
        self.map: List[List[Block]] = [
            [self.blocks[cell] for cell in row] for row in game_map
        ]

    def get_block(self, x, y)->Block:
        if self.within_bounds(x,y):
            return self.map[y][x]
        return None
    
    def set_block(self, x, y, block:Block)->None:
        if self.within_bounds(x,y):
            self.map[y][x] = block

    def break_block(self, x, y)->List[Item]:
        items = []

        block = self.get_block(x,y)
        if block:

            if (not block.mineable):
                return items

            items += block.drop_items()
            self.set_block(x,y, Blocks.Ground())
        
        return items

    def within_bounds(self,x,y):
        return ((0 <= y < len(self.map)) and (0 <= x < len(self.map[0])))

game_map: List[str] = [
    "###############",
    "......T....#..#",
    "#.....#....#..#",
    "#..M..#....#..#",
    "#...T.#...T#..#",
    "#.T...#.T..#..#",
    "###############",
]


def cardinal_to_vector(cardinal: str) -> Tuple[int]:
    cardinal = cardinal.upper()
    return {
        "N": (
            0,
            -1,
        ),
        "E": (
            1,
            0,
        ),
        "S": (
            0,
            1,
        ),
        "W": (
            -1,
            0,
        ),
    }[cardinal]

class Inventory:
    def __init__(self) -> None:
        self.items: List[Item] = []

    def add_item(self, item: Item):
        self.items.append(item)

    def add_items(self, items: List[Item]):
        for item in items:
            self.add_item(item)

class Player:
    def __init__(self, x, y, inventory=Inventory()):
        # Player's position
        self.x = x
        self.y = y

        # Player's viewing angle (for future 3D rendering)
        self.angle = 0

        self.inventory = inventory

    def position_in_front_of_me(self) -> Tuple[int]:
        vec = cardinal_to_vector(self.get_heading())
        pos = self.get_position()
        return (
            vec[0] + pos[0],
            vec[1] + pos[1],
        )

    def break_block_in_front(self, world:World)->None:
        
        pos = self.position_in_front_of_me()
        block = world.get_block(*pos)
        if(block):
            items = world.break_block(*pos)
            self.inventory.add_items(items)


    def block_in_front_of_me(self, world: World) -> Block:
        pos_in_front = self.position_in_front_of_me()
        block = world.get_block(*pos_in_front)
        return block

    def get_heading(self):
        directions = "ESWN"

        index = int(((self.angle + (math.pi / 4)) % (2 * math.pi)) / (math.pi / 2))

        if index >= 4:
            index = index % 4

        return directions[index]

    def move_to(self, offset: Tuple[int], world: World):
        if can_move_to(self.x + offset[0], self.y + offset[1], world):
            self.x += offset[0]
            self.y += offset[1]

    def move_left(self, world: World):
        self.move_to((-1, 0), world)

    def move_right(self, world: World):
        self.move_to((1, 0), world)

    def move_up(self, world: World):
        self.move_to((0, -1), world)

    def move_down(self, world: World):
        self.move_to((0, 1), world)

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

            if is_action_key(key):
                player_pos = self.player.get_position()

                if key == Screen.KEY_LEFT:
                    self.player.move_left(self.world)
                elif key == Screen.KEY_RIGHT:
                    self.player.move_right(self.world)
                elif key == Screen.KEY_UP:
                    self.player.move_up(self.world)
                elif key == Screen.KEY_DOWN:
                    self.player.move_down(self.world)

                elif key == ord("a"):
                    self.player.angle -= math.pi / 16
                elif key == ord("d"):
                    self.player.angle += math.pi / 16

                # move forwards in 3d
                elif key == ord("w"):
                    vec = cardinal_to_vector(self.player.get_heading())
                    self.player.move_to(vec, self.world)

                # move backwards in 3d
                elif key == ord("s"):
                    vec = cardinal_to_vector(self.player.get_heading())
                    vec = (
                        -vec[0],
                        -vec[1],
                    )
                    self.player.move_to(vec, self.world)

                # mine block in front of player
                elif key == ord('m'):
                    self.player.break_block_in_front(self.world)


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
            "Inventory: TODO", 0, len(self.world.map) + 5, colour=Screen.COLOUR_BLUE
        )


class LookingAtEffect(BaseEffect):
    def _update(self, frame_no):
        facing_block = self.player.block_in_front_of_me(self.world)
        text = "Facing: {}".format(facing_block.tooltip)

        self._screen.print_at(
            text, 0, len(self.world.map) + 4, colour=Screen.COLOUR_MAGENTA
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


def is_action_key(key):
    keys = [
        Screen.KEY_LEFT,
        Screen.KEY_RIGHT,
        Screen.KEY_UP,
        Screen.KEY_DOWN,
        ord("w"),
        ord("a"),
        ord("s"),
        ord("d"),
        ord("m"),
    ]
    return key in keys


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
                LookingAtEffect(screen, player, world),
            ],
            -1,
        )
    ]
    screen.play(scenes, stop_on_resize=True)


Screen.wrapper(game)
