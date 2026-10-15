"""Build a bigger, hierarchical corpus for the retrieval ladder: `python gen_scaled_corpus.py [TOTAL_MODELS]` (default 15, at most 30).
Writes data/stark_scaled/{brand,general,models,manuals}/ + INDEX.md + gold.json. Deterministic (no LLM, no randomness): the
fictional manuals are templates, shared between models on purpose, so the same facts repeat across documents and
questions like "which models use a joystick?" have a gold answer computed from the same table that wrote the text."""
import json
import re
import shutil
import sys
from pathlib import Path

SRC = Path("data/stark_spaceships")
OUT = Path("data/stark_scaled")

STEERING = [
    "a force-feedback yoke. Pull to climb, push to dive. Feedback strength is set from 1 to 5 in the Controls menu; use 2 or lower with gloves.",
    "a dual-joystick station. The left stick controls translation and the right stick controls rotation. Press both stick buttons for 2 seconds to centre the ship.",
    "a fly-by-wire steering wheel. Turning the wheel yaws the ship; the wheel has a 540-degree lock-to-lock range and self-centres within 3 seconds of release.",
]
BRAKE = [
    "a 3-stage magnetic retarder. Stage 1 is gentle, stage 3 is for emergencies. Do not use stage 3 below 200 metres of altitude because it overheats the coils.",
    "retro-thruster braking. A full stop from cruise speed takes up to 40 seconds. The brake pedal blends thrusters and drag fins automatically.",
]
THROTTLE = [
    "a slider throttle with 5 detents. Detent 3 is cruise. Moving the slider past detent 4 needs the safety latch to be released.",
    "a foot-pedal throttle with cruise hold. Press the cruise button at the speed you want and release the pedal; any brake input cancels cruise hold.",
]
CLIMATE = [
    "single-zone climate control from 18 to 26 degrees Celsius. The filter must be replaced every 6 months.",
    "dual-zone climate control from 16 to 28 degrees Celsius with a separate cockpit and cabin setting. The filter must be replaced every 4 months.",
    "a fan-only cabin system with no active cooling. In hot docks, open the vent shutters before boarding. The filter must be replaced every 3 months.",
]
INTERIOR = [
    "fabric seats with an LED cabin strip. Clean with a damp cloth only; solvents fade the fabric.",
    "leather seats with wood-grain trim. Condition the leather every 3 months and keep it out of direct sunlight at the dock.",
    "bench seating covered in washable vinyl. The covers can be hosed down with fresh water.",
]
WARNING = [
    "Never fly with the cabin hatch seal warning lit.",
    "Never leave the throttle unattended during docking.",
    "Never charge the power cell unattended overnight.",
]

BRAND = {
    "about_stark.txt": ("Company background: who Stark Spaceships is, its mission and history.",
        "## About Stark Spaceships\nStark Spaceships builds consumer spaceships for families, haulers and adventurers. Founded in 2031, the company ships from three orbital yards and focuses on easy-to-fly, easy-to-repair ships. Every model is covered by the same service network."),
    "warranty_policy.txt": ("Warranty coverage, duration and exclusions.",
        "## Warranty Policy\nAll new ships carry a 3-year or 20,000-flight-hour warranty, whichever comes first. The warranty covers the hull, thrusters and power cell. It does not cover cosmetic wear, interior upholstery, or damage from skipped maintenance."),
    "contact_and_hours.txt": ("Customer service contact details and opening hours.",
        "## Contact and Hours\nEmail customer_service@stack_spaceship.com. Support is open Monday to Friday, 09:00 to 18:00 station time. Emergencies in flight should use the distress beacon, not email."),
}
GENERAL = {
    "safety_regulations.txt": ("Flight licence, no-fly zones and registration rules that apply to every model.",
        "## Safety Regulations\nEvery pilot needs a Class C personal flight licence. Ships over 20 metric tons must be registered with the orbital traffic office. Flying within 5 km of a station without clearance is prohibited."),
    "trade_in_program.txt": ("Trade-in programme: how to exchange an old ship for a new one.",
        "## Trade-in Program\nOwners can trade in any Stark ship younger than 10 years. The trade-in value is 40 percent of the original price, reduced by 5 percent for each unrepaired hull defect found at inspection."),
}


def facts(i):
    """Which variant of each component model i uses. Overlapping groups on purpose: some models share a text, some do not."""
    return {"steering": i % 3, "brake": (i // 3) % 2, "throttle": int(i % 5 == 0), "climate": (i // 2) % 3, "interior": ((i - 1) // 5) % 3}


def manual(i, seats):
    f = facts(i)
    return (f"## Stark {i} Owner's Manual\n"
            f"- **Steering**: Stark {i} uses {STEERING[f['steering']]}\n"
            f"- **Brakes**: Stark {i} stops with {BRAKE[f['brake']]}\n"
            f"- **Throttle**: Stark {i} has {THROTTLE[f['throttle']]}\n"
            f"- **Climate**: Stark {i} has {CLIMATE[f['climate']]}\n"
            f"- **Interior**: {f'Stark {i} has seating for {seats} passengers' if seats else f'Stark {i} carries crew only, no passenger seating'}; it has {INTERIOR[f['interior']]}\n"
            f"- **Service interval**: Service Stark {i} every {100 + 25 * (i % 4)} flight hours. Serial numbers start with SK{i:02d}.\n"
            f"- **Warning**: {WARNING[i % 3]}\n")


if __name__ == "__main__":
    total = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    shutil.rmtree(OUT, ignore_errors=True)
    for d in ("brand", "general", "models", "manuals"):
        (OUT / d).mkdir(parents=True)
    index = ["# Stark Spaceships document index", "Read this first; open only the documents the question needs.", ""]
    gold = {"facts": {}, "models": total}

    def write(folder, name, desc, text):
        (OUT / folder / name).write_text(text)
        index.append(f"- {folder}/{name}: {desc}")

    for name, (desc, text) in BRAND.items():
        write("brand", name, desc, text)
    for name, (desc, text) in GENERAL.items():
        write("general", name, desc, text)
    for name, desc in (("guide_ordering_delivery.txt", "How to place an order, deposit, delivery and damage reports."),
                       ("guide_troubleshooting.txt", "Step-by-step fixes: ship will not start, vibration, wrong heading, cabin pressure, routine maintenance.")):
        write("general", name, desc, (SRC / name).read_text())
    for i in range(1, total + 1):
        text = (SRC / f"model_{i}.txt").read_text()
        m = re.search(r"\*\*Capacity\*\*: (\d+) passengers", text)
        seats = int(m.group(1)) if m else 0  # some specs list crew or cargo, not passengers
        write("models", f"model_{i}.txt", f"Stark {i} specification sheet: size, weight, capacity, colour, price, accessories.", text)
        write("manuals", f"manual_{i}.txt", f"Stark {i} owner's manual: steering, brakes, throttle, climate, interior, service interval, warning.", manual(i, seats))
        gold["facts"][i] = facts(i)
    (OUT / "INDEX.md").write_text("\n".join(index) + "\n")
    (OUT / "gold.json").write_text(json.dumps(gold, indent=1))
    n = sum(1 for _ in OUT.rglob("*.txt"))
    print(f"{n} docs, {sum(p.stat().st_size for p in OUT.rglob('*.txt'))} bytes -> {OUT}")
