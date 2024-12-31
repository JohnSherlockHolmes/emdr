import pygame
import thorpy
from time import sleep
import os

# Constants for custom Pygame events
PROBE_EVENT = pygame.USEREVENT + 1
ACTION_EVENT = pygame.USEREVENT + 2

# Mock Devices module
class Devices:
    @staticmethod
    def set_led(value):
        print(f"LED set to: {value}")

    @staticmethod
    def set_buzzer_duration(duration):
        print(f"Buzzer duration set to: {duration} ms")

    @staticmethod
    def set_tone(frequency, duration, volume):
        print(f"Tone set: {frequency} Hz, {duration} ms, Volume: {volume * 100}%")

    @staticmethod
    def do_buzzer(state):
        print(f"Buzzer {'ON' if state else 'OFF'}")

    @staticmethod
    def do_sound(state):
        print(f"Sound {'ON' if state else 'OFF'}")

# Config mock
class Config:
    speeds = [60, 120, 180]  # Speeds in beats/min
    durations = [500, 1000, 1500]  # Durations in ms
    tones = [('Low', 440, 500), ('High', 880, 500)]
    volumes = [50, 75, 100]  # Volumes in %
    colors = [('Red', 255, 0, 0), ('Green', 0, 255, 0), ('Blue', 0, 0, 255)]

    data = {}

    @staticmethod
    def save():
        print("Config saved.")

    @staticmethod
    def load():
        print("Config loaded.")

# Simple Application class
class MyThorpyApp(thorpy.Application):
    def __init__(self, size, caption=None, flags=0):
        pygame.init()
        self.size = tuple(size)
        self.caption = caption
        screen = pygame.display.set_mode(self.size, flags)
        if self.caption:
            pygame.display.set_caption(caption)

# Main Controller
class Controller:
    def __init__(self):
        self.app = MyThorpyApp(size=(480, 320), caption="EMDR Controller")
        self.speed_selector = self.create_selector((1, 1), "Speed", Config.speeds, "{0} BPM")
        self.duration_selector = self.create_selector((1, 2), "Duration", Config.durations, "{0} ms")
        self.tone_selector = self.create_selector((1, 3), "Tone", Config.tones, "{0[0]}")
        self.volume_selector = self.create_selector((1, 4), "Volume", Config.volumes, "{0}%")

        self.start_button = self.create_button((2, 1), "Start", self.start_click)
        self.stop_button = self.create_button((2, 2), "Stop", self.stop_click)

        self.back = thorpy.Background.make((255, 255, 255), elements=[
            self.speed_selector, self.duration_selector,
            self.tone_selector, self.volume_selector,
            self.start_button, self.stop_button
        ])

        self.menu = thorpy.Menu(self.back)
        self.running = False

    def create_button(self, pos, text, callback):
        btn = thorpy.Clickable(text)
        btn.set_center((100 * pos[0], 50 * pos[1]))
        btn.user_func = callback
        return btn

    def create_selector(self, pos, title, values, fmt):
        elem = thorpy.Element(title)
        elem.set_center((100 * pos[0] - 50, 50 * pos[1]))
        selector = thorpy.BrowserLike.make(title, values, fmt)
        selector.set_center((100 * pos[0] + 50, 50 * pos[1]))
        return selector

    def start_click(self):
        speed = self.speed_selector.get_value()
        duration = self.duration_selector.get_value()
        tone = self.tone_selector.get_value()
        volume = self.volume_selector.get_value()
        print(f"Start clicked: Speed={speed}, Duration={duration}, Tone={tone}, Volume={volume}")

        # Example device action
        Devices.set_led(1)
        Devices.set_buzzer_duration(duration)
        Devices.set_tone(tone[1], tone[2], volume / 100)
        self.running = True

    def stop_click(self):
        print("Stop clicked.")
        Devices.set_led(0)
        Devices.do_buzzer(False)
        Devices.do_sound(False)
        self.running = False

    def run(self):
        self.menu.play()
        self.app.quit()

# Run the Controller
if __name__ == "__main__":
    controller = Controller()
    controller.run()