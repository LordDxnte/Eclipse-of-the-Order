"""
ECLIPSE OF THE ORDER 
─────────────────────────────────────────────
CONTROLS:
  WASD / Arrow Keys   — Move
  SPACE               — Jump (double-jump when upgraded)
  SHIFT               — Dash-roll
  LEFT CLICK / F      — Slash (or Execute stunned foe)
  RIGHT CLICK         — Void Bolt (ranged) (Costs Mana)
  G                   — Parry
  Q                   — Void Blink (upgrade)
  C                   — Soul Rend ultimate (upgrade)
  E                   — Interact / Use door
  P / ESC             — Pause
  F11                 — Toggle Fullscreen
"""

import pygame
import sys
import math
import random
import os, sys

def asset(filename):
    """Resolve asset path whether running as script or PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS          # PyInstaller temp folder
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)

# ─────────────────────────────────────────────────────────────────────────────
#  INIT & WINDOW
# ─────────────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.set_num_channels(32)

WIDTH, HEIGHT = 1920, 1080
RESOLUTIONS   = [(1280, 720), (1366, 768), (1600, 900), (1920, 1080), (2560, 1440)]
curr_res_idx  = 3
WINDOW_W, WINDOW_H = RESOLUTIONS[curr_res_idx]

is_fullscreen = False
flags = pygame.FULLSCREEN if is_fullscreen else 0
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)
pygame.display.set_caption("Eclipse of the Order")
clock  = pygame.time.Clock()

def get_mouse_pos(cam_x=0, cam_y=0):
    mx, my = pygame.mouse.get_pos()
    sw, sh = screen.get_size()                # use the LIVE screen size (handles fullscreen correctly)
    if sw <= 0 or sh <= 0: sw, sh = WINDOW_W, WINDOW_H
    return (mx * WIDTH / sw) + cam_x, (my * HEIGHT / sh) + cam_y

# ─── Palette ──────────────────────────────────────────────────────────────────
BG         = (4,   2,  10)
C_INK      = (12,  8,  22)
C_VOID     = (20,   0,  45)
C_STONE    = (48,  42,  58)
C_STONE2   = (68,  60,  80)
C_PARCH    = (205, 190, 155)
C_PARCH2   = (165, 145, 108)
C_SEPIA    = (115,  85,  45)
C_RUNEGLOW = (175, 115, 255)
C_TORCHA   = (255, 175,  55)
C_TORCHB   = (255, 115,  18)
C_WHITE    = (238, 232, 255)
C_RED      = (195,  35,  35)
C_DKRED    = ( 88,   8,   8)
C_ORANGE   = (255, 138,   0)
C_YELLOW   = (252, 218,   0)
C_CYAN     = ( 75, 215, 252)
C_PURPLE   = (155,  55, 252)
C_GREY     = ( 75,  75,  88)
C_GOLD     = (252, 212,   0)
C_HOLY     = (252, 242, 175)
C_DARKGOLD = (130, 100,   0)
C_PLAGUE   = ( 60, 200,  80)
C_ICE      = (140, 225, 255)
C_BLOOD    = (155,   0,  25)

# ─────────────────────────────────────────────────────────────────────────────
#  FONTS 
# ─────────────────────────────────────────────────────────────────────────────
F_TITLE = pygame.font.SysFont("couriernew", 78, bold=True)
F_BIG   = pygame.font.SysFont("couriernew", 57, bold=True)
F_MED   = pygame.font.SysFont("couriernew", 30, bold=True)
F_SM    = pygame.font.SysFont("couriernew", 20, bold=True)
F_TINY  = pygame.font.SysFont("couriernew", 16)

# ─────────────────────────────────────────────────────────────────────────────
#  PERSISTENT META 
# ─────────────────────────────────────────────────────────────────────────────
import json, os, sys, traceback

# ── Asset path resolver ───────────────────────────────────────────────────────
# Works both when running as a plain .py script AND when bundled with PyInstaller.
def asset(filename):
    """Return the full path to a file inside the assets/ folder."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle — assets are in sys._MEIPASS/assets/
        base = sys._MEIPASS
    else:
        # Running as a normal script — assets sit next to the .py file
        try:
            base = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base = os.path.abspath(".")
    return os.path.join(base, "assets", filename)

# Default meta is ALSO the schema — anything not in the on-disk save falls back here.
META_DEFAULTS = {
    "divine_essence":  0,
    "total_runs":      0,
    "bosses_defeated": 0,
    "total_kills":     0,
    "best_combo":      0,
    "upg_max_hp":      5,
    "upg_dash_cd":     90,
    "upg_double_jump": False,
    "upg_blink":       False,
    "upg_ult":         False,
    "upg_parry_window":12,
    "upg_relic_slots": 2,
    "curse_level":     0,
}
meta = dict(META_DEFAULTS)

# Save file lives next to the exe / script — never inside a PyInstaller bundle.
try:
    if getattr(sys, 'frozen', False):
        # PyInstaller: write save next to the actual executable
        _SAVE_DIR = os.path.dirname(sys.executable)
    else:
        _SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _SAVE_DIR = os.path.abspath(".")
SAVE_PATH = os.path.join(_SAVE_DIR, "eclipse_save.json")

# Soft on-screen "GAME SAVED" notification timer (in frames). Shown silently in HUD corner.
_save_flash_t = 0

def save_meta():
    """Write meta to disk. Silent on failure — never crash the game over a save error."""
    global _save_flash_t
    try:
        tmp = SAVE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        os.replace(tmp, SAVE_PATH)              # atomic rename so a crash mid-write doesn't corrupt
        _save_flash_t = 80                      # ~1.3s flash
    except Exception:
        traceback.print_exc()                   # log but never crash

def load_meta():
    """Load meta from disk, merging on top of defaults so older saves still work."""
    if not os.path.exists(SAVE_PATH): return
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for k, v in data.items():
                # Only accept keys we know about and types that match the default
                if k in META_DEFAULTS and type(v) is type(META_DEFAULTS[k]):
                    meta[k] = v
    except Exception:
        traceback.print_exc()

load_meta()                                     # restore on startup

# ─────────────────────────────────────────────────────────────────────────────
#  RELICS  
# ─────────────────────────────────────────────────────────────────────────────
RELIC_DEFS = {
    "void_heart":    {"name": "Void Heart",       "desc": "+2 Max HP this run",         "color": C_BLOOD,   "icon": "♥"},
    "obsidian_edge": {"name": "Obsidian Edge",    "desc": "Attacks deal +1 dmg",         "color": C_GREY,    "icon": "◆"},
    "swiftness":     {"name": "Wraith's Grace",   "desc": "Dash has 2 charges",          "color": C_CYAN,    "icon": "»"},
    "soulsucker":    {"name": "Soul Siphon",      "desc": "Kills restore 1 HP",          "color": C_PURPLE,  "icon": "★"},
    "thorn_mantle":  {"name": "Thorn Mantle",     "desc": "Parry stuns melee enemies",   "color": C_PLAGUE,  "icon": "✦"},
    "void_echo":     {"name": "Void Echo",        "desc": "Blink damages in radius",     "color": C_RUNEGLOW,"icon": "◉"},
    "cursed_blade":  {"name": "Cursed Blade",     "desc": "+50% dmg, -1 max hp",         "color": C_RED,     "icon": "†"},
    "gilded_soul":   {"name": "Gilded Soul",      "desc": "+25% essence gain",           "color": C_GOLD,    "icon": "⊕"},
    "iron_will":     {"name": "Iron Will",        "desc": "First lethal hit → 1 hp",     "color": C_WHITE,   "icon": "⊗"},
    "plague_touch":  {"name": "Plague Touch",     "desc": "Attacks poison enemies",      "color": C_PLAGUE,  "icon": "⚗"},
}

run = {
    "floor":          1,
    "kills":          0,
    "relics":         [],
    "relic_offered":  [],
    "curse_active":   False,
    "iron_will_used": False,
    "double_jump_used": False,
    "sanctum_return_floor": None,   # floor to return to after mid-run sanctum visit
}

def run_has(relic): return relic in run["relics"]
def run_atk_bonus(): return (1 if run_has("obsidian_edge") else 0) + (1 if run_has("cursed_blade") else 0)
def run_hp_bonus():  return (2 if run_has("void_heart") else 0) - (1 if run_has("cursed_blade") else 0)
def run_essence_mult(): return 1.25 if run_has("gilded_soul") else 1.0

def get_diff():
    base = 0.4 if meta["bosses_defeated"] == 0 else 0.8 + (meta["bosses_defeated"] * 0.05)
    return base + ((run.get("floor", 1) - 1) * 0.1) + (meta["curse_level"] * 0.2)

# ─────────────────────────────────────────────────────────────────────────────
#  AUDIO
# ─────────────────────────────────────────────────────────────────────────────
class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.ch_bgm = pygame.mixer.Channel(0)
        self.ch_hb  = pygame.mixer.Channel(1)
        self.sfx_vol = 0.9
        self.bgm_vol = 0.35

    def load(self, name, path):
        try:    self.sounds[name] = pygame.mixer.Sound(path)
        except: self.sounds[name] = None

    def play(self, name, vol=0.5):
        s = self.sounds.get(name)
        if s: s.set_volume(vol * self.sfx_vol); pygame.mixer.find_channel(True).play(s)

    def stop(self, name):
        s = self.sounds.get(name)
        if s: s.stop()

    def bgm(self, name, vol=None):
        if vol is not None: self.bgm_vol = vol
        s = self.sounds.get(name)
        if s: self.ch_bgm.play(s, loops=-1); self.ch_bgm.set_volume(self.bgm_vol)

    def set_bgm_vol(self, v):
        self.bgm_vol = max(0.0, min(1.0, v))
        self.ch_bgm.set_volume(self.bgm_vol)

    def set_sfx_vol(self, v):
        self.sfx_vol = max(0.0, min(1.0, v))

audio = AudioManager()
for n, p in [("slash","slash.ogg"),("dash","dash.wav"),("parry","parry.wav"),
             ("hit","hit.wav"),("blink","blink.wav"),("heartbeat","heartbeat.wav"),
             ("bgm_explore","bgm_explore.wav"),("bgm_boss","bgm_boss.wav"),
             ("levelup","levelup.wav"),("relic","relic.wav")]:
    audio.load(n, asset(p))

# ─────────────────────────────────────────────────────────────────────────────
#  PNG ASSET LOADING & CUSTOM TEXTURES
# ─────────────────────────────────────────────────────────────────────────────
def _try_load_image(path):
    try: return pygame.image.load(path).convert_alpha()
    except: return None

def _load_scale(path, height):
    try:
        img = pygame.image.load(path).convert_alpha()
        ratio = height / img.get_height()
        new_w = max(1, int(img.get_width() * ratio))
        return pygame.transform.scale(img, (new_w, height))
    except:
        return None

def _load_exact(path, w, h):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (w, h))
    except:
        return None

_SKY_IMG = _try_load_image(asset("sky.png"))
_MOON_IMG = _try_load_image(asset("moon.png"))
_CASTLES_IMG = _try_load_image(asset("bg_castles.png"))
_RUINS_IMG = _try_load_image(asset("mg_ruins.png"))
_NPC_IMG = _load_scale(asset("inevitable.png"), 100) 

_PLAYER_H = 78
_PLAYER_FRAMES_R = []
for _i in range(1, 6):
    f = _load_scale(asset(f"run{_i}.png"), _PLAYER_H)
    if f: _PLAYER_FRAMES_R.append(f)
_PLAYER_FRAMES_L = [pygame.transform.flip(f, True, False) for f in _PLAYER_FRAMES_R]

_SLASH_IMG  = _load_scale(asset("slash.png"), 80)
_SLASH_ULT  = _load_scale(asset("slash.png"), 130)

_GRUNT_H = 65
_GRUNT_FRAMES_R = []
for _i in range(1, 6):
    f = _load_scale(asset(f"thug{_i}.png"), _GRUNT_H)
    if f: _GRUNT_FRAMES_R.append(f)
if not _GRUNT_FRAMES_R: _GRUNT_FRAMES_R = [None]
_GRUNT_FRAMES_L = [pygame.transform.flip(f, True, False) if f else None for f in _GRUNT_FRAMES_R]

_SERAPH_IMG_R = _load_scale(asset("seraph.png"), 90)
_SERAPH_IMG_L = pygame.transform.flip(_SERAPH_IMG_R, True, False) if _SERAPH_IMG_R else None

_BOSS_H = 180
_BOSS_FRAMES_R = []
for _i in range(1, 6):
    f = _load_scale(asset(f"boss_p1_walk{_i}.png"), _BOSS_H)
    if f: _BOSS_FRAMES_R.append(f)
if not _BOSS_FRAMES_R:
    _s = pygame.Surface((110,180),pygame.SRCALPHA); _s.fill((200,180,0,180))
    _BOSS_FRAMES_R = [_s]
_BOSS_FRAMES_L = [pygame.transform.flip(f, True, False) for f in _BOSS_FRAMES_R]

_PROJ_FIREBALL = _load_exact(asset("proj_fireball.png"), 36, 18)
_PROJ_DARKWAVE = _load_exact(asset("proj_darkwave.png"), 70, 34)
_DOOR_IDLE = _load_exact(asset("door_idle.png"), 90, 150)
_DOOR_OPEN = _load_exact(asset("door_open.png"), 90, 150)
_TORCH_IMG = _load_scale(asset("torch.png"), 48)

_FLOOR_IMG = None 
_PLATFORM_IMG = None
_HEAL_SHRINE_IMG = _load_scale(asset("heal_shrine.png"), 90)

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL GAME STATE
# ─────────────────────────────────────────────────────────────────────────────
STATE      = "main_menu"
menu_view  = "main"
PREV_STATE = "main_menu"

player             = None
platforms          = []
enemies            = []
player_projs       = []
env_objects        = []
camera_x           = 0.0

hit_stop_timer     = 0.0
time_scale         = 1.0
bullet_time_timer  = 0
screen_shake       = 0

combo_count        = 0
combo_timer        = 0
COMBO_WINDOW       = 200
kill_streak        = 0          # kills without taking damage
kill_streak_best   = 0          # best streak this run
floor_time_s       = 0.0        # seconds spent on current floor

announce_queue     = []
_hb_playing = False
transition_t       = 0          # frames remaining of black-fade cover; 0 = no transition
hit_flash_t        = 0          # red screen flash on damage (frames)

def announce(text, color=C_YELLOW, dur=130):
    announce_queue.append([text, color, dur, dur])

def add_combo(n=1):
    global combo_count, combo_timer
    combo_count += n
    combo_timer  = COMBO_WINDOW
    if combo_count > meta["best_combo"]:
        meta["best_combo"] = combo_count

def combo_rank():
    if combo_count >= 40: return "S+", C_GOLD
    if combo_count >= 25: return "S",  C_GOLD
    if combo_count >= 15: return "A",  C_PURPLE
    if combo_count >= 8:  return "B",  C_CYAN
    if combo_count >= 4:  return "C",  C_ORANGE
    return "D", C_GREY

def draw_text(surf, text, font, color, x, y, center=False, shadow=True):
    if shadow:
        sh = font.render(text, True, (0,0,0))
        surf.blit(sh, (x - sh.get_width()//2 + 2 if center else x+2, y+2))
    t = font.render(text, True, color)
    surf.blit(t, (x - t.get_width()//2 if center else x, y))

def glow(surf, color, cx, cy, r, a=70):
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    
    # Draw multiple concentric circles to create a soft gradient
    steps = 5 
    for i in range(steps):
        radius = int(r * (1 - i/steps))
        # Distribute the total alpha across the layers
        layer_alpha = int(a / steps) 
        pygame.draw.circle(s, (*color, layer_alpha), (r, r), radius)
        
    surf.blit(s, (cx-r, cy-r), special_flags=pygame.BLEND_RGBA_ADD)

def draw_btn(surf, text, font, color, rect, hover_color=None, disabled=False):
    if disabled: color = C_GREY; hover_color = C_GREY
    mx, my = get_mouse_pos()
    c = (hover_color or C_WHITE) if rect.collidepoint(mx,my) and not disabled else color
    bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    bg.fill((c[0]//8, c[1]//8, c[2]//8, 160))
    surf.blit(bg, rect.topleft)
    pygame.draw.rect(surf, c, rect, 2, border_radius=4)
    t = font.render(text, True, c)
    surf.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    return rect.collidepoint(mx, my) and not disabled

# ─────────────────────────────────────────────────────────────────────────────
#  PROCEDURAL ENVIRONMENT GENERATORS & FALLBACKS
# ─────────────────────────────────────────────────────────────────────────────
FLOOR_W = 7800 
GROUND_Y = 810  

def gen_platforms(rng, floor_num):
    plats = [(200, GROUND_Y-120, 250), (550, GROUND_Y-220, 250), (900, GROUND_Y-120, 200)]
    x = 1200
    while x < FLOOR_W - 400:
        gap = rng.randint(80, 160) + floor_num * 10
        w = rng.randint(180, 400)
        y = rng.randint(GROUND_Y-260, GROUND_Y-100)
        plats.append((x, y, w))
        x += w + gap
    return plats

def gen_enemies(rng, floor_num, plat_list):
    specs = []
    difficulty = floor_num + meta["curse_level"]
    
    max_seraphs = 0 if floor_num == 1 else (1 if floor_num == 2 else 2 if floor_num == 3 else 4 + floor_num)
    seraphs_spawned = 0
    max_ents = 20 if meta["bosses_defeated"] == 0 else 999
    ents_spawned = 0

    # Guarantee more enemies per platform, especially early on
    for i, (px, py, pw) in enumerate(plat_list):
        if ents_spawned >= max_ents: break
        if px < 400 or px > FLOOR_W - 600: continue
        
        spawn_chance = 0.75 if floor_num == 1 else 0.40
        
        if rng.random() < spawn_chance or len(specs) == 0:
            etype = "grunt"
            if meta["upg_blink"] and rng.random() < 0.35: 
                etype = "bulwark"
            elif difficulty >= 3 and rng.random() < 0.20: 
                etype = "wraith"
            patrol_l = max(0, px - rng.randint(50, 150))
            patrol_r = px + pw + rng.randint(50, 150)
            specs.append({"type": etype, "x": px + pw//2, "y": GROUND_Y - 70, "pl": patrol_l, "pr": patrol_r})
            ents_spawned += 1
            
        if rng.random() < 0.40 and seraphs_spawned < max_seraphs and (meta["bosses_defeated"] > 0 or floor_num > 2):
            specs.append({"type": "seraph", "x": px + pw//2, "y": py - 140})
            seraphs_spawned += 1
            ents_spawned += 1

    elite_spacing = 1000 if meta["bosses_defeated"] == 0 else 700
    for ex in range(1200, FLOOR_W - 600, elite_spacing):
        if ents_spawned >= max_ents: break
        if rng.random() < 0.4:
            if meta["upg_blink"] and rng.random() < 0.5:
                etype = "bulwark_elite"
            elif difficulty >= 2 and meta["bosses_defeated"] > 0 and seraphs_spawned < max_seraphs:
                etype = "seraph_elite"
                seraphs_spawned += 1
            else:
                etype = "grunt"
            specs.append({"type": etype, "x": ex, "y": GROUND_Y - 70, "pl": ex - 150, "pr": ex + 150})
            ents_spawned += 1

    return specs

def make_bg(rng, W=6000):
    surf = pygame.Surface((W, HEIGHT))
    for row in range(HEIGHT):
        t = row / HEIGHT
        r, g, b = int(2 + t * 12), int(1 + t * 5), int(8 + t * 25)
        pygame.draw.line(surf, (r, g, b), (0, row), (W, row))
    moon_x, moon_y = W // 4, HEIGHT // 3
    pygame.draw.circle(surf, (200, 180, 255), (moon_x, moon_y), 150)
    pygame.draw.circle(surf, (10, 5, 15), (moon_x - 15, moon_y - 10), 145)
    glow(surf, (120, 80, 220), moon_x, moon_y, 300, 25)
    for i in range(0, W, rng.randint(90, 180)):
        ph = rng.randint(200, HEIGHT - 150)
        pw = rng.randint(40, 80)
        shade = rng.randint(12, 18)
        col = (shade, shade-2, shade+5)
        pygame.draw.rect(surf, col, (i, HEIGHT-ph, pw, ph))
        pygame.draw.polygon(surf, col, [(i, HEIGHT-ph), (i+pw//2, HEIGHT-ph-70), (i+pw, HEIGHT-ph)])
    return surf

def make_midground(rng, W=6000):
    surf = pygame.Surface((W, HEIGHT), pygame.SRCALPHA)
    for i in range(0, W, rng.randint(150, 280)):
        ph = rng.randint(120, 300)
        pw = rng.randint(80, 140)
        shade = rng.randint(22, 38)
        col = (shade, shade-4, shade+10, 255)
        pygame.draw.rect(surf, col, (i, HEIGHT-ph, pw, ph))
        if rng.random() > 0.3:
            pygame.draw.ellipse(surf, (0,0,0,0), (i+pw//4, HEIGHT-ph+30, pw//2, ph))
    return surf

_PROC_BG = make_bg(random.Random(0))
_PROC_MG = make_midground(random.Random(1))

def refresh_bg(seed):
    global _PROC_BG, _PROC_MG
    _PROC_BG = make_bg(random.Random(seed))
    _PROC_MG = make_midground(random.Random(seed + 1))

def draw_bg(surf, cx):
    overlap = 2
    if _SKY_IMG or _MOON_IMG or _CASTLES_IMG:
        if _SKY_IMG:
            w = _SKY_IMG.get_width()
            ox = int(cx * 0.05) % w
            surf.blit(_SKY_IMG, (-ox, 0))
            if -ox + w < WIDTH + overlap: surf.blit(_SKY_IMG, (-ox + w - overlap, 0))
            if -ox + w * 2 < WIDTH + overlap: surf.blit(_SKY_IMG, (-ox + w * 2 - overlap * 2, 0))
        else:
            surf.fill((10, 5, 20)) 
            
        if _MOON_IMG:
            mx = (WIDTH // 4) - int(cx * 0.02)
            my = HEIGHT // 3 - _MOON_IMG.get_height()//2
            surf.blit(_MOON_IMG, (mx, my))

        if _CASTLES_IMG:
            w = _CASTLES_IMG.get_width()
            ox = int(cx * 0.15) % w
            surf.blit(_CASTLES_IMG, (-ox, 0))
            if -ox + w < WIDTH + overlap: surf.blit(_CASTLES_IMG, (-ox + w - overlap, 0))
            if -ox + w * 2 < WIDTH + overlap: surf.blit(_CASTLES_IMG, (-ox + w * 2 - overlap * 2, 0))
    else:
        W = _PROC_BG.get_width()
        ox = int(cx * 0.15) % W
        surf.blit(_PROC_BG, (-ox, 0));
        if -ox + W < WIDTH: surf.blit(_PROC_BG, (-ox + W, 0))

def draw_mg(surf, cx):
    overlap = 2
    if _RUINS_IMG:
        w = _RUINS_IMG.get_width()
        ox = int(cx * 0.35) % w
        surf.blit(_RUINS_IMG, (-ox, 0))
        if -ox + w < WIDTH + overlap: surf.blit(_RUINS_IMG, (-ox + w - overlap, 0))
        if -ox + w * 2 < WIDTH + overlap: surf.blit(_RUINS_IMG, (-ox + w * 2 - overlap * 2, 0))
    else:
        W = _PROC_MG.get_width()
        ox = int(cx * 0.35) % W
        surf.blit(_PROC_MG, (-ox, 0))
        if -ox + W < WIDTH: surf.blit(_PROC_MG, (-ox + W, 0))

def make_floor_tile():
    s = pygame.Surface((128, 128))
    s.fill((25, 15, 35)) 
    for y in range(0, 128, 16):
        off = 8 if (y//16)%2 else 0
        for x in range(-16, 128, 32):
            sh = random.randint(45, 65)
            pygame.draw.rect(s, (sh, sh-15, sh+25), (x+off, y, 30, 14), border_radius=2)
    pygame.draw.line(s, (90, 70, 120), (0, 0), (128, 0), 3) 
    return s

FLOOR_TILE = make_floor_tile()

def make_plat_surf(w):
    s = pygame.Surface((w, 24), pygame.SRCALPHA)
    pygame.draw.rect(s, (35, 25, 50), (0, 0, w, 24), border_radius=3)
    pygame.draw.line(s, (90, 70, 120), (0, 0), (w, 0), 2)
    for y in range(3, 24, 7):
        off = 6 if (y//7)%2 else 0
        for x in range(-6, w, 24):
            sh = random.randint(45, 65)
            pygame.draw.rect(s, (sh, sh-15, sh+25), (x+off, y, 22, 5))
    return s

# ─────────────────────────────────────────────────────────────────────────────
#  VFX & ENTITIES
# ─────────────────────────────────────────────────────────────────────────────
particles = []
def spawn_particles(x, y, n, colors, speed=4, spread=math.pi*2, direction=None, gravity=0.3, sz=(2,6), life=(12,35)):
    for _ in range(n):
        ang = (direction if direction is not None else random.uniform(0, math.pi*2)) + random.uniform(-spread/2, spread/2)
        sp = random.uniform(speed*0.4, speed)
        particles.append({
            "x":x,"y":y,"vx":math.cos(ang)*sp,"vy":math.sin(ang)*sp,
            "g":gravity,"life":random.randint(*life),"ml":life[1],
            "sz":random.randint(*sz),"col":random.choice(colors),
        })

def update_particles(dt):
    for p in particles:
        p["x"]+=p["vx"]*dt; p["y"]+=p["vy"]*dt; p["vy"]+=p["g"]*dt; p["life"]-=dt
    particles[:] = [p for p in particles if p["life"]>0]

def draw_particles(surf, cx):
    for p in particles:
        a = max(0, int(255 * p["life"] / p["ml"]))
        r = max(1, p["sz"])
        s = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*p["col"], a), (r,r), r)
        surf.blit(s, (int(p["x"]-cx)-r, int(p["y"])-r))

class Afterimage:
    def __init__(self, img, x, y):
        self.img = img.copy(); self.x=x; self.y=y; self.a=140; self.alive=True
    def update(self): self.a -= 20; self.alive = self.a > 0
    def draw(self, surf, cx):
        if not self.alive: return
        i = self.img.copy(); i.set_alpha(max(0,self.a))
        surf.blit(i, (self.x-int(cx), self.y))

class VoidTear:
    def __init__(self, x, y, color=None):
        self.x=x; self.y=y; self.col=color or C_PURPLE; self.life=35; self.ml=35; self.alive=True
    def update(self, dt):
        self.life -= dt
        if self.life <= 0: self.alive = False
    def draw(self, surf, cx):
        if not self.alive: return
        t = self.life/self.ml; r=max(1,int(28*t)); a=int(210*t)
        sx,sy=int(self.x-cx),int(self.y)
        s=pygame.Surface((r*2+8,r*4+8),pygame.SRCALPHA)
        pygame.draw.ellipse(s,(*self.col,a),(0,0,r*2+8,r*4+8))
        pygame.draw.ellipse(s,(*C_WHITE,min(255,a+50)),(r//2,r,r+8,r*2+8),2)
        surf.blit(s,(sx-r-4,sy-r*2-4))

void_tears = []

# ── Floating damage numbers ────────────────────────────────────────────────────
_dmg_numbers = []

def spawn_dmg_number(x, y, amount, color=None, crit=False):
    """Spawn a floating damage number at world position (x, y)."""
    _dmg_numbers.append({
        "x": float(x), "y": float(y),
        "vy": -2.2 - random.uniform(0, 1.0),
        "life": 38, "ml": 38,
        "text": str(amount),
        "col": color or (C_GOLD if crit else C_WHITE),
        "crit": crit,
        "scale": 1.5 if crit else 1.0,
    })

def update_dmg_numbers(dt):
    for d in _dmg_numbers:
        d["y"] += d["vy"] * dt
        d["vy"] = min(d["vy"] + 0.08 * dt, 0)
        d["life"] -= dt
    _dmg_numbers[:] = [d for d in _dmg_numbers if d["life"] > 0]

def draw_dmg_numbers(surf, cx):
    for d in _dmg_numbers:
        a = int(255 * (d["life"] / d["ml"]))
        if a <= 0: continue
        fnt = F_MED if d["crit"] else F_SM
        t = fnt.render(d["text"], True, d["col"])
        t.set_alpha(a)
        sx = int(d["x"] - cx) - t.get_width() // 2
        sy = int(d["y"]) - t.get_height() // 2
        surf.blit(t, (sx, sy))

class EssenceDrop:
    def __init__(self, x, y, amount=1):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-2.5,2.5), random.uniform(-4,-1.5))
        self.life = 500; self.amount = amount; self.collected = False
        self.phase = random.uniform(0, math.pi*2)

    def update(self, pl, dt):
        if self.collected: return
        self.life -= dt; self.phase += 0.08*dt
        if self.pos.y < GROUND_Y-20: self.vel.y += 0.18*dt
        else: self.pos.y=GROUND_Y-20; self.vel.x*=0.82; self.vel.y=0
        self.pos += self.vel*dt
        if pl and pl.alive:
            dx = pl.rect.centerx-self.pos.x; dy = pl.rect.centery-self.pos.y
            d = max(1, math.hypot(dx,dy))
            if d < 130: self.vel += pygame.Vector2(dx/d,dy/d)*1.6*dt
            if d < 22:
                self.collected = True
                amt = int(self.amount * run_essence_mult())
                meta["divine_essence"] += amt
                spawn_particles(self.pos.x,self.pos.y,5,[C_CYAN,C_WHITE],speed=3,sz=(2,4),life=(8,18))

    def draw(self, surf, cx):
        if self.collected or self.life <= 0: return
        sx,sy = int(self.pos.x-cx), int(self.pos.y)+int(math.sin(self.phase)*4)
        gs=pygame.Surface((14,14),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*C_CYAN,90),(7,7),7)
        surf.blit(gs,(sx-7,sy-7))
        pygame.draw.circle(surf,C_WHITE,(sx,sy),3)
        pygame.draw.circle(surf,C_CYAN,(sx,sy),3,1)

essence_drops = []

class EssenceMote:
    def __init__(self): self.reset()
    def reset(self):
        self.x=random.uniform(0,FLOOR_W); self.y=random.uniform(60, GROUND_Y-20)
        self.vx=random.uniform(-0.18,0.18); self.vy=random.uniform(-0.25,-0.06)
        self.life=self.ml=random.randint(180,580); self.r=random.randint(1,4)
        self.col=random.choice([C_PURPLE,C_CYAN,C_RUNEGLOW,(80,0,120)])
    def update(self, dt):
        self.x+=self.vx*dt; self.y+=self.vy*dt; self.life-=dt
        if self.life<=0: self.reset()
    def draw(self, surf, cx):
        sx,sy=int(self.x-cx),int(self.y)
        if sx<-20 or sx>WIDTH+20: return
        a=int(160*(self.life/self.ml))
        s=pygame.Surface((self.r*2,self.r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*self.col,a),(self.r,self.r),self.r)
        surf.blit(s,(sx-self.r,sy-self.r))

motes = [EssenceMote() for _ in range(100)]

class RelicPickup:
    def __init__(self, x, y, relic_id):
        self.x=float(x); self.y=float(y); self.rid = relic_id; self.data = RELIC_DEFS[relic_id]
        self.phase = random.uniform(0, math.pi*2)
        self.rect = pygame.Rect(int(x)-18, int(y)-18, 36, 36); self.alive = True
    def update(self, pl, dt):
        self.phase += 0.06*dt
        if pl and pl.alive and self.rect.colliderect(pl.rect) and pl.can_pickup_relic():
            run["relics"].append(self.rid); pl.apply_relic(self.rid)
            announce(f"RELIC: {self.data['name']}  — {self.data['desc']}", self.data["color"], 180)
            spawn_particles(self.x,self.y,25,[self.data["color"],C_WHITE],speed=5,sz=(2,6),life=(10,28))
            audio.play("relic", 0.7); self.alive = False
    def draw(self, surf, cx):
        if not self.alive: return
        sx,sy = int(self.x-cx), int(self.y)+int(math.sin(self.phase)*6)
        c = self.data["color"]
        gs=pygame.Surface((40,40),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*c,70),(20,20),20)
        surf.blit(gs,(sx-20,sy-20))
        pygame.draw.circle(surf,c,(sx,sy),10,2)
        icon = F_MED.render(self.data["icon"], True, c)
        surf.blit(icon,(sx-icon.get_width()//2, sy-icon.get_height()//2))
        mx,my = get_mouse_pos(cx)
        if math.hypot(mx-self.x, my-self.y) < 40:
            lbl = F_SM.render(self.data["name"], True, c)
            surf.blit(lbl,(sx-lbl.get_width()//2, sy-32))

relic_pickups = []

class Torch:
    def __init__(self, x, y):
        self.x=x; self.y=y; self.phase=random.uniform(0,math.pi*2); self.flames=[]
    def update(self, dt):
        self.phase += 0.1*dt
        torch_top = self.y - (_TORCH_IMG.get_height() if _TORCH_IMG else 24) + 4
        if random.random()<0.35:
            self.flames.append([float(self.x),float(torch_top),random.uniform(-0.6,0.6),random.uniform(-1.4,-0.4),random.randint(8,18)])
        for f in self.flames: f[0]+=f[2]*dt; f[1]+=f[3]*dt; f[4]-=dt
        self.flames=[f for f in self.flames if f[4]>0]
    def draw(self, surf, cx):
        sx,sy = int(self.x-cx),int(self.y)
        if _TORCH_IMG: surf.blit(_TORCH_IMG, (sx - _TORCH_IMG.get_width()//2, sy - _TORCH_IMG.get_height()))
        else:
            pygame.draw.rect(surf,C_STONE2,(sx-3,sy-24,6,24),border_radius=2)
            pygame.draw.rect(surf,C_STONE,(sx-3,sy-24,6,24),1,border_radius=2)
        for f in self.flames:
            fx,fy,t = int(f[0]-cx),int(f[1]),f[4]/18.0
            c = C_RUNEGLOW if t>0.5 else C_PURPLE
            r = max(1,int(4*t))
            fs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(fs,(*c,int(200*t)),(r,r),r)
            surf.blit(fs,(fx-r,fy-r))
            
    def draw_light(self, light, cx):
        sx,sy = int(self.x-cx),int(self.y)
        torch_top = sy - ((_TORCH_IMG.get_height() if _TORCH_IMG else 24))
        flk = math.sin(self.phase)*4
        r = int(250+flk*8) 
        glow(light,C_PURPLE,sx,torch_top,r,int(60+flk*4))
        glow(light,C_RUNEGLOW,sx,torch_top,int(r*0.5),90)

class HealShrine:
    """Heart-shaped shrine in the sanctum: spend 8 essence per HP, hold E to drink."""
    COST_PER_HP = 8
    def __init__(self, x, y):
        self.x = x; self.y = y
        self.rect = pygame.Rect(int(x)-30, int(y)-50, 60, 80)
        self.phase = 0.0
        self.charge = 0           # builds up while E held → consumes when full
        self.alive = True

    def update(self, pl, dt):
        self.phase += 0.06*dt
        if not pl or not pl.alive: self.charge = 0; return
        if not self.rect.colliderect(pl.rect): self.charge = 0; return
        # Player overlap + E held → tick the charge meter
        keys = pygame.key.get_pressed()
        can_heal = (pl.hp < pl.max_hp) and (meta["divine_essence"] >= self.COST_PER_HP)
        if keys[pygame.K_e] and can_heal:
            self.charge += 1.5*dt
            spawn_particles(pl.rect.centerx, pl.rect.centery, 1,
                            [C_RED, C_HOLY, C_WHITE], speed=2, gravity=-0.05, sz=(1,3), life=(6,14))
            if self.charge >= 30:
                self.charge = 0
                meta["divine_essence"] -= self.COST_PER_HP
                pl.hp = min(pl.max_hp, pl.hp + 1)
                spawn_particles(pl.rect.centerx, pl.rect.centery, 18,
                                [C_RED, C_HOLY, C_WHITE], speed=4, gravity=-0.1)
                audio.play("relic", 0.55)
        else:
            self.charge = max(0, self.charge - 0.5*dt)

    def draw(self, surf, cx):
        sx, sy = int(self.x - cx), int(self.y)
        # If we have a custom shrine image, use it
        if _HEAL_SHRINE_IMG:
            bob = int(math.sin(self.phase)*4)
            pulse = 0.6 + 0.4*math.sin(self.phase*1.5)
            glow_s = pygame.Surface((90,90), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (*C_RED, int(60*pulse)), (45,45), 45)
            surf.blit(glow_s, (sx-45, sy-45), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(_HEAL_SHRINE_IMG, (sx - _HEAL_SHRINE_IMG.get_width()//2, sy - _HEAL_SHRINE_IMG.get_height()))
        else:
            # Pedestal
            pygame.draw.rect(surf, (35,28,52), (sx-32, sy-12, 64, 24), border_radius=4)
            pygame.draw.rect(surf, C_RUNEGLOW, (sx-32, sy-12, 64, 24), 2, border_radius=4)
            # Floating heart-bowl
            bob = int(math.sin(self.phase)*4)
            pulse = 0.6 + 0.4*math.sin(self.phase*1.5)
            cx2, cy2 = sx, sy - 28 + bob
            glow_s = pygame.Surface((90,90), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (*C_RED, int(60*pulse)), (45,45), 45)
            surf.blit(glow_s, (cx2-45, cy2-45), special_flags=pygame.BLEND_RGBA_ADD)
            # Bowl
            pygame.draw.ellipse(surf, (50,15,25), (cx2-18, cy2-10, 36, 22))
            pygame.draw.ellipse(surf, C_RED, (cx2-18, cy2-10, 36, 22), 2)
            # Liquid inside (heart)
            pygame.draw.circle(surf, C_BLOOD, (cx2-6, cy2-2), 5)
            pygame.draw.circle(surf, C_BLOOD, (cx2+6, cy2-2), 5)
            pygame.draw.polygon(surf, C_BLOOD, [(cx2-10, cy2), (cx2+10, cy2), (cx2, cy2+10)])
        # Label / charge bar — only visible when player is nearby
        if player and self.rect.colliderect(player.rect):
            lbl = F_SM.render(f"DRINK [HOLD E] — {self.COST_PER_HP} ESSENCE / HP", True, C_RED)
            surf.blit(lbl, (sx - lbl.get_width()//2, sy - 80))
            if self.charge > 0:
                bw = 80
                pygame.draw.rect(surf, (30,15,15), (sx-bw//2, sy-58, bw, 6))
                pygame.draw.rect(surf, C_RED, (sx-bw//2, sy-58, int(bw*self.charge/30), 6))

    def draw_light(self, light, cx):
        glow(light, C_RED, int(self.x - cx), int(self.y) - 28, 130, 50)


class Door:
    def __init__(self, x, y, color, label, target_state):
        self.rect       = pygame.Rect(x, y, 90, 150)
        self.color      = color; self.label=label; self.target=target_state
        self.locked     = True; self.gp=0.0; self.open_t=0.0; self.opening=False; self.is_open=False
    def unlock(self): self.locked = False
    def try_open(self):
        if not self.locked and not self.opening: self.opening = True; audio.play("dash", 0.4)
    def update(self, dt):
        self.gp += 0.06*dt
        if self.opening and not self.is_open:
            self.open_t += 0.018*dt
            if random.random()<0.25: spawn_particles(self.rect.centerx,self.rect.bottom-random.randint(0,80), 2,[self.color,C_WHITE],speed=2)
            if self.open_t >= 1.0: self.is_open=True; self.open_t=1.0
    def draw(self, surf, cx):
        sx,sy = self.rect.x-int(cx), self.rect.y
        c = C_GREY if self.locked else self.color
        
        if _DOOR_OPEN and self.open_t > 0.5:
            img = _DOOR_OPEN.copy()
            if self.locked: img.fill((80,80,80,255), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(img, (sx, sy))
        elif _DOOR_IDLE:
            img = _DOOR_IDLE.copy()
            if self.locked: img.fill((80,80,80,255), special_flags=pygame.BLEND_RGBA_MULT)
            tint = pygame.Surface((90,150), pygame.SRCALPHA); tint.fill((*c, 60))
            img.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_ADD); surf.blit(img, (sx, sy))
        else:
            slide = int(45*self.open_t)
            if self.open_t > 0:
                portal=pygame.Surface((90,150),pygame.SRCALPHA)
                pygame.draw.rect(portal,(*c,int(140*self.open_t)),(0,0,90,150),border_radius=5)
                surf.blit(portal,(sx,sy))
            for side, ox in [(0,-slide),(1,45+slide)]:
                dp=pygame.Surface((45,150),pygame.SRCALPHA)
                pygame.draw.rect(dp,(18,14,26),(0,0,45,150),border_radius=5)
                pygame.draw.rect(dp,c,(0,0,45,150),2,border_radius=5)
                surf.blit(dp,(sx+ox,sy))

        y_bob = int(math.sin(self.gp*2)*4) if not self.locked else 0
        lbl = F_SM.render(self.label, True, c)
        surf.blit(lbl, (sx + 45 - lbl.get_width()//2, sy - 26 + y_bob))

        if not self.locked and not self.opening:
            a = int(110+55*math.sin(self.gp))
            gs=pygame.Surface((130,190),pygame.SRCALPHA)
            pygame.draw.ellipse(gs,(*self.color,a//3),(0,0,130,190))
            surf.blit(gs,(sx-20,sy-20))

    def draw_light(self, light, cx):
        if not self.locked: glow(light,self.color,int(self.rect.centerx-cx),self.rect.centery,110,45+int(40*self.open_t))

class Proj:
    def __init__(self, x, y, vx, vy, color=C_RED, radius=7, homing=False, target=None, speed=5, shooter=None, ptype="generic", damage=1, piercing=False, poison=False):
        self.pos   = pygame.Vector2(x,y); self.vel=pygame.Vector2(vx,vy)
        self.color = color; self.radius=radius; self.alive=True; self.trail=[]
        self.homing=homing; self.target=target; self.speed=speed
        self.shooter=shooter; self.ptype=ptype; self.damage=damage
        self.piercing=piercing; self.poison=poison; self.parried=False; self.age=0

    def deflect(self):
        self.vel = -self.vel; self.homing=False; self.color=C_CYAN; self.parried=True

    def update(self, pl, dt):
        self.age += dt
        if self.homing and self.target and getattr(self.target,'alive',False):
            dx=self.target.rect.centerx-self.pos.x; dy=self.target.rect.centery-self.pos.y
            d=max(1,math.hypot(dx,dy))
            self.vel += (pygame.Vector2(dx/d*self.speed,dy/d*self.speed)-self.vel)*0.05*dt
        self.trail.append((self.pos.x,self.pos.y))
        if len(self.trail)>10: self.trail.pop(0)
        self.pos += self.vel*dt

        if self.pos.x<-500 or self.pos.x>FLOOR_W+500 or self.pos.y>1200 or self.pos.y<-200:
            self.alive=False; return

        if self.ptype in ("player_bolt","player_wave","player_ult"):
            targets = [e for e in enemies if e.alive]
            if boss_obj and boss_obj.alive: targets.append(boss_obj)
            
            for e in targets:
                if e.rect.collidepoint(self.pos):
                    # Projectiles do not bypass shields unless explicitly flagged, which player projs currently aren't
                    e.take_damage(self.damage, self.pos.x)
                    if self.poison and hasattr(e,'poison_timer'): e.poison_timer=180
                    spawn_particles(self.pos.x,self.pos.y,12,[C_PURPLE,C_WHITE,C_CYAN],speed=4)
                    if not self.piercing: self.alive=False
                    break
            return

        if self.parried and self.shooter and getattr(self.shooter,'alive',True):
            if self.shooter.rect.collidepoint(self.pos):
                self.alive=False; self.shooter.take_damage(2, self.pos.x, unblockable=True)
                spawn_particles(self.pos.x,self.pos.y,14,[C_CYAN,C_WHITE],speed=4)
                return

        if not self.parried and pl and pl.alive:
            if math.hypot(pl.rect.centerx-self.pos.x,pl.rect.centery-self.pos.y) < self.radius+14:
                self.alive=False; pl.take_damage()
                spawn_particles(self.pos.x,self.pos.y,8,[C_RED,C_ORANGE],speed=3)

    def draw(self, surf, cx):
        sx,sy = int(self.pos.x-cx),int(self.pos.y)
        ang = math.atan2(self.vel.y, self.vel.x)

        if self.ptype == "flaming_gold" and _PROJ_FIREBALL:
            img = _PROJ_FIREBALL
            if self.parried:
                img = img.copy(); img.fill((0,200,255,255), special_flags=pygame.BLEND_RGBA_MULT)
            rot = pygame.transform.rotate(img, -math.degrees(ang))
            surf.blit(rot, (sx-rot.get_width()//2, sy-rot.get_height()//2)); return

        if self.ptype in ("player_wave", "player_bolt") and _PROJ_DARKWAVE:
            rot = pygame.transform.rotate(_PROJ_DARKWAVE, -math.degrees(ang))
            rot.set_alpha(220)
            surf.blit(rot, (sx-rot.get_width()//2, sy-rot.get_height()//2)); return

        for i,(tx,ty) in enumerate(self.trail):
            a = int(140*i/max(1,len(self.trail))); r = max(1,self.radius-int((len(self.trail)-i)*0.6))
            ts=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(ts,(*self.color,a),(r,r),r); surf.blit(ts,(int(tx-cx)-r,int(ty)-r))

        for r,a in [(self.radius*3,25),(self.radius*2,55),(self.radius,255)]:
            s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(s,(*self.color,a),(r,r),r); surf.blit(s,(sx-r,sy-r))

def apply_poison_tick(e, dt):
    if not hasattr(e,'poison_timer'): return
    if e.poison_timer > 0:
        e.poison_timer -= dt
        if int(e.poison_timer) % 40 < 1:
            e.hp -= 1
            spawn_particles(e.rect.centerx,e.rect.y+10,4,[C_PLAGUE,(80,220,60)],speed=2,gravity=-0.1,sz=(2,4))
            if e.hp <= 0: e.alive = False

class HolyPillar:
    def __init__(self, x, warn=60):
        self.x=float(x); self.w=55; self.state="warn"; self.timer=float(warn); self.alive=True; self.alpha=0
        self.rect=pygame.Rect(int(x)-self.w//2,0,self.w,GROUND_Y)
    def update(self, pl, dt):
        if self.state=="warn":
            self.timer-=dt; self.alpha=min(145,int(145*(1-self.timer/60.0)))
            if self.timer<=0:
                self.state="active"; self.timer=14.0; self.alpha=255
                spawn_particles(self.x,GROUND_Y,18,[C_GOLD,C_HOLY,C_WHITE],speed=6,direction=-math.pi/2,spread=math.pi,gravity=0.15)
        elif self.state=="active":
            self.timer-=dt
            if self.timer<=0: self.state="fade"; self.timer=28.0
            if pl and pl.alive and self.rect.colliderect(pl.rect): pl.take_damage()
        elif self.state=="fade":
            self.timer-=dt; self.alpha=max(0,int(255*(self.timer/28.0)))
            if self.timer<=0: self.alive=False
    def draw(self, surf, cx):
        sx=int(self.x-cx)
        if self.state=="warn":
            pygame.draw.ellipse(surf,(*C_RED,150),(sx-self.w//2,GROUND_Y-12,self.w,18),2)
            ws=pygame.Surface((self.w,GROUND_Y),pygame.SRCALPHA); ws.fill((*C_RED,int(self.alpha*0.25)))
            surf.blit(ws,(sx-self.w//2,0))
        else:
            ps=pygame.Surface((self.w,GROUND_Y),pygame.SRCALPHA)
            pygame.draw.rect(ps,(*C_GOLD,int(self.alpha*0.55)),(0,0,self.w,GROUND_Y))
            pygame.draw.rect(ps,(*C_WHITE,self.alpha),(self.w//4,0,self.w//2,GROUND_Y))
            surf.blit(ps,(sx-self.w//2,0))
            pygame.draw.ellipse(surf,(*C_WHITE,self.alpha),(sx-self.w//2-8,GROUND_Y-17,self.w+16,26))

# ─────────────────────────────────────────────────────────────────────────────
#  ENEMIES
# ─────────────────────────────────────────────────────────────────────────────
class EnemyBase:
    def __init__(self):
        self.alive=True; self.hit_timer=0; self.poison_timer=0; self.projs=[]; self.projectiles=self.projs

    def _tick_hit(self, dt): 
        if self.hit_timer>0: self.hit_timer-=dt

    def _land_on_floor(self, dt):
        self.vel_y = min(getattr(self,'vel_y',0)+0.75*dt, 18)
        self.pos.y += self.vel_y*dt; self.rect.y=int(self.pos.y)
        if self.rect.bottom>=GROUND_Y: self.rect.bottom=GROUND_Y; self.vel_y=0; self.pos.y=float(self.rect.y)

    def _move_towards(self, tx, speed, dt):
        dx=tx-self.rect.centerx; self.direction = 1 if dx>=0 else -1
        if abs(dx)>4: self.pos.x += speed*self.direction*dt
        self.rect.x=int(self.pos.x)

    def _drop_essence(self, n=1, elite=False):
        global kill_streak, kill_streak_best
        amount = 3 if elite else 1
        for _ in range(n): essence_drops.append(EssenceDrop(self.rect.centerx,self.rect.centery,amount))
        meta["total_kills"]+=1; run["kills"]+=1
        kill_streak += 1
        if kill_streak > kill_streak_best: kill_streak_best = kill_streak
        if kill_streak == 5:  announce("KILL STREAK  ×5 — RELENTLESS!", C_ORANGE, 100)
        elif kill_streak == 10: announce("KILL STREAK  ×10 — UNSTOPPABLE!", C_RED, 120)
        elif kill_streak > 10 and kill_streak % 5 == 0:
            announce(f"KILL STREAK  ×{kill_streak} — VOID INCARNATE!", C_RUNEGLOW, 120)

    def _maybe_drop_relic(self):
        if random.random()<0.5:
            pool=[k for k in RELIC_DEFS if k not in run["relics"]+run["relic_offered"]]
            if pool and len(run["relics"])<meta["upg_relic_slots"]:
                rid=random.choice(pool); run["relic_offered"].append(rid)
                relic_pickups.append(RelicPickup(self.rect.centerx,self.rect.centery-30,rid))

class Grunt(EnemyBase):
    def __init__(self, x, y, pl, pr):
        super().__init__()
        self.pos=pygame.Vector2(x,y); self.vel_y=0
        self.HP = max(2, int(4 * get_diff()))
        self.hp = self.HP; self.direction=1
        self.rect=pygame.Rect(x,y,44,62)
        self.pl=pl; self.pr=pr; self.state="patrol"
        self.MELEE_CD=55; self.MELEE_DUR=14
        self.melee_t=random.randint(20,50); self.melee_a=0
        self.anim_t=0.0; self.poison_timer=0
        if _GRUNT_FRAMES_R and _GRUNT_FRAMES_R[0] is not None:
            self._imgs_r = _GRUNT_FRAMES_R; self._imgs_l = _GRUNT_FRAMES_L
            self.rect = pygame.Rect(x, y, _GRUNT_FRAMES_R[0].get_width(), _GRUNT_FRAMES_R[0].get_height())
        else:
            self._imgs_r = self._mk_frames((155,90,220))
            self._imgs_l = [pygame.transform.flip(f,True,False) for f in self._imgs_r]

    def _mk_frames(self, tint):
        frames=[]
        for i in range(4):
            s=pygame.Surface((44,62),pygame.SRCALPHA)
            pygame.draw.ellipse(s,(*tint,200),(8,12,28,42))
            pygame.draw.circle(s,(tint[0]//2+60,tint[1]//2+40,tint[2]//2+40,220),(22,10),9)
            pygame.draw.circle(s,(*C_RED,240),(18+(i%2),8),2)
            pygame.draw.circle(s,(*C_RED,240),(26+(i%2),8),2)
            cy = int(math.sin(i*math.pi/2)*3)
            pygame.draw.rect(s,(*tint,120),(6,30+cy,32,24),border_radius=4)
            frames.append(s)
        return frames

    def take_damage(self, amount, sx, unblockable=False):
        self.hp -= amount; self.hit_timer=14
        spawn_dmg_number(self.rect.centerx, self.rect.y, amount)
        if run_has("soulsucker") and player: player.hp = min(player.max_hp, player.hp+1)
        if self.hp<=0: self.alive=False; self._drop_essence(random.randint(1,2))

    def update(self, pl, plats, dt):
        if not self.alive: return
        self._tick_hit(dt); apply_poison_tick(self, dt)
        dist=math.hypot(pl.rect.centerx-self.rect.centerx, pl.rect.centery-self.rect.centery)
        if dist<65:   self.state="attack"
        elif dist<380:self.state="chase"
        else:         self.state="patrol"

        if self.state=="patrol":
            self.pos.x += 1.8*self.direction*dt
            if self.pos.x<self.pl: self.direction=1
            if self.pos.x>self.pr: self.direction=-1
        elif self.state=="chase":
            self._move_towards(pl.rect.centerx, 2.8, dt)
        elif self.state=="attack":
            self._move_towards(pl.rect.centerx, 2.0, dt)
            self.melee_t-=dt
            if self.melee_t<=0:
                self.melee_t=float(self.MELEE_CD); self.melee_a=self.MELEE_DUR
                spawn_particles(self.rect.centerx+self.direction*28,self.rect.centery,5,[C_PURPLE,C_WHITE],speed=3)

        if self.melee_a>0:
            self.melee_a-=dt
            mr=pygame.Rect(0,0,50,64)
            if self.direction>0: mr.midleft=self.rect.midright
            else: mr.midright=self.rect.midleft
            if mr.colliderect(pl.rect):
                pl.take_damage()
                if run_has("thorn_mantle") and pl.parry_t>0:
                    self.hp-=2
                    if self.hp<=0: self.alive=False
        self._land_on_floor(dt); self.anim_t=(self.anim_t+0.12*dt) % len(self._imgs_r)

    def draw(self, surf, cx):
        if not self.alive: return
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return
        imgs = self._imgs_r if self.direction>0 else self._imgs_l
        fi = int(self.anim_t) % len(imgs)
        img = imgs[fi]
        if img is None: return
        if self.poison_timer>0:
            img=img.copy(); img.fill((*C_PLAGUE,180),special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(img,(self.rect.x-cx,self.rect.y))
        if self.melee_a>0:
            arc_s=pygame.Surface((70,55),pygame.SRCALPHA)
            pygame.draw.arc(arc_s,(*C_PURPLE,int(170*self.melee_a/self.MELEE_DUR)),(0,0,70,55),-math.pi/3,math.pi/3,4)
            sx=self.rect.x-int(cx)
            if self.direction>0: surf.blit(arc_s,(sx+self.rect.w-5,self.rect.centery-27))
            else: surf.blit(pygame.transform.flip(arc_s,True,False),(sx-65,self.rect.centery-27))
        if self.hp<self.HP:
            for i in range(min(self.HP, 10)):
                c=C_RED if i<self.hp else C_GREY
                pygame.draw.rect(surf,c,(self.rect.x-int(cx)+i*9,self.rect.y-8,7,4))

class Bulwark(Grunt):
    def __init__(self, x, y, pl, pr):
        super().__init__(x, y, pl, pr)
        self.HP = 4          # always exactly 4 HP — shield compensates for low health
        self.hp = self.HP
        self.MELEE_CD = 80
        
    def take_damage(self, amount, sx, unblockable=False):
        if not unblockable and ((self.direction>0 and sx>self.rect.centerx) or (self.direction<0 and sx<self.rect.centerx)):
            spawn_particles(self.rect.centerx+self.direction*22,self.rect.centery,8,[C_GOLD,C_WHITE,C_GREY],speed=5)
            audio.play("parry",0.5)
            if player: player.pos.x -= self.direction*10; player.rect.x=int(player.pos.x)
        else:
            super().take_damage(amount, sx, unblockable=unblockable)

    def update(self, pl, plats, dt):
        old_dir = self.direction
        super().update(pl, plats, dt)
        if self.melee_a > 0:
            self.direction = old_dir

    def draw(self, surf, cx):
        super().draw(surf,cx)
        if self.alive:
            sx=self.rect.x-cx
            if self.direction>0: sr=(sx+self.rect.w-4,self.rect.y+8,10,44)
            else:                sr=(sx-6,self.rect.y+8,10,44)
            pygame.draw.rect(surf,(90,90,100),sr,border_radius=3)
            pygame.draw.rect(surf,C_GOLD,sr,2,border_radius=3)
            pygame.draw.circle(surf,C_GOLD,(int(sr[0]+5),int(sr[1]+22)),4,1)

class Wraith(EnemyBase):
    def __init__(self, x, y):
        super().__init__()
        self.pos=pygame.Vector2(x,y); 
        self.HP = max(2, int(4 * get_diff()))
        self.hp=self.HP; self.direction=1
        self.rect=pygame.Rect(x,y,40,54); self.phase=random.uniform(0,math.pi*2)
        self.base_y=float(y); self.tele_cd=120; self.shoot_cd=90; self.poison_timer=0
        self.state="hover"

    def take_damage(self, amount, sx, unblockable=False):
        self.hp-=amount; self.hit_timer=14
        spawn_dmg_number(self.rect.centerx, self.rect.y, amount, C_PURPLE)
        if run_has("soulsucker") and player: player.hp=min(player.max_hp,player.hp+1)
        if self.hp<=0: self.alive=False; self._drop_essence(2)

    def update(self, pl, plats, dt):
        if not self.alive: return
        self._tick_hit(dt); apply_poison_tick(self, dt)
        self.phase+=0.06*dt; self.tele_cd-=dt; self.shoot_cd-=dt
        self.direction=1 if pl.rect.centerx>self.rect.centerx else -1
        self.pos.y=self.base_y+math.sin(self.phase)*20
        dx=pl.rect.centerx-self.rect.centerx
        # FIX: proper chase/keep-distance behaviour. Was barely moving when far away.
        if abs(dx) > 380:        # too far → close in fast
            self.pos.x += 2.4 * self.direction * dt
        elif abs(dx) > 220:      # mid-range → slow approach
            self.pos.x += 1.4 * self.direction * dt
        elif abs(dx) < 140:      # too close → drift back to keep range
            self.pos.x -= 1.6 * self.direction * dt
        # else: hover and shoot
        self.rect.topleft=(int(self.pos.x),int(self.pos.y))

        if self.tele_cd<=0:
            self.tele_cd=180
            self.pos.x=pl.rect.centerx+random.choice([-1,1])*random.randint(120,250)
            void_tears.append(VoidTear(self.pos.x,self.pos.y,(80,0,120)))
            spawn_particles(int(self.pos.x),int(self.pos.y),16,[(80,0,140),C_PURPLE],speed=4)

        if self.shoot_cd<=0:
            self.shoot_cd=100
            dx2=pl.rect.centerx-self.rect.centerx; dy2=pl.rect.centery-self.rect.centery
            d=max(1,math.hypot(dx2,dy2))
            self.projs.append(Proj(self.rect.centerx,self.rect.centery, dx2/d*4.5,dy2/d*4.5,(120,0,160),7,shooter=self))

        for p in self.projs: p.update(pl,dt)
        self.projs=[p for p in self.projs if p.alive]

    def draw(self, surf, cx):
        if not self.alive: return
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return
        sx,sy=self.rect.x-int(cx),self.rect.y
        a=int(170+70*math.sin(self.phase))
        gs=pygame.Surface((40,54),pygame.SRCALPHA)
        pygame.draw.ellipse(gs,(*C_VOID,a),(4,8,32,38))
        pygame.draw.circle(gs,(*C_PURPLE,a),(20,12),10)
        pygame.draw.circle(gs,(*C_RED,240),(14,10),2)
        pygame.draw.circle(gs,(*C_RED,240),(26,10),2)
        surf.blit(gs,(sx,sy))
        for p in self.projs: p.draw(surf,cx)

class Seraph(EnemyBase):
    def __init__(self, x, y, elite=False):
        super().__init__()
        self.pos=pygame.Vector2(x,y); self.base_y=float(y)
        self.MAX_HP = max(3, int(6 * get_diff()))
        self.POSTURE_MAX = 10
        self.hp=self.MAX_HP+(2 if elite else 0)
        self.posture=self.POSTURE_MAX
        self.direction=1; self.elite=elite; self.poison_timer=0
        self.rect=pygame.Rect(x,y,52,72)
        self.state="hover"; self.stun_t=0
        self.hover_t=random.uniform(0,math.pi*2)
        self.wing_t=random.uniform(0,math.pi*2)
        
        self.BEAM_CD=480; self.DIVE_CD=600; self.PILLAR_CD=700
        atk_scale = max(0.4, get_diff())
        self.beam_cd=random.randint(int(280/atk_scale), int(self.BEAM_CD/atk_scale))
        self.dive_cd=random.randint(int(350/atk_scale), int(self.DIVE_CD/atk_scale))
        self.pillar_cd=random.randint(int(400/atk_scale), int(self.PILLAR_CD/atk_scale))
        self._atk_scale=atk_scale
        self.pillars=[]
        self.dive_origin=pygame.Vector2(x,y); self.dive_target=pygame.Vector2(x,y)
        self.dive_t=0; self.facing_r=True; self.anim_t=0.0
        self._make_sprite()

    def _make_sprite(self):
        w,h=52,72; s=pygame.Surface((w,h),pygame.SRCALPHA)
        pygame.draw.ellipse(s,(*C_HOLY,210),(8,22,36,44))
        pygame.draw.ellipse(s,(*C_GOLD,180),(10,0,32,14),3)
        pygame.draw.circle(s,(*C_HOLY,230),(26,14),11)
        pygame.draw.circle(s,(*C_GOLD,120),(26,14),13,2)
        self._body=s

    def take_damage(self, amount, sx, unblockable=False):
        self.hp-=amount; self.posture-=amount*2; self.hit_timer=14
        spawn_dmg_number(self.rect.centerx, self.rect.y, amount, C_GOLD)
        if run_has("soulsucker") and player: player.hp=min(player.max_hp,player.hp+1)
        if self.hp<=0:
            self.alive=False; self._drop_essence(random.randint(2,4), elite=self.elite)
            if self.elite: self._maybe_drop_relic()

    def _fire(self, pl):
        dx=pl.rect.centerx-self.rect.centerx; dy=pl.rect.centery-self.rect.centery
        d=max(1,math.hypot(dx,dy))
        self.projs.append(Proj(self.rect.centerx,self.rect.centery, dx/d*3.5,dy/d*3.5,C_GOLD,9,homing=False,target=pl, speed=3.0,shooter=self,ptype="spearhead",damage=1))
        if self.elite:
            ang=0.3
            self.projs.append(Proj(self.rect.centerx,self.rect.centery, math.cos(math.atan2(dy,dx)+ang)*3.5, math.sin(math.atan2(dy,dx)+ang)*3.5, C_HOLY,7,shooter=self,damage=1))

    def update(self, pl, dt):
        if not self.alive: return
        self._tick_hit(dt); apply_poison_tick(self, dt)
        for pil in self.pillars: pil.update(pl,dt)
        self.pillars=[p for p in self.pillars if p.alive]
        for p in self.projs: p.update(pl,dt)
        self.projs=[p for p in self.projs if p.alive]

        self.hover_t+=0.04*dt; self.wing_t+=0.09*dt; self.anim_t+=0.15*dt

        if self.posture<=0 and self.state!="stunned":
            self.state="stunned"; self.stun_t=220
        if self.state=="stunned":
            self.stun_t-=dt
            if self.stun_t<=0: self.posture=self.POSTURE_MAX; self.state="hover"
            return

        if self.state=="hover":
            self.direction=1 if pl.rect.centerx>self.rect.centerx else -1
            self.facing_r = (self.direction > 0) # FIX: Seraph actually turns to look at you now
            
            sc = getattr(self,'_atk_scale',1.0)
            # FIX: Hover speed boosted significantly 
            self.pos.x += 1.5 * self.direction * dt * sc 
            self.pos.y  = self.base_y+math.sin(self.hover_t)*16
            self.rect.topleft=(int(self.pos.x),int(self.pos.y))
            
            self.beam_cd-=dt; self.dive_cd-=dt; self.pillar_cd-=dt
            
            if self.beam_cd<=0: self._fire(pl); self.beam_cd=int(self.BEAM_CD/sc)
            if self.pillar_cd<=0:
                tx=pl.rect.centerx+int(pl.vel.x*10 if hasattr(pl,'vel') else 0)
                self.pillars.append(HolyPillar(tx))
                if self.elite: self.pillars.append(HolyPillar(tx+random.choice([-180,180])))
                self.pillar_cd=int(self.PILLAR_CD/sc)
            if self.dive_cd<=0:
                self.state="dive"; self.dive_origin=pygame.Vector2(self.pos)
                self.dive_target=pygame.Vector2(pl.rect.centerx, GROUND_Y - 80)
                self.dive_t=0; self.dive_cd=int(self.DIVE_CD/sc)
        elif self.state=="dive":
            self.dive_t+=dt; t=min(1.0,self.dive_t/20.0); ease=t*t*(3-2*t)
            self.pos.x=self.dive_origin.x+(self.dive_target.x-self.dive_origin.x)*ease
            self.pos.y=self.dive_origin.y+(self.dive_target.y-self.dive_origin.y)*ease
            self.rect.topleft=(int(self.pos.x),int(self.pos.y))
            if self.dive_t%2==0: spawn_particles(self.rect.centerx,self.rect.centery,3,[C_GOLD,C_WHITE],speed=2,gravity=0.1)
            if t>=1.0:
                spawn_particles(self.rect.centerx,self.rect.bottom,16,[C_GOLD,C_WHITE,C_HOLY],speed=5, spread=math.pi,direction=-math.pi/2,gravity=0.18)
                if abs(pl.rect.centerx-self.rect.centerx)<70: pl.take_damage()
                self.state="return"; self.dive_t=0; self.base_y=self.dive_origin.y
        elif self.state=="return":
            self.dive_t+=dt; t=min(1.0,self.dive_t/32.0); ease=t*t*(3-2*t)
            self.pos.x=self.dive_target.x+(self.dive_origin.x-self.dive_target.x)*ease
            self.pos.y=self.dive_target.y+(self.dive_origin.y-self.dive_target.y)*ease
            self.rect.topleft=(int(self.pos.x),int(self.pos.y))
            if t>=1.0: self.state="hover"

    def draw(self, surf, cx):
        if not self.alive: return
        for pil in self.pillars: pil.draw(surf,cx)
        for p in self.projs: p.draw(surf,cx)
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return
        sx,sy=self.rect.x-int(cx),self.rect.y
        is_stun = self.state=="stunned"

        # ── Procedural wings: ONLY drawn when there is no PNG sprite (the PNG already has wings).
        #     Surface is generously sized so the polygon is NEVER clipped, even at extreme flap.
        body_has_wings = bool(_SERAPH_IMG_R and _SERAPH_IMG_L)
        if not is_stun and not body_has_wings:
            wbeat = math.sin(self.wing_t)
            wing_alpha = int(120 + 70 * abs(wbeat))
            WS_W, WS_H = 220, 160
            ANCHOR_X, ANCHOR_Y = WS_W//2, WS_H//2
            ws = pygame.Surface((WS_W, WS_H), pygame.SRCALPHA)
            for side in (-1, 1):
                # wing extends outward; flap lifts the tip up (negative y)
                tip_x  = ANCHOR_X + side * int(50 + 12*wbeat)
                tip_y  = ANCHOR_Y + int(-26 + wbeat*-10)
                root_t = (ANCHOR_X + side*6, ANCHOR_Y - 2)
                root_b = (ANCHOR_X + side*10, ANCHOR_Y + 18)
                lp = [root_t, (tip_x, tip_y), root_b]
                pygame.draw.polygon(ws, (*C_HOLY, wing_alpha), lp)
                pygame.draw.polygon(ws, (*C_GOLD, 140), lp, 2)
                # feather lines
                for f in range(3):
                    fx = root_t[0] + (tip_x - root_t[0]) * (0.35 + f*0.22)
                    fy = root_t[1] + (tip_y - root_t[1]) * (0.35 + f*0.22)
                    pygame.draw.line(ws, (*C_GOLD, 90),
                                     (ANCHOR_X + side*4, ANCHOR_Y + 8),
                                     (int(fx), int(fy)), 1)
            # Anchor the wing surface so its centre lands on the body centre
            surf.blit(ws, (sx + self.rect.w//2 - ANCHOR_X,
                          sy + self.rect.h//2 - ANCHOR_Y))

        body = None
        if body_has_wings: body = (_SERAPH_IMG_R if self.facing_r else _SERAPH_IMG_L).copy()
        else: body = self._body.copy()
        # Subtle vertical bob synced to hover so the sprite breathes even when not moving
        bob = int(math.sin(self.hover_t*1.3) * 2)
        if is_stun: body.fill((100,100,100,255),special_flags=pygame.BLEND_RGBA_MULT)
        if self.poison_timer>0: body.fill((*C_PLAGUE,150),special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(body,(sx, sy + bob))

        if is_stun: draw_text(surf,"EXECUTE [F]",F_SM,C_RED,sx+26,sy-22,center=True)

        bw,bx,by=55,sx+26-27,sy-11
        pygame.draw.rect(surf,(30,15,45),(bx,by,bw,4))
        pygame.draw.rect(surf,C_RED,(bx,by,max(0,int(bw*self.hp/self.MAX_HP)),4))
        if self.elite:
            crown=F_TINY.render("★",True,C_GOLD)
            surf.blit(crown,(sx+26-crown.get_width()//2,sy-30))

# ── Boss: The Sovereign Aetheria ────────────────────
class Boss(EnemyBase):
    def __init__(self, x, y):
        super().__init__()
        self.pos=pygame.Vector2(x,y); self.vel_y=0
        self.MAX_HP = max(25, int(40 * get_diff()))
        self.POSTURE_MAX = int(80 * get_diff())
        self.P2 = self.MAX_HP * 0.70
        self.P3 = self.MAX_HP * 0.35

        self.hp=self.MAX_HP; self.posture=self.POSTURE_MAX
        self.rect=pygame.Rect(x,y,110,190)
        self.state="active"; self.stun_t=0; self.direction=-1
        self.anim_t=0.0; self.alive=True; self.death_t=100
        self.phase2_done=False; self.phase3_done=False; self.phase_flash=0
        
        speed_mult = 1.0 / max(0.6, get_diff())
        self.shoot_t=90.0 * speed_mult; self.charge_t=220.0 * speed_mult
        self.melee_t=0.0; self.melee_a=0
        self.charging=False; self.spawn_t=500.0 * speed_mult; self.p2_vuln=False
        self.keys_list=[]; self.keys_found=0
        self.pillars=[]; self.adds=[]
        self.CHARGE_SPD= 9 * max(0.6, get_diff()); self.poison_timer=0
        self._mk_frames()

    def _mk_frames(self):
        self._frames={}
        if _BOSS_FRAMES_R:
            for ph in [1,2,3]:
                tints = {1:None, 2:(255,165,80,200), 3:(220,40,40,200)}
                frames = []
                for f in _BOSS_FRAMES_R:
                    img = f.copy()
                    if tints[ph]:
                        tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                        tint.fill(tints[ph])
                        img.blit(tint,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
                    frames.append(img)
                self._frames[ph] = frames
            self._frames_l = {}
            for ph in [1,2,3]:
                self._frames_l[ph] = [pygame.transform.flip(f,True,False) for f in self._frames[ph]]
            w = _BOSS_FRAMES_R[0].get_width(); h = _BOSS_FRAMES_R[0].get_height()
            self.rect = pygame.Rect(int(self.pos.x), int(self.pos.y), w, h); return

        self._frames_l = {}
        for ph,tint in [(1,(220,185,0)),(2,(255,130,0)),(3,(185,20,20))]:
            frames=[]
            for i in range(4):
                s=pygame.Surface((110,190),pygame.SRCALPHA)
                sway=int(math.sin(i*math.pi/2)*4)
                pygame.draw.ellipse(s,(*tint,200),(15,30+sway,80,140))
                pygame.draw.circle(s,(*tint,220),(55,22),20)
                pygame.draw.circle(s,(*C_WHITE,180),(55,18),22,3)
                if ph==2: pygame.draw.ellipse(s,(*C_ORANGE,100),(5,25+sway,100,160))
                if ph==3:
                    pygame.draw.ellipse(s,(*C_RED,80),(0,20+sway,110,170))
                    pygame.draw.circle(s,(*C_RED,200),(55,22),22,3)
                frames.append(s)
            self._frames[ph]=frames
            self._frames_l[ph]=[pygame.transform.flip(f,True,False) for f in frames]

    @property
    def ph(self): return 1 if self.hp>self.P2 else (2 if self.hp>self.P3 else 3)

    def take_damage(self, amount, sx, unblockable=False):
        if self.ph==2 and not self.p2_vuln:
            announce("COLLECT ALL KEYS FIRST!",C_RED,70); return
        self.hp-=amount; self.posture-=amount*1.4; self.hit_timer=12
        spawn_dmg_number(self.rect.centerx, self.rect.y - 20, amount, C_ORANGE, crit=(amount>=6))
        spawn_particles(self.rect.centerx,self.rect.centery,14,[C_GOLD,C_ORANGE,C_WHITE],speed=5)
        if self.hp<=0:
            self.alive=False
            for _ in range(20): essence_drops.append(EssenceDrop(self.rect.centerx,self.rect.centery,3))
            meta["total_kills"]+=1; run["kills"]+=1
            meta["bosses_defeated"] = meta.get("bosses_defeated", 0) + 1
            # NG+ : every boss-clear bumps curse level (caps at 5) so subsequent runs scale up
            if meta["bosses_defeated"] > 0 and meta["curse_level"] < 5:
                meta["curse_level"] = min(5, meta["bosses_defeated"])
            # Dramatic slow-mo on boss kill
            global time_scale, bullet_time_timer, hit_stop_timer, screen_shake
            time_scale = 0.25; bullet_time_timer = 95
            hit_stop_timer = max(hit_stop_timer, 10.0)
            screen_shake = max(screen_shake, 24)

            # FIX: Bosses guarantee a relic drop now
            pool=[k for k in RELIC_DEFS if k not in run["relics"]+run["relic_offered"]]
            if pool:
                rid=random.choice(pool); run["relic_offered"].append(rid)
                relic_pickups.append(RelicPickup(self.rect.centerx,self.rect.centery-30,rid))
            save_meta()                      # auto-save after major milestone

    def _fire(self, pl, count=1, spread=0):
        ba=math.atan2(pl.rect.centery-self.rect.centery,pl.rect.centerx-self.rect.centerx)
        for i in range(count):
            a=ba+math.radians(spread*(i-(count-1)/2))
            self.projs.append(Proj(self.rect.centerx,self.rect.centery,math.cos(a)*6,math.sin(a)*6,C_GOLD,11,shooter=self,ptype="flaming_gold",damage=1))

    def _spawn_keys(self):
        self.keys_list=[]; self.keys_found=0; self.p2_vuln=False
        boss_plats = platforms 
        for px,py,pw in random.sample(boss_plats, min(4,len(boss_plats))):
            self.keys_list.append([float(px+pw//2),float(py-24),False, pygame.Rect(int(px+pw//2)-12,int(py-24)-12,24,24),random.uniform(0,math.pi*2)])

    def update(self, pl, dt):
        if not self.alive:
            if self.death_t>0: self.death_t-=dt
            return
        self._tick_hit(dt); apply_poison_tick(self, dt)
        if self.phase_flash>0: self.phase_flash-=1
        if self.melee_a>0: self.melee_a-=dt

        if self.ph==2 and not self.phase2_done:
            self.phase2_done=True; self.phase_flash=55
            announce("— PHASE II — THE KEYS ARE SCATTERED!",C_ORANGE,200)
            spawn_particles(self.rect.centerx,self.rect.centery,40,[C_GOLD,C_ORANGE,C_WHITE],speed=8)
            self._spawn_keys()
        if self.ph==3 and not self.phase3_done:
            self.phase3_done=True; self.phase_flash=80; self.p2_vuln=True
            announce("PHASE III — AETHERIA UNBOUND!",C_RED,220)
            spawn_particles(self.rect.centerx,self.rect.centery,60,[C_RED,C_ORANGE,C_GOLD,C_PURPLE],speed=9)

        for k in self.keys_list:
            k[4]+=0.07*dt
            k[3].x=int(k[0])-12
            if not k[2] and k[3].colliderect(pl.rect):
                k[2]=True; self.keys_found+=1
                spawn_particles(int(k[0]),int(k[1]),18,[C_GOLD,C_WHITE,C_CYAN],speed=4,gravity=-0.1)
                rem=sum(1 for kk in self.keys_list if not kk[2])
                if rem==0: self.p2_vuln=True; announce("ALL KEYS — STRIKE NOW!",C_CYAN,120)
                else: announce(f"KEY {self.keys_found}/4 — {rem} REMAIN",C_GOLD,80)

        for pil in self.pillars: pil.update(pl,dt)
        self.pillars=[p for p in self.pillars if p.alive]
        for p in self.projs: p.update(pl,dt)
        self.projs=[p for p in self.projs if p.alive]
        for add in self.adds: add.update(pl,platforms,dt)
        self.adds=[a for a in self.adds if a.alive]

        if self.posture<=0 and self.state!="stunned":
            self.state="stunned"; self.stun_t=250

        if self.state=="stunned":
            self.stun_t-=dt
            if self.stun_t<=0: self.posture=self.POSTURE_MAX; self.state="active"
            return

        self._land_on_floor(dt)
        self.direction=1 if pl.rect.centerx>self.rect.centerx else -1
        speed_mult = max(0.5, get_diff())

        if self.ph==1:
            if abs(pl.rect.centerx-self.rect.centerx)>20:
                self.pos.x+=2.2 * speed_mult *self.direction*dt; self.rect.x=int(self.pos.x)
            self.shoot_t-=dt
            if self.shoot_t<=0: self.shoot_t=95.0 / speed_mult; self._fire(pl)
        elif self.ph==2:
            if abs(pl.rect.centerx-self.rect.centerx)>20:
                self.pos.x+=1.6 * speed_mult *self.direction*dt; self.rect.x=int(self.pos.x)
            self.shoot_t-=dt
            if self.shoot_t<=0: self.shoot_t=150.0 / speed_mult; self._fire(pl,3,20)
        elif self.ph==3:
            self.charge_t-=dt; self.melee_t-=dt; self.spawn_t-=dt; self.shoot_t-=dt
            if self.charge_t<=0: self.charge_t=200.0 / speed_mult; self.charging=True
            if self.charging:
                self.pos.x+=self.CHARGE_SPD*self.direction*dt; self.rect.x=int(self.pos.x)
                if abs(pl.rect.centerx-self.rect.centerx)<90:
                    self.charging=False
                    spawn_particles(self.rect.centerx,self.rect.bottom,22,[C_RED,C_ORANGE,C_GOLD],speed=6, spread=math.pi,direction=-math.pi/2,gravity=0.2)
            else:
                if abs(pl.rect.centerx-self.rect.centerx)>20:
                    self.pos.x+=3.5 * speed_mult *self.direction*dt; self.rect.x=int(self.pos.x)
            if self.melee_t<=0:
                self.melee_t=60.0 / speed_mult; self.melee_a=18
                spawn_particles(self.rect.centerx,self.rect.centery,12,[C_RED,C_ORANGE],speed=5)
            if self.melee_a>0:
                mr=pygame.Rect(0,0,130,95)
                if self.direction>0: mr.midleft=self.rect.midright
                else: mr.midright=self.rect.midleft
                if mr.colliderect(pl.rect): 
                    pl.take_damage()
                    if run_has("thorn_mantle") and pl.parry_t>0:
                        self.hp-=2
            if self.shoot_t<=0: self.shoot_t=42.0 / speed_mult; self._fire(pl,2,15)
            if self.spawn_t<=0:
                self.spawn_t=420.0 / speed_mult
                lx,rx=int(self.pos.x)-140,int(self.pos.x)+140
                self.adds.append(Bulwark(lx,350,lx-60,lx+180))
                self.adds.append(Grunt(rx,350,rx-180,rx+60))

        self.anim_t=(self.anim_t+0.09*dt)%4

    def draw(self, surf, cx):
        for p in self.projs: p.draw(surf,cx)
        for add in self.adds: add.draw(surf,cx)
        for pil in self.pillars: pil.draw(surf,cx)
        for k in self.keys_list:
            if k[2]: continue
            kx,ky=int(k[0]-cx),int(k[1])+int(math.sin(k[4])*5)
            gs=pygame.Surface((30,30),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*C_GOLD,70),(15,15),15)
            surf.blit(gs,(kx-15,ky-15))
            pygame.draw.circle(surf,C_GOLD,(kx,ky),7,3)
            pygame.draw.line(surf,C_GOLD,(kx,ky+7),(kx,ky+16),3)

        if not self.alive and self.death_t<=0: return
        sx,sy=self.rect.x-int(cx),self.rect.y

        if self.state=="stunned":
            img=self._frames[self.ph][int(self.anim_t)].copy()
            img.fill((85,85,85,255),special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(img,(sx+random.randint(-2,2),sy+14))
            draw_text(surf,"EXECUTE [F]",F_MED,C_RED,sx+55,sy-32,center=True)
            return

        if self.phase_flash>0:
            fs=pygame.Surface(self.rect.size,pygame.SRCALPHA)
            fs.fill((*C_RED,int(180*self.phase_flash/80)))
            surf.blit(fs,(sx,sy))
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return

        fi = int(self.anim_t) % len(self._frames[self.ph])
        if self.direction>0: img = self._frames_l[self.ph][fi] if hasattr(self,'_frames_l') else pygame.transform.flip(self._frames[self.ph][fi],True,False)
        else: img = self._frames[self.ph][fi]
        surf.blit(img,(sx,sy))

        if self.melee_a>0:
            ma=pygame.Surface((160,110),pygame.SRCALPHA)
            pygame.draw.arc(ma,(*C_RED,int(190*self.melee_a/18)),(0,0,160,110),-math.pi/3,math.pi/3,7)
            if self.direction>0: surf.blit(ma,(self.rect.right-int(cx)-8,self.rect.centery-55))
            else: surf.blit(pygame.transform.flip(ma,True,False),(self.rect.left-int(cx)-152,self.rect.centery-55))



# ─────────────────────────────────────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────────────────────────────────────
class Player:
    DASH_DUR  = 9
    ATK_CD    = 20
    PARRY_WIN = 12
    PARRY_CD  = 60
    BLINK_MAX = 1200
    ULT_DUR   = 28

    def __init__(self, x, y):
        self.pos=pygame.Vector2(x,y); self.vel=pygame.Vector2(0,0)
        self.max_hp    = max(1, meta["upg_max_hp"] + run_hp_bonus())
        self.hp        = self.max_hp
        
        self.max_mana  = 100.0
        self.mana      = self.max_mana
        self.mana_regen = 5.0 
        
        self.target_h  = 72
        self.rect      = pygame.Rect(x,y,42,self.target_h)
        self.alive=True; self.facing_r=True; self.on_ground=False
        self.invincible=0; self.crouching=False
        self.dashing=False; self.dash_t=0; self.dash_cd=0
        self.dash_dir=pygame.Vector2(1,0); self.dash_charges=2 if run_has("swiftness") else 1
        self.atk_t=0; self.atk_cd=0; self.atk_hit=False; self.is_atk=False
        self.ult_t=0; self.ult_cd=0; self.is_ult=False; self.ult_hit=False
        self.parry_t=0; self.parry_cd=0; self.parry_ok=0
        self.blink_cd=0; self.shoot_cd=0; self.dj_used=False
        self.anim_t=0.0; self.afterimages=[]
        self._build_sprite()

    def _build_sprite(self):
        if _PLAYER_FRAMES_R:
            self._frames_r = _PLAYER_FRAMES_R; self._frames_l = _PLAYER_FRAMES_L
            self._base_r   = _PLAYER_FRAMES_R[0]; self._base_l   = _PLAYER_FRAMES_L[0]
            self.target_h  = _PLAYER_FRAMES_R[0].get_height()
            self.rect = pygame.Rect(int(self.pos.x), int(self.pos.y), _PLAYER_FRAMES_R[0].get_width(), self.target_h)
        else:
            w,h=42,72; s=pygame.Surface((w,h),pygame.SRCALPHA)
            pygame.draw.ellipse(s,(30,15,55,220),(4,10,34,54))
            pygame.draw.line(s,(130,130,150,200),(32,0),(22,60),3)
            pygame.draw.arc(s,(180,180,220,220),(18,0,22,16),-math.pi/2,math.pi/2,4)
            pygame.draw.circle(s,(20,12,38,230),(20,8),9); pygame.draw.circle(s,(20,12,38,230),(20,8),11,2)
            pygame.draw.circle(s,(*C_RUNEGLOW,255),(16,6),2); pygame.draw.circle(s,(*C_RUNEGLOW,255),(24,6),2)
            self._frames_r=[s]; self._frames_l=[pygame.transform.flip(s,True,False)]
            self._base_r=s; self._base_l=self._frames_l[0]
        if _SLASH_IMG: self._slash = _SLASH_IMG
        else:
            ss=pygame.Surface((28,60),pygame.SRCALPHA)
            pygame.draw.arc(ss,(*C_WHITE,210),(0,0,28,60),-math.pi/2,math.pi*0.7,5)
            self._slash=ss
        self._slash_ult = _SLASH_ULT if _SLASH_ULT else self._slash

    def can_pickup_relic(self): return len(run["relics"]) < meta["upg_relic_slots"]
    def apply_relic(self, rid):
        if rid=="void_heart": self.max_hp+=2; self.hp=min(self.max_hp,self.hp+2)
        elif rid=="cursed_blade": self.max_hp=max(1,self.max_hp-1); self.hp=min(self.max_hp,self.hp)
        elif rid=="swiftness": self.dash_charges=2

    def sync(self):
        mhp = meta["upg_max_hp"]+run_hp_bonus()
        self.max_hp=max(1,mhp); self.hp=min(self.hp,self.max_hp)

    def take_damage(self):
        if self.invincible>0 or not self.alive: return
        if run_has("iron_will") and not run["iron_will_used"] and self.hp==1:
            run["iron_will_used"]=True; announce("IRON WILL — LETHAL BLOW NEGATED!",C_WHITE,120)
            spawn_particles(self.rect.centerx,self.rect.centery,22,[C_WHITE,C_GOLD],speed=5)
            self.invincible=90; return
        if self.dashing and self.dash_t>=(self.DASH_DUR-4):
            global time_scale, bullet_time_timer
            time_scale=0.28; bullet_time_timer=65
            self.invincible=max(self.invincible,self.DASH_DUR+12)
            spawn_particles(self.rect.centerx,self.rect.centery,20,[C_CYAN,C_WHITE,C_PURPLE],speed=5,gravity=-0.05)
            add_combo(2); return

        audio.play("hit",0.8)
        global combo_count,combo_timer,hit_flash_t,kill_streak; combo_count=0; combo_timer=0
        hit_flash_t = max(hit_flash_t, 18)
        kill_streak = 0   # broken streak
        self.hp-=1; self.invincible=65
        global screen_shake; screen_shake=max(screen_shake,9)
        spawn_particles(self.rect.centerx,self.rect.centery,14,[C_RED,C_PARCH,C_WHITE], speed=4,gravity=0.4,sz=(2,6),life=(10,28))
        if self.hp<=0:
            self.alive=False
            save_meta()                       # persist final totals on death

    def _execution(self, enemy):
        global screen_shake,hit_stop_timer
        screen_shake=22; hit_stop_timer=16.0
        self.pos.x=enemy.rect.centerx-self.rect.w//2; self.rect.x=int(self.pos.x)
        self.invincible=32; audio.play("slash",1.0)
        spawn_particles(enemy.rect.centerx,enemy.rect.centery,55, [C_RED,C_WHITE,C_GOLD,C_CYAN],speed=11,sz=(3,10))
        dmg=15 if isinstance(enemy,Boss) else 10
        # FIX: route through take_damage so death-cleanup runs (boss relic drop, save, NG+ bump, etc.)
        enemy.take_damage(dmg, self.rect.centerx, unblockable=True)
        # Reset posture / state ONLY if still alive (so the enemy "wakes up" from stun on a non-lethal exec)
        if enemy.alive and hasattr(enemy,'posture'):
            enemy.posture = getattr(enemy,'POSTURE_MAX',100)
            enemy.state = "hover" if hasattr(enemy,'_fire') else "active"
        if self.hp<self.max_hp: self.hp+=1
        self.mana = min(self.max_mana, self.mana + 35) 
        add_combo(6)

    def _start_dash(self, keys):
        if self.dash_cd>0: return
        dx,dy=0,0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx+=1
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx-=1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy-=1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy+=1
        if dx==0 and dy==0: dx=1 if self.facing_r else -1
        ln=max(1,math.hypot(dx,dy))
        self.dash_dir=pygame.Vector2(dx/ln,dy/ln)
        self.dashing=True; self.dash_t=self.DASH_DUR
        self.dash_cd=meta["upg_dash_cd"]
        self.invincible=self.DASH_DUR+5
        for _ in range(3): self.afterimages.append(Afterimage(self._base_r if self.facing_r else self._base_l,self.rect.x,self.rect.y))

    def _do_blink(self, cam_x):
        if self.blink_cd>0: return
        audio.play("blink",0.7)
        mx,my=get_mouse_pos(cam_x)
        dx,dy=mx-self.rect.centerx,my-self.rect.centery
        d=math.hypot(dx,dy); limit=self.BLINK_MAX
        if d>limit: dx,dy=dx*(limit/d),dy*(limit/d)
        void_tears.append(VoidTear(self.rect.centerx,self.rect.centery,C_PURPLE))
        spawn_particles(self.rect.centerx,self.rect.centery,18,[C_PURPLE,C_CYAN,C_RUNEGLOW],speed=5,gravity=-0.05)
        self.pos.x+=dx-self.rect.w//2; self.pos.y=min(self.pos.y+dy, GROUND_Y-self.rect.h)
        self.rect.topleft=(int(self.pos.x),int(self.pos.y))
        void_tears.append(VoidTear(self.rect.centerx,self.rect.centery,C_CYAN))
        spawn_particles(self.rect.centerx,self.rect.centery,18,[C_CYAN,C_PURPLE,C_WHITE],speed=5,gravity=-0.05)
        for _ in range(3): self.afterimages.append(Afterimage(self._base_r if self.facing_r else self._base_l,self.rect.x,self.rect.y))
        self.blink_cd=130; self.invincible=max(self.invincible,14)

        # FIX: Blink ALWAYS deals AoE damage on arrival. void_echo relic boosts dmg & radius.
        radius   = 180 if run_has("void_echo") else 110
        dmg      = (4 if run_has("void_echo") else 2) + run_atk_bonus()
        targets = [e for e in enemies if e.alive]
        if boss_obj and boss_obj.alive: targets.append(boss_obj)
        hit_any = False
        for e in targets:
            if math.hypot(e.rect.centerx-self.rect.centerx, e.rect.centery-self.rect.centery) < radius:
                # Add +1 bonus damage if hitting a Thug/Bulwark
                bonus = 1 if isinstance(e, Grunt) else 0 
                e.take_damage(dmg + bonus, self.rect.centerx, unblockable=True)
                spawn_particles(e.rect.centerx, e.rect.centery, 14, [C_PURPLE,C_CYAN,C_RUNEGLOW], speed=5)
                hit_any = True
        if hit_any:
            add_combo(1)
            global screen_shake
            screen_shake = max(screen_shake, 6)

    def _atk_damage(self):
        hb=pygame.Rect(0,0,88,95)
        if self.facing_r: hb.midleft=self.rect.center
        else: hb.midright=self.rect.center
        hit=False; dmg=3+run_atk_bonus()
        
        targets = [e for e in enemies if e.alive]
        if boss_obj and boss_obj.alive: targets.append(boss_obj)
        
        for e in targets:
            if hb.colliderect(e.rect):
                e.take_damage(dmg,self.rect.centerx)
                if run_has("plague_touch") and hasattr(e,'poison_timer'): e.poison_timer=200
                if isinstance(e,Seraph): spawn_particles(e.rect.centerx,e.rect.centery,12,[C_GOLD,C_WHITE],speed=4)
                else: spawn_particles(e.rect.centerx,e.rect.centery,9,[C_RUNEGLOW,C_WHITE],speed=4)
                hit=True
        if hit: 
            add_combo(1)
            self.mana = min(self.max_mana, self.mana + 12)

    def _ult_damage(self):
        hb=pygame.Rect(0,0,310,240)
        if self.facing_r: hb.midleft=self.rect.center
        else: hb.midright=self.rect.center
        dmg=6+run_atk_bonus()
        
        targets = [e for e in enemies if e.alive]
        if boss_obj and boss_obj.alive: targets.append(boss_obj)
        
        for e in targets:
            if hb.colliderect(e.rect):
                e.take_damage(dmg,self.rect.centerx, unblockable=True)
                spawn_particles(e.rect.centerx,e.rect.centery,28,[C_RED,C_GOLD,C_WHITE],speed=7)
        add_combo(4)

    def try_parry(self, proj_lists):
        if self.parry_t<=0: return
        pb=pygame.Rect(0,0,76,76); pb.centery=self.rect.centery
        if self.facing_r: pb.midleft=self.rect.midright
        else: pb.midright=self.rect.midleft
        for plist in proj_lists:
            for p in plist:
                if not p.alive or p.parried: continue
                if pb.collidepoint(p.pos.x,p.pos.y):
                    p.deflect()
                    self.parry_ok=22; self.invincible=max(self.invincible,22)
                    spawn_particles(int(p.pos.x),int(p.pos.y),18,[C_CYAN,C_WHITE,C_GOLD],speed=5,gravity=-0.05)
                    global hit_stop_timer; hit_stop_timer=5.0
                    add_combo(1)
                    self.mana = min(self.max_mana, self.mana + 15)

    def update(self, keys, cam_x, dt):
        if not self.alive: return
        self.sync()
        
        self.mana = min(self.max_mana, self.mana + (self.mana_regen * (dt / 60.0)))

        for attr in ['invincible','dash_cd','blink_cd','parry_cd','parry_ok','ult_cd','shoot_cd','atk_cd']:
            v=getattr(self,attr,0)
            if v>0: setattr(self,attr,max(0,v-dt))
        if self.parry_t>0: self.parry_t-=dt; 

        if (keys[pygame.K_f] or pygame.mouse.get_pressed()[0]) and not self.is_atk and not self.is_ult and self.atk_cd<=0:
            executed=False
            
            check=[e for e in enemies if getattr(e,'state','')=="stunned"]
            if boss_obj and getattr(boss_obj,'state','')=="stunned": check.append(boss_obj)
            
            for e in check:
                if math.hypot(e.rect.centerx-self.rect.centerx,e.rect.centery-self.rect.centery)<105:
                    self._execution(e); self.atk_cd=self.ATK_CD; executed=True; break
            if not executed:
                self.is_atk=True; self.atk_t=float(self.ATK_CD); self.atk_hit=False
                spawn_particles(self.rect.right if self.facing_r else self.rect.left, self.rect.centery,10,[C_PARCH,C_WHITE],speed=5)
                audio.play("slash",0.6)
                if combo_rank()[0] in ("S","S+"):
                    player_projs.append(Proj(self.rect.centerx,self.rect.centery, 10 if self.facing_r else -10,0, C_PURPLE,14,speed=8,shooter=self, ptype="player_wave",damage=2+run_atk_bonus(),piercing=True))

        if self.is_atk:
            self.atk_t-=dt
            if not self.atk_hit and self.atk_t<=self.ATK_CD*0.55:
                self.atk_hit=True; self._atk_damage()
            if self.atk_t<=0: self.is_atk=False; self.atk_cd=self.ATK_CD

        if keys[pygame.K_c] and meta["upg_ult"] and not self.is_ult and not self.is_atk and self.ult_cd<=0:
            self.is_ult=True; self.ult_t=float(self.ULT_DUR); self.ult_hit=False
            audio.play("slash",0.9); global screen_shake; screen_shake=max(screen_shake,16)
            spawn_particles(self.rect.centerx,self.rect.centery,28,[C_RED,C_ORANGE,C_GOLD],speed=8)

        if self.is_ult:
            self.ult_t-=dt
            if not self.ult_hit and self.ult_t<=self.ULT_DUR*0.45:
                self.ult_hit=True; self._ult_damage()
            if self.ult_t<=0: self.is_ult=False; self.ult_cd=meta.get("upg_ult_cd", 600)

        if pygame.mouse.get_pressed()[2] and self.shoot_cd<=0 and not self.dashing and not self.is_ult and self.mana >= 25:
            self.mana -= 25
            mx,my=get_mouse_pos(cam_x)
            ang=math.atan2(my-self.rect.centery,mx-self.rect.centerx)
            is_poison=run_has("plague_touch")
            player_projs.append(Proj(self.rect.centerx,self.rect.centery, math.cos(ang)*12,math.sin(ang)*12, C_PLAGUE if is_poison else C_PURPLE, 6,shooter=self,ptype="player_bolt", damage=2+run_atk_bonus(),poison=is_poison))
            audio.play("slash",0.45); self.shoot_cd=28

        if keys[pygame.K_g] and self.parry_cd<=0 and not self.is_atk:
            self.parry_t=self.PARRY_WIN+(meta["upg_parry_window"]-12)
            self.parry_cd=meta["upg_parry_window"]+48
            spawn_particles(self.rect.centerx,self.rect.centery,7,[C_CYAN,C_WHITE],speed=3,gravity=-0.05,sz=(2,5),life=(5,14))
            audio.play("parry",0.7)

        if keys[pygame.K_q] and meta["upg_blink"] and self.blink_cd<=0 and not self.dashing:
            self._do_blink(cam_x)

        if keys[pygame.K_LSHIFT] and not self.dashing and self.dash_cd<=0:
            self._start_dash(keys); audio.play("dash",0.6)

        if self.dashing:
            self.dash_t-=dt
            if int(self.dash_t)%2==0: self.afterimages.append(Afterimage(self._base_r if self.facing_r else self._base_l,self.rect.x,self.rect.y))
            spawn_particles(self.rect.centerx,self.rect.centery,3,[C_PURPLE,C_CYAN,C_RUNEGLOW],speed=3,gravity=-0.05,sz=(2,5),life=(4,12))
            if self.dash_t<=0: self.dashing=False; self.invincible=max(self.invincible,8)

        for ai in self.afterimages: ai.update()
        self.afterimages=[ai for ai in self.afterimages if ai.alive]

        if self.dashing:
            spd=360/self.DASH_DUR
            self.pos+=self.dash_dir*spd*dt; self.rect.topleft=(int(self.pos.x),int(self.pos.y))
            if self.rect.bottom>GROUND_Y: self.rect.bottom=GROUND_Y; self.pos.y=float(self.rect.y)
            return

        old_bottom = self.rect.bottom
        self.crouching = (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])
        self.rect.height = self.target_h // 2 if self.crouching else self.target_h
        self.rect.bottom = old_bottom
        self.pos.y = float(self.rect.y)

        mx=0
        if not self.crouching:
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]: mx-=4.8*dt; self.facing_r=False
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: mx+=4.8*dt; self.facing_r=True

        self.pos.x+=mx; self.rect.x=int(self.pos.x)
        for px,py,pw in platforms:
            pr=pygame.Rect(px,py,pw,20)
            if self.rect.colliderect(pr):
                if mx>0: self.rect.right=pr.left
                if mx<0: self.rect.left=pr.right
                self.pos.x=float(self.rect.x)

        self.vel.y=min(self.vel.y+0.78*dt,20)
        self.pos.y+=self.vel.y*dt; self.rect.y=int(self.pos.y)

        self.on_ground=False
        if self.rect.bottom>=GROUND_Y:
            self.rect.bottom=GROUND_Y; self.pos.y=float(self.rect.y); self.vel.y=0
            self.on_ground=True; self.dj_used=False

        for px,py,pw in platforms:
            pr=pygame.Rect(px,py,pw,20)
            if self.rect.colliderect(pr):
                if self.vel.y>0:
                    self.rect.bottom=pr.top; self.vel.y=0
                    self.on_ground=True; self.dj_used=False
                elif self.vel.y<0:
                    self.rect.top=pr.bottom; self.vel.y=0
                self.pos.y=float(self.rect.y)

        if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]:
            if self.on_ground:
                self.vel.y=-15.5
            elif meta["upg_double_jump"] and not self.dj_used:
                self.vel.y=-14.0; self.dj_used=True
                spawn_particles(self.rect.centerx,self.rect.bottom,10,[C_PURPLE,C_CYAN],speed=3,direction=math.pi/2,spread=math.pi/2,gravity=-0.1)

        if mx!=0: self.anim_t=(self.anim_t+abs(mx)*0.055)%4

    def draw(self, surf, cx):
        for ai in self.afterimages: ai.draw(surf,cx)
        if self.invincible>0 and not self.dashing and int(self.invincible)%6<3: return

        if self.parry_ok>0:
            pr2=54+(20-self.parry_ok)*2; ps2=pygame.Surface((pr2*2,pr2*2),pygame.SRCALPHA)
            pygame.draw.circle(ps2,(*C_CYAN,int(190*self.parry_ok/22)),(pr2,pr2),pr2,4)
            surf.blit(ps2,(self.rect.centerx-int(cx)-pr2,self.rect.centery-pr2))

        if self.parry_t>0:
            sa=int(170*self.parry_t/self.PARRY_WIN); sh=pygame.Surface((80,80),pygame.SRCALPHA)
            pygame.draw.ellipse(sh,(*C_CYAN,sa),(0,0,80,80)); pygame.draw.ellipse(sh,(*C_WHITE,min(255,sa+55)),(0,0,80,80),3)
            ox=self.rect.right-int(cx) if self.facing_r else self.rect.left-int(cx)-80
            surf.blit(sh,(ox,self.rect.centery-40))

        vy=self.rect.y
        fi = int(self.anim_t) % len(self._frames_r)
        img = self._frames_r[fi] if self.facing_r else self._frames_l[fi]
        
        if self.crouching:
            img = pygame.transform.scale(img, (img.get_width(), img.get_height() // 2))
            
        surf.blit(img,(self.rect.x-int(cx),vy))

        if self.is_atk:
            prog=1.0-(self.atk_t/self.ATK_CD)
            ang=(-65+88*prog) if self.facing_r else (245-88*prog)
            rot=pygame.transform.rotate(self._slash, ang if not self.facing_r else -ang)
            rot.set_alpha(255 if prog<0.65 else int(255*(1-prog)/0.35))
            surf.blit(rot,(self.rect.centerx-int(cx)+(18 if self.facing_r else -18)-rot.get_width()//2, self.rect.centery-rot.get_height()//2))

        if self.is_ult:
            prog=1.0-(self.ult_t/self.ULT_DUR); sf=3.8+math.sin(prog*math.pi)*1.4
            base_slash = self._slash_ult
            sw2,sh2=int(max(1,base_slash.get_width()*sf)),int(max(1,base_slash.get_height()*sf))
            big=pygame.transform.smoothscale(base_slash,(sw2,sh2)).copy()
            big.fill((255,55,10,255),special_flags=pygame.BLEND_RGBA_MULT)
            ang2=(-95+150*prog) if self.facing_r else (275-150*prog)
            rot2=pygame.transform.rotate(big if self.facing_r else pygame.transform.flip(big,True,False),-ang2)
            rot2.set_alpha(255 if prog<0.65 else int(255*(1-prog)/0.35))
            surf.blit(rot2,(self.rect.centerx-int(cx)+(40 if self.facing_r else -40)-rot2.get_width()//2, self.rect.centery-rot2.get_height()//2))

    def draw_hud(self, surf):
        bw,bh,bx,by=280,24,35,35
        pygame.draw.rect(surf,(15,10,22),(bx,by,bw,bh),border_radius=4)
        pygame.draw.rect(surf,(60,55,72),(bx-2,by-2,bw+4,bh+4),2,border_radius=5)
        if self.hp>0:
            pct=self.hp/self.max_hp
            c=(int(195*(1-pct)+35*pct),int(35*pct),int(35*pct))
            pygame.draw.rect(surf,c,(bx,by,int(bw*pct),bh),border_radius=4)
        for i in range(1,self.max_hp):
            lx=bx+int(i*(bw/self.max_hp))
            pygame.draw.line(surf,(60,55,72),(lx,by),(lx,by+bh),1)
        draw_text(surf,f"HP  {self.hp}/{self.max_hp}",F_SM,C_WHITE,bx,by-24)
        
        mana_y = by + bh + 8
        pygame.draw.rect(surf, (10, 15, 25), (bx, mana_y, bw, 10), border_radius=2)
        if self.mana > 0:
            m_pct = self.mana / self.max_mana
            pygame.draw.rect(surf, C_CYAN, (bx, mana_y, int(bw * m_pct), 10), border_radius=2)
        mn_lbl = F_TINY.render(f"MANA  {int(self.mana)}/{int(self.max_mana)}", True, C_CYAN)
        surf.blit(mn_lbl, (bx + bw + 8, mana_y - 2))

        draw_text(surf,f"FLOOR {run['floor']}",F_SM,C_GREY,bx+220,by-24)
        # Floor timer
        ft = int(floor_time_s)
        timer_str = f"{ft//60}:{ft%60:02d}"
        draw_text(surf, timer_str, F_TINY, C_GREY, bx+bw-1, by+bh+20)

        # ── stats row + active relics row
        info_y = mana_y + 18
        draw_text(surf, f"KILLS  {run['kills']}", F_SM, C_GREY, bx, info_y)
        draw_text(surf, f"✦ {meta['divine_essence']}", F_SM, C_CYAN, bx + 110, info_y)
        if meta.get("curse_level", 0) > 0:
            draw_text(surf, f"NG+{meta['curse_level']}", F_SM, C_RED, bx + 220, info_y)

        # Active-relic icons (top-left, under stats)
        for i, rid in enumerate(run["relics"]):
            d = RELIC_DEFS[rid]
            rx = bx + i * 36; ry = info_y + 28
            chip = pygame.Rect(rx, ry, 32, 32)
            pygame.draw.rect(surf, (15, 10, 22), chip, border_radius=4)
            pygame.draw.rect(surf, d["color"], chip, 2, border_radius=4)
            ic = F_SM.render(d["icon"], True, d["color"])
            surf.blit(ic, (rx + 16 - ic.get_width()//2, ry + 16 - ic.get_height()//2))

        # ── "GAME SAVED" flash (top-right corner, fades out)
        global _save_flash_t
        if _save_flash_t > 0:
            a = min(255, int(255 * (_save_flash_t / 60)))
            txt = F_SM.render("✓ GAME SAVED", True, C_PLAGUE)
            txt.set_alpha(a)
            surf.blit(txt, (WIDTH - txt.get_width() - 22, HEIGHT - 50))
            _save_flash_t = max(0, _save_flash_t - 1)

        ax,ay,sz,sp=35,HEIGHT-95,50,15
        abilities=[]
        abilities.append(("SHF","DASH",self.dash_cd,meta["upg_dash_cd"],C_CYAN))
        abilities.append(("G","PARRY",self.parry_cd,self.PARRY_WIN+48,C_GOLD if self.parry_t>0 else C_WHITE))
        abilities.append(("RMB","BOLT",self.shoot_cd,28,C_PURPLE))
        if meta["upg_blink"]: abilities.insert(0,("Q","BLINK",self.blink_cd,130,C_RUNEGLOW))
        if meta["upg_ult"]:   abilities.append(("C","ULT",self.ult_cd,600,C_RED))

        for i,(k,nm,cd,mcd,col) in enumerate(abilities):
            cx2=ax+(sz+sp)*i; cy2=ay
            bg=pygame.Surface((sz,sz),pygame.SRCALPHA); bg.fill((12,8,20,180))
            surf.blit(bg,(cx2,cy2))
            if cd>0:
                ov=pygame.Surface((sz,int(sz*(cd/mcd))),pygame.SRCALPHA); ov.fill((0,0,0,170))
                surf.blit(ov,(cx2,cy2+sz-int(sz*(cd/mcd))))
            
            border_col = col if cd<=0 else C_GREY
            if nm == "BOLT" and self.mana < 25: border_col = C_RED

            pygame.draw.rect(surf,border_col,(cx2,cy2,sz,sz),2,border_radius=3)
            kt=F_SM.render(k,True,border_col)
            surf.blit(kt,(cx2+sz//2-kt.get_width()//2,cy2+sz//2-kt.get_height()//2))
            nt=F_TINY.render(nm,True,border_col)
            surf.blit(nt,(cx2+sz//2-nt.get_width()//2,cy2-16))

        if combo_timer>0:
            rnk,rcol=combo_rank()
            draw_text(surf,f"RANK {rnk}",F_BIG,rcol,WIDTH-180,36,center=True)
            cw=110
            pygame.draw.rect(surf,(35,35,45),(WIDTH-180-cw//2,84,cw,5),border_radius=2)
            pygame.draw.rect(surf,rcol,(WIDTH-180-cw//2,84,int(cw*(combo_timer/COMBO_WINDOW)),5),border_radius=2)
            draw_text(surf,f"×{combo_count}",F_SM,rcol,WIDTH-180,92,center=True)

        if kill_streak >= 5:
            sc = C_RUNEGLOW if kill_streak >= 10 else C_ORANGE
            draw_text(surf, f"STREAK  ×{kill_streak}", F_SM, sc, WIDTH-180, 128, center=True)

# ─────────────────────────────────────────────────────────────────────────────
#  LIGHTING
# ─────────────────────────────────────────────────────────────────────────────
def build_light_layer(torches, doors, cam_x):
    ll=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    ll.fill((160, 150, 180, 255)) 
    for t in torches: t.draw_light(ll,cam_x)
    for d in doors: d.draw_light(ll,cam_x)
    for eo in env_objects:
        if hasattr(eo, 'draw_light'): eo.draw_light(ll, cam_x)
    return ll

# ─────────────────────────────────────────────────────────────────────────────
#  WORLD / FLOOR BUILDER
# ─────────────────────────────────────────────────────────────────────────────
torches   = []
doors     = []
boss_obj  = None
run_seed  = 1

def build_floor(floor_num):
    global FLOOR_W, enemies, player_projs, torches, doors, boss_obj, platforms, relic_pickups, essence_drops, env_objects
    
    FLOOR_W = 3800 if meta["bosses_defeated"] == 0 else 7800
    
    particles.clear(); void_tears.clear()
    essence_drops=[]; player_projs=[]; relic_pickups=[]; env_objects=[]

    rng=random.Random(run_seed+floor_num*17)
    refresh_bg(run_seed+floor_num)

    platforms[:] = gen_platforms(rng, floor_num)
    
    torches.clear()
    for x in range(300, FLOOR_W, 800):
        torches.append(Torch(x, GROUND_Y))
    
    for px, py, pw in platforms:
        if rng.random() > 0.2: 
            torches.append(Torch(px + 20, py))
            torches.append(Torch(px + pw - 20, py))

    specs=gen_enemies(rng, floor_num, platforms)
    enemies.clear()
    for sp in specs:
        t=sp["type"]
        if t=="grunt":        enemies.append(Grunt(sp["x"],sp["y"],sp["pl"],sp["pr"]))
        elif t=="bulwark":    enemies.append(Bulwark(sp["x"],sp["y"],sp["pl"],sp["pr"]))
        elif t=="wraith":     enemies.append(Wraith(sp["x"],sp["y"]))
        elif t=="seraph":     enemies.append(Seraph(sp["x"],sp["y"],elite=False))
        elif t=="seraph_elite": enemies.append(Seraph(sp["x"],sp["y"],elite=True))
        elif t=="bulwark_elite":
            b=Bulwark(sp["x"],sp["y"],sp["x"]-150,sp["x"]+150)
            b.HP=int(8*get_diff()); b.hp=b.HP
            enemies.append(b)

    boss_obj=None
    doors.clear()
    
    # FIX: Mid-floor door to The Inevitable (only if they've beaten the boss at least once -> NG+1)
    if floor_num >= 1 and meta["bosses_defeated"] > 0:
        inevitable_door = Door(FLOOR_W//2, GROUND_Y-170, C_RUNEGLOW, "THE INEVITABLE [E]", "sanctum_midrun")
        inevitable_door.locked = True
        doors.append(inevitable_door)
        
    if floor_num < 3: doors.append(Door(FLOOR_W-300, GROUND_Y-170, C_CYAN, "DESCEND [E]", f"floor{floor_num+1}"))
    else: doors.append(Door(FLOOR_W-300, GROUND_Y-170, C_RED, "ENTER THE SANCTUM [E]", "boss_room"))
    announce(f"FLOOR {floor_num}  — {len([e for e in enemies if e.alive])} ENTITIES DETECTED", C_CYAN if floor_num==1 else C_ORANGE, 160)

def build_boss_room():
    global enemies, player_projs, torches, doors, boss_obj, platforms, relic_pickups, essence_drops, env_objects, FLOOR_W
    FLOOR_W = 3200                                  # bound the boss arena
    particles.clear(); void_tears.clear()
    essence_drops=[]; player_projs=[]; relic_pickups=[]; enemies.clear(); env_objects=[]
    rng=random.Random(run_seed+999); refresh_bg(run_seed+999)

    platforms[:]=[]
    for px,py,pw in [(300, GROUND_Y-160, 200), (700, GROUND_Y-300, 180), (1100, GROUND_Y-160, 200),
                     (1500, GROUND_Y-350, 180), (1900, GROUND_Y-160, 200), (2300, GROUND_Y-300, 180),
                     (2700, GROUND_Y-160, 200)]:
        platforms.append((px,py,pw))
        
    torches.clear()
    for px, py, pw in platforms:
        torches.append(Torch(px + pw//2, py))
    for x in range(100, 3200, 400):
        torches.append(Torch(x, GROUND_Y))
        
    boss_obj=Boss(1500, GROUND_Y-200); enemies.clear(); doors.clear()
    announce("⚠  THE SOVEREIGN AETHERIA AWAKENS",C_RED,200); audio.bgm("bgm_boss",audio.bgm_vol)

def build_sanctum(midrun=False):
    global enemies,player_projs,torches,doors,boss_obj, platforms,relic_pickups,essence_drops, env_objects
    particles.clear(); void_tears.clear()
    essence_drops=[]; player_projs=[]; relic_pickups=[]; enemies.clear(); boss_obj=None
    env_objects=[]                                 # reset shrines etc

    platforms[:]=[(200, GROUND_Y-150, 300), (800, GROUND_Y-240, 200), (1400, GROUND_Y-150, 250)]
    
    torches.clear()
    for px, py, pw in platforms:
        torches.append(Torch(px + 20, py))
        torches.append(Torch(px + pw - 20, py))
    torches.append(Torch(500, GROUND_Y))
    torches.append(Torch(1100, GROUND_Y))
    
    # Healing shrine — pay essence, regain HP. Always available in sanctum.
    env_objects.append(HealShrine(1200, GROUND_Y-90))
    
    doors.clear()
    if midrun:
        # Return door — go back to the floor you came from
        ret_floor = run.get("sanctum_return_floor") or 1
        d = Door(1600, GROUND_Y-170, C_CYAN, f"RETURN TO FLOOR {ret_floor} [E]", "return_to_floor")
        d.locked = False; doors.append(d)
        announce(f"THE INEVITABLE — FLOOR {ret_floor} AWAITS YOUR RETURN", C_RUNEGLOW, 160)
    else:
        d=Door(1600, GROUND_Y-170, C_GOLD,"NEXT RUN [E]","new_run")
        d.locked=False; doors.append(d)
        announce("THE SANCTUM — SPEND YOUR ESSENCE",C_CYAN,160)
    refresh_bg(42)
    audio.bgm("bgm_explore",audio.bgm_vol)

# ─────────────────────────────────────────────────────────────────────────────
#  MENU LAYOUT (dynamic rects)
# ─────────────────────────────────────────────────────────────────────────────
def menu_btn(i, n=4, width=330, h=65):
    total = n*h + (n-1)*12
    y0 = HEIGHT//2 - total//2
    return pygame.Rect(WIDTH//2-width//2, y0+i*(h+12), width, h)

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────
display_surf = pygame.Surface((WIDTH, HEIGHT))
menu_cam_x   = 0.0

def start_new_run():
    global player, run, run_seed, STATE, camera_x, boss_obj, kill_streak, kill_streak_best
    meta["total_runs"] += 1
    save_meta()                                # persist run counter
    run_seed = random.randint(1, 99999)
    kill_streak = 0; kill_streak_best = 0
    run.update({
        "floor": 1, "kills": 0, "relics": [], "relic_offered": [],
        "curse_active": meta["curse_level"]>0,
        "iron_will_used": False, "double_jump_used": False,
        "sanctum_return_floor": None,
    })
    player = Player(200, GROUND_Y - 80)
    camera_x = 0.0
    build_floor(1)
    STATE = "game"

def state_for_floor(fl): return "game"

def draw_menu_bg():
    global menu_cam_x
    menu_cam_x += 0.3
    draw_bg(display_surf, menu_cam_x*0.2)
    draw_mg(display_surf, menu_cam_x*0.45)
    ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,165))
    display_surf.blit(ov,(0,0))
    ver=F_TINY.render("v1.0",True,(55,50,70))
    display_surf.blit(ver,(WIDTH-ver.get_width()-8,HEIGHT-ver.get_height()-6))

vignette=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
for _i in range(55): pygame.draw.rect(vignette,(0,0,0,int(155*(1-_i/55))),(_i,_i,WIDTH-_i*2,HEIGHT-_i*2),2)

def floor_to_display():
    if _FLOOR_IMG:
        th = _FLOOR_IMG.get_height(); tw = _FLOOR_IMG.get_width()
        for i in range(-2, int(WIDTH/tw)+4):
            display_surf.blit(_FLOOR_IMG, (i*tw - int(camera_x)%tw - tw*2 - (i*2), GROUND_Y))
        fh = HEIGHT - GROUND_Y - th
        if fh > 0: pygame.draw.rect(display_surf, (18, 14, 10), (0, GROUND_Y + th, WIDTH, fh))
    else:
        tw=FLOOR_TILE.get_width(); th=FLOOR_TILE.get_height()
        for i in range(-2,int(WIDTH/tw)+4):
            display_surf.blit(FLOOR_TILE,(i*tw-int(camera_x)%tw-tw*2, GROUND_Y))
        fh = HEIGHT - GROUND_Y - th
        if fh > 0: pygame.draw.rect(display_surf, (20, 12, 28), (0, GROUND_Y + th, WIDTH, fh))

def draw_platforms():
    for px,py,pw in platforms:
        sx=px-int(camera_x)
        if sx>-200 and sx<WIDTH+200:
            if _PLATFORM_IMG:
                orig_w = _PLATFORM_IMG.get_width(); orig_h = _PLATFORM_IMG.get_height()
                plat_h = max(20, min(40, int(orig_h * (pw / orig_w))))
                ps = pygame.transform.scale(_PLATFORM_IMG, (pw, plat_h))
                display_surf.blit(ps, (sx, py)) 
            else:
                ps=make_plat_surf(pw)
                display_surf.blit(ps,(sx, py)) 

def draw_game():
    draw_bg(display_surf, camera_x)
    draw_mg(display_surf, camera_x)
    for m in motes: m.draw(display_surf, camera_x)
    floor_to_display()
    draw_platforms()

    for t in torches: t.draw(display_surf, camera_x)
    for eo in env_objects: eo.draw(display_surf, camera_x)
    for e in enemies:
        if hasattr(e,'draw'): e.draw(display_surf, camera_x)
    if boss_obj: boss_obj.draw(display_surf, camera_x)
    for r in relic_pickups: r.draw(display_surf, camera_x)
    for d in doors: d.draw(display_surf, camera_x)
    if player: player.draw(display_surf, camera_x)
    for p in player_projs: p.draw(display_surf, camera_x)
    for d in essence_drops: d.draw(display_surf, camera_x)
    for vt in void_tears: vt.draw(display_surf, camera_x)
    draw_particles(display_surf, camera_x)
    draw_dmg_numbers(display_surf, camera_x)

    ll=build_light_layer(torches, doors, camera_x)
    display_surf.blit(ll,(0,0),special_flags=pygame.BLEND_RGBA_MULT)

    if player: player.draw_hud(display_surf)

    if boss_obj and boss_obj.alive:
        ph=boss_obj.ph; bw,bh=550,25; bxb=WIDTH//2-bw//2; byb=HEIGHT-75
        pygame.draw.rect(display_surf,(22,10,35),(bxb-2,byb-2,bw+4,bh+4),border_radius=6)
        phc={1:C_GOLD,2:C_ORANGE,3:C_RED}[ph]
        pygame.draw.rect(display_surf,phc,(bxb,byb,int(bw*boss_obj.hp/boss_obj.MAX_HP),bh),border_radius=5)
        phl=F_SM.render(f"SOVEREIGN AETHERIA  — PHASE {ph}",True,phc)
        display_surf.blit(phl,(WIDTH//2-phl.get_width()//2,byb-24))
        # Posture bar
        posture_pct = max(0.0, boss_obj.posture / boss_obj.POSTURE_MAX)
        pb_w = int(bw * posture_pct)
        pygame.draw.rect(display_surf,(30,30,15),(bxb,byb+bh+4,bw,6),border_radius=2)
        pygame.draw.rect(display_surf,C_CYAN,(bxb,byb+bh+4,pb_w,6),border_radius=2)
        if posture_pct < 0.25:
            stun_lbl = F_TINY.render("STAGGER NEAR!", True, C_CYAN)
            display_surf.blit(stun_lbl, (bxb+bw+8, byb+bh+1))
        if ph==2:
            kt=F_SM.render(f"KEYS {boss_obj.keys_found}/4"+(" — STRIKE!" if boss_obj.p2_vuln else " — COLLECT THEM"),True,C_GOLD if not boss_obj.p2_vuln else C_CYAN)
            display_surf.blit(kt,(WIDTH//2-kt.get_width()//2,byb+bh+14))

    alive_count=sum(1 for e in enemies if e.alive)
    if alive_count>0 and not boss_obj:
        ec=F_SM.render(f"ENTITIES: {alive_count}",True,C_RED); display_surf.blit(ec,(WIDTH-ec.get_width()-20,20))
    elif alive_count==0 and not boss_obj:
        ec=F_SM.render("ENTITIES: 0",True,C_CYAN); display_surf.blit(ec,(WIDTH-ec.get_width()-20,20))

    for d in doors:
        if not d.locked and not d.opening:
            if player and d.rect.colliderect(player.rect):
                ht=F_SM.render("Press E to proceed",True,d.color)
                display_surf.blit(ht,(WIDTH//2-ht.get_width()//2,HEIGHT//2-80))

    ay=HEIGHT//4
    for ann in announce_queue:
        text,col,timer,mt=ann
        a=min(255,int(timer*5.5))
        bg=pygame.Surface((len(text)*11+36,45),pygame.SRCALPHA); bg.fill((0,0,0,min(190,a)))
        display_surf.blit(bg,(WIDTH//2-bg.get_width()//2,ay))
        t=F_MED.render(text,True,col); t.set_alpha(a); display_surf.blit(t,(WIDTH//2-t.get_width()//2,ay+12))
        ay+=50

    if player and not player.alive:
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,200)); display_surf.blit(ov,(0,0))
        draw_text(display_surf,"YOUR REIGN ENDS HERE",F_BIG,C_RED,WIDTH//2,HEIGHT//2-150,center=True)
        # Run stats card
        sw, sh = 600, 255
        card = pygame.Rect(WIDTH//2 - sw//2, HEIGHT//2 - 100, sw, sh)
        pygame.draw.rect(display_surf, (16, 10, 26), card, border_radius=8)
        pygame.draw.rect(display_surf, C_RED, card, 2, border_radius=8)
        draw_text(display_surf, "— RUN SUMMARY —", F_MED, C_PARCH2,
                  WIDTH//2, card.y + 22, center=True)
        rows = [
            (f"Floor reached", f"{run['floor']}"),
            (f"Kills",         f"{run['kills']}"),
            (f"Best streak",   f"×{kill_streak_best}"),
            (f"Best combo",    f"×{meta['best_combo']}"),
            (f"Relics",        f"{len(run['relics'])}/{meta['upg_relic_slots']}"),
            (f"Total essence", f"{meta['divine_essence']}"),
        ]
        for i,(k,v) in enumerate(rows):
            ry = card.y + 70 + i*28
            draw_text(display_surf, k, F_SM, C_GREY,  card.x + 30,    ry)
            draw_text(display_surf, v, F_SM, C_WHITE, card.right - 30 - F_SM.size(v)[0], ry)
        draw_text(display_surf,"[SPACE] Return to Menu",F_MED,C_PARCH2,WIDTH//2,card.bottom+30,center=True)

    if hit_flash_t > 0:
        fa = int(120 * (hit_flash_t / 18))
        hf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); hf.fill((180, 0, 0, fa))
        display_surf.blit(hf, (0, 0))

    if bullet_time_timer>0:
        bto=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); bto.fill((0,55,115,int(32*(bullet_time_timer/65))))
        display_surf.blit(bto,(0,0))
        btt=F_SM.render("COUNTER VOID",True,C_CYAN); btt.set_alpha(min(255,int(32*5*(bullet_time_timer/65))))
        display_surf.blit(btt,(WIDTH//2-btt.get_width()//2,76))

    if player and player.alive and player.hp<=1:
        vignette.set_alpha(int(185*(0.55+0.45*math.sin(pygame.time.get_ticks()*0.006))))
        tv=vignette.copy(); rv=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); rv.fill((110,0,0,0))
        tv.blit(rv,(0,0),special_flags=pygame.BLEND_RGBA_ADD); display_surf.blit(tv,(0,0))

    hint=F_TINY.render("WASD/ARROWS: move • SPACE: jump • SHIFT: dash • LMB/F: attack • RMB: bolt • G: parry • Q: blink • C: ult • E: interact • P: pause • F11: fullscreen",True,(80,75,100))
    display_surf.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT-24))
    ver=F_TINY.render("v1.0",True,(55,50,70))
    display_surf.blit(ver,(WIDTH-ver.get_width()-8,HEIGHT-ver.get_height()-6))


while True:
    raw_dt = clock.tick(60)
    dt_mult = min(raw_dt/(1000/60), 2.8)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: save_meta(); pygame.quit(); sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my = get_mouse_pos()

            if STATE=="main_menu":
                if menu_view=="main":
                    if menu_btn(0).collidepoint(mx,my): start_new_run()
                    elif menu_btn(1).collidepoint(mx,my): STATE,menu_view="main_menu","codex"
                    elif menu_btn(2).collidepoint(mx,my): STATE,menu_view="main_menu","settings"
                    elif menu_btn(3).collidepoint(mx,my): save_meta(); pygame.quit(); sys.exit()
                elif menu_view=="settings":
                    if pygame.Rect(WIDTH//2-180,HEIGHT//2-100,50,45).collidepoint(mx,my): audio.set_bgm_vol(audio.bgm_vol-0.1)
                    elif pygame.Rect(WIDTH//2+130,HEIGHT//2-100,50,45).collidepoint(mx,my): audio.set_bgm_vol(audio.bgm_vol+0.1)
                    elif pygame.Rect(WIDTH//2-180,HEIGHT//2-15,50,45).collidepoint(mx,my): audio.set_sfx_vol(audio.sfx_vol-0.1); audio.play("slash",0.5)
                    elif pygame.Rect(WIDTH//2+130,HEIGHT//2-15,50,45).collidepoint(mx,my): audio.set_sfx_vol(audio.sfx_vol+0.1); audio.play("slash",0.5)
                    elif pygame.Rect(WIDTH//2-180,HEIGHT//2+70,50,45).collidepoint(mx,my): curr_res_idx=max(0,curr_res_idx-1)
                    elif pygame.Rect(WIDTH//2+130,HEIGHT//2+70,50,45).collidepoint(mx,my): curr_res_idx=min(len(RESOLUTIONS)-1,curr_res_idx+1)
                    elif pygame.Rect(WIDTH//2-180,HEIGHT//2+155,50,45).collidepoint(mx,my) or pygame.Rect(WIDTH//2+130,HEIGHT//2+155,50,45).collidepoint(mx,my):
                        is_fullscreen = not is_fullscreen
                    elif pygame.Rect(WIDTH//2-200,HEIGHT//2+250,180,55).collidepoint(mx,my): menu_view="main"
                    elif pygame.Rect(WIDTH//2+20,HEIGHT//2+250,180,55).collidepoint(mx,my):
                        WINDOW_W,WINDOW_H=RESOLUTIONS[curr_res_idx]
                        flags = pygame.FULLSCREEN if is_fullscreen else 0
                        screen=pygame.display.set_mode((WINDOW_W,WINDOW_H), flags)
                    elif pygame.Rect(WIDTH//2-100,HEIGHT//2+325,200,45).collidepoint(mx,my):
                        meta.clear()
                        meta.update(META_DEFAULTS)
                        save_meta()
                        menu_view = "main"
                elif menu_view=="codex":
                    if pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55).collidepoint(mx,my): menu_view="main"
            
            elif STATE=="paused":
                if menu_view=="pause_main":
                    if menu_btn(0,5).collidepoint(mx,my): STATE=PREV_STATE
                    elif menu_btn(1,5).collidepoint(mx,my): menu_view="inventory"
                    elif menu_btn(2,5).collidepoint(mx,my): menu_view="settings"
                    elif menu_btn(3,5).collidepoint(mx,my): STATE,menu_view="main_menu","main"; audio.bgm("bgm_explore",audio.bgm_vol)
                    elif menu_btn(4,5).collidepoint(mx,my): save_meta(); pygame.quit(); sys.exit()
                elif menu_view=="inventory":
                    if pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55).collidepoint(mx,my): menu_view="pause_main"
                elif menu_view=="settings":
                    if pygame.Rect(WIDTH//2-180,HEIGHT//2-100,50,45).collidepoint(mx,my): audio.set_bgm_vol(audio.bgm_vol-0.1)
                    elif pygame.Rect(WIDTH//2+130,HEIGHT//2-100,50,45).collidepoint(mx,my): audio.set_bgm_vol(audio.bgm_vol+0.1)
                    elif pygame.Rect(WIDTH//2-180,HEIGHT//2-15,50,45).collidepoint(mx,my): audio.set_sfx_vol(audio.sfx_vol-0.1); audio.play("slash",0.5)
                    elif pygame.Rect(WIDTH//2+130,HEIGHT//2-15,50,45).collidepoint(mx,my): audio.set_sfx_vol(audio.sfx_vol+0.1); audio.play("slash",0.5)
                    elif pygame.Rect(WIDTH//2-180,HEIGHT//2+70,50,45).collidepoint(mx,my): curr_res_idx=max(0,curr_res_idx-1)
                    elif pygame.Rect(WIDTH//2+130,HEIGHT//2+70,50,45).collidepoint(mx,my): curr_res_idx=min(len(RESOLUTIONS)-1,curr_res_idx+1)
                    elif pygame.Rect(WIDTH//2-180,HEIGHT//2+155,50,45).collidepoint(mx,my) or pygame.Rect(WIDTH//2+130,HEIGHT//2+155,50,45).collidepoint(mx,my):
                        is_fullscreen = not is_fullscreen
                    elif pygame.Rect(WIDTH//2-200,HEIGHT//2+250,180,55).collidepoint(mx,my): menu_view="pause_main"
                    elif pygame.Rect(WIDTH//2+20,HEIGHT//2+250,180,55).collidepoint(mx,my):
                        WINDOW_W,WINDOW_H=RESOLUTIONS[curr_res_idx]
                        flags = pygame.FULLSCREEN if is_fullscreen else 0
                        screen=pygame.display.set_mode((WINDOW_W,WINDOW_H), flags)
                    elif pygame.Rect(WIDTH//2-100,HEIGHT//2+325,200,45).collidepoint(mx,my):
                        meta.clear()
                        meta.update(META_DEFAULTS)
                        save_meta()
                        STATE, menu_view = "main_menu", "main"
                        audio.bgm("bgm_explore",audio.bgm_vol)
                elif menu_view=="sanctum_shop":
                    cost_hp=20; cost_dash=18; cost_dj=35; cost_blink=40; cost_ult=60; cost_parry=25; cost_relic=30
                    shop_items=[
                        ("upg_max_hp", cost_hp, True),
                        ("upg_dash_cd", cost_dash, meta["upg_dash_cd"]>35),
                        ("upg_double_jump", cost_dj, not meta["upg_double_jump"]),
                        ("upg_blink", cost_blink, not meta["upg_blink"]),
                        ("upg_ult", cost_ult, not meta["upg_ult"]),
                        ("upg_parry_window", cost_parry, meta["upg_parry_window"]<22),
                        ("upg_relic_slots", cost_relic, meta["upg_relic_slots"]<5)
                    ]
                    for bi, (key, cost, avail) in enumerate(shop_items):
                        r = menu_btn(bi, len(shop_items), 500, 55)
                        if r.collidepoint(mx, my) and avail and meta["divine_essence"] >= cost:
                            meta["divine_essence"] -= cost
                            if key == "upg_max_hp": meta[key] += 1; player.max_hp += 1; player.hp += 1
                            elif key == "upg_dash_cd": meta[key] -= 5
                            elif key in ["upg_double_jump", "upg_blink", "upg_ult"]: meta[key] = True
                            elif key == "upg_parry_window": meta[key] += 2
                            elif key == "upg_relic_slots": meta[key] += 1
                            audio.play("relic", 0.8)
                            save_meta()           # persist purchase immediately
                            
                    back=pygame.Rect(WIDTH//2-100,HEIGHT-80,200,50)
                    if back.collidepoint(mx,my): STATE="sanctum"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                flags = pygame.FULLSCREEN if is_fullscreen else 0
                screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)
            elif event.key in (pygame.K_ESCAPE,pygame.K_p):
                if STATE in ("game","sanctum"):
                    PREV_STATE=STATE; STATE="paused"; menu_view="pause_main"
                elif STATE=="paused":
                    if menu_view=="sanctum_shop":
                        STATE = PREV_STATE if PREV_STATE in ("game","sanctum") else "sanctum"
                    elif menu_view in ("settings","inventory"):
                        menu_view="pause_main"
                    else:
                        STATE=PREV_STATE
            elif STATE=="game" and player and not player.alive:
                if event.key==pygame.K_SPACE:
                    STATE,menu_view="main_menu","main"; audio.bgm("bgm_explore",audio.bgm_vol)
            elif STATE in ("game","sanctum") and player and player.alive:
                if event.key==pygame.K_e:
                    for d in doors:
                        if not d.locked and d.rect.colliderect(player.rect): d.try_open()
                    if STATE=="sanctum":
                        npc_rect=pygame.Rect(800,GROUND_Y-160,80,100)
                        if npc_rect.colliderect(player.rect):
                            PREV_STATE="sanctum"; STATE="paused"; menu_view="sanctum_shop"

    display_surf.fill(BG)

    if STATE=="main_menu":
        draw_menu_bg()
        for m in motes: m.update(dt_mult); m.draw(display_surf, menu_cam_x*0.2)
        t=pygame.time.get_ticks()/1000; ty=int(HEIGHT//4-50+math.sin(t*0.8)*4)
        draw_text(display_surf,"ECLIPSE",F_TITLE,C_VOID,WIDTH//2,ty,center=True)
        draw_text(display_surf,"ECLIPSE",F_TITLE,(60,0,100),WIDTH//2-1,ty-1,center=True)
        draw_text(display_surf,"ECLIPSE",F_TITLE,C_RUNEGLOW,WIDTH//2+1,ty+1,center=True)
        draw_text(display_surf,"OF THE ORDER",F_MED,C_PARCH2,WIDTH//2,ty+80,center=True)
        draw_text(display_surf,"─────────────────────────────",F_SM,C_SEPIA,WIDTH//2,ty+115,center=True)

        sub=F_TINY.render(f"RUNS: {meta['total_runs']}  •  BEST COMBO: ×{meta['best_combo']}  •  KILLS: {meta['total_kills']}  •  ✦ {meta['divine_essence']}  •  BOSSES: {meta['bosses_defeated']}",True,C_GREY)
        display_surf.blit(sub,(WIDTH//2-sub.get_width()//2,HEIGHT-40))

        if menu_view=="main":
            for i,(lbl,col) in enumerate([("BEGIN THE HUNT",C_PARCH),("CODEX",C_PARCH),("SETTINGS",C_PARCH),("ABANDON VOID",C_RED)]):
                draw_btn(display_surf,lbl,F_MED,col,menu_btn(i),C_CYAN if col==C_PARCH else C_RED)
        elif menu_view=="settings":
            draw_text(display_surf,"SETTINGS",F_BIG,C_GOLD,WIDTH//2,HEIGHT//4,center=True)
            def _settings_row(label, val_str, row_y):
                draw_text(display_surf, label, F_SM, C_PARCH2, WIDTH//2, row_y - 25, center=True)
                draw_text(display_surf, val_str, F_MED, C_WHITE, WIDTH//2, row_y + 5, center=True)
                draw_btn(display_surf,"◄",F_MED,C_PARCH,pygame.Rect(WIDTH//2-180,row_y,50,45),C_CYAN)
                draw_btn(display_surf,"►",F_MED,C_PARCH,pygame.Rect(WIDTH//2+130, row_y,50,45),C_CYAN)
            _settings_row("BGM VOLUME", f"{int(audio.bgm_vol*100)}%",   HEIGHT//2-100)
            _settings_row("SFX VOLUME", f"{int(audio.sfx_vol*100)}%",   HEIGHT//2-15)
            _settings_row("RESOLUTION", f"{RESOLUTIONS[curr_res_idx][0]}×{RESOLUTIONS[curr_res_idx][1]}", HEIGHT//2+70)
            _settings_row("FULLSCREEN", "ON" if is_fullscreen else "OFF", HEIGHT//2+155)
            draw_btn(display_surf,"BACK",F_MED,C_PARCH,pygame.Rect(WIDTH//2-200,HEIGHT//2+250,180,55),C_CYAN)
            draw_btn(display_surf,"APPLY",F_MED,C_GOLD, pygame.Rect(WIDTH//2+20, HEIGHT//2+250,180,55),C_GOLD)
            draw_btn(display_surf,"WIPE PROGRESS",F_SM,C_RED,pygame.Rect(WIDTH//2-100,HEIGHT//2+325,200,45),C_WHITE)
        
        elif menu_view=="codex":
            draw_text(display_surf,"CODEX OF RELICS",F_BIG,C_GOLD,WIDTH//2,HEIGHT//6 - 40,center=True)
            relics_list = list(RELIC_DEFS.items())
            cols = 2
            col_w = 700
            start_x = WIDTH//2 - (cols * col_w)//2
            for idx,(rid,d) in enumerate(relics_list):
                col = idx % cols
                row = idx // cols
                box_x = start_x + col * col_w + 30
                box_y = HEIGHT//6 + 40 + row * 110
                
                card = pygame.Rect(box_x, box_y, col_w - 60, 90)
                pygame.draw.rect(display_surf, (16, 12, 22), card, border_radius=8)
                pygame.draw.rect(display_surf, (45, 35, 60), card, 2, border_radius=8)
                
                pygame.draw.circle(display_surf, d["color"], (box_x + 45, box_y + 45), 24, 2)
                ic = F_MED.render(d["icon"], True, d["color"])
                display_surf.blit(ic, (box_x + 45 - ic.get_width()//2, box_y + 45 - ic.get_height()//2))
                
                draw_text(display_surf, d["name"], F_SM, d["color"], box_x + 90, box_y + 20, center=False)
                draw_text(display_surf, d["desc"], F_TINY, C_GREY, box_x + 90, box_y + 50, center=False)
            
            draw_btn(display_surf,"BACK",F_MED,C_PARCH,pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55),C_CYAN)

    elif STATE=="paused":
        draw_game()
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,175)); display_surf.blit(ov,(0,0))
        if menu_view=="pause_main":
            draw_text(display_surf,"PAUSED",F_BIG,C_GOLD,WIDTH//2,HEIGHT//4-40,center=True)
            for i,(lbl,col) in enumerate([("RESUME",C_PARCH),("INVENTORY",C_PARCH),("SETTINGS",C_PARCH),("MAIN MENU",C_PARCH),("QUIT",C_RED)]):
                draw_btn(display_surf,lbl,F_MED,col,menu_btn(i,5),C_CYAN if col==C_PARCH else C_RED)
                
        elif menu_view=="inventory":
            draw_text(display_surf,"INVENTORY",F_BIG,C_GOLD,WIDTH//2,HEIGHT//6,center=True)
            draw_text(display_surf,f"✦ {meta['divine_essence']}  DIVINE ESSENCE",F_MED,C_CYAN,WIDTH//2,HEIGHT//6+60,center=True)
            
            draw_text(display_surf,"COLLECTED RELICS:",F_SM,C_PARCH2,WIDTH//2,HEIGHT//6+130,center=True)
            
            if not run["relics"]:
                draw_text(display_surf,"No relics obtained this run.",F_SM,C_GREY,WIDTH//2,HEIGHT//6+180,center=True)
            else:
                for i,rid in enumerate(run["relics"]):
                    d = RELIC_DEFS[rid]
                    ry = HEIGHT//6 + 180 + i * 50
                    draw_text(display_surf,f"{d['icon']} {d['name']} — {d['desc']}",F_SM,d["color"],WIDTH//2,ry,center=True)
                    
            draw_btn(display_surf,"BACK",F_MED,C_PARCH,pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55),C_CYAN)
            
        elif menu_view=="settings":
            draw_text(display_surf,"SETTINGS",F_BIG,C_GOLD,WIDTH//2,HEIGHT//4,center=True)
            def _settings_row(label, val_str, row_y):
                draw_text(display_surf, label, F_SM, C_PARCH2, WIDTH//2, row_y - 25, center=True)
                draw_text(display_surf, val_str, F_MED, C_WHITE, WIDTH//2, row_y + 5, center=True)
                draw_btn(display_surf,"◄",F_MED,C_PARCH,pygame.Rect(WIDTH//2-180,row_y,50,45),C_CYAN)
                draw_btn(display_surf,"►",F_MED,C_PARCH,pygame.Rect(WIDTH//2+130, row_y,50,45),C_CYAN)
            _settings_row("BGM VOLUME", f"{int(audio.bgm_vol*100)}%",   HEIGHT//2-100)
            _settings_row("SFX VOLUME", f"{int(audio.sfx_vol*100)}%",   HEIGHT//2-15)
            _settings_row("RESOLUTION", f"{RESOLUTIONS[curr_res_idx][0]}×{RESOLUTIONS[curr_res_idx][1]}", HEIGHT//2+70)
            _settings_row("FULLSCREEN", "ON" if is_fullscreen else "OFF", HEIGHT//2+155)
            draw_btn(display_surf,"BACK",F_MED,C_PARCH,pygame.Rect(WIDTH//2-200,HEIGHT//2+250,180,55),C_CYAN)
            draw_btn(display_surf,"APPLY",F_MED,C_GOLD, pygame.Rect(WIDTH//2+20, HEIGHT//2+250,180,55),C_GOLD)
            draw_btn(display_surf,"WIPE PROGRESS",F_SM,C_RED,pygame.Rect(WIDTH//2-100,HEIGHT//2+325,200,45),C_WHITE)
            
        elif menu_view=="sanctum_shop":
            draw_text(display_surf,"THE SANCTUM — SPEND YOUR ESSENCE",F_BIG,C_GOLD,WIDTH//2,HEIGHT//4-45,center=True)
            draw_text(display_surf,f"✦ {meta['divine_essence']}  DIVINE ESSENCE",F_MED,C_CYAN,WIDTH//2,HEIGHT//4+15,center=True)
            cost_hp=20; cost_dash=18; cost_dj=35; cost_blink=40; cost_ult=60; cost_parry=25; cost_relic=30
            shop_items=[
                (f"+1 MAX HP  ◆{cost_hp}  [current: {meta['upg_max_hp']}]",  cost_hp,  True,         C_RED),
                (f"FASTER DASH  ◆{cost_dash}  [cd: {meta['upg_dash_cd']}]",  cost_dash,meta["upg_dash_cd"]>35, C_CYAN),
                (f"DOUBLE JUMP  ◆{cost_dj}"+(" [OWNED]" if meta["upg_double_jump"] else ""),   cost_dj,  not meta["upg_double_jump"], C_PURPLE),
                (f"VOID BLINK  ◆{cost_blink}"+(" [OWNED]" if meta["upg_blink"] else ""),      cost_blink,not meta["upg_blink"],       C_RUNEGLOW),
                (f"SOUL REND ULT  ◆{cost_ult}"+(" [OWNED]" if meta["upg_ult"] else ""),        cost_ult, not meta["upg_ult"],          C_RED),
                (f"WIDER PARRY  ◆{cost_parry}  [win: {meta['upg_parry_window']}]",             cost_parry,meta["upg_parry_window"]<22, C_GOLD),
                (f"+1 RELIC SLOT  ◆{cost_relic}  [slots: {meta['upg_relic_slots']}]",          cost_relic,meta["upg_relic_slots"]<5,   C_PLAGUE),
            ]
            for bi,(lbl,cost,avail,col) in enumerate(shop_items):
                r=menu_btn(bi,len(shop_items),500,55)
                can=(avail and meta["divine_essence"]>=cost)
                draw_btn(display_surf,lbl,F_SM,col,r,col if can else None,disabled=not can)
            back=pygame.Rect(WIDTH//2-100,HEIGHT-80,200,50)
            draw_btn(display_surf,"LEAVE",F_MED,C_PARCH,back,C_CYAN)

    elif STATE in ("game","sanctum"):
        if hit_stop_timer>0:
            hit_stop_timer=max(0.0,hit_stop_timer-dt_mult)
        else:
            if bullet_time_timer>0:
                bullet_time_timer-=1
                if bullet_time_timer<=0: time_scale=1.0
            edt=dt_mult*time_scale

            for m in motes: m.update(edt)
            for t in torches: t.update(edt)

            for e in enemies:
                if hasattr(e,'update'):
                    if isinstance(e,(Grunt,Bulwark)): e.update(player,platforms,edt)
                    elif isinstance(e,Wraith): e.update(player,platforms,edt)
                    elif isinstance(e,Seraph): e.update(player,edt)
            enemies[:] = [e for e in enemies if e.alive]

            if boss_obj: boss_obj.update(player,edt)

            keys=pygame.key.get_pressed()
            if player and player.alive:
                player.update(keys,int(camera_x),dt_mult)
                plists=[e.projs for e in enemies]+([boss_obj.projs] if boss_obj else [])
                player.try_parry(plists)

            for p in player_projs: p.update(player,dt_mult)
            player_projs[:] = [p for p in player_projs if p.alive]

            for d in essence_drops: d.update(player,dt_mult)
            essence_drops[:] = [d for d in essence_drops if not d.collected and d.life>0]

            for r in relic_pickups: r.update(player,dt_mult)
            relic_pickups[:] = [r for r in relic_pickups if r.alive]

            for vt in void_tears: vt.update(edt)
            void_tears[:] = [vt for vt in void_tears if vt.alive]
            update_particles(edt)
            update_dmg_numbers(edt)
            if STATE == "game": floor_time_s += raw_dt / 1000.0

            # Update env objects (healing shrines, etc.)
            for eo in env_objects: eo.update(player, edt)
            env_objects[:] = [eo for eo in env_objects if eo.alive]

            # DOOR LOGIC FIX
            all_alive = [e for e in enemies if e.alive]
            for d in doors:
                d.update(edt)
                if d.locked and len(all_alive)==0 and (not boss_obj or not boss_obj.alive):
                    d.unlock()
            
            # FIX: block door transitions if the player is dead — death screen takes priority
            if player and player.alive and len(all_alive)==0 and (not boss_obj or not boss_obj.alive):
                if any(not d.locked for d in doors):
                    if getattr(build_floor, '_announced', None) != run["floor"]:
                        build_floor._announced = run["floor"]
                        if meta["bosses_defeated"] > 0:
                            announce("PATH CLEARED — PROCEED  •  OR VISIT THE INEVITABLE",C_CYAN,150)
                        else:
                            announce("PATH CLEARED — PROCEED",C_CYAN,150)
                        # Visual flourish: burst of particles from the player on room clear
                        if player:
                            spawn_particles(player.rect.centerx, player.rect.centery, 38,
                                            [C_CYAN, C_RUNEGLOW, C_WHITE, C_PURPLE],
                                            speed=6, gravity=-0.08, sz=(2,7), life=(18,45))
                            screen_shake = max(screen_shake, 5)
                
                # Check ALL doors to see if any are fully open
                door_triggered = None
                for d in doors:
                    if d.is_open:
                        door_triggered = d
                        break
                
                if door_triggered:
                    tgt = door_triggered.target
                    door_triggered.is_open = False
                    door_triggered.opening = False
                    door_triggered.open_t = 0
                    transition_t = 28               # ~0.45s black fade-in on every transition
                    
                    if tgt.startswith("floor"):
                        fl=int(tgt.replace("floor","")); run["floor"]=fl
                        floor_time_s = 0.0
                        player.pos.x=200; player.rect.x=200
                        player.pos.y=GROUND_Y-80; player.rect.y=int(player.pos.y)
                        camera_x=0.0; build_floor(fl); STATE="game"
                    elif tgt=="boss_room":
                        run["floor"]=4
                        floor_time_s = 0.0
                        player.pos.x=200; player.rect.x=200
                        player.pos.y=GROUND_Y-80; player.rect.y=int(player.pos.y)
                        camera_x=0.0; build_boss_room(); STATE="game"
                    elif tgt=="new_run": start_new_run()
                    elif tgt=="sanctum_midrun":
                        run["sanctum_return_floor"] = run["floor"]
                        player.pos.x=200; player.rect.x=200
                        player.pos.y=GROUND_Y-80; player.rect.y=int(player.pos.y)
                        camera_x=0.0; build_sanctum(midrun=True); STATE="sanctum"
                        announce("THE INEVITABLE AWAITS — YOUR JOURNEY PAUSES HERE", C_RUNEGLOW, 160)
                    elif tgt=="sanctum_enter":
                        player.pos.x=200; player.rect.x=200
                        player.pos.y=GROUND_Y-80; player.rect.y=int(player.pos.y)
                        camera_x=0.0; build_sanctum(); STATE="sanctum"
                    elif tgt=="return_to_floor":
                        fl = run.get("sanctum_return_floor") or 1
                        run["floor"] = fl; run["sanctum_return_floor"] = None
                        player.pos.x=200; player.rect.x=200
                        player.pos.y=GROUND_Y-80; player.rect.y=int(player.pos.y)
                        camera_x=0.0
                        build_floor(fl)
                        # Floor was already cleared before visiting the sanctum —
                        # wipe enemies so the player doesn't have to fight again.
                        enemies.clear()
                        # Unlock the exit door immediately since all enemies are gone
                        for d in doors:
                            if d.locked: d.unlock()
                        build_floor._announced = fl   # suppress duplicate "PATH CLEARED" message
                        STATE="game"
                        announce(f"RETURNING TO FLOOR {fl} — PRESS ONWARD", C_CYAN, 160)

            if boss_obj and not boss_obj.alive and boss_obj.death_t<=0:
                if not any(d.target=="sanctum_enter" for d in doors):
                    vd=Door(2600, GROUND_Y-170, C_GOLD,"ENTER SANCTUM [E]","sanctum_enter")
                    vd.locked=False; doors.append(vd)
                    announce("SOVEREIGN AETHERIA SLAIN — THE SANCTUM OPENS",C_GOLD,220); audio.bgm("bgm_explore",audio.bgm_vol)

            if combo_timer>0:
                combo_timer-=dt_mult
                if combo_timer<=0: combo_count=0

            for ann in announce_queue: ann[2]-=dt_mult
            announce_queue[:] = [a for a in announce_queue if a[2]>0]

            if player: camera_x+=(player.rect.centerx-camera_x-WIDTH//2)/10; camera_x=max(0,camera_x)

            hbs=audio.sounds.get("heartbeat")
            if hbs:
                if player and player.alive and player.hp<=1 and not _hb_playing:
                    _hb_playing=True; audio.ch_hb.play(hbs,loops=-1); audio.ch_hb.set_volume(0.6)
                elif (not player or not player.alive or player.hp>1) and _hb_playing:
                    _hb_playing=False; audio.ch_hb.stop()

            if screen_shake>0: screen_shake-=1
            if hit_flash_t>0: hit_flash_t-=1

        draw_game()

        if STATE=="sanctum":
            npc_x=800-int(camera_x); npc_y=GROUND_Y-160
            if _NPC_IMG:
                display_surf.blit(_NPC_IMG, (npc_x - _NPC_IMG.get_width()//2 + 40, npc_y - _NPC_IMG.get_height() + 100))
            else:
                ns=pygame.Surface((80,100),pygame.SRCALPHA)
                pygame.draw.ellipse(ns,(*C_RUNEGLOW,180),(15,15,50,70))
                pygame.draw.circle(ns,(*C_RUNEGLOW,220),(40,14),12)
                pygame.draw.circle(ns,(240,235,255,255),(36,12),2); pygame.draw.circle(ns,(240,235,255,255),(44,12),2)
                display_surf.blit(ns,(npc_x,npc_y))
                
            lb=F_SM.render("THE INEVITABLE [E]",True,C_RUNEGLOW); display_surf.blit(lb,(npc_x+40-lb.get_width()//2,npc_y-22))
            if player and pygame.Rect(800,GROUND_Y-160,80,100).colliderect(player.rect):
                ht=F_SM.render("Press E to open Sanctum",True,C_RUNEGLOW); display_surf.blit(ht,(WIDTH//2-ht.get_width()//2,HEIGHT//2-80))

    # ── floor transition fade (drawn last, over everything in display_surf)
    if transition_t > 0:
        a = int(255 * min(1.0, transition_t / 28))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((0,0,0,a))
        display_surf.blit(ov, (0,0))
        transition_t = max(0, transition_t - 1)

    scaled=pygame.transform.scale(display_surf,(WINDOW_W,WINDOW_H))
    if screen_shake>0: screen.blit(scaled,(random.randint(-screen_shake,screen_shake), random.randint(-screen_shake,screen_shake)))
    else: screen.blit(scaled,(0,0))
    pygame.display.flip()
