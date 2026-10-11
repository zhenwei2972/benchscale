"""Build volumes of common printers, so a design can say whether it fits."""

PRINTERS = {
    "bambu_a1_mini": {"name": "Bambu Lab A1 mini", "x": 180, "y": 180, "z": 180},
    "bambu_a1": {"name": "Bambu Lab A1", "x": 256, "y": 256, "z": 256},
    "bambu_p1s": {"name": "Bambu Lab P1S / X1", "x": 256, "y": 256, "z": 256},
    "prusa_mk4": {"name": "Prusa MK4", "x": 250, "y": 210, "z": 220},
    "prusa_mini": {"name": "Prusa MINI+", "x": 180, "y": 180, "z": 180},
    "ender_3": {"name": "Creality Ender-3", "x": 220, "y": 220, "z": 250},
}
DEFAULT_PRINTER = "bambu_a1_mini"
