import pygame

class Upgrade:
    def __init__(self, id, name, description, icon_name, effect_fn):
        self.id = id
        self.name = name
        self.description = description
        self.icon_name = icon_name
        self.effect_fn = effect_fn

    def apply(self):
        self.effect_fn()

def get_available_upgrades():
    from apple import AppleManager
    
    # Tính toán phần trăm buff hiện tại
    hp_boost = (1.03 ** AppleManager.hp_lvl) * 100
    stamina_boost = (1.03 ** AppleManager.stamina_lvl) * 100
    dmg_boost = (1.03 ** AppleManager.dmg_lvl) * 100
    
    return [
        Upgrade(
            "max_hp", 
            f"HP.Lvl {AppleManager.hp_lvl}", 
            f"HP Boost: {hp_boost:.2f}%", 
            "heart_icon", 
            lambda: AppleManager.apply_upgrade("max_hp")
        ),
        Upgrade(
            "max_stamina", 
            f"Stamina.Lvl {AppleManager.stamina_lvl}", 
            f"Stamina Boost: {stamina_boost:.2f}%", 
            "stamina_icon", 
            lambda: AppleManager.apply_upgrade("max_stamina")
        ),
        Upgrade(
            "damage_mult", 
            f"Dmg.Lvl {AppleManager.dmg_lvl}", 
            f"Dmg Boost: {dmg_boost:.2f}%", 
            "dmg_icon", 
            lambda: AppleManager.apply_upgrade("damage_mult")
        )
    ]
