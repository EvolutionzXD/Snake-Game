import json
import os

class SaveSystem:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.current_slot = 1
        self.save_dir = "saves"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def set_current_slot(self, slot_num):
        self.current_slot = slot_num

    def get_save_path(self, slot_num=None):
        slot = slot_num if slot_num is not None else self.current_slot
        return os.path.join(self.save_dir, f"save_{slot}.json")

    def save_game(self, username, exp, level, unlocked_wave, hp_lvl, stamina_lvl, dmg_lvl, coins=0, status_points=0):
        data = {
            "username": username,
            "exp": exp,
            "level": level,
            "unlocked_wave": unlocked_wave,
            "hp_lvl": hp_lvl,
            "stamina_lvl": stamina_lvl,
            "dmg_lvl": dmg_lvl,
            "coins": coins,
            "status_points": status_points
        }
        with open(self.get_save_path(), "w") as f:
            json.dump(data, f)
            
    def get_save_summary(self, slot_num):
        path = self.get_save_path(slot_num)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    return {
                        "is_empty": False,
                        "username": data.get("username", f"Player {slot_num}"),
                        "level": data.get("level", 1),
                        "wave": data.get("unlocked_wave", 1),
                        "coins": data.get("coins", 0)
                    }
            except:
                pass
        return {"is_empty": True}

    def load_game(self, slot_num=None):
        path = self.get_save_path(slot_num)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    return data
            except:
                pass
        
        # Default save data if no file exists
        return {
            "username": f"Player {slot_num if slot_num else self.current_slot}",
            "exp": 0,
            "level": 1,
            "unlocked_wave": 1,
            "max_hp_bonus": 0.0,
            "max_stamina_bonus": 0.0,
            "damage_mult": 1.0
        }

    def delete_save(self, slot_num):
        path = self.get_save_path(slot_num)
        if os.path.exists(path):
            os.remove(path)
