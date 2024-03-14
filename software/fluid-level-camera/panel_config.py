import board
import neopixel

class PanelConfig:
    def __init__(self, estimation_type):
        self.LED_COUNT = 256
        self.LED_PIN = board.D18
        self.lights = neopixel.NeoPixel(self.LED_PIN, self.LED_COUNT, brightness=0.25, auto_write=False, pixel_order=neopixel.GRB)
        self.strip = neopixel.NeoPixel(self.LED_PIN, self.LED_COUNT, brightness=0.25, auto_write=False)
        self.num_leds_per_line = 16
        self.set_panel_color(estimation_type)
    
    def set_panel_color(self, estimation_type):
        if estimation_type == "volume":
            for i in range(len(self.strip)):
                line = i // self.num_leds_per_line
                red = 145 - 2 * line
                self.strip[i] = (red, 140, 180)
            self.strip.show()