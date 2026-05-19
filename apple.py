import pygame
import math
import random
from entity import Node
from config import GetAppleConfig
from particle import ParticleManager

class AppleManager:
    speed = 400.0
    speed_multiplier = 1.0 # Vũ khí có thể ghi đè biến này để làm chậm
    apple_node = None
    
    stamina = 100.0
    max_stamina = 100.0
    
    dash_timer = 0.0      # Thời gian còn lại của cú Dash
    dash_cooldown = 0.0   # Thời gian hồi Dash
    DASH_DURATION = 0.5
    DASH_COOLDOWN_TIME = 0.6
    
    username = "Player"
    
    # EXP System
    level = 1
    exp = 0
    max_exp = 50
    pending_level_ups = 0
    coins = 0 # Tiền táo
    pepper_coins = 0 # Tiền đá (Rock-coin)

    # Stat Levels (Dùng cho công thức (1+3%)^lvl)
    hp_lvl = 0
    stamina_lvl = 0
    dmg_lvl = 0
    status_points = 0
    
    damage_mult = 1.0
    magnet_radius = 200.0
    
    jackpot_stat_bonus = 0 # Thưởng thêm chỉ số khi trong trạng thái Jackpot

    @classmethod
    def recalculate_stats(cls):
        """Tính toán lại toàn bộ chỉ số HP, Stamina, Damage dựa trên level gốc và jackpot bonus."""
        effective_hp_lvl = min(cls.hp_lvl + cls.jackpot_stat_bonus, 999)
        effective_stamina_lvl = min(cls.stamina_lvl + cls.jackpot_stat_bonus, 999)
        effective_dmg_lvl = min(cls.dmg_lvl + cls.jackpot_stat_bonus, 999)

        cls.max_stamina = min(100.0 * (1.03 ** effective_stamina_lvl), 999999999999)
        cls.damage_mult = min(1.0 * (1.03 ** effective_dmg_lvl), 999999999999)
        
        if cls.apple_node:
            old_max = cls.apple_node.MaxHp
            cls.apple_node.MaxHp = min(100.0 * (1.03 ** effective_hp_lvl), 999999999999)
            # Khi MaxHp tăng, cộng thêm phần chênh lệch vào Hp hiện tại để không bị mất máu oan
            if cls.apple_node.MaxHp > old_max:
                cls.apple_node.Hp += (cls.apple_node.MaxHp - old_max)
            cls.apple_node.Hp = min(cls.apple_node.Hp, cls.apple_node.MaxHp)

    @classmethod
    def load_data(cls, data):
        """Nạp dữ liệu người chơi từ file save (EXP, Level, Coin, các chỉ số HP/Stamina/Damage)."""
        cls.username = data.get("username", "Player")
        cls.exp = data.get("exp", 0)
        cls.level = data.get("level", 1)
        cls.max_exp = int(50 * (1.2 ** (cls.level - 1)))
        cls.coins = data.get("coins", 0)
        cls.pepper_coins = data.get("pepper_coins", 0)
        
        # Load levels
        cls.hp_lvl = data.get("hp_lvl", 0)
        cls.stamina_lvl = data.get("stamina_lvl", 0)
        cls.dmg_lvl = data.get("dmg_lvl", 0)
        cls.status_points = data.get("status_points", cls.level - 1 - (cls.hp_lvl + cls.stamina_lvl + cls.dmg_lvl))
        if cls.status_points < 0: cls.status_points = 0 # Safety check
        
        # Tính toán lại stats dựa trên công thức (1.03 ^ lvl)
        cls.recalculate_stats()
        cls.stamina = cls.max_stamina
        
        # Sẽ apply max_hp_bonus khi Spawn()

    @classmethod
    def add_exp(cls, amount):
        """Cộng EXP cho người chơi, tự động lên cấp và cấp Status Point nếu EXP đủ ngưỡng."""
        cls.exp += amount
        leveled_up = False
        while cls.exp >= cls.max_exp:
            cls.exp -= cls.max_exp
            cls.level += 1
            cls.pending_level_ups += 1
            cls.status_points += 1
            cls.max_exp = int(cls.max_exp * 1.2)
            leveled_up = True
            
            # Spawn level up particle
            if cls.apple_node:
                ParticleManager.get_instance().spawn(
                    pos=cls.apple_node.position, count=30, color=(255, 255, 50), 
                    alpha=200, size_range=(4, 8), speed_range=(100, 300), 
                    lifetime=0.6, gravity=-50.0
                )
        return leveled_up

    @classmethod
    def add_coin(cls, amount=1):
        """Cộng Apple Coin cho người chơi và hiện thị particle vàng nhỏ tại vị trí nhân vật."""
        cls.coins += amount
        if cls.apple_node:
            ParticleManager.get_instance().spawn(
                pos=cls.apple_node.position, count=5, color=(255, 200, 0), # Màu vàng
                alpha=200, size_range=(3, 6), speed_range=(50, 150), 
                lifetime=0.4, gravity=-30.0
            )

    @classmethod
    def add_pepper(cls, amount=1):
        """Cộng Rock-coin (Pepper) cho người chơi."""
        cls.pepper_coins += amount
        if cls.apple_node:
            ParticleManager.get_instance().spawn(
                pos=cls.apple_node.position, count=8, color=(200, 200, 200), # Màu xám đá
                alpha=200, size_range=(3, 6), speed_range=(50, 150), 
                lifetime=0.5, gravity=-20.0
            )

    @classmethod
    def Spawn(cls, pos):
        """Tạo node Táo tại vị trí `pos`, áp dụng config và tính MaxHp dựa trên hp_lvl hiện tại."""
        cls.apple_node = Node(pos)
        cls.apple_node.apply_config(GetAppleConfig())
        # Apply HP based on level: Base 100 * (1.03 ^ lvl)
        cls.recalculate_stats()
        cls.apple_node.Hp = cls.apple_node.MaxHp

    @classmethod
    def save_stats(cls):
        """Lưu toàn bộ thống kê người chơi (EXP, Level, Coin, chỉ số nâng cấp) vào Slot hiện tại."""
        from save_system import SaveSystem
        from stage import StageManager
        from inventory import InventoryManager
        SaveSystem.get_instance().save_game(
            cls.username, cls.exp, cls.level, StageManager.get_instance().max_unlocked_wave,
            cls.hp_lvl, cls.stamina_lvl, cls.dmg_lvl, cls.coins, cls.status_points,
            InventoryManager.get_instance().save_data(), cls.pepper_coins
        )

    @classmethod
    def apply_upgrade(cls, upgrade_id):
        """Dùng 1 Status Point để nâng cấp chỉ số tương ứng với `upgrade_id` (max_hp, max_stamina, damage_mult).
        Trả về False nếu không đủ Status Point."""
        if cls.status_points <= 0: return False # Cần status point mới nâng cấp được
        
        if upgrade_id == "max_hp":
            cls.hp_lvl += 1
        elif upgrade_id == "max_stamina":
            cls.stamina_lvl += 1
        elif upgrade_id == "damage_mult":
            cls.dmg_lvl += 1
        
        cls.recalculate_stats()
        
        cls.status_points -= 1
        cls.save_stats()
        return True

    @classmethod
    def reset_stats(cls):
        """Tiêu 1000 Coin để hoàn trả toàn bộ Status Point đã phân bổ, đưa các chỉ số về giá trị gốc.
        Trả về False nếu không đủ Coin."""
        if cls.coins < 1000: return False
        
        cls.coins -= 1000
        total_spent = cls.hp_lvl + cls.stamina_lvl + cls.dmg_lvl
        cls.status_points += total_spent
        
        cls.hp_lvl = 0
        cls.stamina_lvl = 0
        cls.dmg_lvl = 0
        
        # Reset các chỉ số về mặc định (nhưng vẫn giữ Jackpot bonus nếu đang có)
        cls.recalculate_stats()
        if cls.apple_node:
            cls.apple_node.Hp = cls.apple_node.MaxHp # Hồi đầy máu khi reset
        cls.stamina = cls.max_stamina
        
        cls.save_stats()
        return True

    @classmethod
    def Process(cls, dt):
        """Cập nhật nhân vật Táo mỗi frame: hồi máu/stamina tự nhiên, xử lý di chuyển WASD,
        animation Dash, đầu bụi khi chạy và điều chỉnh ảnh flip theo hướng dạng."""
        if not cls.apple_node: return
        
        # Hồi máu (1% mỗi giây) và Hồi thể lực (5% mỗi giây)
        if cls.apple_node.Hp > 0:
            cls.apple_node.Hp = min(cls.apple_node.MaxHp, cls.apple_node.Hp + cls.apple_node.MaxHp * 0.01 * dt)
        cls.stamina = min(cls.max_stamina, cls.stamina + cls.max_stamina * 0.05 * dt)

        # Reset multiplier mỗi frame, vũ khí sẽ set lại nếu cần
        current_mult = cls.speed_multiplier
        cls.speed_multiplier = 1.0 
        
        # Giảm cooldown
        if cls.dash_cooldown > 0: cls.dash_cooldown -= dt
        
        # Xử lý Dash & Animation
        if cls.dash_timer > 0:
            cls.dash_timer -= dt
            cls.apple_node.MinFrame = 2
            cls.apple_node.MaxFrame = 5
            progress = (cls.DASH_DURATION - cls.dash_timer) / cls.DASH_DURATION
            # Gán frame offset (0 đến 3) để khi cộng MinFrame=2 sẽ ra 2,3,4,5
            cls.apple_node.frame = int(progress * 3.9) 
        else:
            cls.apple_node.MinFrame = 0
            cls.apple_node.MaxFrame = 1
            # Không cần gán frame = 0 ở đây để entity.py tự chạy animation 0-1
            
        # Tính toán tốc độ di chuyển
        current_speed = cls.speed * current_mult
            
        keys = pygame.key.get_pressed()
        move = pygame.math.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        
        # Di chuyển và lật hình ảnh
        if move.length_squared() > 0:
            if cls.dash_timer <= 0:
                cls.apple_node.direction = cls.apple_node.direction.lerp(move.normalize() * current_speed, 0.2)
                if move.x < 0: cls.apple_node.flipX = True
                elif move.x > 0: cls.apple_node.flipX = False
                
            cls.apple_node.textureOffsetY = math.sin(pygame.time.get_ticks() * cls.speed/10000) * 3.0 - cls.apple_node.textureHeight * cls.apple_node.scaleMultiplier
            
            # --- BỤI KHI CHẠY ---
            if random.random() < 0.5 and cls.dash_timer <= 0:
                back_dir = -move.normalize()
                dust_pos = cls.apple_node.position + back_dir * 15
                ParticleManager.get_instance().spawn(pos=dust_pos, count=1, color=(200, 185, 140), alpha=140, size_range=(3, 7), speed_range=(20, 80), lifetime=0.3, gravity=120.0)
        else:
            if cls.dash_timer <= 0:
                cls.apple_node.direction *= 0.8
            cls.apple_node.textureOffsetY = - cls.apple_node.textureHeight * cls.apple_node.scaleMultiplier

    @classmethod
    def Dash(cls, power=2000.0):
        """Thực hiện cú Dash theo hướng di chuyển (hoặc hướng đang nhìn), tiêu 10 Stamina, tạo bất khả xâm phạm tạm thời."""
        if not cls.apple_node or cls.dash_cooldown > 0 or cls.stamina < 30.0: return
        
        cls.stamina -= 10.0 # Tiêu hao 10 thể lực mỗi lần Dash
        
        keys = pygame.key.get_pressed()
        move_dir = pygame.math.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        
        if move_dir.length_squared() > 0:
            dash_direction = move_dir.normalize()
        else:
            if cls.apple_node.direction.length_squared() > 0:
                dash_direction = cls.apple_node.direction.normalize()
            else:
                dash_direction = pygame.math.Vector2(1, 0)
        
        if dash_direction.x < 0: cls.apple_node.flipX = True
        elif dash_direction.x > 0: cls.apple_node.flipX = False

        cls.apple_node.velocity = dash_direction * power
        cls.apple_node.stun = 0.5
        cls.apple_node.invincibility = 0.5
        cls.dash_timer = cls.DASH_DURATION
        cls.dash_cooldown = cls.DASH_COOLDOWN_TIME
        
        ParticleManager.get_instance().spawn(pos=cls.apple_node.position, count=15, color=(255, 255, 255), alpha=150, size_range=(4, 10), speed_range=(50, 300), lifetime=0.4, gravity=0.0)

    @classmethod
    def get_all_apples(cls):
        """Trả về danh sách tất cả node Táo (mask=2) còn sống trong active_nodes."""
        from entity import active_nodes
        return [n for n in active_nodes if n.mask == 2 and not n.is_dead]

    @classmethod
    def GetPosition(cls):
        """Trả về vị trí hiện tại của apple_node, hoặc Vector2(0,0) nếu nhân vật chưa tồn tại."""
        return cls.apple_node.position if cls.apple_node else pygame.math.Vector2(0,0)
