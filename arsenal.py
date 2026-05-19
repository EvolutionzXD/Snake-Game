from weapon import Gun, Sword, Flamethrower, StandWeapon, FlameExtinguisher, RealitySlash, TarotCardWeapon
from config import (GetProjectileConfig, GetSwordAirDashConfig, GetFlameConfig, 
                    GetGhostPunchConfig, GetFoamConfig, GetSlashConfig, GetCardDummyConfig)

# WEAPON_CATALOG - "Từ điển" chứa thông số gốc và lộ trình nâng cấp của vũ khí
# Cấu trúc: ID: { class, args, kwargs, description, color, max_level, upgrades }
WEAPON_CATALOG = {
    "Pistol": {
        "class": Gun,
        "args": ("Pistol", GetProjectileConfig),
        "kwargs": {"texture_name": "pistol", "fire_rate": 0.4, "speed": 4000.0, "arm_len": 5, "stick_len": 30, "scale": 2, "stamina_cost": 0.0},
        "description": "Normal gun, reliable and doesn't cost stamina.",
        "color": (200, 200, 200),
        "avatar": "pistol",
        "max_level": 5,
        "upgrades": {
            2: {"cost": (20, 0), "desc": "Lightweight mechanism (+5% Fire Rate)", "kwargs_update": {"fire_rate": 0.38}},
            3: {"cost": (30, 0), "desc": "Polished barrel (+5% Fire Rate)", "kwargs_update": {"fire_rate": 0.36}},
            4: {"cost": (40, 10), "desc": "Better trigger (+5% Fire Rate)", "kwargs_update": {"fire_rate": 0.34}},
            5: {"cost": (50, 10), "desc": "Match grade components (+5% Fire Rate)", "kwargs_update": {"fire_rate": 0.32}},
            "awaken": {"cost": (100, 10), "desc": "Your first awakened!", "kwargs_update": {"fire_rate": 0.1}}
        }
    },
    "LeafBlower": {
        "class": Flamethrower,
        "args": ("LeafBlower", GetProjectileConfig),
        "kwargs": {"fire_rate": 0.1, "speed": 2000.0, "arm_len": 2, "stick_len": 35, "recoil": 5, "scale": 1.5, "stamina_cost": 0.5, "shot_count": 6, "damage_override": 0.0},
        "description": "ZERO damage, but look at those leaves fly!",
        "color": (100, 255, 100),
        "avatar": "pistol",
        "max_level": 1,
        "upgrades": {
            "awaken": {"cost": (300, 40), "desc": "Please turn off particle T^T", "kwargs_update": {"fire_rate": 0.05, "shot_count": 30, "speed": 1500, "scale": 2.0}}
        }
    },
    "AirSword": {
        "class": Sword,
        "args": ("AirSword", GetSwordAirDashConfig),
        "kwargs": {"texture_name": "stick", "fire_rate": 0.5, "speed": 0.0, "arm_len": 2, "stick_len": 50, "recoil": 0, "scale": 2.5, "stamina_cost": 15.0},
        "description": "Call it a sword, but it's just a stick.",
        "color": (150, 200, 255),
        "avatar": "stick",
        "max_level": 1,
        "upgrades": {
            "awaken": {"cost": (250, 30), "desc": "STORM KING: Colossal stick, Double slashes & Summon Projectiles!", "kwargs_update": {"fire_rate": 0.15, "scale": 4.5, "arm_len": 10, "stick_len": 100, "stamina_cost": 5.0}}
        }
    },
    "FlameThrower": {
        "class": Flamethrower,
        "args": ("FlameThrower", GetFlameConfig),
        "kwargs": {"texture_name": "flame_thrower", "fire_rate": 0.03, "speed": 2000.0, "arm_len": 10, "stick_len": 30, "recoil": 2, "scale": 1.8, "stamina_cost": 0.5},
        "description": "Flamethrower. Burn everything in range. [S-tier!]",
        "color": (255, 100, 50),
        "avatar": "flame_thrower",
        "max_level": 5,
        "upgrades": {
            1: {"cost": (200, 20), "desc": "PURCHASE: Burn them all!", "kwargs_update": {}},
            2: {"cost": (100, 5), "desc": "Pressurized tank (+Range)", "kwargs_update": {"speed": 2200.0}},
            3: {"cost": (150, 10), "desc": "High-octane fuel (+Range)", "kwargs_update": {"speed": 2400.0}},
            4: {"cost": (200, 15), "desc": "Reinforced nozzle (+Range)", "kwargs_update": {"speed": 2600.0}},
            5: {"cost": (300, 20), "desc": "Industrial pump (+Range)", "kwargs_update": {"speed": 2800.0}},
            "awaken": {"cost": (500, 50), "desc": "HELLFIRE: Blue flames with extreme range!", "kwargs_update": {"speed": 3500.0, "fire_rate": 0.02}}
        }
    },
    "StarPlatinum": {
        "class": StandWeapon,
        "args": ("StarPlatinum", GetGhostPunchConfig),
        "kwargs": {"texture_name": "stick", "fire_rate": 0.04, "speed": 0.0, "arm_len": 0, "stick_len": 0, "recoil": 0, "scale": 0.8, "stamina_cost": 2.0},
        "description": "It's your inner spirit.",
        "color": (180, 100, 255),
        "avatar": "stick",
        "max_level": 5,
        "upgrades": {
            1: {"cost": (250, 25), "desc": "PURCHASE: Unleash your spirit!", "kwargs_update": {}},
            2: {"cost": (50, 0), "desc": "Concentrated spirit (+5% Speed)", "kwargs_update": {"fire_rate": 0.038}},
            3: {"cost": (80, 5), "desc": "Stronger link (+5% Speed)", "kwargs_update": {"fire_rate": 0.036}},
            4: {"cost": (120, 10), "desc": "Battle hardening (+5% Speed)", "kwargs_update": {"fire_rate": 0.034}},
            5: {"cost": (200, 20), "desc": "Spiritual peak (+5% Speed)", "kwargs_update": {"fire_rate": 0.032}},
            "awaken": {"cost": (400, 40), "desc": "THE WORLD: ORA ORA ORA!", "kwargs_update": {"fire_rate": 0.02, "stamina_cost": 1.0}}
        }
    },
    "FlameExtinguisher": {
        "class": FlameExtinguisher,
        "args": ("FlameExtinguisher", GetFoamConfig),
        "kwargs": {"texture_name": "fire_extinquisher", "fire_rate": 0.03, "speed": 2000.0, "arm_len": 10, "stick_len": 30, "recoil": 2, "scale": 1.8, "stamina_cost": 0.5, "stun_override": 0.0},
        "description": "This thing can save your life from fire, and snakes [One of the best].",
        "color": (100, 200, 255),
        "avatar": "fire_extinquisher",
        "max_level": 5,
        "upgrades": {
            1: {"cost": (150, 15), "desc": "PURCHASE: Safety first, kills second.", "kwargs_update": {}},
            2: {"cost": (50, 0), "desc": "Wider nozzle (+2s Stun)", "kwargs_update": {"scale": 2.0, "stun_override": 6.0}},
            3: {"cost": (100, 5), "desc": "Higher pressure (+4s Stun)", "kwargs_update": {"speed": 2300.0, "stun_override": 8.0}},
            4: {"cost": (150, 10), "desc": "Double canister (+6s Stun)", "kwargs_update": {"stamina_cost": 0.3, "stun_override": 10.0}},
            5: {"cost": (200, 15), "desc": "Military grade foam (+8s Stun)", "kwargs_update": {"fire_rate": 0.025, "stun_override": 12.0}},
            "awaken": {"cost": (400, 30), "desc": "ICE AGE: Infinite foam, 3 DMG & 10s Freeze!", "kwargs_update": {"fire_rate": 0.02, "speed": 3000.0, "stun_override": 15.0, "damage_override": 3.0, "stamina_cost": 0.0}}
        }
    },
    "RealitySlash": {
        "class": RealitySlash,
        "args": ("RealitySlash", GetSlashConfig),
        "kwargs": {"texture_name": "RealitySlash", "fire_rate": 0.5, "speed": 0.0, "arm_len": 2, "stick_len": 50, "recoil": 0, "scale": 2.5, "stamina_cost": 35.0, "free_slash": 0, "chaos_radius": 100},
        "description": "It's just a really high damage weapon.",
        "color": (255, 50, 50),
        "avatar": "RealitySlash",
        "max_level": 5,
        "upgrades": {
            1: {"cost": (600, 60), "desc": "PURCHASE: Cut through space-time.", "kwargs_update": {}},
            2: {"cost": (150, 10), "desc": "Sharper reality (+1 Free Slash)", "kwargs_update": {"stamina_cost": 30.0, "free_slash": 1, "chaos_radius": 120}},
            3: {"cost": (250, 20), "desc": "Dimensions tear (+1 Free Slash)", "kwargs_update": {"stamina_cost": 30.0, "free_slash": 1, "chaos_radius": 150}},
            4: {"cost": (400, 30), "desc": "Void edge (+1 Free Slash)", "kwargs_update": {"stamina_cost": 20.0, "free_slash": 2, "chaos_radius": 180}},
            5: {"cost": (600, 50), "desc": "Existence erasure (+2 Free Slash)", "kwargs_update": {"stamina_cost": 20.0, "free_slash": 2, "chaos_radius": 220}},
            "awaken": {"cost": (1000, 100), "desc": "WORLD CUTTER: Extreme Chaos!", "kwargs_update": {"stamina_cost": 10.0, "free_slash": 8, "chaos_radius": 400}}
        }
    },
    "TarotCard": {
        "class": TarotCardWeapon,
        "name": "TarotCard",
        "args": ("TarotCard", GetCardDummyConfig),
        "kwargs": {"texture_name": "card", "fire_rate": 0.4, "stamina_cost": 5.0, "speed": 2500.0, "recoil_dist": 0, "scale": 4.0},
        "description": "Luck of the draw. Test your destiny!",
        "color": (255, 255, 100),
        "avatar": "card",
        "max_level": 1,
        "upgrades": {
            1: {"cost": (50, 0), "desc": "Beginner's Luck", "kwargs_update": {"fire_rate": 0.35}},
            "awaken": {"cost": (300, 30), "desc": "JACKPOT: Luck of the Draw", "kwargs_update": {"fire_rate": 0.25}}
        }
    },
}
