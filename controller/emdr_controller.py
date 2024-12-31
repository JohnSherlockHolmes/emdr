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
    def __init__(self, caption=None, icon="thorpy", center=True):
        global _SCREEN, _CURRENT_APPLICATION
        _CURRENT_APPLICATION = self
        pygame.init()
        if center:
            os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.set_icon(icon)
        # Use the current display resolution for full-screen mode
        self.size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN)
        if caption:
            pygame.display.set_caption(caption)
        _SCREEN = screen
        self.default_path = "./"

class Container(thorpy.Ghost):
    def set_visible(self, value):
        for elem in self.get_elements():
            elem.set_visible(value)
            elem.set_active(value)

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
    def __init__(self, fullscreen=True, touchscreen=False):
        self.in_load = False
        self.pausing = False
        self.stopping = False
        if touchscreen:
            pygame.mouse.set_cursor((8, 8), (0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0))
        self.app = MyThorpyApp(caption="EMDR Controller", icon='pygame')
        self.screen_width, self.screen_height = self.app.size
        self.create_ui_elements()
        self.config_mode()
        self.reset_action()
        self.activate(self.btn_lightbar)
        self.deactivate(self.btn_lightbar)
        self.activate(self.btn_buzzer)
        self.deactivate(self.btn_buzzer)
        self.check_usb(None)

    def create_ui_elements(self):
        self.btn_start = self.button(0, 0, 'Play', self.start_click)
        self.btn_start24 = self.button(1, 0, 'Play24', self.start24_click)
        self.btn_stop = self.button(2, 0, 'Stop', self.stop_click)
        self.btn_pause = self.button(3, 0, 'Pause', self.pause_click, togglable=True)
        self.btn_lightbar = self.button(0, 1, 'Light', self.lightbar_click, togglable=True)
        self.btn_lightbar.active = False
        self.btn_buzzer = self.button(0, 2, 'Buzzer', self.buzzer_click, togglable=True)
        self.btn_buzzer.active = False
        self.btn_headphone = self.button(0, 3, 'Sound', self.headphone_click, togglable=True)
        # speed area
        self.sel_counter = Selector(2, 1, 'Counter', None, '{0:d}', None, None)
        self.sel_counter.set_value(0)
        self.btn_speed_plus = self.button(3, 2, '+')
        self.btn_speed_minus = self.button(1, 2, '-')
        self.sel_speed = Selector(2, 2, 'Speed', Config.speeds, '{0:d}/min', self.btn_speed_plus, self.btn_speed_minus, self.update_speed)
        self.box_speed = Container(elements=[
            self.sel_counter,
            self.btn_speed_plus,
            self.sel_speed,
            self.btn_speed_minus,
        ])
        # lightbar area
        self.btn_light_on = self.button(1, 1, 'On', togglable=True)
        self.btn_light_off = self.button(2, 1, 'Off', togglable=True)
        self.switch_light = Switch(self.btn_light_on, self.btn_light_off, self.update_light)
        self.btn_light_test = self.button(3, 1, 'Test', self.light_test_click, togglable=True)
        self.btn_light_color_plus = self.button(3, 2, '+')
        self.btn_light_color_minus = self.button(1, 2, '-')
        self.sel_light_color = Selector(2, 2, 'Colour', Config.colors, '{0}', self.btn_light_color_plus, self.btn_light_color_minus, self.update_light, cyclic=True)
        self.btn_light_intens_plus = self.button(3, 3, '+')
        self.btn_light_intens_minus = self.button(1, 3, '-')
        self.sel_light_intens = Selector(2, 3, 'Brightness', Config.intensities, '{0:d}%', self.btn_light_intens_plus, self.btn_light_intens_minus, self.update_light)
        self.box_lightbar = Container(elements=[
            self.btn_light_on,
            self.btn_light_off,
            self.btn_light_test,
            self.btn_light_color_plus,
            self.sel_light_color,
            self.btn_light_color_minus,
            self.btn_light_intens_plus,
            self.sel_light_intens,
            self.btn_light_intens_minus,
        ])
        # buzzer area
        self.btn_buzzer_on = self.button(1, 1, 'On', togglable=True)
        self.btn_buzzer_off = self.button(2, 1, 'Off', togglable=True)
        self.switch_buzzer = Switch(self.btn_buzzer_on, self.btn_buzzer_off, self.update_buzzer)
        self.btn_buzzer_test = self.button(3, 1, 'Test', self.buzzer_test_click)
        self.btn_buzzer_duration_plus = self.button(3, 2, '+')
        self.btn_buzzer_duration_minus = self.button(1, 2, '-')
        self.sel_buzzer_duration = Selector(2, 2, 'Duration', Config.durations, '{0:d} ms', self.btn_buzzer_duration_plus, self.btn_buzzer_duration_minus, self.update_buzzer)
        self.box_buzzer = Container(elements=[
            self.btn_buzzer_on,
            self.btn_buzzer_off,
            self.btn_buzzer_test,
            self.btn_buzzer_duration_plus,
            self.sel_buzzer_duration,
            self.btn_buzzer_duration_minus,
        ])
        # headphone area
        self.btn_headphone_on = self.button(1, 1, 'On', togglable=True)
        self.btn_headphone_off = self.button(2, 1, 'Off', togglable=True)
        self.switch_headphone = Switch(self.btn_headphone_on, self.btn_headphone_off, self.update_sound)
        self.btn_headphone_test = self.button(3, 1, 'Test', self.headphone_test_click)
        self.btn_headphone_volume_plus = self.button(3, 2, '+')
        self.btn_headphone_volume_minus = self.button(1, 2, '-')
        self.sel_headphone_volume = Selector(2, 2, 'Volume', Config.volumes, '{0:d}%', self.btn_headphone_volume_plus, self.btn_headphone_volume_minus, self.update_sound)
        self.btn_headphone_tone_plus = self.button(3, 3, '+')
        self.btn_headphone_tone_minus = self.button(1, 3, '-')
        self.sel_headphone_tone = Selector(2, 3, 'Sound', Config.tones, '{0}', self.btn_headphone_tone_plus, self.btn_headphone_tone_minus, self.update_sound, cyclic=True)
        self.box_headphone = Container(elements=[
            self.btn_headphone_on,
            self.btn_headphone_off,
            self.btn_headphone_test,
            self.btn_headphone_volume_plus,
            self.sel_headphone_volume,
            self.btn_headphone_volume_minus,
            self.btn_headphone_tone_plus,
            self.sel_headphone_tone,
            self.btn_headphone_tone_minus,
        ])
        #
        self.back = thorpy.Background.make((255, 255, 255), elements=[
            self.btn_start,
            self.btn_start24,
            self.btn_stop,
            self.btn_pause,
            self.btn_lightbar,
            self.btn_buzzer,
            self.btn_headphone,
            self.box_speed,
            self.box_lightbar,
            self.box_buzzer,
            self.box_headphone,
        ])
        self.back.add_reaction(thorpy.Reaction(reacts_to=PROBE_EVENT, reac_func=self.check_usb))
        self.back.add_reaction(thorpy.Reaction(reacts_to=ACTION_EVENT, reac_func=self.action))
        self.menu = thorpy.Menu(self.back)

    def button(self, x, y, title, callback=None, togglable=False):
        try:
            painter = thorpy.painters.imageframe.ButtonImage(
                img_normal=os.path.join('imgs', '%s_normal.png' % title.lower()),
                img_pressed=os.path.join('imgs', '%s_pressed.png' % title.lower())
            )
        except:
            painter = thorpy.painters.imageframe.ButtonImage(
                img_normal=os.path.join('imgs', '%s_normal.png' % 'default'),
                img_pressed=os.path.join('imgs', '%s_pressed.png' % 'default')
            )
        try:
            inactive_painter = thorpy.painters.imageframe.ButtonImage(
                img_normal=os.path.join('imgs', '%s_inactive.png' % title.lower())
            )
        except:
            inactive_painter = thorpy.painters.imageframe.ButtonImage(
                img_normal=os.path.join('imgs', '%s_inactive.png' % 'default')
            )
        if togglable:
            btn = thorpy.Togglable('')
        else:
            btn = thorpy.Clickable('')
        btn.normal_painter = painter
        btn.inactive_painter = inactive_painter
        btn.set_painter(painter)
        btn.user_func = callback
        btn.finish()
        # Scale position based on screen size
        btn.set_center_pos((self.screen_width // 6 + self.screen_width // 3 * x, self.screen_height // 8 + self.screen_height // 4 * y))
        return btn
