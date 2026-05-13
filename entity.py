import pygame
import random
from resources import get_surfaces
from effects import CameraShake, EffectManager  # Import 1 lần duy nhất
from particle import ParticleManager
from vfx import VFXManager
from config import GLOBAL_SCALE

STUN_TIME = 0.3
INVINCIBILITY_TIME = 0.1
CELL_SIZE = 60.0  

# Hằng số offset cho grid - không tạo lại mỗi frame
_GRID_OFFSETS = [(-1,-1), (0,-1), (1,-1), (-1,0), (0,0), (1,0), (-1,1), (0,1), (1,1)]
_SCREEN_CENTER = pygame.math.Vector2(600, 400)

active_nodes = []
grid_mat = {}
_shadow_cache = {}  # Cache bóng đổ để tránh tính lại mỗi frame

class Node:
    __slots__ = ['position', 'velocity', 'direction', 'angle', 'textureName', 
                 'hitbox_radius', 'MaxHp', 'Hp', 'knockback', 'stun', 'invincibility', 
                 'damage', 'mask', 'maskOut', 'textureOffsetX', 'textureOffsetY', 
                 'MinFrame', 'MaxFrame', 'frame', 'textureWidth', 'textureHeight', 
                 'scaleMultiplier', 'hasOutline', 'hasShadow', 'flashEffect', 'is_dead', 'is_dummy', 'canShakeCamera', 'canApplyFlash', 'lifetime', 'has_heavy_hit', 'flipX', 'flipY', 'stun_on_hit', 'has_trail_particles', 'trail_color', 'alpha', 'origin_pos', 'snake_head', 'snake_depth', 'knockback_resistance', 'can_be_stunned']

    def __init__(self, pos):
        self.position = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(0, 0)
        self.direction = pygame.math.Vector2(0, 0)
        self.angle = 0.0
        self.textureName = ""
        self.hitbox_radius = 30.0
        self.MaxHp = 100.0
        self.Hp = 100.0
        self.knockback = 10.0
        self.stun = 0.0
        self.invincibility = 0.0
        self.damage = 10.0
        self.mask = 0
        self.maskOut = (0,)
        self.textureOffsetX = 0.0
        self.textureOffsetY = 0.0
        self.MinFrame = 0
        self.MaxFrame = 0
        self.frame = 0.0
        self.textureWidth = 32.0
        self.textureHeight = 32.0
        self.scaleMultiplier = 1.0
        self.hasOutline = False
        self.hasShadow = True
        self.flashEffect = 0.0
        self.is_dead = False
        self.is_dummy = False 
        self.canShakeCamera = True
        self.canApplyFlash = True
        self.lifetime = -1.0 # -1 means infinite
        self.has_heavy_hit = False # Để giới hạn hiệu ứng rung/khựng hình một lần mỗi projectile
        self.flipX = False
        self.flipY = False
        self.stun_on_hit = 0.1
        self.has_trail_particles = True
        self.trail_color = (200, 200, 200)
        self.alpha = 255
        self.origin_pos = self.position.copy()
        self.snake_head = None
        self.snake_depth = 0
        self.knockback_resistance = 1.0
        self.can_be_stunned = True
        active_nodes.append(self)

    def apply_config(self, config):
        """Nạp toàn bộ thông số từ một NodeConfig (máu, sát thương, knockback, mask, texture, v.v.)."""
        self.textureName = config.textureName
        self.hitbox_radius = config.hitbox_radius
        self.MaxHp = config.MaxHp
        self.Hp = config.MaxHp
        self.knockback = config.knockback
        self.damage = config.damage
        self.mask = config.mask
        self.maskOut = config.maskOut
        if not isinstance(self.maskOut, (list, tuple)):
            self.maskOut = (self.maskOut,)
        self.MinFrame = config.MinFrame
        self.MaxFrame = config.MaxFrame
        self.textureWidth = config.textureWidth
        self.textureHeight = config.textureHeight
        self.scaleMultiplier = config.scaleMultiplier
        self.hasOutline = config.hasOutline
        self.canShakeCamera = config.canShakeCamera
        self.canApplyFlash = config.canApplyFlash
        self.lifetime = config.lifetime
        self.stun_on_hit = config.stun_on_hit
        self.has_trail_particles = config.has_trail_particles
        self.trail_color = getattr(config, 'trail_color', (200, 200, 200))
        self.hasShadow = config.hasShadow
        self.knockback_resistance = getattr(config, 'knockback_resistance', 1.0)
        self.can_be_stunned = getattr(config, 'can_be_stunned', True)

    def deal_damage_to(self, other, amount):
        """Trừ máu `other` theo `amount`, hiển thị số sát thương nếu nhắm vào rắn, rúng màn hình nếu cấu hình cho phép."""
        other.Hp -= amount
        
        # Kiểm tra xem đòn đánh có nhắm vào kẻ địch (mask 1) không để hiện số damage
        if 1 in self.maskOut:
            EffectManager.get_instance().add_damage_number(other.position + pygame.math.Vector2(0, -30), amount)
        if self.canShakeCamera:
            CameraShake.get_instance().add_trauma(0.5)
        
        # --- PARTICLE KHI BỊ ĐÁNH (Bỏ theo ý người dùng) ---
        # hit_count = max(5, min(int(amount / 3), 20))
        # ...
            
    def apply_flash_to(self, other, duration):
        """Bật hiệu ứng nhấp nháy trắng (Flash) cho `other` trong `duration` giây nếu vũ khí có thuộc tính canApplyFlash."""
        if self.canApplyFlash:
            other.flashEffect = max(other.flashEffect, duration)

    def apply_stun_to(self, other, duration):
        """Gây hiệu ứng stun lên `other` trong `duration` giây, tạm khóa hướng di chuyển của thực thể đó."""
        if getattr(other, 'can_be_stunned', True):
            other.stun = max(other.stun, duration)

    def apply_knockback_to(self, other, force):
        """Dẩy bắn `other` ra xa theo hướng từ self sang other.
        Nếu lực đẩy vượt 1500, kích hoạt HitStop để tăng cảm giác ủy lực của đòn đánh."""
        resistance = getattr(other, 'knockback_resistance', 1.0)
        actual_force = force * resistance
        if actual_force <= 0: return
        
        # --- HIỆU ỨNG KHỰNG HÌNH CHO ĐÒN NẶNG (Screen Freeze) ---
        # Nếu lực đẩy cực lớn, tạo hiệu ứng dừng hình lâu hơn theo ý bạn
        if actual_force > 1500 and not getattr(self, 'has_heavy_hit', False):
            EffectManager.get_instance().trigger_hitstop(0.25) # Tăng từ 0.12 -> 0.25
            self.has_heavy_hit = True 
            
        if self.position.distance_squared_to(other.position) > 0:
            push_dir = (other.position - self.position).normalize()
        else:
            push_dir = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        other.velocity += push_dir * actual_force

    def get_position_id(self):
        """Trả về toạ độ ô lưới (Grid Cell) dưới dạng tuple (col, row) mà node này đang ở."""
        return (int(self.position.x // CELL_SIZE), int(self.position.y // CELL_SIZE))

    def get_surfaces(self):
        """Lấy cặp surface (outline, sprite) tương ứng với frame và góc xoay hiện tại từ ResourceManager."""
        if not self.textureName or self.is_dead or self.is_dummy: return None, None
        curr_frame = int(self.frame) + self.MinFrame
        return get_surfaces(self.textureName, curr_frame, 4.0, self.scaleMultiplier, self.angle, self.flashEffect, self.hasOutline)

    def draw_outline(self, screen, camera):
        """Vẽ viền outline (nếu có) của node lên màn hình, có hỗ trợ Viewport Culling để tối ưu."""
        outline_surf, _ = self.get_surfaces()
        if not outline_surf: return
        
        target = camera + _SCREEN_CENTER
        draw_pos = (self.position - target) * GLOBAL_SCALE + _SCREEN_CENTER + pygame.math.Vector2(self.textureOffsetX, self.textureOffsetY) * GLOBAL_SCALE
        
        # Viewport Culling
        w, h = outline_surf.get_size()
        if draw_pos.x + w < 0 or draw_pos.x - w > screen.get_width() or draw_pos.y + h < 0 or draw_pos.y - h > screen.get_height():
            return

        if self.flipX or self.flipY:
            outline_surf = pygame.transform.flip(outline_surf, self.flipX, self.flipY)
        outline_surf.set_alpha(self.alpha)
        rect = outline_surf.get_rect(center=(draw_pos.x, draw_pos.y))
        screen.blit(outline_surf, rect)

    def draw_sprite(self, screen, camera):
        """Vẽ sprite chính của node lên màn hình, có hỗ trợ Viewport Culling và flip X/Y."""
        _, sprite_surf = self.get_surfaces()
        if not sprite_surf: return
        
        target = camera + _SCREEN_CENTER
        draw_pos = (self.position - target) * GLOBAL_SCALE + _SCREEN_CENTER + pygame.math.Vector2(self.textureOffsetX, self.textureOffsetY) * GLOBAL_SCALE
        
        # Viewport Culling
        w, h = sprite_surf.get_size()
        if draw_pos.x + w < 0 or draw_pos.x - w > screen.get_width() or draw_pos.y + h < 0 or draw_pos.y - h > screen.get_height():
            return

        if self.flipX or self.flipY:
            sprite_surf = pygame.transform.flip(sprite_surf, self.flipX, self.flipY)
        sprite_surf.set_alpha(self.alpha)
        rect = sprite_surf.get_rect(center=(draw_pos.x, draw_pos.y))
        screen.blit(sprite_surf, rect)

    def draw_shadow(self, screen, camera):
        """Vẽ bóng đổ phía dưới node bằng cách tạo mask nối đen và nén theo trục Y (có cache để tránh tính lại mỗi frame)."""
        if not self.hasShadow: return
        _, sprite_surf = self.get_surfaces()
        if not sprite_surf: return
        
        target = camera + _SCREEN_CENTER
        draw_pos = (self.position - target) * GLOBAL_SCALE + _SCREEN_CENTER + pygame.math.Vector2(self.textureOffsetX, -self.textureOffsetY*0.5) * GLOBAL_SCALE
        
        # Viewport Culling (do it before calculating shadow mask)
        w, h = sprite_surf.get_size()
        if draw_pos.x + w < 0 or draw_pos.x - w > screen.get_width() or draw_pos.y + h < 0 or draw_pos.y - h > screen.get_height():
            return
        
        surf_key = id(sprite_surf)
        if surf_key not in _shadow_cache:
            raw_shadow = pygame.mask.from_surface(sprite_surf).to_surface(setcolor=(0,0,0,80), unsetcolor=(0,0,0,0))
            w_s, h_s = raw_shadow.get_size()
            raw_shadow = pygame.transform.flip(raw_shadow, False, True)
            _shadow_cache[surf_key] = pygame.transform.scale(raw_shadow, (w_s, int(h_s * 0.5)))
        
        shadow_surf = _shadow_cache[surf_key]
        if self.flipX or self.flipY:
            shadow_surf = pygame.transform.flip(shadow_surf, self.flipX, self.flipY)
            
        rect = shadow_surf.get_rect(midtop=(draw_pos.x, draw_pos.y + 5 * GLOBAL_SCALE))
        screen.blit(shadow_surf, rect)

def process_physics_and_collisions(dt):
    """Hàm cốt lõi được gọi mỗi frame:
    - Xử lý thực thể chết: tạo particle, rời EXP, dịn danh sách.
    - Cập nhật vật lý: di chuyển, ma sát, stun, đời sống.
    - Đăng ký node vào Grid Hash theo mask.
    - Kiểm tra và xử lý va chạm hiệu quả nh᷑ Grid Hash (gần O(N) thay vì O(N^2))."""
    global active_nodes
    
    # Single pass removal thay vì any() + list comprehension riêng biệt
    had_dead = False
    for n in active_nodes:
        if n.Hp <= 0 or n.is_dead:
            had_dead = True
            break
    
    if had_dead:
        # --- HIỆU ỨNG KHI CHẾT ---
        pm = ParticleManager.get_instance()
        for n in active_nodes:
            if n.Hp <= 0:
                n.is_dead = True
                
                if n.mask == 1:  # Node rắn (Xanh lá) - Luôn nổ khi chết
                    scale = n.scaleMultiplier
                    count = int(8 + scale * 20)
                    pm.spawn(
                        pos=n.position, count=count, color=(50, 200, 70), alpha=255,
                        size_range=(3, max(5, int(4 + scale * 14))),
                        speed_range=(80, int(200 + scale * 200)),
                        lifetime=0.5 + scale * 0.3, gravity=250.0,
                    )
                    
                    if getattr(n, 'snake_head', None) == n:
                        from stage import StageManager
                        StageManager.get_instance().on_snake_killed(n.position, n.MaxHp)
        
        active_nodes[:] = [n for n in active_nodes if n.Hp > 0 and not n.is_dead]

    grid_mat.clear()

    for node in active_nodes:
        if node.lifetime > 0:
            node.lifetime -= dt
            if node.lifetime <= 0:
                node.Hp = 0
                continue
                
        if node.stun <= 0:
            frameVelocity = node.velocity + node.direction
        else:
            frameVelocity = node.velocity.copy()
            node.stun -= dt

        node.position += frameVelocity * dt
        node.velocity *= 0.9  
        
        # --- HIỆU ỨNG BỤI TRƯỢT DÀI (Nhiều khói hơn) ---
        if node.has_trail_particles:
            vel_sq = node.velocity.length_squared()
            color = node.trail_color
            if vel_sq > 640000: # Vận tốc > 800 px/s (Cực mạnh)
                pm = ParticleManager.get_instance()
                # Spawn nhiều hạt hơn (4 hạt mỗi frame) để tạo vệt trượt dày đặc
                pm.spawn(
                    pos         = node.position,
                    count       = 4, 
                    color       = color, 
                    alpha       = 160,
                    size_range  = (4, 10),
                    speed_range = (40, 150),
                    lifetime    = 0.5,
                    gravity     = 100.0 
                )
            elif vel_sq > 160000: # Vận tốc > 400 px/s (Bình thường)
                if random.random() < 0.7: # Tăng tỉ lệ xuất hiện lên 70%
                    pm = ParticleManager.get_instance()
                    pm.spawn(
                        pos         = node.position, 
                        count       = 2, # Tăng lên 2 hạt
                        color       = color, 
                        alpha       = 130, 
                        size_range  = (3, 7), 
                        speed_range = (10, 40), 
                        lifetime    = 0.4, 
                        gravity     = -30.0
                    )
            elif vel_sq > 40000: # Thêm khói nhẹ cả khi di chuyển nhanh vừa phải (>200)
                if random.random() < 0.3:
                    ParticleManager.get_instance().spawn(pos=node.position, count=1, color=color, alpha=80, size_range=(2, 5), speed_range=(5, 15), lifetime=0.3, gravity=-20.0)

        if node.invincibility > 0: node.invincibility -= dt
        if node.flashEffect > 0: node.flashEffect -= dt
        
        node.frame += dt * 5
        if node.frame >= (node.MaxFrame - node.MinFrame + 1):
            node.frame = 0.0
            
        # --- GRID REGISTRATION ---
        radius = node.hitbox_radius * node.scaleMultiplier
        if radius > CELL_SIZE * 0.5:
            # Nếu node bự hơn nửa cell, đăng ký vào tất cả các cell mà nó chạm tới
            min_x = int((node.position.x - radius) // CELL_SIZE)
            max_x = int((node.position.x + radius) // CELL_SIZE)
            min_y = int((node.position.y - radius) // CELL_SIZE)
            max_y = int((node.position.y + radius) // CELL_SIZE)
            
            if node.mask not in grid_mat: grid_mat[node.mask] = {}
            for cx in range(min_x, max_x + 1):
                for cy in range(min_y, max_y + 1):
                    cell = (cx, cy)
                    if cell not in grid_mat[node.mask]: grid_mat[node.mask][cell] = []
                    grid_mat[node.mask][cell].append(node)
        else:
            # Node nhỏ thì chỉ đăng ký vào cell trung tâm (tối ưu hiệu năng)
            cell = node.get_position_id()
            if node.mask not in grid_mat: grid_mat[node.mask] = {}
            if cell not in grid_mat[node.mask]: grid_mat[node.mask][cell] = []
            grid_mat[node.mask][cell].append(node)

    offsets = _GRID_OFFSETS
    for node in active_nodes:
        for maskOut in node.maskOut:
            if maskOut not in grid_mat: continue
            
            # Tối ưu: Chỉ tìm kiếm trong các cell mà node này thực sự chạm tới
            radius = node.hitbox_radius * node.scaleMultiplier
            if radius > CELL_SIZE * 0.5:
                min_x = int((node.position.x - radius) // CELL_SIZE)
                max_x = int((node.position.x + radius) // CELL_SIZE)
                min_y = int((node.position.y - radius) // CELL_SIZE)
                max_y = int((node.position.y + radius) // CELL_SIZE)
                
                for cx in range(min_x, max_x + 1):
                    for cy in range(min_y, max_y + 1):
                        cell = (cx, cy)
                        if cell in grid_mat[maskOut]:
                            for other in grid_mat[maskOut][cell]:
                                if node is other or other.invincibility > 0: continue
                                r_sum = (node.hitbox_radius * node.scaleMultiplier) + (other.hitbox_radius * other.scaleMultiplier)
                                dist_sq = node.position.distance_squared_to(other.position)
                                if dist_sq < r_sum * r_sum:
                                    node.deal_damage_to(other, node.damage)
                                    node.apply_knockback_to(other, node.knockback)
                                    node.apply_stun_to(other, node.stun_on_hit)
                                    node.apply_flash_to(other, 0.5)
                                    other.invincibility = INVINCIBILITY_TIME
            else:
                px, py = node.get_position_id()
                for dx, dy in offsets:
                    cell = (px + dx, py + dy)
                    if cell in grid_mat[maskOut]:
                        for other in grid_mat[maskOut][cell]:
                            if node is other or other.invincibility > 0: continue
                            r_sum = (node.hitbox_radius * node.scaleMultiplier) + (other.hitbox_radius * other.scaleMultiplier)
                            dist_sq = node.position.distance_squared_to(other.position)
                            if dist_sq < r_sum * r_sum:
                                node.deal_damage_to(other, node.damage)
                                node.apply_knockback_to(other, node.knockback)
                                node.apply_stun_to(other, node.stun_on_hit)
                                node.apply_flash_to(other, 0.5)
                                other.invincibility = INVINCIBILITY_TIME
