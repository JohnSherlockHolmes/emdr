import pygame
import thorpy
from devices import Devices
from config import Config
from hiperf_timer import HighPerfTimer
from time import sleep
import os
from thorpy.painting.painters.imageframe import ButtonImage
import sys
from math import log

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
        
        # Set the screen to fullscreen with resizing
        screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN + pygame.RESIZABLE + flags)
        
        if self.caption:
            pygame.display.set_caption(caption)
        
        _SCREEN = screen
        self.default_path = "./"

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # User closes the window
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # Press Escape to exit fullscreen
                        running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.size = event.size
                    pygame.display.set_mode(self.size, pygame.RESIZABLE)
                    self.update_layout()  # Recalculate button sizes/positions

            pygame.display.update()

        pygame.quit()
        
class Selector(Container):

    def __init__(self, x, y, title, values, format, btn_plus, btn_minus, updater=None, cyclic=False):
        super().__init__()
        painter = thorpy.painters.basicframe.BasicFrame(color=(255, 255, 255))
        self.elem1 = thorpy.Element(title)
        self.elem1.set_painter(painter)
        self.elem1.set_size((120, 30), margins=(0,0))
        self.elem1.set_font_size(14)
        self.elem1.set_center_pos((60 + 120 * x, 40 + 80 * y - 12))
        self.elem2 = thorpy.Element(format)
        self.elem2.set_painter(painter)
        self.elem2.set_size((120, 30), margins=(0,0))
        self.elem2.set_font_size(18)
        self.elem2.set_center_pos((60 + 120 * x, 40 + 80 * y + 12))
        self.add_elements([self.elem1, self.elem2])
        self.updater = None
        self.values = values
        self.value = 0
        self.format = format
        self.value_index = 0
        self.show_value()
        self.updater = updater
        self.cyclic = cyclic
        if btn_plus:
            btn_plus.user_func = self.next_value
        if btn_minus:
            btn_minus.user_func = self.prev_value

    def show_value(self):
        if self.values:
            val = self.values[self.value_index]
        else:
            val = self.value
        if type(val) == tuple:
            str = self.format.format(*val)
        else:
            str = self.format.format(val)
        self.elem2.set_text(str)
        self.elem1.unblit_and_reblit()
        self.elem2.unblit_and_reblit()
        if self.updater is not None:
            self.updater()

    def next_value(self):
        self.value_index += 1
        if self.value_index >= len(self.values):
            if self.cyclic:
                self.value_index = 0
            else:
                self.value_index = len(self.values) - 1
        self.show_value()

    def prev_value(self):
        self.value_index -= 1
        if self.value_index < 0:
            if self.cyclic:
                self.value_index = len(self.values) - 1
            else:
                self.value_index = 0
        self.show_value()

    def get_value(self):
        if self.values:
            val = self.values[self.value_index]
        else:
            val = self.value
        return val

    def set_value(self, value):
        if self.values:
            idx = self.values.index(value)
            if idx >= 0:
                self.value_index = idx
        else:
            self.value = value
        self.show_value()

class Switch():

    def __init__(self, btn_on, btn_off, updater=None):
        self.updater = None
        self.btn_on = btn_on
        self.btn_on.user_func = self.on_click
        self.btn_off = btn_off
        self.btn_off.user_func = self.off_click
        self.set_value(False)
        self.updater = updater

    def set_value(self, value):
        if value:
            self.btn_on._press()
            self.btn_off._force_unpress()
            self.btn_off.unblit_and_reblit()
        else:
            self.btn_on._force_unpress()
            self.btn_on.unblit_and_reblit()
            self.btn_off._press()

    def get_value(self):
        return self.btn_on.toggled

    def on_click(self):
        self.btn_off._force_unpress()
        self.btn_off.unblit_and_reblit()
        if self.updater is not None:
            self.updater()

    def off_click(self):
        self.btn_on._force_unpress()
        self.btn_on.unblit_and_reblit()
        if self.updater is not None:
            self.updater()

class Controller:
   def __init__(self, fullscreen=False, touchscreen=False):
        self.app = MyThorpyApp(size=(800, 600), caption="EMDR Controller", icon='pygame', flags=pygame.FULLSCREEN if fullscreen else 0)
        
        # Example for scaling buttons
        self.buttons = []
        self.create_buttons()
        self.exit_button = self.button(3, 3, 'Exit', self.exit_click)

        self.back = thorpy.Background.make((255, 255, 255), elements=self.buttons + [self.exit_button])
        self.menu = thorpy.Menu(self.back)

    def create_buttons(self):
        width, height = self.app.size
        button_width, button_height = width // 10, height // 20

        # Example: Adjust button size and position based on window size
        self.buttons.append(self.button(0, 0, 'Play', self.start_click, button_width, button_height))
        self.buttons.append(self.button(1, 0, 'Pause', self.pause_click, button_width, button_height))

    def button(self, x, y, title, callback=None, width=100, height=50):
        btn = thorpy.Clickable(title)
        btn.set_size((width, height))
        btn.set_center_pos((x * width + width // 2, y * height + height // 2))
        btn.user_func = callback
        btn.finish()
        return btn

    def update_layout(self):
        """Update button sizes and positions on window resize."""
        width, height = self.app.size
        button_width, button_height = width // 10, height // 20

        for i, btn in enumerate(self.buttons):
            btn.set_size((button_width, button_height))
            btn.set_center_pos((i * button_width + button_width // 2, button_height // 2))

    def exit_click(self):
        """Exit the application."""
        pygame.quit()
        sys.exit()

    def start_click(self):
        print("Start button clicked")

    def pause_click(self):
        print("Pause button clicked")

    def run(self):
        self.app.run()

if __name__ == "__main__":
    controller = Controller(fullscreen=True)
    controller.run()
