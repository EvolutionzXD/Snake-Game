import pygame
import random
from resources import get_surfaces
from effects import CameraShake, EffectManager  # Import 1 lần duy nhất
from particle import ParticleManager
from vfx import VFXManager

STUN_TIME = 0.3
INVINCIBILITY_TIME = 0.1
CELL_SIZE = 60.0  

# Hằng số offset cho grid - không tạo lại mỗi frame
_GRID_OFFSETS = [(-1,-1), (0,-1), (1,-1), (-1,0), (0,0), (1,0), (-1,1), (0,1), (1,1)]

active_nodes = []
grid_mat = {}
_shadow_cache = {}  # Cache bóng đổ để tránh tính lại mỗi frame

class Node:
    __slots__ = ['position', 'velocity', 'direction', 'angle', 'textureName', 
                 'hitbox_radius', 'MaxHp', 'Hp', 'knockback', 'stun', 'invincibility', 
                 'damage', 'mask', 'maskOut', 'textureOffsetX', 'textureOffsetY', 
                 'MinFrame', 'MaxFrame', 'frame', 'textureWidth', 'textureHeight', 
                 'scaleMultiplier', 'hasOutline', 'hasShadow', 'flashEffect', 'is_dead', 'is_dummy', 'canShakeCamera', 'canApplyFlash', 'lifetime', 'has_heavy_hit', 'flipX', 'flipY', 'stun_on_hit', 'has_trail_particles', 'alpha', 'origin_pos']

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
        self.maskOut = 0
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
        self.alpha = 255
        self.origin_pos = self.position.copy()
        active_nodes.append(self)

    def apply_config(self, config):
        self.textureName = config.textureName
        self.hitbox_radius = config.hitbox_radius
        self.MaxHp = config.MaxHp
        self.Hp = config.MaxHp
        self.knockback = config.knockback
        self.damage = config.damage
        self.mask = config.mask
        self.maskOut = config.maskOut
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
        self.hasShadow = config.hasShadow

    def deal_damage_to(self, other, amount):
        other.Hp -= amount
        
        # Kiểm tra xem đòn đánh có nhắm vào kẻ địch (mask 1) không để hiện số damage
        target_masks = self.maskOut if isinstance(self.maskOut, (list, tuple)) else [self.maskOut]
        if 1 in target_masks:
            EffectManager.get_instance().add_damage_number(other.position + pygame.math.Vector2(0, -30), amount)
        if self.canShakeCamera:
            CameraShake.get_instance().add_trauma(0.5)
        
        # --- PARTICLE KHI BỊ ĐÁNH (MÁU XANH) ---
        # hit_count = max(4, min(int(amount / 8), 16))
        # hit_size  = (3, max(6, min(int(amount / 10), 14)))
        # ParticleManager.get_instance().spawn(
        #     pos         = other.position,
        #     count       = hit_count,
        #     color       = (60, 220, 80),   # Xanh lá — máu rắn
        #     alpha       = 230,
        #     size_range  = hit_size,
        #     speed_range = (60, 280),
        #     lifetime    = 0.45,
        #     gravity     = 300.0,
        # )
            
    def apply_flash_to(self, other, duration):
        if self.canApplyFlash:
            other.flashEffect = max(other.flashEffect, duration)

    def apply_stun_to(self, other, duration):
        other.stun = max(other.stun, duration)

    def apply_knockback_to(self, other, force):
        if self.position.distance_squared_to(other.position) > 0:
            push_dir = (other.position - self.position).normalize()
        else:
            push_dir = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        other.velocity += push_dir * force

    def get_position_id(self):
        return (int(self.position.x // CELL_SIZE), int(self.position.y // CELL_SIZE))

    def get_surfaces(self):
        if not self.textureName or self.is_dead or self.is_dummy: return None, None
        curr_frame = int(self.frame) + self.MinFrame
        return get_surfaces(self.textureName, curr_frame, 4.0, self.scaleMultiplier, self.angle, self.flashEffect, self.hasOutline)

    def draw_outline(self, screen, camera):
        outline_surf, _ = self.get_surfaces()
        if not outline_surf: return
        if self.flipX or self.flipY:
            outline_surf = pygame.transform.flip(outline_surf, self.flipX, self.flipY)
        outline_surf.set_alpha(self.alpha)
        draw_pos = self.position - camera + pygame.math.Vector2(self.textureOffsetX, self.textureOffsetY)
        rect = outline_surf.get_rect(center=(draw_pos.x, draw_pos.y))
        screen.blit(outline_surf, rect)

    def draw_sprite(self, screen, camera):
        _, sprite_surf = self.get_surfaces()
        if not sprite_surf: return
        if self.flipX or self.flipY:
            sprite_surf = pygame.transform.flip(sprite_surf, self.flipX, self.flipY)
        sprite_surf.set_alpha(self.alpha)
        draw_pos = self.position - camera + pygame.math.Vector2(self.textureOffsetX, self.textureOffsetY)
        rect = sprite_surf.get_rect(center=(draw_pos.x, draw_pos.y))
        screen.blit(sprite_surf, rect)

    def draw_shadow(self, screen, camera):
        if not self.hasShadow: return
        _, sprite_surf = self.get_surfaces()
        if not sprite_surf: return
        
        # Cache bóng đổ theo surface id để tránh tính lại mask mỗi frame
        surf_key = id(sprite_surf)
        if surf_key not in _shadow_cache:
            raw_shadow = pygame.mask.from_surface(sprite_surf).to_surface(setcolor=(0,0,0,80), unsetcolor=(0,0,0,0))
            w, h = raw_shadow.get_size()
            raw_shadow = pygame.transform.flip(raw_shadow, False, True)
            _shadow_cache[surf_key] = pygame.transform.scale(raw_shadow, (w, int(h * 0.5)))
        
        shadow_surf = _shadow_cache[surf_key]
        if self.flipX or self.flipY:
            shadow_surf = pygame.transform.flip(shadow_surf, self.flipX, self.flipY)
            
        draw_pos = self.position - camera + pygame.math.Vector2(self.textureOffsetX, -self.textureOffsetY*0.5)
        rect = shadow_surf.get_rect(midtop=(draw_pos.x, draw_pos.y + 5))
        screen.blit(shadow_surf, rect)

def process_physics_and_collisions(dt):
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
            if vel_sq > 640000: # Vận tốc > 800 px/s (Cực mạnh)
                pm = ParticleManager.get_instance()
                # Spawn nhiều hạt hơn (4 hạt mỗi frame) để tạo vệt trượt dày đặc
                pm.spawn(
                    pos         = node.position,
                    count       = 4, 
                    color       = (210, 200, 180), 
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
                        color       = (200, 200, 200), 
                        alpha       = 130, 
                        size_range  = (3, 7), 
                        speed_range = (10, 40), 
                        lifetime    = 0.4, 
                        gravity     = -30.0
                    )
            elif vel_sq > 40000: # Thêm khói nhẹ cả khi di chuyển nhanh vừa phải (>200)
                if random.random() < 0.3:
                    ParticleManager.get_instance().spawn(pos=node.position, count=1, color=(220, 220, 220), alpha=80, size_range=(2, 5), speed_range=(5, 15), lifetime=0.3, gravity=-20.0)

        if node.invincibility > 0: node.invincibility -= dt
        if node.flashEffect > 0: node.flashEffect -= dt
        
        node.frame += dt * 5
        if node.frame >= (node.MaxFrame - node.MinFrame + 1):
            node.frame = 0.0
            
        cell = node.get_position_id()
        if node.mask not in grid_mat: grid_mat[node.mask] = {}
        if cell not in grid_mat[node.mask]: grid_mat[node.mask][cell] = []
        grid_mat[node.mask][cell].append(node)

    offsets = _GRID_OFFSETS
    for node in active_nodes:
        # Hỗ trợ maskOut có thể là 1 giá trị hoặc 1 list các giá trị
        target_masks = node.maskOut if isinstance(node.maskOut, (list, tuple)) else [node.maskOut]
        
        for maskOut in target_masks:
            if maskOut not in grid_mat: continue
            
            px, py = node.get_position_id()
            for dx, dy in offsets:
                cell = (px + dx, py + dy)
                if cell in grid_mat[maskOut]:
                    for other in grid_mat[maskOut][cell]:
                        if node is other or other.invincibility > 0: continue
                        
                        r_sum = (node.hitbox_radius * node.scaleMultiplier) + (other.hitbox_radius * other.scaleMultiplier)
                        dist_sq = node.position.distance_squared_to(other.position)
                        
                        if dist_sq < r_sum * r_sum:
                            # Xử lý va chạm
                            node.deal_damage_to(other, node.damage)
                            node.apply_knockback_to(other, node.knockback)
                            node.apply_stun_to(other, node.stun_on_hit)
                            node.apply_flash_to(other, 0.5)
                            other.invincibility = INVINCIBILITY_TIME
                            
                            # --- HIỆU ỨNG VA CHẠM MẠNH (JUICE) ---
                            # Chỉ kích hoạt 1 lần duy nhất cho mỗi projectile để tránh lag
                            if node.knockback > 2000 and not node.has_heavy_hit:
                                CameraShake.get_instance().add_trauma(0.6)
                                EffectManager.get_instance().trigger_hitstop(0.2)
                                node.has_heavy_hit = True
