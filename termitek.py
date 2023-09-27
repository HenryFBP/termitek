from asciimatics.effects import Effect
from asciimatics.renderers import Renderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication
from asciimatics.event import KeyboardEvent
import math
import logging

# 1. Set up logging configuration
logging.basicConfig(filename='termitek.log', level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

game_map = [
    "###############",
    "#.....T....#..#",
    "#.....#....#..#",
    "#..M..#....#..#",
    "#.....#....#..#",
    "#.....#....#..#",
    "###############"
]

tooltips = {
    "T": "Tree: A source of wood.",
    "M": "Machine: Used for automation.",
    ".": "Ground: Walkable terrain.",
    "#": "Wall: Impenetrable barrier."
}
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
        elif abs(self.angle - (math.pi/2)) < epsilon:
            return "E"
        elif abs(self.angle - math.pi) < epsilon:
            return "S"
        elif abs(self.angle - (3*math.pi/2)) < epsilon:
            return "W"
        # If angle doesn't exactly match, just return the nearest cardinal direction
        return ["N", "E", "S", "W"][int(((self.angle + (math.pi / 4)) % (2 * math.pi)) / (math.pi / 2))]

    def move_left(self, game_map):
        if can_move_to(self.x - 1, self.y, game_map):
            self.x -= 1

    def move_right(self, game_map):
        if can_move_to(self.x + 1, self.y, game_map):
            self.x += 1

    def move_up(self, game_map):
        if can_move_to(self.x, self.y - 1, game_map):
            self.y -= 1

    def move_down(self, game_map):
        if can_move_to(self.x, self.y + 1, game_map):
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
    def __init__(self, screen, player:Player):
        super(BaseEffect, self).__init__(screen)
        self._screen = screen
        self.player = player

    def reset(self):
        pass

    def stop_frame(self):
        return 0
    
    def _update(self, frame_no):
        self._screen.clear_buffer(Screen.COLOUR_WHITE, 0, Screen.COLOUR_BLACK)
        
        # Static Message
        self._screen.print_at('Hello, World!', 0, 0, colour=Screen.COLOUR_GREEN)
        
        # Draw game state - 2D Top-down View
        for y, row in enumerate(game_map):
            for x, cell in enumerate(row):
                if [x, y] == self.player.get_position():
                    self._screen.print_at("P", x, y, colour=Screen.COLOUR_RED, bg=Screen.COLOUR_BLACK)
                else:
                    color = Screen.COLOUR_GREEN if cell == "T" else Screen.COLOUR_BLACK
                    self._screen.print_at(cell, x, y, bg=color)

        # Render 3D view
        render_3d_view(self._screen,self.player.get_position(), self.player.get_angle(), len(game_map[0]) + 2, 0)

        heading = self.player.get_heading()
        compass_text = f"Compass: {heading}"
        self._screen.print_at(compass_text, 0, len(game_map) + 1, colour=Screen.COLOUR_YELLOW)


class PlayerEffect(BaseEffect):
    def process_event(self, event):
        if isinstance(event, KeyboardEvent):

            key = event.key_code
            
            if is_movement_key(key):
                player_pos = self.player.get_position()
                if key == Screen.KEY_LEFT and can_move_to(player_pos[0] - 1, player_pos[1], game_map):
                    self.player.move_left(game_map)
                elif key == Screen.KEY_RIGHT and can_move_to(player_pos[0] + 1, player_pos[1], game_map):
                    self.player.move_right(game_map)
                elif key == Screen.KEY_UP and can_move_to(player_pos[0], player_pos[1] - 1, game_map):
                    self.player.move_up(game_map)
                elif key == Screen.KEY_DOWN and can_move_to(player_pos[0], player_pos[1] + 1, game_map):
                    self.player.move_down(game_map)
                elif key == ord('a'):
                    self.player.angle -= math.pi / 16
                elif key == ord('d'):
                    self.player.angle += math.pi / 16
                logging.info(f'Player moved to: {player_pos}')
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
        for y, row in enumerate(game_map):
            for x, cell in enumerate(row):
                color = Screen.COLOUR_GREEN if cell == "T" else Screen.COLOUR_BLACK
                self._screen.print_at(cell, x, y, bg=color)

        # Draw player on the minimap
        player_x, player_y = self.player.get_position()
        self._screen.print_at("P", int(player_x), int(player_y), bg=Screen.COLOUR_RED)

class CompassEffect(BaseEffect):
    def _update(self, frame_no):
        # You can render compass using ASCII art or simple direction letters based on the player's angle.
        compass_dir = self.player.get_heading()
        self._screen.print_at(compass_dir, 0, len(game_map) + 2, colour=Screen.COLOUR_YELLOW)

class View3DEffect(BaseEffect):
    def _update(self, frame_no):
        render_3d_view(self._screen, self.player.get_position(), self.player.get_angle(), len(game_map[0]) + 2, 0)


FOV = math.pi / 4  # 45 degree field of view
MAX_DISTANCE = 10  # Maximum distance a ray can travel

def can_move_to(x, y, game_map):
    # Check boundaries
    if x < 0 or x >= len(game_map[0]) or y < 0 or y >= len(game_map):
        return False
    # Check for wall
    if game_map[y][x] == "#":
        return False
    return True

def is_movement_key(key):
    movement_keys = [
        Screen.KEY_LEFT,
        Screen.KEY_RIGHT,
        Screen.KEY_UP,
        Screen.KEY_DOWN,
        ord('a'),
        ord('d')
    ]
    return key in movement_keys
def cast_ray(x, y, angle, game_map):
    distance = 0
    dx = math.cos(angle)
    dy = math.sin(angle)

    while distance < MAX_DISTANCE:
        x += dx * 0.1
        y += dy * 0.1
        distance += 0.1

        if 0 <= int(y) < len(game_map) and 0 <= int(x) < len(game_map[0]):
            tile = game_map[int(y)][int(x)]
            if tile == "#":
                break

    return distance

def render_3d_view(screen, player_position, player_angle, start_x, start_y):
    screen_width = screen.width // 2
    screen_height = screen.height
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
            if 0 <= map_x < len(game_map[0]) and 0 <= map_y < len(game_map):
                if game_map[map_y][map_x] == 'T':
                    hit_tree = True
                    break

        # Calculate height based on depth (perspective projection)
        if hit_tree:
            object_height = screen_height / (depth * 1.5)  # Trees are shorter
            object_top = max(0, int(screen_height / 2 - object_height / 2))
            object_bottom = min(screen_height, int(screen_height / 2 + object_height / 2))
            color = Screen.COLOUR_GREEN  # Trees are green
        else:
            object_height = screen_height / depth if depth > 0 else screen_height
            object_top = max(0, int(screen_height / 2 - object_height / 2))
            object_bottom = min(screen_height, int(screen_height / 2 + object_height / 2))
            color = Screen.COLOUR_WHITE  # Walls are white

        # Draw the column
        for y in range(object_top, object_bottom):
            screen.print_at('#', start_x + x, start_y + y, bg=color)

        # Draw ceiling and floor if needed
        for y in range(0, object_top):
            screen.print_at(' ', start_x + x, start_y + y, bg=Screen.COLOUR_BLUE)
        for y in range(object_bottom, screen_height):
            screen.print_at('.', start_x + x, start_y + y, bg=Screen.COLOUR_GREEN)


def game(screen):
    player = Player(1, 1)
    scenes = [Scene([
        MinimapEffect(screen, player), 
        CompassEffect(screen, player), 
        View3DEffect(screen, player),
        PlayerEffect(screen,player),
        ], -1)]
    screen.play(scenes, stop_on_resize=True)

Screen.wrapper(game)
