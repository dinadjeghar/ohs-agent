"""Simulated plant: environmental sensors (as an ESP32/MQTT feed would deliver) and worker state."""
import random
from dataclasses import dataclass, field


@dataclass
class Plant:
    seed: int = 7
    tick: int = 0
    rng: random.Random = field(init=False)

    def __post_init__(self):
        self.rng = random.Random(self.seed)

    def zones(self):
        return ["Zone A - Compressor Room", "Zone B - Welding Bay", "Zone C - Tank Farm"]

    def read_zone(self, zone: str) -> dict:
        r = self.rng
        base = {
            "co_ppm": r.gauss(8, 2),
            "h2s_ppm": max(0.0, r.gauss(1, 0.5)),
            "lel_pct": max(0.0, r.gauss(2, 1)),
            "o2_pct": r.gauss(20.9, 0.15),
            "noise_dba": r.gauss(78, 3),
            "temp_c": r.gauss(27, 1.5),
        }
        # Scripted incidents so the demo tells a story.
        if "Compressor" in zone:
            base["noise_dba"] = r.gauss(93, 2)
            base["co_ppm"] = r.gauss(41, 4)
        if "Welding" in zone:
            base["temp_c"] = r.gauss(36, 1.5)
            base["co_ppm"] = r.gauss(22, 3)
        if "Tank" in zone:
            base["h2s_ppm"] = r.gauss(24, 3)
            base["lel_pct"] = r.gauss(12, 2)
            base["o2_pct"] = r.gauss(19.2, 0.1)
        return {k: round(v, 2) for k, v in base.items()}

    def workers(self):
        return [
            {"id": "W-101", "zone": "Zone A - Compressor Room", "task": "general",
             "ppe_detected": ["helmet", "vest", "boots"], "perclos": 0.08, "shift_hours": 4.5},
            {"id": "W-102", "zone": "Zone B - Welding Bay", "task": "welding",
             "ppe_detected": ["helmet", "gloves", "boots"], "perclos": 0.22, "shift_hours": 9.0},
            {"id": "W-103", "zone": "Zone C - Tank Farm", "task": "confined_space",
             "ppe_detected": ["helmet", "boots"], "perclos": 0.34, "shift_hours": 11.0},
        ]
