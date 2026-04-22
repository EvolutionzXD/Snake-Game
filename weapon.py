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

class Weapon:
    def __init__(self, name, config_func, texture_name="stick", fire_rate=0.2, speed=1200.0, 
                 arm_len=20, stick_len=40, recoil=15, scale=1.5, stamina_cost=0.0, **kwargs):
        self.name = name
        self.config_func = config_func
        self.texture_name = texture_name
        self.fire_rate = fire_rate
        self.speed = speed
        self.scale = scale
        self.arm_len = arm_len
        self.stick_len = stick_len
        self.recoil_dist = recoil 
        self.stamina_cost = stamina_cost
        
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
            
            ProjectileManager.Spawn(
                pos                = pos, 
                target_pos         = target_pos, 
                config_func        = self.config_func, 
                speed              = self.speed,
                inherited_velocity = self._get_player_momentum()
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
                for _ in range(10):
                    spread = random.uniform(-20, 20)
                    rad = math.radians(base_angle + spread)
                    new_dir = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    proj_target = muzzle_pos + new_dir * 100
                    ProjectileManager.Spawn(
                        pos                = muzzle_pos, 
                        target_pos         = proj_target, 
                        config_func        = self.config_func, 
                        speed              = self.speed * random.uniform(0.8, 1.2),
                        inherited_velocity = momentum
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

    def attack(self, manager, pos, target_pos, is_holding):
        self.last_is_holding = is_holding # Lưu trạng thái để update dùng
        if not is_holding: return False
        
        # Chỉ đấm khi đã bay tới gần mục tiêu (chuột)
        if not self.is_near_target: return False

        current_time = time.time()
        if current_time - self.last_fire_time >= self.fire_rate:
            if AppleManager.stamina < self.stamina_cost: return False

            if self.ghost_node:
                punch_pos = self.ghost_node.position + pygame.math.Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
                
                # Tính toán hướng đấm có độ tản 10 độ cho máu lửa
                dir_vec = (pygame.math.Vector2(target_pos) - punch_pos)
                if dir_vec.length_squared() > 0:
                    base_angle = math.degrees(math.atan2(dir_vec.y, dir_vec.x))
                    spread_angle = math.radians(base_angle + random.uniform(-10, 10))
                    punch_target = punch_pos + pygame.math.Vector2(math.cos(spread_angle), math.sin(spread_angle)) * 100
                    
                    ProjectileManager.Spawn(
                        pos                = punch_pos, 
                        target_pos         = punch_target, 
                        config_func        = GetGhostPunchConfig, 
                        speed              = random.uniform(2000, 2600), # Tốc độ đấm biến thiên
                        inherited_velocity = self._get_player_momentum() * 0.2,
                        alpha_override     = 180
                    )
                
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
        
        move_speed = 12 if self.last_is_holding else 6
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
        proj = ProjectileManager.Spawn(
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
        ratio = min(self.charge_values["kb"] / 3000, 1.0)
        color = (int(180 + ratio*75), int(210 + ratio*45), 255)
        ParticleManager.get_instance().spawn_directional(pos=spawn_pos, direction_angle=manager.last_final_angle, count=int(4+ratio*8), color=color, alpha=int(180+ratio*75), size_range=(2,6), speed_range=(80,200), spread_deg=50, lifetime=0.25, gravity=150.0)

class FlameExtinguisher(Gun):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.is_automatic = True

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

class RealitySlash(Weapon):
    def __init__(self, name, config_func, **kwargs):
        super().__init__(name, config_func, **kwargs)
        self.start_pos = None
        self.is_aiming = False
        self.active_slashes = [] # Lưu danh sách nhát chém đang hiển thị
    
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
                self._trigger_slash(self.start_pos, current_mouse)
                # Thêm hiệu ứng animation vào danh sách
                self.active_slashes.append({
                    'start': self.start_pos,
                    'end': current_mouse,
                    'life': 0.25, # Thời gian tồn tại (giây)
                    'max_life': 0.25
                })
                AppleManager.stamina -= self.stamina_cost
                self.is_aiming = False
                self.start_pos = None
                return True
        return False

    def _trigger_slash(self, start_pos, end_pos):
        dist_vec = end_pos - start_pos
        length = dist_vec.length()
        if length < 10: return
      
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
                    # Giảm độ dày xuống 0.8 (từ 20 xuống khoảng 12-14)
                    max_w = ((14 * progress) + 1.5) * GLOBAL_SCALE
                    
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
        self.weapons = {
            "Pistol": Gun("Pistol", GetProjectileConfig, texture_name="pistol", fire_rate=0.4, speed=4000.0, arm_len=5, stick_len=30, scale=2, stamina_cost=0.0),
            "SMG": Gun("SMG", GetProjectileConfig, texture_name="stick", is_automatic=True, fire_rate=0.08, speed=1500.0, arm_len=2, stick_len=25, recoil=10, scale=1.2, stamina_cost=1.5),
            "FlameThrower": Flamethrower("FlameThrower", GetFlameConfig, texture_name="flame_thrower", fire_rate=0.03, speed=900.0, arm_len=10, stick_len=30, recoil=2, scale=1.8, stamina_cost=0.5),
            "AirSword": Sword("AirSword", GetSwordAirDashConfig, texture_name="stick", fire_rate=0.5, speed=0.0, arm_len=2, stick_len=50, recoil=0, scale=2.5, stamina_cost=20.0),
            "StarPlatinum": StandWeapon("StarPlatinum", GetGhostPunchConfig, texture_name="stick", fire_rate=0.04, speed=0.0, arm_len=0, stick_len=0, recoil=0, scale=0.8, stamina_cost=2.0),
            "FlameExtinguisher": FlameExtinguisher("FlameExtinguisher", GetFoamConfig, texture_name="fire_extinquisher", fire_rate=0.03, speed=2000.0, arm_len=10, stick_len=30, recoil=2, scale=1.8, stamina_cost=0.5),
            "RealitySlash": RealitySlash("RealitySlash", GetSlashConfig, texture_name="stick", fire_rate=0.5, speed=0.0, arm_len=2, stick_len=50, recoil=0, scale=2.5, stamina_cost=35.0)
        }
        self.active_weapon = self.weapons["Pistol"]
        self.angle = 0 
        self.last_final_angle = 0
        self.last_player_pos = pygame.math.Vector2(0,0)
        self.last_camera = pygame.math.Vector2(0,0)

    def switch_weapon(self, name):
        if name in self.weapons:
            self.active_weapon.on_unequip()
            if hasattr(self.active_weapon, "is_charging"):
                self.active_weapon.is_charging = False
            self.active_weapon = self.weapons[name]

    def attack(self, pos, target_pos, is_holding=False):
        self.last_player_pos = pos
        return self.active_weapon.attack(self, pos, target_pos, is_holding)

    def update_and_draw(self, screen, player_pos, camera, dt):
        self.last_player_pos = player_pos
        self.last_camera = camera
        self.active_weapon.update(self, dt)
        
        # Luôn cập nhật góc xoay dựa trên chuột để Stand cũng dùng được
        mouse_scr = pygame.math.Vector2(pygame.mouse.get_pos())
        screen_center = pygame.math.Vector2(600, 400)
        world_mouse = (mouse_scr - screen_center) / GLOBAL_SCALE + camera + screen_center
        direction = world_mouse - player_pos
        if direction.length_squared() > 0:
            target_angle = math.degrees(math.atan2(direction.y, direction.x))
            diff = (target_angle - self.angle + 180) % 360 - 180
            self.angle += diff * 20 * dt

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
