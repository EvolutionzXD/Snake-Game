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
    
    return [
        Upgrade(
            "max_hp", 
            "MAX HP", 
            "+25 Giới hạn máu & Hồi đầy máu", 
            "heart_icon", 
            lambda: AppleManager.apply_upgrade("max_hp")
        ),
        Upgrade(
            "max_stamina", 
            "MAX STAMINA", 
            "+200 Giới hạn thể lực & Hồi đầy", 
            "stamina_icon", 
            lambda: AppleManager.apply_upgrade("max_stamina")
        ),
        Upgrade(
            "damage_mult", 
            "DAMAGE BOOST", 
            "+15% Sát thương cho tất cả vũ khí", 
            "dmg_icon", 
            lambda: AppleManager.apply_upgrade("damage_mult")
        )
    ]
