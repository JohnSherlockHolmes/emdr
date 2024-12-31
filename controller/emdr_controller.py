import pygame
import thorpy
from devices import Devices
from config import Config
from hiperf_timer import HighPerfTimer
from time import sleep
import os
import sys

PROBE_EVENT = pygame.USEREVENT + 1
ACTION_EVENT = pygame.USEREVENT + 2

class MyThorpyApp(thorpy.Application):
    def __init__(self, size, caption=None, icon="thorpy", center=True, flags=0):
        global _SCREEN, _CURRENT_APPLICATION
        _CURRENT_APPLICATION = self
        self.size = tuple(size)
        self.caption = caption
        pygame.init()
        if center:
            os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.set_icon(icon)
        screen = pygame.display.set_mode(self.size, flags)
        if self.caption:
            pygame.display.set_caption(self.caption)
        _SCREEN = screen
        self.default_path = "./"

    def set_icon(self, icon):
        try:
            pygame.display.set_icon(pygame.image.load(icon))
        except FileNotFoundError:
            print(f"Icon {icon} not found. Using default.")

class Container(thorpy.Ghost):
    def set_visible(self, value):
        for elem in self.get_elements():
            elem.set_visible(value)
            elem.set_active(value)

class Selector(Container):
    def __init__(self, x, y, title, values, format_str, btn_plus, btn_minus, updater=None, cyclic=False):
        super().__init__()
        self.elem1 = thorpy.make_text(title, font_size=14)
        self.elem1.set_center((60 + 120 * x, 40 + 80 * y - 12))
        self.elem2 = thorpy.make_text(format_str, font_size=18)
        self.elem2.set_center((60 + 120 * x, 40 + 80 * y + 12))
        self.add_elements([self.elem1, self.elem2])
        self.updater = updater
        self.values = values
        self.value = 0
        self.format_str = format_str
        self.value_index = 0
        self.cyclic = cyclic
        self.show_value()

        if btn_plus:
            btn_plus.user_func = self.next_value
        if btn_minus:
            btn_minus.user_func = self.prev_value

    def show_value(self):
        val = self.values[self.value_index] if self.values else self.value
        formatted_val = self.format_str.format(*val) if isinstance(val, tuple) else self.format_str.format(val)
        self.elem2.set_text(formatted_val)
        self.elem1.unblit_and_reblit()
        self.elem2.unblit_and_reblit()
        if self.updater:
            self.updater()

    def next_value(self):
        self.value_index = (self.value_index + 1) % len(self.values) if self.cyclic else min(self.value_index + 1, len(self.values) - 1)
        self.show_value()

    def prev_value(self):
        self.value_index = (self.value_index - 1) % len(self.values) if self.cyclic else max(self.value_index - 1, 0)
        self.show_value()

    def get_value(self):
        return self.values[self.value_index] if self.values else self.value

    def set_value(self, value):
        if self.values and value in self.values:
            self.value_index = self.values.index(value)
        else:
            self.value = value
        self.show_value()

class Switch(Container):
    def __init__(self, x, y, title, btn_action, updater=None):
        super().__init__()
        self.elem = thorpy.make_text(title, font_size=16)
        self.elem.set_center((60 + 120 * x, 40 + 80 * y))
        self.add_elements([self.elem])
        self.updater = updater
        self.state = False
        if btn_action:
            btn_action.user_func = self.toggle
        self.show_state()

    def show_state(self):
        state_text = "ON" if self.state else "OFF"
        self.elem.set_text(f"{state_text}")
        self.elem.unblit_and_reblit()
        if self.updater:
            self.updater()

    def toggle(self):
        self.state = not self.state
        self.show_state()

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state
        self.show_state()

class Controller:
    def __init__(self, fullscreen=False, touchscreen=False):
        self.fullscreen = fullscreen
        self.touchscreen = touchscreen
        self.devices = Devices()
        self.config = Config()
        self.timer = HighPerfTimer()

        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.app = MyThorpyApp((800, 600), "MyThorPyApp", flags=flags)

        self.menu_elements = []
        self.setup_ui()

    def setup_ui(self):
        self.main_box = thorpy.Box.make(self.menu_elements)
        thorpy.store(self.main_box)
        self.menu = thorpy.Menu(self.main_box)

    def event_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == PROBE_EVENT:
                    self.handle_probe_event()
                elif event.type == ACTION_EVENT:
                    self.handle_action_event()
                self.menu.react(event)

    def handle_probe_event(self):
        print("Handling probe event")

    def handle_action_event(self):
        print("Handling action event")

if __name__ == "__main__":
    fullscreen = False  # Set to True if fullscreen mode is required
    touchscreen = False  # Set to True if running on a touchscreen device
    controller = Controller(fullscreen, touchscreen)
    controller.event_loop()
