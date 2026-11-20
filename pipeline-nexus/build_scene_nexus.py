# build_scene_nexus_ep3.py — NEXUS ZERO Episode 3 "THE CHOICE" (vinyl-toy stylized).
# Copy build_scene_nexus_ep2.py, adaptasi Ep 3 (bukan dari nol).
# 2 set: ruang inti NEXUS (RX=80, MONUMENTAL 60x48 m, dinding 16 m, wajah
# hologram ~12 m, 12 kolom circuitry 14 m, gerbang cahaya putih 5x6 m yang
# TERBUKA PENUH sejak S1 — gate_open=1 konstan, tanpa animasi celah) + ISI
# gerbang: AULA MEMORI putih tanpa ujung (lantai reflektif putih, 213 Kairo
# membeku sebagai instans collection, kabut putih tipis).
# TIDAK ADA kota aerial di Ep 3. TIDAK ADA teks 3D judul di set (judul hanya ASS).
# 4 karakter lock DESIGN-v1.md: KAIRO (1.8 m, bekas luka alis kiri WAJIB, kilau
# biru TERANG emisi 2.0 sejak S3, backpack tergeletak di lantai, data core di
# soket), NEXUS (wajah hologram merah partikel ~12 m + wajah kecil dari dalam
# aula S8), EVA (silver-white, mata biru — SATU-SATUNYA biru), SENTINEL (logam
# hitam 2.2 m, sensor merah; BERHENTI di ambang gerbang S3, tidak masuk).
# Pelajaran fix Ep 2 (berlaku lagi): fitur wajah NEXUS di DEPAN permukaan bola
# (mata y=22.32 vs permukaan ~22.4); luka tipis 0,07 warna gelap; kilau biru
# harus terbaca; GATE_M 1,2; aula putih jangan blown-out (GATE_M 0,9).
# Render setup B7: Eevee, samples env FS_SAMPLES default 6, ray OFF, volumetrics
# tile 16, DOF ON, motion blur ON, subsurf 1, bevel 0, AgX. World strength 0.45,
# kabut 0.02 ruang inti / 0.01 aula memori.
# Run:
#   blender -b --factory-startup -P build_scene_nexus_ep3.py -- <out.png> [--res 540 960]
import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = args[0] if args else "//nexus_ep3_preview.png"
RES_X, RES_Y = (540, 960)
if "--res" in args:
    i = args.index("--res")
    RES_X, RES_Y = int(args[i + 1]), int(args[i + 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- render setup B7 ----------
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "None"


def _set(obj, attr, value):
    if hasattr(obj, attr):
        setattr(obj, attr, value)


_set(scene.eevee, "use_raytracing", os.environ.get("FS_RAY", "0") == "1")
_set(scene.eevee, "use_shadows", True)
_set(scene.eevee, "volumetric_tile_size", os.environ.get("FS_VOLTILE", "16"))
_set(scene.eevee, "volumetric_end", 60.0)
scene.eevee.taa_render_samples = int(os.environ.get("FS_SAMPLES", "6"))
scene.render.use_motion_blur = os.environ.get("FS_MB", "1") == "1"
_set(scene.render, "motion_blur_shutter", 0.5)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.055, 0.059, 0.067, 1.0)  # langit malam #0E0F11
bg.inputs["Strength"].default_value = 0.45  # malam jauh lebih gelap


# ---------- materials ----------
def mat(name, rgb, rough=0.45, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


def halo_mat(name, rgb, strength, alpha_center):
    """Emissive transparan dengan falloff radial (alpha penuh di tengah,
    memudar -> 0 di tepi) — hologram tanpa tepi persegi yang keras."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    b.inputs["Roughness"].default_value = 1.0
    tex = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "RADIAL"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    # Jarak radial di koordinat Generated: tepi tengah panel ~0.5, sudut ~0.7.
    # Fade HARUS selesai di 0.45 supaya tidak ada tepi persegi yang tersisa
    # (stop 0.55/0.85 sebelumnya membuat tepi panel tetap alpha penuh).
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (alpha_center, alpha_center, alpha_center, 1.0)
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    mid = ramp.color_ramp.elements.new(0.20)
    mid.color = (alpha_center, alpha_center, alpha_center, 1.0)
    nt.links.new(tex.outputs["Generated"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Alpha"])
    m.blend_method = "BLEND"
    return m


# --- Kairo ---
SKIN_KAI = mat("SkinKairo", (0.79, 0.63, 0.51), 0.5)          # #C9A186
HAIR_KAI = mat("HairKairo", (0.05, 0.05, 0.06), 0.6)
JACKET = mat("JacketKairo", (0.12, 0.13, 0.15), 0.6)          # #1E2126
JACKET2 = mat("JacketRes1", (0.16, 0.14, 0.12), 0.6)
JACKET3 = mat("JacketRes2", (0.10, 0.13, 0.16), 0.6)
SHIRT = mat("ShirtKairo", (0.16, 0.16, 0.18), 0.6)
PANTS_K = mat("PantsKairo", (0.08, 0.09, 0.10), 0.6)          # #14161A
BOOTS = mat("BootsKairo", (0.16, 0.13, 0.09), 0.55)           # #2A2118
BACKPACK_M = mat("Backpack", (0.14, 0.15, 0.17), 0.6)         # #23262B
STRIP_BLUE = emissive("StripBlue", (0.18, 0.42, 1.0), 0.6)    # #2E6BFF lemah
EYE_DARK = mat("EyeDark", (0.05, 0.03, 0.02), 0.2)            # mata cokelat gelap Kairo
# --- EVA ---
SKIN_EVA = mat("SkinEva", (0.85, 0.87, 0.89), 0.25, metal=0.6)  # silver-white #D8DDE3
SUIT_EVA = mat("SuitEva", (0.88, 0.89, 0.91), 0.3, metal=0.4)
EYE_BLUE = emissive("EyeBlue", (0.30, 0.65, 1.0), 1.2)       # #4DA6FF — satu-satunya biru
CIRCUIT_BLUE = emissive("CircuitBlue", (0.30, 0.65, 1.0), 0.5)
# --- Sentinel ---
METAL_SEN = mat("MetalSentinel", (0.05, 0.06, 0.06), 0.35, metal=0.9)  # #0D0E10
METAL_SEN2 = mat("MetalSentinel2", (0.10, 0.11, 0.12), 0.3, metal=0.9)
SENSOR_OFF = mat("SensorOff", (0.08, 0.02, 0.02), 0.3)
SENSOR_RED = emissive("SensorRed", (1.0, 0.0, 0.0), 0.9)     # AgX: merah hanya di luminansi rendah (1.2 masih salmon)
# --- NEXUS ---
NEXUS_RED = emissive("NexusRed", (1.0, 0.10, 0.10), 0.8)     # #FF1A1A wajah hologram (1.2 masih pucat di AgX)
NEXUS_EYE = emissive("NexusEye", (1.0, 0.05, 0.05), 0.9)
NEXUS_GLOW = emissive("NexusGlow", (0.55, 0.02, 0.02), 0.5)
NEXUS_HEAD = mat("NexusHead", (0.12, 0.02, 0.02), 0.5)       # siluet kepala gelap (fitur di depannya)
NEXUS_HEAD.use_nodes = True
_nb = NEXUS_HEAD.node_tree.nodes["Principled BSDF"]
_nb.inputs["Emission Color"].default_value = (0.55, 0.02, 0.02, 1.0)
_nb.inputs["Emission Strength"].default_value = 0.3
NEXUS_DOT = emissive("NexusDot", (1.0, 0.12, 0.12), 1.0)     # partikel wajah
NEXUS_DOT_DIM = emissive("NexusDotDim", (1.0, 0.12, 0.12), 0.45)  # partikel redup (variasi awan)
# wajah BESAR ruang inti (bukan layar kota): mata pekat + halo transparan.
# NEXUS_EYE_BIG: base diffuse GELAP supaya emisi dominan — mata tetap merah
# pekat di AgX, tidak tercuci jadi pink pucat oleh cahaya sekitar.
NEXUS_EYE_BIG = emissive("NexusEyeBig", (1.0, 0.0, 0.0), 0.7)
_nb2 = NEXUS_EYE_BIG.node_tree.nodes["Principled BSDF"]
_nb2.inputs["Base Color"].default_value = (0.30, 0.0, 0.0, 1.0)
# bola mata besar kena specular dari area light depan (CoreFill) -> kilau
# putih menutupi merahnya (mata Sentinel kecil di f_0032 tidak kena ini).
# Matikan specular: mata harus merah pekat, bukan pink pucat.
_nb2.inputs["Roughness"].default_value = 1.0
if "Specular IOR Level" in _nb2.inputs:
    _nb2.inputs["Specular IOR Level"].default_value = 0.0
NEXUS_HALO = halo_mat("NexusHalo", (1.0, 0.08, 0.08), 0.55, 0.4)      # panel wajah: transparan, tepi memudar
NEXUS_EYE_GLOW = halo_mat("NexusEyeGlow", (1.0, 0.06, 0.06), 0.5, 0.4)  # glow samar di belakang mata
SCAN_M = emissive("ScanLine", (1.0, 0.12, 0.12), 0.55)       # garis scanline tipis di wajah
SCAN_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.5
SCAN_M.blend_method = "BLEND"
CIRCUIT_RED = emissive("CircuitRed", (1.0, 0.08, 0.08), 0.9)
# --- set ---
GROUND = mat("Ground", (0.090, 0.094, 0.102), 0.9)
WET_GROUND = mat("WetGround", (0.05, 0.06, 0.08), 0.15)      # jalan basah reflektif
WALL = mat("Wall", (0.141, 0.149, 0.165), 0.85)
BUILDING = mat("Building", (0.11, 0.12, 0.14), 0.9)
BUILDING2 = mat("Building2", (0.13, 0.11, 0.11), 0.9)
WIN_WARM = emissive("WinWarm", (1.0, 0.72, 0.38), 1.2)
WIN_DARK = mat("WinDark", (0.05, 0.06, 0.09), 0.4)
WIN_RED = emissive("WinRed", (1.0, 0.10, 0.10), 1.0)
LAMP_GLOW = emissive("LampGlow", (1.0, 0.85, 0.55), 6.0)
SIREN_GLOW = emissive("SirenGlow", (0.827, 0.282, 0.235), 6.0)
POLE = mat("Pole", (0.15, 0.15, 0.16), 0.5, metal=0.6)
NEON_RED = emissive("NeonRed", (1.0, 0.08, 0.08), 2.0)
NEON_BLUE = emissive("NeonBlue", (0.18, 0.42, 1.0), 1.2)
SCREEN_M = mat("ScreenDark", (0.03, 0.03, 0.04), 0.4)
PAPER = mat("Paper", (0.92, 0.90, 0.84), 0.7)
INK = mat("Ink", (0.05, 0.05, 0.08), 0.5)
WOOD = mat("Wood", (0.35, 0.22, 0.12), 0.7)
CABLE_M = mat("Cable", (0.08, 0.08, 0.09), 0.6)
CORE_BODY = mat("CoreBody", (0.04, 0.04, 0.05), 0.3, metal=0.7)
CORE_LINE = emissive("CoreLine", (1.0, 0.05, 0.05), 1.4)     # garis merah data core
GATE_M = emissive("GateLight", (1.0, 1.0, 0.95), 1.2)  # FIX R1: gerbang harus lebih terang dari dinding         # gerbang cahaya putih (disembunyikan s.d. S8; 1.5 lalu 0.9 masih blown-out putih murni)
# --- aula memori (Ep 3): putih terang tapi BUKAN putih murni blown-out ---
HALL_FLOOR = mat("HallFloor", (0.92, 0.92, 0.90), 0.15)   # lantai reflektif putih
HALL_WALL = mat("HallWall", (0.88, 0.88, 0.86), 0.85)     # dinding/kolom putih lembut
HALL_COL = mat("HallCol", (0.85, 0.85, 0.83), 0.6)
# FIX R1: dinding/kolom aula tidak kena cahaya langsung (semua lampu aula
# mengarah sumbu Y) — beri emisi putih lembut 0.25 supaya aula terbaca PUTIH,
# bukan hitam di paruh atas frame. Lantai sudah terang, tidak perlu emisi.
for _hw, _hc in ((HALL_WALL, (0.88, 0.88, 0.86)), (HALL_COL, (0.85, 0.85, 0.83))):
    _hw.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (*_hc, 1.0)
    _hw.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.25
# mata 213 Kairo: gelap (tertutup) sampai S7 — animate menaikkan emisi ke 1.5.
K213_EYE_M = emissive("K213Eye", (0.30, 0.65, 1.0), 0.0)
_KB = K213_EYE_M.node_tree.nodes["Principled BSDF"]
_KB.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1.0)
# kilau bekas luka 213 instans (gelombang S6): biru terang, sama seperti Kairo.
SCAR213_M = emissive("ScarGlow213", (0.10, 0.30, 0.90), 2.0)
RAIN_M = mat("Rain", (0.75, 0.82, 0.9), 0.1)
RAIN_M.blend_method = "BLEND"
RAIN_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
DRONE_M = mat("Drone", (0.10, 0.10, 0.11), 0.4, metal=0.7)
DRONE_LIGHT = emissive("DroneLight", (1.0, 0.05, 0.05), 2.0)
BARRICADE_M = mat("Barricade", (0.35, 0.30, 0.10), 0.7)
SOCKET_M = mat("Socket", (0.12, 0.12, 0.14), 0.4, metal=0.8)


def smooth(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    o.select_set(False)


def block(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def ball(name, loc, size, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=32, ring_count=16)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def cylinder(name, loc, radius, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=32)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    smooth(o)
    return o


def dot(name, loc, size, m):
    """Titik partikel hemat: icosphere subdiv 1 (bukan UV sphere 32x16)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (size, size, size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def plane(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    return o


def text_obj(name, body, loc, size, m, rot=(math.radians(90), 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.name = name
    t.data.body = body
    t.data.extrude = 0.015
    t.data.size = size
    t.data.align_x = "CENTER"
    t.data.resolution_u = 16
    try:
        t.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    except Exception:
        pass
    t.data.materials.append(m)
    return t


def nexus_mini_face(prefix, loc, w, h, eye_mat=NEXUS_EYE):
    """Wajah NEXUS kecil di layar kota: glow plane + 2 mata + mulut."""
    cx, cy, cz = loc
    plane(f"{prefix}_Glow", (cx, cy, cz), (w, h), NEXUS_GLOW, rot=(math.radians(90), 0, 0))
    ball(f"{prefix}_EyeL", (cx - w * 0.22, cy - 0.06, cz + h * 0.12),
         (w * 0.09, 0.05, h * 0.05), eye_mat)
    ball(f"{prefix}_EyeR", (cx + w * 0.22, cy - 0.06, cz + h * 0.12),
         (w * 0.09, 0.05, h * 0.05), eye_mat)
    block(f"{prefix}_Mouth", (cx, cy - 0.06, cz - h * 0.22), (w * 0.3, 0.04, h * 0.03), eye_mat)


# ---------- SET 3: ruang inti NEXUS (RX=80, hitam raksasa) ----------
RX = 80.0
block("NX_Floor", (RX, 0, -0.1), (60, 48, 0.2), WET_GROUND)  # EPIC: lantai reflektif 60x48 m
# Ep 3: dinding belakang BERLUBANG gerbang 5,6 m — Kairo+EVA berjalan MENEMBUS
# ambang di S3c; tanpa lubang mereka menabrak dinding padat (Ep 2: dinding utuh).
block("NX_WallBackL", (RX - 16.4, 23.8, 8.0), (27.2, 0.4, 16.0), WALL)
block("NX_WallBackR", (RX + 16.4, 23.8, 8.0), (27.2, 0.4, 16.0), WALL)
block("NX_WallBackT", (RX, 23.8, 11.0), (5.6, 0.4, 10.0), WALL)
block("NX_WallL", (RX - 29.8, 0, 8.0), (0.4, 48, 16.0), WALL)
block("NX_WallR", (RX + 29.8, 0, 8.0), (0.4, 48, 16.0), WALL)
block("NX_WallFront", (RX, -23.8, 8.0), (60, 0.4, 16.0), WALL)
# wajah hologram NEXUS raksasa ~6 m di dinding belakang atas ("langit-langit")
# PENTING: fitur wajah HARUS di depan permukaan bola kepala (y<=10.85) — kalau
# di y=11.3 fitur terkubur di dalam bola dan wajah jadi telur merah polos.
# RONDE FIX 1: wajah BUKAN lagi panel persegi opaque — halo transparan
# (falloff radial, 9.5x7, lebih besar dari wajah) + awan partikel DI DEPAN
# wajah + mata besar menyipit + scanline. Harus terbaca HOLOGRAM, bukan poster.
plane("NX_FaceGlow", (RX, 23.5, 10.0), (18, 13), NEXUS_HALO, rot=(math.radians(90), 0, 0))  # EPIC: halo 18x13 m
ball("NX_FaceHead", (RX, 23.4, 10.0), (5.2, 1.0, 4.0), NEXUS_HEAD)  # EPIC: kepala ~12 m
# mata: lebih besar + menyipit (z 0.4->0.32) + miring mengancam (rotasi Y:
# ujung dalam turun — rotasi Z hanya memiringkan ke arah dalam/luar layar,
# bukan di layar). Glow samar di belakang tiap mata (y=10.92: di belakang
# permukaan depan mata, di depan permukaan bola ~10.98).
eyeL = ball("NX_EyeL", (RX - 2.3, 22.32, 11.0), (1.7, 0.36, 0.64), NEXUS_EYE_BIG)
eyeL.rotation_euler = (0, math.radians(10), 0)
eyeR = ball("NX_EyeR", (RX + 2.3, 22.32, 11.0), (1.7, 0.36, 0.64), NEXUS_EYE_BIG)
eyeR.rotation_euler = (0, math.radians(-10), 0)
plane("NX_EyeGlowL", (RX - 2.3, 22.38, 11.0), (3.0, 1.7), NEXUS_EYE_GLOW,
      rot=(math.radians(90), 0, 0))
plane("NX_EyeGlowR", (RX + 2.3, 22.38, 11.0), (3.0, 1.7), NEXUS_EYE_GLOW,
      rot=(math.radians(90), 0, 0))
# alis: miring mengancam (rotasi Y — ujung dalam turun; rotasi Z lama hanya
# memiringkan ke dalam layar, nyaris tak terlihat dari depan)
block("NX_BrowL", (RX - 2.3, 22.32, 12.3), (2.2, 0.2, 0.24), NEXUS_RED,
      rot=(0, math.radians(16), 0))
block("NX_BrowR", (RX + 2.3, 22.32, 12.3), (2.2, 0.2, 0.24), NEXUS_RED,
      rot=(0, math.radians(-16), 0))
block("NX_Nose", (RX, 22.32, 10.0), (0.24, 0.2, 1.8), NEXUS_RED)
block("NX_Mouth", (RX, 22.32, 8.0), (3.2, 0.2, 0.28), NEXUS_EYE)
# scanline horizontal tipis melintasi wajah (z 5.5/7.0/7.9: di antara
# mulut-mata-alis, tidak menutupi mata) — samar, alpha 0.5
for _i, _sz in enumerate((8.5, 11.0, 13.0)):
    block(f"NX_Scan{_i}", (RX, 22.28, _sz), (10.8, 0.06, 0.09), SCAN_M)
# partikel wajah: grid titik merah di sekitar wajah
import random as _random2
_random2.seed(2149)
for i in range(80):
    px = RX + _random2.uniform(-5.6, 5.6)
    pz = 10.0 + _random2.uniform(-4.0, 4.0)
    py = 23.3 - _random2.uniform(0.0, 1.0)
    _s = _random2.uniform(0.06, 0.14)
    ball(f"NX_Dot{i}", (px, py, pz), (_s, _s, _s), NEXUS_DOT)
# awan partikel DI DEPAN wajah (hologram berdimensi): ~320 titik tersebar
# y 10.55-10.90 — di depan permukaan bola (~10.9), sebagian di depan mata —
# ukuran bervariasi (15% besar 0.09-0.14), terang/redup selang-seling.
# Drift noise ditambahkan di animate_nexus.py (driver sin per titik).
for i in range(320):
    px = RX + _random2.uniform(-6.8, 6.8)
    pz = 10.0 + _random2.uniform(-4.8, 4.8)
    py = _random2.uniform(23.05, 23.40)
    _s = _random2.uniform(0.06, 0.16) if _random2.random() < 0.85 else _random2.uniform(0.18, 0.28)
    dot(f"NX_DotF{i}", (px, py, pz), _s, NEXUS_DOT if i % 3 else NEXUS_DOT_DIM)
# partikel digital melayang di ruangan
for i in range(40):
    px = RX + _random2.uniform(-25, 25)
    py = _random2.uniform(-20, 20)
    pz = _random2.uniform(0.5, 14.0)
    _s = _random2.uniform(0.04, 0.10)
    ball(f"NX_Float{i}", (px, py, pz), (_s, _s, _s), NEXUS_DOT)
# kolom circuitry menyala merah di sekeliling
# EPIC: 12 kolom 14 m — baris luar + baris dalam (depth depan-tengah-belakang).
for i, (ccx, ccy) in enumerate(((-20, -12), (-20, 12), (20, -12), (20, 12),
                                (-10, -6), (-10, 6), (10, -6), (10, 6),
                                (-5, 15), (5, 15), (-5, -18), (5, -18))):
    block(f"NX_Col{i}", (RX + ccx, ccy, 7.0), (1.2, 1.2, 14.0), WALL)
    block(f"NX_ColLight{i}", (RX + ccx, ccy - 0.65 if ccy < 0 else ccy + 0.65, 7.0),
          (0.15, 0.15, 13.6), CIRCUIT_RED)
    for _k in range(3):
        block(f"NX_ColStrip{i}_{_k}", (RX + ccx, ccy, 2.4 + _k * 4.0),
              (1.25, 1.25, 0.12), CIRCUIT_RED)
# soket core di tengah ruangan (S6: Kairo memasang core) — KECIL + RENDAH +
# GESER ke samping (RX+0.6, -0.6): soket 1.0 m di tengah (RX,0) menutupi badan
# Kairo di shot hero S8 (f1422 v2) dan Kairo menembusnya saat jalan ke gerbang.
cylinder("NX_SocketBase", (RX + 2.5, -3.0, 0.175), 0.32, 0.35, SOCKET_M)
cylinder("NX_SocketTop", (RX + 2.5, -3.0, 0.40), 0.22, 0.10, METAL_SEN2)
block("NX_SocketSlot", (RX + 2.5, -3.0, 0.46), (0.14, 0.14, 0.05), CORE_LINE)
# gerbang cahaya putih di ujung (S8) — di dinding belakang bawah, di bawah wajah
# (disembunyikan via props["gate"] s.d. S8 — di S6/S7 ia terbaca seperti pintu putih polos)
_gate_plane = plane("NX_Gate", (RX, 23.55, 3.0), (5.0, 6.0), GATE_M, rot=(math.radians(90), 0, 0))  # EPIC: gerbang 5x6 m, TERBUKA di S6 (skala X di-key di animate)
_gate_plane.hide_render = False  # Ep 3: gerbang TERBUKA PENUH sejak S1 (gate_open=1 konstan)
block("NX_GateFrameL", (RX - 2.6, 23.5, 3.0), (0.4, 0.5, 6.0), WALL)
block("NX_GateFrameR", (RX + 2.6, 23.5, 3.0), (0.4, 0.5, 6.0), WALL)
block("NX_GateFrameT", (RX, 23.5, 6.1), (5.6, 0.5, 0.4), WALL)

# ---------- kabut (volume) ----------
def haze(name, loc, scale, density):
    m = bpy.data.materials.new(name + "M")
    m.use_nodes = True
    nt = m.node_tree.nodes
    nt.remove(nt["Principled BSDF"])
    vol = nt.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = density
    vol.inputs["Color"].default_value = (0.85, 0.88, 0.95, 1.0)
    m.node_tree.links.new(vol.outputs["Volume"], nt["Material Output"].inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    h = bpy.context.object
    h.name = name
    h.scale = scale
    h.data.materials.append(m)
    return h


if os.environ.get("FS_VOL", "1") == "1":
    haze("NX_Haze", (RX, 0, 6.0), (30, 24, 8), 0.02)  # ruang inti (EPIC: volume 60x48x16)
    haze("MH_Haze", (RX, 54, 6.0), (24, 30, 8), 0.01)  # aula memori: kabut putih tipis

# ---------- karakter vinyl-toy ----------
# Kepala ~40% tinggi (KAIRO 1.8 unit). Karakter menghadap -Y (ke arah kamera default).
# Rig empty dibuat di animate_nexus.py.
CHARS = {}


def make_character(prefix, kind, scale, base, jacket_mat, skin_mat, eye_mat,
                   eye_red_mat=None):
    """kind: kairo | eva | sentinel | res | civ. base=(x,y,z)."""
    s = scale
    bx, by, bz = base
    hip_z = 0.48 * s
    sho_z = 1.12 * s
    sho_x = 0.38 * s * (1.35 if kind == "sentinel" else 1.0)
    head_z = 1.45 * s
    head_r = 0.275 * s * (1.1 if kind == "sentinel" else 1.0)
    head_mat = skin_mat
    # sentinel: mata sensor merah yang bisa dinyalakan via eye_red
    _red = kind == "sentinel"
    eye_r = 0.065 * s if _red else 0.055 * s  # sentinel 0.065 (0.075 terlalu besar/kartun)

    def P(x, y, z):
        return (bx + x, by + y, bz + z)

    body, head, armL, armR, legL, legR = [], [], [], [], [], []
    for side, sx in (("L", -1), ("R", 1)):
        _leg = block(f"{prefix}_Leg{side}", P(0.14 * sx * s, 0, 0.24 * s),
                     (0.17 * s, 0.2 * s, 0.42 * s), PANTS_K if kind in ("kairo", "res") else
                     (SUIT_EVA if kind == "eva" else (METAL_SEN if kind == "sentinel" else JACKET3)))
        _shoe = block(f"{prefix}_Shoe{side}", P(0.14 * sx * s, -0.04 * s, 0.07 * s),
                      (0.2 * s, 0.3 * s, 0.12 * s),
                      BOOTS if kind in ("kairo", "res") else METAL_SEN)
        (legL if side == "L" else legR).extend([_leg, _shoe])
    # torso + detail
    body.append(block(f"{prefix}_Torso", P(0, 0, 0.78 * s), (0.62 * s, 0.5 * s, 0.6 * s), jacket_mat))
    if kind == "kairo":
        # saku dada taktis (kotak pipih — JANGAN kena subsurf, biar tetap crisp)
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Pocket{side}", P(0.15 * sx * s, -0.26 * s, 0.88 * s),
                              (0.2 * s, 0.03 * s, 0.14 * s), SHIRT))
        # bantalan bahu taktis
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Pad{side}", P(0.32 * sx * s, 0, 1.08 * s),
                              (0.22 * s, 0.3 * s, 0.1 * s), JACKET))
    if kind == "sentinel":
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Pad{side}", P(0.52 * sx * s, 0, 1.15 * s),
                              (0.42 * s, 0.36 * s, 0.22 * s), METAL_SEN2))
        # piston sendi bahu
        for side, sx in (("L", -1), ("R", 1)):
            body.append(cylinder(f"{prefix}_Piston{side}", P(sho_x * sx, 0.1 * s, sho_z),
                                 0.05 * s, 0.3 * s, METAL_SEN2, rot=(0, math.radians(90), 0)))
    # lengan (pivot di bahu)
    for side, sx in (("L", -1), ("R", 1)):
        lst = armL if side == "L" else armR
        lst.append(block(f"{prefix}_Arm{side}", P(sho_x * sx, 0, sho_z - 0.28 * s),
                         (0.16 * s, 0.18 * s, 0.5 * s), jacket_mat))
        lst.append(ball(f"{prefix}_Hand{side}", P(sho_x * sx, 0, sho_z - 0.56 * s),
                        (0.09 * s,) * 3, head_mat))
    # kepala + wajah
    head.append(ball(f"{prefix}_Head", P(0, 0, head_z), (head_r, head_r * 0.92, head_r), head_mat))
    if kind == "kairo":
        # rambut hitam pendek (mesh pendek, bukan particle hair)
        head.append(ball(f"{prefix}_Hair", P(0, 0.06 * s, head_z + 0.10 * s),
                         (head_r * 1.02, head_r * 0.95, head_r * 0.75), HAIR_KAI))
        # kerah tinggi jaket
        head.append(block(f"{prefix}_Collar", P(0, 0.05 * s, head_z - 0.24 * s),
                          (0.4 * s, 0.3 * s, 0.14 * s), JACKET))
    if kind == "sentinel":
        # helm / pelat kepala logam + visor
        head.append(ball(f"{prefix}_Helm", P(0, 0.05 * s, head_z + 0.08 * s),
                         (head_r * 1.08, head_r * 1.0, head_r * 0.7), METAL_SEN2))
        head.append(block(f"{prefix}_Visor", P(0, -0.22 * s, head_z + 0.05 * s),
                          (0.34 * s, 0.04 * s, 0.07 * s), SENSOR_OFF))
    eyes_black, eyes_red = [], []
    for side, sx in (("L", -1), ("R", 1)):
        eyes_black.append(ball(f"{prefix}_EyeB{side}", P(0.11 * sx * s, -0.235 * s, head_z + 0.03 * s),
                               (0.055 * s, 0.03 * s, 0.07 * s), eye_mat))
        if eye_red_mat is not None:
            eyes_red.append(ball(f"{prefix}_EyeR{side}", P(0.11 * sx * s, -0.24 * s, head_z + 0.03 * s),
                                 (eye_r, 0.032 * s, eye_r * 1.25), eye_red_mat))
    head.extend(eyes_black)
    head.extend(eyes_red)
    mouth = block(f"{prefix}_Mouth", P(0, -0.25 * s, head_z - 0.13 * s),
                  (0.12 * s, 0.03 * s, 0.03 * s), mat(f"{prefix}_MouthM", (0.10, 0.02, 0.03), 0.3))
    head.append(mouth)
    if kind in ("kairo", "res", "civ"):
        for side, sx in (("L", -1), ("R", 1)):
            head.append(block(f"{prefix}_Brow{side}", P(0.11 * sx * s, -0.25 * s, head_z + 0.13 * s),
                              (0.12 * s, 0.03 * s, 0.03 * s), HAIR_KAI, rot=(0, 0, math.radians(-10 * sx))))
    if kind == "eva":
        # garis circuitry biru di pelipis + "rambut energi" tipis
        for side, sx in (("L", -1), ("R", 1)):
            head.append(block(f"{prefix}_Circuit{side}", P(0.24 * sx * s, -0.1 * s, head_z + 0.1 * s),
                              (0.03 * s, 0.03 * s, 0.16 * s), CIRCUIT_BLUE))
    info = {
        "base": Vector(base), "scale": s, "kind": kind,
        "hip_z": hip_z, "sho_z": sho_z, "sho_x": sho_x, "head_z": head_z,
        "head_pivot_z": 1.18 * s,
        "body": body, "head": head, "armL": armL, "armR": armR,
        "legL": legL, "legR": legR,
        "eyes_black": eyes_black, "eyes_red": eyes_red, "mouth": mouth,
    }
    CHARS[prefix] = info
    return info


make_character("KAI", "kairo", 1.0, (0, 0, 0), JACKET, SKIN_KAI, EYE_DARK)
make_character("EVA", "eva", 1.0, (0, 0, 0), SUIT_EVA, SKIN_EVA, EYE_BLUE)
for _i in range(1, 9):
    make_character(f"SEN{_i}", "sentinel", 1.22, (0, 0, 0), METAL_SEN, METAL_SEN,
                   SENSOR_OFF, SENSOR_RED)
make_character("RES1", "res", 1.0, (0, 0, 0), JACKET2, SKIN_KAI, EYE_DARK)
make_character("RES2", "res", 1.0, (0, 0, 0), JACKET3, SKIN_KAI, EYE_DARK)
make_character("CIV1", "civ", 1.0, (0, 0, 0), JACKET3, SKIN_KAI, EYE_DARK)
make_character("CIV2", "civ", 1.0, (0, 0, 0), JACKET2, SKIN_KAI, EYE_DARK)

# --- bekas luka alis kiri KAIRO (WAJIB terbaca di close-up) ---
# Alis kiri = sisi +X (karakter menghadap -Y: kiri anatomis = +X; konvensi L
# builder zombie (-X) justru sisi kanan). RONDE FIX 1: garis TIPIS warna
# kulit sedikit lebih terang #D8B49A (bukan putih), TANPA emissive — versi
# lama (0.12 x 0.022, emissive 0.15) terbaca seperti plester putih tebal.
SCAR_M = mat("Scar", (0.65, 0.50, 0.40), 0.7)  # FIX R2: lebih gelap lagi
# y=-0.22 (bukan -0.28): permukaan dahi di titik ini y~-0.19 — luka lama
# mengambang ~9 cm di depan kulit sehingga terbaca seperti strip terpisah.
# Kini menempel di kulit (0.04 di depan permukaan), tetap terbaca sebagai garis.
scar = block("KAI_Scar", (0.11, -0.22, 1.60), (0.06, 0.008, 0.006), SCAR_M,  # FIX R2: garis tipis
             rot=(0, 0, math.radians(-25)))
CHARS["KAI"]["head"].append(scar)
CHARS["KAI"]["scar"] = scar
# EPIC Ep 2 — kilau biru bekas luka (S4 ECU saja, SANGAT lemah): glow tipis
# di depan garis luka, di-key via prop scar_glow di animate.
SCAR_GLOW_M = emissive("ScarGlowBlue", (0.10, 0.30, 0.90), 2.0)  # Ep 3: TERANG sejak S3 (Ep 2 S4: 0.8 sangat lemah) — jangan blown-out
scar_glow = block("KAI_ScarGlow", (0.11, -0.235, 1.60), (0.07, 0.006, 0.008),
                  SCAR_GLOW_M, rot=(0, 0, math.radians(-25)))
scar_glow.hide_render = True
CHARS["KAI"]["head"].append(scar_glow)
CHARS["KAI"]["scar_glow"] = scar_glow
# EPIC Ep 2 — titik laser merah di tubuh EVA (S8: Sentinel membidik EVA).
# Dibangun di posisi dada karakter-di-origin, ikut root rig EVA di animate.
LASER_RED = emissive("LaserRed", (1.0, 0.05, 0.05), 2.5)
eva_laser1 = ball("EvaLaser1", (0.10, -0.26, 1.05), (0.03, 0.03, 0.03), LASER_RED)
eva_laser2 = ball("EvaLaser2", (-0.12, -0.26, 0.85), (0.03, 0.03, 0.03), LASER_RED)
eva_laser1.hide_render = True
eva_laser2.hide_render = True
# EPIC Ep 3 — titik laser merah di dada KAIRO (S1: laser BERGESER dari EVA
# ke Kairo, f24-71). Dibangun di dada origin, ikut root rig KAIRO di animate.
KAI_LASER = emissive("LaserRedKairo", (1.0, 0.05, 0.05), 2.5)
kai_laser1 = ball("KaiLaser1", (0.10, -0.26, 1.05), (0.03, 0.03, 0.03), KAI_LASER)
kai_laser2 = ball("KaiLaser2", (-0.12, -0.26, 0.85), (0.03, 0.03, 0.03), KAI_LASER)
kai_laser1.hide_render = True
kai_laser2.hide_render = True

# --- backpack KAIRO (objek terpisah — dilepas di S6-S8, di-key via props) ---
bp_box = block("KAI_Backpack", (0, 0.32, 0.95), (0.42, 0.2, 0.5), BACKPACK_M)
bp_flap = block("KAI_BackpackFlap", (0, 0.42, 1.12), (0.44, 0.06, 0.16), JACKET)
bp_strip1 = block("KAI_BPStrip1", (0.12, 0.43, 0.95), (0.05, 0.02, 0.34), STRIP_BLUE)
bp_strip2 = block("KAI_BPStrip2", (-0.12, 0.43, 0.95), (0.05, 0.02, 0.34), STRIP_BLUE)
bp_ant = cylinder("KAI_BPAntenna", (0.18, 0.32, 1.35), 0.012, 0.35, POLE)
BACKPACK_OBJS = [bp_box, bp_flap, bp_strip1, bp_strip2, bp_ant]
for _o in BACKPACK_OBJS:
    _o.hide_render = True
# backpack tergeletak di lantai ruang inti (S6-S8)
bp_drop = block("KAI_BackpackDropped", (RX - 2.0, -1.5, 0.18), (0.42, 0.5, 0.2), BACKPACK_M,
                rot=(0, 0, math.radians(15)))
bp_drop.hide_render = True

# --- data core (kubus 12 cm, garis merah berdenyut) — di tangan kanan KAIRO ---
core = block("CoreCube", (0.38, -0.05, 0.56), (0.12, 0.12, 0.12), CORE_BODY)
core_line1 = block("CoreLine1", (0.38, -0.05, 0.56), (0.13, 0.13, 0.02), CORE_LINE)
core_line2 = block("CoreLine2", (0.38, -0.05, 0.56), (0.02, 0.13, 0.13), CORE_LINE)
CORE_OBJS = [core, core_line1, core_line2]
for _o in CORE_OBJS:
    _o.hide_render = True
# core terpasang di soket ruang inti (S6+) — ikut posisi soket geser
core_sock = block("CoreSocketed", (RX + 2.5, -3.0, 0.48), (0.12, 0.12, 0.12), CORE_BODY)
core_sock_l = block("CoreSocketedLine", (RX + 2.5, -3.0, 0.48), (0.13, 0.13, 0.02), CORE_LINE)
CORE_SOCKET_OBJS = [core_sock, core_sock_l]
for _o in CORE_SOCKET_OBJS:
    _o.hide_render = True

# ---------- SET 4: aula memori (ISI gerbang, S4-S8) — set BARU Ep 3 ----------
# Aula putih tanpa ujung di balik gerbang (y 24..84): lantai reflektif PUTIH,
# dinding/kolom putih lembut, cahaya putih lembut — kebalikan palet trilogi
# (hitam/merah/biru -> putih), set paling terang di seri. Ambang 5x6 m yang
# sama mengembang menjadi ruang tanpa batas di dalam — JANGAN buat gerbang
# kedua. Kabut putih tipis supaya barisan memudar ke putih tanpa ujung.
MH = 54.0  # pusat aula (sumbu Y)
block("MH_Floor", (RX, MH, -0.1), (48, 60, 0.2), HALL_FLOOR)
block("MH_Ceil", (RX, MH, 16.0), (48, 60, 0.2), HALL_WALL)
block("MH_WallBack", (RX, 84.0, 8.0), (48, 0.4, 16.0), HALL_WALL)
block("MH_WallL", (RX - 24.0, MH, 8.0), (0.4, 60, 16.0), HALL_WALL)
block("MH_WallR", (RX + 24.0, MH, 8.0), (0.4, 60, 16.0), HALL_WALL)
for _i, (_hx, _hy) in enumerate(((-20, 36), (-20, 48), (-20, 60), (-20, 72),
                                 (20, 36), (20, 48), (20, 60), (20, 72))):
    block(f"MH_Col{_i}", (RX + _hx, _hy, 7.0), (1.2, 1.2, 14.0), HALL_COL)
# --- 213 Kairo membeku: SATU model beku (collection) di-instans 213x ---
# Instans = linked duplicates model Kairo yang sama (tanpa rig baru, tanpa
# lip-sync, tanpa dialog): pose beku di tengah langkah, mata TERTUTUP sampai
# S7 (material K213Eye gelap -> biru menyala serentak), SATU LANGKAH serentak
# S8 (translasi instance -Y 0.35 m ke arah ambang, di-key di animate).
KF_COLL = bpy.data.collections.new("KairoFrozen")
bpy.context.scene.collection.children.link(KF_COLL)
_KF = []
_KF.append(block("KF_Torso", (0, 0, 0.78), (0.62, 0.5, 0.6), JACKET))
_KF.append(ball("KF_Head", (0, 0, 1.45), (0.275, 0.253, 0.275), SKIN_KAI))
_KF.append(ball("KF_Hair", (0, 0.06, 1.55), (0.28, 0.26, 0.21), HAIR_KAI))
_KF.append(block("KF_Scar", (0.11, -0.22, 1.60), (0.06, 0.008, 0.006), SCAR_M,
                 rot=(0, 0, math.radians(-25))))
for _sx in (-1, 1):
    _side = "L" if _sx < 0 else "R"
    _KF.append(ball(f"KF_Eye{_side}", (0.11 * _sx, -0.235, 1.48),
                    (0.055, 0.03, 0.07), K213_EYE_M))
    _KF.append(block(f"KF_Arm{_side}", (0.38 * _sx, 0.10 * _sx, 0.84),
                    (0.16, 0.18, 0.5), JACKET))
    _KF.append(block(f"KF_Leg{_side}", (0.14 * _sx, -0.15 if _sx < 0 else 0.12, 0.24),
                    (0.17, 0.2, 0.42), PANTS_K))
    _KF.append(block(f"KF_Shoe{_side}", (0.14 * _sx, -0.19 if _sx < 0 else 0.16, 0.07),
                    (0.2, 0.3, 0.12), BOOTS))
for _o in _KF:
    bpy.context.scene.collection.objects.unlink(_o)
    KF_COLL.objects.link(_o)
K213_BASE = {}
K213_SCAR_GLOW = []
for _idx in range(213):
    _row, _col = divmod(_idx, 17)
    _x = RX - 24.0 + _col * 3.0
    _y = 30.0 + _row * 3.6
    _e = bpy.data.objects.new(f"K213_{_idx:03d}", None)
    bpy.context.scene.collection.objects.link(_e)
    _e.instance_type = "COLLECTION"
    _e.instance_collection = KF_COLL
    _e.location = (_x, _y, 0.0)
    K213_BASE[_e.name] = (_x, _y, 0.0)
    # kilau bekas luka per instans (gelombang S6: di-key per baris di animate)
    _sg = dot(f"K213_{_idx:03d}_ScarGlow", (_x + 0.11, _y - 0.24, 1.60), 0.045, SCAR213_M)
    _sg.hide_render = True
    K213_SCAR_GLOW.append(_sg)
# --- wajah NEXUS kecil dari DALAM aula (S8): lebih kecil, lebih jauh, BERKEDIP ---
# FIX R1: posisi lama (y=20, di LUAR gerbang di ruang inti) TIDAK PERNAH
# terlihat — semua kamera S8 ada di sisi aula menatap +Y, wajah itu ada di
# BELAKANG kamera. Dipindah ke ujung jauh aula (y=68, z=9, menghadap -Y ke
# arah kamera): dari wide S8 ia terbaca kecil + jauh, berkedip merah di atas
# barisan — sesuai naskah "lebih kecil, lebih jauh". Hanya muncul di S8
# (hide_render di-key dari props nexus_face di animate).
plane("NX_FaceSmall_Glow", (RX, 68.0, 9.0), (4.0, 3.0), NEXUS_GLOW, rot=(math.radians(90), 0, 0))
ball("NX_FaceSmall_EyeL", (RX - 0.9, 67.94, 9.5), (0.35, 0.05, 0.22), NEXUS_EYE)
ball("NX_FaceSmall_EyeR", (RX + 0.9, 67.94, 9.5), (0.35, 0.05, 0.22), NEXUS_EYE)
block("NX_FaceSmall_Mouth", (RX, 67.94, 8.3), (1.2, 0.04, 0.12), NEXUS_EYE)
NX_FACE_SMALL_OBJS = [bpy.data.objects[n] for n in
                      ("NX_FaceSmall_Glow", "NX_FaceSmall_EyeL",
                       "NX_FaceSmall_EyeR", "NX_FaceSmall_Mouth")]
for _o in NX_FACE_SMALL_OBJS:
    _o.hide_render = True

# ---------- lampu ----------
def point_light(name, loc, color, energy, shadow=False):
    bpy.ops.object.light_add(type="POINT", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.shadow_soft_size = 0.5
    o.data.use_shadow = shadow
    return o


def area_light(name, loc, color, energy, size, rot, shadow=False):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.size = size
    o.data.use_shadow = shadow
    o.rotation_euler = rot
    return o


# --- ruang inti (warisan Ep 2; lampu kota/persembunyian TIDAK ADA — Ep 3 tanpa kota) ---
area_light("CoreFill", (RX, -16, 8), (0.62, 0.72, 1.0), 90.0, 16, (math.radians(55), 0, 0))
point_light("RimRedCore", (RX, 10.0, 3.0), (1.0, 0.08, 0.05), 500.0)
point_light("EvaRimCore", (RX + 4, -6, 2.5), (0.30, 0.65, 1.0), 0.0)
point_light("NexusLight", (RX, 16.0, 10.0), (1.0, 0.08, 0.05), 300.0)
area_light("GateLight", (RX, 22.5, 3.5), (1.0, 1.0, 0.95), 0.0, 12, (math.radians(90), 0, 0))
# --- aula memori: cahaya putih lembut merata (jangan blown-out) ---
# FIX R1: lampu area aula terlalu redup untuk ukurannya (300 W / 20x20 m)
# + dinding samping tidak kena cahaya langsung sama sekali (semua lampu aula
# mengarah sumbu Y) — langit-langit/dinding atas render HITAM (Ronde 1:
# S4 mean 78->66, paruh atas frame gelap). Perbaikan: HallLight 300->1200
# (sorot ke langit-langit), HallFill 150->400, dinding/kolom diberi emisi
# putih lembut 0.25 supaya terbaca putih apa pun arah cahaya.
area_light("HallLight1", (RX, 40, 12), (1.0, 1.0, 0.98), 1200.0, 20, (math.radians(140), 0, 0))
area_light("HallLight2", (RX, 66, 12), (1.0, 1.0, 0.98), 1200.0, 20, (math.radians(140), 0, 0))
area_light("HallFill", (RX, 54, 6), (0.95, 0.97, 1.0), 400.0, 24, (math.radians(55), 0, 0))
point_light("HallRedFlicker", (RX, 26, 3.0), (1.0, 0.08, 0.05), 0.0)  # kedip merah S5 dari ambang
point_light("EvaRimHall", (RX, 30, 2.5), (0.30, 0.65, 1.0), 0.0)
# glow mata Sentinel ECU (S1/S2) — ikut rig kepala SEN1 di animate
bpy.ops.object.light_add(type="POINT", location=(0, -0.3, 1.8))
eye_glow = bpy.context.object
eye_glow.name = "EyeGlow"
eye_glow.data.color = (1.0, 0.05, 0.05)
eye_glow.data.energy = 0.0
# denyut merah data core — ikut lengan kanan KAIRO di animate
bpy.ops.object.light_add(type="POINT", location=(0.38, -0.1, 0.56))
core_light = bpy.context.object
core_light.name = "CoreLight"
core_light.data.color = (1.0, 0.1, 0.05)
core_light.data.energy = 0.0

# ---------- quality pass B7: subsurf 1 di semua bagian karakter, bevel 0 ----------
# Detail pipih (saku, bekas luka, circuitry, visor) TIDAK kena subsurf — kalau
# kena, kotak pipih menggembung jadi bantal (pelajaran still S3 f421: "Shirt"
# jadi heksagon di dada Kairo).
SUB = int(os.environ.get("FS_SUB", "1"))
_NOSUB = ("Pocket", "Scar", "Circuit", "Visor")
for _info in CHARS.values():
    for _part in (_info["body"] + _info["head"] + _info["armL"] + _info["armR"]
                  + _info["legL"] + _info["legR"]):
        if _part.type == "MESH" and SUB > 0 and not any(_k in _part.name for _k in _NOSUB):
            _s = _part.modifiers.new("Subdiv", "SUBSURF")
            _s.levels = 0
            _s.render_levels = SUB
# vinyl: clear-coat ringan
for _m, _coat in ((SKIN_KAI, 0.5), (JACKET, 0.3), (BACKPACK_M, 0.2), (SKIN_EVA, 0.6)):
    _b = _m.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in _b.inputs:
        _b.inputs["Coat Weight"].default_value = _coat
        _b.inputs["Coat Roughness"].default_value = 0.15

# ---------- kamera default (plan yang menggerakkan per frame) ----------
bpy.ops.object.camera_add(location=(0, -6.5, 1.7))
cam = bpy.context.object
cam.data.lens = 40
look = Vector((0, 0, 1.3)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = os.environ.get("FS_DOF", "1") == "1"
cam.data.dof.focus_distance = 6.5
cam.data.dof.aperture_fstop = 2.0
scene.camera = cam

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
