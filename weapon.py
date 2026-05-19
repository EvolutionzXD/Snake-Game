import pygame
import time
import math
import random
from random import random as random_func
from projectile import ProjectileManager
from config import GetProjectileConfig, GetSwordAirDashConfig, GetFlameConfig, GetGhostPunchConfig, GetFoamConfig, GetSlashConfig
from resources import ResourceManager
from particle import ParticleManager
from apple import AppleManager
from config import GLOBAL_SCALE
from entity import Node

class Weapon:
    def __init__(self, name, config_func, texture_name="stick", fire_rate=0.2, speed=1200.0, 
                 arm_len=20, stick_len=40, recoil=15, scale=1.5, stamina_cost=0.0, level=1, is_awakened=False, **kwargs):
        self.name = name
        self.level = level
        self.is_awakened = is_awakened
        self.config_func = config_func
        self.texture_name = texture_name
        self.fire_rate = fire_rate
        self.speed = speed
        self.scale = scale
        self.arm_len = arm_len
        self.stick_len = stick_len
        self.recoil_dist = recoil 
        self.stamina_cost = stamina_cost

        # Lưu toàn bộ kwargs mở rộng (như damage_override) vào self
        for k, v in kwargs.items():
            setattr(self, k, v)

        # Áp dụng nâng cấp từ WEAPON_CATALOG
        from arsenal import WEAPON_CATALOG
        if name in WEAPON_CATALOG:
            upgrades = WEAPON_CATALOG[name].get("upgrades", {})
            # Áp dụng cộng dồn các mốc level (hoặc lấy mốc cao nhất)
            # Ở đây ta lấy mốc hiện tại cho đơn giản
            for lv in range(2, level + 1):
                if lv in upgrades:
                    for k, v in upgrades[lv].get("kwargs_update", {}).items():
                        setattr(self, k, v)
            
            # Áp dụng awakening nếu có
            if is_awakened and "awaken" in upgrades:
                for k, v in upgrades["awaken"].get("kwargs_update", {}).items():
                    setattr(self, k, v)
        
        # State
        self.current_recoil = 0.0
        self.last_fire_time = 0.0
        self.is_charging = False
        self.charge_start_time = 0.0

    def attack(self, manager, pos, target_pos, is_holding):
        pass

    def update(self, manager, dt):
        self.current_recoil = pygame.math.lerp(self.current_recoil, 0, min(15 * dt, 1.0))

    def on_unequip(self):
        pass

    def _get_player_momentum(self):
        if AppleManager.apple_node:
            return AppleManager.apple_node.velocity + AppleManager.apple_node.direction
        return pygame.math.Vector2(0, 0)

class Gun(Weapon):
    def __init__(self, name, config_func, is_automatic=False, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.is_automatic = is_automatic

    def attack(self, manager, pos, target_pos, is_holding):
        current_time = time.time()
        if self.is_automatic:
            if not is_holding: return False
        else:
            if not is_holding:
                self.is_charging = False
                return False
            if self.is_charging: return False 
            self.is_charging = True

        if current_time - self.last_fire_time >= self.fire_rate:
            if AppleManager.stamina < self.stamina_cost: return False
            
            # Bắn phát chính
            ProjectileManager.Spawn(
                pos                = pos, 
                target_pos         = target_pos, 
                config_func        = self.config_func, 
                speed              = self.speed,
                inherited_velocity = self._get_player_momentum(),
                damage_override    = getattr(self, "damage_override", None)
            )

            # --- AWAKENING: Bắn 2 phát (Dual Shot) ---
            if self.is_awakened:
                # Tính hướng lệch một chút
                dir_vec = (pygame.math.Vector2(target_pos) - pos)
                if dir_vec.length_squared() > 0:
                    angle = math.degrees(math.atan2(dir_vec.y, dir_vec.x))
                    for offset in [-10, 10]: # Bắn thêm 2 tia lệch trái phải
                        rad = math.radians(angle + offset)
                        new_target = pos + pygame.math.Vector2(math.cos(rad), math.sin(rad)) * 100
                        ProjectileManager.Spawn(
                            pos                = pos, 
                            target_pos         = new_target, 
                            config_func        = self.config_func, 
                            speed              = self.speed,
                            inherited_velocity = self._get_player_momentum(),
                            damage_override    = getattr(self, "damage_override", None)
                        )

            AppleManager.stamina -= self.stamina_cost
            self.last_fire_time = current_time
            self.current_recoil = self.recoil_dist
            return True
        return False

class Flamethrower(Gun):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.is_automatic = True
        self.shot_count = getattr(self, "shot_count", 10) # Mặc định là 10 nếu không khai báo

    def attack(self, manager, pos, target_pos, is_holding):
        if not is_holding: return False
        current_time = time.time()
        
        if current_time - self.last_fire_time >= self.fire_rate:
            if AppleManager.stamina < self.stamina_cost: return False
            
            angle_rad = math.radians(manager.last_final_angle)
            muzzle_dist = self.arm_len + self.stick_len * self.scale * 0.8
            muzzle_offset = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad)) * muzzle_dist
            muzzle_pos = pos + muzzle_offset

            base_dir = (pygame.math.Vector2(target_pos) - pos)
            if base_dir.length_squared() > 0:
                base_angle = math.degrees(math.atan2(base_dir.y, base_dir.x))
                momentum = self._get_player_momentum()
                for _ in range(int(self.shot_count)):
                    spread = random.uniform(-20, 20)
                    rad = math.radians(base_angle + spread)
                    new_dir = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    proj_target = muzzle_pos + new_dir * 100
                    ProjectileManager.Spawn(
                        pos                = muzzle_pos, 
                        target_pos         = proj_target, 
                        config_func        = self.config_func, 
                        speed              = self.speed * random.uniform(0.8, 1.2),
                        inherited_velocity = momentum,
                        damage_override    = getattr(self, "damage_override", None)
                    )
                for _ in range(random.randint(2, 4)):
                    color = random.choice([(255, 50, 0), (255, 150, 0), (255, 230, 0)])
                    ParticleManager.get_instance().spawn_directional(
                        pos = muzzle_pos,
                        direction_angle = base_angle + random.uniform(-20, 20),
                        count = 1, color = color, alpha = random.randint(180, 255),
                        size_range = (4, 10), speed_range = (150, 400),
                        spread_deg = 30, lifetime = random.uniform(0.1, 0.3), gravity = -100.0,
                        use_additive = True
                    )
            AppleManager.stamina -= self.stamina_cost
            self.last_fire_time = current_time
            self.current_recoil = self.recoil_dist
            return True
        return False

class StandWeapon(Weapon):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.is_automatic = True
        self.ghost_node = None
        self.is_near_target = False
        self.last_is_holding = False
        self.punch_count = 0 # Đếm số cú đấm để kích hoạt ZA WARUDO

    def attack(self, manager, pos, target_pos, is_holding):
        self.last_is_holding = is_holding # Lưu trạng thái để update dùng
        if not is_holding: return False
        
        # Chỉ đấm khi đã bay tới gần mục tiêu (chuột)
        if not self.is_near_target: return False

        current_time = time.time()
        if current_time - self.last_fire_time >= self.fire_rate:
            if AppleManager.stamina < self.stamina_cost: return False

            if self.ghost_node:
                # ORA ORA ORA: Nếu Awaken thì đấm 3 phát cùng lúc
                num_punches = 3 if self.is_awakened else 1
                for _ in range(num_punches):
                    punch_pos = self.ghost_node.position + pygame.math.Vector2(random.uniform(-40, 40), random.uniform(-40, 40))
                    
                    # Tính toán hướng đấm
                    dir_vec = (pygame.math.Vector2(target_pos) - punch_pos)
                    if dir_vec.length_squared() > 0:
                        base_angle = math.degrees(math.atan2(dir_vec.y, dir_vec.x))
                        spread_angle = math.radians(base_angle + random.uniform(-10, 10))
                        punch_target = punch_pos + pygame.math.Vector2(math.cos(spread_angle), math.sin(spread_angle)) * 100
                        
                        ProjectileManager.Spawn(
                            pos                = punch_pos, 
                            target_pos         = punch_target, 
                            config_func        = GetGhostPunchConfig, 
                            speed              = random.uniform(2000, 3000) if self.is_awakened else random.uniform(2000, 2600),
                            inherited_velocity = self._get_player_momentum() * 0.2,
                            alpha_override     = 180,
                            damage_override    = getattr(self, "damage_override", None)
                        )
                
                # --- XỬ LÝ ZA WARUDO ---
                if self.is_awakened:
                    from effects import EffectManager
                    # CHỈ TÍNH khi thời gian KHÔNG đang dừng
                    if EffectManager.get_instance().time_stop_timer <= 0:
                        self.punch_count += num_punches
                        if self.punch_count >= 200:
                            self._trigger_za_warudo()
                            self.punch_count = 0

                if random_func() < 0.6:
                    aura_pos = self.ghost_node.position + pygame.math.Vector2(random.uniform(-40, 40), random.uniform(-40, 40))
                    ParticleManager.get_instance().spawn_directional(
                        pos = aura_pos,
                        direction_angle = 90, count = 1, color = (180, 100, 255), alpha = 200,
                        size_range = (40, 65), speed_range = (50, 150),
                        spread_deg = 45, lifetime = 0.8, gravity = -180.0,
                        texture_name = "ghost_letter"
                    )

            AppleManager.stamina -= self.stamina_cost
            self.last_fire_time = current_time
            return True
        return False

    def _trigger_za_warudo(self):
        """Kích hoạt dừng thời gian: Đóng băng mọi thứ nma cho phép rắn vẫn bắn đạn."""
        from effects import EffectManager, CameraShake
        from particle import ParticleManager
        
        # Hiệu ứng thị giác & Rung màn hình
        EffectManager.get_instance().trigger_time_stop(15.0) # Dừng trong 15 giây
        CameraShake.get_instance().add_trauma(1.0)
        
        # --- HIỆU ỨNG VÒNG TRÒN NĂNG LƯỢNG ---
        pm = ParticleManager.get_instance()
        for i in range(0, 360, 10): # 36 hạt tỏa ra các hướng
            pm.spawn_directional(
                pos             = self.ghost_node.position,
                direction_angle = i,
                count           = 1,
                color           = (200, 220, 255),
                alpha           = 255,
                size_range      = (20, 45),    # Hạt to xỉu như bạn muốn
                speed_range     = (600, 1000), # Bay cực nhanh tạo sóng xung kích
                spread_deg      = 2,
                lifetime        = 0.6,
                gravity         = 0.0
            )

        # BỎ STUN: Để rắn vẫn có thể bắn đạn (nma đạn sẽ đứng yên)
        from entity import active_nodes
        for node in active_nodes:
            if node.mask == 1:
                node.flashEffect = 0.6

    def update(self, manager, dt):
        super().update(manager, dt)
        from entity import Node
        if self.ghost_node is None:
            self.ghost_node = Node(manager.last_player_pos)
            self.ghost_node.textureName = "apple_ghost"
            self.ghost_node.alpha = 180
            self.ghost_node.hasShadow = False
            self.ghost_node.mask = -1     # Không va chạm với bất kỳ ai
            self.ghost_node.maskOut = []  # Không gây sát thương cho bất kỳ ai
            self.ghost_node.Hp = 999999   # Bất tử
            self.ghost_node.invincibility = 999999

        # --- TÍNH TOÁN VỊ TRÍ MỤC TIÊU ---
        mouse_scr = pygame.math.Vector2(pygame.mouse.get_pos())
        screen_center = pygame.math.Vector2(600, 400)
        mouse_pos = (mouse_scr - screen_center) / GLOBAL_SCALE + manager.last_camera + screen_center
        mouse_dir = (mouse_pos - manager.last_player_pos)
        
        if self.last_is_holding:
            # Khi tấn công: Bay tới GẦN chuột (cách 80px để có khoảng trống đấm)
            if mouse_dir.length_squared() > 0:
                target_ghost_pos = mouse_pos - mouse_dir.normalize() * 80
            else:
                target_ghost_pos = mouse_pos
        else:
            # Khi đứng yên: Bay ra sau lưng Apple
            if mouse_dir.length_squared() > 0:
                target_ghost_pos = manager.last_player_pos - mouse_dir.normalize() * 70 + pygame.math.Vector2(0, -40)
            else:
                target_ghost_pos = manager.last_player_pos + pygame.math.Vector2(-70, -40)

        # Di chuyển mượt mà tới đích
        dist_vec = target_ghost_pos - self.ghost_node.position
        dist_sq = dist_vec.length_squared()
        self.is_near_target = dist_sq < 10000 # < 100 pixel là coi như đã tới vị trí "sẵn sàng"
        
        # AWAKEN: Bay nhanh hơn để ORA ORA cho kịp
        move_speed = 12 if self.last_is_holding else 6
        if self.is_awakened: move_speed *= 1.8
        
        self.ghost_node.position += dist_vec * move_speed * dt
        
        self.ghost_node.scaleMultiplier = 0.8 # Nhỏ hơn xíu theo ý bạn
        # Animation & Flip
        self.ghost_node.frame += dt * 5
        if self.ghost_node.frame > 2: self.ghost_node.frame = 0
        check_angle = (manager.angle + 180) % 360 - 180
        self.ghost_node.flipX = check_angle > 90 or check_angle < -90

    def draw_special(self, screen, camera):
        if self.ghost_node:
            self.ghost_node.draw_outline(screen, camera)
            self.ghost_node.draw_sprite(screen, camera)

    def on_unequip(self):
        if self.ghost_node:
            self.ghost_node.Hp = 0 # Để physics system dọn dẹp nó
            self.ghost_node = None

class Sword(Weapon):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.swing_progress = 0.0
        self.sword_spawns_done = 0
        self.charge_values = {"kb": 0, "stun": 0, "dmg": 0}
        self.last_charge_duration = 0.0 # Lưu thời gian gồng của cú đánh gần nhất

    def attack(self, manager, pos, target_pos, is_holding):
        current_time = time.time()
        
        if is_holding:
            if not self.is_charging and current_time - self.last_fire_time >= self.fire_rate:
                # Ngăn gồng kiếm nếu không còn thể lực
                if AppleManager.stamina < self.stamina_cost: return False
                
                self.is_charging = True
                self.charge_start_time = current_time 
                self.swing_progress = 1.0 
                self.sword_spawns_done = 0
            return False
        else:
            if self.is_charging:
                charge_dur = current_time - self.charge_start_time
                self.last_charge_duration = charge_dur # Lưu lại để kiểm tra điều kiện triệu hồi zone
                
                if self.is_awakened:
                    # AWAKEN: Sát thương cực đại 800 (đạt được trong 2s gồng)
                    self.charge_values["kb"] = min(800 + (charge_dur * 4600), 10000)
                    self.charge_values["stun"] = min(1.0 + (charge_dur * 2.0), 5.0)
                    self.charge_values["dmg"] = min(20 + (charge_dur * 390), 800)
                else:
                    # Thông số bình thường
                    self.charge_values["kb"] = min(400 + (charge_dur * 2300), 3000)
                    self.charge_values["stun"] = min(0.5 + (charge_dur * 0.5), 1.5)
                    self.charge_values["dmg"] = min(10 + (charge_dur * 30), 90)
                self.is_charging = False
                self.last_fire_time = current_time
                self.swing_progress = 0.89 
                
                # Tiêu tốn thể lực khi tung kiếm án
                AppleManager.stamina -= self.stamina_cost
                return True
        return False

    def update(self, manager, dt):
        super().update(manager, dt)
        if self.is_charging:
            AppleManager.speed_multiplier = 0.7
        if self.swing_progress > 0:
            if self.is_charging and self.swing_progress <= 0.71:
                self._handle_charge_particles(manager, dt)
            else:
                self._handle_swing_animation(manager, dt)

    def _handle_charge_particles(self, manager, dt):
        charge_dur = time.time() - self.charge_start_time
        if charge_dur >= 0.8:
            ratio = min((charge_dur - 0.8) / 1.2, 1.0)
            check_angle = (manager.angle + 180) % 360 - 180
            angle_off = 120 if (check_angle > 90 or check_angle < -90) else -120
            rad = math.radians(manager.angle + angle_off)
            tip = manager.last_player_pos + pygame.math.Vector2(math.cos(rad), math.sin(rad)) * (30 + random_func() * 70)
            if random_func() < 0.2 + ratio * 0.2:
                gray = int(180 + ratio * 45)
                ParticleManager.get_instance().spawn(pos=tip, count=1, color=(gray, gray, gray), alpha=int(80+ratio*80), size_range=(3,6), speed_range=(10,40), lifetime=0.5, gravity=-60.0)

    def _handle_swing_animation(self, manager, dt):
        p = self.swing_progress
        thresholds = [0.68, 0.55, 0.42, 0.29, 0.16]
        if self.sword_spawns_done < 5 and p <= thresholds[self.sword_spawns_done]:
            self._spawn_slash(manager)
            self.sword_spawns_done += 1
        anim_speed = 5.0 if p >= 0.1 else 0.5
        self.swing_progress = max(0, self.swing_progress - anim_speed * dt)

    def _spawn_slash(self, manager):
        rad = math.radians(manager.last_final_angle)
        dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        spawn_pos = manager.last_player_pos + dir_vec * 60
        target = spawn_pos + dir_vec * 100
        momentum = self._get_player_momentum() * 0.5
        
        # Vết chém chính
        ProjectileManager.Spawn(
            pos                = spawn_pos, 
            target_pos         = target, 
            config_func        = self.config_func, 
            speed              = self.speed,
            knockback_override = self.charge_values["kb"], 
            stun_override      = self.charge_values["stun"], 
            damage_override    = self.charge_values["dmg"], 
            lifetime_override  = 0.04,
            inherited_velocity = momentum
        )

        # --- AWAKENING: STORM KING ---
        if self.is_awakened:
            # 1. Thêm một lớp kiếm khí ở xa hơn (Outer Layer) - BẮN 3 TIA HÌNH QUẠT
            for angle_offset in [-15, 0, 15]:
                rad_outer = math.radians(manager.last_final_angle + angle_offset)
                dir_outer = pygame.math.Vector2(math.cos(rad_outer), math.sin(rad_outer))
                
                outer_spawn_pos = manager.last_player_pos + dir_outer * 155
                outer_target = outer_spawn_pos + dir_outer * 100
                ProjectileManager.Spawn(
                    pos                = outer_spawn_pos, 
                    target_pos         = outer_target, 
                    config_func        = self.config_func, 
                    speed              = self.speed,
                    knockback_override = self.charge_values["kb"] * 0.4, 
                    stun_override      = self.charge_values["stun"], 
                    damage_override    = self.charge_values["dmg"] * 0.4, 
                    lifetime_override  = 0.04,
                    inherited_velocity = momentum
                )

            # 2. Triệu hồi Vùng Đỏ (AtkX2 Zone) RA XA - CHỈ KHI GỒNG ĐỦ 1S
            if self.last_charge_duration >= 1.0:
                from config import GetAtkX2ZoneConfig
                zone_pos = manager.last_player_pos + dir_vec * 220
                ProjectileManager.Spawn(
                    pos                = zone_pos,
                    target_pos         = zone_pos,
                    config_func        = GetAtkX2ZoneConfig,
                    speed              = 0.0,
                    inherited_velocity = momentum * 0.1
                )

        ratio = min(self.charge_values["kb"] / 3000, 1.0)
        color = (int(180 + ratio*75), int(210 + ratio*45), 255)
        ParticleManager.get_instance().spawn_directional(pos=spawn_pos, direction_angle=manager.last_final_angle, count=int(4+ratio*8), color=color, alpha=int(180+ratio*75), size_range=(2,6), speed_range=(80,200), spread_deg=50, lifetime=0.25, gravity=150.0)

class FlameExtinguisher(Gun):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.is_automatic = True
        self.stun_override = getattr(self, "stun_override", None)
        self.damage_override = getattr(self, "damage_override", None)

    def attack(self, manager, pos, target_pos, is_holding):
        if not is_holding: return False
        current_time = time.time()
        
        if current_time - self.last_fire_time >= self.fire_rate:
            if AppleManager.stamina < self.stamina_cost: return False
            
            angle_rad = math.radians(manager.last_final_angle)
            muzzle_dist = self.arm_len + self.stick_len * self.scale * 0.8
            muzzle_offset = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad)) * muzzle_dist
            muzzle_pos = pos + muzzle_offset

            base_dir = (pygame.math.Vector2(target_pos) - pos)
            if base_dir.length_squared() > 0:
                base_angle = math.degrees(math.atan2(base_dir.y, base_dir.x))
                momentum = self._get_player_momentum()
                for _ in range(15):
                    spread = random.uniform(-20, 20)
                    rad = math.radians(base_angle + spread)
                    new_dir = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    proj_target = muzzle_pos + new_dir * 100
                    ProjectileManager.Spawn(
                        pos                = muzzle_pos, 
                        target_pos         = proj_target, 
                        config_func        = self.config_func, 
                        speed              = self.speed * random.uniform(0.8, 1.2),
                        stun_override      = self.stun_override,
                        damage_override    = self.damage_override,
                        inherited_velocity = momentum
                    )
                for _ in range(random.randint(2, 4)):
                    color = random.choice([(255, 255, 255), (255, 255, 255), (255, 255, 255)])
                    ParticleManager.get_instance().spawn_directional(
                        pos = muzzle_pos,
                        direction_angle = base_angle + random.uniform(-20, 20),
                        count = 1, color = color, alpha = random.randint(180, 255),
                        size_range = (4, 10), speed_range = (150, 400),
                        spread_deg = 30, lifetime = random.uniform(0.1, 0.3), gravity = -100.0,
                        use_additive = True
                    )
            AppleManager.stamina -= self.stamina_cost
            self.last_fire_time = current_time
            self.current_recoil = self.recoil_dist
            return True
        return False

class TarotCardWeapon(Weapon):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.hand = []
        self.max_cards = 3
        self.card_reload_timer = 0.0
        self.card_reload_delay = 0.8 # Hồi 1 lá mỗi 0.8s
        self.active_dummies = []
        self.is_automatic = False
        self.is_visible = True
        
        # --- LOGIC LUCKY DRAW (AWAKEN) ---
        self.jackpot_timer = 0.0
        self.last_card_type = -1
        self.match_count = 1

    def update(self, manager, dt):
        super().update(manager, dt)
        
        # Hồi bài
        if len(self.hand) < self.max_cards:
            self.card_reload_timer -= dt
            if self.card_reload_timer <= 0:
                self.card_reload_timer = self.card_reload_delay
                # Tăng xác suất trúng thưởng khi đang Jackpot (thêm 40% cơ hội ép ra bài trùng)
                is_jackpot = self.jackpot_timer > 0
                if is_jackpot and len(self.hand) > 0 and random.random() < 0.6:
                    new_card = random.choice(self.hand) # Chọn ngẫu nhiên một lá đang có trong tay để tăng tỉ lệ trùng
                else:
                    new_card = random.randint(0, 4)
                
                # --- KIỂM TRA BÀI TRÙNG TRONG TOÀN BỘ TAY BÀI (HÀO PHÓNG) ---
                if self.is_awakened:
                    occurences = self.hand.count(new_card)
                    if occurences == 1: # Đã có 1 lá -> giờ là 2 lá (Lucky Pair)
                        from apple import AppleManager
                        self._trigger_lucky_pair(AppleManager.GetPosition())
                    elif occurences == 2: # Đã có 2 lá -> giờ là 3 lá (Jackpot)
                        self._trigger_jackpot_start()
                
                self.hand.append(new_card)
                
        # Xử lý các lá bài đang bay (dummy)
        alive_dummies = []
        is_jackpot = self.jackpot_timer > 0
        for dummy, card_type in self.active_dummies:
            # Trigger khi lá bài "chết" (Hp <= 0 hoặc is_dead) hoặc khi nó bay chậm lại
            if dummy.Hp <= 0 or dummy.is_dead or dummy.velocity.length_squared() < 10000:
                # Nếu đang Jackpot, giảm tối đa số lượng hạt (0.2) để bắn được nhiều đạn mà không lag
                self.trigger_card_effect(dummy.position, card_type, particle_mult=0.2 if is_jackpot else 1.0)
                dummy.Hp = 0 
                dummy.is_dead = True
            else:
                alive_dummies.append((dummy, card_type))
                
        self.active_dummies = alive_dummies
        
        # Ẩn vũ khí khi đang có bài bay
        self.is_visible = (len(self.active_dummies) == 0)

        # --- LOGIC JACKPOT (SPAM 6 HƯỚNG) ---
        if self.jackpot_timer > 0:
            self.jackpot_timer -= dt
            from apple import AppleManager
            # Buff bất tử & vô hạn Stamina
            if AppleManager.apple_node:
                AppleManager.apple_node.invincibility = 0.5
                AppleManager.stamina = AppleManager.max_stamina
            
            # Spam đạn 12 hướng liên tục (mỗi 0.4s một lần - rất nhanh)
            if int(self.jackpot_timer / 0.4) != int((self.jackpot_timer + dt) / 0.4):
                self._trigger_jackpot_spam(manager)

            # Khi hết thời gian Jackpot, trả lại chỉ số cũ
            if self.jackpot_timer <= 0:
                AppleManager.jackpot_stat_bonus = 0
                AppleManager.recalculate_stats()

    def trigger_card_effect(self, pos, card_type, particle_mult=1.0):
        from config import (GetAtkZoneConfig, GetTeleportZoneConfig, GetIceZoneConfig, 
                            GetAtkX2ZoneConfig, GetPoisonZoneConfig)
        
        configs = [GetAtkZoneConfig, GetTeleportZoneConfig, GetIceZoneConfig, 
                   GetAtkX2ZoneConfig, GetPoisonZoneConfig]
        
        zone = ProjectileManager.Spawn(
            pos, pos, 
            config_func=configs[card_type],
            speed=0.0
        )
        
        # Sát thương vẫn cần nhân thêm damage_mult từ AppleManager (ProjectileManager.Spawn đã tự nhân)
        
        # --- HIỆU ỨNG PARTICLE ĐẶC TRƯNG ---
        if card_type == 0: # atk
            ParticleManager.get_instance().spawn(pos=pos, count=int(20 * particle_mult), color=(255, 50, 50), alpha=200, size_range=(5, 10), speed_range=(100, 300), lifetime=0.5, gravity=0)
        elif card_type == 1: # teleport
            if AppleManager.apple_node:
                # ... (logic mồi nhử giữ nguyên)
                loot = Node(AppleManager.apple_node.position)
                loot.textureName = "apple_ghost"
                loot.knockback_resistance = 0.2
                loot.stun_on_hit = 0.5
                loot.scaleMultiplier = 0.6
                loot.maskOut = [1]
                loot.knockback = 150
                loot.damage = 0
                loot.hasShadow = True
                loot.MaxHp = loot.Hp = AppleManager.apple_node.MaxHp; loot.mask = 2 # mask 2 giúp nó được nhận diện như Player
                loot.lifetime = 15.0 # Mồi nhử sẽ tự hỏng sau 15 giây
                loot.velocity = pygame.math.Vector2(random.uniform(-150, 150), random.uniform(-150, 150))
                from entity import active_nodes
                active_nodes.append(loot)
                AppleManager.apple_node.position = pos.copy()
            ParticleManager.get_instance().spawn(pos=pos, count=int(25 * particle_mult), color=(180, 50, 255), alpha=200, size_range=(6, 12), speed_range=(150, 400), lifetime=0.6, gravity=0)
        elif card_type == 2: # ice
            ParticleManager.get_instance().spawn(pos=pos, count=int(40 * particle_mult), color=(100, 220, 255), alpha=200, size_range=(5, 10), speed_range=(50, 250), lifetime=0.8, gravity=0)
        elif card_type == 3: # atk x 2
            ParticleManager.get_instance().spawn(pos=pos, count=int(40 * particle_mult), color=(255, 20, 20), alpha=220, size_range=(8, 15), speed_range=(200, 500), lifetime=0.7, gravity=0)
        elif card_type == 4: # poison
            # Tạo "Sương mù độc" phủ kín toàn bộ Radius
            pm = ParticleManager.get_instance()
            effective_radius = zone.hitbox_radius * zone.scaleMultiplier
            for _ in range(int(100 * particle_mult)):
                angle = random.uniform(0, 2 * math.pi)
                dist = effective_radius * math.sqrt(random.random())
                p_pos = pos + pygame.math.Vector2(math.cos(angle) * dist, math.sin(angle) * dist)
                pm.spawn(
                    pos=p_pos, count=1, color=(80, 255, 50), alpha=random.randint(100, 180),
                    size_range=(15, 35), speed_range=(10, 50),
                    lifetime=zone.lifetime * random.uniform(0.7, 1.3), gravity=-3.0
                )

    def attack(self, manager, pos, target_pos, is_holding):
        if not is_holding:
            self.is_charging = False
            return False
        
        if self.is_charging: return False 
        self.is_charging = True
            
        current_time = time.time()
        if current_time - self.last_fire_time >= self.fire_rate:
            if len(self.hand) == 0: return False 
            if AppleManager.stamina < self.stamina_cost: return False
            
            AppleManager.stamina -= self.stamina_cost
            self.last_fire_time = current_time
            self.current_recoil = self.recoil_dist
            
            card_type = self.hand.pop(0)
            
            from config import GetCardDummyConfig
            direction = pygame.math.Vector2(target_pos) - pygame.math.Vector2(pos)
            if direction.length_squared() > 0:
                direction = direction.normalize()
                
            dummy = ProjectileManager.Spawn(
                pos, target_pos,
                config_func=GetCardDummyConfig,
                speed=self.speed,
                inherited_velocity=self._get_player_momentum()
            )
            
            self.active_dummies.append((dummy, card_type))
            return True
        return False

    def _trigger_lucky_pair(self, pos):
        """Hồi phục và bắn 4 hướng khi trúng 2 lá giống nhau."""
        from apple import AppleManager
        from effects import EffectManager
        # Hồi phục
        if AppleManager.apple_node:
            AppleManager.apple_node.Hp = AppleManager.apple_node.MaxHp
            AppleManager.stamina = AppleManager.max_stamina
        
        # Hiện chữ (To hơn)
        EffectManager.get_instance().trigger_text_popup("2 OF 3", pos, color=(255, 255, 100), is_large=True)
        # Thông báo hồi phục cụ thể
        EffectManager.get_instance().trigger_text_popup("FULL HP & STAMINA RESTORED", pos + pygame.math.Vector2(0, 80), color=(100, 255, 100))
        
        # Bắn 6 hướng siêu tốc
        for i in range(6):
            angle = i * 60
            rad = math.radians(angle)
            target = pos + pygame.math.Vector2(math.cos(rad) * 100, math.sin(rad) * 100)
            from config import GetCardDummyConfig
            dummy = ProjectileManager.Spawn(pos, target, config_func=GetCardDummyConfig, speed=self.speed)
            # Dùng card_type của lá bài vừa kích hoạt lucky pair
            card_type = self.hand[-1] if self.hand else random.randint(0, 4)
            self.active_dummies.append((dummy, card_type))

    def _trigger_jackpot_start(self):
        """Kích hoạt trạng thái Jackpot 15 giây."""
        from effects import EffectManager, CameraShake
        from apple import AppleManager
        self.jackpot_timer = 15.0
        # Tăng chỉ số tạm thời
        AppleManager.jackpot_stat_bonus += 5
        AppleManager.recalculate_stats()
        
        EffectManager.get_instance().trigger_text_popup("JACKPOT!!!", AppleManager.GetPosition(), color=(255, 50, 255), is_large=True)
        CameraShake.get_instance().add_trauma(1.0)

    def _trigger_jackpot_spam(self, manager):
        """Spam đạn 6 hướng tỏa tròn."""
        from apple import AppleManager
        pos = AppleManager.GetPosition()
        for i in range(6): # Quay về 6 hướng
            angle = i * 60 + (time.time() * 50) 
            rad = math.radians(angle)
            target = pos + pygame.math.Vector2(math.cos(rad) * 100, math.sin(rad) * 100)
            from config import GetCardDummyConfig
            # Giữ speed 0.6x cho hoành tráng
            dummy = ProjectileManager.Spawn(pos, target, config_func=GetCardDummyConfig, speed=self.speed * 0.6)
            # Chọn card_type ngẫu nhiên cho đạn spam, loại bỏ loại 1 (Teleport)
            self.active_dummies.append((dummy, random.choice([0, 2, 3, 4])))

    def on_unequip(self):
        if self.jackpot_timer > 0:
            from apple import AppleManager
            AppleManager.jackpot_stat_bonus = 0
            AppleManager.recalculate_stats()
            self.jackpot_timer = 0

class RealitySlash(Weapon):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.start_pos = None
        self.is_aiming = False
        self.active_slashes = [] 
        self.free_slash = getattr(self, "free_slash", 0) 
        self.chaos_radius = getattr(self, "chaos_radius", 100) # Mặc định là 100 nếu không có
    
    def attack(self, manager, pos, target_pos, is_holding):
        current_mouse = pygame.math.Vector2(target_pos)
        if AppleManager.stamina < self.stamina_cost: 
            is_holding = False
            self.is_aiming = False
        
        if is_holding:
            if not self.is_aiming:
                self.start_pos = current_mouse
                self.is_aiming = True
            return False
        else:
            if self.is_aiming:
                # Vết chém chính
                self._trigger_slash(self.start_pos, current_mouse)
                self.active_slashes.append({
                    'start': self.start_pos, 'end': current_mouse,
                    'life': 0.25, 'max_life': 0.25, 'is_free': False
                })
                
                # Các vết chém phụ (Free Slashes)
                for _ in range(int(self.free_slash)):
                    offset = self.chaos_radius # Sử dụng biến chaos_radius thay vì fix cứng 100
                    f_start = self.start_pos + pygame.math.Vector2(random.uniform(-offset, offset), random.uniform(-offset, offset))
                    f_end = current_mouse + pygame.math.Vector2(random.uniform(-offset, offset), random.uniform(-offset, offset))
                    
                    self._trigger_slash(f_start, f_end, damage_multiplier=0.25)
                    self.active_slashes.append({
                        'start': f_start, 'end': f_end,
                        'life': 0.18, 'max_life': 0.18, 'is_free': True
                    })

                AppleManager.stamina -= self.stamina_cost
                self.is_aiming = False
                self.start_pos = None
                return True
        return False

    def _trigger_slash(self, start_pos, end_pos, damage_multiplier=1.0):
        dist_vec = end_pos - start_pos
        length = dist_vec.length()
        if length < 10: return
        
        # Lấy damage gốc từ config để nhân tỉ lệ (cho các vết chém phụ)
        damage_override = None
        if damage_multiplier != 1.0:
            base_config = self.config_func()
            damage_override = base_config.damage * damage_multiplier
      
        steps = int(length / 20) + 1
        for i in range(steps):
            spawn_pos = start_pos + dist_vec * (i / max(1, steps - 1))
            ProjectileManager.Spawn(
                pos                = spawn_pos, 
                target_pos         = end_pos, 
                config_func        = self.config_func, 
                speed              = 0,
                inherited_velocity = pygame.math.Vector2(0, 0),
                alpha_override     = 0,
                damage_override    = damage_override,
                lifetime_override  = 0.1
            )
            
        # Thêm Rung màn hình và Effect
        from effects import CameraShake, EffectManager
        CameraShake.get_instance().add_trauma(0.6)
        if length > 200:
            EffectManager.get_instance().trigger_hitstop(0.08)

        # Particle Sukuna
        direction_deg = math.degrees(math.atan2(dist_vec.y, dist_vec.x))
        for p_color, p_count in [((220, 0, 0), 30), ((0, 0, 0), 20)]:
            ParticleManager.get_instance().spawn_directional(
                pos = start_pos + dist_vec * 0.5,
                direction_angle = direction_deg,
                count = p_count, color = p_color, size_range = (4, 10),
                speed_range = (200, 700), spread_deg = 50, lifetime = 0.5, gravity = 150
            )

    def draw_special(self, screen, camera):
        if self.is_aiming and self.start_pos:
            mouse_scr = pygame.math.Vector2(pygame.mouse.get_pos())
            screen_center = pygame.math.Vector2(600, 400)
            mouse_pos = (mouse_scr - screen_center) / GLOBAL_SCALE + camera + screen_center
            self._draw_dashed_line(screen, self.start_pos, mouse_pos, camera, (200, 50, 50))

        new_slashes = []
        for s in self.active_slashes:
            s['life'] -= 0.016
            if s['life'] > 0:
                progress = s['life'] / s['max_life']
                alpha = int(progress * 255)
                center = pygame.math.Vector2(600, 400)
                target = camera + center
                p1 = (s['start'] - target) * GLOBAL_SCALE + center
                p2 = (s['end'] - target) * GLOBAL_SCALE + center
                dist_vec = s['end'] - s['start']
                
                if dist_vec.length_squared() > 10:
                    perp = pygame.math.Vector2(-dist_vec.y, dist_vec.x).normalize()
                    
                    # Nếu là vết chém phụ thì vẽ mỏng hơn
                    thickness_mult = 0.4 if s.get('is_free', False) else 1.0
                    max_w = ((14 * progress) + 1.5) * GLOBAL_SCALE * thickness_mult
                    
                    # Vẽ 2 lớp để tránh bị sọc: Hào quang đỏ và Lõi đen
                    # 1. Hào quang đỏ thẫm (Mờ và Rộng)
                    glow_color = (150, 0, 0, alpha // 2)
                    glow_w = max_w * 2.2
                    pygame.draw.polygon(screen, glow_color, [
                        (p1.x, p1.y),
                        ((p1.x+p2.x)/2 + perp.x*glow_w, (p1.y+p2.y)/2 + perp.y*glow_w),
                        (p2.x, p2.y),
                        ((p1.x+p2.x)/2 - perp.x*glow_w, (p1.y+p2.y)/2 - perp.y*glow_w)
                    ])
                    
                    # 2. Lõi đen mực (Sắc và Mỏng)
                    core_color = (10, 0, 0, alpha)
                    core_w = max_w * 0.5
                    pygame.draw.polygon(screen, core_color, [
                        (p1.x, p1.y),
                        ((p1.x+p2.x)/2 + perp.x*core_w, (p1.y+p2.y)/2 + perp.y*core_w),
                        (p2.x, p2.y),
                        ((p1.x+p2.x)/2 - perp.x*core_w, (p1.y+p2.y)/2 - perp.y*core_w)
                    ])
                
                new_slashes.append(s)
        self.active_slashes = new_slashes

    def _draw_dashed_line(self, screen, start, end, camera, color, dash_len=10):
        dist_vec = end - start
        dist = dist_vec.length()
        if dist == 0: return
        center = pygame.math.Vector2(600, 400)
        target = camera + center
        for i in range(0, int(dist), dash_len * 2):
            p1 = (start + dist_vec * (i / dist) - target) * GLOBAL_SCALE + center
            p2 = (start + dist_vec * (min(i + dash_len, dist) / dist) - target) * GLOBAL_SCALE + center
            pygame.draw.line(screen, color, p1, p2, int(20 * GLOBAL_SCALE))
        
class WeaponManager:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None: cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.weapons = {} # Lưu trữ các instance vũ khí thực tế
        self.slot_names = [] # Tên 3 vũ khí trong slot
        
        self.angle = 0 
        self.last_final_angle = 0
        self.last_player_pos = pygame.math.Vector2(0,0)
        self.last_camera = pygame.math.Vector2(0,0)
        
        self.active_weapon = None
        # Khởi tạo súng sẽ được gọi sau khi Inventory đã nạp data

    def initialize_loadout(self):
        """Khởi tạo 3 instance vũ khí dựa trên Inventory Loadout."""
        from inventory import InventoryManager
        from arsenal import WEAPON_CATALOG
        
        inv = InventoryManager.get_instance()
        self.slot_names = inv.get_equipped_list()
        self.weapons = {}
        
        for name in self.slot_names:
            if name in WEAPON_CATALOG:
                data = WEAPON_CATALOG[name]
                level = inv.get_level(name)
                is_awakened = inv.is_awakened(name)
                # Khởi tạo instance: Class(*args, level=level, is_awakened=is_awakened, **kwargs)
                self.weapons[name] = data["class"](*data["args"], level=level, is_awakened=is_awakened, **data["kwargs"])
        
        # Đặt vũ khí mặc định từ slot hiện tại của Inventory
        active_id = inv.get_active_weapon_id()
        self.active_weapon = self.weapons.get(active_id, list(self.weapons.values())[0])

    def switch_to_slot(self, slot_idx):
        """Chuyển vũ khí theo index của slot (0, 1, 2)."""
        if 0 <= slot_idx < len(self.slot_names):
            from inventory import InventoryManager
            inv = InventoryManager.get_instance()
            inv.current_slot_idx = slot_idx
            
            name = self.slot_names[slot_idx]
            if name in self.weapons:
                if self.active_weapon == self.weapons[name]: return
                
                self.active_weapon.on_unequip()
                if hasattr(self.active_weapon, "is_charging"):
                    self.active_weapon.is_charging = False
                    
                self.active_weapon = self.weapons[name]

    def switch_weapon(self, name):
        """Chuyển vũ khí theo tên (tìm trong loadout)."""
        if name in self.slot_names:
            idx = self.slot_names.index(name)
            self.switch_to_slot(idx)

    def cycle_weapon(self, direction):
        """Cuộn vũ khí trong 3 slot."""
        from inventory import InventoryManager
        inv = InventoryManager.get_instance()
        new_idx = (inv.current_slot_idx + direction) % len(self.slot_names)
        self.switch_to_slot(new_idx)

    def attack(self, pos, target_pos, is_holding=False):
        self.last_player_pos = pos
        return self.active_weapon.attack(self, pos, target_pos, is_holding)

    def update(self, dt, player_pos, camera):
        self.last_player_pos = player_pos
        self.last_camera = camera
        self.active_weapon.update(self, dt)
        
        # Cập nhật hướng xoay vũ khí
        mouse_scr = pygame.math.Vector2(pygame.mouse.get_pos())
        screen_center = pygame.math.Vector2(600, 400)
        world_mouse = (mouse_scr - screen_center) / GLOBAL_SCALE + camera + screen_center
        direction = world_mouse - player_pos
        if direction.length_squared() > 0:
            target_angle = math.degrees(math.atan2(direction.y, direction.x))
            diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += diff * 20 * dt

    def draw(self, screen, player_pos, camera):
        # Gọi các hiệu ứng vẽ đặc biệt của vũ khí (ví dụ: đường nét đứt, aura, ghost...)
        if hasattr(self.active_weapon, "draw_special"):
            self.active_weapon.draw_special(screen, camera)
            
        # StandWeapon không cần vẽ tay/vũ khí đè lên con ma nên return sớm
        if isinstance(self.active_weapon, StandWeapon):
            return
            
        swing_off = 0
        if isinstance(self.active_weapon, Sword):
            p = self.active_weapon.swing_progress
            if p > 0.7: swing_off = (1.0 - (p-0.7)/0.3) * -120.0
            elif p > 0.1: 
                t = (p-0.1)/0.6
                swing_off = (1.0 - t) * 210.0 - 120.0 if t > 0 else 90.0
            else: swing_off = (p/0.1) * 90.0
            
        self._draw_weapon(screen, player_pos, camera, swing_off)

    def _draw_weapon(self, screen, player_pos, camera, swing_off):
        tex_name = self.active_weapon.texture_name
        # Ẩn vũ khí nếu thuộc tính is_visible = False (áp dụng cho TarotCard)
        if hasattr(self.active_weapon, "is_visible") and not self.active_weapon.is_visible:
            return
            
        weapon_tex = ResourceManager.get_instance().get_texture(tex_name)
        if not weapon_tex: return
        s = self.active_weapon.scale
        surf = pygame.transform.scale(weapon_tex, (int(32 * s * GLOBAL_SCALE), int(32 * s * GLOBAL_SCALE)))
        check_angle = (self.angle + 180) % 360 - 180
        flip_y = check_angle > 90 or check_angle < -90
        if flip_y:
            surf = pygame.transform.flip(surf, False, True)
            off, current_swing = 45, -swing_off
        else:
            off, current_swing = -45, swing_off
            
        # TarotCard vẽ thẳng hướng chuột, không cần offset 45 độ như súng/kiếm
        if isinstance(self.active_weapon, TarotCardWeapon):
            off = 0
            
        jitter_pos, jitter_ang = pygame.math.Vector2(0,0), 0
        if self.active_weapon.is_charging and isinstance(self.active_weapon, Sword):
            dur = time.time() - self.active_weapon.charge_start_time
            intens = min(dur * 1.5, 3.0)
            jitter_pos = pygame.math.Vector2(random.uniform(-intens, intens), random.uniform(-intens, intens))
            jitter_ang = random.uniform(-intens*2, intens*2)
        self.last_final_angle = self.angle + current_swing + jitter_ang
        rot_surf = pygame.transform.rotate(surf, -self.last_final_angle + off)
        
        center = pygame.math.Vector2(600, 400)
        target = camera + center
        rel_pos = (player_pos - target) * GLOBAL_SCALE + center
        
        dist = (self.active_weapon.arm_len + self.active_weapon.stick_len - self.active_weapon.current_recoil) * GLOBAL_SCALE
        rad = math.radians(self.last_final_angle)
        draw_pos = rel_pos + pygame.math.Vector2(math.cos(rad) * dist, math.sin(rad) * dist) + jitter_pos * GLOBAL_SCALE
        screen.blit(rot_surf, rot_surf.get_rect(center=(draw_pos.x, draw_pos.y)))
