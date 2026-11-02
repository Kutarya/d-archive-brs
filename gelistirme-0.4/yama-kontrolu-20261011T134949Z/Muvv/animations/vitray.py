import threading

from animations.layer import Layer


class Vitray:
    def __init__(self, zone_map):
        self.zone_map = zone_map
        self.layers = []
        self.led_count = zone_map.led_count
        self.lock = threading.RLock()

    def add_layer(self, layer):
        if not isinstance(layer, Layer):
            raise TypeError("Expected a Layer.")
        with self.lock:
            self.layers.append(layer)

    def replace_layers(self, layers):
        layers = list(layers)
        if any(not isinstance(layer, Layer) for layer in layers):
            raise TypeError("Expected Layers.")
        with self.lock:
            self.layers[:] = layers

    def clear_layers(self):
        self.replace_layers([])

    def render(self):
        with self.lock:
            frame = [(0, 0, 0)] * self.led_count
            for layer in self.layers:
                if layer.enabled and layer.effect.enabled:
                    frame = layer.process(frame, self.led_count, self.zone_map.positions)
            return frame
