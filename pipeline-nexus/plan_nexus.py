#!/usr/bin/env python3
# plan_nexus_ep3.py — generator plan.json NEXUS ZERO Episode 3 "THE CHOICE".
# Satu baris per frame (f 0..1439). Per frame: rig tiap karakter, intensitas
# lampu, kamera (x,y,z,target,focus,lens,roll Dutch), flag.
# Murni Python (tanpa bpy). Pola: plan_nexus_ep2.py.
# Set: ruang inti MONUMENTAL (RX=80, 60x48 m, dinding 16 m, wajah ~12 m,
# gerbang 5x6 m TERBUKA PENUH sejak S1 di y=23.55) + aula memori putih
# (pusat y=54, lantai putih, barisan 213 Kairo membeku y 30..73.2).
# TIDAK ADA flash putih di Ep 3 (berakhir hitam + end card).
# TIDAK ADA kota aerial di Ep 3.
# Flag baru: gate_open = 1.0 S1-S3b + S4-S8, KECUALI 0.0 di S3c (f480-599):
# kamera 3c ada di DALAM aula menatap balik — panel gerbang opak (5x6 m)
# menutupi Kairo+EVA kalau tetap 1.0 (temuan tes farm Ronde 1: frame putih
# polos). Panel disembunyikan tepat di cut 3b->3c, muncul lagi di cut ke S4
# (kamera S4 membelakangi gerbang — pop tidak terlihat).
# scar_glow terang (S3+);
# scar_wave (S6, 0..1 baris demi baris); laser_eva (S1 f0-23) +
# laser_kairo (S1 f24-71, laser BERGESER); nexus_flicker (S5);
# kairo213_eyes (S7+); kairo213_step (S8, 0..1); nexus_face (S8).
#   python3 plan_nexus_ep3.py [plan.json]
import json
import math
import os
import sys

N = 1440
RX = 80.0   # offset ruang inti NEXUS (sama dengan build_scene_nexus_ep2.py)
ALL_CHARS = ["KAI", "EVA"] + [f"SEN{i}" for i in range(1, 9)] + ["RES1", "RES2", "CIV1", "CIV2"]


def clamp(x, a, b):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def seg_t(f, a, b):
    return clamp((f - a) / max(1, b - a), 0.0, 1.0)


def shake(f, amp, freq=1.7):
    return amp * (math.sin(f * 0.9 * freq) * 0.6 + math.sin(f * 2.3 * freq + 1.3) * 0.4)


def walk_cycle(phase, amp, arm_amp=None):
    if arm_amp is None:
        arm_amp = amp * 0.8
    return {
        "legL": amp * math.sin(phase),
        "legR": -amp * math.sin(phase),
        "armL": -arm_amp * math.sin(phase),
        "armR": arm_amp * math.sin(phase),
        "bob": 0.045 * abs(math.cos(phase)),
    }


def char(x=0, y=0, z=0, rot=0, lean=0, squash=1.0, crouch=0.0, pitch=0.0,
         head_tilt=0, head_turn=0, armL=0, armR=0, legL=0, legR=0,
         eye_red=False, vis=True, mouthW=1.0, mouthH=1.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "rot": round(rot, 2),
            "lean": round(lean, 2), "squash": round(squash, 3), "crouch": round(crouch, 3),
            "pitch": round(pitch, 2), "head_tilt": round(head_tilt, 2),
            "head_turn": round(head_turn, 2), "armL": round(armL, 2), "armR": round(armR, 2),
            "legL": round(legL, 2), "legR": round(legR, 2),
            "eye_red": bool(eye_red), "vis": bool(vis),
            "mouthW": round(mouthW, 2), "mouthH": round(mouthH, 2)}


def hidden():
    return char(vis=False)


def cam(x, y, z, tx, ty, tz, focus, lens, roll=0.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
            "tx": round(tx, 3), "ty": round(ty, 3), "tz": round(tz, 3),
            "focus": round(focus, 2), "lens": round(lens, 1),
            "roll": round(roll, 2)}


def lights(nexus=120, gate=400, rim=0, eye=0, core=150, eva=0, fill=90,
           hall=0, hallred=0):
    """Ep 3: nexus/gate/rim/eye/core/eva/fill (ruang inti) + hall (cahaya putih
    aula: HallLight1+2 + HallFill) + hallred (kedip merah S5 dari ambang)."""
    return {"nexus": round(nexus, 1), "gate": round(gate, 1), "rim": round(rim, 1),
            "eye": round(eye, 1), "core": round(core, 1), "eva": round(eva, 1),
            "fill": round(fill, 1), "hall": round(hall, 1),
            "hallred": round(hallred, 1)}


def sentinel_patrol(x, y, f, phase0=0.0, rot=90, speed=0.5):
    """Sentinel: langkah berat kaku, kepala menoleh dengan jeda mekanik."""
    ph = phase0 + f * 0.06 * speed
    step = 14 * math.sin(ph)
    turn = 18 * math.sin(math.floor(f / 20) * 1.1)
    return char(x, y, 0.02 * abs(math.cos(ph)), rot=rot, lean=3,
                head_tilt=2, head_turn=turn,
                armL=6, armR=-6, legL=step, legR=-step, eye_red=True)


def sentinel_frozen(x, y, rot=180):
    """Sentinel MEMBEKU di tengah langkah (S1 Ep 2): satu lutut setengah
    tertekuk, badan condong, sensor menyala (eye_red=True — padam diatur
    lewat lampu eye di plan, bukan di sini)."""
    return char(x, y, 0, rot=rot, lean=6, crouch=0.25, head_tilt=3,
                armL=8, armR=-4, legL=18, legR=-8, eye_red=True)



rows = []
for f in range(N):
    chars = {}
    # core SUDAH terpasang di soket sejak S6 Ep 1; backpack tergeletak di
    # lantai ruang inti sejak S6 Ep 1 — keduanya ada di SEMUA segmen Ep 3,
    # TIDAK dibawa masuk gerbang. Gerbang TERBUKA PENUH sejak S1.
    props = {"core_in_hand": False, "core_table": False, "core_socket": True,
             "backpack": False, "backpack_dropped": True, "rain": False,
             "gate": True, "scar_glow": False, "laser_eva": False,
             "laser_kairo": False, "nexus_face": False, "kairo213_eyes": False}
    gate_open = 1.0
    wall_emit = 0.25  # emisi dinding/kolom aula (FIX R1: aula terbaca putih)
    nexus_flicker = False
    scar_wave = 0.0
    kairo213_step = 0.0
    flash_white = False  # TIDAK ADA flash di Ep 3

    # ================= S1 HOOK (0-71) — "HE DID NOT CHOOSE." =================
    if f < 72:
        # Kairo menggenggam tangan EVA; laser merah BERGESER dari EVA (f0-23)
        # ke dada Kairo (f24-71); Sentinel membeku membidik.
        props["laser_eva"] = f < 24
        props["laser_kairo"] = 24 <= f < 72
        t = seg_t(f, 0, 71)
        chars["KAI"] = char(RX, 4.0, 0, rot=180, lean=6, head_tilt=0,
                            armL=5, armR=55, legL=0, legR=0)
        chars["EVA"] = char(RX + 2.0, 3.0, 0, rot=200, lean=2, head_tilt=0,
                            armL=55, armR=5, legL=0, legR=0)
        for _sx, _nm in ((-3, "SEN1"), (3, "SEN2")):
            chars[_nm] = char(RX + _sx, 12, 0, rot=0, lean=5, head_tilt=0,
                              armL=6, armR=55, legL=0, legR=0, eye_red=True)
        chars_cam = cam(RX + 0.6, lerp(-7.0, -5.0, smooth(t)), lerp(1.0, 1.2, smooth(t)),
                        RX, 4.5, 1.35, lerp(7.0, 5.5, smooth(t)),
                        lerp(52, 48, t), roll=8)
        li = lights(nexus=1200, gate=450, rim=600, eye=700, eva=300,
                    fill=200, core=150)
        for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S2 NEXUS MENAWAR (72-287) =================
    elif f < 288:
        if f < 144:
            # 2a: fast push-in ke wajah NEXUS — terbentuk kembali TAJAM
            t = seg_t(f, 72, 143)
            chars["KAI"] = char(RX, 4.0, 0, rot=180, lean=4, head_tilt=lerp(0, -12, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 3.0, 0, rot=200, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            for _sx, _nm in ((-3, "SEN1"), (3, "SEN2")):
                chars[_nm] = char(RX + _sx, 12, 0, rot=0, lean=5, head_tilt=0,
                                  armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX - 1.0, lerp(-8.0, -5.0, smooth(t)), lerp(2.0, 3.5, smooth(t)),
                            RX, lerp(2.0, 10.0, smooth(t)), lerp(1.5, 9.0, smooth(t)),
                            lerp(9.0, 15.0, smooth(t)), lerp(50, 62, t))
            li = lights(nexus=lerp(800, 2000, smooth(t)), gate=450, rim=700,
                        fill=200, core=150, eva=300, eye=500)
        elif f < 216:
            # 2b: cut ke gerbang — berdenyut putih vs merah di satu frame
            t = seg_t(f, 144, 215)
            chars["KAI"] = char(RX, 4.0, 0, rot=180, lean=4, head_tilt=0,
                                head_turn=lerp(0, -20, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 3.0, 0, rot=200, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            for _sx, _nm in ((-3, "SEN1"), (3, "SEN2")):
                chars[_nm] = char(RX + _sx, 12, 0, rot=0, lean=5, head_tilt=0,
                                  armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX + 1.0, -6.0, 1.5, RX, 23.0, 3.0, 18.0, 55)
            pulse = 450 + 150 * math.sin(t * math.pi)
            li = lights(nexus=600, gate=pulse, rim=500, fill=200, core=150,
                        eva=300, eye=500)
        else:
            # 2c: Sentinel menurunkan senjata SETENGAH — ragu, pertama kalinya
            t = seg_t(f, 216, 287)
            chars["KAI"] = char(RX, 4.0, 0, rot=180, lean=4, head_tilt=-8,
                                head_turn=-20, armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 3.0, 0, rot=200, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            for _sx, _nm in ((-3, "SEN1"), (3, "SEN2")):
                chars[_nm] = char(RX + _sx, 12, 0, rot=0, lean=3,
                                  head_tilt=lerp(0, 5, smooth(t)),
                                  armL=6, armR=lerp(55, 25, smooth(t)),
                                  legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX, lerp(-4.0, -2.0, smooth(t)), 2.0,
                            RX, 8.0, 1.5, 10.0, 52)
            li = lights(nexus=1500, gate=450, rim=600, fill=200, core=150,
                        eva=300, eye=600)
        for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S3 GERBANG PUTIH (288-599) — "THE WHITE GATE" =================
    elif f < 600:
        props["scar_glow"] = True  # kilau biru TERANG sejak S3
        if f < 360:
            # 3a: tracking two-shot — Kairo + EVA berjalan BERSAMA ke gerbang
            t = seg_t(f, 288, 359)
            kai_y = lerp(4.0, 10.0, smooth(t))
            eva_y = lerp(3.0, 9.0, smooth(t))
            ph = f * 0.35
            c = walk_cycle(ph, 26)
            chars["KAI"] = char(RX, kai_y, c["bob"], rot=180, lean=8, head_tilt=0,
                                armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            chars["EVA"] = char(RX + 2.0, eva_y, c["bob"], rot=180, lean=2, head_tilt=0,
                                armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            for _sx, _nm in ((-3, "SEN1"), (3, "SEN2")):
                chars[_nm] = char(RX + _sx, 12, 0, rot=0, lean=3, head_tilt=5,
                                  armL=6, armR=25, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX + 3.0, kai_y - 8.0, 1.6, RX + 1.0, kai_y + 1.0, 1.4,
                            6.0, 50)
            li = lights(nexus=400, gate=500, rim=400, fill=200, core=150,
                        eva=lerp(300, 600, smooth(t)), eye=400)
        elif f < 480:
            # 3b: gerbang membesar; 2 Sentinel BERHENTI di ambang — tidak masuk
            t = seg_t(f, 360, 479)
            kai_y = lerp(10.0, 17.0, smooth(t))
            eva_y = lerp(9.0, 16.0, smooth(t))
            ph = f * 0.35
            c = walk_cycle(ph, 26)
            chars["KAI"] = char(RX, kai_y, c["bob"], rot=180, lean=8, head_tilt=0,
                                armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            chars["EVA"] = char(RX + 2.0, eva_y, c["bob"], rot=180, lean=2, head_tilt=0,
                                armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            for _sx, _nm in ((-3, "SEN1"), (3, "SEN2")):
                chars[_nm] = char(RX + _sx, 20, 0, rot=180, lean=3, head_tilt=5,
                                  armL=6, armR=25, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX + 2.0, kai_y - 7.0, 1.5, RX, 18.0, 3.0, 12.0, 55)
            li = lights(nexus=300, gate=550, rim=300, fill=200, core=150,
                        eva=600, eye=300)
        else:
            # 3c: melewati ambang — kamera dari DALAM aula menatap balik ke gerbang
            # FIX R1: panel gerbang opak HARUS 0 di sini — kalau 1.0, kamera di
            # dalam aula hanya melihat panel putih polos (Ronde 1: mean 192,3).
            gate_open = 0.0
            t = seg_t(f, 480, 599)
            kai_y = lerp(17.0, 24.5, smooth(t))
            eva_y = lerp(16.0, 23.5, smooth(t))
            ph = f * 0.35
            c = walk_cycle(ph, 26)
            chars["KAI"] = char(RX, kai_y, c["bob"], rot=180, lean=8, head_tilt=0,
                                armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            chars["EVA"] = char(RX + 2.0, eva_y, c["bob"], rot=180, lean=2, head_tilt=0,
                                armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            for _sx, _nm in ((-3, "SEN1"), (3, "SEN2")):
                chars[_nm] = char(RX + _sx, 20, 0, rot=180, lean=3, head_tilt=5,
                                  armL=6, armR=25, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX, 30.0, 2.0, RX, 22.0, 1.5, 8.0, 50)
            li = lights(nexus=lerp(300, 100, smooth(t)), gate=600, rim=200,
                        fill=200, core=150, eva=600, eye=200,
                        hall=lerp(0, 150, smooth(t)))
        for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S4 AULA MEMORI (600-863) =================
    elif f < 864:
        props["scar_glow"] = True
        if f < 672:
            # 4a: slow dolly, reveal aula — barisan 213 Kairo membeku
            t = seg_t(f, 600, 671)
            chars["KAI"] = char(RX, 26.0, 0, rot=180, lean=4, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 25.5, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX + 1.0, lerp(28.0, 32.0, smooth(t)), 1.8,
                            RX, 40.0, 1.5, lerp(12.0, 20.0, smooth(t)), 48)
            li = lights(nexus=0, gate=300, rim=0, fill=150, core=0,
                        eva=400, hall=300)
        elif f < 768:
            # 4b: dolly menyusuri barisan — Kairo berjalan pelan di antara mereka
            t = seg_t(f, 672, 767)
            kai_y = lerp(26.0, 28.5, smooth(t))
            ph = f * 0.30
            c = walk_cycle(ph, 18)
            chars["KAI"] = char(RX, kai_y, c["bob"], rot=180, lean=5, head_tilt=0,
                                armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            chars["EVA"] = char(RX + 2.0, kai_y - 0.5, c["bob"], rot=180, lean=2,
                                head_tilt=0, armL=c["armL"], armR=c["armR"],
                                legL=c["legL"], legR=c["legR"])
            chars_cam = cam(RX + 6.0, kai_y - 6.0, 1.7, RX - 6.0, kai_y + 8.0, 1.4,
                            10.0, 50)
            li = lights(nexus=0, gate=250, rim=0, fill=150, core=0,
                        eva=400, hall=320)
        else:
            # 4c: wide aula — Kairo kecil di antara barisan yang memudar ke putih
            t = seg_t(f, 768, 863)
            chars["KAI"] = char(RX, 28.5, 0, rot=180, lean=4, head_tilt=0,
                                head_turn=lerp(0, 30, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 29.5, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX, 24.0, 3.0, RX, 55.0, 1.5, 30.0, 42)
            li = lights(nexus=0, gate=250, rim=0, fill=150, core=0,
                        eva=400, hall=350)
        for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S5 NEXUS MENGEJAR (864-1055) =================
    elif f < 1056:
        props["scar_glow"] = True
        nexus_flicker = True  # kedip merah merayap dari ambang
        if f < 936:
            # 5a: tilt-up dari lantai aula ke ambang — dinding mulai berkedip merah
            # FIX R3: kamera lama di (RX, 30, z) = TEPAT di belakang Kairo
            # (80, 28,5) — badannya memblokir tilt-up (frame blur biru-abu /
            # putih polos, Ronde 4). Kamera geser +3 m ke samping (RX+3) supaya
            # gerbang bersih di frame; Kairo/EVA di tepi kiri.
            t = seg_t(f, 864, 935)
            chars["KAI"] = char(RX, 28.5, 0, rot=180, lean=4, head_tilt=lerp(0, -10, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 29.5, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX + 3.0, 30.0, lerp(1.0, 3.0, smooth(t)),
                            RX, 24.0, lerp(1.5, 6.0, smooth(t)), 8.0, 50, roll=9)
            hr = 900 if (f // 6) % 2 == 0 else 100
            li = lights(nexus=300, gate=250, rim=0, fill=150, core=0,
                        eva=400, hall=300, hallred=hr)
        elif f < 1008:
            # 5b: wide aula — kedip merah menyebar, 213 Kairo BELUM bergerak
            t = seg_t(f, 936, 1007)
            chars["KAI"] = char(RX, 28.5, 0, rot=180, lean=4, head_tilt=-10,
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 29.5, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX, 26.0, 2.5, RX, 50.0, 1.5, 25.0, 46)
            hr = 900 if (f // 4) % 2 == 0 else 100
            li = lights(nexus=400, gate=250, rim=0, fill=150, core=0,
                        eva=400, hall=300, hallred=hr)
        else:
            # 5c: close Kairo + EVA di tengah kedip — setengah putih setengah merah
            # FIX R3: fokus lama 3,0 — subjek di 1,1-1,8 m dari kamera (lensa 62,
            # f/2,0) = wajah blur. Fokus 1,5 m (tengah Kairo 1,12 / EVA 1,8).
            t = seg_t(f, 1008, 1055)
            chars["KAI"] = char(RX, 28.5, 0, rot=180, lean=4, head_tilt=-10,
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 2.0, 29.5, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX + 1.0, 28.0, 1.6, RX + 0.5, 30.0, 1.5, 1.5, 62)
            hr = 800 if (f // 3) % 2 == 0 else 150
            li = lights(nexus=500, gate=250, rim=0, fill=150, core=0,
                        eva=400, hall=280, hallred=hr)
        for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S6 SENTUHAN PERTAMA (1056-1199) =================
    elif f < 1200:
        props["scar_glow"] = True
        scar_wave = smooth(seg_t(f, 1056, 1199))  # cahaya menjalar baris demi baris
        if f < 1120:
            # 6a: ECU bekas luka — EVA MENYENTUH (pertama kalinya)
            # FIX R2: kamera lama 0,4 m dari wajah (fokus 2,6 m) = blur total
            # f/2.0 (Ronde 2). Kamera mundur ke 2,5 m + fokus = jarak (2,5).
            # EVA mendekat ke (RX+0,6, 28,2) khusus 6a supaya tangan terangkatnya
            # masuk frame kanan (posisi lama 1,5 m tidak terjangkau lengannya).
            t = seg_t(f, 1056, 1119)
            chars["KAI"] = char(RX, 28.5, 0, rot=0, lean=6, head_tilt=-4, head_turn=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 0.6, 28.2, 0, rot=200, lean=3, head_tilt=4,
                                armL=5, armR=lerp(5, 55, smooth(t)), legL=0, legR=0)
            chars_cam = cam(lerp(RX + 0.3, RX + 0.15, smooth(t)), lerp(26.0, 26.1, smooth(t)),
                            lerp(1.65, 1.62, smooth(t)),
                            RX, 28.5, 1.6, lerp(2.5, 2.4, smooth(t)), lerp(75, 85, t))
            li = lights(nexus=0, gate=250, rim=0, fill=150, core=0,
                        eva=600, hall=300)
        else:
            # 6b: ECU -> wide gelombang cahaya — cahaya biru menyapu aula
            # FIX R1: kamera TETAP di sisi aula (y 29.6->24.5) — jalur lama
            # (y 26->20) MENEMBUS panel gerbang opak di y=23.55, frame jadi
            # putih polos (Ronde 1: mean 214,0). Target tetap barisan (y=35).
            t = seg_t(f, 1120, 1199)
            chars["KAI"] = char(RX, 28.5, 0, rot=0, lean=6, head_tilt=-4, head_turn=0,
                                armL=5, armR=55, legL=0, legR=0)
            chars["EVA"] = char(RX + 1.3, 28.5, 0, rot=200, lean=3, head_tilt=4,
                                armL=5, armR=55, legL=0, legR=0)
            chars_cam = cam(RX + 0.5, lerp(29.6, 24.5, smooth(t)), lerp(1.62, 3.0, smooth(t)),
                            RX, 35.0, 1.5, lerp(2.8, 15.0, smooth(t)), lerp(62, 48, t))
            li = lights(nexus=0, gate=250, rim=0, fill=150, core=0,
                        eva=lerp(600, 800, smooth(t)), hall=300)
        for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S7 MEREKA MEMILIH (1200-1319) =================
    elif f < 1320:
        props["scar_glow"] = True
        props["kairo213_eyes"] = True  # mata 213 Kairo TERBUKA — BIRU, serentak
        scar_wave = 1.0  # gelombang selesai; semua bekas luka menyala
        if f < 1260:
            # 7a: dolly-in ke mata Kairo -> ECU
            # FIX R2: fokus lama 2,6->1,8 berlawanan arah dengan jarak
            # (1,53->2,21 m) — f/2.0 jadi blur. Fokus kini = jarak (1,55->2,2);
            # kamera digeser supaya jaraknya 1,5->2,2 m dari wajah (hero di 28,5).
            t = seg_t(f, 1200, 1259)
            chars["KAI"] = char(RX, 28.5, 0, rot=0, lean=4, head_tilt=0,
                                head_turn=lerp(0, 30, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 1.3, 28.5, 0, rot=200, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(lerp(RX + 0.3, RX + 0.15, smooth(t)), lerp(27.0, 26.3, smooth(t)),
                            lerp(1.65, 1.62, smooth(t)),
                            RX, 28.5, 1.55, lerp(1.55, 2.2, smooth(t)), lerp(70, 85, t))
            li = lights(nexus=0, gate=250, rim=0, fill=150, core=0,
                        eva=700, hall=320)
        else:
            # 7b: wide aula — semua mata terbuka, aula berubah biru
            t = seg_t(f, 1260, 1319)
            chars["KAI"] = char(RX, 28.5, 0, rot=0, lean=4, head_tilt=0, head_turn=30,
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 1.3, 28.5, 0, rot=200, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX, 24.0, 3.5, RX, 55.0, 1.5, 30.0, 42)
            li = lights(nexus=0, gate=250, rim=0, fill=150, core=0,
                        eva=900, hall=350)
        for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S8 TWIST (1320-1439) =================
    else:
        props["scar_glow"] = True
        props["kairo213_eyes"] = True
        props["nexus_face"] = True  # wajah NEXUS kecil berkedip dari luar gerbang
        scar_wave = 1.0
        kairo213_step = smooth(seg_t(f, 1320, 1379))  # SATU LANGKAH serentak
        if f < 1380:
            # 8a: wide hero — 213 Kairo melangkah serentak ke arah ambang
            t = seg_t(f, 1320, 1379)
            chars["KAI"] = char(RX, 28.5, 0, rot=180, lean=6, head_tilt=0,
                                head_turn=30, armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 1.3, 29.5, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX + 0.6, lerp(24.0, 25.0, smooth(t)), lerp(1.3, 1.6, smooth(t)),
                            RX, 45.0, 1.5, 22.0, lerp(50, 48, t))
            li = lights(nexus=200, gate=300, rim=0, fill=150, core=0,
                        eva=800, hall=350)
        else:
            # 8b: pull-back lambat -> hitam + end card (f1380-1439, ASS)
            t = seg_t(f, 1380, 1439)
            chars["KAI"] = char(RX, 28.5, 0, rot=180, lean=6, head_tilt=0,
                                head_turn=30, armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(RX + 1.3, 29.5, 0, rot=180, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX + 0.6, lerp(24.0, 28.0, smooth(t)), lerp(1.6, 2.5, smooth(t)),
                            RX, 45.0, 1.5, lerp(22.0, 26.0, smooth(t)), lerp(48, 42, t))
            # aula meredup menuju hitam (end card di atas hitam)
            dim = 1.0 - 0.92 * smooth(seg_t(f, 1400, 1439))
            # FIX R2: emisi dinding 0,25 TIDAK ikut dim lampu — tanpa ini akhir
            # film mentok mean ~86 (abu-abu, bukan hitam). Ikutkan dim ke emisi.
            wall_emit = 0.25 * dim
            li = lights(nexus=200 * dim, gate=300 * dim, rim=0, fill=150 * dim,
                        core=0, eva=800 * dim, hall=350 * dim)
        for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()

    # pastikan SEMUA karakter ada di tiap baris (0 frame kosong)
    for _p in ALL_CHARS:
        if _p not in chars:
            chars[_p] = hidden()

    rows.append({"f": f, "t": round(f / 24.0, 4), "chars": chars, "lights": li,
                 "cam": chars_cam, "props": props, "flash_white": flash_white,
                 "gate_open": round(gate_open, 3), "wall_emit": round(wall_emit, 4),
                 "nexus_flicker": bool(nexus_flicker),
                 "scar_wave": round(scar_wave, 3),
                 "kairo213_step": round(kairo213_step, 3)})


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "plan.json")
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    print(f"WROTE {out}: {len(rows)} rows")
    # self-checks
    assert len(rows) == N
    assert rows[0]["f"] == 0 and rows[-1]["f"] == N - 1
    flashes = [r["f"] for r in rows if r["flash_white"]]
    assert flashes == [], f"flash frames (harus kosong di Ep 3): {flashes}"
    empty_rows = [r["f"] for r in rows if not r["chars"]]
    assert not empty_rows, f"frame kosong: {empty_rows}"
    missing = [(r["f"], [p for p in ALL_CHARS if p not in r["chars"]])
               for r in rows if any(p not in r["chars"] for p in ALL_CHARS)]
    assert not missing, f"karakter hilang: {missing[:5]}"
    gate = [r["f"] for r in rows if r["gate_open"] > 0]
    # FIX R1: gate_open 0 HANYA di S3c (480-599, kamera dari dalam aula);
    # di luar itu 1.0 di semua frame.
    assert gate == list(range(0, 480)) + list(range(600, N)), \
        f"gate_open: {gate[:1]}..{gate[-1:]} (harus 0-479 + 600-1439)"
    scar = [r["f"] for r in rows if r["props"]["scar_glow"]]
    assert scar[0] == 288 and scar[-1] == N - 1, f"scar_glow: {scar[0]}-{scar[-1]}"
    laser_e = [r["f"] for r in rows if r["props"]["laser_eva"]]
    laser_k = [r["f"] for r in rows if r["props"]["laser_kairo"]]
    assert laser_e == list(range(0, 24)), f"laser_eva: {laser_e[:1]}..{laser_e[-1:]}"
    assert laser_k == list(range(24, 72)), f"laser_kairo: {laser_k[:1]}..{laser_k[-1:]}"
    wave = [(r["f"], r["scar_wave"]) for r in rows if r["scar_wave"] > 0]
    assert wave[0][0] == 1058, f"scar_wave mulai: {wave[0]}"  # f1056-1057 = 0.000 (awal ramp, dibulatkan)
    assert wave[-1] == (N - 1, 1.0), f"scar_wave akhir: {wave[-1]}"
    assert rows[1199]["scar_wave"] == 1.0, "scar_wave harus 1.0 di f1199"
    flick = [r["f"] for r in rows if r["nexus_flicker"]]
    assert flick == list(range(864, 1056)), f"nexus_flicker: {flick[:1]}..{flick[-1:]}"
    eyes = [r["f"] for r in rows if r["props"]["kairo213_eyes"]]
    assert eyes[0] == 1200 and eyes[-1] == N - 1, f"kairo213_eyes: {eyes[0]}-{eyes[-1]}"
    step = [(r["f"], r["kairo213_step"]) for r in rows if r["kairo213_step"] > 0]
    assert step[0][0] == 1321, f"kairo213_step mulai: {step[0]}"
    assert rows[1379]["kairo213_step"] == 1.0, "kairo213_step harus 1.0 di f1379"
    assert rows[1439]["kairo213_step"] == 1.0
    face = [r["f"] for r in rows if r["props"]["nexus_face"]]
    assert face[0] == 1320 and face[-1] == N - 1, f"nexus_face: {face[0]}-{face[-1]}"
    # FIX R2: emisi dinding 0.25 di semua frame, meredup bersama dim 8b.
    assert rows[0]["wall_emit"] == 0.25 and rows[1399]["wall_emit"] == 0.25
    assert rows[1439]["wall_emit"] == 0.02, f"wall_emit akhir: {rows[1439]['wall_emit']}"
    print(f"CHECK OK: 0 flash, semua {len(rows)} baris punya "
          f"{len(ALL_CHARS)} karakter, 0 frame kosong")
    print(f"  gate_open=1: 0-479 + 600-1439 ({len(gate)} frame, 0 di S3c 480-599)")
    print(f"  scar_glow: {scar[0]}-{scar[-1]} ({len(scar)} frame)")
    print(f"  laser_eva: {laser_e[0]}-{laser_e[-1]} | laser_kairo: {laser_k[0]}-{laser_k[-1]}")
    print(f"  scar_wave naik: {wave[0][0]}-{1199} (1.0 sejak f1199)")
    print(f"  nexus_flicker: {flick[0]}-{flick[-1]} ({len(flick)} frame)")
    print(f"  kairo213_eyes: {eyes[0]}-{eyes[-1]} ({len(eyes)} frame)")
    print(f"  kairo213_step naik: {step[0][0]}-1379 (1.0 sejak f1379)")
    print(f"  nexus_face: {face[0]}-{face[-1]} ({len(face)} frame)")


if __name__ == "__main__":
    main()
