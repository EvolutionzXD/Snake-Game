import json
import os

class SettingsManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SettingsManager()
        return cls._instance

    def __init__(self):
        self.filepath = "settings.json"
        
        # Cấu trúc dữ liệu mặc định
        self.settings = {
            "video": {
                "show_fps": True,
                "show_hitbox": False,
                "show_grid": False,
                "screen_shake": True,
                "particles": True
            },
            "gameplay": {
                "auto_collect_exp": False,
                "show_damage_numbers": True,
                "show_enemy_hp": True
            },
            "audio": {
                "master_volume": 1.0,
                "sfx_volume": 1.0,
                "bgm_volume": 0.5
            }
        }
        
        # Load cấu hình nếu có
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    
                    # Cập nhật thông minh: Giữ lại các key mới nếu JSON cũ thiếu
                    for category, values in data.items():
                        if category in self.settings:
                            for k, v in values.items():
                                if k in self.settings[category]:
                                    self.settings[category][k] = v
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, category, key):
        """Lấy giá trị của một setting"""
        return self.settings.get(category, {}).get(key, None)

    def set(self, category, key, value):
        """Thay đổi và lưu lại setting"""
        if category in self.settings and key in self.settings[category]:
            self.settings[category][key] = value
            self.save_settings()

    def toggle(self, category, key):
        """Đổi trạng thái Bật/Tắt (True/False)"""
        current_val = self.get(category, key)
        if isinstance(current_val, bool):
            self.set(category, key, not current_val)
            return not current_val
        return current_val
