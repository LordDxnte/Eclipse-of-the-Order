# Eclipse of the Order

A dark fantasy action roguelite built in Python with Pygame.

Fight through cursed floors, collect relics, master your abilities, and face the Sovereign Aetheria in an escalating battle across three brutal phases.

---

## Gameplay

Each run takes you through procedurally generated floors packed with enemies. Kill everything to unlock the door and descend deeper. Survive long enough and you'll face the boss. Die and start again — but keep your Divine Essence and spend it on permanent upgrades between runs.

The game gets harder with every boss you beat. Welcome to NG+.

---

## Controls

| Key | Action |
|---|---|
| WASD / Arrow Keys | Move |
| SPACE | Jump (double jump if upgraded) |
| SHIFT | Dash |
| Left Click / F | Slash attack — or Execute a stunned enemy |
| Right Click | Void Bolt (costs Mana) |
| G | Parry |
| Q | Void Blink (upgrade required) |
| C | Soul Rend ultimate (upgrade required) |
| E | Interact / Use door |
| P / ESC | Pause |
| F11 | Toggle fullscreen |

---

## Relics

Relics are passive items collected during a run. Each one changes how you play.

- **Void Heart** — +2 Max HP this run
- **Obsidian Edge** — Attacks deal +1 damage
- **Wraith's Grace** — Dash has 2 charges
- **Soul Siphon** — Kills restore 1 HP
- **Thorn Mantle** — Parry stuns melee enemies
- **Void Echo** — Blink damages in a radius
- **Cursed Blade** — +50% damage, -1 max HP
- **Gilded Soul** — +25% essence gain
- **Iron Will** — First lethal hit leaves you at 1 HP
- **Plague Touch** — Attacks poison enemies

---

## Permanent Upgrades

Spend Divine Essence at The Inevitable (the Sanctum NPC) between runs:

- +1 Max HP
- Faster Dash cooldown
- Double Jump
- Void Blink
- Soul Rend Ultimate
- Wider Parry window
- Extra Relic slots

---

## The Boss — Sovereign Aetheria

Three phases. Each one worse than the last.

- **Phase I** — Ranged attacks, aggressive pursuit
- **Phase II** — Invulnerable until you collect all 4 scattered keys
- **Phase III** — Charges, summons adds, relentless pressure

Break her posture to stagger her. Execute her while stunned for massive damage.

---

## Running from Source

**Requirements:** Python 3.10+ and Pygame

```bash
pip install pygame
python3 eclipse_of_the_order.py
```

Place all assets in an `assets/` folder next to the script.

---

## Building

```bash
pip install pyinstaller
pyinstaller --onedir --windowed --name "Eclipse of the Order" --add-data "assets:assets" eclipse_of_the_order.py
```

The finished build will be in `dist/Eclipse of the Order/`.

---

## Credits

Made by **LordDxnte**  
Built with Python + Pygame
