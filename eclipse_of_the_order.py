"""
ECLIPSE OF THE ORDER — v1.0
─────────────────────────────────────────────
CONTROLS:
  Customizable in the Keybinds Menu (Keyboard & Gamepad supported)
  Gamepad Defaults: A=Jump, B=Bolt, X=Flask, Y=Attack, LB=Parry, RB=Dash, LT=Blink, RT=Ult
  LMB                 — Attack (Fallback)
  RMB                 — Instant Parry (Scythe Block)
  P / ESC / START     — Pause
  F11                 — Toggle Fullscreen
"""

import pygame, sys, math, random, os, json

# ==========================================
# STORY & DIALOGUE STRINGS
# ==========================================
STORY_DIALOGUE = {
    "floor_1_start": "FLOOR {floor}  — {entities} ENTITIES DETECTED",
    "path_cleared": "PATH CLEARED — PROCEED",
    "path_cleared_sanctum": "PATH CLEARED — PROCEED • OR VISIT THE INEVITABLE",
    "sanctum_welcome": "THE INEVITABLE: 'Welcome to the Sanctum. Equip Talismans & spend essence.'",
    "sanctum_midrun": "THE INEVITABLE: 'Prepare for Floor {next_f}, Executioner.'",
    "sanctum_boss_ready": "THE INEVITABLE: 'The Sovereign awaits. Claim your destiny.'",
    "sanctum_master_mode": "THE INEVITABLE: 'Master Mode awaits... The curse deepens to Level {curse}.'",
    "boss_greet": "AETHERIA: 'You dare to challenge me, Reaper?'",
    "boss_p2": "AETHERIA: 'The keys to your demise are scattered!'",
    "boss_p3": "AETHERIA: 'I AM THE DIVINE! KNEEL!'",
    "boss_keys_found": "ALL KEYS — STRIKE NOW!",
    "aetheria_death": "AETHERIA SLAIN — THE SANCTUM OPENS",
    "inevitable_prompt": "Press {key} to speak with The Inevitable",
    "training_welcome": "TRAINING GROUNDS — TEST YOUR ARSENAL"
}

def asset(filename):
    if getattr(sys, 'frozen', False): base = sys._MEIPASS
    else:
        try: base = os.path.dirname(os.path.abspath(__file__))
        except NameError: base = os.path.abspath(".")
    return os.path.join(base, "assets", filename)

pygame.init()
pygame.mixer.set_num_channels(32)
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for joy in joysticks: joy.init()

WIDTH, HEIGHT = 1920, 1080
RESOLUTIONS = [(1280, 720), (1366, 768), (1600, 900), (1920, 1080), (1920, 1200), (2560, 1440), (2560, 1600), (3840, 2160)]
curr_res_idx = 3
WINDOW_W, WINDOW_H = RESOLUTIONS[curr_res_idx]

is_fullscreen = False
flags = pygame.FULLSCREEN if is_fullscreen else 0
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)
display_surf = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("Eclipse of the Order")
clock = pygame.time.Clock()

def get_mouse_pos(cam_x=0, cam_y=0):
    mx, my = pygame.mouse.get_pos()
    sw, sh = screen.get_size()
    if sw <= 0 or sh <= 0: sw, sh = WINDOW_W, WINDOW_H
    return (mx * WIDTH / sw) + cam_x, (my * HEIGHT / sh) + cam_y

BG=(4,2,10); C_VOID=(20,0,45); C_STONE=(48,42,58); C_STONE2=(68,60,80); C_PARCH=(205,190,155)
C_PARCH2=(165,145,108); C_SEPIA=(115,85,45); C_RUNEGLOW=(175,115,255); C_WHITE=(238,232,255)
C_RED=(195,35,35); C_DKRED=(88,8,8); C_ORANGE=(255,138,0); C_YELLOW=(252,218,0)
C_CYAN=(75,215,252); C_PURPLE=(155,55,252); C_GREY=(75,75,88); C_GOLD=(252,212,0)
C_HOLY=(252,242,175); C_PLAGUE=(60,200,80); C_BLOOD=(155,0,25); C_SILVER=(180,180,200)

F_TITLE = pygame.font.SysFont("couriernew", 78, bold=True)
F_BIG   = pygame.font.SysFont("couriernew", 57, bold=True)
F_MED   = pygame.font.SysFont("couriernew", 30, bold=True)
F_SM    = pygame.font.SysFont("couriernew", 20, bold=True)
F_TINY  = pygame.font.SysFont("couriernew", 16)

STATE = "main_menu"; menu_view = "main"; PREV_STATE = "main_menu"; binding_action = None
player = None; platforms = []; enemies = []; player_projs = []; env_objects = []; camera_x = 0.0; menu_cam_x = 0.0
hit_stop_timer = 0.0; time_scale = 1.0; bullet_time_timer = 0; screen_shake = 0; transition_t = 0
combo_count = 0; combo_timer = 0; COMBO_WINDOW = 200; kill_streak = 0; kill_streak_best = 0; floor_time_s = 0.0
announce_queue = []; _hb_playing = False; parry_sparks = []; parry_rings = []
abyssal_tears = []

# Gamepad Menu Navigation Globals
current_menu_rects = []
pad_menu_idx = 0
pad_menu_cooldown = 0
using_gamepad = False
_held_keys = {}  # Manual key state tracking (immune to focus loss from gamepad)

# Per-frame "just pressed" flags for actions — set in event loop, consumed in draw/update
_frame_interact_pressed = False
_frame_jump_pressed = False

META_DEFAULTS = {
    "divine_essence":0, "total_runs":0, "bosses_defeated":0, "total_kills":0, "best_combo":0, "best_floor":0, "total_parries":0, 
    "upg_max_hp":5, "upg_dash_cd":90, "upg_double_jump":False, "upg_blink":False, "upg_ult":False, "upg_parry_window":14, "upg_relic_slots":2, 
    "curse_level":0, "reforge_bonus":0, "fullscreen":False, "run_history":[], "resolution_idx": 3,
    "bgm_vol": 0.35, "sfx_vol": 0.9,
    "binds": {
        "left": pygame.K_a, "right": pygame.K_d, "up": pygame.K_w, "down": pygame.K_s, 
        "jump": pygame.K_SPACE, "dash": pygame.K_LSHIFT, "atk": pygame.K_f, "bolt": pygame.K_g, 
        "blink": pygame.K_q, "ult": pygame.K_c, "flask": pygame.K_r, "stance": pygame.K_v, 
        "interact": pygame.K_e, "trinket": pygame.K_t, "cleave": pygame.K_x
    },
    "pad_binds": {
        "jump": 0, "bolt": 1, "flask": 2, "atk": 3, 
        "parry": 4, "dash": 5, "blink": "LT", "ult": "RT", 
        "interact": 0, "trinket": 8, "cleave": 9,
        "stance": 10, "start": 7
    }
}
meta = dict(META_DEFAULTS)
meta["binds"] = dict(META_DEFAULTS["binds"])
meta["pad_binds"] = dict(META_DEFAULTS["pad_binds"])

def key_pressed(keys, action):
    """Safely read a bind from the keys list, returning False for out-of-range codes."""
    code = meta["binds"].get(action, -1)
    if 0 <= code < len(keys): return bool(keys[code])
    return bool(_held_keys.get(code, False))  # fallback for high keycodes like K_LSHIFT

def safe_key(keys, keycode):
    """Safely check a raw pygame keycode, returning False if out of range."""
    return bool(keys[keycode]) if 0 <= keycode < len(keys) else False

try:
    if getattr(sys, 'frozen', False): _SAVE_DIR = os.path.dirname(sys.executable)
    else: _SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: _SAVE_DIR = os.path.abspath(".")
SAVE_PATH = os.path.join(_SAVE_DIR, "eclipse_save.json"); _save_flash_t = 0

def save_meta():
    global _save_flash_t
    try:
        tmp = SAVE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(meta, f, indent=2)
        os.replace(tmp, SAVE_PATH); _save_flash_t = 80
    except Exception: pass

def load_meta():
    if not os.path.exists(SAVE_PATH): return
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f: data = json.load(f)
        if isinstance(data, dict):
            for k, v in data.items():
                if k == "binds" and isinstance(v, dict):
                    # Only load binds that are valid integer keycodes
                    for action, keycode in v.items():
                        if action in meta["binds"] and isinstance(keycode, int) and 0 <= keycode < 1073742367:
                            meta["binds"][action] = keycode
                elif k == "pad_binds" and isinstance(v, dict):
                    meta[k].update(v)
                elif k in META_DEFAULTS and type(v) is type(META_DEFAULTS[k]): 
                    meta[k] = v
    except Exception: pass

load_meta()
# Sanity-check: if core movement keys are missing or out of valid range, reset binds to defaults
_core_actions = ("left", "right", "jump", "dash", "atk")
if any(not isinstance(meta["binds"].get(a), int) or meta["binds"].get(a, -1) > 512
       for a in _core_actions if a != "dash"):
    meta["binds"] = dict(META_DEFAULTS["binds"])
is_fullscreen = meta.get("fullscreen", False)
_info = pygame.display.Info()
_native_w, _native_h = _info.current_w, _info.current_h
if "resolution_idx" in meta:
    curr_res_idx = max(0, min(int(meta["resolution_idx"]), len(RESOLUTIONS)-1))
    if RESOLUTIONS[curr_res_idx][0] > _native_w or RESOLUTIONS[curr_res_idx][1] > _native_h:
        curr_res_idx = min(range(len(RESOLUTIONS)), key=lambda i: abs(RESOLUTIONS[i][0]-_native_w)+abs(RESOLUTIONS[i][1]-_native_h))
        meta["resolution_idx"] = curr_res_idx
else:
    curr_res_idx = min(range(len(RESOLUTIONS)), key=lambda i: abs(RESOLUTIONS[i][0]-_native_w)+abs(RESOLUTIONS[i][1]-_native_h))
    meta["resolution_idx"] = curr_res_idx
WINDOW_W, WINDOW_H = RESOLUTIONS[curr_res_idx]
flags = pygame.FULLSCREEN if is_fullscreen else 0; screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)

FLOOR_CURSES = {"none":{"name":"Blessed Path","desc":"No modifier","color":C_CYAN,"hostile":False},"haste":{"name":"Enemy Haste","desc":"Enemies move 50% faster","color":C_RED,"hostile":True},"bulwark_tide":{"name":"Bulwark Tide","desc":"All grunts are bulwarks","color":C_GOLD,"hostile":True},"wraith_storm":{"name":"Wraith Storm","desc":"Wraiths are everywhere","color":C_PURPLE,"hostile":True},"mana_drain":{"name":"Mana Drain","desc":"Mana regen -70%","color":C_CYAN,"hostile":True},"double_drops":{"name":"Gilded Floor","desc":"Essence drops ×2","color":C_GOLD,"hostile":False},"elite_surge":{"name":"Elite Surge","desc":"Elites drop bonus relic","color":C_RUNEGLOW,"hostile":False},"bloodlust":{"name":"Bloodlust","desc":"Kill restores ½HP (1 time)","color":C_RED,"hostile":False},"iron_curse":{"name":"Iron Curse","desc":"You start at ½ HP","color":C_DKRED,"hostile":True},"parry_boon":{"name":"Parry Boon","desc":"Parries restore full mana","color":C_SILVER,"hostile":False},"darkness":{"name":"Encroaching Dark","desc":"Reduced vision radius","color":(30,30,50),"hostile":True}}
current_floor_curse = "none"

def pick_floor_curse(floor_num, rng):
    global current_floor_curse
    if floor_num == 1: current_floor_curse = "none"; return
    pool = list(FLOOR_CURSES.keys()); hostile = [k for k in pool if FLOOR_CURSES[k]["hostile"]]; benign = [k for k in pool if not FLOOR_CURSES[k]["hostile"]]
    current_floor_curse = rng.choice(hostile) if rng.random() < 0.55 + floor_num * 0.05 else rng.choice(benign)

def curse_active(name): return current_floor_curse == name

# ==========================================
# LORE AND ITEM DEFINITIONS
# ==========================================
TRINKET_DEFS = {
    "time_shard": {"name":"Time Shard", "desc":"Bullet time 5 sec", "lore":"A crystallized moment from a dying star.", "color":C_CYAN, "icon":"◈"},
    "soul_bomb":  {"name":"Soul Bomb", "desc":"Kill all weak enemies", "lore":"Compressed agony. Handle with care.", "color":C_PURPLE, "icon":"✺"},
    "essence_jar":{"name":"Essence Jar", "desc":"+30 essence", "lore":"Greed incarnate, sealed in glass.", "color":C_GOLD, "icon":"○"},
    "relic_shard":{"name":"Relic Shard", "desc":"Random relic effect", "lore":"A broken piece of a forgotten god's armory.", "color":C_RUNEGLOW, "icon":"◆"}
}
player_trinket = None

RELIC_DEFS = {
    "void_heart":    {"name":"Void Heart", "desc":"+2 Max HP this run", "lore":"Carved from the chest of a fallen Void-Walker. It beats still.", "color":C_BLOOD, "icon":"♥"},
    "obsidian_edge": {"name":"Obsidian Edge", "desc":"Attacks deal +1 dmg", "lore":"Ground from the eye-tooth of a dead god. Nothing withstands its edge.", "color":C_GREY, "icon":"◆"},
    "swiftness":     {"name":"Wraith's Grace", "desc":"Dash has 2 charges", "lore":"Stolen from a Wraith mid-vanish. It smells of cold graves.", "color":C_CYAN, "icon":"»"},
    "soulsucker":    {"name":"Soul Siphon", "desc":"Kills restore 1 HP", "lore":"A hollow needle that drinks what the dying no longer need.", "color":C_PURPLE, "icon":"★"},
    "thorn_mantle":  {"name":"Thorn Mantle", "desc":"Parry stuns melee enemies", "lore":"Woven from barbed roots that hunger for blood.", "color":C_PLAGUE, "icon":"✦"},
    "void_echo":     {"name":"Void Echo", "desc":"Blink damages in radius", "lore":"Your passage tears external fabric. The void remembers.", "color":C_RUNEGLOW, "icon":"◉"},
    "cursed_blade":  {"name":"Cursed Blade", "desc":"+50% dmg, -1 max hp", "lore":"It whispers promises. The cost is always flesh.", "color":C_RED, "icon":"†"},
    "gilded_soul":   {"name":"Gilded Soul", "desc":"+25% essence gain", "lore":"A merchant's soul, pressed into coin. Greed outlasts the body.", "color":C_GOLD, "icon":"⊕"},
    "iron_will":     {"name":"Iron Will", "desc":"First lethal hit → 1 hp", "lore":"The Order's last vow: not yet. Not today. Not ever.", "color":C_WHITE, "icon":"⊗"},
    "plague_touch":  {"name":"Plague Touch", "desc":"Attacks poison enemies", "lore":"A vial of the Black Bloom. One drop ends dynasties.", "color":C_PLAGUE, "icon":"⚗"},
    "parry_master":  {"name":"Parry Master", "desc":"Parry heals 1 HP every 3", "lore":"To turn the blade is to drink from it.", "color":C_SILVER, "icon":"⚔"},
    "momentum_stone":{"name":"Momentum Stone", "desc":"High combo → +dmg", "lore":"Ancient war-relic. It grows heavier with each kill.", "color":C_ORANGE, "icon":"◎"}
}

TALISMAN_DEFS = {
    "phantom":    {"name": "Talisman of the Phantom", "short": "PHANTOM", "desc": "Dash becomes a teleport through enemies, leaving a void tear that deals 3 dmg (+50% CD)", "lore": "They say the first Phantom stepped through a dying star. He never stepped back out.", "color": C_PURPLE, "icon": "◈"},
    "bloodpact":  {"name": "Talisman of the Blood Pact", "short": "BLOODPACT", "desc": "You deal +2 dmg but lose 1 HP every 15 seconds. Kills fully reset the timer.", "lore": "Signed in a language with no word for mercy. The ink was not ink.", "color": C_BLOOD, "icon": "†"},
    "eclipse":    {"name": "Talisman of the Eclipse", "short": "ECLIPSE", "desc": "After 5 consecutive hits without being struck, your next attack stuns any enemy instantly.", "lore": "When the sun was devoured, the survivors learned to strike in perfect darkness.", "color": C_GOLD, "icon": "◉"},
    "voidwarden": {"name": "Talisman of the Void Warden", "short": "VOIDWARDEN", "desc": "Parrying restores 8 mana AND slows all enemies 40% for 2 seconds.", "lore": "A sentinel who holds the gate between worlds. Its patience is absolute. Its grip, eternal.", "color": C_CYAN, "icon": "⊗"},
    "runebound":  {"name": "Talisman of the Runebound", "short": "RUNEBOUND", "desc": "Bolt shots cost no mana. Every 4th bolt fired is a homing runic bolt dealing double damage.", "lore": "The runes were carved by someone who had already forgotten their own name.", "color": C_RUNEGLOW, "icon": "✺"}
}

SANCTUM_SHOP_ITEMS = [
    ("upg_max_hp", "+1 MAX HP", 20, C_RED, "Permanently increase maximum health by 1.", "Vitality drained from a lesser deity. It warms the blood."),
    ("upg_dash_cd", "FASTER DASH", 18, C_CYAN, "Reduce dash cooldown by 5 frames.", "The wind's whisper trapped in a glass bottle."),
    ("upg_double_jump", "DOUBLE JUMP", 35, C_PURPLE, "Leap a second time in mid-air.", "Defy gravity. Defy the Order. Ascend."),
    ("upg_blink", "VOID BLINK", 40, C_RUNEGLOW, "Teleport instantly to your cursor.", "Space is merely a suggestion to the Abyss."),
    ("upg_ult", "SOUL REND ULT", 60, C_RED, "Unlock the Soul Rend ultimate ability.", "A devastation technique forbidden by the elders."),
    ("upg_parry_window", "WIDER PARRY", 25, C_SILVER, "Increase parry active frames by 2.", "A charm that slows down time in the critical moment."),
    ("upg_relic_slots", "+1 RELIC SLOT", 30, C_PLAGUE, "Carry one additional relic.", "Sew an extra dimensional pocket into your cloak."),
    ("reforge", "REFORGE SCYTHE (+1 DMG)", 50, C_DKRED, "Increase base attack damage by 1.", "Bathe your blade in the blood of the fallen.")
]

MERCHANT_SHOP_ITEMS = [
    ("flasks", "REFILL FLASKS", 30, C_RED, "Restores all your healing flasks.", "A crimson brew that tastes of iron and ash."),
    ("max_hp", "+1 MAX HP", 80, C_GOLD, "Permanently increases your maximum health.", "A crystallized shard of a martyr's soul."),
    ("ult", "CHARGE ULTIMATE", 40, C_PURPLE, "Fully resets your Soul Rend cooldown.", "Swirling ether that hums with destructive potential.")
]

active_talismans = []
def talisman_active(key): return key in active_talismans
def equip_talisman(key):
    if key in active_talismans:
        active_talismans.remove(key)
    elif len(active_talismans) < 2:
        active_talismans.append(key)
    else:
        active_talismans[0] = key

_talisman_bloodpact_timer = 0.0
_talisman_eclipse_hits    = 0
_talisman_eclipse_ready   = False
_talisman_runebound_count = 0
_talisman_slow_timer      = 0.0

def _tick_talismans(dt):
    global _talisman_bloodpact_timer, _talisman_slow_timer
    if talisman_active("bloodpact") and player and player.alive:
        _talisman_bloodpact_timer += dt
        if _talisman_bloodpact_timer >= 900:
            _talisman_bloodpact_timer = 0.0
            if player.hp > 1:
                player.hp -= 1
                spawn_particles(player.rect.centerx, player.rect.centery, 10, [C_BLOOD, C_RED], speed=4, gravity=0.05, sz=(2,5), life=(10,25))
                announce("BLOOD PACT — HP DRAINED", C_BLOOD, 70)
    if _talisman_slow_timer > 0:
        _talisman_slow_timer -= dt

def _talisman_on_player_hit():
    global _talisman_eclipse_hits, _talisman_eclipse_ready
    if talisman_active("eclipse"):
        _talisman_eclipse_hits  = 0
        _talisman_eclipse_ready = False

def _talisman_on_player_hit_enemy(target=None):
    global _talisman_eclipse_hits, _talisman_eclipse_ready
    if not talisman_active("eclipse"): return False
    if _talisman_eclipse_ready:
        _talisman_eclipse_ready = False
        _talisman_eclipse_hits  = 0
        return True
    _talisman_eclipse_hits += 1
    if _talisman_eclipse_hits >= 5:
        _talisman_eclipse_hits  = 0
        _talisman_eclipse_ready = True
        announce("ECLIPSE — NEXT STRIKE STUNS!", C_GOLD, 100)
    return False

def _talisman_bloodpact_kill_reset():
    global _talisman_bloodpact_timer
    if talisman_active("bloodpact"):
        _talisman_bloodpact_timer = 0.0

def _talisman_voidwarden_on_parry():
    global _talisman_slow_timer
    if talisman_active("voidwarden"):
        _talisman_slow_timer = 120

def talisman_slow_active(): return _talisman_slow_timer > 0

run = {"floor":1, "kills":0, "relics":[], "relic_offered":[], "curse_active":False, "iron_will_used":False, "double_jump_used":False, "sanctum_return_floor":None, "parries_this_run":0, "trinket":None, "flasks": 3, "floor_curse_shown":False, "parry_heal_counter":0, "treasure_rooms_found":0, "wraiths_killed":0, "slayer_spawned":False}

def run_has(relic): return relic in run["relics"]
def run_atk_bonus(): return (1 if run_has("obsidian_edge") else 0) + (1 if run_has("momentum_stone") and combo_count >= 10 else 0) + meta.get("reforge_bonus", 0)
def run_dmg_mult(): return 1.5 if run_has("cursed_blade") else 1.0
def run_hp_bonus(): return (2 if run_has("void_heart") else 0) - (1 if run_has("cursed_blade") else 0)
def run_essence_mult(): return (1.25 if run_has("gilded_soul") else 1.0) * (2.0 if curse_active("double_drops") else 1.0)
def get_diff(): return (0.4 if meta["bosses_defeated"]==0 else 0.8+(meta["bosses_defeated"]*0.05)) + ((run.get("floor",1)-1)*0.1) + (meta["curse_level"]*0.2)

class AudioManager:
    def __init__(self):
        self.sounds = {}; self.ch_bgm = pygame.mixer.Channel(0); self.ch_hb = pygame.mixer.Channel(1); self.sfx_vol = 0.9; self.bgm_vol = 0.35
    def load(self, name, path):
        try: self.sounds[name] = pygame.mixer.Sound(path)
        except: self.sounds[name] = None
    def play(self, name, vol=0.5):
        s = self.sounds.get(name)
        if s: s.set_volume(vol * self.sfx_vol); pygame.mixer.find_channel(True).play(s)
    def stop(self, name):
        s = self.sounds.get(name);
        if s: s.stop()
    def bgm(self, name, vol=None):
        if vol is not None: self.bgm_vol = vol
        s = self.sounds.get(name)
        if s: self.ch_bgm.play(s, loops=-1); self.ch_bgm.set_volume(self.bgm_vol)
    def set_bgm_vol(self, v): self.bgm_vol = max(0.0, min(1.0, v)); self.ch_bgm.set_volume(self.bgm_vol)
    def set_sfx_vol(self, v): self.sfx_vol = max(0.0, min(1.0, v))

audio = AudioManager()
audio.set_bgm_vol(meta.get("bgm_vol", 0.35))
audio.set_sfx_vol(meta.get("sfx_vol", 0.9))

for n, p in [("slash","slash.ogg"),("dash","dash.wav"),("parry","parry.wav"),("hit","hit.wav"),("blink","blink.wav"),("heartbeat","heartbeat.wav"),("bgm_explore","bgm_explore.wav"),("bgm_boss","bgm_boss.wav"),("levelup","levelup.wav"),("relic","relic.wav")]: audio.load(n, asset(p))

def _try_load_image(path):
    try: return pygame.image.load(path).convert_alpha()
    except: return None
def _load_scale(path, height):
    try: img = pygame.image.load(path).convert_alpha(); return pygame.transform.scale(img, (max(1, int(img.get_width() * (height / img.get_height()))), height))
    except: return None
def _load_exact(path, w, h):
    try: return pygame.transform.scale(pygame.image.load(path).convert_alpha(), (w, h))
    except: return None

_SKY_IMG = _try_load_image(asset("sky.png")); _MOON_IMG = _try_load_image(asset("moon.png")); _CASTLES_IMG = _try_load_image(asset("bg_castles.png")); _RUINS_IMG = _try_load_image(asset("mg_ruins.png"))
_NPC_IMG = _load_scale(asset("inevitable.png"), 100)
_RIFT_IMG = _try_load_image(asset("rift.png")) or _try_load_image(asset("portal.png"))
_DUMMY_IMG = _load_scale(asset("dummy.png"), 90)

_PLAYER_H = 78
_PLAYER_FRAMES_R = []
for _i in range(1, 6):
    f = _load_scale(asset(f"run{_i}.png"), _PLAYER_H)
    if f: _PLAYER_FRAMES_R.append(f)
_PLAYER_FRAMES_L = [pygame.transform.flip(f, True, False) for f in _PLAYER_FRAMES_R]

_SLASH_IMG = _load_scale(asset("slash.png"), 80); _SLASH_ULT = _load_scale(asset("slash.png"), 130)
_GRUNT_H = 65
_GRUNT_FRAMES_R = []
for _i in range(1, 6):
    f = _load_scale(asset(f"thug{_i}.png"), _GRUNT_H)
    if f: _GRUNT_FRAMES_R.append(f)
if not _GRUNT_FRAMES_R: _GRUNT_FRAMES_R = [None]
_GRUNT_FRAMES_L = [pygame.transform.flip(f, True, False) if f else None for f in _GRUNT_FRAMES_R]

_SERAPH_IMG_R = _load_scale(asset("seraph.png"), 90); _SERAPH_IMG_L = pygame.transform.flip(_SERAPH_IMG_R, True, False) if _SERAPH_IMG_R else None
_BOSS_H = 180
_BOSS_FRAMES_R = []
for _i in range(1, 6):
    f = _load_scale(asset(f"boss_p1_walk{_i}.png"), _BOSS_H)
    if f: _BOSS_FRAMES_R.append(f)
if not _BOSS_FRAMES_R: _s = pygame.Surface((110,180),pygame.SRCALPHA); _s.fill((200,180,0,180)); _BOSS_FRAMES_R = [_s]
_BOSS_FRAMES_L = [pygame.transform.flip(f, True, False) for f in _BOSS_FRAMES_R]
_PROJ_FIREBALL = _load_exact(asset("proj_fireball.png"), 36, 18); _PROJ_DARKWAVE = _load_exact(asset("proj_darkwave.png"), 70, 34); _DOOR_IDLE = _load_exact(asset("door_idle.png"), 90, 150); _DOOR_OPEN = _load_exact(asset("door_open.png"), 90, 150); _TORCH_IMG = _load_scale(asset("torch.png"), 48)
_ESSENCE_IMG     = _load_scale(asset("essence.png"), 16)
_VOID_TEAR_IMG   = _try_load_image(asset("void_tear.png"))
_CHEST_IMG       = _load_exact(asset("chest.png"), 80, 72)
_CHEST_OPEN_IMG  = _load_exact(asset("chest_open.png"), 80, 72)
_REST_SHRINE_IMG = _load_scale(asset("rest_shrine.png"), 110)
_TALISMAN_STONE_IMG = _load_scale(asset("talisman_stone.png"), 110)
_BLOOD_ALTAR_IMG = _load_scale(asset("blood_altar.png"), 80)
_MERCHANT_IMG    = _load_scale(asset("merchant.png"), 80)
_WRAITH_IMG_R    = _load_scale(asset("wraith.png"), 56)
_WRAITH_IMG_L    = pygame.transform.flip(_WRAITH_IMG_R, True, False) if _WRAITH_IMG_R else None
_CAT_CHAMPA_IMG  = _load_scale(asset("cat_champa.png"), 24)
_CAT_PEPPER_IMG  = _load_scale(asset("cat_pepper.png"), 24)

def spawn_parry_vfx(x, y, facing_r):
    cx = x + (38 if facing_r else -38); cy = y
    parry_rings.append({"x": cx, "y": cy, "r": 8, "max_r": 80, "life": 22, "ml": 22, "col": C_CYAN})
    parry_rings.append({"x": cx, "y": cy, "r": 4, "max_r": 55, "life": 16, "ml": 16, "col": C_WHITE})
    parry_rings.append({"x": cx, "y": cy, "r": 2, "max_r": 40, "life": 12, "ml": 12, "col": C_GOLD})
    for _ in range(22):
        ang = (0.0 if facing_r else math.pi) + random.uniform(-math.pi * 0.65, math.pi * 0.65); spd = random.uniform(4.0, 11.0)
        parry_sparks.append({"x": float(cx), "y": float(cy), "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd - 1.5, "g": 0.45, "life": random.randint(10, 24), "ml": 24, "col": random.choice([C_CYAN, C_WHITE, C_GOLD, C_SILVER]), "sz": random.randint(2, 5)})

def update_parry_vfx(dt):
    for s in parry_sparks: s["x"] += s["vx"]*dt; s["y"] += s["vy"]*dt; s["vy"] += s["g"]*dt; s["life"] -= dt
    parry_sparks[:] = [s for s in parry_sparks if s["life"] > 0]
    for r in parry_rings: r["r"] = r["max_r"] * (1.0 - r["life"]/r["ml"]); r["life"] -= dt
    parry_rings[:] = [r for r in parry_rings if r["life"] > 0]

def draw_parry_vfx(surf, cx):
    for s in parry_sparks:
        sz = max(1, s["sz"]); ps = pygame.Surface((sz*2, sz*2), pygame.SRCALPHA); pygame.draw.circle(ps, (*s["col"], int(255 * s["life"]/s["ml"])), (sz, sz), sz); surf.blit(ps, (int(s["x"]-cx)-sz, int(s["y"])-sz))
    for r in parry_rings:
        radius = max(1, int(r["r"])); rs = pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA); pygame.draw.circle(rs, (*r["col"], int(200 * r["life"]/r["ml"])), (radius+2, radius+2), radius, max(1, int(3*(r["life"]/r["ml"])))); surf.blit(rs, (int(r["x"]-cx)-radius-2, int(r["y"])-radius-2))

def announce(text, color=C_YELLOW, dur=130): announce_queue.append([text, color, dur, dur])
def add_combo(n=1):
    global combo_count, combo_timer; combo_count += n; combo_timer = COMBO_WINDOW
    if combo_count > meta["best_combo"]: meta["best_combo"] = combo_count

def combo_rank():
    if combo_count >= 40: return "S+", C_GOLD
    if combo_count >= 25: return "S",  C_GOLD
    if combo_count >= 15: return "A",  C_PURPLE
    if combo_count >= 8:  return "B",  C_CYAN
    if combo_count >= 4:  return "C",  C_ORANGE
    return "D", C_GREY

def draw_text(surf, text, font, color, x, y, center=False, shadow=True):
    if shadow: sh = font.render(text, True, (0,0,0)); surf.blit(sh, (x - sh.get_width()//2 + 2 if center else x+2, y+2))
    t = font.render(text, True, color); surf.blit(t, (x - t.get_width()//2 if center else x, y))

def draw_text_wrapped(surf, text, font, color, x, y, max_width, center=True):
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line: lines.append(' '.join(current_line))
    for i, line in enumerate(lines):
        draw_text(surf, line, font, color, x, y + i * (font.get_height() + 5), center=center)

def glow(surf, color, cx, cy, r, a=70):
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    for i in range(5): pygame.draw.circle(s, (*color, int(a/5)), (r, r), int(r * (1 - i/5)))
    surf.blit(s, (cx-r, cy-r), special_flags=pygame.BLEND_RGBA_ADD)

def menu_btn(index, total, btn_w=240, btn_h=55, spacing=70):
    start_y = HEIGHT // 2 - 170
    x = WIDTH // 2 - btn_w // 2
    y = start_y + index * spacing
    return pygame.Rect(x, y, btn_w, btn_h)

def draw_btn(surf, text, font, color, rect, hover_color=None, disabled=False):
    global current_menu_rects, pad_menu_idx, using_gamepad
    
    if rect not in current_menu_rects:
        current_menu_rects.append(rect)
        
    idx = current_menu_rects.index(rect)
    # Clamp pad_menu_idx to valid range now that we have at least one rect
    if pad_menu_idx >= len(current_menu_rects): pad_menu_idx = len(current_menu_rects) - 1
    if pad_menu_idx < 0: pad_menu_idx = 0
    is_pad_selected = (idx == pad_menu_idx) and using_gamepad

    if disabled: color = C_GREY; hover_color = C_GREY
    mx, my = get_mouse_pos()
    
    c = (hover_color or C_WHITE) if (rect.collidepoint(mx,my) or is_pad_selected) and not disabled else color
    bg = pygame.Surface(rect.size, pygame.SRCALPHA); bg.fill((c[0]//8, c[1]//8, c[2]//8, 160)); surf.blit(bg, rect.topleft)
    pygame.draw.rect(surf, c, rect, 2, border_radius=4); t = font.render(text, True, c); surf.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    
    return (rect.collidepoint(mx, my) or is_pad_selected) and not disabled

FLOOR_W = 7800; GROUND_Y = 810

def gen_platforms(rng, floor_num):
    plats = [(200, GROUND_Y-120, 250), (550, GROUND_Y-220, 250), (900, GROUND_Y-120, 200)]; x = 1200
    while x < FLOOR_W - 400: w = rng.randint(180, 400); plats.append((x, rng.randint(GROUND_Y-260, GROUND_Y-100), w)); x += w + rng.randint(80, 160) + floor_num * 10
    return plats

def gen_enemies(rng, floor_num, plat_list):
    specs = []; difficulty = floor_num + meta["curse_level"]; max_seraphs = 0 if floor_num == 1 else (1 if floor_num == 2 else 2 if floor_num == 3 else 4 + floor_num)
    seraphs_spawned = 0; max_ents = 20 if meta["bosses_defeated"] == 0 else 999; ents_spawned = 0
    for px, py, pw in plat_list:
        if ents_spawned >= max_ents: break
        if px < 400 or px > FLOOR_W - 600: continue
        if rng.random() < (0.75 if floor_num == 1 else 0.40) or len(specs) == 0:
            etype = "grunt"
            if curse_active("bulwark_tide"): etype = "bulwark"
            elif curse_active("wraith_storm") and rng.random() < 0.6: etype = "wraith"
            elif meta["upg_blink"] and rng.random() < 0.35: etype = "bulwark"
            elif difficulty >= 3 and rng.random() < 0.20: etype = "wraith"
            specs.append({"type": etype, "x": px + pw//2, "y": GROUND_Y - 70, "pl": max(0, px - rng.randint(50, 150)), "pr": px + pw + rng.randint(50, 150)}); ents_spawned += 1
        if rng.random() < 0.40 and seraphs_spawned < max_seraphs and (meta["bosses_defeated"] > 0 or floor_num > 2):
            specs.append({"type": "seraph", "x": px + pw//2, "y": py - 140}); seraphs_spawned += 1; ents_spawned += 1
    for ex in range(1200, FLOOR_W - 600, 1000 if meta["bosses_defeated"] == 0 else 700):
        if ents_spawned >= max_ents: break
        if rng.random() < 0.4:
            if meta["upg_blink"] and rng.random() < 0.5: etype = "bulwark_elite"
            elif difficulty >= 2 and meta["bosses_defeated"] > 0 and seraphs_spawned < max_seraphs: etype = "seraph_elite"; seraphs_spawned += 1
            else: etype = "grunt"
            specs.append({"type": etype, "x": ex, "y": GROUND_Y - 70, "pl": ex - 150, "pr": ex + 150}); ents_spawned += 1
    return specs

def make_bg(rng, W=6000):
    surf = pygame.Surface((W, HEIGHT))
    for row in range(HEIGHT): pygame.draw.line(surf, (int(2 + (row/HEIGHT)*12), int(1 + (row/HEIGHT)*5), int(8 + (row/HEIGHT)*25)), (0, row), (W, row))
    moon_x, moon_y = W // 4, HEIGHT // 3; pygame.draw.circle(surf, (200, 180, 255), (moon_x, moon_y), 150); pygame.draw.circle(surf, (10, 5, 15), (moon_x - 15, moon_y - 10), 145); glow(surf, (120, 80, 220), moon_x, moon_y, 300, 25)
    for i in range(0, W, rng.randint(90, 180)):
        ph = rng.randint(200, HEIGHT - 150); pw = rng.randint(40, 80); shade = rng.randint(12, 18); col = (shade, shade-2, shade+5)
        pygame.draw.rect(surf, col, (i, HEIGHT-ph, pw, ph)); pygame.draw.polygon(surf, col, [(i, HEIGHT-ph), (i+pw//2, HEIGHT-ph-70), (i+pw, HEIGHT-ph)])
    return surf

def make_midground(rng, W=6000):
    surf = pygame.Surface((W, HEIGHT), pygame.SRCALPHA)
    for i in range(0, W, rng.randint(150, 280)):
        ph = rng.randint(120, 300); pw = rng.randint(80, 140); shade = rng.randint(22, 38)
        pygame.draw.rect(surf, (shade, shade-4, shade+10, 255), (i, HEIGHT-ph, pw, ph))
        if rng.random() > 0.3: pygame.draw.ellipse(surf, (0,0,0,0), (i+pw//4, HEIGHT-ph+30, pw//2, ph))
    return surf

_PROC_BG = make_bg(random.Random(0)); _PROC_MG = make_midground(random.Random(1))

def refresh_bg(seed): global _PROC_BG, _PROC_MG; _PROC_BG = make_bg(random.Random(seed)); _PROC_MG = make_midground(random.Random(seed + 1))

def draw_bg(surf, cx):
    overlap = 2
    if _SKY_IMG or _MOON_IMG or _CASTLES_IMG:
        if _SKY_IMG: w = _SKY_IMG.get_width(); ox = int(cx * 0.05) % w; surf.blit(_SKY_IMG, (-ox, 0)); surf.blit(_SKY_IMG, (-ox + w - overlap, 0)) if -ox + w < WIDTH + overlap else None; surf.blit(_SKY_IMG, (-ox + w * 2 - overlap * 2, 0)) if -ox + w * 2 < WIDTH + overlap else None
        else: surf.fill((10, 5, 20))
        if _MOON_IMG: surf.blit(_MOON_IMG, ((WIDTH // 4) - int(cx * 0.02), HEIGHT // 3 - _MOON_IMG.get_height()//2))
        if _CASTLES_IMG: w = _CASTLES_IMG.get_width(); ox = int(cx * 0.15) % w; surf.blit(_CASTLES_IMG, (-ox, 0)); surf.blit(_CASTLES_IMG, (-ox + w - overlap, 0)) if -ox + w < WIDTH + overlap else None; surf.blit(_CASTLES_IMG, (-ox + w * 2 - overlap * 2, 0)) if -ox + w * 2 < WIDTH + overlap else None
    else: W = _PROC_BG.get_width(); ox = int(cx * 0.15) % W; surf.blit(_PROC_BG, (-ox, 0)); surf.blit(_PROC_BG, (-ox + W, 0)) if -ox + W < WIDTH else None

def draw_mg(surf, cx):
    overlap = 2
    if _RUINS_IMG: w = _RUINS_IMG.get_width(); ox = int(cx * 0.35) % w; surf.blit(_RUINS_IMG, (-ox, 0)); surf.blit(_RUINS_IMG, (-ox + w - overlap, 0)) if -ox + w < WIDTH + overlap else None; surf.blit(_RUINS_IMG, (-ox + w * 2 - overlap * 2, 0)) if -ox + w * 2 < WIDTH + overlap else None
    else: W = _PROC_MG.get_width(); ox = int(cx * 0.35) % W; surf.blit(_PROC_MG, (-ox, 0)); surf.blit(_PROC_MG, (-ox + W, 0)) if -ox + W < WIDTH else None

def make_floor_tile():
    s = pygame.Surface((128, 128)); s.fill((25, 15, 35))
    for y in range(0, 128, 16):
        off = 8 if (y//16)%2 else 0
        for x in range(-16, 128, 32): pygame.draw.rect(s, (random.randint(45, 65), random.randint(30, 50), random.randint(70, 90)), (x+off, y, 30, 14), border_radius=2)
    pygame.draw.line(s, (90, 70, 120), (0, 0), (128, 0), 3); return s

FLOOR_TILE = make_floor_tile()

def make_plat_surf(w):
    s = pygame.Surface((w, 24), pygame.SRCALPHA); pygame.draw.rect(s, (35, 25, 50), (0, 0, w, 24), border_radius=3); pygame.draw.line(s, (90, 70, 120), (0, 0), (w, 0), 2)
    for y in range(3, 24, 7):
        off = 6 if (y//7)%2 else 0
        for x in range(-6, w, 24): pygame.draw.rect(s, (random.randint(45, 65), random.randint(30, 50), random.randint(70, 90)), (x+off, y, 22, 5))
    return s

particles = []
def spawn_particles(x, y, n, colors, speed=4, spread=math.pi*2, direction=None, gravity=0.3, sz=(2,6), life=(12,35)):
    for _ in range(n): ang = (direction if direction is not None else random.uniform(0, math.pi*2)) + random.uniform(-spread/2, spread/2); sp = random.uniform(speed*0.4, speed); particles.append({"x":x,"y":y,"vx":math.cos(ang)*sp,"vy":math.sin(ang)*sp,"g":gravity,"life":random.randint(*life),"ml":life[1],"sz":random.randint(*sz),"col":random.choice(colors)})

def update_particles(dt):
    for p in particles: p["x"]+=p["vx"]*dt; p["y"]+=p["vy"]*dt; p["vy"]+=p["g"]*dt; p["life"]-=dt
    particles[:] = [p for p in particles if p["life"]>0]

def draw_particles(surf, cx):
    for p in particles:
        r = max(1, p["sz"]); s = pygame.Surface((r*2,r*2), pygame.SRCALPHA); pygame.draw.circle(s, (*p["col"], max(0, int(255 * p["life"] / p["ml"]))), (r,r), r); surf.blit(s, (int(p["x"]-cx)-r, int(p["y"])-r))

class Afterimage:
    def __init__(self, img, x, y): self.img = img.copy(); self.x=x; self.y=y; self.a=140; self.alive=True
    def update(self): self.a -= 20; self.alive = self.a > 0
    def draw(self, surf, cx):
        if not self.alive: return
        i = self.img.copy(); i.set_alpha(max(0,self.a)); surf.blit(i, (self.x-int(cx), self.y))

class VoidTear:
    def __init__(self, x, y, color=None): self.x=x; self.y=y; self.col=color or C_PURPLE; self.life=35; self.ml=35; self.alive=True
    def update(self, dt): self.life -= dt; self.alive = self.life > 0
    def draw(self, surf, cx):
        if not self.alive: return
        t = self.life/self.ml; r=max(1,int(28*t)); a=int(210*t); sx,sy=int(self.x-cx),int(self.y)
        s=pygame.Surface((r*2+8,r*4+8),pygame.SRCALPHA); pygame.draw.ellipse(s,(*self.col,a),(0,0,r*2+8,r*4+8)); pygame.draw.ellipse(s,(*C_WHITE,min(255,a+50)),(r//2,r,r+8,r*2+8),2); surf.blit(s,(sx-r-4,sy-r*2-4))

void_tears = []; _dmg_numbers = []

class AbyssalTear:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.life = 180.0 
        self.max_life = 180.0
        self.radius = 350
        self.damage_timer = 0.0
        self.alive = True
        self.phase = 0.0

    def update(self, dt):
        self.life -= dt
        if self.life <= 0: 
            self.alive = False
            return
        
        self.phase += 0.05 * dt
        self.damage_timer -= dt

        targets = [e for e in enemies if e.alive]
        if boss_obj and boss_obj.alive: targets.append(boss_obj)
        
        hit_any = False
        for e in targets:
            dx = self.x - e.rect.centerx
            dy = self.y - e.rect.centery
            dist = math.hypot(dx, dy)
            
            if dist < self.radius and dist > 10:
                pull_force = ((self.radius - dist) / self.radius) * 6.0 * dt
                e.pos.x += (dx / dist) * pull_force
                e.rect.x = int(e.pos.x)

            if dist < 70 and self.damage_timer <= 0:
                dmg = int((5 + run_atk_bonus()) * run_dmg_mult())
                e.take_damage(dmg, self.x, unblockable=True)
                spawn_particles(e.rect.centerx, e.rect.centery, 5, [C_VOID, C_PURPLE, C_WHITE], speed=6)
                hit_any = True

        if hit_any:
            self.damage_timer = 15.0
            audio.play("hit", 0.3)

    def draw(self, surf, cx):
        if not self.alive: return
        sx, sy = int(self.x - cx), int(self.y)
        scale = min(1.0, self.life / 20.0) if self.life < 20 else min(1.0, (self.max_life - self.life) / 20.0)
        tear_img = _VOID_TEAR_IMG or _RIFT_IMG
        if tear_img:
            w, h = max(1, int(tear_img.get_width() * scale)), max(1, int(tear_img.get_height() * scale))
            scaled_img = pygame.transform.scale(tear_img, (w, h))
            surf.blit(scaled_img, (sx - w//2, sy - h//2))
        else:
            r = int(50 * scale)
            if r > 0:
                pygame.draw.circle(surf, (15, 0, 30), (sx, sy), r)
                pygame.draw.circle(surf, C_PURPLE, (sx, sy), r, max(1, r//5))
                pygame.draw.circle(surf, C_CYAN, (sx, sy), r//2, 1)

def spawn_dmg_number(x, y, amount, color=None, crit=False): _dmg_numbers.append({"x": float(x), "y": float(y), "vy": -2.2 - random.uniform(0, 1.0), "life": 38, "ml": 38, "text": str(amount), "col": color or (C_GOLD if crit else C_WHITE), "crit": crit})
def update_dmg_numbers(dt):
    for d in _dmg_numbers: d["y"] += d["vy"] * dt; d["vy"] = min(d["vy"] + 0.08 * dt, 0); d["life"] -= dt
    _dmg_numbers[:] = [d for d in _dmg_numbers if d["life"] > 0]
def draw_dmg_numbers(surf, cx):
    for d in _dmg_numbers:
        a = int(255 * (d["life"] / d["ml"]))
        if a <= 0: continue
        t = (F_MED if d["crit"] else F_SM).render(d["text"], True, d["col"]); t.set_alpha(a); surf.blit(t, (int(d["x"] - cx) - t.get_width() // 2, int(d["y"]) - t.get_height() // 2))

class EssenceDrop:
    def __init__(self, x, y, amount=1): self.pos = pygame.Vector2(x, y); self.vel = pygame.Vector2(random.uniform(-2.5,2.5), random.uniform(-4,-1.5)); self.life = 500; self.amount = amount; self.collected = False; self.phase = random.uniform(0, math.pi*2)
    def update(self, pl, dt):
        if self.collected: return
        self.life -= dt; self.phase += 0.08*dt
        if self.pos.y < GROUND_Y-20: self.vel.y += 0.18*dt
        else: self.pos.y=GROUND_Y-20; self.vel.x*=0.82; self.vel.y=0
        self.pos += self.vel*dt
        if pl and pl.alive:
            dx = pl.rect.centerx-self.pos.x; dy = pl.rect.centery-self.pos.y; d = max(1, math.hypot(dx,dy))
            if d < 130: self.vel += pygame.Vector2(dx/d,dy/d)*1.6*dt
            if d < 22: self.collected = True; meta["divine_essence"] += int(self.amount * run_essence_mult()); spawn_particles(self.pos.x,self.pos.y,5,[C_CYAN,C_WHITE],speed=3,sz=(2,4),life=(8,18))
    def draw(self, surf, cx):
        if self.collected or self.life <= 0: return
        sx,sy = int(self.pos.x-cx), int(self.pos.y)+int(math.sin(self.phase)*4)
        if _ESSENCE_IMG:
            surf.blit(_ESSENCE_IMG,(sx-_ESSENCE_IMG.get_width()//2,sy-_ESSENCE_IMG.get_height()//2))
        else:
            gs=pygame.Surface((14,14),pygame.SRCALPHA); pygame.draw.circle(gs,(*C_CYAN,90),(7,7),7); surf.blit(gs,(sx-7,sy-7)); pygame.draw.circle(surf,C_WHITE,(sx,sy),3); pygame.draw.circle(surf,C_CYAN,(sx,sy),3,1)

essence_drops = []

class EssenceMote:
    def __init__(self): self.reset()
    def reset(self): self.x=random.uniform(0,FLOOR_W); self.y=random.uniform(60, GROUND_Y-20); self.vx=random.uniform(-0.18,0.18); self.vy=random.uniform(-0.25,-0.06); self.life=self.ml=random.randint(180,580); self.r=random.randint(1,4); self.col=random.choice([C_PURPLE,C_CYAN,C_RUNEGLOW,(80,0,120)])
    def update(self, dt):
        self.x+=self.vx*dt; self.y+=self.vy*dt; self.life-=dt
        if self.life<=0: self.reset()
    def draw(self, surf, cx):
        sx,sy=int(self.x-cx),int(self.y)
        if -20 <= sx <= WIDTH+20: s=pygame.Surface((self.r*2,self.r*2),pygame.SRCALPHA); pygame.draw.circle(s,(*self.col,int(160*(self.life/self.ml))),(self.r,self.r),self.r); surf.blit(s,(sx-self.r,sy-self.r))

motes = [EssenceMote() for _ in range(100)]

class RelicPickup:
    def __init__(self, x, y, relic_id): self.x=float(x); self.y=float(y); self.rid = relic_id; self.data = RELIC_DEFS[relic_id]; self.phase = random.uniform(0, math.pi*2); self.rect = pygame.Rect(int(x)-18, int(y)-18, 36, 36); self.alive = True
    def update(self, pl, dt):
        self.phase += 0.06*dt
        if pl and pl.alive and self.rect.colliderect(pl.rect) and pl.can_pickup_relic(): run["relics"].append(self.rid); pl.apply_relic(self.rid); announce(f"RELIC: {self.data['name']}  — {self.data['desc']}", self.data["color"], 180); spawn_particles(self.x,self.y,25,[self.data["color"],C_WHITE],speed=5,sz=(2,6),life=(10,28)); audio.play("relic", 0.7); self.alive = False
    def draw(self, surf, cx):
        if not self.alive: return
        sx,sy = int(self.x-cx), int(self.y)+int(math.sin(self.phase)*6); c = self.data["color"]
        gs=pygame.Surface((40,40),pygame.SRCALPHA); pygame.draw.circle(gs,(*c,70),(20,20),20); surf.blit(gs,(sx-20,sy-20)); pygame.draw.circle(surf,c,(sx,sy),10,2); icon = F_MED.render(self.data["icon"], True, c); surf.blit(icon,(sx-icon.get_width()//2, sy-icon.get_height()//2))
        mx,my = get_mouse_pos(cx)
        if math.hypot(mx-self.x, my-self.y) < 40: lbl = F_SM.render(self.data["name"], True, c); surf.blit(lbl,(sx-lbl.get_width()//2, sy-32))

relic_pickups = []

class TreasureChest:
    def __init__(self, x, y): self.x=float(x); self.y=float(y); self.phase=0.0; self.rect=pygame.Rect(int(x)-24,int(y)-28,48,56); self.alive=True; self.opened=False; self.contents = self._roll_contents()
    def _roll_contents(self):
        r = random.random()
        if r < 0.35: return ("relic", None)
        elif r < 0.60: return ("essence", random.randint(15, 35))
        elif r < 0.80: return ("trinket", random.choice(list(TRINKET_DEFS.keys())))
        else: return ("hp", 2)
    def update(self, pl, dt):
        self.phase += 0.06*dt
        if not self.opened and pl and pl.alive and safe_key(pygame.key.get_pressed(), meta["binds"].get("interact", -1)) and self.rect.colliderect(pl.rect): self._open(pl)
    def _open(self, pl):
        self.opened = True; ctype, cval = self.contents; spawn_particles(self.x, self.y-20, 30, [C_GOLD, C_WHITE, C_YELLOW], speed=6, sz=(3,8))
        if ctype == "relic":
            pool=[k for k in RELIC_DEFS if k not in run["relics"]+run["relic_offered"]]
            if pool and pl.can_pickup_relic(): rid=random.choice(pool); run["relic_offered"].append(rid); relic_pickups.append(RelicPickup(self.x, self.y-40, rid)); announce("TREASURE: RELIC FOUND!", C_GOLD, 160)
            else: meta["divine_essence"] += 20; announce("TREASURE: +20 ESSENCE (RELIC SLOTS FULL)", C_CYAN, 130)
        elif ctype == "essence": meta["divine_essence"] += cval; announce(f"TREASURE: +{cval} ESSENCE", C_CYAN, 130)
        elif ctype == "trinket":
            global player_trinket
            if player_trinket is None: player_trinket = cval; d = TRINKET_DEFS[cval]; announce(f"TRINKET: {d['name']} — {d['desc']}", d["color"], 160)
            else: meta["divine_essence"] += 12; announce("TREASURE: +12 ESSENCE (TRINKET SLOT FULL)", C_CYAN, 130)
        elif ctype == "hp":
            missing = pl.max_hp - pl.hp
            if missing > 0: pl.hp += min(cval, missing); announce(f"TREASURE: +{min(cval, missing)} HP RESTORED", C_RED, 130)
            else: meta["divine_essence"] += 15; announce("TREASURE: +15 ESSENCE (HP FULL)", C_CYAN, 130)
        run["treasure_rooms_found"] = run.get("treasure_rooms_found", 0) + 1; audio.play("relic", 0.9); self.alive = False
    def draw(self, surf, cx):
        if not self.alive: return
        sx,sy = int(self.x-cx), int(self.y); bob = int(math.sin(self.phase)*3)
        img = (_CHEST_OPEN_IMG if self.opened else _CHEST_IMG)
        if img:
            ground_sy = int(GROUND_Y - cx*0 - cx*0)  # GROUND_Y in screen space (no cam offset on Y)
            surf.blit(img,(sx-img.get_width()//2, GROUND_Y-img.get_height()+bob))
        else:
            pygame.draw.rect(surf, (70,45,15), (sx-22, sy-20+bob, 44, 40), border_radius=4); pygame.draw.rect(surf, (110,75,25), (sx-22, sy-20+bob, 44, 40), 2, border_radius=4); pygame.draw.rect(surf, (55,35,10), (sx-22, sy-6+bob, 44, 8))
            pygame.draw.circle(surf, C_GOLD, (sx, sy-2+bob), 5); pygame.draw.circle(surf, C_GOLD, (sx, sy-2+bob), 5, 2)
            gs = pygame.Surface((60,60), pygame.SRCALPHA); pygame.draw.circle(gs, (*C_GOLD, int(40*(0.6 + 0.4*math.sin(self.phase)))), (30,30), 30); surf.blit(gs, (sx-30, sy-30+bob), special_flags=pygame.BLEND_RGBA_ADD)
        if player and self.rect.colliderect(player.rect): lbl = F_SM.render(f"[{pygame.key.name(meta['binds']['interact']).upper()}] OPEN CHEST", True, C_GOLD); surf.blit(lbl, (sx-lbl.get_width()//2, sy-50+bob))

treasure_chests = []

class Torch:
    def __init__(self, x, y): self.x=x; self.y=y; self.phase=random.uniform(0,math.pi*2); self.flames=[]
    def update(self, dt):
        self.phase += 0.1*dt; torch_top = self.y - (_TORCH_IMG.get_height() if _TORCH_IMG else 24) + 4
        if random.random()<0.35: self.flames.append([float(self.x),float(torch_top),random.uniform(-0.6,0.6),random.uniform(-1.4,-0.4),random.randint(8,18)])
        for f in self.flames: f[0]+=f[2]*dt; f[1]+=f[3]*dt; f[4]-=dt
        self.flames=[f for f in self.flames if f[4]>0]
    def draw(self, surf, cx):
        sx,sy = int(self.x-cx),int(self.y)
        if _TORCH_IMG: surf.blit(_TORCH_IMG, (sx - _TORCH_IMG.get_width()//2, sy - _TORCH_IMG.get_height()))
        else: pygame.draw.rect(surf,C_STONE2,(sx-3,sy-24,6,24),border_radius=2); pygame.draw.rect(surf,C_STONE,(sx-3,sy-24,6,24),1,border_radius=2)
        for f in self.flames:
            fx,fy,t = int(f[0]-cx),int(f[1]),f[4]/18.0; c = C_RUNEGLOW if t>0.5 else C_PURPLE; r = max(1,int(4*t))
            fs=pygame.Surface((r*2,r*2),pygame.SRCALPHA); pygame.draw.circle(fs,(*c,int(200*t)),(r,r),r); surf.blit(fs,(fx-r,fy-r))
    def draw_light(self, light, cx):
        sx,sy = int(self.x-cx),int(self.y); torch_top = sy - ((_TORCH_IMG.get_height() if _TORCH_IMG else 24)); flk = math.sin(self.phase)*4; r = int(250+flk*8)
        glow(light,C_PURPLE,sx,torch_top,r,int(60+flk*4)); glow(light,C_RUNEGLOW,sx,torch_top,int(r*0.5),90)

class RestShrine:
    COST = 50
    def __init__(self, x, y): self.x=x; self.y=y; self.rect=pygame.Rect(int(x)-40,int(y)-50,80,80); self.phase=0.0; self.alive=True; self.used=False
    def update(self, pl, dt):
        self.phase += 0.06*dt
        if not pl or not pl.alive or self.used: return
        if safe_key(pygame.key.get_pressed(), meta["binds"].get("interact", -1)) and self.rect.colliderect(pl.rect):
            if meta["divine_essence"] >= self.COST:
                meta["divine_essence"] -= self.COST; self.used=True; pl.hp = pl.max_hp
                run["flasks"] = 3
                spawn_particles(pl.rect.centerx, pl.rect.centery, 30, [C_GOLD, C_WHITE, C_HOLY], speed=5, gravity=-0.1); audio.play("levelup", 0.7)
                announce("RESTED: FULL HEAL & FLASKS REFILLED. ENEMIES RESPAWNED.", C_GOLD, 200)
                global enemies; enemies.clear()
                specs = gen_enemies(random.Random(), run["floor"], platforms)
                for sp in specs:
                    t=sp["type"]
                    if t=="grunt": enemies.append(Grunt(sp["x"],sp["y"],sp["pl"],sp["pr"]))
                    elif t=="bulwark": enemies.append(Bulwark(sp["x"],sp["y"],sp["pl"],sp["pr"]))
                    elif t=="wraith": enemies.append(Wraith(sp["x"],sp["y"]))
                    elif t=="seraph": enemies.append(Seraph(sp["x"],sp["y"],elite=False))
                    elif t=="seraph_elite": enemies.append(Seraph(sp["x"],sp["y"],elite=True))
                    elif t=="bulwark_elite": b=Bulwark(sp["x"],sp["y"],sp["x"]-150,sp["x"]+150); b.HP=int(8*get_diff()); b.hp=b.HP; enemies.append(b)
            else: announce("NOT ENOUGH ESSENCE TO REST", C_RED, 60)
    def draw(self, surf, cx):
        sx,sy = int(self.x-cx), int(self.y); bob = int(math.sin(self.phase)*4); pulse = 0.6+0.4*math.sin(self.phase*1.5); c_glow = C_GOLD if not self.used else C_STONE
        if _REST_SHRINE_IMG:
            img = _REST_SHRINE_IMG.copy()
            if self.used: img.fill((80,80,80,255),special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(img,(sx-img.get_width()//2, GROUND_Y-img.get_height()+bob))
        else:
            pygame.draw.rect(surf,(35,28,52),(sx-40,sy-12,80,24),border_radius=4); pygame.draw.rect(surf,c_glow,(sx-40,sy-12,80,24),2,border_radius=4)
            cx2,cy2 = sx,sy-28+bob; gs = pygame.Surface((90,90),pygame.SRCALPHA); pygame.draw.circle(gs,(*c_glow,int(60*pulse)),(45,45),45); surf.blit(gs,(cx2-45,cy2-45),special_flags=pygame.BLEND_RGBA_ADD)
            pygame.draw.ellipse(surf,(50,45,25) if not self.used else (30,30,30),(cx2-24,cy2-10,48,22)); pygame.draw.ellipse(surf,c_glow,(cx2-24,cy2-10,48,22),2)
        if player and self.rect.colliderect(player.rect) and not self.used: lbl = F_SM.render(f"REST [{pygame.key.name(meta['binds']['interact']).upper()}] — {self.COST} ESSENCE", True, C_GOLD); surf.blit(lbl,(sx-lbl.get_width()//2, sy-80))
    def draw_light(self, light, cx):
        if not self.used: glow(light,C_GOLD,int(self.x-cx),int(self.y)-28,150,60)

class TalismanStone:
    def __init__(self, x, y):
        self.x = float(x); self.y = float(y)
        self.rect = pygame.Rect(int(x)-40, int(y)-60, 80, 80)
        self.phase = 0.0; self.alive = True
    def update(self, pl, dt):
        self.phase += 0.05 * dt
        if not pl or not pl.alive: return
        if safe_key(pygame.key.get_pressed(), meta["binds"].get("interact", -1)) and self.rect.colliderect(pl.rect):
            global STATE, menu_view, PREV_STATE
            PREV_STATE = STATE; STATE = "paused"; menu_view = "talisman_select"
    def draw(self, surf, cx):
        sx, sy = int(self.x - cx), int(self.y)
        pulse = 0.6 + 0.4 * math.sin(self.phase * 1.3)
        col = C_PURPLE
        if _TALISMAN_STONE_IMG:
            surf.blit(_TALISMAN_STONE_IMG,(sx-_TALISMAN_STONE_IMG.get_width()//2, GROUND_Y-_TALISMAN_STONE_IMG.get_height()))
        else:
            pygame.draw.rect(surf, (30, 20, 45), (sx-38, sy-8, 76, 28), border_radius=4)
            pygame.draw.rect(surf, col, (sx-38, sy-8, 76, 28), 2, border_radius=4)
            orb = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(orb, (*col, int(80 * pulse)), (25, 25), 25)
            pygame.draw.circle(orb, (*col, 200), (25, 25), 12, 2)
            surf.blit(orb, (sx - 25, sy - 58))
        for i, tkey in enumerate(active_talismans):
            td = TALISMAN_DEFS[tkey]
            ic = F_SM.render(td["icon"], True, td["color"])
            surf.blit(ic, (sx - 18 + i * 22, sy - 60))
        if player and self.rect.colliderect(player.rect):
            lbl = F_SM.render(f"TALISMANS [{pygame.key.name(meta['binds']['interact']).upper()}]", True, col)
            surf.blit(lbl, (sx - lbl.get_width()//2, sy - 80))
    def draw_light(self, light, cx):
        glow(light, C_PURPLE, int(self.x - cx), int(self.y) - 35, 130, 50)

class CursedBloodAltar:
    def __init__(self, x, y):
        self.x            = float(x)
        self.y            = float(y)
        self.rect         = pygame.Rect(int(x) - 30, int(y) - 64, 60, 80)
        self.phase        = 0.0
        self.alive        = True
        self.used         = False
        self._use_cooldown = 0

    def update(self, pl, dt):
        self.phase += 0.07 * dt
        if self._use_cooldown > 0:
            self._use_cooldown -= dt
        if self.used or not pl or not pl.alive:
            return
        if (self._use_cooldown <= 0
                and safe_key(pygame.key.get_pressed(), meta["binds"].get("interact", -1))
                and self.rect.colliderect(pl.rect)):
            self._activate(pl)

    def _activate(self, pl):
        if pl.max_hp <= 1:
            announce("MAX HP TOO LOW — THE ALTAR REFUSES YOU", C_BLOOD, 80)
            self._use_cooldown = 40
            return
        self.used = True
        pl.max_hp -= 1
        pl.hp      = min(pl.hp, pl.max_hp)
        pool = [k for k in RELIC_DEFS if k not in run["relics"] + run["relic_offered"]]
        if pool and pl.can_pickup_relic():
            rid = random.choice(pool)
            run["relic_offered"].append(rid)
            relic_pickups.append(RelicPickup(self.x, self.y - 50, rid))
        else:
            meta["divine_essence"] += 25
            announce("RELIC SLOTS FULL — +25 ESSENCE GRANTED", C_BLOOD, 120)
        for _ in range(5):
            essence_drops.append(EssenceDrop(self.x, self.y - 20))
        spawn_particles(self.x, self.y - 32, 60, [C_BLOOD, C_RED, (10, 0, 0), (0, 0, 0)], speed=9, gravity=0.15, sz=(3, 10), life=(18, 50))
        spawn_particles(self.x, self.y - 32, 30, [C_WHITE, C_BLOOD], speed=5, gravity=-0.05, sz=(2, 5), life=(10, 28))
        audio.play("relic", 0.9)
        announce("BLOOD PACT — 1 MAX HP SACRIFICED FOR POWER", C_BLOOD, 200)

    def draw(self, surf, cx):
        sx, sy  = int(self.x - cx), int(self.y)
        pulse   = 0.5 + 0.5 * math.sin(self.phase * 1.6)
        c_glow  = C_BLOOD if not self.used else (40, 10, 10)
        if _BLOOD_ALTAR_IMG:
            img = _BLOOD_ALTAR_IMG.copy()
            if self.used: img.fill((60,20,20,255),special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(img,(sx-img.get_width()//2, sy-img.get_height()))
        else:
            pygame.draw.rect(surf, (22, 14, 18), (sx - 24, sy - 8, 48, 20), border_radius=3)
            pygame.draw.rect(surf, (50, 35, 40), (sx - 24, sy - 8, 48, 20), 1, border_radius=3)
            pygame.draw.rect(surf, (28, 18, 22), (sx - 14, sy - 64, 28, 56), border_radius=4)
            pygame.draw.rect(surf, (55, 38, 44), (sx - 14, sy - 64, 28, 56), 1, border_radius=4)
            pygame.draw.rect(surf, (38, 24, 30), (sx - 18, sy - 68, 36, 10), border_radius=3)
            pygame.draw.rect(surf, (70, 45, 52), (sx - 18, sy - 68, 36, 10), 1, border_radius=3)
        rune_alpha = int(130 * pulse) if not self.used else 20
        rune_surf = pygame.Surface((20, 40), pygame.SRCALPHA)
        pygame.draw.line(rune_surf, (*c_glow, rune_alpha), (10, 2),  (10, 38), 2)
        pygame.draw.line(rune_surf, (*c_glow, rune_alpha), (3,  12), (17, 12), 2)
        pygame.draw.line(rune_surf, (*c_glow, rune_alpha), (5,  24), (15, 24), 2)
        surf.blit(rune_surf, (sx - 10, sy - 58))
        if not self.used:
            orb_r    = int(14 + 4 * pulse)
            orb_surf = pygame.Surface((orb_r * 2 + 4, orb_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(orb_surf, (*C_BLOOD, int(90 * pulse)), (orb_r + 2, orb_r + 2), orb_r)
            pygame.draw.circle(orb_surf, (*C_RED, int(160 * pulse)), (orb_r + 2, orb_r + 2), max(1, orb_r - 5), 2)
            surf.blit(orb_surf, (sx - orb_r - 2, sy - 82 - orb_r))
        else:
            pygame.draw.circle(surf, (30, 8, 8), (sx, sy - 82), 5)
        if player and self.rect.colliderect(player.rect) and not self.used:
            k_name = pygame.key.name(meta["binds"]["interact"]).upper()
            lbl = F_SM.render(f"[{k_name}] BLOOD PACT: -1 MAX HP \u2192 RELIC + ESSENCE", True, C_BLOOD)
            surf.blit(lbl, (sx - lbl.get_width() // 2, sy - 108))
        elif self.used:
            spent = F_TINY.render("SPENT", True, (60, 20, 20))
            surf.blit(spent, (sx - spent.get_width() // 2, sy - 90))

    def draw_light(self, light, cx):
        if not self.used:
            pulse = 0.5 + 0.5 * math.sin(self.phase * 1.6)
            glow(light, C_BLOOD, int(self.x - cx), int(self.y) - 82, int(120 + 30 * pulse), int(55 * pulse))

class Merchant:
    def __init__(self, x, y): self.x=x; self.y=y; self.rect=pygame.Rect(int(x)-30,int(y)-80,60,80); self.phase=0.0; self.alive=True
    def update(self, pl, dt):
        self.phase += 0.05*dt
        if pl and pl.alive and self.rect.colliderect(pl.rect) and safe_key(pygame.key.get_pressed(), meta["binds"].get("interact", -1)):
            global STATE, menu_view, PREV_STATE; PREV_STATE=STATE; STATE="paused"; menu_view="merchant_shop"
    def draw(self, surf, cx):
        sx,sy = int(self.x-cx), int(self.y); bob = int(math.sin(self.phase)*3)
        if _MERCHANT_IMG:
            surf.blit(_MERCHANT_IMG,(sx-_MERCHANT_IMG.get_width()//2, sy-_MERCHANT_IMG.get_height()+bob))
        else:
            ms = pygame.Surface((60,80), pygame.SRCALPHA); pygame.draw.ellipse(ms, (30,20,40), (10, 20+bob, 40, 60)); pygame.draw.circle(ms, (180,160,200), (30, 20+bob), 15); surf.blit(ms, (sx-30, sy-80))
        if player and self.rect.colliderect(player.rect): lbl = F_SM.render(f"TRADE [{pygame.key.name(meta['binds']['interact']).upper()}]", True, C_CYAN); surf.blit(lbl,(sx-lbl.get_width()//2, sy-110))
    def draw_light(self, light, cx): glow(light,C_CYAN,int(self.x-cx),int(self.y)-40,120,40)

class Door:
    def __init__(self, x, y, color, label, target_state): self.rect=pygame.Rect(x,y,90,150); self.color=color; self.label=label; self.target=target_state; self.locked=True; self.gp=0.0; self.open_t=0.0; self.opening=False; self.is_open=False
    def unlock(self): self.locked = False
    def try_open(self):
        if not self.locked and not self.opening: self.opening=True; audio.play("dash",0.4)
    def update(self, dt):
        self.gp += 0.06*dt
        if self.opening and not self.is_open:
            self.open_t += 0.018*dt
            if random.random()<0.25: spawn_particles(self.rect.centerx,self.rect.bottom-random.randint(0,80),2,[self.color,C_WHITE],speed=2)
            if self.open_t >= 1.0: self.is_open=True; self.open_t=1.0
    def draw(self, surf, cx):
        sx,sy = self.rect.x-int(cx),self.rect.y; c = C_GREY if self.locked else self.color
        if _DOOR_OPEN and self.open_t > 0.5:
            img = _DOOR_OPEN.copy(); img.fill((80,80,80,255),special_flags=pygame.BLEND_RGBA_MULT) if self.locked else None; surf.blit(img,(sx,sy))
        elif _DOOR_IDLE:
            img = _DOOR_IDLE.copy(); img.fill((80,80,80,255),special_flags=pygame.BLEND_RGBA_MULT) if self.locked else None
            tint = pygame.Surface((90,150),pygame.SRCALPHA); tint.fill((*c,60)); img.blit(tint,(0,0),special_flags=pygame.BLEND_RGBA_ADD); surf.blit(img,(sx,sy))
        else:
            slide = int(45*self.open_t)
            if self.open_t > 0: portal=pygame.Surface((90,150),pygame.SRCALPHA); pygame.draw.rect(portal,(*c,int(140*self.open_t)),(0,0,90,150),border_radius=5); surf.blit(portal,(sx,sy))
            for side,ox in [(0,-slide),(1,45+slide)]: dp=pygame.Surface((45,150),pygame.SRCALPHA); pygame.draw.rect(dp,(18,14,26),(0,0,45,150),border_radius=5); pygame.draw.rect(dp,c,(0,0,45,150),2,border_radius=5); surf.blit(dp,(sx+ox,sy))
        y_bob = int(math.sin(self.gp*2)*4) if not self.locked else 0
        lbl = F_SM.render(self.label.replace("[E]", f"[{pygame.key.name(meta['binds']['interact']).upper()}]"),True,c); surf.blit(lbl,(sx+45-lbl.get_width()//2,sy-26+y_bob))
        if not self.locked and not self.opening: a = int(110+55*math.sin(self.gp)); gs=pygame.Surface((130,190),pygame.SRCALPHA); pygame.draw.ellipse(gs,(*self.color,a//3),(0,0,130,190)); surf.blit(gs,(sx-20,sy-20))
    def draw_light(self, light, cx):
        if not self.locked: glow(light,self.color,int(self.rect.centerx-cx),self.rect.centery,110,45+int(40*self.open_t))

class Proj:
    def __init__(self, x, y, vx, vy, color=C_RED, radius=7, homing=False, target=None, speed=5, shooter=None, ptype="generic", damage=1, piercing=False, poison=False):
        self.pos=pygame.Vector2(x,y); self.vel=pygame.Vector2(vx,vy); self.color=color; self.radius=radius; self.alive=True; self.trail=[]; self.homing=homing; self.target=target; self.speed=speed; self.shooter=shooter; self.ptype=ptype; self.damage=damage; self.piercing=piercing; self.poison=poison; self.parried=False; self.age=0
    def deflect(self): self.vel=-self.vel; self.homing=False; self.color=C_CYAN; self.parried=True
    def update(self, pl, dt):
        self.age += dt
        if self.homing and self.target and getattr(self.target,'alive',False):
            dx=self.target.rect.centerx-self.pos.x; dy=self.target.rect.centery-self.pos.y; d=max(1,math.hypot(dx,dy))
            self.vel += (pygame.Vector2(dx/d*self.speed,dy/d*self.speed)-self.vel)*0.05*dt
        self.trail.append((self.pos.x,self.pos.y))
        if len(self.trail)>10: self.trail.pop(0)
        self.pos += self.vel*dt
        if self.pos.x<-500 or self.pos.x>FLOOR_W+500 or self.pos.y>1200 or self.pos.y<-200: self.alive=False; return

        if self.ptype in ("player_bolt","player_wave","player_ult"):
            targets=[e for e in enemies if e.alive]
            if boss_obj and boss_obj.alive: targets.append(boss_obj)
            for e in targets:
                if e.rect.collidepoint(self.pos):
                    e.take_damage(self.damage, self.pos.x)
                    if self.poison and hasattr(e,'poison_timer'): e.poison_timer=200
                    spawn_particles(self.pos.x,self.pos.y,12,[C_PURPLE,C_WHITE,C_CYAN],speed=4)
                    if not self.piercing: self.alive=False
                    break
            return

        if self.parried and self.shooter and getattr(self.shooter,'alive',True):
            if self.shooter.rect.collidepoint(self.pos):
                self.alive=False; self.shooter.take_damage(2,self.pos.x,unblockable=True)
                spawn_particles(self.pos.x,self.pos.y,14,[C_CYAN,C_WHITE],speed=4); return

        if not self.parried and pl and pl.alive:
            if math.hypot(pl.rect.centerx-self.pos.x,pl.rect.centery-self.pos.y) < self.radius+14:
                if pl.parry_state == "active":
                    self.deflect(); pl.invincible=max(pl.invincible,15)
                    spawn_parry_vfx(pl.rect.centerx, pl.rect.centery, pl.facing_r)
                    spawn_particles(int(self.pos.x),int(self.pos.y),18,[C_CYAN,C_WHITE,C_GOLD],speed=5,gravity=-0.05)
                    add_combo(1); pl.mana=min(pl.max_mana,pl.mana+15)
                    if curse_active("parry_boon"): pl.mana = pl.max_mana
                    _on_successful_parry()
                else:
                    self.alive=False; pl.take_damage()

    def draw(self, surf, cx):
        sx,sy=int(self.pos.x-cx),int(self.pos.y); ang=math.atan2(self.vel.y,self.vel.x)
        if self.ptype=="flaming_gold" and _PROJ_FIREBALL:
            img=_PROJ_FIREBALL
            if self.parried: img=img.copy(); img.fill((0,200,255,255),special_flags=pygame.BLEND_RGBA_MULT)
            rot=pygame.transform.rotate(img,-math.degrees(ang)); surf.blit(rot,(sx-rot.get_width()//2,sy-rot.get_height()//2)); return
        if self.ptype in ("player_wave","player_bolt") and _PROJ_DARKWAVE:
            rot=pygame.transform.rotate(_PROJ_DARKWAVE,-math.degrees(ang)); rot.set_alpha(220); surf.blit(rot,(sx-rot.get_width()//2,sy-rot.get_height()//2)); return
        for i,(tx,ty) in enumerate(self.trail):
            a=int(140*i/max(1,len(self.trail))); r=max(1,self.radius-int((len(self.trail)-i)*0.6))
            ts=pygame.Surface((r*2,r*2),pygame.SRCALPHA); pygame.draw.circle(ts,(*self.color,a),(r,r),r); surf.blit(ts,(int(tx-cx)-r,int(ty)-r))
        for r,a in [(self.radius*3,25),(self.radius*2,55),(self.radius,255)]:
            s=pygame.Surface((r*2,r*2),pygame.SRCALPHA); pygame.draw.circle(s,(*self.color,a),(r,r),r); surf.blit(s,(sx-r,sy-r))

def apply_poison_tick(e, dt):
    if not hasattr(e,'poison_timer'): return
    if e.poison_timer>0:
        e.poison_timer-=dt; tick_rate=20 if getattr(e,'fast_poison',False) else 40
        if int(e.poison_timer)%tick_rate<1:
            e.hp-=1; spawn_particles(e.rect.centerx,e.rect.y+10,4,[C_PLAGUE,(80,220,60)],speed=2,gravity=-0.1,sz=(2,4))
            if e.hp<=0: e.alive=False

class HolyPillar:
    def __init__(self, x, warn=60): self.x=float(x); self.w=55; self.state="warn"; self.timer=float(warn); self.alive=True; self.alpha=0; self.rect=pygame.Rect(int(x)-self.w//2,0,self.w,GROUND_Y)
    def update(self, pl, dt):
        if self.state=="warn":
            self.timer-=dt; self.alpha=min(145,int(145*(1-self.timer/60.0)))
            if self.timer<=0: self.state="active"; self.timer=14.0; self.alpha=255; spawn_particles(self.x,GROUND_Y,18,[C_GOLD,C_HOLY,C_WHITE],speed=6,direction=-math.pi/2,spread=math.pi,gravity=0.15)
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
            pygame.draw.ellipse(surf,(*C_RED,150),(sx-self.w//2,GROUND_Y-12,self.w,18),2); ws=pygame.Surface((self.w,GROUND_Y),pygame.SRCALPHA); ws.fill((*C_RED,int(self.alpha*0.25))); surf.blit(ws,(sx-self.w//2,0))
        else:
            ps=pygame.Surface((self.w,GROUND_Y),pygame.SRCALPHA); pygame.draw.rect(ps,(*C_GOLD,int(self.alpha*0.55)),(0,0,self.w,GROUND_Y)); pygame.draw.rect(ps,(*C_WHITE,self.alpha),(self.w//4,0,self.w//2,GROUND_Y)); surf.blit(ps,(sx-self.w//2,0))
            pygame.draw.ellipse(surf,(*C_WHITE,self.alpha),(sx-self.w//2-8,GROUND_Y-17,self.w+16,26))

def _on_successful_parry():
    run["parries_this_run"] = run.get("parries_this_run", 0) + 1; meta["total_parries"] = meta.get("total_parries", 0) + 1
    if run_has("parry_master") and player:
        run["parry_heal_counter"] = run.get("parry_heal_counter", 0) + 1
        if run["parry_heal_counter"] >= 3:
            run["parry_heal_counter"] = 0; player.hp = min(player.max_hp, player.hp + 1); announce("PARRY MASTER — HP RESTORED", C_SILVER, 80); spawn_particles(player.rect.centerx, player.rect.centery, 12, [C_SILVER, C_WHITE], speed=3, gravity=-0.1)
    if curse_active("parry_boon") and player: player.mana = player.max_mana

def _resolve_melee_vs_parry(enemy, pl):
    global hit_stop_timer, screen_shake
    if pl.parry_state == "active":
        pl.parry_state = "none"; pl.parry_cd = 5; pl.invincible = max(pl.invincible, 15); pl.mana = min(pl.max_mana, pl.mana + 15)
        if curse_active("parry_boon"): pl.mana = pl.max_mana
        if hasattr(enemy, 'stagger_meter'):
            stagger_bonus = 1.0
            enemy.stagger_meter += 1.0 * stagger_bonus
            if enemy.stagger_meter >= enemy.stagger_threshold:
                enemy.state = "stunned"; enemy.stun_t = 220 if not isinstance(enemy,Boss) else 250; enemy.stagger_meter = 0; announce("POSTURE BROKEN!", C_GOLD, 80)
        hit_stop_timer = 5.0; screen_shake = max(screen_shake, 8); spawn_parry_vfx(pl.rect.centerx, pl.rect.centery, pl.facing_r); audio.play("parry", 1.0)
        if talisman_active("voidwarden"):
            pl.mana = min(pl.max_mana, pl.mana + 8)
            _talisman_voidwarden_on_parry()
            announce("VOID WARDEN — ENEMIES SLOWED!", C_CYAN, 70)
        if run_has("thorn_mantle"):
            enemy.hp -= 2; spawn_particles(enemy.rect.centerx, enemy.rect.centery, 8, [C_PLAGUE,C_WHITE], speed=4)
            if enemy.hp <= 0: enemy.alive = False
        add_combo(2); _on_successful_parry(); return True
    else: pl.take_damage(); return True

class EnemyBase:
    def __init__(self):
        self.alive=True; self.hit_timer=0; self.poison_timer=0; self.projs=[]; self.projectiles=self.projs; self.stagger_meter=0; self.stagger_threshold=1+int(meta.get("curse_level", 0)*0.6)
    def _tick_hit(self, dt): self.hit_timer-=dt if self.hit_timer>0 else 0
    def _land_on_floor(self, dt):
        self.vel_y=min(getattr(self,'vel_y',0)+0.75*dt,18); self.pos.y+=self.vel_y*dt; self.rect.y=int(self.pos.y)
        if self.rect.bottom>=GROUND_Y: self.rect.bottom=GROUND_Y; self.vel_y=0; self.pos.y=float(self.rect.y)
    def _move_towards(self, tx, speed, dt):
        speed_mod = 1.5 if curse_active("haste") else 1.0
        if talisman_slow_active(): speed_mod *= 0.6
        dx=tx-self.rect.centerx; self.direction=1 if dx>=0 else -1
        if abs(dx)>4: self.pos.x+=speed*speed_mod*self.direction*dt
        self.rect.x=int(self.pos.x)
    def _drop_essence(self, n=1, elite=False):
        global kill_streak, kill_streak_best
        amount=3 if elite else 1
        for _ in range(n): essence_drops.append(EssenceDrop(self.rect.centerx,self.rect.centery,amount))
        meta["total_kills"]+=1; run["kills"]+=1; kill_streak+=1
        if kill_streak>kill_streak_best: kill_streak_best=kill_streak
        if curse_active("bloodlust") and player and not getattr(run,'_bloodlust_used',False) and random.random()<0.3: run["_bloodlust_used"]=True; player.hp=min(player.max_hp, player.hp+1); announce("BLOODLUST — HP RESTORED", C_RED, 80)
        if kill_streak==5: announce("KILL STREAK  ×5 — RELENTLESS!",C_ORANGE,100)
        elif kill_streak==10: announce("KILL STREAK  ×10 — UNSTOPPABLE!",C_RED,120)
        elif kill_streak>10 and kill_streak%5==0: announce(f"KILL STREAK  ×{kill_streak} — VOID INCARNATE!",C_RUNEGLOW,120)
    def _maybe_drop_relic(self):
        if random.random()<(0.7 if curse_active("elite_surge") else 0.5):
            pool=[k for k in RELIC_DEFS if k not in run["relics"]+run["relic_offered"]]
            if pool and len(run["relics"])<meta["upg_relic_slots"]:
                rid=random.choice(pool); run["relic_offered"].append(rid); relic_pickups.append(RelicPickup(self.rect.centerx,self.rect.centery-30,rid))

class TrainingDummy(EnemyBase):
    def __init__(self, x, y):
        super().__init__()
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(x, y - 40, 50, 90)
        self.HP = 999999
        self.hp = self.HP
        self.state = "idle"
        self.stun_t = 0
        self.stagger_threshold = 15
        self.total_dmg = 0
        self.dps_t = 0
        if _DUMMY_IMG:
            self.rect.width = _DUMMY_IMG.get_width()
            self.rect.height = _DUMMY_IMG.get_height()

    def take_damage(self, amount, sx, unblockable=False):
        self.hit_timer = 12
        self.stagger_meter += 0.25
        self.total_dmg += amount
        self.dps_t = 180
        spawn_dmg_number(self.rect.centerx, self.rect.y, amount, C_ORANGE if unblockable else C_WHITE)
        if run_has("soulsucker") and player: player.hp = min(player.max_hp, player.hp + 1)

    def update(self, pl, plats, dt):
        self._tick_hit(dt)
        apply_poison_tick(self, dt)
        if self.dps_t > 0:
            self.dps_t -= dt
            if self.dps_t <= 0:
                self.total_dmg = 0
        
        if self.state == "stunned":
            self.stun_t -= dt
            if self.stun_t <= 0:
                self.stun_t = 0; self.state = "idle"; self.stagger_meter = 0
            return
        
        if self.stagger_meter >= self.stagger_threshold:
            self.state = "stunned"; self.stun_t = 300

        self._land_on_floor(dt)

    def draw(self, surf, cx):
        sx, sy = self.rect.x - int(cx), self.rect.y
        if self.hit_timer > 0 and int(self.hit_timer) % 4 < 2: return
        
        if _DUMMY_IMG:
            img = _DUMMY_IMG.copy()
            if self.poison_timer > 0: img.fill((*C_PLAGUE, 150), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(img, (sx, sy))
        else:
            pygame.draw.rect(surf, (90, 60, 40), (sx + 15, sy + 30, 20, 60))
            pygame.draw.ellipse(surf, (120, 90, 70), (sx, sy, 50, 40)) 
            pygame.draw.rect(surf, (100, 70, 50), (sx - 10, sy + 40, 70, 15), border_radius=4) 
        
        if self.total_dmg > 0:
            draw_text(surf, f"COMBO DMG: {self.total_dmg}", F_SM, C_GOLD, sx + self.rect.width//2, sy - 30, center=True)
            
        if self.state == "stunned":
            btn = "Y" if using_gamepad else pygame.key.name(meta['binds']['atk']).upper()
            draw_text(surf, f"EXECUTE [{btn}]", F_SM, C_RED, sx + self.rect.width//2, sy - 50, center=True)
        
        if self.stagger_meter > 0:
            sw = int(self.stagger_threshold * 5)
            pygame.draw.rect(surf, (50, 50, 50), (sx + self.rect.width//2 - sw//2, sy - 10, sw, 4))
            pygame.draw.rect(surf, C_ORANGE, (sx + self.rect.width//2 - sw//2, sy - 10, int(self.stagger_meter * 5), 4))

class Grunt(EnemyBase):
    def __init__(self, x, y, pl, pr):
        super().__init__(); self.pos=pygame.Vector2(x,y); self.vel_y=0; self.HP=max(2,int(4*get_diff())); self.hp=self.HP; self.direction=1; self.rect=pygame.Rect(x,y,44,62); self.pl=pl; self.pr=pr; self.state="patrol"
        self.MELEE_CD=55; self.MELEE_DUR=14; self.melee_t=random.randint(20,50); self.melee_a=0; self.anim_t=0.0; self.stun_t=0
        self._weapon = pygame.Surface((16, 60), pygame.SRCALPHA); pygame.draw.rect(self._weapon, (120, 110, 130), (4, 0, 8, 45)); pygame.draw.rect(self._weapon, (60, 40, 40), (4, 45, 8, 15)); pygame.draw.rect(self._weapon, (90, 80, 40), (0, 42, 16, 4))
        if _GRUNT_FRAMES_R and _GRUNT_FRAMES_R[0] is not None:
            self._imgs_r=_GRUNT_FRAMES_R; self._imgs_l=_GRUNT_FRAMES_L; self.rect=pygame.Rect(x,y,_GRUNT_FRAMES_R[0].get_width(),_GRUNT_FRAMES_R[0].get_height())
        else: self._imgs_r=self._mk_frames((155,90,220)); self._imgs_l=[pygame.transform.flip(f,True,False) for f in self._imgs_r]

    def _mk_frames(self, tint):
        frames=[]
        for i in range(4):
            s=pygame.Surface((44,62),pygame.SRCALPHA); pygame.draw.ellipse(s,(*tint,200),(8,12,28,42)); pygame.draw.circle(s,(tint[0]//2+60,tint[1]//2+40,tint[2]//2+40,220),(22,10),9)
            pygame.draw.circle(s,(*C_RED,240),(18+(i%2),8),2); pygame.draw.circle(s,(*C_RED,240),(26+(i%2),8),2); pygame.draw.rect(s,(*tint,120),(6,30+int(math.sin(i*math.pi/2)*3),32,24),border_radius=4); frames.append(s)
        return frames

    def take_damage(self, amount, sx, unblockable=False):
        self.hp-=amount; self.hit_timer=14; self.stagger_meter += 0.25; spawn_dmg_number(self.rect.centerx,self.rect.y,amount)
        if run_has("soulsucker") and player: player.hp=min(player.max_hp,player.hp+1)
        if self.hp <= 0:
            self.alive = False
            self._drop_essence(random.randint(1, 2))
            _talisman_bloodpact_kill_reset()

    def update(self, pl, plats, dt):
        if not self.alive: return
        self._tick_hit(dt); apply_poison_tick(self,dt)
        if self.state=="stunned":
            self.stun_t-=dt
            if self.stun_t<=0: self.stun_t=0; self.state="patrol"; self.stagger_meter=0
            self._land_on_floor(dt); return
        dist=math.hypot(pl.rect.centerx-self.rect.centerx,pl.rect.centery-self.rect.centery)
        if dist<80: self.state="attack"
        elif dist<380: self.state="chase"
        else: self.state="patrol"

        if self.state=="patrol":
            slow = 0.6 if talisman_slow_active() else 1.0
            self.pos.x+=1.8*(1.5 if curse_active("haste") else 1.0)*slow*self.direction*dt
            if self.pos.x<self.pl: self.direction=1
            if self.pos.x>self.pr: self.direction=-1
        elif self.state=="chase": self._move_towards(pl.rect.centerx,2.8,dt)
        elif self.state=="attack":
            self._move_towards(pl.rect.centerx,2.0,dt); self.melee_t-=dt
            if self.melee_t<=0: self.melee_t=float(self.MELEE_CD); self.melee_a=self.MELEE_DUR

        if self.melee_a>0:
            self.melee_a-=dt; mr = pygame.Rect(0, 0, 50, 60)
            if self.direction > 0: mr.left = self.rect.centerx
            else: mr.right = self.rect.centerx
            mr.centery = self.rect.centery
            if mr.colliderect(pl.rect): _resolve_melee_vs_parry(self,pl)

        self._land_on_floor(dt); self.anim_t=(self.anim_t+0.12*dt)%len(self._imgs_r)

    def draw(self, surf, cx):
        if not self.alive: return
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return
        img=(self._imgs_r if self.direction>0 else self._imgs_l)[int(self.anim_t)%len(self._imgs_r)]
        if img is None: return
        if self.poison_timer>0: img=img.copy(); img.fill((*C_PLAGUE,180),special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(img,(self.rect.x-int(cx),self.rect.y))
        
        if self.melee_a>0:
            prog = 1.0 - (self.melee_a / self.MELEE_DUR); ang_deg = (-30 + 120 * prog) if self.direction > 0 else (30 - 120 * prog); pivot = pygame.Surface((100, 100), pygame.SRCALPHA); pivot.blit(self._weapon, (50 - 8, 50 - 50)); rot = pygame.transform.rotate(pivot, -ang_deg); hx = self.rect.centerx - int(cx) + (10 if self.direction > 0 else -10); hy = self.rect.centery + 5; surf.blit(rot, (hx - rot.get_width()//2, hy - rot.get_height()//2))

        if self.state=="stunned": 
            btn = "Y" if using_gamepad else pygame.key.name(meta['binds']['atk']).upper()
            draw_text(surf,f"EXECUTE [{btn}]",F_SM,C_RED,self.rect.x-int(cx)+22,self.rect.y-22,center=True)
        if self.hp<self.HP:
            for i in range(min(self.HP,10)): pygame.draw.rect(surf,C_RED if i<self.hp else C_GREY,(self.rect.x-int(cx)+i*9,self.rect.y-8,7,4))
        if self.stagger_meter > 0: pygame.draw.rect(surf, (50,50,50), (self.rect.x-int(cx), self.rect.y-14, int(self.stagger_threshold * 9), 4)); pygame.draw.rect(surf, C_ORANGE, (self.rect.x-int(cx), self.rect.y-14, int(self.stagger_meter * 9), 4))

class Bulwark(Grunt):
    def __init__(self, x, y, pl, pr):
        super().__init__(x,y,pl,pr); self.HP=4; self.hp=self.HP; self.MELEE_CD=80
        self._weapon = pygame.Surface((20, 60), pygame.SRCALPHA); pygame.draw.rect(self._weapon, (100, 100, 110), (2, 0, 16, 45), border_radius=2); pygame.draw.rect(self._weapon, (60, 40, 40), (6, 45, 8, 15))
    def take_damage(self, amount, sx, unblockable=False):
        if not unblockable and ((self.direction>0 and sx>self.rect.centerx) or (self.direction<0 and sx<self.rect.centerx)):
            spawn_particles(self.rect.centerx+self.direction*22,self.rect.centery,8,[C_GOLD,C_WHITE,C_GREY],speed=5); audio.play("parry",0.5)
            if player: player.pos.x-=self.direction*10; player.rect.x=int(player.pos.x)
        else: super().take_damage(amount,sx,unblockable=unblockable)
    def update(self, pl, plats, dt):
        old_dir=self.direction; super().update(pl, plats, dt); self.direction=old_dir if self.melee_a>0 else self.direction
    def draw(self, surf, cx):
        super().draw(surf, cx)
        if self.alive and self.hit_timer <= 0:
            sx=self.rect.x-int(cx); sr=(sx+self.rect.w-4,self.rect.y+8,10,44) if self.direction>0 else (sx-6,self.rect.y+8,10,44)
            pygame.draw.rect(surf,(90,90,100),sr,border_radius=3); pygame.draw.rect(surf,C_GOLD,sr,2,border_radius=3); pygame.draw.circle(surf,C_GOLD,(int(sr[0]+5),int(sr[1]+22)),4,1)

class Wraith(EnemyBase):
    def __init__(self, x, y, is_boss=False):
        super().__init__(); self.pos=pygame.Vector2(x,y); self.is_boss=is_boss
        self.HP = max(2,int(4*get_diff())) * (15 if is_boss else 1); self.hp=self.HP; self.direction=1
        self.rect=pygame.Rect(x,y, 80 if is_boss else 40, 108 if is_boss else 54); self.phase=random.uniform(0,math.pi*2); self.base_y=float(y); self.tele_cd=120; self.shoot_cd=90; self.state="hover"
        self.stagger_threshold = (1 + int(meta.get("curse_level", 0) * 0.6)) * (5 if is_boss else 1)

    def take_damage(self, amount, sx, unblockable=False):
        self.hp-=amount; self.hit_timer=14; self.stagger_meter += 0.25
        spawn_dmg_number(self.rect.centerx,self.rect.y,amount,C_PURPLE)
        if run_has("soulsucker") and player: player.hp=min(player.max_hp,player.hp+1)
        if self.hp<=0:
            self.alive=False; self._drop_essence(10 if self.is_boss else 2, elite=self.is_boss)
            if not self.is_boss:
                run["wraiths_killed"] = run.get("wraiths_killed", 0) + 1
                if run["wraiths_killed"] >= 5 and not run.get("slayer_spawned", False):
                    run["slayer_spawned"] = True; announce("SLAYER BOUNTY: WRAITH KING APPEARS!", C_PURPLE, 200)
                    global enemies; wboss = Wraith(self.rect.centerx, 200, is_boss=True); enemies.append(wboss)
            else: announce("WRAITH KING SLAIN! MASSIVE LOOT DROPPED.", C_GOLD, 200); self._maybe_drop_relic(); self._maybe_drop_relic()

    def update(self, pl, plats, dt):
        if not self.alive: return
        self._tick_hit(dt); apply_poison_tick(self,dt); self.phase+=0.06*dt; self.tele_cd-=dt; self.shoot_cd-=dt
        if self.state=="stunned":
            self.stun_t-=dt
            if self.stun_t<=0: self.stun_t=0; self.state="hover"; self.stagger_meter=0
            return
            
        self.direction=1 if pl.rect.centerx>self.rect.centerx else -1; self.pos.y=self.base_y+math.sin(self.phase)*(30 if self.is_boss else 20)
        dx=pl.rect.centerx-self.rect.centerx; speed_mod=(1.5 if curse_active("haste") else 1.0) * (1.5 if self.is_boss else 1.0)
        if abs(dx)>380: self.pos.x+=2.4*speed_mod*self.direction*dt
        elif abs(dx)>220: self.pos.x+=1.4*speed_mod*self.direction*dt
        elif abs(dx)<140: self.pos.x-=1.6*speed_mod*self.direction*dt
        self.rect.topleft=(int(self.pos.x),int(self.pos.y))
        
        if self.tele_cd<=0:
            self.tele_cd=120 if self.is_boss else 180; self.pos.x=pl.rect.centerx+random.choice([-1,1])*random.randint(120,250)
            void_tears.append(VoidTear(self.pos.x,self.pos.y,(80,0,120))); spawn_particles(int(self.pos.x),int(self.pos.y),16,[(80,0,140),C_PURPLE],speed=4)
        if self.shoot_cd<=0:
            self.shoot_cd=50 if self.is_boss else 100; dx2=pl.rect.centerx-self.rect.centerx; dy2=pl.rect.centery-self.rect.centery; d=max(1,math.hypot(dx2,dy2))
            if self.is_boss:
                for a in [-0.2, 0, 0.2]: self.projs.append(Proj(self.rect.centerx,self.rect.centery,math.cos(math.atan2(dy2,dx2)+a)*5.5,math.sin(math.atan2(dy2,dx2)+a)*5.5,(150,0,200),10,shooter=self, damage=2))
            else: self.projs.append(Proj(self.rect.centerx,self.rect.centery,dx2/d*4.5,dy2/d*4.5,(120,0,160),7,shooter=self))
        for p in self.projs: p.update(pl,dt)
        self.projs=[p for p in self.projs if p.alive]

    def draw(self, surf, cx):
        if not self.alive: return
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return
        sx,sy=self.rect.x-int(cx),self.rect.y; a=int(170+70*math.sin(self.phase))
        _wi = (_WRAITH_IMG_R if self.direction > 0 else _WRAITH_IMG_L) if not self.is_boss else None
        if _wi:
            img = _wi.copy(); img.set_alpha(a)
            if self.poison_timer > 0: img.fill((*C_PLAGUE,150),special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(img,(sx,sy))
        else:
            gs=pygame.Surface(self.rect.size,pygame.SRCALPHA); scale = 2 if self.is_boss else 1
            pygame.draw.ellipse(gs,(*C_VOID,a),(4*scale,8*scale,32*scale,38*scale)); pygame.draw.circle(gs,(*C_PURPLE,a),(20*scale,12*scale),10*scale)
            pygame.draw.circle(gs,(*C_RED,240),(14*scale,10*scale),2*scale); pygame.draw.circle(gs,(*C_RED,240),(26*scale,10*scale),2*scale); surf.blit(gs,(sx,sy))
        for p in self.projs: p.draw(surf,cx)
        if self.state=="stunned": 
            btn = "Y" if using_gamepad else pygame.key.name(meta['binds']['atk']).upper()
            draw_text(surf,f"EXECUTE [{btn}]",F_SM,C_RED,self.rect.x-int(cx)+self.rect.w//2,self.rect.y-22,center=True)
        if self.is_boss: bw = 100; bx = sx + self.rect.w//2 - bw//2; by = sy - 10; pygame.draw.rect(surf,(30,15,45),(bx,by,bw,6)); pygame.draw.rect(surf,C_PURPLE,(bx,by,max(0,int(bw*self.hp/self.HP)),6))
        if self.stagger_meter > 0: sw = int(self.stagger_threshold * (5 if self.is_boss else 9)); pygame.draw.rect(surf, (50,50,50), (sx, sy-14, sw, 4)); pygame.draw.rect(surf, C_ORANGE, (sx, sy-14, int(self.stagger_meter * (5 if self.is_boss else 9)), 4))

class Seraph(EnemyBase):
    def __init__(self, x, y, elite=False):
        super().__init__(); self.pos=pygame.Vector2(x,y); self.base_y=float(y); self.MAX_HP=max(3,int(6*get_diff())); self.hp=self.MAX_HP+(2 if elite else 0); self.direction=1; self.elite=elite; self.rect=pygame.Rect(x,y,52,72); self.state="hover"
        self.stun_t=0; self.hover_t=random.uniform(0,math.pi*2); self.wing_t=random.uniform(0,math.pi*2)
        self.stagger_threshold = 2 + int(meta.get("curse_level", 0) * 0.6); self.BEAM_CD=480; self.DIVE_CD=600; self.PILLAR_CD=700; atk_scale=max(0.4,get_diff())
        self.beam_cd=random.randint(int(280/atk_scale),int(self.BEAM_CD/atk_scale)); self.dive_cd=random.randint(int(350/atk_scale),int(self.DIVE_CD/atk_scale)); self.pillar_cd=random.randint(int(400/atk_scale),int(self.PILLAR_CD/atk_scale))
        self._atk_scale=atk_scale; self.pillars=[]; self.dive_origin=pygame.Vector2(x,y); self.dive_target=pygame.Vector2(x,y); self.dive_t=0; self.facing_r=True; self.anim_t=0.0; self._make_sprite()

    def _make_sprite(self):
        w,h=52,72; s=pygame.Surface((w,h),pygame.SRCALPHA); pygame.draw.ellipse(s,(*C_HOLY,210),(8,22,36,44)); pygame.draw.ellipse(s,(*C_GOLD,180),(10,0,32,14),3); pygame.draw.circle(s,(*C_HOLY,230),(26,14),11); pygame.draw.circle(s,(*C_GOLD,120),(26,14),13,2); self._body=s

    def take_damage(self, amount, sx, unblockable=False):
        self.hp-=amount; self.stagger_meter += 0.25; self.hit_timer=14; spawn_dmg_number(self.rect.centerx,self.rect.y,amount,C_GOLD)
        if run_has("soulsucker") and player: player.hp=min(player.max_hp,player.hp+1)
        if self.hp<=0: self.alive=False; self._drop_essence(random.randint(2,4),elite=self.elite); self._maybe_drop_relic() if self.elite else None

    def _fire(self, pl):
        dx=pl.rect.centerx-self.rect.centerx; dy=pl.rect.centery-self.rect.centery; d=max(1,math.hypot(dx,dy)); self.projs.append(Proj(self.rect.centerx,self.rect.centery,dx/d*3.5,dy/d*3.5,C_GOLD,9,homing=False,target=pl,speed=3.0,shooter=self,ptype="spearhead",damage=1))
        if self.elite: self.projs.append(Proj(self.rect.centerx,self.rect.centery,math.cos(math.atan2(dy,dx)+0.3)*3.5,math.sin(math.atan2(dy,dx)+0.3)*3.5,C_HOLY,7,shooter=self,damage=1))

    def update(self, pl, dt):
        if not self.alive: return
        self._tick_hit(dt); apply_poison_tick(self,dt)
        for pil in self.pillars: pil.update(pl,dt)
        self.pillars=[p for p in self.pillars if p.alive]; self.projs=[p for p in self.projs if p.alive]
        for p in self.projs: p.update(pl,dt)
        
        self.hover_t+=0.04*dt; self.wing_t+=0.09*dt; self.anim_t+=0.15*dt
        if self.stagger_meter>=self.stagger_threshold and self.state!="stunned": self.state="stunned"; self.stun_t=220
        if self.state=="stunned":
            self.stun_t-=dt
            if self.stun_t<=0: self.stun_t=0; self.state="hover"; self.stagger_meter = 0 
            return
            
        if self.state=="hover":
            self.direction=1 if pl.rect.centerx>self.rect.centerx else -1; self.facing_r=(self.direction>0); sc=getattr(self,'_atk_scale',1.0); speed_mod=1.5 if curse_active("haste") else 1.0; self.pos.x+=1.5*speed_mod*self.direction*dt*sc; self.pos.y=self.base_y+math.sin(self.hover_t)*16; self.rect.topleft=(int(self.pos.x),int(self.pos.y)); self.beam_cd-=dt; self.dive_cd-=dt; self.pillar_cd-=dt
            if self.beam_cd<=0: self._fire(pl); self.beam_cd=int(self.BEAM_CD/sc)
            if self.pillar_cd<=0:
                tx=pl.rect.centerx+int(pl.vel.x*10 if hasattr(pl,'vel') else 0); self.pillars.append(HolyPillar(tx))
                if self.elite: self.pillars.append(HolyPillar(tx+random.choice([-180,180])))
                self.pillar_cd=int(self.PILLAR_CD/sc)
            if self.dive_cd<=0: self.state="dive"; self.dive_origin=pygame.Vector2(self.pos); self.dive_target=pygame.Vector2(pl.rect.centerx,GROUND_Y-80); self.dive_t=0; self.dive_cd=int(self.DIVE_CD/sc)
        elif self.state=="dive":
            self.dive_t+=dt; t=min(1.0,self.dive_t/20.0); ease=t*t*(3-2*t); self.pos.x=self.dive_origin.x+(self.dive_target.x-self.dive_origin.x)*ease; self.pos.y=self.dive_origin.y+(self.dive_target.y-self.dive_origin.y)*ease; self.rect.topleft=(int(self.pos.x),int(self.pos.y))
            if self.dive_t%2==0: spawn_particles(self.rect.centerx,self.rect.centery,3,[C_GOLD,C_WHITE],speed=2,gravity=0.1)
            if t>=1.0:
                spawn_particles(self.rect.centerx,self.rect.bottom,16,[C_GOLD,C_WHITE,C_HOLY],speed=5,spread=math.pi,direction=-math.pi/2,gravity=0.18)
                if abs(pl.rect.centerx-self.rect.centerx)<70: pl.take_damage()
                self.state="return"; self.dive_t=0; self.base_y=self.dive_origin.y
        elif self.state=="return":
            self.dive_t+=dt; t=min(1.0,self.dive_t/32.0); ease=t*t*(3-2*t); self.pos.x=self.dive_target.x+(self.dive_origin.x-self.dive_target.x)*ease; self.pos.y=self.dive_target.y+(self.dive_origin.y-self.dive_target.y)*ease; self.rect.topleft=(int(self.pos.x),int(self.pos.y))
            if t>=1.0: self.state="hover"

    def draw(self, surf, cx):
        if not self.alive: return
        for pil in self.pillars: pil.draw(surf,cx)
        for p in self.projs: p.draw(surf,cx)
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return
        sx,sy=self.rect.x-int(cx),self.rect.y; is_stun=self.state=="stunned"; body_has_wings=bool(_SERAPH_IMG_R and _SERAPH_IMG_L)
        if not is_stun and not body_has_wings:
            wbeat=math.sin(self.wing_t); wing_alpha=int(120+70*abs(wbeat)); ws=pygame.Surface((220,160),pygame.SRCALPHA)
            for side in (-1,1): lp=[(110+side*6,78), (110+side*int(50+12*wbeat), 80+int(-26+wbeat*-10)), (110+side*10,98)]; pygame.draw.polygon(ws,(*C_HOLY,wing_alpha),lp); pygame.draw.polygon(ws,(*C_GOLD,140),lp,2)
            surf.blit(ws,(sx+self.rect.w//2-110,sy+self.rect.h//2-80))
        body=(_SERAPH_IMG_R if self.facing_r else _SERAPH_IMG_L).copy() if bool(_SERAPH_IMG_R and _SERAPH_IMG_L) else self._body.copy(); bob=int(math.sin(self.hover_t*1.3)*2)
        if is_stun: body.fill((100,100,100,255),special_flags=pygame.BLEND_RGBA_MULT)
        if self.poison_timer>0: body.fill((*C_PLAGUE,150),special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(body,(sx,sy+bob))
        if is_stun: 
            btn = "Y" if using_gamepad else pygame.key.name(meta['binds']['atk']).upper()
            draw_text(surf,f"EXECUTE [{btn}]",F_SM,C_RED,sx+26,sy-22,center=True)
        bw,bx,by=55,sx+26-27,sy-11; pygame.draw.rect(surf,(30,15,45),(bx,by,bw,4)); pygame.draw.rect(surf,C_RED,(bx,by,max(0,int(bw*self.hp/self.MAX_HP)),4))
        if self.stagger_meter > 0: pygame.draw.rect(surf, (50,50,50), (bx, by-5, int(self.stagger_threshold * 5), 3)); pygame.draw.rect(surf, C_ORANGE, (bx, by-5, int(self.stagger_meter * 5), 3))
        if self.elite: crown=F_TINY.render("★",True,C_GOLD); surf.blit(crown,(sx+26-crown.get_width()//2,sy-30))

class Boss(EnemyBase):
    def __init__(self, x, y):
        super().__init__(); self.pos=pygame.Vector2(x,y); self.vel_y=0; self.MAX_HP=max(25,int(40*get_diff())); self.hp=self.MAX_HP; self.P2=self.MAX_HP*0.70; self.P3=self.MAX_HP*0.35
        self.rect=pygame.Rect(x,y,110,190); self.state="active"; self.stun_t=0; self.direction=-1; self.facing_r=False; self.anim_t=0.0; self.death_t=100; self.phase2_done=False; self.phase3_done=False; self.phase_flash=0
        speed_mult=1.0/max(0.6,get_diff()); self.shoot_t=90.0*speed_mult; self.charge_t=220.0*speed_mult; self.melee_t=0.0; self.melee_a=0
        self.charging=False; self.spawn_t=500.0*speed_mult; self.p2_vuln=False; self.keys_list=[]; self.keys_found=0; self.pillars=[]; self.adds=[]
        self.CHARGE_SPD=9*max(0.6,get_diff()); self.stagger_threshold = 3 + int(meta.get("curse_level", 0) * 0.8)
        self._weapon = pygame.Surface((30, 140), pygame.SRCALPHA); pygame.draw.rect(self._weapon, C_RED, (10, 0, 10, 100)); pygame.draw.rect(self._weapon, C_GOLD, (6, 0, 18, 100), 2); pygame.draw.rect(self._weapon, (40, 20, 20), (10, 100, 10, 40)); pygame.draw.rect(self._weapon, C_STONE, (0, 95, 30, 10))
        self._mk_frames()

    def _mk_frames(self):
        self._frames={}
        if _BOSS_FRAMES_R:
            for ph in [1,2,3]:
                tints={1:None,2:(255,165,80,200),3:(220,40,40,200)}; frames=[]
                for f in _BOSS_FRAMES_R:
                    img=f.copy()
                    if tints[ph]: tint=pygame.Surface(img.get_size(),pygame.SRCALPHA); tint.fill(tints[ph]); img.blit(tint,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
                    frames.append(img)
                self._frames[ph]=frames
            self._frames_l={ph: [pygame.transform.flip(f,True,False) for f in self._frames[ph]] for ph in [1,2,3]}
            self.rect=pygame.Rect(int(self.pos.x),int(self.pos.y),_BOSS_FRAMES_R[0].get_width(),_BOSS_FRAMES_R[0].get_height()); return
        self._frames_l={}
        for ph,tint in [(1,(220,185,0)),(2,(255,130,0)),(3,(185,20,20))]:
            frames=[]
            for i in range(4):
                s=pygame.Surface((110,190),pygame.SRCALPHA); sway=int(math.sin(i*math.pi/2)*4)
                pygame.draw.ellipse(s,(*tint,200),(15,30+sway,80,140)); pygame.draw.circle(s,(*tint,220),(55,22),20); pygame.draw.circle(s,(*C_WHITE,180),(55,18),22,3)
                if ph==2: pygame.draw.ellipse(s,(*C_ORANGE,100),(5,25+sway,100,160))
                if ph==3: pygame.draw.ellipse(s,(*C_RED,80),(0,20+sway,110,170)); pygame.draw.circle(s,(*C_RED,200),(55,22),22,3)
                frames.append(s)
            self._frames[ph]=frames; self._frames_l[ph]=[pygame.transform.flip(f,True,False) for f in frames]

    @property
    def ph(self): return 1 if self.hp>self.P2 else (2 if self.hp>self.P3 else 3)

    def take_damage(self, amount, sx, unblockable=False):
        if self.ph==2 and not self.p2_vuln: announce("COLLECT ALL KEYS FIRST!",C_RED,70); return
        self.hp-=amount; self.stagger_meter+=0.25
        self.hit_timer=12; spawn_dmg_number(self.rect.centerx,self.rect.y-20,amount,C_ORANGE,crit=(amount>=6)); spawn_particles(self.rect.centerx,self.rect.centery,14,[C_GOLD,C_ORANGE,C_WHITE],speed=5)
        if self.hp<=0:
            self.alive=False
            for _ in range(20): essence_drops.append(EssenceDrop(self.rect.centerx,self.rect.centery,3))
            meta["total_kills"]+=1; run["kills"]+=1; meta["bosses_defeated"]=meta.get("bosses_defeated",0)+1
            _talisman_bloodpact_kill_reset()
            if meta["bosses_defeated"]>0 and meta["curse_level"]<5: meta["curse_level"]=min(5,meta["bosses_defeated"])
            global time_scale,bullet_time_timer,hit_stop_timer,screen_shake; time_scale=0.25; bullet_time_timer=95; hit_stop_timer=max(hit_stop_timer,10.0); screen_shake=max(screen_shake,24)
            pool=[k for k in RELIC_DEFS if k not in run["relics"]+run["relic_offered"]]
            if pool: rid=random.choice(pool); run["relic_offered"].append(rid); relic_pickups.append(RelicPickup(self.rect.centerx,self.rect.centery-30,rid))
            save_meta()

    def _fire(self, pl, count=1, spread=0):
        ba=math.atan2(pl.rect.centery-self.rect.centery,pl.rect.centerx-self.rect.centerx)
        for i in range(count): a=ba+math.radians(spread*(i-(count-1)/2)); self.projs.append(Proj(self.rect.centerx,self.rect.centery,math.cos(a)*6,math.sin(a)*6,C_GOLD,11,shooter=self,ptype="flaming_gold",damage=1))

    def _spawn_keys(self):
        self.keys_list=[]; self.keys_found=0; self.p2_vuln=False
        for px,py,pw in random.sample(platforms,min(4,len(platforms))): self.keys_list.append([float(px+pw//2),float(py-24),False,pygame.Rect(int(px+pw//2)-12,int(py-24)-12,24,24),random.uniform(0,math.pi*2)])

    def update(self, pl, dt):
        if not self.alive:
            if self.death_t>0: self.death_t-=dt; return
        self._tick_hit(dt); apply_poison_tick(self,dt)
        if self.phase_flash>0: self.phase_flash-=1
        if self.melee_a>0: self.melee_a-=dt
        if self.ph==2 and not self.phase2_done: 
            self.phase2_done=True; self.phase_flash=55; 
            announce(STORY_DIALOGUE.get("boss_p2", "AETHERIA: 'The keys to your demise are scattered!'"),C_ORANGE,200); 
            spawn_particles(self.rect.centerx,self.rect.centery,40,[C_GOLD,C_ORANGE,C_WHITE],speed=8); self._spawn_keys()
        if self.ph==3 and not self.phase3_done: 
            self.phase3_done=True; self.phase_flash=80; self.p2_vuln=True; 
            announce(STORY_DIALOGUE.get("boss_p3", "AETHERIA: 'I AM THE ABYSS! KNEEL!'"),C_RED,220); 
            spawn_particles(self.rect.centerx,self.rect.centery,60,[C_RED,C_ORANGE,C_GOLD,C_PURPLE],speed=9)
        for k in self.keys_list:
            k[4]+=0.07*dt; k[3].x=int(k[0])-12
            if not k[2] and k[3].colliderect(pl.rect):
                k[2]=True; self.keys_found+=1; spawn_particles(int(k[0]),int(k[1]),18,[C_GOLD,C_WHITE,C_CYAN],speed=4,gravity=-0.1)
                rem=sum(1 for kk in self.keys_list if not kk[2])
                if rem==0: self.p2_vuln=True; announce(STORY_DIALOGUE.get("boss_keys_found", "ALL KEYS — STRIKE NOW!"),C_CYAN,120)
                else: announce(f"KEY {self.keys_found}/4 — {rem} REMAIN",C_GOLD,80)
        for pil in self.pillars: pil.update(pl,dt)
        self.pillars=[p for p in self.pillars if p.alive]; self.projs=[p for p in self.projs if p.alive]; self.adds=[a for a in self.adds if a.alive]
        for p in self.projs: p.update(pl,dt)
        for add in self.adds: add.update(pl,platforms,dt)
        if self.stagger_meter>=self.stagger_threshold and self.state!="stunned": self.state="stunned"; self.stun_t=250
        if self.state=="stunned":
            self.stun_t-=dt
            if self.stun_t<=0: self.stun_t=0; self.state="active"; self.stagger_meter = 0 
            return
        self._land_on_floor(dt); self.direction=1 if pl.rect.centerx>self.rect.centerx else -1; self.facing_r=(self.direction>0); speed_mult=max(0.5,get_diff())
        if self.ph==1:
            if abs(pl.rect.centerx-self.rect.centerx)>20: self.pos.x+=2.2*speed_mult*self.direction*dt; self.rect.x=int(self.pos.x)
            self.shoot_t-=dt
            if self.shoot_t<=0: self.shoot_t=95.0/speed_mult; self._fire(pl)
        elif self.ph==2:
            if abs(pl.rect.centerx-self.rect.centerx)>20: self.pos.x+=1.6*speed_mult*self.direction*dt; self.rect.x=int(self.pos.x)
            self.shoot_t-=dt
            if self.shoot_t<=0: self.shoot_t=150.0/speed_mult; self._fire(pl,3,20)
        elif self.ph==3:
            self.charge_t-=dt; self.melee_t-=dt; self.spawn_t-=dt; self.shoot_t-=dt
            if self.charge_t<=0: self.charge_t=200.0/speed_mult; self.charging=True
            if self.charging:
                self.pos.x+=self.CHARGE_SPD*self.direction*dt; self.rect.x=int(self.pos.x)
                if abs(pl.rect.centerx-self.rect.centerx)<90: self.charging=False; spawn_particles(self.rect.centerx,self.rect.bottom,22,[C_RED,C_ORANGE,C_GOLD],speed=6,spread=math.pi,direction=-math.pi/2,gravity=0.2)
            else:
                if abs(pl.rect.centerx-self.rect.centerx)>20: self.pos.x+=3.5*speed_mult*self.direction*dt; self.rect.x=int(self.pos.x)
            if self.melee_t<=0: self.melee_t=60.0/speed_mult; self.melee_a=18; spawn_particles(self.rect.centerx,self.rect.centery,12,[C_RED,C_ORANGE],speed=5)
            if self.melee_a>0:
                mr = pygame.Rect(0, 0, 100, 140); mr.left = self.rect.centerx if self.facing_r else self.rect.centerx - 100; mr.centery = self.rect.centery
                if mr.colliderect(pl.rect): _resolve_melee_vs_parry(self,pl)
            if self.shoot_t<=0: self.shoot_t=42.0/speed_mult; self._fire(pl,2,15)
            if self.spawn_t<=0: self.spawn_t=420.0/speed_mult; lx,rx=int(self.pos.x)-140,int(self.pos.x)+140; self.adds.append(Bulwark(lx,350,lx-60,lx+180)); self.adds.append(Grunt(rx,350,rx-180,rx+60))
        self.anim_t=(self.anim_t+0.09*dt)%4

    def draw(self, surf, cx):
        for p in self.projs: p.draw(surf,cx)
        for add in self.adds: add.draw(surf,cx)
        for pil in self.pillars: pil.draw(surf,cx)
        for k in self.keys_list:
            if k[2]: continue
            kx,ky=int(k[0]-cx),int(k[1])+int(math.sin(k[4])*5); gs=pygame.Surface((30,30),pygame.SRCALPHA); pygame.draw.circle(gs,(*C_GOLD,70),(15,15),15); surf.blit(gs,(kx-15,ky-15))
            pygame.draw.circle(surf,C_GOLD,(kx,ky),7,3); pygame.draw.line(surf,C_GOLD,(kx,ky+7),(kx,ky+16),3)
        if not self.alive and self.death_t<=0: return
        sx,sy=self.rect.x-int(cx),self.rect.y
        if self.state=="stunned":
            _stun_frames = self._frames_l[self.ph] if self.facing_r else self._frames[self.ph]
            img = _stun_frames[int(self.anim_t) % len(_stun_frames)].copy()
            img.fill((85,85,85,255), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(img, (sx + random.randint(-2,2), sy + 14))
            btn = "Y" if using_gamepad else pygame.key.name(meta['binds']['atk']).upper()
            draw_text(surf,f"EXECUTE [{btn}]",F_MED,C_RED,sx+55,sy-32,center=True); return
        if self.phase_flash>0: fs=pygame.Surface(self.rect.size,pygame.SRCALPHA); fs.fill((*C_RED,int(180*self.phase_flash/80))); surf.blit(fs,(sx,sy))
        if self.hit_timer>0 and int(self.hit_timer)%4<2: return
        
        fi=int(self.anim_t)%len(self._frames[self.ph])
        img = self._frames_l[self.ph][fi] if self.facing_r else self._frames[self.ph][fi]
        surf.blit(img,(sx,sy))
        
        if self.melee_a>0:
            prog = 1.0 - (self.melee_a / 18.0); ang_deg = (-30 + 130 * prog) if self.facing_r else (30 - 130 * prog); pivot = pygame.Surface((240, 240), pygame.SRCALPHA); pivot.blit(self._weapon, (120 - 15, 120 - 120)); rot = pygame.transform.rotate(pivot, -ang_deg); hx = self.rect.centerx - int(cx) + (30 if self.facing_r else -30); hy = self.rect.centery; surf.blit(rot, (hx - rot.get_width()//2, hy - rot.get_height()//2))

class Player:
    DASH_DUR=9; ATK_CD=20; PARRY_MAX_CD=40; BLINK_MAX=1200; ULT_DUR=28; PARRY_ACTIVE=14
    CLEAVE_DUR=12; CLEAVE_MAX_CD=480 # 8 seconds
    
    def __init__(self, x, y):
        self.pos=pygame.Vector2(x,y); self.vel=pygame.Vector2(0,0)
        self.max_hp=max(1,meta["upg_max_hp"]+run_hp_bonus()); self.hp=self.max_hp
        self.max_mana=100.0; self.mana=self.max_mana; self.mana_regen=5.0 * (0.3 if curse_active("mana_drain") else 1.0)
        self.target_h=72; self.rect=pygame.Rect(x,y,42,self.target_h)
        self.alive=True; self.facing_r=True; self.on_ground=False; self.invincible=0; self.crouching=False
        self.dashing=False; self.dash_t=0; self.dash_cd=0; self.dash_dir=pygame.Vector2(1,0); self.dash_charges=2 if run_has("swiftness") else 1
        self.cleaving=False; self.cleave_t=0; self.cleave_cd=0; self.cleave_dir=pygame.Vector2(1,0)
        self.atk_t=0; self.atk_cd=0; self.atk_hit=False; self.is_atk=False; self.atk_facing_r=True
        self.ult_t=0; self.ult_cd=0; self.is_ult=False; self.ult_hit=False; self.ult_facing_r=True
        self.parry_state="none"; self.parry_timer=0; self.parry_cd=0
        self.blink_cd=0; self.shoot_cd=0; self.dj_used=False; self.anim_t=0.0; self.afterimages=[]
        self.stance = "reaper"; self.stance_cd = 0
        self.prev_jump = False; self.prev_r = False
        if curse_active("iron_curse"): self.hp = max(1, self.hp // 2); announce("IRON CURSE — YOU BEGIN WOUNDED", C_DKRED, 160)
        self._build_sprite()

    def _build_sprite(self):
        if _PLAYER_FRAMES_R:
            self._frames_r=_PLAYER_FRAMES_R; self._frames_l=_PLAYER_FRAMES_L; self._base_r=_PLAYER_FRAMES_R[0]; self._base_l=_PLAYER_FRAMES_L[0]
            self.target_h=_PLAYER_FRAMES_R[0].get_height(); self.rect=pygame.Rect(int(self.pos.x),int(self.pos.y),_PLAYER_FRAMES_R[0].get_width(),self.target_h)
        else:
            s=pygame.Surface((42,72),pygame.SRCALPHA); pygame.draw.ellipse(s,(30,15,55,220),(4,10,34,54)); pygame.draw.line(s,(130,130,150,200),(32,0),(22,60),3)
            pygame.draw.arc(s,(180,180,220,220),(18,0,22,16),-math.pi/2,math.pi/2,4); pygame.draw.circle(s,(20,12,38,230),(20,8),9); pygame.draw.circle(s,(20,12,38,230),(20,8),11,2)
            pygame.draw.circle(s,(*C_RUNEGLOW,255),(16,6),2); pygame.draw.circle(s,(*C_RUNEGLOW,255),(24,6),2)
            self._frames_r=[s]; self._frames_l=[pygame.transform.flip(s,True,False)]; self._base_r=s; self._base_l=self._frames_l[0]
        
        self._slash = _SLASH_IMG if _SLASH_IMG else pygame.Surface((35,80),pygame.SRCALPHA)
        if not _SLASH_IMG: 
            pygame.draw.arc(self._slash,(*C_WHITE,210),(0,0,35,80),-math.pi/2,math.pi*0.7,5)
            pygame.draw.circle(self._slash, (*C_BLOOD, 200), (30, 10), 6)
        self._slash_ult=_SLASH_ULT if _SLASH_ULT else self._slash

    def can_pickup_relic(self): return len(run["relics"])<meta["upg_relic_slots"]
    def apply_relic(self, rid):
        if rid=="void_heart": self.max_hp+=2; self.hp=min(self.max_hp,self.hp+2)
        elif rid=="cursed_blade": self.max_hp=max(1,self.max_hp-1); self.hp=min(self.max_hp,self.hp)
        elif rid=="swiftness": self.dash_charges=2

    def sync(self): self.max_hp=max(1,meta["upg_max_hp"]+run_hp_bonus()); self.hp=min(self.hp,self.max_hp)

    def use_trinket(self):
        global time_scale, bullet_time_timer, kill_streak, player_trinket
        if player_trinket is None: return
        d=TRINKET_DEFS[player_trinket]; announce(f"USED: {d['name']} — {d['desc']}", d["color"], 120)
        if player_trinket=="time_shard": time_scale=0.22; bullet_time_timer=300
        elif player_trinket=="soul_bomb":
            killed=0
            for e in enemies:
                if e.alive and not isinstance(e,(Seraph,Boss,Wraith,TrainingDummy)) or (isinstance(e, Wraith) and not getattr(e, 'is_boss', False)): e.hp=0; e.alive=False; spawn_particles(e.rect.centerx,e.rect.centery,12,[C_PURPLE,C_WHITE],speed=4); killed+=1
            if killed>0:
                run["kills"]+=killed; meta["total_kills"]+=killed
                for _ in range(killed): essence_drops.append(EssenceDrop(self.rect.centerx,self.rect.centery,1))
        elif player_trinket=="essence_jar": meta["divine_essence"]+=30
        elif player_trinket=="relic_shard":
            pool=[k for k in RELIC_DEFS if k not in run["relics"]+run["relic_offered"]]
            if pool and self.can_pickup_relic(): rid=random.choice(pool); run["relics"].append(rid); self.apply_relic(rid); announce(f"RELIC SHARD: {RELIC_DEFS[rid]['name']}!",RELIC_DEFS[rid]["color"],160)
        audio.play("relic",0.9); player_trinket=None

    def take_damage(self):
        if self.invincible>0 or not self.alive: return
        if run_has("iron_will") and not run["iron_will_used"] and self.hp==1: run["iron_will_used"]=True; announce("IRON WILL — LETHAL BLOW NEGATED!",C_WHITE,120); spawn_particles(self.rect.centerx,self.rect.centery,22,[C_WHITE,C_GOLD],speed=5); self.invincible=90; return
        if self.dashing and self.dash_t >= (self.DASH_DUR - 4):
            global time_scale, bullet_time_timer
            time_scale = 0.28; bullet_time_timer = 65
            self.invincible = max(self.invincible, self.DASH_DUR + 12)
            spawn_particles(self.rect.centerx, self.rect.centery, 20,
                            [C_CYAN, C_WHITE, C_PURPLE], speed=5, gravity=-0.05)
            add_combo(2)
            return
        audio.play("hit",0.8)
        global combo_count, combo_timer, kill_streak; combo_count=0; combo_timer=0; kill_streak=0
        _talisman_on_player_hit()
        
        self.hp-=1; self.invincible=65 
        spawn_particles(self.rect.centerx, self.rect.centery, 45, [C_RED, C_DKRED, C_WHITE, C_STONE], speed=8, gravity=0.5, sz=(3,8), life=(15,35))
        if self.hp<=0: self.alive=False; _record_run_history(); save_meta()

    def _execution(self, enemy):
        global hit_stop_timer; hit_stop_timer=16.0
        self.pos.x=enemy.rect.centerx-self.rect.w//2; self.rect.x=int(self.pos.x); self.invincible=32; audio.play("slash",1.0)
        spawn_particles(enemy.rect.centerx,enemy.rect.centery,55,[C_RED,C_WHITE,C_GOLD,C_CYAN],speed=11,sz=(3,10))
        enemy.take_damage(15 if isinstance(enemy,Boss) else 10,self.rect.centerx,unblockable=True)
        if enemy.alive and hasattr(enemy,'stagger_meter'): enemy.stagger_meter=0; enemy.state="hover" if hasattr(enemy,'_fire') else "active"
        if self.hp<self.max_hp: self.hp+=1
        self.mana=min(self.max_mana,self.mana+35); add_combo(6)

    def _start_dash(self, keys, pad_dx=0, pad_dy=0):
        if getattr(self, "dash_charges", 1) <= 0: return
        self.dash_charges -= 1
        if self.dash_cd <= 0: self.dash_cd = meta["upg_dash_cd"]
        
        dx, dy = pad_dx, pad_dy
        if dx == 0 and dy == 0:
            dx = (1 if key_pressed(keys, "right") else (-1 if key_pressed(keys, "left") else 0))
            dy = (-1 if key_pressed(keys, "up")   else (1  if key_pressed(keys, "down") else 0))
        if dx == 0 and dy == 0: dx = 1 if self.facing_r else -1
        ln = max(1, math.hypot(dx, dy))
        self.dash_dir = pygame.Vector2(dx / ln, dy / ln)

        if talisman_active("phantom"):
            dist = 200 
            self.pos.x += self.dash_dir.x * dist
            self.pos.y += self.dash_dir.y * dist
            self.pos.y = min(self.pos.y, GROUND_Y - self.rect.h)
            self.rect.topleft = (int(self.pos.x), int(self.pos.y))
            void_tears.append(VoidTear(self.rect.centerx, self.rect.centery, C_PURPLE))
            spawn_particles(self.rect.centerx, self.rect.centery, 18, [C_PURPLE, C_CYAN, C_RUNEGLOW], speed=5, gravity=-0.05)
            _phantom_targets = [e for e in enemies if e.alive]
            if boss_obj and boss_obj.alive: _phantom_targets.append(boss_obj)
            for _pe in _phantom_targets:
                if math.hypot(_pe.rect.centerx-self.rect.centerx, _pe.rect.centery-self.rect.centery) < 80:
                    _pe.take_damage(3, self.rect.centerx, unblockable=True)
                    spawn_particles(_pe.rect.centerx, _pe.rect.centery, 10, [C_PURPLE, C_WHITE], speed=4)
            self.dashing = False
            self.dash_t  = 0
            self.dash_cd = int(meta["upg_dash_cd"] * 1.5)
            return

        self.dashing  = True; self.dash_t  = self.DASH_DUR
        self.invincible = self.DASH_DUR + 5

        self.dash_cd = meta["upg_dash_cd"]
        for _ in range(3):
            self.afterimages.append(
                Afterimage(self._base_r if self.facing_r else self._base_l, self.rect.x, self.rect.y))

    def _do_blink(self, pad_aim_x, pad_aim_y, cam_x):
        if self.blink_cd>0: return
        audio.play("blink",0.7)
        
        if using_gamepad and (abs(pad_aim_x) > 0.2 or abs(pad_aim_y) > 0.2):
            dx, dy = pad_aim_x * self.BLINK_MAX, pad_aim_y * self.BLINK_MAX
        else:
            mx,my=get_mouse_pos(cam_x); dx,dy=mx-self.rect.centerx,my-self.rect.centery
            
        d=math.hypot(dx,dy)
        if d>self.BLINK_MAX: dx,dy=dx*(self.BLINK_MAX/d),dy*(self.BLINK_MAX/d)
        
        void_tears.append(VoidTear(self.rect.centerx,self.rect.centery,C_PURPLE)); spawn_particles(self.rect.centerx,self.rect.centery,18,[C_PURPLE,C_CYAN,C_RUNEGLOW],speed=5,gravity=-0.05)
        self.pos.x+=dx-self.rect.w//2; self.pos.y=min(self.pos.y+dy,GROUND_Y-self.rect.h); self.rect.topleft=(int(self.pos.x),int(self.pos.y))
        void_tears.append(VoidTear(self.rect.centerx,self.rect.centery,C_CYAN)); spawn_particles(self.rect.centerx,self.rect.centery,18,[C_CYAN,C_PURPLE,C_WHITE],speed=5,gravity=-0.05)
        for _ in range(3): self.afterimages.append(Afterimage(self._base_r if self.facing_r else self._base_l,self.rect.x,self.rect.y))
        self.blink_cd=130; self.invincible=max(self.invincible,14); radius=180 if run_has("void_echo") else 110
        dmg=int(((4 if run_has("void_echo") else 2)+run_atk_bonus())*run_dmg_mult()); targets=[e for e in enemies if e.alive]
        if boss_obj and boss_obj.alive: targets.append(boss_obj)
        hit_any=False; synergy_active=run_has("plague_touch") and run_has("void_echo")
        for e in targets:
            if math.hypot(e.rect.centerx-self.rect.centerx,e.rect.centery-self.rect.centery)<radius:
                e.take_damage(dmg+(1 if isinstance(e,Grunt) else 0),self.rect.centerx,unblockable=True)
                spawn_particles(e.rect.centerx,e.rect.centery,14,[C_PURPLE,C_CYAN,C_RUNEGLOW],speed=5); hit_any=True
                if synergy_active: e.poison_timer=200; e.fast_poison=True
        if hit_any:
            add_combo(1)
            if synergy_active: announce("VOID PLAGUE — ACCELERATED TOXIN!",C_PLAGUE,90)

    def _atk_damage(self):
        hb=pygame.Rect(0,0,88,95)
        if self.atk_facing_r: hb.midleft=self.rect.center
        else: hb.midright=self.rect.center
        hit=False; dmg=int((3+run_atk_bonus())*run_dmg_mult())
        if self.stance == "executioner": dmg *= 2
        if talisman_active("bloodpact"): dmg += 2
        targets=[e for e in enemies if e.alive]
        if boss_obj and boss_obj.alive: targets.append(boss_obj)
        for e in targets:
            if hb.colliderect(e.rect):
                instastun = _talisman_on_player_hit_enemy(e)
                e.take_damage(dmg,self.rect.centerx)
                if instastun and hasattr(e, 'state') and e.alive:
                    e.state = "stunned"; e.stun_t = 200; e.stagger_meter = 0
                    spawn_particles(e.rect.centerx, e.rect.centery, 20, [C_GOLD, C_WHITE, C_YELLOW], speed=6, gravity=-0.05)
                    announce("ECLIPSE STRIKE — ENEMY STUNNED!", C_GOLD, 100)
                if run_has("plague_touch") and hasattr(e,'poison_timer'): e.poison_timer=200
                spawn_particles(e.rect.centerx,e.rect.centery,12 if isinstance(e,Seraph) else 9,[C_GOLD if isinstance(e,Seraph) else C_RUNEGLOW,C_WHITE],speed=4); hit=True
        if hit: add_combo(1); self.mana=min(self.max_mana,self.mana+12)

    def _ult_damage(self):
        global hit_stop_timer, time_scale, bullet_time_timer
        hb=pygame.Rect(0,0,1200,600)
        hb.center=self.rect.center
        dmg=int((25+run_atk_bonus())*run_dmg_mult())
        targets=[e for e in enemies if e.alive]
        if boss_obj and boss_obj.alive: targets.append(boss_obj)
        hit_any=False
        for e in targets:
            if hb.colliderect(e.rect):
                e.take_damage(dmg,self.rect.centerx,unblockable=True)
                spawn_particles(e.rect.centerx,e.rect.centery,40,[C_RED,C_DKRED,C_WHITE],speed=9)
                void_tears.append(VoidTear(e.rect.centerx,e.rect.centery,C_RED))
                hit_any=True
        if hit_any:
            hit_stop_timer=12.0; time_scale=0.15; bullet_time_timer=120
            announce("SOUL REND!",C_DKRED,150)
        add_combo(10)

    def try_parry(self, proj_lists):
        if self.parry_state != "active": return
        pb=pygame.Rect(0,0,76,76); pb.centery=self.rect.centery
        if self.facing_r: pb.midleft=self.rect.midright
        else: pb.midright=self.rect.midleft
        for plist in proj_lists:
            for p in plist:
                if not p.alive or p.parried: continue
                if pb.collidepoint(p.pos.x,p.pos.y):
                    p.deflect(); self.invincible=max(self.invincible,22)
                    spawn_parry_vfx(self.rect.centerx, self.rect.centery, self.facing_r); spawn_particles(int(p.pos.x),int(p.pos.y),18,[C_CYAN,C_WHITE,C_GOLD],speed=5,gravity=-0.05)
                    add_combo(1); self.mana=min(self.max_mana,self.mana+15)
                    if curse_active("parry_boon"): self.mana=self.max_mana
                    _on_successful_parry()

    def update(self, keys, pad_inputs, cam_x, dt):
        if not self.alive: return
        self.sync()
        if not talisman_active("bloodpact"):
            self.mana = min(self.max_mana,
                self.mana + ((self.mana_regen *
                    (0.3 if curse_active("mana_drain") else 1.0)) * (dt / 60.0)))
                    
        for attr in ['invincible','dash_cd','blink_cd','parry_cd','ult_cd','shoot_cd','atk_cd', 'stance_cd', 'cleave_cd']: 
            v=getattr(self,attr,0); setattr(self,attr,max(0,v-dt)) if v>0 else None

        max_dashes = 2 if run_has("swiftness") else 1
        if not hasattr(self, "dash_charges"): self.dash_charges = max_dashes
        if self.dash_charges < max_dashes and self.dash_cd <= 0:
            self.dash_charges += 1
            if self.dash_charges < max_dashes:
                self.dash_cd = meta["upg_dash_cd"]

        if self.parry_state == "active":
            self.parry_timer -= dt
            if self.parry_timer <= 0: self.parry_state = "none"; self.parry_cd = self.PARRY_MAX_CD

        if (key_pressed(keys, "trinket") or pad_inputs.get("trinket")) and player_trinket is not None: self.use_trinket()
        
        curr_r = (key_pressed(keys, "flask") or pad_inputs.get("flask"))
        if curr_r and not self.prev_r and run.get("flasks", 0) > 0 and self.hp < self.max_hp:
            run["flasks"] -= 1; self.hp = self.max_hp
            spawn_particles(self.rect.centerx, self.rect.centery, 30, [C_RED, C_HOLY, C_WHITE], speed=5, gravity=-0.1)
            audio.play("levelup", 0.7); announce(f"FLASK USED! ({run['flasks']} LEFT)", C_RED, 120)
        self.prev_r = curr_r
        
        if (key_pressed(keys, "stance") or pad_inputs.get("stance")) and self.stance_cd <= 0:
            self.stance = "executioner" if self.stance == "reaper" else "reaper"
            self.stance_cd = 30; announce(f"{self.stance.upper()} STANCE ENGAGED", C_RED if self.stance=="executioner" else C_CYAN, 90)

        eff_atk_cd = self.ATK_CD * (2.0 if self.stance == "executioner" else 1.0)
        if (key_pressed(keys, "atk") or pad_inputs.get("atk") or pygame.mouse.get_pressed()[0]) and not self.is_atk and not self.is_ult and not self.cleaving and self.atk_cd<=0:
            executed=False; check=[e for e in enemies if getattr(e,'state','')=="stunned"]
            if boss_obj and getattr(boss_obj,'state','')=="stunned": check.append(boss_obj)
            for e in check:
                if math.hypot(e.rect.centerx-self.rect.centerx,e.rect.centery-self.rect.centery)<105: self._execution(e); self.atk_cd=eff_atk_cd; executed=True; break
            if not executed:
                self.is_atk=True; self.atk_t=float(eff_atk_cd); self.atk_hit=False; self.atk_facing_r=self.facing_r
                spawn_particles(self.rect.right if self.facing_r else self.rect.left,self.rect.centery,10,[C_PARCH,C_WHITE],speed=5); audio.play("slash",0.6)
                if combo_rank()[0] in ("S","S+"): player_projs.append(Proj(self.rect.centerx,self.rect.centery,10 if self.facing_r else -10,0,C_PURPLE,14,speed=8,shooter=self,ptype="player_wave",damage=int((2+run_atk_bonus())*run_dmg_mult()),piercing=True))

        if self.is_atk:
            self.atk_t-=dt
            if not self.atk_hit and self.atk_t<=eff_atk_cd*0.55: self.atk_hit=True; self._atk_damage()
            if self.atk_t<=0: self.is_atk=False; self.atk_cd=eff_atk_cd

        # ULT only in REAPER stance
        if (key_pressed(keys, "ult") or pad_inputs.get("ult")) and meta["upg_ult"] and not self.is_ult and not self.is_atk and not self.cleaving and self.ult_cd<=0 and self.stance == "reaper":
            self.is_ult=True; self.ult_t=float(self.ULT_DUR); self.ult_hit=False; self.ult_facing_r=self.facing_r; audio.play("slash",0.9)
            spawn_particles(self.rect.centerx,self.rect.centery,28,[C_RED,C_ORANGE,C_GOLD],speed=8)

        if self.is_ult:
            self.ult_t-=dt
            if not self.ult_hit and self.ult_t<=self.ULT_DUR*0.45: self.ult_hit=True; self._ult_damage()
            if self.ult_t<=0: self.is_ult=False; self.ult_cd=meta.get("upg_ult_cd",600)

        # ABYSSAL TEAR (Cleave rework) only in EXECUTIONER stance
        if (key_pressed(keys, "cleave") or pad_inputs.get("cleave")) and not self.cleaving and not self.dashing and self.cleave_cd <= 0 and self.stance == "executioner":
            if self.is_atk: self.is_atk=False; self.atk_t=0; self.atk_cd=int(eff_atk_cd*0.5)
            self.cleave_cd = self.CLEAVE_MAX_CD
            self.cleaving = True
            self.cleave_t = self.CLEAVE_DUR
            self.invincible = self.CLEAVE_DUR + 10
            
            dx, dy = pad_inputs.get("dir_x", 0), pad_inputs.get("dir_y", 0)
            if dx == 0 and dy == 0:
                dx = (1 if key_pressed(keys, "right") else (-1 if key_pressed(keys, "left") else 0))
                dy = (-1 if key_pressed(keys, "up")   else (1  if key_pressed(keys, "down") else 0))
            if dx == 0 and dy == 0: dx = 1 if self.facing_r else -1
            ln = max(1, math.hypot(dx, dy))
            self.cleave_dir = pygame.Vector2(dx / ln, dy / ln)
            
            audio.play("dash", 0.8)
            abyssal_tears.append(AbyssalTear(self.rect.centerx, self.rect.centery))
            announce("— ABYSSAL TEAR —", C_PURPLE, 120)

        if self.cleaving:
            self.cleave_t -= dt
            if int(self.cleave_t) % 2 == 0:
                self.afterimages.append(Afterimage(self._base_r if self.facing_r else self._base_l, self.rect.x, self.rect.y))
            
            spawn_particles(self.rect.centerx, self.rect.centery, 3, [(50, 0, 10), (10, 0, 30), (90, 0, 20)], speed=1, sz=(3, 6), life=(8, 18))
            
            if self.cleave_t <= 0:
                self.cleaving = False
            
            self.pos += self.cleave_dir * (400/self.CLEAVE_DUR) * dt
            self.rect.topleft = (int(self.pos.x), int(self.pos.y))
            if self.rect.bottom > GROUND_Y: self.rect.bottom = GROUND_Y; self.pos.y = float(self.rect.y)
            return

        if (key_pressed(keys, "bolt") or pad_inputs.get("bolt")) and self.shoot_cd<=0 and not self.dashing and not self.is_ult and not self.cleaving:
            runebound = talisman_active("runebound")
            mana_cost = 0 if runebound else 25
            if self.mana >= mana_cost:
                if not runebound: self.mana -= mana_cost
                
                pad_aim_x, pad_aim_y = pad_inputs.get("aim_x", 0), pad_inputs.get("aim_y", 0)
                if using_gamepad and (abs(pad_aim_x) > 0.2 or abs(pad_aim_y) > 0.2):
                    ang = math.atan2(pad_aim_y, pad_aim_x)
                else:
                    mx,my=get_mouse_pos(cam_x); ang=math.atan2(my-self.rect.centery,mx-self.rect.centerx)
                    
                is_poison=run_has("plague_touch")
                global _talisman_runebound_count
                _talisman_runebound_count = (_talisman_runebound_count + 1) if runebound else 0
                is_runic = runebound and (_talisman_runebound_count % 4 == 0)
                dmg_mult = 2 if is_runic else 1
                bolt_color = C_RUNEGLOW if is_runic else (C_PLAGUE if is_poison else C_PURPLE)
                bolt_r = 10 if is_runic else 6
                player_projs.append(Proj(
                    self.rect.centerx, self.rect.centery,
                    math.cos(ang)*12, math.sin(ang)*12,
                    bolt_color, bolt_r,
                    homing=is_runic,
                    target=min([e for e in enemies if e.alive] + ([boss_obj] if boss_obj and boss_obj.alive else []),
                               key=lambda e: math.hypot(e.rect.centerx-self.rect.centerx, e.rect.centery-self.rect.centery),
                               default=None) if is_runic else None,
                    shooter=self, ptype="player_bolt",
                    damage=int((2+run_atk_bonus())*run_dmg_mult()*dmg_mult),
                    poison=is_poison
                ))
                if is_runic:
                    spawn_particles(self.rect.centerx, self.rect.centery, 12, [C_RUNEGLOW, C_WHITE, C_CYAN], speed=5, gravity=-0.05)
                    announce("RUNIC BOLT!", C_RUNEGLOW, 60)
                audio.play("slash", 0.65 if is_runic else 0.45); self.shoot_cd=28

        if (pygame.mouse.get_pressed()[2] or pad_inputs.get("parry")) and self.parry_cd<=0 and not self.is_atk and self.parry_state=="none":
            self.parry_state="active"; self.parry_timer= meta.get("upg_parry_window", 14) / (2 if self.stance == "executioner" else 1)
            self.parry_cd=self.PARRY_MAX_CD; spawn_particles(self.rect.centerx, self.rect.centery, 5, [C_CYAN, C_WHITE], speed=2)

        if (key_pressed(keys, "blink") or pad_inputs.get("blink")) and meta["upg_blink"] and self.blink_cd<=0 and not self.dashing and not self.cleaving: 
            self._do_blink(pad_inputs.get("aim_x", 0), pad_inputs.get("aim_y", 0), cam_x)

        if (key_pressed(keys, "dash") or pad_inputs.get("dash")) and not self.dashing and getattr(self, "dash_charges", 1) > 0 and not self.cleaving:
            if self.is_atk: self.is_atk=False; self.atk_t=0; self.atk_cd=int(eff_atk_cd*0.5)
            self._start_dash(keys, pad_inputs.get("dir_x", 0), pad_inputs.get("dir_y", 0)); audio.play("dash",0.6)

        if self.dashing:
            self.dash_t -= dt
            if int(self.dash_t) % 2 == 0:
                self.afterimages.append(
                    Afterimage(self._base_r if self.facing_r else self._base_l, self.rect.x, self.rect.y))
            spawn_particles(self.rect.centerx, self.rect.centery, 3,
                            [C_PURPLE, C_CYAN, C_RUNEGLOW], speed=3,
                            gravity=-0.05, sz=(2, 5), life=(4, 12))

            if self.dash_t <= 0:
                self.dashing = False
                self.invincible = max(self.invincible, 8)

        for ai in self.afterimages: ai.update()
        self.afterimages=[ai for ai in self.afterimages if ai.alive]

        if self.dashing:
            self.pos+=self.dash_dir*(360/self.DASH_DUR)*dt; self.rect.topleft=(int(self.pos.x),int(self.pos.y))
            if self.rect.bottom>GROUND_Y: self.rect.bottom=GROUND_Y; self.pos.y=float(self.rect.y)
            return

        old_bottom=self.rect.bottom; self.crouching=(key_pressed(keys, "down") or safe_key(keys, pygame.K_LCTRL) or safe_key(keys, pygame.K_RCTRL) or pad_inputs.get("dir_y", 0) > 0.7); self.rect.height=self.target_h//2 if self.crouching else self.target_h; self.rect.bottom=old_bottom; self.pos.y=float(self.rect.y)

        mx=0
        if not self.crouching:
            move_spd=4.8*(1.2 if combo_rank()[0] in ("S","S+") else 1.0)*dt
            pad_dx = pad_inputs.get("dir_x", 0)
            if key_pressed(keys, "left") or pad_dx < -0.3: mx-=move_spd; self.facing_r=False
            if key_pressed(keys, "right") or pad_dx > 0.3: mx+=move_spd; self.facing_r=True

        self.pos.x+=mx; self.rect.x=int(self.pos.x)
        for px,py,pw in platforms:
            pr=pygame.Rect(px,py,pw,20)
            if self.rect.colliderect(pr):
                if mx>0: self.rect.right=pr.left
                if mx<0: self.rect.left=pr.right
                self.pos.x=float(self.rect.x)

        self.vel.y=min(self.vel.y+0.78*dt,20); self.pos.y+=self.vel.y*dt; self.rect.y=int(self.pos.y); self.on_ground=False
        if self.rect.bottom>=GROUND_Y:
            self.rect.bottom=GROUND_Y; self.pos.y=float(self.rect.y); self.vel.y=0; self.on_ground=True; self.dj_used=False

        for px,py,pw in platforms:
            pr=pygame.Rect(px,py,pw,20)
            if self.rect.colliderect(pr):
                if self.vel.y>0: self.rect.bottom=pr.top; self.vel.y=0; self.on_ground=True; self.dj_used=False
                elif self.vel.y<0: self.rect.top=pr.bottom; self.vel.y=0
                self.pos.y=float(self.rect.y)

        curr_jump = (key_pressed(keys, "jump") or pad_inputs.get("jump"))
        if curr_jump and not self.prev_jump:
            if self.on_ground: self.vel.y=-15.5
            elif meta["upg_double_jump"] and not self.dj_used: self.vel.y=-14.0; self.dj_used=True; spawn_particles(self.rect.centerx,self.rect.bottom,10,[C_PURPLE,C_CYAN],speed=3,direction=math.pi/2,spread=math.pi/2,gravity=-0.1)
        self.prev_jump = curr_jump
        
        if mx!=0: self.anim_t=(self.anim_t+abs(mx)*0.055)%4

    def draw(self, surf, cx):
        for ai in self.afterimages: ai.draw(surf,cx)
        if self.invincible>0 and not self.dashing and not self.cleaving and int(self.invincible)%6<3: return

        vy=self.rect.y; fi=int(self.anim_t)%len(self._frames_r); img=self._frames_r[fi] if self.facing_r else self._frames_l[fi]
        if self.crouching: img=pygame.transform.scale(img,(img.get_width(),img.get_height()//2))
        surf.blit(img,(self.rect.x-int(cx),vy))

        if self.parry_state == "active":
            rot = pygame.transform.rotate(self._slash, -30 if self.facing_r else 30)
            px = self.rect.centerx - int(cx) + (12 if self.facing_r else -12)
            surf.blit(rot, (px - rot.get_width()//2, self.rect.centery - rot.get_height()//2))

        if self.is_atk and self.parry_state != "active":
            eff_atk_cd = self.ATK_CD * (2.0 if self.stance == "executioner" else 1.0)
            prog=1.0-(self.atk_t/eff_atk_cd); ang=(-65+88*prog) if self.atk_facing_r else (245-88*prog)
            rot=pygame.transform.rotate(self._slash,ang if not self.atk_facing_r else -ang)
            if self.stance == "executioner": rot.fill((255,50,50,255), special_flags=pygame.BLEND_RGBA_MULT)
            rot.set_alpha(255 if prog<0.65 else int(255*(1-prog)/0.35))
            surf.blit(rot,(self.rect.centerx-int(cx)+(18 if self.atk_facing_r else -18)-rot.get_width()//2,self.rect.centery-rot.get_height()//2))

        if self.is_ult:
            prog=1.0-(self.ult_t/self.ULT_DUR); sf=8.0+math.sin(prog*math.pi)*3.0; base_slash=self._slash_ult; sw2,sh2=int(max(1,base_slash.get_width()*sf)),int(max(1,base_slash.get_height()*sf))
            big=pygame.transform.smoothscale(base_slash,(sw2,sh2)).copy(); big.fill((255,10,10,255),special_flags=pygame.BLEND_RGBA_MULT)
            ang2=(-95+150*prog) if self.ult_facing_r else (275-150*prog); rot2=pygame.transform.rotate(big if self.ult_facing_r else pygame.transform.flip(big,True,False),-ang2); rot2.set_alpha(255 if prog<0.65 else int(255*(1-prog)/0.35))
            surf.blit(rot2,(self.rect.centerx-int(cx)+(80 if self.ult_facing_r else -80)-rot2.get_width()//2,self.rect.centery-rot2.get_height()//2))

    def draw_hud(self, surf):
        # Top-Left HUD Overhaul - Sleek dark-translucent backing panel
        bw, bh, bx, by = 340, 20, 30, 30
        panel_w = 400
        panel_h = 240 + (35 if active_talismans else 0)
        
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 12, 22, 180), (0, 0, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(panel, (60, 55, 72, 220), (0, 0, panel_w, panel_h), 2, border_radius=8)
        surf.blit(panel, (bx - 10, by - 10))

        # Minimalist aligned bars for HP/Mana
        # HP Bar
        pygame.draw.rect(surf, (30, 15, 20), (bx, by, bw, bh), border_radius=4)
        if self.hp > 0:
            pct = self.hp / self.max_hp
            c = (int(195*(1-pct)+35*pct), int(35*pct), int(35*pct))
            pygame.draw.rect(surf, c, (bx, by, int(bw*pct), bh), border_radius=4)
        for i in range(1, self.max_hp):
            lx = bx + int(i*(bw/self.max_hp))
            pygame.draw.line(surf, (40, 25, 30), (lx, by), (lx, by+bh), 1)
        draw_text(surf, f"{self.hp}/{self.max_hp}", F_SM, C_WHITE, bx + bw + 10, by - 2)

        # Mana Bar
        mana_y = by + bh + 10
        pygame.draw.rect(surf, (15, 25, 40), (bx, mana_y, bw, 12), border_radius=3)
        if self.mana > 0:
            m_pct = self.mana / self.max_mana
            pygame.draw.rect(surf, C_CYAN, (bx, mana_y, int(bw*m_pct), 12), border_radius=3)
        draw_text(surf, f"{int(self.mana)}", F_TINY, C_CYAN, bx + bw + 10, mana_y - 2)

        # Info Row
        info_y = mana_y + 25
        draw_text(surf, f"FL {run['floor']}", F_SM, C_GREY, bx, info_y)
        draw_text(surf, f"KILLS {run['kills']}", F_SM, C_GREY, bx + 100, info_y)
        draw_text(surf, f"✦ {meta['divine_essence']}", F_SM, C_CYAN, bx + 220, info_y)
        if meta.get("curse_level",0)>0:
            draw_text(surf, f"NG+{meta['curse_level']}", F_SM, C_RED, bx + 320, info_y)

        # Relics Row
        relic_y = info_y + 30
        for i, rid in enumerate(run["relics"]):
            d = RELIC_DEFS[rid]
            rx, ry = bx + i*34, relic_y
            chip = pygame.Rect(rx, ry, 28, 28)
            pygame.draw.rect(surf, (20, 15, 30), chip, border_radius=4)
            pygame.draw.rect(surf, d["color"], chip, 1, border_radius=4)
            ic = F_SM.render(d["icon"], True, d["color"])
            surf.blit(ic, (rx + 14 - ic.get_width()//2, ry + 14 - ic.get_height()//2))

        # Talismans
        tali_y = relic_y + 40
        if active_talismans:
            for ti, tkey in enumerate(active_talismans):
                td = TALISMAN_DEFS[tkey]
                tr = pygame.Rect(bx + ti * 120, tali_y, 110, 26)
                bg3 = pygame.Surface((110, 26), pygame.SRCALPHA)
                bg3.fill((*td["color"], 30)); surf.blit(bg3, tr.topleft)
                pygame.draw.rect(surf, td["color"], tr, 1, border_radius=3)
                lbl3 = F_TINY.render(f"{td['icon']} {td['short']}", True, td["color"])
                surf.blit(lbl3, (tr.x + 6, tr.y + 5))
            tali_y += 35

        # Grouped Square Icons (Flask, Trinket)
        grp_y = tali_y
        sq = 36; sp = 8
        # Trinket
        tx = bx
        tri_rect = pygame.Rect(tx, grp_y, sq, sq)
        pygame.draw.rect(surf, (20, 15, 30), tri_rect, border_radius=4)
        if player_trinket:
            d2 = TRINKET_DEFS[player_trinket]
            pygame.draw.rect(surf, d2["color"], tri_rect, 2, border_radius=4)
            ic2 = F_SM.render(d2["icon"], True, d2["color"])
            surf.blit(ic2, (tx + sq//2 - ic2.get_width()//2, grp_y + sq//2 - ic2.get_height()//2))
        else:
            pygame.draw.rect(surf, C_GREY, tri_rect, 1, border_radius=4)
        
        btn_txt = "START" if using_gamepad else pygame.key.name(meta["binds"]["trinket"]).upper()
        tri_lbl = F_TINY.render(f"[{btn_txt}] TRN", True, C_GREY); surf.blit(tri_lbl, (tx, grp_y - 15))

        # Flasks
        fx = tx + sq + sp + max(20, tri_lbl.get_width() - sq)
        fl_rect = pygame.Rect(fx, grp_y, sq, sq)
        pygame.draw.rect(surf, (20, 15, 30), fl_rect, border_radius=4)
        pygame.draw.rect(surf, C_RED if run.get("flasks",0)>0 else C_GREY, fl_rect, 2, border_radius=4)
        fl_lbl = F_SM.render(str(run.get("flasks", 0)), True, C_RED)
        surf.blit(fl_lbl, (fx + sq//2 - fl_lbl.get_width()//2, grp_y + sq//2 - fl_lbl.get_height()//2))
        
        btn_txt = "X" if using_gamepad else pygame.key.name(meta["binds"]["flask"]).upper()
        flt = F_TINY.render(f"[{btn_txt}] FLK", True, C_RED); surf.blit(flt, (fx, grp_y - 15))

        # --- BOTTOM CENTER ATTACKS GUI ---
        abilities = []
        parry_col = C_GOLD if self.parry_state=="active" else C_WHITE
        
        def get_lbl(action, gp_str):
            if using_gamepad: return gp_str
            code = meta["binds"].get(action)
            return pygame.key.name(code).upper()[:3] if code is not None else "RMB"
            
        abilities.append((get_lbl("dash", "RB"), "DSH", self.dash_cd, meta["upg_dash_cd"], C_CYAN))
        abilities.append((get_lbl("parry", "LB"), "PRY", self.parry_cd, self.PARRY_MAX_CD, parry_col))
        abilities.append((get_lbl("bolt", "B"), "BLT", self.shoot_cd, 28, C_PURPLE))
        if meta["upg_blink"]: abilities.append((get_lbl("blink", "LT"), "BLK", self.blink_cd, 130, C_RUNEGLOW))
        if meta["upg_ult"] and self.stance == "reaper": abilities.append((get_lbl("ult", "RT"), "ULT", self.ult_cd, 600, C_RED))
        if self.stance == "executioner": abilities.append((get_lbl("cleave", "R-CLICK"), "CLV", self.cleave_cd, self.CLEAVE_MAX_CD, C_RED))
        
        ab_sq = 44; ab_sp = 25
        total_w = len(abilities) * ab_sq + (len(abilities) - 1) * ab_sp
        start_x = WIDTH // 2 - total_w // 2
        start_y = HEIGHT - 85
        
        for i, (k_lbl, nm, cd, mcd, col) in enumerate(abilities):
            cx2 = start_x + (ab_sq + ab_sp)*i
            bg = pygame.Surface((ab_sq, ab_sq), pygame.SRCALPHA); bg.fill((12,8,20,180)); surf.blit(bg, (cx2, start_y))
            if cd > 0 and mcd > 0: 
                ov = pygame.Surface((ab_sq, int(ab_sq*(cd/mcd))), pygame.SRCALPHA)
                ov.fill((0,0,0,170)); surf.blit(ov, (cx2, start_y + ab_sq - int(ab_sq*(cd/mcd))))
            
            border_col = col if cd<=0 or mcd<=0 else C_GREY
            if nm == "BLT" and self.mana < 25: border_col = C_RED
            pygame.draw.rect(surf, border_col, (cx2, start_y, ab_sq, ab_sq), 2, border_radius=4)
            
            kt = F_TINY.render(k_lbl, True, border_col)
            surf.blit(kt, (cx2 + ab_sq//2 - kt.get_width()//2, start_y - 18))
            
            nt = F_TINY.render(nm, True, border_col)
            surf.blit(nt, (cx2 + ab_sq//2 - nt.get_width()//2, start_y + ab_sq + 4))
            
        st_lbl = "L-CLICK" if using_gamepad else pygame.key.name(meta["binds"]["stance"]).upper()
        draw_text(surf, f"[{st_lbl}] STANCE: {self.stance.upper()}", F_SM, C_RED if self.stance == "executioner" else C_CYAN, WIDTH//2, start_y - 45, center=True)
        # --- END BOTTOM CENTER ---

        if current_floor_curse != "none":
            cd=FLOOR_CURSES[current_floor_curse]; badge=pygame.Rect(WIDTH-260,12,250,34); bg2=pygame.Surface((250,34),pygame.SRCALPHA); bg2.fill((*cd["color"],40)); surf.blit(bg2,badge.topleft)
            pygame.draw.rect(surf,cd["color"],badge,1,border_radius=3); cl=F_TINY.render(f"⚠ {cd['name']}: {cd['desc']}",True,cd["color"]); surf.blit(cl,(badge.x+6,badge.y+9))

        global _save_flash_t
        if _save_flash_t>0: a=min(255,int(255*(_save_flash_t/60))); txt=F_SM.render("✓ GAME SAVED",True,C_PLAGUE); txt.set_alpha(a); surf.blit(txt,(WIDTH-txt.get_width()-22,HEIGHT-50)); _save_flash_t=max(0,_save_flash_t-1)

        if combo_timer>0:
            rnk,rcol=combo_rank(); draw_text(surf,f"RANK {rnk}",F_BIG,rcol,WIDTH-180,36,center=True); cw=110
            pygame.draw.rect(surf,(35,35,45),(WIDTH-180-cw//2,84,cw,5),border_radius=2); pygame.draw.rect(surf,rcol,(WIDTH-180-cw//2,84,int(cw*(combo_timer/COMBO_WINDOW)),5),border_radius=2)
            draw_text(surf,f"×{combo_count}",F_SM,rcol,WIDTH-180,92,center=True)
        if kill_streak>=5: draw_text(surf,f"STREAK  ×{kill_streak}",F_SM,C_RUNEGLOW if kill_streak>=10 else C_ORANGE,WIDTH-180,128,center=True)

class CatCompanion:
    LEAP_CD_MAX     = 720
    RING_CD_MAX     = 480
    GIFT_CD_MAX     = 4800
    RING_RADIUS     = 120

    def __init__(self):
        self.is_champa   = random.choice([True, False])
        self.x           = 200.0
        self.y           = float(GROUND_Y)
        self.col         = (240, 130, 20) if self.is_champa else (35, 35, 40)
        self.name        = "Champa" if self.is_champa else "Pepper"
        self.facing_r    = True
        self.vel_y       = 0.0
        self.anim_t      = 0.0
        self.leap_cd        = random.randint(180, self.LEAP_CD_MAX)
        self.leap_t         = 0
        self.leap_target_x  = 0.0
        self.leap_target_y  = 0.0
        self.hiss_marks     = []
        self.ring_cd        = random.randint(120, self.RING_CD_MAX)
        self.ring_ready     = False
        self.ring_flash     = 0
        self.gift_cd        = random.randint(2400, self.GIFT_CD_MAX)
        self.flash          = 0
        trait = "pounces on enemies & marks them!" if self.is_champa else "shields you from projectiles!"
        announce(f"{self.name} joined you — {trait}", self.col, 140)

    def _champa_try_leap(self, dt):
        self.leap_cd -= dt
        for hm in self.hiss_marks:
            hm["tick_cd"] -= dt
            if hm["tick_cd"] <= 0 and hm["ticks_left"] > 0:
                hm["tick_cd"] = 60
                hm["ticks_left"] -= 1
                if hm["enemy"].alive:
                    hm["enemy"].take_damage(1, hm["enemy"].rect.centerx, unblockable=True)
                    spawn_particles(hm["enemy"].rect.centerx, hm["enemy"].rect.centery, 5,
                                    [C_ORANGE, C_GOLD], speed=3, sz=(2,4), life=(6,14))
        self.hiss_marks = [hm for hm in self.hiss_marks
                           if hm["ticks_left"] > 0 and hm["enemy"].alive]

        if self.leap_t > 0:
            self.leap_t -= dt
            tx, ty = self.leap_target_x, self.leap_target_y
            dx, dy = tx - self.x, ty - self.y
            d = max(1, math.hypot(dx, dy))
            speed = min(d, 14 * dt)
            self.x += dx / d * speed
            self.y += dy / d * speed
            self.facing_r = dx > 0
            if d < 20 or self.leap_t <= 0:
                self.leap_t = 0
                targets = [e for e in enemies if e.alive]
                if boss_obj and boss_obj.alive: targets.append(boss_obj)
                if targets:
                    tgt = min(targets, key=lambda e: math.hypot(e.rect.centerx - self.x, e.rect.centery - self.y))
                    if math.hypot(tgt.rect.centerx - self.x, tgt.rect.centery - self.y) < 90:
                        self.hiss_marks.append({"enemy": tgt, "ticks_left": 6, "tick_cd": 60})
                        spawn_particles(int(self.x), int(self.y), 22,
                                        [C_ORANGE, C_GOLD, C_WHITE], speed=5, gravity=-0.05,
                                        sz=(2,6), life=(8,22))
                        announce("Champa's HISS MARK — 6 extra hits incoming!", C_ORANGE, 90)
                        audio.play("parry", 0.35)
            return

        if self.leap_cd <= 0:
            self.leap_cd = self.LEAP_CD_MAX
            targets = [e for e in enemies if e.alive]
            if boss_obj and boss_obj.alive: targets.append(boss_obj)
            if not targets: return
            tgt = min(targets, key=lambda e: math.hypot(e.rect.centerx - self.x, e.rect.centery - self.y))
            self.leap_target_x = float(tgt.rect.centerx)
            self.leap_target_y = float(tgt.rect.centery)
            self.leap_t = 28

    def _pepper_try_intercept(self, dt):
        self.ring_cd -= dt
        if self.ring_cd <= 0:
            self.ring_cd = self.RING_CD_MAX
            self.ring_ready = True
        if not self.ring_ready or not player or not player.alive:
            return
        all_proj_lists = [e.projs for e in enemies] + ([boss_obj.projs] if boss_obj else [])
        for plist in all_proj_lists:
            for proj in plist:
                if not proj.alive or proj.parried: continue
                dist = math.hypot(proj.pos.x - player.rect.centerx, proj.pos.y - player.rect.centery)
                if dist < self.RING_RADIUS:
                    proj.alive = False
                    self.ring_ready = False
                    self.ring_flash = 40
                    player.mana = min(player.max_mana, player.mana + 10)
                    spawn_particles(int(proj.pos.x), int(proj.pos.y), 18,
                                    [(35,35,40), C_PURPLE, C_WHITE], speed=5,
                                    gravity=-0.05, sz=(2,6), life=(8,22))
                    announce("Pepper blocked it — +10 Mana!", (160, 160, 200), 80)
                    audio.play("parry", 0.5)
                    return

    def update(self, pl, dt):
        if not pl or not pl.alive: return
        self.gift_cd -= dt
        if self.gift_cd <= 0:
            self.gift_cd = self.GIFT_CD_MAX
            essence_drops.append(EssenceDrop(self.x, self.y, 4))
            spawn_particles(int(self.x), int(self.y), 14,
                            [self.col, C_WHITE, C_CYAN], speed=4, gravity=-0.1)
            announce(f"{self.name} found some essence!", self.col, 100)

        if self.is_champa:
            self._champa_try_leap(dt)
        else:
            self._pepper_try_intercept(dt)

        if self.flash > 0: self.flash -= dt
        if self.ring_flash > 0: self.ring_flash -= dt

        if self.leap_t <= 0:
            tx = pl.rect.centerx - (50 if pl.facing_r else -50)
            dx = tx - self.x
            if abs(dx) > 15:
                self.x      += dx * 0.06 * dt
                self.facing_r = dx > 0
                self.anim_t  += 0.25 * dt
            else:
                self.anim_t = 0

            if pl.vel.y < -5 and self.y >= GROUND_Y - 5:
                self.vel_y = -12.5

            self.vel_y  = min(self.vel_y + 0.75 * dt, 18)
            self.y     += self.vel_y * dt
            if self.y >= GROUND_Y: self.y = GROUND_Y; self.vel_y = 0

    def draw(self, surf, cx):
        sx  = int(self.x - cx)
        sy  = int(self.y)
        bob = abs(math.sin(self.anim_t) * 5) if self.anim_t > 0 else 0

        if self.is_champa and self.leap_t > 0:
            trail_alpha = int(160 * (self.leap_t / 28))
            trail = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(trail, (*C_ORANGE, trail_alpha), (10, 10), 9)
            surf.blit(trail, (sx - 10, sy - 25 - bob))

        for hm in self.hiss_marks:
            if hm["enemy"].alive:
                ex = hm["enemy"].rect.centerx - int(cx)
                ey = hm["enemy"].rect.y - 8
                mark = F_TINY.render(f"✦{hm['ticks_left']}", True, C_ORANGE)
                surf.blit(mark, (ex - mark.get_width()//2, ey))

        if not self.is_champa:
            if self.ring_ready and player:
                px = player.rect.centerx - int(cx)
                py = player.rect.centery
                ring_alpha = 30 + int(20 * math.sin(pygame.time.get_ticks() * 0.004))
                ring = pygame.Surface((self.RING_RADIUS*2, self.RING_RADIUS*2), pygame.SRCALPHA)
                pygame.draw.circle(ring, (120, 120, 200, ring_alpha),
                                   (self.RING_RADIUS, self.RING_RADIUS), self.RING_RADIUS, 2)
                surf.blit(ring, (px - self.RING_RADIUS, py - self.RING_RADIUS))
            if self.ring_flash > 0:
                pct = self.ring_flash / 40.0
                burst = pygame.Surface((160, 160), pygame.SRCALPHA)
                for r in [70, 50, 30]:
                    pygame.draw.circle(burst, (120, 120, 200, int(90*pct*(r/70))), (80, 80), r, 3)
                surf.blit(burst, (sx - 80, sy - 95 - bob), special_flags=pygame.BLEND_RGBA_ADD)

        _cat_img = (_CAT_CHAMPA_IMG if self.is_champa else _CAT_PEPPER_IMG)
        if _cat_img:
            ci = _cat_img if self.facing_r else pygame.transform.flip(_cat_img, True, False)
            surf.blit(ci,(sx-ci.get_width()//2, sy-ci.get_height()-bob))
        else:
            pygame.draw.ellipse(surf, self.col, (sx - 12, sy - 15 - bob, 24, 15))
            hx  = sx + (10 if self.facing_r else -10)
            pygame.draw.circle(surf, self.col, (hx, sy - 18 - bob), 9)
            pygame.draw.polygon(surf, self.col, [(hx-7, sy-22-bob), (hx-2, sy-28-bob), (hx-1, sy-20-bob)])
            pygame.draw.polygon(surf, self.col, [(hx+1, sy-20-bob), (hx+2, sy-28-bob), (hx+7, sy-22-bob)])
            eye_col = (255, 165, 0) if self.is_champa else (160, 0, 255)
            pygame.draw.circle(surf, eye_col, (hx+(3 if self.facing_r else -3), sy-20-bob), 2)
            pygame.draw.circle(surf, eye_col, (hx+(7 if self.facing_r else -7), sy-20-bob), 2)
            tail_x = sx - (12 if self.facing_r else -12)
            pygame.draw.line(surf, self.col, (tail_x, sy-10-bob), (tail_x-(8 if self.facing_r else -8), sy-20-bob), 3)

        name_surf = F_TINY.render(self.name, True, self.col)
        surf.blit(name_surf, (sx - name_surf.get_width()//2, sy - 42 - bob))

def _record_run_history():
    hist = meta.get("run_history", []); hist.insert(0, {"floor": run.get("floor", 1), "kills": run.get("kills", 0), "relics": len(run.get("relics", [])), "parries": run.get("parries_this_run", 0), "curse": current_floor_curse})
    meta["run_history"] = hist[:5]; meta["best_floor"] = max(meta.get("best_floor", 0), run.get("floor", 1))

def build_light_layer(torches, doors, cam_x):
    ll=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ll.fill((40,35,55,255) if curse_active("darkness") else (160,150,180,255))
    for t in torches: t.draw_light(ll,cam_x)
    for d in doors: d.draw_light(ll,cam_x)
    for eo in env_objects: hasattr(eo,'draw_light') and eo.draw_light(ll,cam_x)
    if curse_active("darkness") and player and player.alive: px=player.rect.centerx-int(cam_x); py=player.rect.centery; glow(ll,C_WHITE,px,py,160,120); glow(ll,C_CYAN,px,py,80,80)
    return ll

torches=[]; doors=[]; boss_obj=None; run_seed=1; companion=None

def build_floor(floor_num):
    global FLOOR_W,enemies,player_projs,torches,doors,boss_obj,platforms,relic_pickups,essence_drops,env_objects,treasure_chests,player_trinket,current_floor_curse
    FLOOR_W=3800 if meta["bosses_defeated"]==0 else 7800
    particles.clear(); void_tears.clear(); parry_sparks.clear(); parry_rings.clear(); abyssal_tears.clear()
    essence_drops=[]; player_projs=[]; relic_pickups=[]; env_objects=[]; treasure_chests=[]
    rng=random.Random(run_seed+floor_num*17); pick_floor_curse(floor_num, rng); refresh_bg(run_seed+floor_num)
    platforms[:]=gen_platforms(rng,floor_num); torches.clear()
    for x in range(300,FLOOR_W,800): torches.append(Torch(x,GROUND_Y))
    for px,py,pw in platforms:
        if rng.random()>0.2: torches.append(Torch(px+20,py)); torches.append(Torch(px+pw-20,py))
    specs=gen_enemies(rng,floor_num,platforms); enemies.clear()
    for sp in specs:
        t=sp["type"]
        if t=="grunt": enemies.append(Grunt(sp["x"],sp["y"],sp["pl"],sp["pr"]))
        elif t=="bulwark": enemies.append(Bulwark(sp["x"],sp["y"],sp["pl"],sp["pr"]))
        elif t=="wraith": enemies.append(Wraith(sp["x"],sp["y"]))
        elif t=="seraph": enemies.append(Seraph(sp["x"],sp["y"],elite=False))
        elif t=="seraph_elite": enemies.append(Seraph(sp["x"],sp["y"],elite=True))
        elif t=="bulwark_elite": b=Bulwark(sp["x"],sp["y"],sp["x"]-150,sp["x"]+150); b.HP=int(8*get_diff()); b.hp=b.HP; enemies.append(b)
    treasure_chests.append(TreasureChest(rng.randint(FLOOR_W//3, 2*FLOOR_W//3), GROUND_Y-40))
    
    if floor_num == 2: env_objects.append(Merchant(FLOOR_W//2, GROUND_Y))

    _altar_budget = 1 + (1 if meta.get("curse_level", 0) >= 3 else 0)
    _altars_placed = 0
    _plat_pool = list(platforms)
    rng.shuffle(_plat_pool)
    for (px, py, pw) in _plat_pool:
        if _altars_placed >= _altar_budget:
            break
        if pw >= 140 and rng.random() < 0.10:
            env_objects.append(CursedBloodAltar(px + pw // 2, py))
            _altars_placed += 1

    boss_obj=None; doors.clear()
    interact_key = "A" if using_gamepad else pygame.key.name(meta["binds"]["interact"]).upper()
    if floor_num>=1 and meta["bosses_defeated"]>0:
        inv_door=Door(FLOOR_W//2 + 400,GROUND_Y-170,C_RUNEGLOW,f"THE INEVITABLE [{interact_key}]","sanctum_midrun"); inv_door.locked=True; doors.append(inv_door)
    if floor_num<3: doors.append(Door(FLOOR_W-300,GROUND_Y-170,C_CYAN,f"DESCEND [{interact_key}]",f"floor{floor_num+1}"))
    else: doors.append(Door(FLOOR_W-300,GROUND_Y-170,C_RED,f"ENTER THE SANCTUM [{interact_key}]","boss_room"))
    
    cd = FLOOR_CURSES[current_floor_curse]
    alive_count = len([e for e in enemies if e.alive])
    if current_floor_curse != "none":
        announce(f"FLOOR {floor_num} CURSE: {cd['name']} — {cd['desc']}", cd["color"], 200)
    else:
        dialogue = STORY_DIALOGUE.get("floor_1_start", "FLOOR {floor}  — {entities} ENTITIES DETECTED")
        announce(dialogue.format(floor=floor_num, entities=alive_count), C_CYAN if floor_num==1 else C_ORANGE, 160)

def build_boss_room():
    global enemies,player_projs,torches,doors,boss_obj,platforms,relic_pickups,essence_drops,env_objects,treasure_chests,FLOOR_W,current_floor_curse
    FLOOR_W=3200; current_floor_curse="none"; particles.clear(); void_tears.clear(); parry_sparks.clear(); parry_rings.clear(); abyssal_tears.clear()
    essence_drops=[]; player_projs=[]; relic_pickups=[]; enemies.clear(); env_objects=[]; treasure_chests=[]
    rng=random.Random(run_seed+999); refresh_bg(run_seed+999); platforms[:]=[]
    for px,py,pw in [(300,GROUND_Y-160,200),(700,GROUND_Y-300,180),(1100,GROUND_Y-160,200),(1500,GROUND_Y-350,180),(1900,GROUND_Y-160,200),(2300,GROUND_Y-300,180),(2700,GROUND_Y-160,200)]: platforms.append((px,py,pw))
    torches.clear()
    for px,py,pw in platforms: torches.append(Torch(px+pw//2,py))
    for x in range(100,3200,400): torches.append(Torch(x,GROUND_Y))
    boss_obj=Boss(1500,GROUND_Y-200); enemies.clear(); doors.clear()
    announce(STORY_DIALOGUE.get("boss_greet", "AETHERIA: 'You dare enter my domain, Executioner?'"), C_RED, 200)
    audio.bgm("bgm_boss",audio.bgm_vol)

def build_sanctum(midrun=False):
    global enemies,player_projs,torches,doors,boss_obj,platforms,relic_pickups,essence_drops,env_objects,treasure_chests,current_floor_curse
    particles.clear(); void_tears.clear(); parry_sparks.clear(); parry_rings.clear()
    essence_drops=[]; player_projs=[]; relic_pickups=[]; enemies.clear(); boss_obj=None; env_objects=[]; treasure_chests=[]; current_floor_curse="none"
    platforms[:]=[(200,GROUND_Y-150,300),(800,GROUND_Y-240,200),(1400,GROUND_Y-150,250)]; torches.clear()
    for px,py,pw in platforms: torches.append(Torch(px+20,py)); torches.append(Torch(px+pw-20,py))
    torches.append(Torch(500,GROUND_Y)); torches.append(Torch(1100,GROUND_Y))
    env_objects.append(RestShrine(1200,GROUND_Y-90)); doors.clear()
    interact_key = "A" if using_gamepad else pygame.key.name(meta["binds"]["interact"]).upper()
    if midrun:
        next_f = (run.get("sanctum_return_floor") or 1) + 1
        label = f"PROCEED TO FLOOR {next_f} [{interact_key}]" if next_f < 4 else f"ENTER THE SANCTUM [{interact_key}]"
        d = Door(1600, GROUND_Y-170, C_CYAN if next_f < 4 else C_RED, label, "return_to_floor")
        d.locked = False; doors.append(d)
        ann_text = STORY_DIALOGUE.get("sanctum_midrun", "THE INEVITABLE: 'Prepare for Floor {next_f}, Executioner.'").format(next_f=next_f) if next_f < 4 else STORY_DIALOGUE.get("sanctum_boss_ready", "THE INEVITABLE: 'The Sovereign awaits. Claim your destiny.'")
        announce(ann_text, C_RUNEGLOW, 160)
    else:
        if meta.get("bosses_defeated", 0) > 0:
            d = Door(1600, GROUND_Y-170, C_BLOOD,
                     f"ENTER MASTER MODE [{interact_key}]", "master_loop")
            d.locked = False; doors.append(d)
            curse_preview = min(meta["curse_level"] + 1, 99)
            announce(
                STORY_DIALOGUE.get("sanctum_master_mode", "THE INEVITABLE: 'Master Mode awaits... The curse deepens to Level {curse}.'").format(curse=curse_preview),
                C_BLOOD, 200
            )
        else:
            d = Door(1600, GROUND_Y-170, C_GOLD,
                     f"NEXT RUN [{interact_key}]", "new_run")
            d.locked = False; doors.append(d)
        announce(STORY_DIALOGUE.get("sanctum_welcome", "THE INEVITABLE: 'Welcome to the Sanctum. Equip Talismans & spend essence.'"), C_CYAN, 160)
        env_objects.append(TalismanStone(550, GROUND_Y - 90))
    refresh_bg(42); audio.bgm("bgm_explore",audio.bgm_vol)

def build_training_room():
    global enemies, player_projs, torches, doors, boss_obj, platforms, relic_pickups, essence_drops, env_objects, treasure_chests, current_floor_curse, FLOOR_W, player, camera_x, companion
    FLOOR_W = 2000; current_floor_curse = "none"
    particles.clear(); void_tears.clear(); parry_sparks.clear(); parry_rings.clear(); abyssal_tears.clear()
    essence_drops=[]; player_projs=[]; relic_pickups=[]; enemies.clear(); env_objects=[]; treasure_chests=[]; boss_obj=None
    refresh_bg(42)
    platforms[:] = [(100, GROUND_Y-100, 1800)]
    torches.clear()
    torches.append(Torch(400, GROUND_Y)); torches.append(Torch(1200, GROUND_Y))
    enemies.append(TrainingDummy(1000, GROUND_Y - 100))
    doors.clear()
    
    interact_key = "A" if using_gamepad else pygame.key.name(meta["binds"]["interact"]).upper()
    d = Door(200, GROUND_Y-170, C_CYAN, f"RETURN TO MENU [{interact_key}]", "return_menu")
    d.locked = False
    doors.append(d)
    
    active_talismans.clear()
    player = Player(400, GROUND_Y-80)
    camera_x = 0.0
    companion = CatCompanion()
    announce(STORY_DIALOGUE.get("training_welcome", "TRAINING GROUNDS — TEST YOUR ARSENAL"), C_CYAN, 160)

def handle_gamepad_menu_nav(dt_mult):
    global pad_menu_idx, pad_menu_cooldown, current_menu_rects, STATE, PREV_STATE, menu_view, using_gamepad
    
    if not joysticks or not current_menu_rects: return
    joy = joysticks[0]
    
    pad_menu_cooldown -= dt_mult
    if pad_menu_cooldown > 0: return

    try:
        hat_y = joy.get_hat(0)[1]
        axis_y = joy.get_axis(1)
        
        if hat_y == 1 or axis_y < -0.5:
            pad_menu_idx = (pad_menu_idx - 1) % len(current_menu_rects)
            pad_menu_cooldown = 12
            audio.play("hit", 0.1)
        elif hat_y == -1 or axis_y > 0.5:
            pad_menu_idx = (pad_menu_idx + 1) % len(current_menu_rects)
            pad_menu_cooldown = 12
            audio.play("hit", 0.1)
            
        if joy.get_button(0): 
            mx, my = current_menu_rects[pad_menu_idx].center
            pygame.mouse.set_pos((mx, my))
            ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (mx, my)})
            pygame.event.post(ev)
            pad_menu_cooldown = 20
            
    except pygame.error:
        pass

def get_gamepad_inputs():
    inputs = {}
    if not joysticks: return inputs
    
    joy = joysticks[0]
    for action, btn_id in meta["pad_binds"].items():
        if isinstance(btn_id, int) and btn_id < joy.get_numbuttons():
            inputs[action] = joy.get_button(btn_id)
        elif btn_id == "LT":
            if joy.get_numaxes() > 4 and joy.get_axis(4) > 0.5: inputs[action] = True
            elif joy.get_numaxes() > 2 and joy.get_axis(2) > 0.5: inputs[action] = True # Fallback depending on OS
        elif btn_id == "RT":
            if joy.get_numaxes() > 5 and joy.get_axis(5) > 0.5: inputs[action] = True
            elif joy.get_numaxes() > 2 and joy.get_axis(2) < -0.5: inputs[action] = True # Fallback depending on OS
            
    # Simple D-Pad to directional handling
    if joy.get_numhats() > 0:
        hat = joy.get_hat(0)
        if hat[0] != 0: inputs["dir_x"] = hat[0]
        if hat[1] != 0: inputs["dir_y"] = -hat[1]
    
    # Left analog stick handling
    if joy.get_numaxes() >= 2:
        ax = joy.get_axis(0)
        ay = joy.get_axis(1)
        if abs(ax) > 0.3: inputs["dir_x"] = ax
        if abs(ay) > 0.3: inputs["dir_y"] = ay

    # Right analog stick handling (for aiming blink/bolt)
    if joy.get_numaxes() >= 4:
        # standard XInput is 2/3 or 3/4
        ax2 = joy.get_axis(3) if joy.get_numaxes() > 4 else joy.get_axis(2)
        ay2 = joy.get_axis(4) if joy.get_numaxes() > 4 else joy.get_axis(3)
        if abs(ax2) > 0.2: inputs["aim_x"] = ax2
        if abs(ay2) > 0.2: inputs["aim_y"] = ay2
        
    return inputs

def is_action_pressed(action_key, event=None):
    global _frame_interact_pressed, _frame_jump_pressed
    if event and event.type == pygame.KEYDOWN and event.key == meta["binds"].get(action_key): return True
    if event and event.type == pygame.JOYBUTTONDOWN:
        for joy in joysticks:
            if event.button == meta["pad_binds"].get(action_key): return True
    # Fallback: use per-frame flags (for calls without an event, e.g. from draw/update)
    if event is None:
        if action_key == "interact" and _frame_interact_pressed: return True
        if action_key == "jump" and _frame_jump_pressed: return True
    return False

def start_new_run():
    global player,run,run_seed,STATE,camera_x,boss_obj,kill_streak,kill_streak_best,player_trinket,companion
    meta["total_runs"]+=1; save_meta(); run_seed=random.randint(1,99999); kill_streak=0; kill_streak_best=0; player_trinket=None
    run.update({"floor":1,"kills":0,"relics":[],"relic_offered":[],"curse_active":meta["curse_level"]>0,"iron_will_used":False,"double_jump_used":False,"sanctum_return_floor":None,"parries_this_run":0,"trinket":None,"flasks":3,"floor_curse_shown":False,"parry_heal_counter":0,"treasure_rooms_found":0,"wraiths_killed":0,"slayer_spawned":False})
    player=Player(200,GROUND_Y-80); camera_x=0.0; companion=CatCompanion(); build_floor(1); STATE="game"
    audio.bgm("bgm_explore", audio.bgm_vol)

def draw_menu_bg():
    global menu_cam_x; menu_cam_x+=0.3; draw_bg(display_surf,menu_cam_x*0.2); draw_mg(display_surf,menu_cam_x*0.45)
    ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,165)); display_surf.blit(ov,(0,0))
    ver=F_TINY.render("v1.0",True,(55,50,70)); display_surf.blit(ver,(WIDTH-ver.get_width()-8,HEIGHT-ver.get_height()-6))

def floor_to_display():
    tw=FLOOR_TILE.get_width(); th=FLOOR_TILE.get_height()
    for i in range(-2,int(WIDTH/tw)+4): display_surf.blit(FLOOR_TILE,(i*tw-int(camera_x)%tw-tw*2,GROUND_Y))
    fh=HEIGHT-GROUND_Y-th
    if fh>0: pygame.draw.rect(display_surf,(20,12,28),(0,GROUND_Y+th,WIDTH,fh))

def draw_platforms():
    for px,py,pw in platforms:
        sx=px-int(camera_x)
        if sx>-200 and sx<WIDTH+200: display_surf.blit(make_plat_surf(pw),(sx,py))

def draw_game():
    draw_bg(display_surf,camera_x); draw_mg(display_surf,camera_x)
    for m in motes: m.draw(display_surf,camera_x)
    floor_to_display(); draw_platforms()
    for t in torches: t.draw(display_surf,camera_x)
    for eo in env_objects: eo.draw(display_surf,camera_x)
    for tc in treasure_chests: tc.draw(display_surf,camera_x)
    for e in enemies:
        if hasattr(e,'draw'): e.draw(display_surf,camera_x)
    if boss_obj: boss_obj.draw(display_surf,camera_x)
    for r in relic_pickups: r.draw(display_surf,camera_x)
    for d in doors: d.draw(display_surf,camera_x)
    if player: player.draw(display_surf,camera_x)
    if companion: companion.draw(display_surf,camera_x)
    for p in player_projs: p.draw(display_surf,camera_x)
    for d in essence_drops: d.draw(display_surf,camera_x)
    for vt in void_tears: vt.draw(display_surf,camera_x)
    for at in abyssal_tears: at.draw(display_surf,camera_x)
    draw_particles(display_surf,camera_x); draw_parry_vfx(display_surf,camera_x); draw_dmg_numbers(display_surf,camera_x)
    display_surf.blit(build_light_layer(torches,doors,camera_x),(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    if player: player.draw_hud(display_surf)

    if boss_obj and boss_obj.alive:
        ph=boss_obj.ph; bw,bh=550,25; bxb=WIDTH//2-bw//2; byb=HEIGHT-75; pygame.draw.rect(display_surf,(22,10,35),(bxb-2,byb-2,bw+4,bh+4),border_radius=6)
        phc={1:C_GOLD,2:C_ORANGE,3:C_RED}[ph]; pygame.draw.rect(display_surf,phc,(bxb,byb,int(bw*boss_obj.hp/boss_obj.MAX_HP),bh),border_radius=5)
        phl=F_SM.render(f"SOVEREIGN AETHERIA  — PHASE {ph}",True,phc); display_surf.blit(phl,(WIDTH//2-phl.get_width()//2,byb-24))
        posture_pct = max(0.0, 1.0 - (boss_obj.stagger_meter / boss_obj.stagger_threshold))
        pygame.draw.rect(display_surf,(30,30,15),(bxb,byb+bh+4,bw,6),border_radius=2); pygame.draw.rect(display_surf,C_CYAN,(bxb,byb+bh+4,int(bw*posture_pct),6),border_radius=2)
        if posture_pct<0.25: stun_lbl=F_TINY.render("STAGGER NEAR!",True,C_CYAN); display_surf.blit(stun_lbl,(bxb+bw+8,byb+bh+1))
        if ph==2: kt=F_SM.render(f"KEYS {boss_obj.keys_found}/4"+(" — STRIKE!" if boss_obj.p2_vuln else " — COLLECT THEM"),True,C_GOLD if not boss_obj.p2_vuln else C_CYAN); display_surf.blit(kt,(WIDTH//2-kt.get_width()//2,byb+bh+14))

    alive_count=sum(1 for e in enemies if e.alive)
    if alive_count>0 and not boss_obj: ec=F_SM.render(f"ENTITIES: {alive_count}",True,C_RED); display_surf.blit(ec,(WIDTH-ec.get_width()-20,20))
    elif alive_count==0 and not boss_obj: ec=F_SM.render("ENTITIES: 0",True,C_CYAN); display_surf.blit(ec,(WIDTH-ec.get_width()-20,20))

    for d in doors:
        if not d.locked and not d.opening:
            if player and d.rect.colliderect(player.rect): ht=F_SM.render(f"Press {pygame.key.name(meta['binds']['interact']).upper()} to proceed",True,d.color); display_surf.blit(ht,(WIDTH//2-ht.get_width()//2,HEIGHT//2-80))

    ay=HEIGHT//4
    for ann in announce_queue:
        text,col,timer,mt=ann; a=min(255,int(timer*5.5))
        bg=pygame.Surface((len(text)*11+36,45),pygame.SRCALPHA); bg.fill((0,0,0,min(190,a))); display_surf.blit(bg,(WIDTH//2-bg.get_width()//2,ay))
        t=F_MED.render(text,True,col); t.set_alpha(a); display_surf.blit(t,(WIDTH//2-t.get_width()//2,ay+12)); ay+=50

    if player and not player.alive:
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,210)); display_surf.blit(ov,(0,0)); draw_text(display_surf,"YOUR REIGN ENDS HERE",F_BIG,C_RED,WIDTH//2,HEIGHT//2-185,center=True)
        sw,sh=760,400; card=pygame.Rect(WIDTH//2-sw//2,HEIGHT//2-150,sw,sh)
        pygame.draw.rect(display_surf,(16,10,26),card,border_radius=8); pygame.draw.rect(display_surf,C_RED,card,2,border_radius=8)
        draw_text(display_surf,"— RUN SUMMARY —",F_MED,C_PARCH2,WIDTH//2,card.y+22,center=True)
        cd=FLOOR_CURSES[current_floor_curse]
        for i,(k,v) in enumerate([("Floor reached",f"{run['floor']}"),("Kills",f"{run['kills']}"),("Best streak",f"×{kill_streak_best}"),("Parries",f"{run.get('parries_this_run',0)}"),("Best combo",f"×{meta['best_combo']}"),("Floor curse",cd["name"]),("Relics found",f"{len(run['relics'])}/{meta['upg_relic_slots']}"),("Total essence",f"{meta['divine_essence']}")]):
            ry=card.y+70+i*28; draw_text(display_surf,k,F_SM,C_GREY,card.x+30,ry); draw_text(display_surf,v,F_SM,cd["color"] if k=="Floor curse" else C_WHITE,card.right-30-F_SM.size(v)[0],ry)
        hist=meta.get("run_history",[])
        if len(hist)>1:
            pygame.draw.line(display_surf,C_STONE,(card.x+20,card.bottom-100),(card.right-20,card.bottom-100),1); draw_text(display_surf,"LAST RUNS",F_TINY,(90,80,100),card.x+30,card.bottom-90)
            for hi,h in enumerate(hist[1:4]): hl=F_TINY.render(f"Fl.{h['floor']}  {h['kills']}k  {h['parries']}p  {h.get('relics',0)}r",True,(75,70,90)); display_surf.blit(hl,(card.x+30,card.bottom-70+hi*22))
        draw_text(display_surf,"[SPACE] / [GAMEPAD A] Return to Menu",F_MED,C_PARCH2,WIDTH//2,card.bottom+30,center=True)

    k_str = f"{pygame.key.name(meta['binds']['left']).upper()}{pygame.key.name(meta['binds']['right']).upper()}{pygame.key.name(meta['binds']['up']).upper()}{pygame.key.name(meta['binds']['down']).upper()}: move  JUMP: {pygame.key.name(meta['binds']['jump']).upper()}  DASH: {pygame.key.name(meta['binds']['dash']).upper()}  LMB/{pygame.key.name(meta['binds']['atk']).upper()}: atk  RMB: parry  BOLT: {pygame.key.name(meta['binds']['bolt']).upper()}  BLINK: {pygame.key.name(meta['binds']['blink']).upper()}  ULT: {pygame.key.name(meta['binds']['ult']).upper()}  TRINKET: {pygame.key.name(meta['binds']['trinket']).upper()}  STANCE: {pygame.key.name(meta['binds']['stance']).upper()}  CLEAVE: {pygame.key.name(meta['binds'].get('cleave', pygame.K_x)).upper()}"
    hint=F_TINY.render(k_str,True,(80,75,100)); display_surf.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT-24))

# -------------------------
# MAIN GAME LOOP
# -------------------------
while True:
    raw_dt=clock.tick(60); dt_mult=min(raw_dt/(1000/60),2.8)
    _frame_interact_pressed = False
    _frame_jump_pressed = False
    current_menu_rects.clear()
    # After clearing rects, keep pad_menu_idx from going stale (will be clamped after rects are rebuilt)

    for event in pygame.event.get():
        if event.type==pygame.QUIT: save_meta(); pygame.quit(); sys.exit()
        
        if event.type == pygame.KEYDOWN:
            _held_keys[event.key] = True
        elif event.type == pygame.KEYUP:
            _held_keys[event.key] = False
        if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYHATMOTION:
            using_gamepad = True
        elif event.type == pygame.JOYAXISMOTION and abs(event.value) > 0.5:
            using_gamepad = True
        elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            using_gamepad = False
        
        if event.type == pygame.JOYDEVICEADDED:
            joy = pygame.joystick.Joystick(event.device_index); joy.init(); joysticks.append(joy)
        elif event.type == pygame.JOYDEVICEREMOVED:
            joysticks = [j for j in joysticks if j.get_instance_id() != event.instance_id]

        if event.type==pygame.KEYDOWN or event.type==pygame.JOYBUTTONDOWN:
            if binding_action is not None and event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:
                    _max_key = len(pygame.key.get_pressed()) - 1
                    if 0 <= event.key <= _max_key:
                        meta["binds"][binding_action] = event.key
                        save_meta()
                    # silently ignore keys outside valid range (media keys, etc.)
                binding_action = None
                continue
            elif binding_action is not None and event.type == pygame.JOYBUTTONDOWN:
                meta["pad_binds"][binding_action] = event.button
                save_meta()
                binding_action = None
                continue

            # Track per-frame action presses for menus
            if event.type == pygame.KEYDOWN:
                if event.key == meta["binds"].get("interact"): _frame_interact_pressed = True
                if event.key == meta["binds"].get("jump"): _frame_jump_pressed = True
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == meta["pad_binds"].get("interact"): _frame_interact_pressed = True
                if event.button == meta["pad_binds"].get("jump"): _frame_jump_pressed = True
                
            if getattr(event, 'key', None)==pygame.K_F11: is_fullscreen=not is_fullscreen; flags=pygame.FULLSCREEN if is_fullscreen else 0; screen=pygame.display.set_mode((WINDOW_W,WINDOW_H),flags)
            elif getattr(event, 'key', None) in (pygame.K_ESCAPE,pygame.K_p) or (event.type == pygame.JOYBUTTONDOWN and event.button == meta["pad_binds"].get("start", 7)):
                if STATE in ("game","sanctum","training"): PREV_STATE=STATE; STATE="paused"; menu_view="pause_main"; pad_menu_idx=0
                elif STATE=="paused":
                    if menu_view=="sanctum_shop": STATE=PREV_STATE if PREV_STATE in ("game","sanctum","training") else "sanctum"
                    elif menu_view in ("settings","inventory", "merchant_shop", "controls", "talisman_select"): menu_view="pause_main"; pad_menu_idx=0
                    else: STATE=PREV_STATE
            elif STATE=="game" and player and not player.alive:
                if getattr(event, 'key', None)==pygame.K_SPACE or (event.type == pygame.JOYBUTTONDOWN and event.button == meta["pad_binds"].get("jump")): STATE,menu_view="main_menu","main"; audio.bgm("bgm_explore",audio.bgm_vol)
            elif STATE in ("game","sanctum","training") and player and player.alive:
                if is_action_pressed("interact", event):
                    for d in doors: d.try_open() if not d.locked and d.rect.colliderect(player.rect) else None
                    if STATE=="sanctum" and pygame.Rect(800,GROUND_Y-160,80,100).colliderect(player.rect): PREV_STATE="sanctum"; STATE="paused"; menu_view="sanctum_shop"

        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and binding_action is None:
            mx,my=get_mouse_pos()
            if STATE=="main_menu":
                if menu_view=="main":
                    if menu_btn(0,6).collidepoint(mx,my): start_new_run()
                    elif menu_btn(1,6).collidepoint(mx,my): STATE="training"; build_training_room(); audio.bgm("bgm_explore",audio.bgm_vol)
                    elif menu_btn(2,6).collidepoint(mx,my): STATE,menu_view="main_menu","codex"
                    elif menu_btn(3,6).collidepoint(mx,my): STATE,menu_view="main_menu","settings"
                    elif menu_btn(4,6).collidepoint(mx,my): STATE,menu_view="main_menu","controls"
                    elif menu_btn(5,6).collidepoint(mx,my): save_meta(); pygame.quit(); sys.exit()
                elif menu_view=="settings":
                    _sy=HEIGHT//2-280
                    if pygame.Rect(WIDTH//2-180,_sy+88,50,45).collidepoint(mx,my): 
                        audio.set_bgm_vol(audio.bgm_vol-0.1); meta["bgm_vol"] = audio.bgm_vol; save_meta()
                    elif pygame.Rect(WIDTH//2+130,_sy+88,50,45).collidepoint(mx,my): 
                        audio.set_bgm_vol(audio.bgm_vol+0.1); meta["bgm_vol"] = audio.bgm_vol; save_meta()
                    elif pygame.Rect(WIDTH//2-180,_sy+168,50,45).collidepoint(mx,my): 
                        audio.set_sfx_vol(audio.sfx_vol-0.1); audio.play("slash",0.5); meta["sfx_vol"] = audio.sfx_vol; save_meta()
                    elif pygame.Rect(WIDTH//2+130,_sy+168,50,45).collidepoint(mx,my): 
                        audio.set_sfx_vol(audio.sfx_vol+0.1); audio.play("slash",0.5); meta["sfx_vol"] = audio.sfx_vol; save_meta()
                    elif pygame.Rect(WIDTH//2-180,_sy+248,50,45).collidepoint(mx,my): curr_res_idx=(curr_res_idx-1)%len(RESOLUTIONS)
                    elif pygame.Rect(WIDTH//2+130,_sy+248,50,45).collidepoint(mx,my): curr_res_idx=(curr_res_idx+1)%len(RESOLUTIONS)
                    elif pygame.Rect(WIDTH//2-110,_sy+315,220,42).collidepoint(mx,my): is_fullscreen=not is_fullscreen
                    elif pygame.Rect(WIDTH//2-200,_sy+400,180,55).collidepoint(mx,my): menu_view="main"
                    elif pygame.Rect(WIDTH//2+20,_sy+400,180,55).collidepoint(mx,my):
                        WINDOW_W,WINDOW_H=RESOLUTIONS[curr_res_idx]; flags=pygame.FULLSCREEN if is_fullscreen else 0; screen=pygame.display.set_mode((WINDOW_W,WINDOW_H),flags)
                        meta["resolution_idx"]=curr_res_idx; meta["fullscreen"]=is_fullscreen; save_meta()
                    elif pygame.Rect(WIDTH//2-100,_sy+468,200,45).collidepoint(mx,my):
                        meta.clear(); meta.update({k:(dict(v) if isinstance(v,dict) else v) for k,v in META_DEFAULTS.items()}); save_meta(); menu_view="main"
                elif menu_view=="controls":
                    bind_list = list(meta["binds"].items()); cols = 2; n_rows=(len(bind_list)+cols-1)//cols
                    table_h=n_rows*55; start_y=HEIGHT//2-table_h//2-20
                    for idx, (act, key_val) in enumerate(bind_list):
                        cx = WIDTH//2 - 350 + (idx%cols)*400; cy = start_y + (idx//cols)*55
                        if pygame.Rect(cx, cy, 300, 45).collidepoint(mx,my): binding_action = act
                    if pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55).collidepoint(mx,my): menu_view="main"
                elif menu_view=="codex":
                    if pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55).collidepoint(mx,my): menu_view="main"
            
            elif STATE=="paused":
                if menu_view=="pause_main":
                    if menu_btn(0,6).collidepoint(mx,my): STATE=PREV_STATE
                    elif menu_btn(1,6).collidepoint(mx,my): menu_view="inventory"
                    elif menu_btn(2,6).collidepoint(mx,my): menu_view="settings"
                    elif menu_btn(3,6).collidepoint(mx,my): menu_view="controls"
                    elif menu_btn(4,6).collidepoint(mx,my): STATE,menu_view="main_menu","main"; audio.bgm("bgm_explore",audio.bgm_vol)
                    elif menu_btn(5,6).collidepoint(mx,my): save_meta(); pygame.quit(); sys.exit()
                elif menu_view=="inventory":
                    if pygame.Rect(100, 850, 200, 55).collidepoint(mx, my): menu_view="pause_main"
                elif menu_view=="merchant_shop":
                    for bi, item in enumerate(MERCHANT_SHOP_ITEMS):
                        k, name, cost, col, desc, lore = item
                        r = pygame.Rect(100, 220 + bi*80, 500, 60)
                        avail = True
                        if k == "flasks" and run.get("flasks", 3) >= 3: avail = False
                        if k == "ult" and player.ult_cd <= 0: avail = False
                        
                        can = (avail and meta["divine_essence"] >= cost)
                        if r.collidepoint(mx, my) and can:
                            meta["divine_essence"] -= cost
                            if k == "flasks": run["flasks"] = 3
                            elif k == "max_hp": player.max_hp += 1; player.hp += 1
                            elif k == "ult": player.ult_cd = 0
                            audio.play("relic", 0.8)
                    if pygame.Rect(100, 850, 200, 55).collidepoint(mx, my): STATE=PREV_STATE; menu_view="pause_main"
                elif menu_view=="sanctum_shop":
                    for bi, item in enumerate(SANCTUM_SHOP_ITEMS):
                        k, name, cost, col, desc, lore = item
                        r = pygame.Rect(100, 220 + bi*70, 500, 60)
                        avail = True
                        if k == "upg_dash_cd" and meta["upg_dash_cd"] <= 35: avail = False
                        if k in ["upg_double_jump", "upg_blink", "upg_ult"] and meta[k]: avail = False
                        if k == "upg_parry_window" and meta["upg_parry_window"] >= 22: avail = False
                        if k == "upg_relic_slots" and meta["upg_relic_slots"] >= 5: avail = False
                        
                        can = (avail and meta["divine_essence"] >= cost)
                        if r.collidepoint(mx, my) and can:
                            meta["divine_essence"] -= cost
                            if k == "upg_max_hp": meta[k]+=1; player.max_hp+=1; player.hp+=1
                            elif k == "upg_dash_cd": meta[k]-=5
                            elif k in ["upg_double_jump","upg_blink","upg_ult"]: meta[k]=True
                            elif k == "upg_parry_window": meta[k]+=2
                            elif k == "upg_relic_slots": meta[k]+=1
                            elif k == "reforge": meta["reforge_bonus"] = meta.get("reforge_bonus", 0) + 1
                            audio.play("relic", 0.8)
                            save_meta()
                    if pygame.Rect(100, 850, 200, 55).collidepoint(mx, my): STATE = "sanctum"
                elif menu_view == "talisman_select":
                    all_keys = list(TALISMAN_DEFS.keys())
                    for bi, tkey in enumerate(all_keys):
                        r = pygame.Rect(100, 220 + bi*80, 500, 60)
                        if r.collidepoint(mx, my): equip_talisman(tkey)
                    if pygame.Rect(100, 850, 200, 55).collidepoint(mx, my):
                        STATE = PREV_STATE
                        menu_view = "pause_main" if STATE == "paused" else "main"
                elif menu_view=="settings":
                    _sy=HEIGHT//2-280
                    if pygame.Rect(WIDTH//2-180,_sy+88,50,45).collidepoint(mx,my): 
                        audio.set_bgm_vol(audio.bgm_vol-0.1); meta["bgm_vol"] = audio.bgm_vol; save_meta()
                    elif pygame.Rect(WIDTH//2+130,_sy+88,50,45).collidepoint(mx,my): 
                        audio.set_bgm_vol(audio.bgm_vol+0.1); meta["bgm_vol"] = audio.bgm_vol; save_meta()
                    elif pygame.Rect(WIDTH//2-180,_sy+168,50,45).collidepoint(mx,my): 
                        audio.set_sfx_vol(audio.sfx_vol-0.1); audio.play("slash",0.5); meta["sfx_vol"] = audio.sfx_vol; save_meta()
                    elif pygame.Rect(WIDTH//2+130,_sy+168,50,45).collidepoint(mx,my): 
                        audio.set_sfx_vol(audio.sfx_vol+0.1); audio.play("slash",0.5); meta["sfx_vol"] = audio.sfx_vol; save_meta()
                    elif pygame.Rect(WIDTH//2-180,_sy+248,50,45).collidepoint(mx,my): curr_res_idx=(curr_res_idx-1)%len(RESOLUTIONS)
                    elif pygame.Rect(WIDTH//2+130,_sy+248,50,45).collidepoint(mx,my): curr_res_idx=(curr_res_idx+1)%len(RESOLUTIONS)
                    elif pygame.Rect(WIDTH//2-110,_sy+315,220,42).collidepoint(mx,my): is_fullscreen=not is_fullscreen
                    elif pygame.Rect(WIDTH//2-200,_sy+400,180,55).collidepoint(mx,my): menu_view="pause_main"
                    elif pygame.Rect(WIDTH//2+20,_sy+400,180,55).collidepoint(mx,my):
                        WINDOW_W,WINDOW_H=RESOLUTIONS[curr_res_idx]; flags=pygame.FULLSCREEN if is_fullscreen else 0; screen=pygame.display.set_mode((WINDOW_W,WINDOW_H),flags)
                        meta["resolution_idx"]=curr_res_idx; meta["fullscreen"]=is_fullscreen; save_meta()
                    elif pygame.Rect(WIDTH//2-100,_sy+468,200,45).collidepoint(mx,my):
                        meta.clear(); meta.update({k:(dict(v) if isinstance(v,dict) else v) for k,v in META_DEFAULTS.items()}); save_meta(); STATE,menu_view="main_menu","main"; audio.bgm("bgm_explore",audio.bgm_vol)
                elif menu_view=="controls":
                    bind_list = list(meta["binds"].items()); cols = 2; n_rows=(len(bind_list)+cols-1)//cols
                    table_h=n_rows*55; start_y=HEIGHT//2-table_h//2-20
                    for idx, (act, key_val) in enumerate(bind_list):
                        cx = WIDTH//2 - 350 + (idx%cols)*400; cy = start_y + (idx//cols)*55
                        if pygame.Rect(cx, cy, 300, 45).collidepoint(mx,my): binding_action = act
                    if pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55).collidepoint(mx,my): menu_view="pause_main"

    if STATE in ("main_menu","paused"):
        if using_gamepad: handle_gamepad_menu_nav(dt_mult)
        draw_menu_bg()
        
        if STATE=="main_menu":
            if menu_view=="main":
                draw_text(display_surf,"ECLIPSE OF THE ORDER",F_TITLE,C_RUNEGLOW,WIDTH//2,HEIGHT//2-320,center=True)
                draw_text(display_surf,"— THE DEFINITIVE CUT —",F_SM,C_PARCH2,WIDTH//2,HEIGHT//2-240,center=True)
                for i,(lbl,col) in enumerate([("NEW RUN",C_CYAN),("TRAINING",C_ORANGE),("CODEX",C_PARCH),("SETTINGS",C_GREY),("KEYBINDS",C_GOLD),("QUIT",C_RED)]):
                    draw_btn(display_surf,lbl,F_MED,col,menu_btn(i,6))
            elif menu_view=="settings":
                _sy = HEIGHT//2 - 280
                draw_text(display_surf,"-- SETTINGS --",F_BIG,C_PARCH,WIDTH//2,_sy,center=True)
                draw_text(display_surf,"MUSIC VOLUME",F_SM,C_GREY,WIDTH//2,_sy+75,center=True)
                draw_btn(display_surf,"<",F_BIG,C_CYAN,pygame.Rect(WIDTH//2-180,_sy+88,50,45))
                draw_text(display_surf,f"{int(audio.bgm_vol*100)}%",F_MED,C_WHITE,WIDTH//2,_sy+93,center=True)
                draw_btn(display_surf,">",F_BIG,C_CYAN,pygame.Rect(WIDTH//2+130,_sy+88,50,45))
                draw_text(display_surf,"SFX VOLUME",F_SM,C_GREY,WIDTH//2,_sy+155,center=True)
                draw_btn(display_surf,"<",F_BIG,C_CYAN,pygame.Rect(WIDTH//2-180,_sy+168,50,45))
                draw_text(display_surf,f"{int(audio.sfx_vol*100)}%",F_MED,C_WHITE,WIDTH//2,_sy+173,center=True)
                draw_btn(display_surf,">",F_BIG,C_CYAN,pygame.Rect(WIDTH//2+130,_sy+168,50,45))
                draw_text(display_surf,"RESOLUTION",F_SM,C_GREY,WIDTH//2,_sy+235,center=True)
                draw_btn(display_surf,"<",F_BIG,C_CYAN,pygame.Rect(WIDTH//2-180,_sy+248,50,45))
                _rw,_rh=RESOLUTIONS[curr_res_idx]
                draw_text(display_surf,f"{_rw} x {_rh}",F_MED,C_WHITE,WIDTH//2,_sy+253,center=True)
                draw_btn(display_surf,">",F_BIG,C_CYAN,pygame.Rect(WIDTH//2+130,_sy+248,50,45))
                _fscol=C_CYAN if is_fullscreen else C_GREY
                draw_btn(display_surf,f"FULLSCREEN: {'ON' if is_fullscreen else 'OFF'}",F_SM,_fscol,pygame.Rect(WIDTH//2-110,_sy+315,220,42))
                draw_text(display_surf,"click to toggle  -  APPLY to confirm",F_TINY,C_STONE2,WIDTH//2,_sy+368,center=True)
                draw_btn(display_surf,"< BACK",F_MED,C_GREY,pygame.Rect(WIDTH//2-200,_sy+400,180,55))
                draw_btn(display_surf,"APPLY",F_MED,C_CYAN,pygame.Rect(WIDTH//2+20,_sy+400,180,55))
                draw_btn(display_surf,"RESET ALL",F_SM,C_RED,pygame.Rect(WIDTH//2-100,_sy+468,200,45))
            elif menu_view=="controls":
                draw_text(display_surf,"— KEYBINDS —",F_BIG,C_GOLD,WIDTH//2,HEIGHT//6-30,center=True)
                draw_text(display_surf,"Click any action to rebind it (Keyboard or Gamepad)",F_SM,C_GREY,WIDTH//2,HEIGHT//6+28,center=True)
                bind_list=list(meta["binds"].items()); cols=2; n_rows=(len(bind_list)+cols-1)//cols
                table_h=n_rows*55; start_y=HEIGHT//2-table_h//2-20
                ACTION_LABELS={"left":"MOVE LEFT","right":"MOVE RIGHT","up":"LOOK UP","down":"CROUCH","jump":"JUMP","dash":"DASH","atk":"ATTACK","bolt":"BOLT SHOT","blink":"VOID BLINK","ult":"SOUL REND ULT","flask":"USE FLASK","stance":"CHANGE STANCE","interact":"INTERACT","trinket":"USE TRINKET", "cleave":"HOLLOW CLEAVE"}
                mx,my = get_mouse_pos()
                for idx,(act,key_val) in enumerate(bind_list):
                    col_x=WIDTH//2-350+(idx%cols)*400; row_y=start_y+(idx//cols)*55
                    label=ACTION_LABELS.get(act,act.upper()); key_name=pygame.key.name(key_val).upper()
                    pad_btn = meta["pad_binds"].get(act)
                    pad_str = f" / JOY:{pad_btn}" if pad_btn is not None else ""
                    
                    r = pygame.Rect(col_x,row_y,300,45)
                    if r not in current_menu_rects: current_menu_rects.append(r)
                    is_hovered=r.collidepoint(mx,my) or (using_gamepad and current_menu_rects.index(r) == pad_menu_idx)
                    is_active=(binding_action==act)
                    
                    if is_action_pressed("interact") and is_hovered and pad_menu_cooldown <= 0:
                        binding_action = act
                        pad_menu_cooldown = 20
                    
                    bg_col=(40,30,0) if is_active else ((20,15,35) if is_hovered else (12,8,20))
                    bg=pygame.Surface((300,45),pygame.SRCALPHA); bg.fill((*bg_col,200)); display_surf.blit(bg,(col_x,row_y))
                    border_col=C_GOLD if is_active else (C_RUNEGLOW if is_hovered else C_STONE)
                    pygame.draw.rect(display_surf,border_col,r,2,border_radius=4)
                    draw_text(display_surf,label,F_SM,C_PARCH if not is_active else C_GOLD,col_x+12,row_y+12)
                    key_surf=F_TINY.render(f"[{key_name}{pad_str}]",True,C_CYAN if not is_active else C_GOLD); display_surf.blit(key_surf,(col_x+300-key_surf.get_width()-10,row_y+14))
                draw_btn(display_surf,"◄ BACK",F_MED,C_GREY,pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55))
            elif menu_view=="codex":
                draw_text(display_surf,"— CODEX —",F_BIG,C_PARCH,WIDTH//2,HEIGHT//6,center=True)
                cy=HEIGHT//4+20
                for i,(lbl,desc,col) in enumerate([("ATTACK [LMB / ATK]","Strike enemies in melee range",C_ORANGE),("PARRY [RMB]","Block & counter projectiles/melee at perfect timing",C_CYAN),("DASH","Invincible dash; perfect-frame = bullet time",C_PURPLE),("BLINK","Teleport to cursor (upgrade required)",C_RUNEGLOW),("BOLT","Ranged void bolt (costs mana)",C_CYAN),("ULTIMATE","Soul Rend: area devastation (upgrade required)",C_RED),("STANCE","Toggle Reaper / Executioner stance",C_GOLD),("CLEAVE","Hollow Cleave: Executioner dash (8s cooldown)",C_DKRED),("FLOOR KEYS","Collect 4 scattered keys to break phase-2 shield",C_GOLD),("TRINKET","Single-use consumable from treasure chests",C_PARCH)]):
                    draw_text(display_surf,lbl,F_SM,col,WIDTH//2-400,cy+i*42); draw_text(display_surf,desc,F_TINY,C_GREY,WIDTH//2-400+10,cy+i*42+20)
                draw_btn(display_surf,"◄ BACK",F_MED,C_GREY,pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55))
        elif STATE=="paused":
            ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,180)); display_surf.blit(ov,(0,0))
            if menu_view=="pause_main":
                draw_text(display_surf,"PAUSED",F_BIG,C_PARCH,WIDTH//2,HEIGHT//2-310,center=True)
                for i,(lbl,col) in enumerate([("RESUME",C_CYAN),("INVENTORY",C_PARCH),("SETTINGS",C_GREY),("KEYBINDS",C_GOLD),("MAIN MENU",C_RED),("QUIT",C_DKRED)]):
                    draw_btn(display_surf,lbl,F_MED,col,menu_btn(i,6))
            
            elif menu_view=="inventory":
                draw_text(display_surf, "— INVENTORY —", F_BIG, C_PARCH, WIDTH//4, 100, center=True)
                if player:
                    draw_text(display_surf, f"HP: {player.hp}/{player.max_hp}   MANA: {int(player.mana)}/{int(player.max_mana)}", F_MED, C_WHITE, 100, 200)
                    draw_text(display_surf, f"FLASKS: {run.get('flasks',0)}/3", F_MED, C_ORANGE, 100, 250)
                    draw_text(display_surf, f"ESSENCE: ◆{meta['divine_essence']}", F_MED, C_GOLD, 100, 300)
                    
                    hovered_item = None
                    draw_text(display_surf, "RELICS", F_MED, C_GOLD, 100, 400)
                    if not run["relics"]: draw_text(display_surf, "Empty", F_SM, C_GREY, 100, 440)
                    mx, my = get_mouse_pos()
                    for ri, rid in enumerate(run["relics"]):
                        rd = RELIC_DEFS[rid]
                        r = pygame.Rect(100, 440 + ri*60, 500, 50)
                        if r not in current_menu_rects: current_menu_rects.append(r)
                        is_hovered = r.collidepoint(mx, my) or (using_gamepad and current_menu_rects.index(r) == pad_menu_idx)
                        if is_hovered: hovered_item = rd
                        draw_btn(display_surf, f"{rd['icon']} {rd['name']}", F_SM, rd["color"], r)
                    
                    ty = 440 + max(5, len(run["relics"])) * 60
                    draw_text(display_surf, "TRINKET", F_MED, C_CYAN, 100, ty)
                    if player_trinket:
                        td = TRINKET_DEFS[player_trinket]
                        r = pygame.Rect(100, ty + 40, 500, 50)
                        if r not in current_menu_rects: current_menu_rects.append(r)
                        is_hovered = r.collidepoint(mx, my) or (using_gamepad and current_menu_rects.index(r) == pad_menu_idx)
                        if is_hovered: hovered_item = td
                        draw_btn(display_surf, f"{td['icon']} {td['name']}", F_SM, td["color"], r)
                    else:
                        draw_text(display_surf, "Empty", F_SM, C_GREY, 100, ty + 40)
                    
                draw_btn(display_surf, "◄ BACK", F_MED, C_GREY, pygame.Rect(100, 850, 200, 55))
                
                rx = WIDTH//2 + 50
                pygame.draw.line(display_surf, C_STONE, (WIDTH//2, 100), (WIDTH//2, HEIGHT-100), 2)
                if hovered_item:
                    draw_text(display_surf, f"{hovered_item['icon']} {hovered_item['name']}", F_BIG, hovered_item['color'], rx, 220)
                    draw_text_wrapped(display_surf, hovered_item['desc'], F_SM, C_WHITE, rx, 300, 800, center=False)
                    if "lore" in hovered_item:
                        draw_text_wrapped(display_surf, f"\"{hovered_item['lore']}\"", F_MED, C_STONE2, rx, 400, 800, center=False)
                else:
                    draw_text(display_surf, "Hover over an item to see its details.", F_MED, C_GREY, rx, HEIGHT//2)
                    
            elif menu_view == "talisman_select":
                draw_text(display_surf, "— TALISMAN LOADOUT —", F_BIG, C_PURPLE, WIDTH//4, 100, center=True)
                draw_text(display_surf, f"EQUIPPED: {len(active_talismans)}/2", F_SM, C_GREY, WIDTH//4, 150, center=True)
                hovered_item = None
                all_keys = list(TALISMAN_DEFS.keys())
                mx, my = get_mouse_pos()
                for bi, tkey in enumerate(all_keys):
                    td = TALISMAN_DEFS[tkey]
                    equipped = tkey in active_talismans
                    can = equipped or len(active_talismans) < 2
                    border_col = td["color"] if equipped else (C_GREY if not can else td["color"])
                    r = pygame.Rect(100, 220 + bi*80, 500, 60)
                    if r not in current_menu_rects: current_menu_rects.append(r)
                    is_hovered = r.collidepoint(mx, my) or (using_gamepad and current_menu_rects.index(r) == pad_menu_idx)
                    if is_hovered: hovered_item = td
                    
                    if is_action_pressed("interact") and is_hovered and pad_menu_cooldown <= 0:
                        equip_talisman(tkey)
                        pad_menu_cooldown = 20
                    
                    bg = pygame.Surface(r.size, pygame.SRCALPHA)
                    bg.fill((border_col[0]//8, border_col[1]//8, border_col[2]//8, 160))
                    display_surf.blit(bg, r.topleft)
                    pygame.draw.rect(display_surf, border_col if not is_hovered else C_WHITE, r, 2, border_radius=4)
                    title = f"{td['icon']} {td['name']} {'[EQUIPPED]' if equipped else ''}"
                    draw_text(display_surf, title, F_SM, border_col if not is_hovered else C_WHITE, r.x + 20, r.y + 15)
                draw_btn(display_surf, "◄ BACK", F_MED, C_GREY, pygame.Rect(100, 850, 200, 55))
                
                rx = WIDTH//2 + 50
                pygame.draw.line(display_surf, C_STONE, (WIDTH//2, 100), (WIDTH//2, HEIGHT-100), 2)
                if hovered_item:
                    draw_text(display_surf, f"{hovered_item['icon']} {hovered_item['name']}", F_BIG, hovered_item['color'], rx, 220)
                    draw_text_wrapped(display_surf, hovered_item['desc'], F_SM, C_WHITE, rx, 300, 800, center=False)
                    draw_text_wrapped(display_surf, f"\"{hovered_item['lore']}\"", F_MED, C_STONE2, rx, 400, 800, center=False)
                else:
                    draw_text(display_surf, "Hover over a Talisman to view its properties.", F_MED, C_GREY, rx, HEIGHT//2)
                    
            elif menu_view=="merchant_shop":
                draw_text(display_surf, "— MERCHANT —", F_BIG, C_CYAN, WIDTH//4, 100, center=True)
                if player:
                    draw_text(display_surf, f"YOUR ESSENCE: ◆{meta['divine_essence']}", F_MED, C_GOLD, WIDTH//4, 160, center=True)
                    hovered_item = None
                    mx, my = get_mouse_pos()
                    for bi, item in enumerate(MERCHANT_SHOP_ITEMS):
                        k, name, cost, col, desc, lore = item
                        r = pygame.Rect(100, 220 + bi*80, 500, 60)
                        if r not in current_menu_rects: current_menu_rects.append(r)
                        avail = True
                        curr_text = ""
                        if k == "flasks": 
                            curr_text = f"[{run.get('flasks',3)}/3]"
                            if run.get("flasks", 3) >= 3: avail = False
                        elif k == "max_hp": curr_text = f"[current: {player.max_hp}]"
                        elif k == "ult":
                            if player.ult_cd <= 0: avail = False
                        
                        can = (avail and meta["divine_essence"] >= cost)
                        is_hovered = r.collidepoint(mx, my) or (using_gamepad and current_menu_rects.index(r) == pad_menu_idx)
                        if is_hovered: hovered_item = (name, cost, col, desc, lore, curr_text, can, avail)
                        
                        btn_lbl = f"{name}  ◆{cost}  {curr_text}" if avail else f"{name}  [MAXED/FULL]"
                        
                        if draw_btn(display_surf, btn_lbl, F_SM, col, r, col if can else None, disabled=not can):
                            if is_action_pressed("interact") and can and pad_menu_cooldown <= 0:
                                meta["divine_essence"] -= cost
                                if k == "flasks": run["flasks"] = 3
                                elif k == "max_hp": player.max_hp += 1; player.hp += 1
                                elif k == "ult": player.ult_cd = 0
                                audio.play("relic", 0.8)
                                pad_menu_cooldown = 20
                        
                    draw_btn(display_surf, "◄ LEAVE", F_MED, C_GREY, pygame.Rect(100, 850, 200, 55))
                    
                    rx = WIDTH//2 + 50
                    pygame.draw.line(display_surf, C_STONE, (WIDTH//2, 100), (WIDTH//2, HEIGHT-100), 2)
                    if hovered_item:
                        name, cost, col, desc, lore, curr_text, can, avail = hovered_item
                        draw_text(display_surf, name, F_BIG, col, rx, 220)
                        draw_text(display_surf, f"Cost: ◆{cost}   {curr_text}", F_MED, C_GOLD if can else C_RED, rx, 290)
                        draw_text_wrapped(display_surf, desc, F_SM, C_WHITE, rx, 350, 800, center=False)
                        draw_text_wrapped(display_surf, f"\"{lore}\"", F_MED, C_STONE2, rx, 450, 800, center=False)
                    else:
                        draw_text(display_surf, "Hover over an item to see details.", F_MED, C_GREY, rx, HEIGHT//2)
                        
            elif menu_view=="sanctum_shop":
                draw_text(display_surf, "— THE SANCTUM —", F_BIG, C_RUNEGLOW, WIDTH//4, 100, center=True)
                if player:
                    draw_text(display_surf, f"YOUR ESSENCE: ◆{meta['divine_essence']}", F_MED, C_GOLD, WIDTH//4, 160, center=True)
                    hovered_item = None
                    mx, my = get_mouse_pos()
                    for bi, item in enumerate(SANCTUM_SHOP_ITEMS):
                        k, name, cost, col, desc, lore = item
                        r = pygame.Rect(100, 220 + bi*70, 500, 60)
                        if r not in current_menu_rects: current_menu_rects.append(r)
                        avail = True
                        curr_text = ""
                        if k == "upg_max_hp": curr_text = f"[cur: {meta['upg_max_hp']}]"
                        elif k == "upg_dash_cd": curr_text = f"[cd: {meta['upg_dash_cd']}]"; avail = meta["upg_dash_cd"] > 35
                        elif k in ["upg_double_jump", "upg_blink", "upg_ult"]: curr_text = "[OWNED]" if meta[k] else ""; avail = not meta[k]
                        elif k == "upg_parry_window": curr_text = f"[win: {meta['upg_parry_window']}]"; avail = meta["upg_parry_window"] < 22
                        elif k == "upg_relic_slots": curr_text = f"[slots: {meta['upg_relic_slots']}]"; avail = meta["upg_relic_slots"] < 5
                        elif k == "reforge": curr_text = f"[bonus: +{meta.get('reforge_bonus',0)}]"
                        
                        can = (avail and meta["divine_essence"] >= cost)
                        is_hovered = r.collidepoint(mx, my) or (using_gamepad and current_menu_rects.index(r) == pad_menu_idx)
                        if is_hovered: hovered_item = (name, cost, col, desc, lore, curr_text, can, avail)
                        
                        btn_lbl = f"{name}  ◆{cost}  {curr_text}" if avail else f"{name}  [MAXED/OWNED]"
                        
                        if draw_btn(display_surf, btn_lbl, F_SM, col, r, col if can else None, disabled=not can):
                            if is_action_pressed("interact") and can and pad_menu_cooldown <= 0:
                                meta["divine_essence"] -= cost
                                if k == "upg_max_hp": meta[k]+=1; player.max_hp+=1; player.hp+=1
                                elif k == "upg_dash_cd": meta[k]-=5
                                elif k in ["upg_double_jump","upg_blink","upg_ult"]: meta[k]=True
                                elif k == "upg_parry_window": meta[k]+=2
                                elif k == "upg_relic_slots": meta[k]+=1
                                elif k == "reforge": meta["reforge_bonus"] = meta.get("reforge_bonus", 0) + 1
                                audio.play("relic", 0.8)
                                save_meta()
                                pad_menu_cooldown = 20
                        
                    draw_btn(display_surf, "◄ LEAVE", F_MED, C_GREY, pygame.Rect(100, 850, 200, 55))
                    
                    rx = WIDTH//2 + 50
                    pygame.draw.line(display_surf, C_STONE, (WIDTH//2, 100), (WIDTH//2, HEIGHT-100), 2)
                    if hovered_item:
                        name, cost, col, desc, lore, curr_text, can, avail = hovered_item
                        draw_text(display_surf, name, F_BIG, col, rx, 220)
                        draw_text(display_surf, f"Cost: ◆{cost}   {curr_text}", F_MED, C_GOLD if can else C_RED, rx, 290)
                        draw_text_wrapped(display_surf, desc, F_SM, C_WHITE, rx, 350, 800, center=False)
                        draw_text_wrapped(display_surf, f"\"{lore}\"", F_MED, C_STONE2, rx, 450, 800, center=False)
                    else:
                        draw_text(display_surf, "Hover over an item to see details.", F_MED, C_GREY, rx, HEIGHT//2)
                        
            elif menu_view=="settings":
                _sy=HEIGHT//2-280
                draw_text(display_surf,"-- SETTINGS --",F_BIG,C_PARCH,WIDTH//2,_sy,center=True)
                draw_text(display_surf,"MUSIC VOLUME",F_SM,C_GREY,WIDTH//2,_sy+75,center=True)
                draw_btn(display_surf,"<",F_BIG,C_CYAN,pygame.Rect(WIDTH//2-180,_sy+88,50,45))
                draw_text(display_surf,f"{int(audio.bgm_vol*100)}%",F_MED,C_WHITE,WIDTH//2,_sy+93,center=True)
                draw_btn(display_surf,">",F_BIG,C_CYAN,pygame.Rect(WIDTH//2+130,_sy+88,50,45))
                draw_text(display_surf,"SFX VOLUME",F_SM,C_GREY,WIDTH//2,_sy+155,center=True)
                draw_btn(display_surf,"<",F_BIG,C_CYAN,pygame.Rect(WIDTH//2-180,_sy+168,50,45))
                draw_text(display_surf,f"{int(audio.sfx_vol*100)}%",F_MED,C_WHITE,WIDTH//2,_sy+173,center=True)
                draw_btn(display_surf,">",F_BIG,C_CYAN,pygame.Rect(WIDTH//2+130,_sy+168,50,45))
                draw_text(display_surf,"RESOLUTION",F_SM,C_GREY,WIDTH//2,_sy+235,center=True)
                draw_btn(display_surf,"<",F_BIG,C_CYAN,pygame.Rect(WIDTH//2-180,_sy+248,50,45))
                _rw,_rh=RESOLUTIONS[curr_res_idx]
                draw_text(display_surf,f"{_rw} x {_rh}",F_MED,C_WHITE,WIDTH//2,_sy+253,center=True)
                draw_btn(display_surf,">",F_BIG,C_CYAN,pygame.Rect(WIDTH//2+130,_sy+248,50,45))
                _fscol=C_CYAN if is_fullscreen else C_GREY
                draw_btn(display_surf,f"FULLSCREEN: {'ON' if is_fullscreen else 'OFF'}",F_SM,_fscol,pygame.Rect(WIDTH//2-110,_sy+315,220,42))
                draw_text(display_surf,"click to toggle  -  APPLY to confirm",F_TINY,C_STONE2,WIDTH//2,_sy+368,center=True)
                draw_btn(display_surf,"< BACK",F_MED,C_GREY,pygame.Rect(WIDTH//2-200,_sy+400,180,55))
                draw_btn(display_surf,"APPLY",F_MED,C_CYAN,pygame.Rect(WIDTH//2+20,_sy+400,180,55))
                draw_btn(display_surf,"RESET & QUIT",F_SM,C_RED,pygame.Rect(WIDTH//2-100,_sy+468,200,45))
            elif menu_view=="controls":
                draw_text(display_surf,"— KEYBINDS —",F_BIG,C_GOLD,WIDTH//2,HEIGHT//2-270,center=True)
                draw_text(display_surf,"Click any action to rebind it (Keyboard or Gamepad)",F_SM,C_GREY,WIDTH//2,HEIGHT//2-222,center=True)
                bind_list=list(meta["binds"].items()); cols=2; n_rows=(len(bind_list)+cols-1)//cols
                table_h=n_rows*55; start_y=HEIGHT//2-table_h//2-20
                ACTION_LABELS={"left":"MOVE LEFT","right":"MOVE RIGHT","up":"LOOK UP","down":"CROUCH","jump":"JUMP","dash":"DASH","atk":"ATTACK","bolt":"BOLT SHOT","blink":"VOID BLINK","ult":"SOUL REND ULT","flask":"USE FLASK","stance":"CHANGE STANCE","interact":"INTERACT","trinket":"USE TRINKET", "cleave":"HOLLOW CLEAVE"}
                mx,my = get_mouse_pos()
                for idx,(act,key_val) in enumerate(bind_list):
                    col_x=WIDTH//2-350+(idx%cols)*400; row_y=start_y+(idx//cols)*55
                    label=ACTION_LABELS.get(act,act.upper()); key_name=pygame.key.name(key_val).upper()
                    pad_btn = meta["pad_binds"].get(act)
                    pad_str = f" / JOY:{pad_btn}" if pad_btn is not None else ""
                    
                    r = pygame.Rect(col_x,row_y,300,45)
                    if r not in current_menu_rects: current_menu_rects.append(r)
                    is_hovered=r.collidepoint(mx,my) or (using_gamepad and current_menu_rects.index(r) == pad_menu_idx)
                    is_active=(binding_action==act)
                    
                    if is_action_pressed("interact") and is_hovered and pad_menu_cooldown <= 0:
                        binding_action = act
                        pad_menu_cooldown = 20
                    
                    bg_col=(40,30,0) if is_active else ((20,15,35) if is_hovered else (12,8,20))
                    bg=pygame.Surface((300,45),pygame.SRCALPHA); bg.fill((*bg_col,200)); display_surf.blit(bg,(col_x,row_y))
                    border_col=C_GOLD if is_active else (C_RUNEGLOW if is_hovered else C_STONE)
                    pygame.draw.rect(display_surf,border_col,r,2,border_radius=4)
                    draw_text(display_surf,label,F_SM,C_PARCH if not is_active else C_GOLD,col_x+12,row_y+12)
                    key_surf=F_TINY.render(f"[{key_name}{pad_str}]",True,C_CYAN if not is_active else C_GOLD); display_surf.blit(key_surf,(col_x+300-key_surf.get_width()-10,row_y+14))
                draw_btn(display_surf,"◄ BACK",F_MED,C_GREY,pygame.Rect(WIDTH//2-110,HEIGHT-90,220,55))

    elif STATE in ("game", "sanctum", "training"):
        keys_state = pygame.key.get_pressed()
        # Merge get_pressed() with manual _held_keys tracking
        # _held_keys is reliable even when gamepad steals SDL focus
        keys = list(keys_state)
        for _kc, _kv in _held_keys.items():
            if _kv and 0 <= _kc < len(keys):
                keys[_kc] = True
        pad_inputs = get_gamepad_inputs()
        if hit_stop_timer > 0: 
            hit_stop_timer = max(0.0, hit_stop_timer - dt_mult)
        else:
            if bullet_time_timer > 0: 
                bullet_time_timer -= 1
                time_scale = 1.0 if bullet_time_timer <= 0 else time_scale
            
            edt = dt_mult * time_scale
            for m in motes: m.update(edt)
            for t in torches: t.update(edt)
            update_parry_vfx(edt)
            _tick_talismans(edt)
            
            for e in enemies:
                if hasattr(e,'update'): 
                    e.update(player, platforms, edt) if isinstance(e, (Grunt, Bulwark, Wraith, TrainingDummy)) else e.update(player, edt) if isinstance(e, Seraph) else None
            enemies[:] = [e for e in enemies if e.alive]
            
            if boss_obj: boss_obj.update(player, edt)
            if companion: companion.update(player, edt)

            
            _keys_len = len(keys)
            for action, key_code in meta["binds"].items():
                pad_val = meta["pad_binds"].get(action)
                if isinstance(pad_val, int) and pad_inputs.get(action):
                    if 0 <= key_code < _keys_len:
                        keys[key_code] = True
                elif pad_val in ("LT", "RT") and pad_inputs.get(action):
                    if 0 <= key_code < _keys_len:
                        keys[key_code] = True

            if player and player.alive:
                player.update(keys, pad_inputs, int(camera_x), dt_mult)
                plists = [e.projs for e in enemies] + ([boss_obj.projs] if boss_obj else [])
                player.try_parry(plists)

            for p in player_projs: p.update(player, dt_mult)
            player_projs[:] = [p for p in player_projs if p.alive]
            
            for d in essence_drops: d.update(player, dt_mult)
            essence_drops[:] = [d for d in essence_drops if not d.collected and d.life > 0]
            
            for r in relic_pickups: r.update(player, dt_mult)
            relic_pickups[:] = [r for r in relic_pickups if r.alive]
            
            for tc in treasure_chests: tc.update(player, edt)
            treasure_chests[:] = [tc for tc in treasure_chests if tc.alive]
            
            for vt in void_tears: vt.update(edt)
            void_tears[:] = [vt for vt in void_tears if vt.alive]
            
            for at in abyssal_tears: at.update(edt)
            abyssal_tears[:] = [at for at in abyssal_tears if at.alive]
            
            update_particles(edt); update_dmg_numbers(edt)

            if STATE == "game": floor_time_s += raw_dt / 1000.0
            
            for eo in env_objects: eo.update(player, edt)
            env_objects[:] = [eo for eo in env_objects if eo.alive]

            all_alive = [e for e in enemies if e.alive]
            for d in doors:
                d.update(edt)
                if d.locked and len(all_alive) == 0 and (not boss_obj or not boss_obj.alive): 
                    d.unlock()

            if player and player.alive and len(all_alive) == 0 and (not boss_obj or not boss_obj.alive):
                if any(not d.locked for d in doors):
                    if getattr(build_floor, '_announced', None) != run["floor"]:
                        build_floor._announced = run["floor"]
                        announce(STORY_DIALOGUE.get("path_cleared", "PATH CLEARED — PROCEED") if meta["bosses_defeated"] == 0 else STORY_DIALOGUE.get("path_cleared_sanctum", "PATH CLEARED — PROCEED  •  OR VISIT THE INEVITABLE"), C_CYAN, 150)
                        if player: spawn_particles(player.rect.centerx, player.rect.centery, 38, [C_CYAN, C_RUNEGLOW, C_WHITE, C_PURPLE], speed=6, gravity=-0.08, sz=(2,7), life=(18,45))

            door_triggered = next((d for d in doors if d.is_open), None)
            if door_triggered:
                tgt = door_triggered.target; door_triggered.is_open = False; door_triggered.opening = False; door_triggered.open_t = 0; transition_t = 28
                if tgt.startswith("floor"):
                    fl = int(tgt.replace("floor", "")); run["floor"] = fl; floor_time_s = 0.0; player.pos.x = 200; player.rect.x = 200; player.pos.y = GROUND_Y - 80; player.rect.y = int(player.pos.y); camera_x = 0.0; build_floor(fl); STATE = "game"
                elif tgt == "boss_room":
                    run["floor"] = 4; floor_time_s = 0.0; player.pos.x = 200; player.rect.x = 200; player.pos.y = GROUND_Y - 80; player.rect.y = int(player.pos.y); camera_x = 0.0; build_boss_room(); STATE = "game"
                elif tgt == "new_run": 
                    start_new_run()
                elif tgt == "master_loop":
                    meta["curse_level"] = meta.get("curse_level", 0) + 1
                    save_meta()
                    _saved_relics    = list(run["relics"])
                    _saved_talismans = list(active_talismans)
                    run.update({
                        "floor": 1, "kills": 0, "relics": _saved_relics,
                        "relic_offered": list(_saved_relics),
                        "curse_active": True, "iron_will_used": False,
                        "double_jump_used": False, "sanctum_return_floor": None,
                        "parries_this_run": 0, "trinket": None, "flasks": 3,
                        "floor_curse_shown": False, "parry_heal_counter": 0,
                        "treasure_rooms_found": 0, "wraiths_killed": 0,
                        "slayer_spawned": False
                    })
                    active_talismans.clear()
                    active_talismans.extend(_saved_talismans)
                    player.sync()
                    player.pos.x = 200; player.rect.x = 200
                    player.pos.y = GROUND_Y - 80; player.rect.y = int(player.pos.y)
                    camera_x = 0.0; floor_time_s = 0.0
                    build_floor(1); STATE = "game"
                    announce(f"MASTER MODE: CURSE LEVEL INCREASED TO {meta['curse_level']}", C_BLOOD, 260)
                elif tgt == "sanctum_midrun":
                    run["sanctum_return_floor"] = run["floor"]; player.pos.x = 200; player.rect.x = 200; player.pos.y = GROUND_Y - 80; player.rect.y = int(player.pos.y); camera_x = 0.0; build_sanctum(midrun=True); STATE = "sanctum"
                elif tgt == "sanctum_enter":
                    player.pos.x = 200; player.rect.x = 200; player.pos.y = GROUND_Y - 80; player.rect.y = int(player.pos.y); camera_x = 0.0; build_sanctum(); STATE = "sanctum"
                elif tgt == "return_to_floor":
                    fl = (run.get("sanctum_return_floor") or 1) + 1; run["floor"] = fl; run["sanctum_return_floor"] = None; player.pos.x = 200; player.rect.x = 200; player.pos.y = GROUND_Y - 80; player.rect.y = int(player.pos.y); camera_x = 0.0
                    if fl < 4: build_floor(fl)
                    else: build_boss_room()
                    STATE = "game"
                elif tgt == "return_menu":
                    STATE = "main_menu"; menu_view = "main"; audio.bgm("bgm_explore", audio.bgm_vol)

            if boss_obj and not boss_obj.alive and boss_obj.death_t <= 0:
                if not any(d.target == "sanctum_enter" for d in doors):
                    interact_key = "A" if using_gamepad else pygame.key.name(meta["binds"]["interact"]).upper()
                    vd = Door(2600, GROUND_Y - 170, C_GOLD, f"ENTER SANCTUM [{interact_key}]", "sanctum_enter"); vd.locked = False; doors.append(vd); announce(STORY_DIALOGUE.get("aetheria_death", "AETHERIA SLAIN — THE SANCTUM OPENS"), C_GOLD, 220); audio.bgm("bgm_explore", audio.bgm_vol)

            if combo_timer > 0: combo_timer -= dt_mult; combo_count = 0 if combo_timer <= 0 else combo_count
            for ann in announce_queue: ann[2] -= dt_mult
            announce_queue[:] = [a for a in announce_queue if a[2] > 0]
            
            if player: camera_x += (player.rect.centerx - camera_x - WIDTH // 2) / 10; camera_x = max(0, camera_x)

            hbs = audio.sounds.get("heartbeat")
            if hbs:
                if player and player.alive and player.hp <= 1 and not _hb_playing: 
                    _hb_playing = True; audio.ch_hb.play(hbs, loops=-1); audio.ch_hb.set_volume(0.6)
                elif (not player or not player.alive or player.hp > 1) and _hb_playing: 
                    _hb_playing = False; audio.ch_hb.stop()

        draw_game()

        if STATE == "sanctum":
            npc_x = 800 - int(camera_x); npc_y = GROUND_Y - 160
            if _NPC_IMG: display_surf.blit(_NPC_IMG, (npc_x - _NPC_IMG.get_width() // 2 + 40, npc_y - _NPC_IMG.get_height() + 100))
            else:
                ns = pygame.Surface((80, 100), pygame.SRCALPHA); pygame.draw.ellipse(ns, (*C_RUNEGLOW, 180), (15, 15, 50, 70)); pygame.draw.circle(ns, (*C_RUNEGLOW, 220), (40, 14), 12); display_surf.blit(ns, (npc_x, npc_y))
            
            interact_key = "A" if using_gamepad else pygame.key.name(meta["binds"]["interact"]).upper()
            lb = F_SM.render(f"THE INEVITABLE [{interact_key}]", True, C_RUNEGLOW); display_surf.blit(lb, (npc_x + 40 - lb.get_width() // 2, npc_y - 22))
            if player and pygame.Rect(800, GROUND_Y - 160, 80, 100).colliderect(player.rect): 
                ht = F_SM.render(STORY_DIALOGUE.get("inevitable_prompt", "Press {key} to speak").format(key=interact_key), True, C_RUNEGLOW); display_surf.blit(ht, (WIDTH // 2 - ht.get_width() // 2, HEIGHT // 2 - 80))

    if binding_action is not None:
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((0, 0, 0, 210)); display_surf.blit(ov, (0, 0))
        draw_text(display_surf, f"PRESS ANY KEY/BUTTON TO BIND: {binding_action.upper()}", F_BIG, C_GOLD, WIDTH // 2, HEIGHT // 2, center=True)
        draw_text(display_surf, "PRESS [ESC] TO CANCEL", F_SM, C_GREY, WIDTH // 2, HEIGHT // 2 + 60, center=True)

    if transition_t > 0:
        a = int(255 * min(1.0, transition_t / 28)); ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((0, 0, 0, a)); display_surf.blit(ov, (0, 0)); transition_t = max(0, transition_t - 1)

    shake_x, shake_y = 0, 0
    if screen_shake > 0:
        shake_x = random.randint(-int(screen_shake), int(screen_shake))
        shake_y = random.randint(-int(screen_shake), int(screen_shake))
        screen_shake = max(0, screen_shake - dt_mult * 0.8)
        screen.fill((0, 0, 0)) 

    screen.blit(pygame.transform.scale(display_surf, (WINDOW_W, WINDOW_H)), (shake_x, shake_y))
    pygame.display.flip()
