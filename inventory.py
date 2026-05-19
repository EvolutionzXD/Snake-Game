import json
import os

class InventoryManager:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None: cls._instance = cls()
        return cls._instance

    def __init__(self):
        from arsenal import WEAPON_CATALOG
        # self.weapons: { name: {"level": level, "is_awakened": bool} }. Level 0 = Locked.
        self.weapons = {name: {"level": 0, "is_awakened": False} for name in WEAPON_CATALOG.keys()}
        self.weapons["Pistol"] = {"level": 1, "is_awakened": False}
        self.weapons["LeafBlower"] = {"level": 1, "is_awakened": False}
        self.weapons["AirSword"] = {"level": 1, "is_awakened": False}
        
        # Loadout mặc định
        self.equipped_weapons = ["Pistol", "LeafBlower", "AirSword"]
        self.current_slot_idx = 0

    def is_unlocked(self, weapon_id):
        """Kiểm tra xem vũ khí đã được mở khóa chưa (Lv > 0)."""
        return self.weapons.get(weapon_id, {}).get("level", 0) > 0

    def get_level(self, weapon_id):
        """Lấy cấp độ hiện tại của vũ khí."""
        return self.weapons.get(weapon_id, {}).get("level", 0)

    def set_level(self, weapon_id, level):
        """Đặt cấp độ cho vũ khí."""
        if weapon_id in self.weapons:
            self.weapons[weapon_id]["level"] = level

    def is_awakened(self, weapon_id):
        """Kiểm tra vũ khí đã thức tỉnh chưa."""
        return self.weapons.get(weapon_id, {}).get("is_awakened", False)

    def set_awakened(self, weapon_id, status):
        """Đặt trạng thái thức tỉnh."""
        if weapon_id in self.weapons:
            self.weapons[weapon_id]["is_awakened"] = status

    def equip_weapon(self, slot_idx, weapon_id):
        """Lắp một vũ khí vào slot tương ứng (0, 1, 2). Chỉ cho phép nếu đã mở khóa (Lv > 0)."""
        if 0 <= slot_idx < 3 and self.is_unlocked(weapon_id):
            if weapon_id in self.equipped_weapons:
                old_idx = self.equipped_weapons.index(weapon_id)
                self.equipped_weapons[old_idx] = self.equipped_weapons[slot_idx]
            
            self.equipped_weapons[slot_idx] = weapon_id
            return True
        return False

    def get_equipped_list(self):
        return self.equipped_weapons

    def get_active_weapon_id(self):
        return self.equipped_weapons[self.current_slot_idx]

    def load_data(self, data):
        """Nạp dữ liệu inventory từ save file."""
        if "inventory" in data:
            inv = data["inventory"]
            # Nạp dictionary levels & awakened status
            saved_weapons = inv.get("weapons", {})
            for wid, info in saved_weapons.items():
                # Migration: Chuyển dữ liệu từ SMG cũ sang LeafBlower mới
                target_id = "LeafBlower" if wid == "SMG" else wid
                
                if target_id in self.weapons:
                    if isinstance(info, dict):
                        self.weapons[target_id] = info
                    else:
                        # Convert từ format cũ (chỉ có level)
                        self.weapons[target_id] = {"level": info, "is_awakened": False}
            
            # Cũ: support mảng unlocked cũ
            old_unlocked = inv.get("unlocked", [])
            for wid in old_unlocked:
                target_id = "LeafBlower" if wid == "SMG" else wid
                if target_id in self.weapons and self.weapons[target_id]["level"] == 0:
                    self.weapons[target_id] = {"level": 1, "is_awakened": False}

            # Nạp loadout và migrate SMG -> LeafBlower trong slot đang đeo
            raw_equipped = inv.get("equipped", self.equipped_weapons)
            self.equipped_weapons = ["LeafBlower" if w == "SMG" else w for w in raw_equipped]
            while len(self.equipped_weapons) < 3:
                self.equipped_weapons.append("Pistol")
            self.equipped_weapons = self.equipped_weapons[:3]

    def save_data(self):
        """Trả về dictionary để lưu vào save file."""
        return {
            "weapons": self.weapons, 
            "equipped": self.equipped_weapons
        }
