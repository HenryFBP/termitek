from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent

def demo(screen):
    screen.print_at('Hello, World! Press q or ESC', 0, 0, colour=Screen.COLOUR_GREEN)
    screen.refresh()
    while True:
        ev = screen.get_event()
        if isinstance(ev, KeyboardEvent) and ev.key_code in [ord('Q'), ord('q'), Screen.KEY_ESCAPE]:
            return

Screen.wrapper(demo)
