"""How-to animation for a shake_fill_rack, rendered headless in Blender.

    blender -b -P tools/howto_video.py -- ASSETS_DIR FRAMES_DIR [all | f1,f2,...]

ASSETS_DIR comes from tools/export_video_assets.py (the printed parts, one tip
and their layout, at true scale; 1 Blender unit = 1 mm). The motion is
keyframed to show the steps, not simulated: the end card says so.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
ASSETS, FRAMES = Path(argv[0]), Path(argv[1])
WHICH = argv[2] if len(argv) > 2 else "all"
LAY = json.loads((ASSETS / "layout.json").read_text())
FPS, END = 30, 1590
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
random.seed(7)

Hs, PEAKS, LID_SEAT = LAY["stand_height"], LAY["deck_peaks"], LAY["lid_seat"]
TIP = LAY["tip"]
L, FLOOR, CH = TIP["length"], TIP["floor"], TIP["collar_h"]
SEATED_Z = LAY["seated_point_z"]
DECK_TOP = Hs + PEAKS
(sx0, sy0, _), (sx1, sy1, _) = LAY["bounds"]["stand"]
CX, CY = (sx0 + sx1) / 2, (sy0 + sy1) / 2

# --- scene ----------------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, END
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
scene.render.engine = next(e for e in engines if "EEVEE" in e)
try:
    scene.eevee.taa_render_samples = 24
except AttributeError:
    pass
try:
    scene.view_settings.view_transform = "Standard"
except TypeError:
    pass
scene.render.image_settings.file_format = "PNG"

world = bpy.data.worlds.new("world")
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.78, 0.81, 0.86, 1)
bg.inputs["Strength"].default_value = 0.55


def material(name, rgb, rough=0.5, emit=False, alpha=1.0, blended=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    if blended:     # smooth transparency instead of dithered grain
        try:
            m.surface_render_method = "BLENDED"
        except (AttributeError, TypeError):
            m.blend_method = "BLEND"
    nt = m.node_tree
    if emit:
        for n in list(nt.nodes):
            if n.type != "OUTPUT_MATERIAL":
                nt.nodes.remove(n)
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (*rgb, 1)
        e.inputs["Strength"].default_value = 1.0
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        if alpha < 1.0:
            t = nt.nodes.new("ShaderNodeBsdfTransparent")
            mix = nt.nodes.new("ShaderNodeMixShader")
            mix.inputs[0].default_value = alpha
            nt.links.new(t.outputs[0], mix.inputs[1])
            nt.links.new(e.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], out.inputs["Surface"])
        else:
            nt.links.new(e.outputs[0], out.inputs["Surface"])
        return m
    p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Alpha"].default_value = alpha
    return m


PLA = material("PLA white", (0.82, 0.80, 0.76), 0.6)
LID = material("PLA white lid", (0.82, 0.80, 0.76), 0.6, blended=True)
TIPM = material("tip yellow", (0.98, 0.78, 0.12), 0.3)
BENCH = material("bench", (0.30, 0.33, 0.38), 0.75)


def import_stl(path: Path, name: str, mat):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=str(path))
    obj = (set(bpy.data.objects) - before).pop()
    obj.name = name
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    scene.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


def adopt(child, parent):
    child.parent = parent
    child.matrix_parent_inverse.identity()


def key(obj, frame, loc=None, rot=None):
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rot
        obj.keyframe_insert("rotation_euler", frame=frame)


def show(obj, frames_on):
    """Visible only inside the given (start, end) frame ranges."""
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=1)
    for a, b in frames_on:
        obj.hide_render = False
        obj.keyframe_insert("hide_render", frame=a)
        obj.hide_render = True
        obj.keyframe_insert("hide_render", frame=b)


bpy.ops.mesh.primitive_plane_add(size=1200, location=(CX, CY, -0.01))
bench = bpy.context.active_object
bench.data.materials.append(BENCH)

sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
scene.collection.objects.link(sun)
sun.data.energy, sun.data.angle = 2.4, math.radians(8)
sun.rotation_euler = (math.radians(38), math.radians(-18), math.radians(-35))
fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
scene.collection.objects.link(fill)
fill.data.energy = 0.45
fill.rotation_euler = (math.radians(60), math.radians(30), math.radians(150))

# --- the rig: pivot (tilt about the left bottom edge) > rack (shake) > parts and tips ---------
pivot = empty("pivot", (sx0, CY, 0))
rack = empty("rack", (-sx0, -CY, 0), parent=pivot)
stand = import_stl(ASSETS / "stand.stl", "stand", PLA)
deck = import_stl(ASSETS / "deck.stl", "deck", PLA)
lid = import_stl(ASSETS / "lid.stl", "lid", LID)
for o in (stand, deck):      # the lid moves on its own, so it does not tilt when parked
    adopt(o, rack)
tip_mesh = import_stl(ASSETS / "tip.stl", "tip_source", TIPM)
tip_mesh.hide_render = True


def new_tip(name):
    o = bpy.data.objects.new(name, tip_mesh.data)
    scene.collection.objects.link(o)
    adopt(o, rack)
    return o


def lying_pose(i, layer):
    yaw = math.radians(random.uniform(-6, 6) + (38 if i % 2 else 180 - 38))
    elev = math.radians(random.uniform(8, 22))
    th = math.pi / 2 - elev
    d = Vector((math.sin(th) * math.cos(yaw), math.sin(th) * math.sin(yaw), math.cos(th)))
    centre = Vector((CX + random.uniform(-2, 2), CY + random.uniform(-2, 2), DECK_TOP + 4.5 + 4.2 * layer))
    point = centre - d * (L / 2)
    return point, (0.0, th, yaw)


# --- the story ------------------------------------------------------------------------------
# 0. the three printed parts on the bench
key(deck, 1, loc=(sx1 + 26, 0, 0))
key(lid, 1, loc=(sx0 - 70, 0, 0))
# 1. deck into the stand
key(deck, 120, loc=(sx1 + 26, 0, 0))
key(deck, 150, loc=(sx1 + 26, 0, Hs + 30))
key(deck, 180, loc=(0, 0, Hs + 30))
key(deck, 208, loc=(0, 0, Hs))

# 2. fit check: one tip per column, front row
front = [c for c in LAY["centres"] if c[3] == LAY["rows"] - 1]
fit_tips = []
for i, (x, y, col, _) in enumerate(front):
    t = new_tip(f"fit_{col + 1}")
    f0 = 262 + 22 * i
    key(t, 1, loc=(x, y, SEATED_Z + 120), rot=(0, 0, 0))
    key(t, f0, loc=(x, y, SEATED_Z + 120), rot=(0, 0, 0))
    if col == 0:        # hole too small: sits high, leaning
        key(t, f0 + 24, loc=(x, y, SEATED_Z + 4.0), rot=(math.radians(-7), 0, 0))
    elif col == len(front) - 1:   # hole too big: wobbles
        key(t, f0 + 24, loc=(x, y, SEATED_Z - 0.2), rot=(0, 0, 0))
        for k, f in enumerate(range(f0 + 30, 440, 8)):
            key(t, f, rot=(0, math.radians(6 if k % 2 else -6), 0))
        key(t, 444, rot=(0, 0, 0))
    else:
        key(t, f0 + 24, loc=(x, y, SEATED_Z), rot=(0, 0, 0))
    key(t, 448, loc=t.location.copy())
    key(t, 470, loc=(x, y, SEATED_Z + 160))
    show(t, [(f0, 471)])
    fit_tips.append(t)

# 3. pour 18 tips; 4. lid on; 5. shake: 12 drop in point first, 1 nests, 5 stay loose
holes = LAY["centres"]
order = list(range(len(holes)))
random.shuffle(order)
tips = []
for i in range(18):
    t = new_tip(f"tip_{i + 1:02d}")
    point, rot = lying_pose(i, i // 6)
    f_land = 505 + 5 * i
    start = point + Vector((random.uniform(-15, 15), random.uniform(-15, 15), 130))
    key(t, 1, loc=start, rot=(rot[0] + 0.6, rot[1] - 0.5, rot[2] + 0.8))
    key(t, f_land - 22, loc=start, rot=(rot[0] + 0.6, rot[1] - 0.5, rot[2] + 0.8))
    key(t, f_land, loc=point, rot=rot)
    tips.append((t, point, rot))

lid_mat_alpha = next(n for n in LID.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
key(lid, 650, loc=(sx0 - 70, 0, 0))
key(lid, 680, loc=(sx0 - 70, 0, LID_SEAT + 45))
key(lid, 708, loc=(0, 0, LID_SEAT + 45))
key(lid, 730, loc=(0, 0, LID_SEAT))
for f, a in ((732, 1.0), (746, 0.28), (972, 0.28), (986, 1.0)):
    lid_mat_alpha.default_value = a
    lid_mat_alpha.keyframe_insert("default_value", frame=f)

shake_start, shake_end = 748, 966
for f in range(shake_start, shake_end + 1, 2):
    ramp = min(1.0, (f - shake_start) / 20, (shake_end - f) / 20)
    dx = 9.0 * ramp * math.sin(2 * math.pi * 2.6 * (f - shake_start) / FPS)
    key(rack, f, loc=(-sx0 + dx, -CY, 0))
    key(lid, f, loc=(dx, 0, LID_SEAT))           # held on: it shakes with the rack
key(rack, shake_end + 2, loc=(-sx0, -CY, 0))
key(lid, shake_end + 2, loc=(0, 0, LID_SEAT))

for k, idx in enumerate(order):
    t, point, rot = tips[k]
    x, y, _, _ = holes[idx]
    f0 = 768 + 13 * k
    # lean towards the far corner of the lid, point into the hole, then upright
    corners = [(sx0, sy0), (sx1, sy0), (sx0, sy1), (sx1, sy1)]
    fx, fy = max(corners, key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)
    yaw = math.atan2(fy - y, fx - x)
    key(t, f0, loc=point, rot=rot)
    key(t, f0 + 8, loc=(x, y, DECK_TOP + 1.0), rot=(0, math.radians(60), yaw))
    key(t, f0 + 15, loc=(x, y, DECK_TOP - 12.0), rot=(0, math.radians(28), yaw))
    key(t, f0 + 24, loc=(x, y, SEATED_Z), rot=(0, 0, yaw))
nest_t, nest_point, nest_rot = tips[12]
nx, ny, _, _ = holes[order[4]]
key(nest_t, 905, loc=nest_point, rot=nest_rot)
key(nest_t, 918, loc=(nx - 1.5, ny, DECK_TOP + 14), rot=(0, math.radians(35), nest_rot[2]))
key(nest_t, 930, loc=(nx, ny, SEATED_Z + 10.5), rot=(0, 0, nest_rot[2]))
loose = tips[13:]
for j, (t, point, rot) in enumerate(loose):
    for f in range(shake_start + 6 * j, shake_end, 24):
        jig = Vector((random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5), 0))
        key(t, f, loc=point + jig, rot=(rot[0], rot[1], rot[2] + random.uniform(-0.12, 0.12)))
    # after the shake the extras lie across the seated collars
    rest = point.copy()
    rest.z = Hs + FLOOR + CH + 1.6 + 1.0 * j
    key(t, shake_end, loc=rest, rot=rot)

# 6. lid off
key(lid, 990, loc=(0, 0, LID_SEAT))
key(lid, 1018, loc=(0, 0, LID_SEAT + 55))
PARK = (sx1 - sx0) + 28           # the lid parks on the right, clear of the pour
key(lid, 1048, loc=(PARK, 0, LID_SEAT + 55))
key(lid, 1070, loc=(PARK, 0, 0))

# 7. tilt to pour the extras back (not upside down)
key(pivot, 1100, rot=(0, 0, 0))
key(pivot, 1138, rot=(0, math.radians(-35), 0))
key(pivot, 1222, rot=(0, math.radians(-35), 0))
key(pivot, 1258, rot=(0, 0, 0))
for j, (t, point, rot) in enumerate(loose):
    rest = t.location.copy()
    f0 = 1134 + 6 * j
    key(t, f0, loc=rest)
    key(t, f0 + 26, loc=(sx0 - 30, rest.y, rest.z + 2))
    key(t, f0 + 50, loc=(sx0 - 70, rest.y, rest.z - 80))
    show(t, [(480, f0 + 50)])

# 8. pick out the one standing high
key(nest_t, 1318, loc=(nx, ny, SEATED_Z + 10.5))
key(nest_t, 1346, loc=(nx, ny, SEATED_Z + 70))
key(nest_t, 1370, loc=(nx + 60, ny - 40, SEATED_Z + 90))
show(nest_t, [(480, 1371)])
for t, _, _ in tips[:12]:
    show(t, [(480, END + 1)])

# --- camera ---------------------------------------------------------------------------------
cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.lens, cam.data.clip_start, cam.data.clip_end = 50, 1, 5000
target = empty("target")
track = cam.constraints.new("TRACK_TO")
track.target, track.track_axis, track.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
shots = [   # frame, camera location, look-at
    (1, (CX - 150, CY - 330, 200), (CX + 2, CY, 22)),
    (210, (CX - 150, CY - 330, 200), (CX + 2, CY, 22)),
    (250, (CX - 34, CY - 118, 112), (CX, CY - 4, 47)),
    (450, (CX - 26, CY - 112, 112), (CX, CY - 4, 47)),
    (500, (CX - 125, CY - 250, 165), (CX, CY, 32)),
    (980, (CX - 115, CY - 255, 170), (CX, CY, 34)),
    (1090, (CX - 120, CY - 300, 175), (CX + 5, CY, 26)),
    (1262, (CX - 120, CY - 300, 175), (CX + 5, CY, 26)),
    (1300, (CX - 70, CY - 140, 140), (CX, CY, 52)),
    (1470, (CX + 95, CY - 120, 140), (CX, CY, 52)),
    (END, (CX + 105, CY - 110, 140), (CX, CY, 52)),
]
for f, c, t in shots:
    key(cam, f, loc=c)
    key(target, f, loc=t)

# --- captions, fixed to the camera ---------------------------------------------------------
HUD_D = 10.0
FW, FH = HUD_D * 36 / 50, HUD_D * 36 / 50 * 720 / 1280
WHITE = material("hud white", (1, 1, 1), emit=True)
BAR = material("hud bar", (0.02, 0.03, 0.05), emit=True, alpha=0.78, blended=True)


def hud_plane(name, w, h, x, y, mat):
    bpy.ops.mesh.primitive_plane_add(size=1)
    p = bpy.context.active_object
    p.name, p.scale = name, (w, h, 1)
    p.data.materials.append(mat)
    p.parent = cam
    p.location = (x, y, -HUD_D - 0.01)
    p.visible_shadow = False
    return p


def hud_text(name, body, size, x, y, bold=False, align="LEFT"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT_BOLD if bold else FONT, check_existing=True)
    cu.size, cu.align_x, cu.align_y = size, align, "TOP"
    o = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(o)
    o.data.materials.append(WHITE)
    o.parent = cam
    o.location = (x, y, -HUD_D)
    o.visible_shadow = False
    return o


STEPS = [
    (108, 225, "1   Drop the deck into the stand", "It fits one way only: the cut corner goes at the back left."),
    (226, 478, "2   First time only: one tip in each column",
     "Holes 5.65 / 5.95 / 6.25 / 6.55 mm (1-4 dots on the front). Use the column where the tip stands\n"
     "upright with its collar down in the pocket. Too small: it sits high. Too big: it wobbles."),
    (479, 640, "3   Pour on about 1.5x as many tips as holes", "Here: 18 loose tips for 12 holes."),
    (641, 742, "4   Put the lid on", ""),
    (743, 980, "5   Hold the lid down and shake side to side, 10-20 s",
     "Lid drawn see-through. Tips can only go in point first; full holes stand proud,\n"
     "so loose tips slide off them and into the empty ones."),
    (981, 1086, "6   Lift the lid", ""),
    (1087, 1290, "7   Tilt to pour the extras back into the bag",
     "Tilt, do not turn it over: seated tips stay in their pockets."),
    (1291, 1470, "8   Pick out any tip standing high, fill gaps by hand",
     "A tip stacked inside another stands about 10 mm higher. Then load your pipette from the rack."),
]
bar = hud_plane("bar", FW, FH * 0.2, 0, -FH * 0.4, BAR)
show(bar, [(108, 1471)])
for i, (a, b, title, detail) in enumerate(STEPS):
    t1 = hud_text(f"step{i}", title, FH * 0.052, -FW / 2 + FW * 0.035, -FH * 0.315, bold=True)
    show(t1, [(a, b + 1)])
    if detail:
        t2 = hud_text(f"step{i}d", detail, FH * 0.036, -FW / 2 + FW * 0.035, -FH * 0.385)
        show(t2, [(a, b + 1)])

card = hud_plane("card", FW, FH, 0, 0, BAR)
show(card, [(1, 107), (1471, END + 1)])
for name, body, size, y, bold, rng in [
    ("title", "Filling tips with the shake-fill rack", FH * 0.075, FH * 0.12, True, [(1, 107)]),
    ("subtitle", "Your 12-hole test print: deck, stand and lid. Axygen 200 uL tips.\n"
                 "True-scale animation of the printed parts.", FH * 0.04, -FH * 0.02, False, [(1, 107)]),
    ("endtitle", "Load, shake, lift, tilt, check.", FH * 0.07, FH * 0.16, True, [(1471, END + 1)]),
    ("endnote", "Keyframed animation of the CAD model at true scale: not a recording,\n"
                "not a physics simulation. Tip sizes are ESTIMATED for Axygen T-200-Y.\n"
                "Fill rate is not measured yet: try the coupon and log what you see.",
     FH * 0.038, FH * 0.02, False, [(1471, END + 1)]),
]:
    show(hud_text(name, body, size, 0, y, bold=bold, align="CENTER"), rng)

# --- render ---------------------------------------------------------------------------------
FRAMES.mkdir(parents=True, exist_ok=True)
frames = range(1, END + 1) if WHICH == "all" else [int(f) for f in WHICH.split(",")]
for f in frames:
    scene.frame_set(f)
    scene.render.filepath = str(FRAMES / f"{f:04d}.png")
    bpy.ops.render.render(write_still=True)
print("rendered", len(frames), "frames to", FRAMES)
