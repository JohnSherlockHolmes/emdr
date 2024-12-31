import pygame
import thorpy

# Mock Devices class
class Devices:
    @staticmethod
    def set_led(value):
        print(f"LED set to: {value}")

    @staticmethod
    def set_buzzer_duration(duration):
        print(f"Buzzer duration set to: {duration} ms")

    @staticmethod
    def set_tone(frequency, duration, volume):
        print(f"Tone set: {frequency} Hz, Duration: {duration}, Volume: {volume}%")

    @staticmethod
    def do_buzzer(state):
        print(f"Buzzer {'ON' if state else 'OFF'}")

    @staticmethod
    def do_sound(state):
        print(f"Sound {'ON' if state else 'OFF'}")

# Configuration mock
class Config:
    speeds = [60, 120, 180]  # Beats per minute
    durations = [500, 1000, 1500]  # Milliseconds
    tones = [("Low", 440, 500), ("High", 880, 500)]
    volumes = [50, 75, 100]  # Percentage

# Main Controller
class Controller:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((480, 320))
        pygame.display.set_caption("EMDR Controller")
        self.running = False

        # ThorPy elements
        self.speed_selector = thorpy.BrowserLike.make("Speed", Config.speeds, fmt="{0} BPM")
        self.duration_selector = thorpy.BrowserLike.make("Duration", Config.durations, fmt="{0} ms")
        self.tone_selector = thorpy.BrowserLike.make("Tone", Config.tones, fmt="{0[0]}")
        self.volume_selector = thorpy.BrowserLike.make("Volume", Config.volumes, fmt="{0}%")

        self.start_button = thorpy.make_button("Start", func=self.start_click)
        self.stop_button = thorpy.make_button("Stop", func=self.stop_click)

        # Organizing GUI
        self.panel = thorpy.Box.make(elements=[
            self.speed_selector,
            self.duration_selector,
            self.tone_selector,
            self.volume_selector,
            self.start_button,
            self.stop_button,
        ])

        # Finalize GUI layout
        thorpy.store(self.panel)
        self.panel.center()
        self.menu = thorpy.Menu(self.panel, fps=60)

    def start_click(self):
        speed = self.speed_selector.get_value()
        duration = self.duration_selector.get_value()
        tone = self.tone_selector.get_value()
        volume = self.volume_selector.get_value()
        print(f"Start: Speed={speed}, Duration={duration}, Tone={tone}, Volume={volume}")

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
        self.panel.blit()
        self.panel.update()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                self.menu.react(event)

# Run the Controller
if __name__ == "__main__":
    controller = Controller()
    controller.run()
