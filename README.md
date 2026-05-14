# Eclipse of the Order

A brutal, fast-paced dark fantasy action roguelite built from scratch in Python and Pygame. 

Step into the shoes of a fallen Reaper. Fight through cursed, procedurally generated floors, collect game-breaking relics, master two distinct combat stances, and face the Sovereign Aetheria in a grueling multi-phase boss fight. Die, upgrade your arsenal in the Sanctum, and descend again. 

## ⚔️ Features (v1.0)

* **Dual-Stance Combat:** Dynamically switch between the agile *Reaper* stance and the devastating *Executioner* stance mid-combat.
* **The Talisman System:** Equip powerful modifiers like *Void Warden* or *Blood Pact* to drastically alter your playstyle and abilities.
* **Master Mode (NG+):** Defeating the boss is just the beginning. Enter the Master Loop to face escalating Curse Levels with faster enemies, elite variants, and hazardous floor modifiers.
* **Feline Companions:** Rescue and fight alongside Champa (who pounces and marks enemies for bonus damage) or Pepper (who generates a void ring to intercept projectiles).
* **Deep Progression:** 10+ Relics, permanent Sanctum upgrades, and interactive map objects like Cursed Blood Altars and Treasure Rooms.
* **Full Gamepad Support:** Seamlessly swap between Keyboard/Mouse and Controller with dynamic UI prompts.

---

## 🎮 Controls

Fully customizable in the in-game Keybinds menu.

| Action | Keyboard & Mouse | Gamepad |
| :--- | :--- | :--- |
| **Move** | `W` `A` `S` `D` | D-Pad / Left Stick |
| **Jump / Double Jump**| `SPACE` | `A` |
| **Dash** | `L-SHIFT` | `RB` |
| **Attack / Execute** | `F` or `Left Click` | `Y` |
| **Parry** | `Right Click` | `LB` |
| **Void Bolt** | `G` | `B` |
| **Use Flask** | `R` | `X` |
| **Change Stance** | `V` | `L3` (Stick Click) |
| **Hollow Cleave** | `X` | `R3` (Stick Click) |
| **Void Blink** | `Q` | `LT` |
| **Soul Rend (Ultimate)**| `C` | `RT` |
| **Interact** | `E` | `A` |

*(Note: Blink, Soul Rend, and Double Jump must be unlocked via the Sanctum).*

---

## 💀 Combat Systems

### Stances
* **Reaper Stance:** Fast attacks, standard parry windows, and access to the *Soul Rend* screen-clearing ultimate.
* **Executioner Stance:** Attacks deal 2x damage, but parry windows are halved. Replaces your ultimate with *Hollow Cleave*, a devastating offensive dash that leaves Abyssal Tears in its wake.

### Posture & Executions
Consecutive hits and successful parries drain an enemy's Stagger Meter. Once broken, the enemy is stunned. Approach a stunned enemy and press `Attack` to trigger a lethal Execution, restoring HP and granting a massive combo boost.

---

## 🛠️ Installation & Running

### Play the Standalone Executable (Windows/Linux)
Simply download the latest `.exe` from the Releases tab, extract the folder (ensure the `assets` folder is kept in the same directory as the executable), and double-click to play. No installation required.

### Run from Source
If you want to run the raw Python code or compile it yourself:

1. Ensure you have **Python 3.10+** installed.
2. Install Pygame:
   ```bash
   pip install pygame
3.Clone the repository and run the script:
```Bash
   python eclipse_of_the_order.py
